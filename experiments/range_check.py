#!/usr/bin/env python3
"""Step 3 (P2 + amendment A-P2): zero-parameter baselines at context tiers.

  0a range check / 0b z-score  : op-aware, regex-parsed single aggregation (coverage-limited by design)
  0d re-execution              : agent's own code re-run on the visible rows with bootstrap resampling
  sanity rows                  : y:=0 and y:=10y copies of every clean event must be flagged (> 0.95 AUROC)
  T0 check                     : CSV min/max vs the preview event the agent actually received

    python range_check.py --out results/range_check [--boot 2000] [--exec-boot 100] [--limit N]
"""

import argparse
import ast
import collections
import contextlib
import io
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from common import DATASETS_DIR, REPO, infer_severity, iter_runs, load_tasks
from zeroparam import bootstrap_0d, is_sum_type
from zeroparam import interval_score as _zp_interval_score
from zeroparam import rule_0a, rule_0b

EPS = 1e-9
TIERS = {"T0_full": None, "T1_head5": 5, "T2_head2": 2}
OPS = {"mean": "mean", "median": "median", "min": "min", "max": "max", "sum": "sum", "count": "count", "size": "count"}
COL_OP = re.compile(r"""df\s*(?:\[\s*['"]([^'"]+)['"]\s*\]|\.([A-Za-z_]\w*))\s*\.\s*(mean|median|min|max|sum|count|size)\s*\(""")
LEN_DF = re.compile(r"\blen\s*\(\s*df\s*\)")
OUT_OF_SCOPE = re.compile(r"df\s*\[\s*df\s*\[|\.groupby\(|\.loc\[|\.iloc\[|\.query\(|\.where\(|\.nlargest|\.nsmallest|\.sort_values|\.idxmax|\.idxmin")
NUMBER = re.compile(r"(?<![\w.])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?(?![\w.])")
ERROR = re.compile(r"^\s*(ERROR|Traceback)|Error:", re.M)
SAFE_BUILTINS = {k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k) for k in
                 ("__import__", "abs", "bool", "dict", "enumerate", "float", "int", "len", "list", "max", "min", "print",
                  "range", "round", "set", "sorted", "str", "sum", "tuple", "zip")}


def parse_code(code):
    if OUT_OF_SCOPE.search(code):
        return None, "filter_or_groupby"
    pairs = {(OPS[m.group(3)], m.group(1) or m.group(2)) for m in COL_OP.finditer(code)}
    if LEN_DF.search(code):
        pairs.add(("count", None))
    if len(pairs) == 1:
        return pairs.pop(), None
    return None, "no_match" if not pairs else "multiple_aggregations"


def scalar(observation):
    if ERROR.search(observation):
        return None, "error_observation"
    nums = NUMBER.findall(observation)
    if len(nums) != 1:
        return None, "not_single_scalar"
    return float(nums[0].replace(",", "")), None


def sandbox_exec(code, df):
    """ToxicBench python_exec semantics (last expression printed) on a given dataframe. Returns stdout or None."""
    namespace = {"__builtins__": SAFE_BUILTINS, "pd": pd, "df": df.copy()}
    out = io.StringIO()
    try:
        tree = ast.parse(code)
        last = None
        if tree.body and isinstance(tree.body[-1], ast.Expr):
            last = ast.Expression(tree.body[-1].value)
            tree.body = tree.body[:-1]
            ast.fix_missing_locations(tree)
            ast.fix_missing_locations(last)
        with contextlib.redirect_stdout(out):
            if tree.body:
                exec(compile(tree, "<reexec>", "exec"), namespace, namespace)
            if last is not None:
                value = eval(compile(last, "<reexec>", "eval"), namespace, namespace)
                if value is not None:
                    print(value)
    except Exception:
        return None
    return out.getvalue().strip()


class Table:
    def __init__(self, path):
        self.df = pd.read_csv(path)
        self.n = len(self.df)
        self.cache = {}

    def visible(self, column, rows):
        key = (column, rows)
        if key not in self.cache:
            s = pd.to_numeric(self.df[column], errors="coerce").dropna() if column in self.df else None
            self.cache[key] = s if (s is None or rows is None) else s.head(rows)
        return self.cache[key]

    def visible_df(self, rows):
        return self.df if rows is None else self.df.head(rows)


def rule_scores(table, op, column, y, rows):
    """A-P3d: shared zeroparam.rule_0a / rule_0b (0a sum bound [n*min(min,0), n*max(max,0)]; 1% interval floor)."""
    if op == "count":
        return rule_0a("count", y, None, table.n), None
    v = table.visible(column, rows)
    if v is None or len(v) == 0:
        return None, None
    return rule_0a(op, y, v, table.n), rule_0b(op, y, v, table.n)


SUM_TYPE_CALLS_OLD = {"sum", "count", "len", "size", "value_counts", "nunique"}


