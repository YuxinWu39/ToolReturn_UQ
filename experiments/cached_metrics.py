"""Finite-score, same-task cached-output diagnostics; no model dependencies."""
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score
from p4_common import auc_or_none


def validate_rows(rows):
    if rows.duplicated(["task_id", "label"]).any():
        raise ValueError("duplicate (task_id,label)")
    if not set(rows.label.unique()) <= {0, 1}:
        raise ValueError("labels must be binary")
    for col in ("dataset", "template", "severity"):
        if rows.groupby("task_id")[col].nunique(dropna=False).gt(1).any():
            raise ValueError(f"inconsistent task metadata: {col}")


def paired(rows, columns):
    validate_rows(rows)
    finite = np.isfinite(rows[columns].astype(float)).all(axis=1)
    valid = rows[finite]
    ids = valid.groupby("task_id").label.nunique()
    return valid[valid.task_id.isin(ids[ids == 2].index)].copy()


def interval(values, boot=2000, seed=1):
    if not len(values):
        return None
    samples = np.random.default_rng(seed).choice(values, (boot, len(values)), replace=True).mean(axis=1)
    return np.percentile(samples, [2.5, 97.5]).tolist()


def metrics(rows, column, eligible_tasks=None):
    """Diagnostic metrics, including ties; callers separately enforce efficacy gates."""
    eligible = rows.task_id.nunique() if eligible_tasks is None else int(eligible_tasks)
    h = paired(rows, [column])
    per = {}
    for table, g in h.groupby("dataset"):
        per[str(table)] = {
            "tasks": int(g.task_id.nunique()),
            "auroc": auc_or_none(g, "label", column),
            "average_precision": float(average_precision_score(g.label, g[column])),
            "base_rate": float(g.label.mean()),
            "constant": bool(g[column].nunique() == 1),
        }
    aucs = [g["auroc"] for g in per.values()]
    aps = [g["average_precision"] for g in per.values()]
    return {
        "eligible_tasks": eligible, "paired_tasks": int(h.task_id.nunique()),
        "paired_task_coverage": float(h.task_id.nunique() / eligible) if eligible else None,
        "tables": len(per), "events": len(h), "per_table": per,
        "within_auroc": float(np.mean(aucs)) if aucs else None,
        "ci95_table_bootstrap": interval(aucs),
        "pooled_auroc": auc_or_none(h, "label", column),
        "within_average_precision": float(np.mean(aps)) if aps else None,
        "pooled_average_precision": float(average_precision_score(h.label, h[column])) if len(h) else None,
        "base_rate": float(h.label.mean()) if len(h) else None,
        "constant_tables": sum(g["constant"] for g in per.values()),
    }


def slices(rows):
    yield "all", rows
    yield "plausible+subtle", rows[rows.severity.isin(["plausible", "subtle"])]
    for column in ("severity", "template"):
        for name, g in rows.groupby(column):
            yield f"{column}:{name}", g


def scorer_summary(rows):
    rows = rows.rename(columns={"table": "dataset"})
    validate_rows(rows)
    clean = rows[rows.label == 0]
    valid = np.isfinite(clean[["t", "q05", "q95"]].astype(float)).all(axis=1)
    c = clean[valid]
    cov = float(((c.t >= c.q05) & (c.t <= c.q95)).mean()) if len(c) else None
    sanity = {}
    for name in ("s_hi", "s_lo"):
        h = pd.concat([clean.assign(label=0, score=clean.surprise), clean.assign(label=1, score=clean[name])])
        sanity[name] = metrics(h, "score", len(clean))
    pass_gate = (cov is not None and 0.80 <= cov <= 0.98 and all(
        s["within_auroc"] is not None and s["within_auroc"] > 0.95 for s in sanity.values()))
    result = {
        "clean_coverage": cov, "clean_predictions": int(valid.sum()), "eligible_clean": len(clean),
        "sanity": sanity, "gate_pass": bool(pass_gate),
        "real_corruption_status": "eligible-for-reporting" if pass_gate else "withheld-gate-failed",
        "score_diagnostics": {},
    }
    # Ungated numerical diagnostics are explicitly not detector-quality headlines.
    for name, g in slices(rows):
        result["score_diagnostics"][name] = {s: metrics(g, s) for s in ("surprise", "epistemic")}
    return result


def join_baselines(rows, baseline):
    """Cache-level match only: keys, metadata and numerical return; not a raw-code identity proof."""
    rows = rows.rename(columns={"table": "dataset"})
    validate_rows(rows)
    validate_rows(baseline)
    cols = ["task_id", "label", "dataset", "template", "severity", "y", "0d", "0r_log"]
    joined = rows.merge(baseline[cols], on=["task_id", "label"], suffixes=("", "_baseline"), validate="one_to_one")
    for col in ("dataset", "template", "severity"):
        if not joined[col].eq(joined[col + "_baseline"]).all():
            raise ValueError(f"baseline metadata mismatch: {col}")
    if not np.isclose(joined.y, joined.y_baseline, rtol=1e-8, atol=1e-8).all():
        raise ValueError("baseline return mismatch")
    return joined


def common_gain(rows, gate_pass):
    ps = rows[rows.severity.isin(["plausible", "subtle"])]
    h = paired(ps, ["surprise", "0d", "0r_log"])
    result = {"eligible_tasks": int(ps.task_id.nunique()), "common_tasks": int(h.task_id.nunique()),
              "common_tables": int(h.dataset.nunique()),
              "status": "computed" if gate_pass else "withheld-scorer-gate-failed",
              "gain": None, "ci95": None}
    if not gate_pass or h.empty:
        if h.empty and gate_pass:
            result["status"] = "withheld-no-common-support"
        return result
    matrix = np.array([[auc_or_none(g, "label", s) for s in ("surprise", "0d", "0r_log")]
                       for _, g in h.groupby("dataset")])
    means = matrix.mean(axis=0)
    draws = matrix[np.random.default_rng(1).integers(len(matrix), size=(2000, len(matrix)))].mean(axis=1)
    differences = draws[:, 0] - np.maximum(draws[:, 1], draws[:, 2])
    result.update(gain=float(means[0] - max(means[1:])), ci95=np.percentile(differences, [2.5, 97.5]).tolist())
    return result
