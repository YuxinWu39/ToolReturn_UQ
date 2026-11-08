#!/usr/bin/env python3
"""A-REVISION-CACHED: audit saved scores only, never call a model or overwrite inputs."""
import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
import pandas as pd
from cached_metrics import metrics, scorer_summary, slices, join_baselines, common_gain

REPO = Path(__file__).resolve().parents[1]


def run(out):
    sources = {}
    def read(path):
        sources[str(path.relative_to(REPO))] = hashlib.sha256(path.read_bytes()).hexdigest()
        return pd.read_json(path, lines=True)
    tasks = read(REPO / "data/ours/tasks/large_tables_v2.jsonl")
    eligibility = pd.DataFrame([dict(task_id=r.task_id, severity=r.meta["severity_logratio"], template=r.meta["template"])
                                for r in tasks.itertuples()])
    expected = {name: len(g) for name, g in slices(eligibility)}
    result = {"protocol": "A-REVISION-CACHED", "interpretation": "retrospective diagnostic; no new model calls",
              "bootstrap": {"unit": "table", "replicates": 2000, "seed": 1}, "intrinsic": {}, "scorer": {}}
    for path in sorted((REPO / "data/ours/p4").glob("*/*/intrinsic_scores.jsonl")):
        rows = read(path)
        result["intrinsic"][str(path.parent.relative_to(REPO / "data/ours/p4"))] = {
            "efficacy_status": "withheld-no-live-sanity", "h1_status": "not-confirmed-protocol-version-conflict-and-missing-sanity",
            "diagnostics": {name: {s: metrics(g, s, expected[name]) for s in rows if s.startswith("sig")}
                            for name, g in slices(rows)}}
    for path in sorted((REPO / "data/ours/scorer").glob("eval_*_scorer.jsonl")):
        rows = read(path)
        summary = scorer_summary(rows)
        agent, tier = rows.agent.unique(), rows.tier.unique()
        if len(agent) != 1 or len(tier) != 1:
            raise ValueError("mixed agent/tier cache")
        baseline = read(REPO / "data/ours/p4" / agent[0] / tier[0] / "zeroparam_scores.jsonl")
        joined = join_baselines(rows, baseline)
        summary["baseline_join"] = {"scorer_events": len(rows), "baseline_events": len(baseline), "matched_events": len(joined),
                                    "validation": "unique keys + metadata + numerical y; raw code/event identity not proved"}
        summary["registered_gain"] = common_gain(joined, summary["gate_pass"])
        result["scorer"][path.stem] = summary
    result["runtime"] = {"python": platform.python_version(), **{name: version(name) for name in ("numpy", "pandas", "scikit-learn")}}
    result["input_sha256"] = sources
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = ["# Cached-output revision audit", "", "Retrospective diagnostics, not a new confirmatory test. No model calls.", "",
             "AP is average precision. Paired controls use the same task; primary AUROC equally weights tables.", "",
             "## H1 version diagnostics", "", "All intrinsic efficacy headlines withheld: no live sanity controls. Original A-P4 subtle/AP and A-P4b P+S/upper-CI rules differ.", "",
             "| Agent/tier | Signal | Slice | Pairs/eligible | Tables | AUROC [CI] | AP | Base |", "|---|---|---|---:|---:|---|---:|---:|"]
    def f(x): return "NA" if x is None else f"{x:.3f}"
    for name, record in result["intrinsic"].items():
        for sl in ("severity:subtle", "plausible+subtle"):
            for signal in ("sig3_neg_conf", "sig1_mean_entropy"):
                m = record["diagnostics"][sl][signal]
                ci = m["ci95_table_bootstrap"]
                lines.append(f"| {name} | {signal} | {sl} | {m['paired_tasks']}/{m['eligible_tasks']} | {m['tables']} | {f(m['within_auroc'])} {str([round(x,3) for x in ci]) if ci else ''} | {f(m['within_average_precision'])} | {f(m['base_rate'])} |")
    lines += ["", "The balanced-pair base rate is 0.5: AP < 2×base means AP < 1, a weak/non-discriminating criterion. AP aggregation was not fully specified originally.", "",
              "## P5 gates and common support", "", "| Cache | Coverage | High sanity | Low sanity | Constant surprise tables (all) | Common P+S pairs/tables | Gain |", "|---|---:|---:|---:|---:|---|---|"]
    for name, r in result["scorer"].items():
        c = r["registered_gain"]
        lines.append(f"| {name} | {f(r['clean_coverage'])} | {f(r['sanity']['s_hi']['within_auroc'])} | {f(r['sanity']['s_lo']['within_auroc'])} | {r['score_diagnostics']['all']['surprise']['constant_tables']} | {c['common_tasks']}/{c['common_tables']} | {c['status']} |")
    lines += ["", "All rows above are diagnostics. Gate-failed scorer instances cannot establish learned UQ failure or the registered gain. Constant dual-class tables now contribute 0.5; missing-class tables do not.",
              "", "Full JSON includes per table/severity/template metrics, finite paired coverage, pooled secondary metrics, baseline support and input SHA-256. Baseline matching checks cached return and metadata, not full raw event identity.", ""]
    (out / "report.md").write_text("\n".join(lines))
    print("wrote", out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO / "data/ours/revision_cached/20261107")
    run(parser.parse_args().out)
