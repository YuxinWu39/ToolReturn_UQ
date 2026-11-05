#!/usr/bin/env python3
"""P4 zero-parameter signals on REAL agent events (A-P4 / A-P3d): 0a (visible range), 0d (bootstrap re-execution of the
agent's own code on the rows the agent saw), 0o* (draw-conditioned oracle, template statistic on the same rows), 0r_log.
Positives = poisoned scalar python_exec events in toxic runs; negatives = the matching scalar python_exec event in the
clean seed-0 run of the same task. Within-table AUROC primary, pooled secondary; table-bootstrap CI.
    python p4_score_zeroparam.py --agent qwen3-4b --tier T1
"""
import argparse, json, math, re
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import REPO
from gen_tasks import sandbox_exec
from zeroparam import FastTemplate, bootstrap_0d, interval_score, is_sum_type, oracle_law, reference_0r_log, rule_0a, score_0o_star

TIER_ROWS = {"T0_agent": 5, "T1": 5, "T2": 2, "T3": 0}
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
    a = ap.parse_args(); rng = np.random.default_rng(a.seed)
    d = REPO / "data" / "ours" / "p4" / a.agent / a.tier
    load = lambda f: {r["task_id"]: r for r in (json.loads(l) for l in (d / f).open())}
    clean, toxic = load("clean_seed0.jsonl"), load("toxic_seed0.jsonl")
    tasks = {t["task_id"]: t for t in (json.loads(l) for l in (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}
    frames = {n: pd.read_csv(REPO / "data/ours/datasets" / n) for n in {t["dataset"] for t in tasks.values()}}
    k = TIER_ROWS[a.tier]
    rows = []
    for tid, t in tasks.items():
        df = frames[t["dataset"]]; n = len(df); m = t["meta"]
        vis = df.head(k); idx = np.arange(k)
        vals = pd.to_numeric(vis[m["column"]], errors="coerce").values if m["column"] else None
        # T0_agent: the preview carried whole-column numeric_min/max, so 0a uses the whole column (0d/0o*/0r stay on head rows)
        vals_0a = pd.to_numeric(df[m["column"]], errors="coerce").values if (a.tier == "T0_agent" and m["column"]) else vals
        fast = FastTemplate(df, m["op"], m["column"], m["filter"], m["group"])
        law = oracle_law(fast, k, a.oracle_m, rng, t["oracle"]["clean_value"]) if k > 0 else None
        theta_hat = fast.on_subset(idx) if k > 0 else None
        for label, run, want in ((0, clean.get(tid), None), (1, toxic.get(tid), True)):
            if run is None: continue
            e, y = first_scalar_event(run, want)
            if e is None: continue
            code = normalize_agent_code(e["args"].get("code", ""))
            def stat(sample, code=code):
                out = sandbox_exec(code, sample); return None if out is None else scalar(out)
            iv = bootstrap_0d(stat, vis, n, a.boot, rng, scale_sum=is_sum_type(code)) if k > 0 else None
            so, su = score_0o_star(y, theta_hat, law)
            rows.append({"task_id": tid, "dataset": t["dataset"], "template": m["template"], "op": m["op"], "severity": m["severity_logratio"], "label": label, "y": y,
                         "0a": rule_0a(m["op"], y, vals_0a, n) if k > 0 and (vals_0a is not None or m["op"] == "count") else None,
                         "0d": interval_score(y, iv), "0o_star": su, "0r_log": reference_0r_log(m["op"], y, vals, k, bool(m["filter"] or m["group"])) if k > 0 else None,
                         "sum_type": is_sum_type(code)})
    R = pd.DataFrame(rows); R.to_json(d / "zeroparam_scores.jsonl", orient="records", lines=True)
    auc = lambda g, c: (lambda h: None if h.label.nunique() < 2 else float(roc_auc_score(h.label, h[c])))(g.dropna(subset=[c]))
    def within(g, c):
        per = [auc(x, c) for _, x in g.groupby("dataset")]; per = [p for p in per if p is not None]
        if not per: return None, None
        rs = np.random.default_rng(1); bs = [np.mean(rs.choice(per, len(per), replace=True)) for _ in range(2000)]
        return float(np.mean(per)), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
    print(f"{a.agent} {a.tier}: events scored {len(R)} (pos {int(R.label.sum())}, neg {int((R.label==0).sum())})")
    print("signal   coverage  pooled  within-table [CI]      | plausible+subtle pooled/within")
    ps = R[R.severity.isin(["plausible", "subtle"])]
    for c in ("0a", "0d", "0o_star", "0r_log"):
        w, ci = within(R, c); wp, _ = within(ps, c)
        cov = R[c].notna().mean()
        f = lambda x: "  NA " if x is None else f"{x:.3f}"
        print(f"{c:8s} {cov:.2f}      {f(auc(R,c))}   {f(w)} {['%.2f'%x for x in ci] if ci else ''}   | {f(auc(ps,c))}/{f(wp)}")
    print("by template (0d / 0o*):", {tn: (round(auc(g,'0d'),3) if auc(g,'0d') else None, round(auc(g,'0o_star'),3) if auc(g,'0o_star') else None) for tn, g in R.groupby("template")})
    print("by severity (0d / 0o*):", {sv: (round(auc(pd.concat([g, R[R.label==0]]),'0d'),3), round(auc(pd.concat([g, R[R.label==0]]),'0o_star'),3)) for sv, g in R[R.label==1].groupby("severity")})

if __name__ == "__main__":
    main()
