#!/usr/bin/env python3
"""Step 0: verify the ToxicBench fields the plan depends on and inventory what we actually have.

    python inventory.py                      # prints a report, writes results/inventory.json
    python inventory.py --strict             # exit 1 if any required field is missing

No model, no GPU. Reads data/toxicbench/toxictool_bench/{results,tasks,datasets}.
"""

import argparse
import collections
import csv
import glob
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TB = REPO / "data" / "toxicbench" / "toxictool_bench"
RESULTS = TB / "results"
TASKS = TB / "tasks"
DATASETS = TB / "datasets"

RUN_FIELDS = {"task_id", "family", "dataset", "adapter", "model", "environment", "poison", "tool_events", "final_answer", "metrics"}
EVENT_FIELDS = {"step", "tool_name", "args", "clean_observation", "returned_observation", "was_poisoned", "poison_type"}
SMOKE = re.compile(r"smoke|local-", re.I)


def run_id(path, index):
    return f"{path.stem}#{index}"


def iter_runs(include_smoke=False):
    """Yield (run_id, record) for every trajectory in results/*.jsonl, skipping rescored copies."""
    for path in sorted(RESULTS.glob("*.jsonl")):
        if ".rescored" in path.name:
            continue
        with path.open() as handle:
            for index, line in enumerate(handle):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "tool_events" not in record:
                    continue
                if not include_smoke and SMOKE.search(str(record.get("model", ""))):
                    continue
                if "adapter" not in record:  # 64 early-July runs: <ts>_<adapter>_<model>_both.jsonl
                    m = re.match(r"\d{8}-\d{6}_(.+)_[^_]+_both$", path.stem)
                    record["adapter"] = m.group(1) if m else None
                    record["adapter_from_filename"] = True
                yield run_id(path, index), record


def table_sizes():
    sizes = {}
    for path in DATASETS.glob("*.csv"):
        with path.open(newline="") as handle:
            sizes[path.name] = sum(1 for _ in csv.reader(handle)) - 1
    return sizes


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--out", type=Path, default=REPO / "experiments" / "results" / "inventory.json")
    args = parser.parse_args()

    missing_run, missing_event = collections.Counter(), collections.Counter()
    runs = 0
    by = {k: collections.Counter() for k in ("environment", "family", "model", "adapter", "tool_name", "poison_type")}
    events = poisoned = 0
    tasks, datasets = set(), set()
    pair_key = collections.defaultdict(set)  # (task, adapter, model) -> {environments}
    preview_has_minmax = collections.Counter()

    for rid, r in iter_runs():
        runs += 1
        missing_run.update(RUN_FIELDS - set(r))
        for k in ("environment", "family", "model", "adapter"):
            by[k][r.get(k)] += 1
        tasks.add(r["task_id"])
        datasets.add(r.get("dataset"))
        pair_key[(r["task_id"], r.get("adapter"), r.get("model"))].add(r.get("environment"))
        for e in r["tool_events"]:
            events += 1
            missing_event.update(EVENT_FIELDS - set(e))
            by["tool_name"][e.get("tool_name")] += 1
            if e.get("was_poisoned"):
                poisoned += 1
                by["poison_type"][e.get("poison_type")] += 1
            if e.get("tool_name") == "preview":
                preview_has_minmax["numeric_min" in str(e.get("returned_observation", ""))] += 1

    complete_pairs = sum(1 for envs in pair_key.values() if {"clean", "toxic"} <= envs)
    sizes = table_sizes()
    rows = sorted(sizes.values())
    median_rows = rows[len(rows) // 2] if rows else None

    task_files = {p.name: sum(1 for l in p.open() if l.strip()) for p in TASKS.glob("*.jsonl")}

    report = {
        "runs": runs,
        "tasks_seen_in_results": len(tasks),
        "datasets_seen_in_results": len(datasets),
        "events": events,
        "poisoned_events": poisoned,
        "pair_keys": len(pair_key),
        "complete_clean_toxic_pairs": complete_pairs,
        "preview_calls_with_minmax": dict(preview_has_minmax),
        "table_rows": dict(sorted(sizes.items(), key=lambda kv: kv[1])),
        "table_rows_median": median_rows,
        "tables_le_12_rows": sum(n <= 12 for n in rows),
        "task_files": task_files,
        "by": {k: dict(v.most_common()) for k, v in by.items()},
        "missing_run_fields": dict(missing_run),
        "missing_event_fields": dict(missing_event),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1))

    print(f"runs={runs} tasks={len(tasks)} datasets={len(datasets)} events={events} poisoned={poisoned}")
    print(f"pair keys (task,adapter,model)={len(pair_key)}  complete clean+toxic pairs={complete_pairs}")
    print(f"environment={report['by']['environment']}")
    print(f"models={report['by']['model']}")
    print(f"preview calls with numeric_min/max={dict(preview_has_minmax)}")
    print(f"tables={len(sizes)} median_rows={median_rows} tables<=12 rows={report['tables_le_12_rows']}")
    print(f"poison types={report['by']['poison_type']}")
    print(f"missing run fields={dict(missing_run) or 'none'}  missing event fields={dict(missing_event) or 'none'}")
    print(f"wrote {args.out}")
    if args.strict and (missing_run or missing_event):
        sys.exit(1)


if __name__ == "__main__":
    main()
