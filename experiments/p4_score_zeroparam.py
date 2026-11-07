#!/usr/bin/env python3
"""P4 zero-parameter signals on REAL agent events (A-P4 / A-P3d): 0a (visible range), 0d (bootstrap re-execution of the
agent's own code on the rows the agent saw), 0o* (draw-conditioned oracle, template statistic on the same rows), 0r_log.
Positives = poisoned scalar python_exec events in toxic runs; negatives = the matching scalar python_exec event in the
clean seed-0 run of the same task. Within-table AUROC primary, pooled secondary; table-bootstrap CI.
Since 2026-11-07 the rows/min-max used by every check are the ones the agent was ACTUALLY shown before the scored event
(reconstructed from the preceding preview events); --exposure protocol restores the tier-cap reading.
    python p4_score_zeroparam.py --agent qwen3-4b --tier T1
"""
import argparse, json, math, re
import numpy as np, pandas as pd
from common import REPO
from p4_common import TIER_ROWS, TIER_MINMAX, exposure_before, auc_or_none, within_table, paired_tasks, fmt, fmt_ci
from gen_tasks import sandbox_exec
from zeroparam import FastTemplate, bootstrap_0d, interval_score, is_sum_type, oracle_law, reference_0r_log, rule_0a, score_0o_star

NUM = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")

def scalar(text):
    nums = NUM.findall(text or "")
    return float(nums[0]) if len(nums) == 1 else None

def normalize_agent_code(code):
    """Same normalizations the P4 sandbox applied at run time (A-P4 note), so re-execution sees the code the agent ran."""
    lines = code.split("\n")
    if len(lines) > 1 and not lines[0].startswith((" ", "\t")) and all(l.startswith(" ") and not l.startswith("  ") for l in lines[1:] if l.strip()):
        code = "\n".join([lines[0]] + [l[1:] if l.startswith(" ") else l for l in lines[1:]])
    code = "\n".join(l for l in code.split("\n") if not re.match(r"^\s*import\s+pandas(\s+as\s+pd)?\s*$", l))
    code = re.sub(r"pd\.read_csv\(\s*['\"][^'\"]+\.csv['\"]\s*\)", "df.copy()", code)
    return code