def is_sum_type_old(code):
    """A-P3c rule (final call only), kept to count how many events the A-P3d rule reclassifies."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    if not tree.body:
        return False
    node = tree.body[-1]
    expr = node.value if isinstance(node, (ast.Expr, ast.Assign)) else None
    while isinstance(expr, ast.Call):
        f = expr.func
        name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", None)
        if name in SUM_TYPE_CALLS_OLD:
            return True
        if name in ("round", "float", "int", "abs", "print"):
            expr = expr.args[0] if expr.args else None
            continue
        return False
    return False


def reexec_interval(code, table, rows, boot, rng):
    """A-P3c: shared bootstrap_0d (resample size = visible rows; sum-type statistics scaled by n/k; > 20% failures
    -> not computable). The statistic is the agent's own code executed in the ToxicBench-equivalent sandbox."""
    vis = table.visible_df(rows)
    if len(vis) == 0:
        return None

    def stat(sample):
        text = sandbox_exec(code, sample)
        return None if text is None else scalar(text)[0]

    return bootstrap_0d(stat, vis, table.n, boot, rng, scale_sum=is_sum_type(code))


def interval_score(y, interval):
    return _zp_interval_score(y, interval)  # A-P3d: shared implementation (1% floor)


def auc_pair(y, s):
    y, s = np.asarray(y, dtype=bool), np.asarray(s, dtype=float)
    if y.sum() == 0 or (~y).sum() == 0:
        return None, None
    return float(roc_auc_score(y, s)), float(average_precision_score(y, s))


