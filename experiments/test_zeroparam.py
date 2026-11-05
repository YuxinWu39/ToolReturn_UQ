#!/usr/bin/env python3
"""A-P3d unit tests for the shared zero-parameter implementation.

    python test_zeroparam.py            # is_sum_type cases + FastTemplate/template_stat alignment (300 subsets/task)
    python test_zeroparam.py --subsets 1000

Exit 1 on any failure. The alignment part reads data/ours/tasks/large_tables_v2.jsonl.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from common import REPO
from gen_tasks import template_code
from zeroparam import FastTemplate, is_sum_type, rule_0a, template_stat

SUM_TYPE_CASES = {
    # (code, expected)
    "len(df[df['species'] == 'Adelie'])": True,
    "df[df['species'] == 'Adelie']['bill_length_mm'].count()": True,
    "round(df['x'].mean(), 2)": False,
    "df.groupby('g')['x'].sum().max()": True,              # P3 grouped template (round-5 c)
    "df.groupby('g')['x'].count().max()": True,
    "df.groupby('g')['x'].mean().max()": False,
    "df.groupby('g')['x'].size().idxmax()": True,
    "df['x'].sum().round(2)": True,                          # method-form wrapper
    "df['x'].mean().round(2)": False,
    "total = df['x'].sum()\nprint(total)": True,             # print(name) after assignment
    "m = df['x'].mean()\nprint(round(m, 1))": False,
    "df.shape[0]": True,
    "print(df.shape[0])": True,
    "df['x'].max()": False,
    "df['x'].median()": False,
    "df['g'].value_counts().max()": True,
    "df['g'].nunique()": False,                              # round-6: count-distinct does not scale as n/k
    "len(df['x'].unique())": False,                          # round-6
    "df.groupby('g')['x'].mean().sum()": False,              # round-6: sum over location statistics
    "df.groupby('g')['x'].sum().sum()": True,
    "df['x'].count() / len(df)": False,
    "df.groupby('g').size().max()": True,
    "x = 3\nprint(x)": False,
    "": False,
    "this is not python": False,
}


def test_sum_type():
    bad = [(c, e, is_sum_type(c)) for c, e in SUM_TYPE_CASES.items() if is_sum_type(c) != e]
    for c, e, got in bad:
        print(f"FAIL is_sum_type({c!r}) = {got}, expected {e}")
    print(f"is_sum_type: {len(SUM_TYPE_CASES) - len(bad)}/{len(SUM_TYPE_CASES)} passed")
    return not bad


def test_0a_sum_bound():
    # filtered sum over 44% of rows with min/mean = 0.64: the old bound n*min flagged the clean answer
    vals = np.array([2.0, 3.0, 4.0]); n = 100
    y_clean_filtered_sum = 44 * 3.0  # 132 < n*min = 200 under the old rule
    sc = rule_0a("sum", y_clean_filtered_sum, vals, n)
    ok = sc == 0.0
    print(f"0a sum bound: clean filtered sum {y_clean_filtered_sum} -> score {sc} ({'ok' if ok else 'FAIL'})")
    return ok


def test_alignment(subsets, seed=7):
    tasks = [json.loads(l) for l in (REPO / "data" / "ours" / "tasks" / "large_tables_v2.jsonl").open() if l.strip()]
    frames = {n: pd.read_csv(REPO / "data" / "ours" / "datasets" / n) for n in {t["dataset"] for t in tasks}}
    rng = np.random.default_rng(seed)
    mismatches, checked, both_none = 0, 0, 0
    examples = []
    for t in tasks:
        df, m = frames[t["dataset"]], t["meta"]
        n = len(df)
        fast = FastTemplate(df, m["op"], m["column"], m["filter"], m["group"])
        fn = template_stat(m["op"], m["column"], m["filter"], m["group"])
        sum_type = m["op"] in ("sum", "count")
        # the generated template code must agree with is_sum_type
        if is_sum_type(template_code(m["op"], m["column"], m["filter"], m["group"])) != sum_type:
            mismatches += 1
            examples.append(("is_sum_type vs template", t["task_id"]))
        for k in (5, 20):
            if k >= n:
                continue
            for _ in range(subsets // 2):
                idx = rng.choice(n, k, replace=False)
                a = fast.on_subset(idx)
                b = fn(df.iloc[idx].reset_index(drop=True))
                if b is not None and not (isinstance(b, float) and math.isnan(b)) and sum_type:
                    b = b * n / k
                checked += 1
                a_none = a is None or (isinstance(a, float) and math.isnan(a))
                b_none = b is None or (isinstance(b, float) and math.isnan(b))
                if a_none and b_none:
                    both_none += 1
                    continue
                if a_none != b_none or not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9):
                    mismatches += 1
                    if len(examples) < 10:
                        examples.append((t["task_id"], k, a, b))
    print(f"alignment: {checked} subset evaluations, {both_none} both-undefined, {mismatches} mismatches")
    for e in examples:
        print("  mismatch:", e)
    return mismatches == 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--subsets", type=int, default=300)
    args = ap.parse_args()
    ok = test_sum_type() & test_0a_sum_bound() & test_alignment(args.subsets)
    print("ALL PASS" if ok else "FAILURES")
    sys.exit(0 if ok else 1)
