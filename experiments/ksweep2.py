#!/usr/bin/env python3
"""A-P3c + A-P3d: information vs estimator. Draws the k visible rows per (table, k, draw) with a fixed seed and adds the
population oracle 0o (A-P3c, "not achievable"), the draw-conditioned oracle 0o* (A-P3d), the registered
log-form 0r, sanity rows for every reference, the estimator-loss / oracle-knowledge decomposition with
table-level CIs, T0_agent components, and B / floor sensitivities.

    python ksweep2.py [--draws 20] [--boot 50] [--oracle-m 300] [--out ../data/ours/ksweep2]
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from common import REPO
from zeroparam import (FastTemplate, bootstrap_0d, interval_score, oracle_law, range_score, reference_0r_log,
                       rule_0a, score_0o, score_0o_star, template_stat)

REFS = ("0a", "0d", "0o", "0o_star", "0r_log")

KS = [5, 10, 20, 50, 100, 200]


def auc(df, key, label="label"):
    g = df.dropna(subset=[key])
    return None if g[label].nunique() < 2 else float(roc_auc_score(g[label], g[key]))


def per_table(df, key):
    return {d: a for d, g in df.groupby("dataset") for a in [auc(g, key)] if a is not None}


def paired_ci_tables(df, a, b, boot=2000, seed=0):
    """CI of mean over tables of (AUROC_a - AUROC_b), bootstrap over the 6 tables."""
    pa, pb = per_table(df, a), per_table(df, b)
    tables = [t for t in pa if t in pb]
    diffs = np.array([pa[t] - pb[t] for t in tables])
    if len(diffs) == 0:
        return None
    rng = np.random.default_rng(seed)
    means = [float(np.mean(rng.choice(diffs, len(diffs), replace=True))) for _ in range(boot)]
    return {"mean_diff": float(diffs.mean()), "ci95_tables": [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))], "n_tables": len(tables)}


def paired_ci_table_draw(df, a, b, boot=1000, seed=0):
    g = df.dropna(subset=[a, b])
    clusters = g.groupby(["dataset", "draw"]).indices
    keys = list(clusters)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(boot):
        pick = rng.choice(len(keys), len(keys), replace=True)
        idx = np.concatenate([clusters[keys[i]] for i in pick])
        s = g.iloc[idx]
        aa, bb = auc(s, a), auc(s, b)
        if aa is not None and bb is not None:
            vals.append(aa - bb)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def decide(ci, ref="0o_star"):
    """A-P3d decision on the table-level CI of (ref - 0d)."""
    if ci is None:
        return "undecidable"
    lo, hi = ci
    if lo >= -0.05 and hi <= 0.05:
        return f"information limit ({ref} ~ 0d)"
    if lo > 0.05:
        return f"estimator loss ({ref} >> 0d): achievable bar = {ref}"
    if hi < -0.05:
        return f"artefact (0d > {ref})"
    return "undecided"


def sanity_values(full_vals, op, n):
    """A-P3b/A-P3d sanity rows: 10 whole-column spans outside the column, times n for sum-type."""
    if full_vals is None:
        return None
    fv = full_vals[~np.isnan(full_vals)]
    if len(fv) == 0:
        return None
    span = fv.max() - fv.min() + 1.0
    hi, lo = fv.max() + 10 * span, fv.min() - 10 * span
    if op == "sum":
        hi, lo = hi * n, lo * n
    return {"s_hi": hi, "s_lo": lo}


def sanity_auc(df, key):
    """AUROC of clean vs each sanity kind; None if the reference is undefined on the sanity rows."""
    out = {}
    clean = df[df.kind == "clean"].assign(label=0)
    for kind in ("s_hi", "s_lo"):
        s = df[df.kind == kind].assign(label=1)
        out[kind] = auc(pd.concat([clean, s]), key)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tasks", type=Path, default=REPO / "data" / "ours" / "tasks" / "large_tables_v2.jsonl")
    parser.add_argument("--out", type=Path, default=REPO / "data" / "ours" / "ksweep2")
    parser.add_argument("--draws", type=int, default=20)
    parser.add_argument("--boot", type=int, default=50)
    parser.add_argument("--oracle-m", type=int, default=300)
    parser.add_argument("--seed", type=int, default=20261031)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    tasks = [json.loads(l) for l in args.tasks.open() if l.strip()]
    frames = {n: pd.read_csv(REPO / "data" / "ours" / "datasets" / n) for n in {t["dataset"] for t in tasks}}
    draws = {}
    for name, df in frames.items():
        for k in KS:
            if k < len(df):
                for d in range(args.draws):
                    draws[(name, k, d)] = rng.choice(len(df), k, replace=False)

    rows, sens_rows = [], []
    for t in tasks:
        df, m, o = frames[t["dataset"]], t["meta"], t["oracle"]
        n = len(df)
        fg = bool(m["filter"] or m["group"])
        fast = FastTemplate(df, m["op"], m["column"], m["filter"], m["group"])
        fn = template_stat(m["op"], m["column"], m["filter"], m["group"])
        sum_type = m["op"] in ("sum", "count")
        full_vals = pd.to_numeric(df[m["column"]], errors="coerce").values if m["column"] else None
        base = {"task_id": t["task_id"], "dataset": t["dataset"], "template": m["template"], "op": m["op"],
                "severity": m["severity_logratio"], "direction": "up" if t["poison"]["scale"] > 1 else "down"}
        ys = {"clean": o["clean_value"], "poisoned": o["poisoned_value"]}
        sv = sanity_values(full_vals, m["op"], n)
        for k in KS:
            if k >= n:
                continue
            law = oracle_law(fast, k, args.oracle_m, rng, o["clean_value"])
            dist = law[3] if law is not None else None
            for d in range(args.draws):
                idx = draws[(t["dataset"], k, d)]
                vis = df.iloc[idx]
                vals = pd.to_numeric(vis[m["column"]], errors="coerce").values if m["column"] else None
                iv = bootstrap_0d(fn, vis, n, args.boot, rng, scale_sum=sum_type)
                theta_hat = fast.on_subset(idx)  # the observed draw's statistic (0d rules, n/k scaled)
                targets = [(0, "clean", ys["clean"]), (1, "poisoned", ys["poisoned"])]
                if sv is not None:
                    targets += [(1, "s_hi", sv["s_hi"]), (1, "s_lo", sv["s_lo"])]
                for label, name, y in targets:
                    so, su = score_0o(y, dist)
                    sso, ssu = score_0o_star(y, theta_hat, law)
                    rows.append({**base, "k": k, "draw": d, "label": label, "kind": name,
                                 "0a": rule_0a(m["op"], y, vals, n) if (vals is not None or m["op"] == "count") else None,
                                 "0d": interval_score(y, iv), "0o": su, "0o_signed": so, "0o_star": ssu, "0o_star_signed": sso,
                                 "0r_log": reference_0r_log(m["op"], y, vals, k, fg)})
                if k in (5, 20) and d < 5:  # sensitivities: B=500 and floor variants on the same draw
                    iv500 = bootstrap_0d(fn, vis, n, 500, rng, scale_sum=sum_type)
                    for label, name in ((0, "clean"), (1, "poisoned")):
                        y = ys[name]
                        sens_rows.append({**base, "k": k, "draw": d, "label": label,
                                          "0d_B50": interval_score(y, iv), "0d_B500": interval_score(y, iv500),
                                          "0d_floor0": None if iv is None else range_score(y, iv[0], iv[1], floor=0.0),
                                          "0d_floor001": None if iv is None else range_score(y, iv[0], iv[1], floor=0.001),
                                          "0d_floor01": None if iv is None else range_score(y, iv[0], iv[1], floor=0.01)})
        # T0_agent components (A-P3d: reported as two columns, never recombined): 0a whole-column [min,max], 0d head-5
        head = df.head(5)
        hv = pd.to_numeric(head[m["column"]], errors="coerce").values if m["column"] else None
        iv_h = bootstrap_0d(fn, head, n, args.boot, rng, scale_sum=sum_type)
        for label, name in ((0, "clean"), (1, "poisoned"), (1, "s_hi"), (1, "s_lo")):
            if name in ("s_hi", "s_lo"):
                if sv is None:
                    continue
                y = sv[name]
            else:
                y = ys[name]
            rows.append({**base, "k": "T0_agent", "draw": 0, "label": label, "kind": name,
                         "c0a": rule_0a(m["op"], y, full_vals, n) if (full_vals is not None or m["op"] == "count") else None,
                         "c0d": interval_score(y, iv_h)})

    df_rows = pd.DataFrame(rows)
    kall = df_rows[df_rows.k != "T0_agent"].copy()
    kall["k"] = kall["k"].astype(int)
    kall.to_json(args.out / "events.jsonl", orient="records", lines=True)
    kcurve = kall[kall.kind.isin(["clean", "poisoned"])].copy()  # real rows; sanity rows kept in kall

    wt = lambda pt: float(np.mean(list(pt.values()))) if pt else None
    summary = {"draws": args.draws, "boot": args.boot, "oracle_m": args.oracle_m, "k": {}, "T0_agent": {}, "sensitivity": {}}
    for k, g in kcurve.groupby("k"):
        gall = kall[kall.k == k]
        common = g.dropna(subset=["0d", "0o_star"])  # A-P3d common support
        unf = common[(common.template == "unfiltered") & common.op.isin(["mean", "median"])].dropna(subset=["0r_log"])
        block = {"n_rows": int(len(g)), "common_support_frac": float(len(common) / len(g)),
                 "sanity": {s: sanity_auc(gall, s) for s in REFS},
                 "all_support": {s: {"auroc": auc(g, s), "within_table": wt(per_table(g, s))} for s in REFS},
                 "common_support": {s: {"auroc": auc(common, s), "within_table": wt(per_table(common, s)),
                                        "by_direction": {dn: auc(gd, s) for dn, gd in common.groupby("direction")},
                                        "by_template": {tn: auc(gt, s) for tn, gt in common.groupby("template")},
                                        "by_op": {on: auc(go, s) for on, go in common.groupby("op")}} for s in REFS},
                 "estimator_loss_0ostar_minus_0d": {"tables": paired_ci_tables(common, "0o_star", "0d"), "table_draw_ci": paired_ci_table_draw(common, "0o_star", "0d"),
                                                     "by_template": {tn: paired_ci_tables(gt, "0o_star", "0d") for tn, gt in common.groupby("template")}},
                 "oracle_knowledge_0o_minus_0ostar": {"tables": paired_ci_tables(common, "0o", "0o_star"), "table_draw_ci": paired_ci_table_draw(common, "0o", "0o_star")},
                 "legacy_0o_minus_0d_tables": paired_ci_tables(common, "0o", "0d"),
                 "unfiltered_mean_median": {"n_rows": int(len(unf)), **{s: auc(unf, s) for s in ("0d", "0r_log", "0o_star", "0o")},
                                            "0ostar_minus_0d": paired_ci_tables(unf, "0o_star", "0d"), "0ostar_minus_0r_log": paired_ci_tables(unf, "0o_star", "0r_log")}}
        block["withheld"] = [s for s in REFS if any(v is not None and v < 0.95 for v in block["sanity"][s].values())]
        el = block["estimator_loss_0ostar_minus_0d"]["tables"]
        block["decision_A-P3d"] = decide(el["ci95_tables"] if el else None)
        summary["k"][int(k)] = block
    # common-support-at-every-k curve (tasks computable at all k) -- primary per A-P3c/A-P3d
    ok_tasks = set.intersection(*[set(g.dropna(subset=["0d", "0o_star"])["task_id"]) for _, g in kcurve.groupby("k")])
    summary["tasks_computable_at_every_k"] = len(ok_tasks)
    summary["curve_common_tasks"] = {int(k): {s: {"auroc": auc(g[g.task_id.isin(ok_tasks)], s), "within_table": wt(per_table(g[g.task_id.isin(ok_tasks)], s))} for s in ("0d", "0r_log", "0o_star", "0o")}
                                     for k, g in kcurve.groupby("k")}

    # T0_agent: two component columns, each with its own sanity (A-P3d)
    t0 = df_rows[df_rows.k == "T0_agent"].copy()
    real = t0[t0.kind.isin(["clean", "poisoned"])]
    summary["T0_agent"] = {"component_0a_full_minmax": {"auroc": auc(real, "c0a"), "within_table": wt(per_table(real, "c0a")), "sanity": sanity_auc(t0, "c0a")},
                           "component_0d_head5": {"auroc": auc(real, "c0d"), "within_table": wt(per_table(real, "c0d")), "sanity": sanity_auc(t0, "c0d")}}
    for comp in summary["T0_agent"].values():
        comp["withheld"] = any(v is not None and v < 0.95 for v in comp["sanity"].values())

    sens = pd.DataFrame(sens_rows)
    for k, g in sens.groupby("k"):
        summary["sensitivity"][int(k)] = {c: {"auroc": auc(g, c), "clean_fp": float((g[g.label == 0][c].dropna() > 0).mean())} for c in ("0d_B50", "0d_B500", "0d_floor0", "0d_floor001", "0d_floor01")}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1, default=float))

    f = lambda x: "  NA " if x is None else f"{x:.3f}"
    print("k    common | 0d    0r_log 0o*   0o   (common support, pooled) | within-table 0d/0o* | 0o*-0d mean [tables CI] | 0o-0o* mean | decision | withheld")
    for k, b in summary["k"].items():
        c, el, ok = b["common_support"], b["estimator_loss_0ostar_minus_0d"]["tables"], b["oracle_knowledge_0o_minus_0ostar"]["tables"]
        print(f"{k:<4d} {b['common_support_frac']:.2f}   | {f(c['0d']['auroc'])} {f(c['0r_log']['auroc'])} {f(c['0o_star']['auroc'])} {f(c['0o']['auroc'])} | "
              f"{f(c['0d']['within_table'])}/{f(c['0o_star']['within_table'])} | {el['mean_diff']:+.3f} [{el['ci95_tables'][0]:+.3f},{el['ci95_tables'][1]:+.3f}] | "
              f"{ok['mean_diff']:+.3f} | {b['decision_A-P3d']} | {b['withheld']}")
    print("by template, 0o*-0d mean [tables CI]:")
    for k, b in summary["k"].items():
        print(f"  k={k}:", {tn: (round(v["mean_diff"], 3), [round(x, 3) for x in v["ci95_tables"]]) if v else None for tn, v in b["estimator_loss_0ostar_minus_0d"]["by_template"].items()})
    print("unfiltered mean/median (0d / 0r_log / 0o* / 0o; 0o*-0d CI; 0o*-0r_log CI):")
    for k, b in summary["k"].items():
        u = b["unfiltered_mean_median"]
        print(f"  k={k} n={u['n_rows']}: {f(u['0d'])} / {f(u['0r_log'])} / {f(u['0o_star'])} / {f(u['0o'])};",
              [round(x, 3) for x in u["0ostar_minus_0d"]["ci95_tables"]] if u["0ostar_minus_0d"] else None,
              [round(x, 3) for x in u["0ostar_minus_0r_log"]["ci95_tables"]] if u["0ostar_minus_0r_log"] else None)
    print("sanity (s_hi, s_lo) per reference per k:")
    for k, b in summary["k"].items():
        print(f"  k={k}:", {s: tuple(f(v) for v in b["sanity"][s].values()) for s in REFS})
    print("common-support curve (tasks computable at every k):", summary["tasks_computable_at_every_k"],
          {k: {s: (round(v["auroc"], 3), round(v["within_table"], 3) if v["within_table"] else None) for s, v in d.items() if v["auroc"] is not None} for k, d in summary["curve_common_tasks"].items()})
    print("T0_agent components:", json.dumps(summary["T0_agent"], default=lambda x: round(x, 3) if isinstance(x, float) else x))
    print("sensitivity:", json.dumps(summary["sensitivity"], indent=None, default=lambda x: round(x, 3) if isinstance(x, float) else x))


if __name__ == "__main__":
    main()
