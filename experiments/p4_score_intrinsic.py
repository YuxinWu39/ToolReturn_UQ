#!/usr/bin/env python3
"""P4 agent-intrinsic signals (A-P4 H1): signal 1 token entropy and signal 3 shadow verbalized confidence, on the
completion that FOLLOWS each python_exec observation. Positives = poisoned scalar python_exec observations (toxic run);
negatives = the matching python_exec observation in the clean seed-0 run of the same task. Score direction: higher =
more suspicious (entropy as-is; verbalized confidence negated). Within-table AUROC primary; H1 statistic = upper 95% CI
(6-table bootstrap) on plausible+subtle.   python p4_score_intrinsic.py --agent qwen3-4b --tier T1r2
"""
import argparse, json
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import REPO

def events_with_completion(run, want_poisoned):
    """Yield (event, completion) pairs: the completion whose after_observation follows this python_exec event."""
    comps = run.get("completions", [])
    # completion j (j>=1) follows tool event j (1-based step) in a clean ReAct loop; align by order of python_exec observations
    obs_calls = [c for c in comps if c.get("after_observation") and c["after_observation"].get("tool") == "python_exec"]
    pe = [e for e in run["tool_events"] if e["tool_name"] == "python_exec" and not e["returned_observation"].startswith("ERROR")]
    for e, c in zip(pe, obs_calls):
        if want_poisoned is None or bool(e["was_poisoned"]) == want_poisoned:
            yield e, c
            return

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--agent", default="qwen3-4b"); ap.add_argument("--tier", default="T1r2"); a = ap.parse_args()
    d = REPO / "data/ours/p4" / a.agent / a.tier
    load = lambda f: {r["task_id"]: r for r in map(json.loads, (d / f).open())}
    clean, toxic = load("clean_seed0.jsonl"), load("toxic_seed0.jsonl")
    tasks = {t["task_id"]: t for t in map(json.loads, (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}
    rows = []
    for tid, t in tasks.items():
        for label, run, want in ((0, clean.get(tid), None), (1, toxic.get(tid), True)):
            if run is None: continue
            for e, c in events_with_completion(run, want):
                v = (c.get("verbalized") or {}).get("confidence")
                rows.append({"task_id": tid, "dataset": t["dataset"], "template": t["meta"]["template"], "severity": t["meta"]["severity_logratio"], "label": label,
                             "verbalized_conf": v, "sig3_neg_conf": None if v is None else -v,
                             "sig1_first_token_entropy": c.get("first_token_entropy"), "sig1_mean_entropy": c.get("mean_entropy"),
                             "sig1_max_entropy": c.get("max_entropy"), "sig1_neg_sum_logprob": None if c.get("sum_logprob") is None else -c["sum_logprob"],
                             "n_tokens": c.get("n_tokens")})
    R = pd.DataFrame(rows); R.to_json(d / "intrinsic_scores.jsonl", orient="records", lines=True)
    auc = lambda g, c: (lambda h: None if h.label.nunique() < 2 or h[c].nunique() < 2 else float(roc_auc_score(h.label, h[c])))(g.dropna(subset=[c]))
    def within(g, c, boot=2000):
        per = [auc(x, c) for _, x in g.groupby("dataset")]; per = [p for p in per if p is not None]
        if not per: return None, None
        rs = np.random.default_rng(1); bs = [np.mean(rs.choice(per, len(per), replace=True)) for _ in range(boot)]
        return float(np.mean(per)), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    f = lambda x: "  NA " if x is None else f"{x:.3f}"
    ps = R[R.severity.isin(["plausible", "subtle"])]
    print(f"{a.agent} {a.tier}: {len(R)} events (pos {int(R.label.sum())}); verbalized present {R.verbalized_conf.notna().mean():.2f}")
    print("verbalized confidence: clean mean %.1f, poisoned mean %.1f; distribution clean %s poisoned %s" % (
        R[R.label==0].verbalized_conf.mean(), R[R.label==1].verbalized_conf.mean(),
        R[R.label==0].verbalized_conf.value_counts().head(4).to_dict(), R[R.label==1].verbalized_conf.value_counts().head(4).to_dict()))
    print("signal                     pooled  within [CI]           | plausible+subtle within [CI]  -> H1 (upper < 0.60?)")
    for c in ("sig3_neg_conf", "sig1_first_token_entropy", "sig1_mean_entropy", "sig1_max_entropy", "sig1_neg_sum_logprob"):
        w, ci = within(R, c); wp, cip = within(ps, c)
        verdict = "" if cip is None else ("H1 PASS" if cip[1] < 0.60 else "H1 FAIL")
        print(f"{c:26s} {f(auc(R,c))}   {f(w)} {['%.2f'%x for x in ci] if ci else ''}   | {f(wp)} {['%.2f'%x for x in cip] if cip else ''}  {verdict}")
    print("by severity (sig3 / mean-entropy):", {sv: (f(auc(pd.concat([g, R[R.label==0]]), 'sig3_neg_conf')), f(auc(pd.concat([g, R[R.label==0]]), 'sig1_mean_entropy'))) for sv, g in R[R.label==1].groupby("severity")})

if __name__ == "__main__":
    main()