def within_table(df, key, boot=2000, seed=0):
    """Mean of per-table AUROCs (tables with >= 5 pos and >= 5 neg) and a bootstrap-over-tables 95% CI."""
    aucs = []
    for _, g in df.dropna(subset=[key]).groupby("dataset"):
        if g["poisoned"].sum() >= 5 and (~g["poisoned"]).sum() >= 5:
            a, _ = auc_pair(g["poisoned"], g[key])
            if a is not None:
                aucs.append(a)
    if not aucs:
        return None, 0, None
    rng = np.random.default_rng(seed)
    means = [float(np.mean(rng.choice(aucs, len(aucs), replace=True))) for _ in range(boot)]
    return float(np.mean(aucs)), len(aucs), [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def clustered_ci(df, key, boot, seed=0):
    df = df.dropna(subset=[key])
    groups = {c: g for c, g in df.groupby("dataset")}
    names = list(groups)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(boot):
        sample = pd.concat([groups[c] for c in rng.choice(names, len(names), replace=True)])
        a, _ = auc_pair(sample["poisoned"], sample[key])
        if a is not None:
            vals.append(a)
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else None


def preview_minmax(observation, column):
    """numeric_min/max for a column from a preview event's DATASET SUMMARY line, or None."""
    for line in observation.splitlines():
        if line.startswith("{") and "numeric_min" in line:
            try:
                s = json.loads(line)
                return s["numeric_min"].get(column), s["numeric_max"].get(column)
            except (json.JSONDecodeError, KeyError, AttributeError):
                return None
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=REPO / "experiments" / "results" / "range_check")
    parser.add_argument("--boot", type=int, default=2000, help="clustered bootstrap resamples for CIs")
    parser.add_argument("--exec-boot", type=int, default=100, help="bootstrap resamples for 0d re-execution")
    parser.add_argument("--limit", type=int, default=0, help="debug: stop after N in-scope-for-0d events")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    tasks = load_tasks()
    tables, rows, skipped = {}, [], collections.Counter()
    preview_check = collections.Counter()
    t_start = time.time()
    for rid, r in iter_runs():
        if r.get("family") != "numerical":
            continue
        severity = infer_severity(tasks.get(r["task_id"], r))
        ds = r["dataset"]
        if ds not in tables:
            path = DATASETS_DIR / ds
            if not path.exists():
                skipped[("all", "missing_csv")] += 1
                continue
            tables[ds] = Table(path)
        table = tables[ds]
        preview_obs = next((e["clean_observation"] for e in r["tool_events"] if e.get("tool_name") == "preview"), None)
        for e in r["tool_events"]:
            if e.get("tool_name") != "python_exec":
                continue
            cls = "poisoned" if e.get("was_poisoned") else "clean"
            code = str(e.get("args", {}).get("code", ""))
            y, why = scalar(e["returned_observation"])
            if y is None:
                skipped[(cls, why)] += 1
                continue
            parsed, reason = parse_code(code)
            row = {"run_id": rid, "step": e["step"], "task_id": r["task_id"], "adapter": r["adapter"], "model": r["model"],
                   "dataset": ds, "table_rows": table.n, "poisoned": cls == "poisoned", "poison_type": e.get("poison_type"),
                   "severity": severity, "y": y, "rule_scope": parsed is not None, "rule_skip_reason": reason,
                   "op": parsed[0] if parsed else None, "column": parsed[1] if parsed else None}
            if parsed:
                op, column = parsed
                if column is not None and column not in table.df:
                    row["rule_scope"], row["rule_skip_reason"] = False, "column_not_in_csv"
                else:
                    for tier, k in TIERS.items():
                        a, b = rule_scores(table, op, column, y, k)
                        row[f"0a_{tier}"], row[f"0b_{tier}"] = a, b
                    if column is not None and preview_obs:
                        mm = preview_minmax(preview_obs, column)
                        if mm and mm[0] is not None:
                            v = table.visible(column, None)
                            preview_check["match" if abs(float(mm[0]) - float(v.min())) < 1e-6 and abs(float(mm[1]) - float(v.max())) < 1e-6 else "MISMATCH"] += 1
                        else:
                            preview_check["no_column_in_preview"] += 1
                    elif column is not None:
                        preview_check["no_preview_event"] += 1
            # 0d: re-execute the agent's code on visible rows, any code shape allowed
            full_out = sandbox_exec(code, table.df)
            full_val = scalar(full_out)[0] if full_out is not None else None
            row["0d_scope"] = full_val is not None
            row["sum_type"] = is_sum_type(code)
            row["sum_type_old_rule"] = is_sum_type_old(code)
            if full_val is not None:
                for tier, k in TIERS.items():
                    iv = reexec_interval(code, table, k, args.exec_boot, rng)
                    row[f"0d_{tier}"] = interval_score(y, iv)
                    row[f"0d_lo_{tier}"], row[f"0d_hi_{tier}"] = (None, None) if iv is None else iv
            rows.append(row)
            if args.limit and sum(x["0d_scope"] for x in rows) >= args.limit:
                break
        if args.limit and sum(x["0d_scope"] for x in rows) >= args.limit:
            break
    elapsed = time.time() - t_start

    with (args.out / "events.jsonl").open("w") as sink:
        for row in rows:
            sink.write(json.dumps(row) + "\n")
    df = pd.DataFrame(rows)

    def evaluate(frame, key, label):
        sub = frame.dropna(subset=[key])
        auroc, auprc = auc_pair(sub["poisoned"], sub[key]) if len(sub) else (None, None)
        wt, ntab, wt_ci = within_table(sub, key, args.boot)
        out = {"n": int(len(sub)), "n_pos": int(sub["poisoned"].sum()), "auroc": auroc, "auprc": auprc,
               "auroc_ci95_cluster_dataset": clustered_ci(sub, key, args.boot) if len(sub) else None,
               "within_table_auroc": wt, "within_table_n_tables": ntab, "within_table_ci95_table_bootstrap": wt_ci}
        for axis in ("poison_type", "severity"):
            per = {}
            for val, grp in sub[sub["poisoned"]].groupby(axis):
                mixed = pd.concat([grp, sub[~sub["poisoned"]]])
                per[val] = {"n_pos": int(len(grp)), "auroc": auc_pair(mixed["poisoned"], mixed[key])[0]}
            out[f"per_{axis}"] = per
        return out

    primary = df[df["severity"].isin(["plausible", "subtle"]) | ~df["poisoned"]]  # plan's primary slice
    summary = {"python_exec_events_total": int(len(df)) + sum(v for (c, _), v in skipped.items() if c != "all"),
               "scored_events": int(len(df)), "skipped": {f"{c}:{w}": n for (c, w), n in sorted(skipped.items())},
               "rule_scope": {"clean": int((df["rule_scope"] & ~df["poisoned"]).sum()), "poisoned": int((df["rule_scope"] & df["poisoned"]).sum())},
               "reexec_scope": {"clean": int((df["0d_scope"] & ~df["poisoned"]).sum()), "poisoned": int((df["0d_scope"] & df["poisoned"]).sum())},
               "reexec_scored_T1": {"clean": int((df["0d_T1_head5"].notna() & ~df["poisoned"]).sum()), "poisoned": int((df["0d_T1_head5"].notna() & df["poisoned"]).sum()),
                                    "poisoned_dropped_nan": int((df["0d_scope"] & df["poisoned"] & df["0d_T1_head5"].isna()).sum())},
               "rule_skip_reasons_poisoned": dict(collections.Counter(df[df["poisoned"] & ~df["rule_scope"]]["rule_skip_reason"])),
               "preview_T0_check": dict(preview_check), "elapsed_seconds": round(elapsed, 1), "exec_boot": args.exec_boot,
               "pooled": {}, "primary_slice_plausible_subtle": {}, "sanity": {}}
    for tier in TIERS:
        for sig in ("0a", "0b", "0d"):
            key = f"{sig}_{tier}"
            if key in df:
                summary["pooled"][key] = evaluate(df, key, key)
                summary["primary_slice_plausible_subtle"][key] = evaluate(primary, key, key)
    # sanity rows: clean events with y := 0 and y := 10y must be separable from real clean events
    clean = df[~df["poisoned"] & df["rule_scope"]].copy()
    for name, factor in (("y_zero", 0.0), ("y_times_10", 10.0)):
        fake = clean.copy()
        fake["poisoned"] = True
        for tier, k in TIERS.items():
            fake[f"0a_{tier}"] = [rule_scores(tables[d], o, c, factor * y, k)[0] for d, o, c, y in zip(fake["dataset"], fake["op"], fake["column"], fake["y"])]
            fake[f"0b_{tier}"] = [rule_scores(tables[d], o, c, factor * y, k)[1] for d, o, c, y in zip(fake["dataset"], fake["op"], fake["column"], fake["y"])]
        mixed = pd.concat([clean, fake])
        summary["sanity"][name] = {f"0a_{tier}": auc_pair(mixed["poisoned"], mixed[f"0a_{tier}"].fillna(0))[0] for tier in TIERS}
        summary["sanity"][name].update({f"0b_{tier}": auc_pair(mixed.dropna(subset=[f"0b_{tier}"])["poisoned"], mixed.dropna(subset=[f"0b_{tier}"])[f"0b_{tier}"])[0] for tier in TIERS})
        clean_d = df[~df["poisoned"] & df["0d_scope"]].copy()
        fake_d = clean_d.copy(); fake_d["poisoned"] = True
        for tier in TIERS:
            lo, hi = f"0d_lo_{tier}", f"0d_hi_{tier}"
            fake_d[f"0d_{tier}"] = [None if pd.isna(l) else interval_score(factor * y, (l, h)) for l, h, y in zip(fake_d[lo], fake_d[hi], fake_d["y"])]
        mixed_d = pd.concat([clean_d, fake_d])
        summary["sanity"][name].update({f"0d_{tier}": auc_pair(mixed_d.dropna(subset=[f"0d_{tier}"])["poisoned"], mixed_d.dropna(subset=[f"0d_{tier}"])[f"0d_{tier}"])[0] for tier in TIERS})
    scope_df = df[df["0d_scope"]]
    summary["sum_type_rule_change_A-P3d"] = {"events_in_0d_scope": int(len(scope_df)),
                                             "reclassified": int((scope_df["sum_type"] != scope_df["sum_type_old_rule"]).sum()),
                                             "now_sum_type": int(scope_df["sum_type"].sum()), "old_sum_type": int(scope_df["sum_type_old_rule"].sum())}
    summary["G2"] = {"status": "undecidable-on-original-tables (A-P2)", "max_table_rows_in_rule_scope": int(df[df["rule_scope"]]["table_rows"].max()) if df["rule_scope"].any() else None,
                     "0a_T1_aggregate_scale_pooled": summary["pooled"].get("0a_T1_head5", {}).get("per_poison_type", {}).get("aggregate_scale", {}).get("auroc"),
                     "0a_T1_aggregate_scale_primary_slice": summary["primary_slice_plausible_subtle"].get("0a_T1_head5", {}).get("per_poison_type", {}).get("aggregate_scale", {}).get("auroc")}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=1))

    print(f"events scored={len(df)} (of {summary['python_exec_events_total']} python_exec)  elapsed={elapsed:.0f}s  skipped={summary['skipped']}")
    print(f"rule scope={summary['rule_scope']}  reexec scope={summary['reexec_scope']}  reexec scored T1={summary['reexec_scored_T1']}  poisoned rule-skip reasons={summary['rule_skip_reasons_poisoned']}")
    print(f"preview T0 check: {summary['preview_T0_check']}")
    print("sanity:", summary["sanity"])
    for slice_name in ("pooled", "primary_slice_plausible_subtle"):
        print(f"== {slice_name}")
        for key, b in summary[slice_name].items():
            if b["auroc"] is None:
                print(f"  {key:12s} n={b['n']} pos={b['n_pos']} AUROC=NA"); continue
            print(f"  {key:12s} n={b['n']:5d} pos={b['n_pos']:4d} AUROC={b['auroc']:.3f} CI={[round(x,3) for x in b['auroc_ci95_cluster_dataset']]} AUPRC={b['auprc']:.3f} "
                  f"within-table={None if b['within_table_auroc'] is None else round(b['within_table_auroc'],3)} ({b['within_table_n_tables']}t) "
                  f"sev={{{', '.join(f'{k}:{v['auroc']:.3f}' for k,v in b['per_severity'].items() if v['auroc'] is not None)}}}")
    print("G2:", summary["G2"])
    print("sum-type rule change (A-P3d):", summary["sum_type_rule_change_A-P3d"])


if __name__ == "__main__":
    main()