def first_scalar_event(run, poisoned=None):
    for e in run["tool_events"]:
        if e["tool_name"] != "python_exec" or e["returned_observation"].startswith("ERROR"):
            continue
        if poisoned is not None and bool(e["was_poisoned"]) != poisoned:
            continue
        y = scalar(e["returned_observation"])
        if y is not None:
            return e, y
    return None, None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--agent", default="qwen3-4b"); ap.add_argument("--tier", default="T1")
    ap.add_argument("--boot", type=int, default=50); ap.add_argument("--oracle-m", type=int, default=300); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--exposure", choices=["actual", "protocol"], default="actual",
                    help="actual (default): rows/min-max the agent was really shown before the scored event (0 rows -> NA). "
                         "protocol: the tier cap for every event (pre-2026-11-07 behaviour; system-level reading).")
    a = ap.parse_args(); rng = np.random.default_rng(a.seed)
    d = REPO / "data" / "ours" / "p4" / a.agent / a.tier
    load = lambda f: {r["task_id"]: r for r in (json.loads(l) for l in (d / f).open())}
    clean, toxic = load("clean_seed0.jsonl"), load("toxic_seed0.jsonl")
    tasks = {t["task_id"]: t for t in (json.loads(l) for l in (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}
    frames = {n: pd.read_csv(REPO / "data/ours/datasets" / n) for n in {t["dataset"] for t in tasks.values()}}
    k_tier, minmax_tier = TIER_ROWS[a.tier], TIER_MINMAX[a.tier]
    rows = []
    for tid, t in tasks.items():
        df = frames[t["dataset"]]; n = len(df); m = t["meta"]
        fast = FastTemplate(df, m["op"], m["column"], m["filter"], m["group"])
        law_cache = {}
        for label, run, want in ((0, clean.get(tid), None), (1, toxic.get(tid), True)):
            if run is None: continue
            e, y = first_scalar_event(run, want)
            if e is None: continue
            ex = exposure_before(run, e)
            k, minmax = (ex["rows"], ex["minmax"]) if a.exposure == "actual" else (k_tier, minmax_tier)
            vis = df.head(k); idx = np.arange(k)
            vals = pd.to_numeric(vis[m["column"]], errors="coerce").values if (k > 0 and m["column"]) else None
            # 0a: whole-column numeric_min/max only if the preview the agent saw actually carried it
            vals_0a = pd.to_numeric(df[m["column"]], errors="coerce").values if (minmax and m["column"]) else vals
            if k > 0 and k not in law_cache:
                law_cache[k] = (oracle_law(fast, k, a.oracle_m, rng, t["oracle"]["clean_value"]), fast.on_subset(idx))
            law, theta_hat = law_cache.get(k, (None, None))
            code = normalize_agent_code(e["args"].get("code", ""))
            def stat(sample, code=code):
                out = sandbox_exec(code, sample); return None if out is None else scalar(out)
            iv = bootstrap_0d(stat, vis, n, a.boot, rng, scale_sum=is_sum_type(code)) if k > 0 else None
            so, su = score_0o_star(y, theta_hat, law) if k > 0 else (None, None)
            can_0a = (minmax or k > 0) and (vals_0a is not None or m["op"] == "count")
            rows.append({"task_id": tid, "dataset": t["dataset"], "template": m["template"], "op": m["op"], "severity": m["severity_logratio"], "label": label, "y": y,
                         "k_rows": k, "minmax_seen": minmax, "n_preview": ex["n_preview"], "exposure_mode": a.exposure,
                         "0a": rule_0a(m["op"], y, vals_0a, n) if can_0a else None,
                         "0d": interval_score(y, iv), "0o_star": su, "0r_log": reference_0r_log(m["op"], y, vals, k, bool(m["filter"] or m["group"])) if k > 0 else None,
                         "sum_type": is_sum_type(code)})
    R = pd.DataFrame(rows); R.to_json(d / f"zeroparam_scores{'' if a.exposure == 'actual' else '_protocol'}.jsonl", orient="records", lines=True)
    auc = lambda g, c: auc_or_none(g, "label", c)
    print(f"{a.agent} {a.tier} [exposure={a.exposure}]: events scored {len(R)} (pos {int(R.label.sum())}, neg {int((R.label==0).sum())}); "
          f"events with 0 rows shown {int((R.k_rows==0).sum())}, with min/max {int(R.minmax_seen.sum())}")
    print("signal   coverage  pooled  within-table [CI] (tables) | paired-task within [CI] (n tasks) | plaus+subtle pooled/within")
    ps = R[R.severity.isin(["plausible", "subtle"])]
    for c in ("0a", "0d", "0o_star", "0r_log"):
        w, ci, nt = within_table(R, c); wp, _, _ = within_table(ps, c)
        pt = paired_tasks(R, c); Rp = R[R.task_id.isin(pt)]; wq, ciq, _ = within_table(Rp, c)
        print(f"{c:8s} {R[c].notna().mean():.2f}      {fmt(auc(R,c))}   {fmt(w)} {fmt_ci(ci)} ({nt})   | {fmt(wq)} {fmt_ci(ciq)} ({len(pt)})   | {fmt(auc(ps,c))}/{fmt(wp)}")
    print("by template (0d / 0o*):", {tn: (fmt(auc(g,'0d')).strip(), fmt(auc(g,'0o_star')).strip()) for tn, g in R.groupby("template")})
    # severity: positives of that severity vs the clean events of the SAME tasks
    sev = {}
    for sv, g in R[R.label == 1].groupby("severity"):
        ctl = R[(R.label == 0) & R.task_id.isin(g.task_id)]
        h = pd.concat([g, ctl]); sev[sv] = (fmt(auc(h, '0d')).strip(), fmt(auc(h, '0o_star')).strip(), len(g))
    print("by severity (0d / 0o* / n pos; clean controls = same tasks):", sev)

if __name__ == "__main__":
    main()
