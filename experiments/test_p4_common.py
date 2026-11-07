#!/usr/bin/env python3
"""Unit tests for p4_common.py (the 2026-11-07 scoring fixes). Exit 1 on any failure.

    python test_p4_common.py
"""
import sys
import pandas as pd

from p4_common import auc_or_none, completion_after, exposure_before, paired_tasks, within_table


def _run(events, completions=(), tier="T1"):
    return {"tier": tier, "tool_events": events, "completions": list(completions)}


def _ev(step, tool, obs="1.0", **extra):
    return {"step": step, "tool_name": tool, "returned_observation": obs, **extra}


def _comp(step, tool="python_exec", conf=80):
    # n_tool_turns deliberately wrong: alignment must not rely on it (it counts assistant turns incl. parse retries)
    return {"after_observation": {"tool": tool, "n_tool_turns": step + 7}, "verbalized": {"confidence": conf}}


def test_exposure():
    ok = True
    # no preview before the event -> 0 rows, no min/max
    r = _run([_ev(1, "python_exec")])
    ok &= exposure_before(r, r["tool_events"][0]) == {"rows": 0, "minmax": False, "n_preview": 0}
    # preview(5) with min/max then python_exec -> 5 rows, minmax True
    r = _run([_ev(1, "preview", "..", preview_exposure={"rows_exposed": 5, "minmax": True}), _ev(2, "python_exec")], tier="T0_agent")
    ok &= exposure_before(r, r["tool_events"][1]) == {"rows": 5, "minmax": True, "n_preview": 1}
    # preview AFTER the event does not count
    r = _run([_ev(1, "python_exec"), _ev(2, "preview", "..", preview_exposure={"rows_exposed": 5, "minmax": False})])
    ok &= exposure_before(r, r["tool_events"][0])["rows"] == 0
    # two previews: cumulative = max rows exposed
    r = _run([_ev(1, "preview", "..", preview_exposure={"rows_exposed": 2, "minmax": False}),
              _ev(2, "preview", "..", preview_exposure={"rows_exposed": 5, "minmax": False}), _ev(3, "python_exec")])
    ok &= exposure_before(r, r["tool_events"][2]) == {"rows": 5, "minmax": False, "n_preview": 2}
    # legacy preview event without the exposure record -> tier cap
    r = _run([_ev(1, "preview", ".."), _ev(2, "python_exec")], tier="T2")
    ok &= exposure_before(r, r["tool_events"][1])["rows"] == 2
    print("exposure_before:", "PASS" if ok else "FAIL")
    return ok


def test_alignment():
    ok = True
    # ERROR at step 1, poisoned scalar at step 2: the completion for step 2 must be chosen, not step 1's
    r = _run([_ev(1, "python_exec", "ERROR: IndentationError"), _ev(2, "python_exec", "1508850.0", was_poisoned=True)],
             [{"after_observation": None}, _comp(1, conf=50), _comp(2, conf=95)])
    c = completion_after(r, r["tool_events"][1])
    ok &= c is not None and c["verbalized"]["confidence"] == 95
    # parse-error retry between observations (the Qwen3-8B pattern): a retry completion with after_observation=None
    # sits between the preview's follower and the python_exec's follower and must be skipped
    r = _run([_ev(1, "preview", ".."), _ev(2, "python_exec", "326.0", was_poisoned=True)],
             [{"after_observation": None}, _comp(1, tool="preview", conf=None), {"after_observation": None}, _comp(2, conf=95)])
    c = completion_after(r, r["tool_events"][1])
    ok &= c is not None and c["verbalized"]["confidence"] == 95
    # event with no following completion (step cap) -> None
    r = _run([_ev(1, "python_exec")], [{"after_observation": None}])
    ok &= completion_after(r, r["tool_events"][0]) is None
    # tool mismatch at the aligned position -> None (never silently take a preview's completion)
    r = _run([_ev(1, "python_exec")], [_comp(1, tool="preview")])
    ok &= completion_after(r, r["tool_events"][0]) is None
    print("completion_after:", "PASS" if ok else "FAIL")
    return ok


def test_auc():
    ok = True
    # constant scores, both classes present -> 0.5 (not NA)
    h = pd.DataFrame({"label": [0, 0, 1, 1], "s": [80, 80, 80, 80]})
    ok &= auc_or_none(h, "label", "s") == 0.5
    # one class missing -> NA
    h = pd.DataFrame({"label": [1, 1], "s": [80, 90]})
    ok &= auc_or_none(h, "label", "s") is None
    # all scores missing -> NA
    h = pd.DataFrame({"label": [0, 1], "s": [None, None]})
    ok &= auc_or_none(h, "label", "s") is None
    # perfect separation -> 1.0
    h = pd.DataFrame({"label": [0, 0, 1, 1], "s": [1, 2, 3, 4]})
    ok &= auc_or_none(h, "label", "s") == 1.0
    # within_table: a constant table contributes 0.5 and is counted
    g = pd.DataFrame({"dataset": ["A"] * 4 + ["B"] * 4, "label": [0, 0, 1, 1] * 2, "s": [80, 80, 80, 80, 1, 2, 3, 4]})
    m, ci, n = within_table(g, "s", boot=10)
    ok &= n == 2 and abs(m - 0.75) < 1e-9
    # paired_tasks: only tasks with a score for both labels
    R = pd.DataFrame({"task_id": ["t1", "t1", "t2", "t3", "t3"], "label": [0, 1, 0, 0, 1], "s": [1, 2, 3, None, 5]})
    ok &= paired_tasks(R, "s") == {"t1"}
    print("auc_or_none / within_table / paired_tasks:", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    results = [test_exposure(), test_alignment(), test_auc()]
    print("ALL PASS" if all(results) else "FAILURES")
    sys.exit(0 if all(results) else 1)
