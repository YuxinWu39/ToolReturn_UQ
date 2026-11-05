#!/usr/bin/env python3
"""Step 2 (P1 + amendment A-P1): failure taxonomy from paired clean/toxic runs with a run-to-run noise null.

    python taxonomy.py --out results/taxonomy [--boot 2000]

Writes pairs.jsonl and summary.json; prints the amended G1 decision (excess toxic-failure rate, lower CI > 0).
"""

import argparse
import collections
import json
from math import comb
from pathlib import Path

import numpy as np

from common import REPO, adapter_family, infer_severity, load_tasks, pair_runs

CLASSES = ["cap_both_fail", "cap_clean_only_fail", "observation_consumed", "observation_exposed_only", "unexposed",
           "no_effect_recovered", "no_effect_exposed_unexplained", "no_effect_other"]


def classify(clean, toxic):
    ok_c, ok_t = clean["metrics"]["task_success"], toxic["metrics"]["task_success"]
    exposed = any(e.get("was_poisoned") for e in toxic["tool_events"])
    if not ok_c:
        return "cap_clean_only_fail" if ok_t else "cap_both_fail"
    if not ok_t:
        if not exposed:
            return "unexposed"
        return "observation_consumed" if toxic["metrics"].get("poisoned_answer_used") else "observation_exposed_only"
    if toxic["metrics"].get("recovery"):
        return "no_effect_recovered"
    if exposed and not toxic["metrics"].get("poisoned_answer_used"):
        return "no_effect_exposed_unexplained"
    return "no_effect_other"


