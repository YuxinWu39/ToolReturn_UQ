#!/usr/bin/env python3
"""P4 agent-intrinsic signals (A-P4 H1): signal 1 token entropy and signal 3 shadow verbalized confidence, on the
completion that FOLLOWS each python_exec observation. Positives = poisoned scalar python_exec observations (toxic run);
negatives = the matching python_exec observation in the clean seed-0 run of the same task. Score direction: higher =
more suspicious (entropy as-is; verbalized confidence negated). Within-table AUROC primary; historical subtle and plausible+subtle rules conflict.
See A-REVISION-CACHED and audit_cached_revision.py; printed metrics are diagnostics, not H1 decisions.   python p4_score_intrinsic.py --agent qwen3-4b --tier T1r2

2026-11-07 fix: the completion is matched to its tool event by its ordinal among all tool observations, including ERRORs
(n_tool_turns counts assistant turns and is not an event key), instead of zipping a list that had ERROR events removed against
one that had not. The scored event must itself be a single-number observation (same rule as the zero-parameter scorer).
"""
import argparse, json, re
import numpy as np, pandas as pd
from common import REPO
from p4_common import completion_after, auc_or_none, within_table, paired_tasks, fmt, fmt_ci

NUM = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")

def is_scalar(text):
    return len(NUM.findall(text or "")) == 1

def target_event(run, want_poisoned):
    """First non-ERROR scalar python_exec event (poisoned one when want_poisoned), with its following completion.
    Returns (event, completion, reason); completion None with a reason when it cannot be aligned."""
    for e in run["tool_events"]:
        if e["tool_name"] != "python_exec" or e["returned_observation"].startswith("ERROR") or not is_scalar(e["returned_observation"]):
            continue
        if want_poisoned is not None and bool(e["was_poisoned"]) != want_poisoned:
            continue
        c = completion_after(run, e)
        return e, c, (None if c is not None else "no_completion_for_step")
    return None, None, "no_scalar_event"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--agent", default="qwen3-4b"); ap.add_argument("--tier", default="T1r2"); a = ap.parse_args()
    d = REPO / "data/ours/p4" / a.agent / a.tier
    load = lambda f: {r["task_id"]: r for r in map(json.loads, (d / f).open())}
    clean, toxic = load("clean_seed0.jsonl"), load("toxic_seed0.jsonl")
    tasks = {t["task_id"]: t for t in map(json.loads, (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}
    rows, missing = [], {}
    for tid, t in tasks.items():
        for label, run, want in ((0, clean.get(tid), None), (1, toxic.get(tid), True)):
            if run is None: continue
            e, c, why = target_event(run, want)
            if e is None or c is None:
                missing[why] = missing.get(why, 0) + 1; continue
            v = (c.get("verbalized") or {}).get("confidence")
            if v is not None and not (0 <= v <= 100):
                missing["confidence_out_of_range"] = missing.get("confidence_out_of_range", 0) + 1; v = None
            rows.append({"task_id": tid, "dataset": t["dataset"], "template": t["meta"]["template"], "severity": t["meta"]["severity_logratio"], "label": label,
                         "step": e["step"], "errors_before": sum(1 for x in run["tool_events"] if x["step"] < e["step"] and x["returned_observation"].startswith("ERROR")),
                         "verbalized_conf": v, "sig3_neg_conf": None if v is None else -v,
                         "sig1_first_token_entropy": c.get("first_token_entropy"), "sig1_mean_entropy": c.get("mean_entropy"),
                         "sig1_max_entropy": c.get("max_entropy"), "sig1_neg_sum_logprob": None if c.get("sum_logprob") is None else -c["sum_logprob"],
                         "n_tokens": c.get("n_tokens")})
    R = pd.DataFrame(rows); R.to_json(d / "intrinsic_scores.jsonl", orient="records", lines=True)
    auc = lambda g, c: auc_or_none(g, "label", c)
    ps = R[R.severity.isin(["plausible", "subtle"])]
    print(f"{a.agent} {a.tier}: {len(R)} events (pos {int(R.label.sum())}); verbalized present {R.verbalized_conf.notna().mean():.2f}; "
          f"events preceded by an ERROR step {int((R.errors_before>0).sum())}; unscorable {missing}")
    print("verbalized confidence: clean mean %.1f, poisoned mean %.1f; distribution clean %s poisoned %s" % (
        R[R.label==0].verbalized_conf.mean(), R[R.label==1].verbalized_conf.mean(),
        R[R.label==0].verbalized_conf.value_counts().head(4).to_dict(), R[R.label==1].verbalized_conf.value_counts().head(4).to_dict()))
    print("signal                     pooled  within [CI] (tables)   | paired within [CI] (n tasks) | plaus+subtle within [CI] (diagnostics; no live sanity)")
    for c in ("sig3_neg_conf", "sig1_first_token_entropy", "sig1_mean_entropy", "sig1_max_entropy", "sig1_neg_sum_logprob"):
        w, ci, nt = within_table(R, c); wp, cip, _ = within_table(ps, c)
        pt = paired_tasks(R, c); wq, ciq, _ = within_table(R[R.task_id.isin(pt)], c)
        verdict = "H1 decision withheld: protocol-version conflict / no live sanity"
        print(f"{c:26s} {fmt(auc(R,c))}   {fmt(w)} {fmt_ci(ci)} ({nt})   | {fmt(wq)} {fmt_ci(ciq)} ({len(pt)})   | {fmt(wp)} {fmt_ci(cip)}  {verdict}")
    sev = {}
    for sv, g in R[R.label == 1].groupby("severity"):
        h = pd.concat([g, R[(R.label == 0) & R.task_id.isin(g.task_id)]])
        sev[sv] = (fmt(auc(h, 'sig3_neg_conf')).strip(), fmt(auc(h, 'sig1_mean_entropy')).strip(), len(g))
    print("by severity (sig3 / mean-entropy / n pos; clean controls = same tasks):", sev)

if __name__ == "__main__":
    main()
