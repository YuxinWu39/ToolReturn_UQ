"""Shared helpers for the P4 scoring scripts (p4_score_zeroparam.py, p4_score_intrinsic.py).

Added 2026-11-07 after the d0e7ba4 code review found three scoring defects:
  1. zeroparam took df.head(k) from the TIER, not from what the agent actually saw -> `exposure_before`
  2. intrinsic aligned shadow calls to python_exec events by zip after dropping ERROR events -> `completion_after`
  3. within-table AUROC returned NA for a table whose scores are constant with both classes present -> `auc_or_none`
The functions here carry the fixed semantics; test_p4_common.py covers them.
"""
import numpy as np
from sklearn.metrics import roc_auc_score

TIER_ROWS = {"T0_agent": 5, "T1": 5, "T1r2": 5, "T2": 2, "T3": 0}
TIER_MINMAX = {"T0_agent": True, "T1": False, "T1r2": False, "T2": False, "T3": False}


def exposure_before(run, event):
    """What the agent had actually been shown before `event` fired.

    Returns {"rows": max rows exposed by any earlier preview call (head is a prefix, so max = cumulative),
             "minmax": whether any earlier preview carried numeric_min/max,
             "n_preview": number of earlier preview calls}.
    Rows is 0 when the agent never called preview before the event (then no row-based check is computable).
    """
    rows, minmax, n = 0, False, 0
    for e in run["tool_events"]:
        if e["step"] >= event["step"]:
            break
        if e["tool_name"] != "preview":
            continue
        n += 1
        pe = e.get("preview_exposure")
        if pe is None:  # pre-fix trajectories without the exposure record: fall back to the tier cap
            pe = {"rows_exposed": TIER_ROWS.get(run.get("tier"), 0), "minmax": TIER_MINMAX.get(run.get("tier"), False)}
        rows = max(rows, int(pe.get("rows_exposed", 0)))
        minmax = minmax or bool(pe.get("minmax", False))
    return {"rows": rows, "minmax": minmax, "n_preview": n}


def completion_after(run, event):
    """The completion generated right after `event`'s observation.

    Every tool event yields exactly one observation and exactly one completion whose `after_observation` is set
    (parse-error retries carry after_observation=None), so the i-th such completion follows the i-th tool event,
    ERROR observations included. `after_observation.n_tool_turns` is NOT usable as a key: it counts assistant turns,
    which parse-error retries inflate. Returns None when there is no such completion (step cap) or the tool recorded
    on it does not match the event's tool (alignment broken -> treat as missing rather than guess).
    """
    followers = [c for c in run.get("completions", []) if c.get("after_observation")]
    pos = [i for i, e in enumerate(run["tool_events"]) if e["step"] == event["step"]]
    if len(pos) != 1 or pos[0] >= len(followers):
        return None
    c = followers[pos[0]]
    return c if c["after_observation"].get("tool") == event["tool_name"] else None


def auc_or_none(h, label_col, score_col):
    """AUROC on rows with a score. None only when a class is missing or there are no scored rows;
    0.5 when both classes are present but every score is identical (no ranking information)."""
    h = h.dropna(subset=[score_col])
    if len(h) == 0 or h[label_col].nunique() < 2:
        return None
    if h[score_col].nunique() < 2:
        return 0.5
    return float(roc_auc_score(h[label_col], h[score_col]))


def within_table(g, score_col, label_col="label", table_col="dataset", boot=2000, seed=1):
    """Equal-weight mean of per-table AUROC + table-bootstrap percentile CI. Returns (mean, [lo, hi], n_tables)."""
    per = [auc_or_none(x, label_col, score_col) for _, x in g.groupby(table_col)]
    per = [p for p in per if p is not None]
    if not per:
        return None, None, 0
    rs = np.random.default_rng(seed)
    bs = [np.mean(rs.choice(per, len(per), replace=True)) for _ in range(boot)]
    return float(np.mean(per)), [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], len(per)


def paired_tasks(R, score_col, task_col="task_id", label_col="label"):
    """Task ids that have a non-null score for BOTH labels (the 'same-task pairing' claim's denominator)."""
    h = R.dropna(subset=[score_col])
    both = h.groupby(task_col)[label_col].nunique()
    return set(both[both == 2].index)


def fmt(x):
    return "  NA " if x is None else f"{x:.3f}"


def fmt_ci(ci):
    return "" if ci is None else "[%.2f, %.2f]" % tuple(ci)