def mcnemar_exact(b, c):
    """Two-sided exact McNemar p-value for discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def discordance(runs):
    """Among keys with >= 2 runs of the same environment: P(run_2 fails | run_1 succeeds)."""
    succ_then_fail, succ = 0, 0
    for group in runs:
        if len(group) < 2 or not group[0]["metrics"]["task_success"]:
            continue
        succ += 1
        succ_then_fail += int(not group[1]["metrics"]["task_success"])
    return succ_then_fail, succ


def excess_rate(rows, clean_dups, toxic_dups):
    """toxic-fail-given-clean-ok minus clean-vs-clean noise floor."""
    ok = [r for r in rows if r["class"] not in ("cap_both_fail", "cap_clean_only_fail")]
    fail = sum(r["class"] in ("observation_consumed", "observation_exposed_only", "unexposed") for r in ok)
    p_fail = fail / len(ok) if ok else float("nan")
    nf, ns = discordance(clean_dups)
    floor = nf / ns if ns else float("nan")
    return p_fail, floor, p_fail - floor


def clustered_ci(rows, clean_dups, boot, seed=0):
    rng = np.random.default_rng(seed)
    by_task = collections.defaultdict(list)
    for r in rows:
        by_task[r["task_id"]].append(r)
    dup_by_task = collections.defaultdict(list)
    for group in clean_dups:
        dup_by_task[group[0]["task_id"]].append(group)
    tasks = list(by_task)
    vals = []
    for _ in range(boot):
        picked = rng.choice(tasks, len(tasks), replace=True)
        rows_b = [r for t in picked for r in by_task[t]]
        dups_b = [g for t in picked for g in dup_by_task.get(t, [])]
        _, _, ex = excess_rate(rows_b, dups_b, None)
        if not np.isnan(ex):
            vals.append(ex)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=REPO / "experiments" / "results" / "taxonomy")
    parser.add_argument("--boot", type=int, default=2000)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    tasks = load_tasks()
    pairs = pair_runs()
    rows, clean_dups, toxic_dups = [], [], []
    same_source = 0
    for (task_id, adapter, model), envs in sorted(pairs.items(), key=lambda kv: str(kv[0])):
        if len(envs["clean"]) >= 2:
            clean_dups.append(envs["clean"])
        if len(envs["toxic"]) >= 2:
            toxic_dups.append(envs["toxic"])
        if not envs["clean"] or not envs["toxic"]:
            continue
        clean, toxic = envs["clean"][0], envs["toxic"][0]
        same_source += clean["_run_id"].split("#")[0] == toxic["_run_id"].split("#")[0]
        task = tasks.get(task_id, {})
        rows.append({
            "task_id": task_id, "adapter": adapter, "adapter_family": adapter_family(adapter), "model": model,
            "family": toxic.get("family"), "dataset": toxic.get("dataset"),
            "poison_type": (task.get("poison") or toxic.get("poison") or {}).get("type"),
            "severity": infer_severity(task if task else toxic), "class": classify(clean, toxic),
            "clean_run": clean["_run_id"], "toxic_run": toxic["_run_id"],
        })
    with (args.out / "pairs.jsonl").open("w") as sink:
        for row in rows:
            sink.write(json.dumps(row) + "\n")

    def block(subset, dups_c, dups_t, boot):
        counts = collections.Counter(r["class"] for r in subset)
        b = counts["observation_consumed"] + counts["observation_exposed_only"] + counts["unexposed"]  # clean ok, toxic fail
        c = counts["cap_clean_only_fail"]                 # clean fail, toxic ok
        p_fail, floor, ex = excess_rate(subset, dups_c, dups_t)
        tf, ts = discordance(dups_t)
        nf, ns = discordance(dups_c)
        cap, obs = counts["cap_both_fail"] + counts["cap_clean_only_fail"], counts["observation_consumed"] + counts["observation_exposed_only"]
        n_ok = len(subset) - cap
        corrected_obs = max(0.0, obs - floor * n_ok) if ns else None
        obs_c = counts["observation_consumed"]
        return {
            "pairs": len(subset), "classes": {k: counts[k] for k in CLASSES},
            "observation_share_consumed_only": None if cap + obs_c == 0 else round(obs_c / (cap + obs_c), 4),
            "p_toxic_fail_given_clean_ok": round(p_fail, 4), "noise_floor_clean_vs_clean": None if not ns else round(floor, 4),
            "noise_floor_n": ns, "noise_floor_toxic_vs_toxic": None if not ts else round(tf / ts, 4),
            "excess_rate": None if np.isnan(ex) else round(ex, 4),
            "excess_rate_ci95_task_clustered": clustered_ci(subset, dups_c, boot) if ns else None,
            "mcnemar_b_clean_ok_toxic_fail": b, "mcnemar_c_clean_fail_toxic_ok": c, "mcnemar_p_exact": mcnemar_exact(b, c),
            "observation_share_raw": None if cap + obs == 0 else round(obs / (cap + obs), 4),
            "observation_share_noise_corrected": None if corrected_obs is None or cap + corrected_obs == 0 else round(corrected_obs / (cap + corrected_obs), 4),
        }

    overall = block(rows, clean_dups, toxic_dups, args.boot)
    num_rows = [r for r in rows if r["family"] == "numerical"]
    num_dc = [g for g in clean_dups if g[0]["family"] == "numerical"]
    num_dt = [g for g in toxic_dups if g[0]["family"] == "numerical"]
    numerical = block(num_rows, num_dc, num_dt, args.boot)
    strata = {}
    for axis in ("family", "severity", "model", "adapter_family", "poison_type"):
        for value in sorted({str(r[axis]) for r in rows}):
            sub = [r for r in rows if str(r[axis]) == value]
            strata[f"{axis}={value}"] = block(sub, [g for g in clean_dups if str(g[0].get(axis, adapter_family(g[0]["adapter"]) if axis == "adapter_family" else None)) == value] if axis != "poison_type" and axis != "severity" else [], [], 0)

    subtle_num = collections.Counter(r["class"] for r in num_rows if r["severity"] == "subtle")
    lo_all = (overall["excess_rate_ci95_task_clustered"] or [float("nan")])[0]
    lo_num = (numerical["excess_rate_ci95_task_clustered"] or [float("nan")])[0]
    g1_pass = lo_all > 0 and lo_num > 0
    floor_by_model = {}
    for model in sorted({r["model"] for r in rows}):
        nf, ns = discordance([g for g in clean_dups if g[0]["model"] == model])
        floor_by_model[model] = {"noise_floor": None if not ns else round(nf / ns, 4), "n": ns, "pairs": sum(r["model"] == model for r in rows)}
    tot = sum(v["pairs"] for v in floor_by_model.values())
    reweighted = sum(v["noise_floor"] * v["pairs"] for v in floor_by_model.values() if v["noise_floor"] is not None) / max(1, sum(v["pairs"] for v in floor_by_model.values() if v["noise_floor"] is not None))
    summary = {
        "noise_floor_by_model": floor_by_model, "noise_floor_reweighted_to_pairs": round(reweighted, 4),
        "pairs": len(rows), "same_source_file_pairs": same_source, "keys_with_duplicate_clean_runs": len(clean_dups),
        "keys_with_duplicate_toxic_runs": len(toxic_dups), "overall": overall, "numerical": numerical,
        "G1_amended": {"rule": "excess rate lower CI > 0, overall AND numerical", "pass": bool(g1_pass)},
        "H6_power": {"observation_subtle_numerical": subtle_num["observation_consumed"] + subtle_num["observation_exposed_only"],
                     "capability_subtle_numerical": subtle_num["cap_both_fail"] + subtle_num["cap_clean_only_fail"],
                     "h6_exploratory": min(subtle_num["observation_consumed"] + subtle_num["observation_exposed_only"], subtle_num["cap_both_fail"] + subtle_num["cap_clean_only_fail"]) < 50},
        "strata": strata,
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1))

    for name, b in (("overall", overall), ("numerical", numerical)):
        print(f"{name}: pairs={b['pairs']} classes={b['classes']}")
        print(f"  P(toxic fail | clean ok)={b['p_toxic_fail_given_clean_ok']}  noise floor (clean vs clean, n={b['noise_floor_n']})={b['noise_floor_clean_vs_clean']}  "
              f"toxic-vs-toxic={b['noise_floor_toxic_vs_toxic']}")
        print(f"  excess={b['excess_rate']} CI95={b['excess_rate_ci95_task_clustered']}  McNemar b={b['mcnemar_b_clean_ok_toxic_fail']} c={b['mcnemar_c_clean_fail_toxic_ok']} p={b['mcnemar_p_exact']:.2e}")
        print(f"  observation share raw={b['observation_share_raw']} noise-corrected={b['observation_share_noise_corrected']}")
    print(f"noise floor by model: {summary['noise_floor_by_model']}  reweighted={summary['noise_floor_reweighted_to_pairs']}")
    print(f"same-source-file pairs: {same_source}/{len(rows)}   H6 power: {summary['H6_power']}")
    print(f"G1 (amended): {'PASS' if g1_pass else 'FAIL'}")


if __name__ == "__main__":
    main()
