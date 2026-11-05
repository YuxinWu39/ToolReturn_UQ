#!/usr/bin/env python3
"""P5 step 1: assemble the clean-return training set for the C3 scorer and the P4 evaluation events.

Training examples (CLEAN returns only, never from a toxic run):
  (a) ToxicBench scalar python_exec events, clean_observation parsable as one number (any agent, any run)
  (b) P4 clean-run scalar python_exec events (all tiers / seeds / agents under data/ours/p4)
Evaluation examples: P4 events as scored by p4_score_zeroparam.py (poisoned event vs matched clean event), with
labels, so the scorer can be compared on exactly the same rows as 0d / 0o*.

    python build_dataset.py            -> data/ours/scorer/train.jsonl, eval_<agent>_<tier>.jsonl, stats
Each row: {text, t (signed log10 target), y, table, source, task_id, tier, agent, label}
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

from common import REPO, iter_runs

OUT = REPO / "data" / "ours" / "scorer"
NUM = re.compile(r"-?\d+(?:\.\d+)?(?:e-?\d+)?")
P3_TABLES = {t["dataset"] for t in (json.loads(l) for l in (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}


def scalar(text):
    nums = NUM.findall(text or "")
    return float(nums[0]) if len(nums) == 1 else None


def signed_log(y):
    return math.copysign(math.log10(1 + abs(y)), y)


def normalize_code(code):
    lines = code.split("\n")
    if len(lines) > 1 and not lines[0].startswith((" ", "\t")) and all(l.startswith(" ") and not l.startswith("  ") for l in lines[1:] if l.strip()):
        code = "\n".join([lines[0]] + [l[1:] if l.startswith(" ") else l for l in lines[1:]])
    code = "\n".join(l for l in code.split("\n") if not re.match(r"^\s*import\s+pandas(\s+as\s+pd)?\s*$", l))
    return re.sub(r"pd\.read_csv\(\s*['\"][^'\"]+\.csv['\"]\s*\)", "df", code)


def make_text(query, code, preview):
    pv = (preview or "(none)").strip()
    if len(pv) > 2500:
        pv = pv[:2500] + "\n..."
    return f"QUERY: {query.strip()}\nCODE: {normalize_code(code).strip()}\nPREVIEW: {pv}"


def events_from_run(run, query, want_poisoned):
    """Yield (event, preview_text_seen_before_it, y) for scalar python_exec events of the run."""
    preview = None
    for e in run["tool_events"]:
        if e["tool_name"] == "preview":
            preview = e["returned_observation"]
            continue
        if e["tool_name"] != "python_exec" or e["returned_observation"].startswith("ERROR"):
            continue
        if want_poisoned is not None and bool(e["was_poisoned"]) != want_poisoned:
            continue
        y = scalar(e["clean_observation"] if not want_poisoned else e["returned_observation"])
        if y is None:
            continue
        yield e, preview, y
        if want_poisoned is not None:
            return


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train, stats = [], Counter()
    # (a) ToxicBench clean returns (clean_observation is the true value even in toxic runs; P5 excludes toxic runs anyway)
    tb_tasks = {}
    for tf in (REPO / "data/toxicbench/toxictool_bench/tasks").glob("*.jsonl"):
        for l in tf.open():
            if l.strip():
                t = json.loads(l); tb_tasks[t["task_id"]] = t
    seen = set()
    for _run_id, run in iter_runs():
        if run.get("environment") != "clean":
            continue
        task = tb_tasks.get(run["task_id"])
        if not task:
            stats["tb_no_task"] += 1; continue
        for e, preview, y in events_from_run(run, task["user_query"], None):
            key = (run["task_id"], normalize_code(e["args"].get("code", "")), "tb")
            if key in seen:
                stats["tb_dedup"] += 1; continue
            seen.add(key)
            train.append({"text": make_text(task["user_query"], e["args"].get("code", ""), preview), "t": signed_log(y), "y": y,
                          "table": task["dataset"], "source": "toxicbench", "task_id": run["task_id"], "tier": "T0_agent", "agent": run.get("model"), "label": 0})
            stats["tb_train"] += 1
    # (b) P4 clean runs + evaluation files
    p3 = {t["task_id"]: t for t in (json.loads(l) for l in (REPO / "data/ours/tasks/large_tables_v2.jsonl").open())}
    for agent_dir in sorted((REPO / "data/ours/p4").glob("*")):
        for tier_dir in sorted(agent_dir.glob("*")):
            files = {f.stem: f for f in tier_dir.glob("*.jsonl") if f.stem.startswith(("clean_", "toxic_"))}
            if not files:
                continue
            for name, f in files.items():
                if not name.startswith("clean_"):
                    continue
                for run in map(json.loads, f.open()):
                    task = p3[run["task_id"]]
                    for e, preview, y in events_from_run(run, task["user_query"], None):
                        key = (run["task_id"], normalize_code(e["args"].get("code", "")), tier_dir.name)
                        if key in seen:
                            stats["p4_dedup"] += 1; continue
                        seen.add(key)
                        train.append({"text": make_text(task["user_query"], e["args"].get("code", ""), preview), "t": signed_log(y), "y": y,
                                      "table": task["dataset"], "source": "p4_clean", "task_id": run["task_id"], "tier": tier_dir.name, "agent": agent_dir.name, "label": 0})
                        stats[f"p4_train_{agent_dir.name}_{tier_dir.name}"] += 1
            # evaluation rows: poisoned event (toxic) vs matched first clean scalar event (clean seed 0)
            if "clean_seed0" in files and "toxic_seed0" in files:
                clean = {r["task_id"]: r for r in map(json.loads, files["clean_seed0"].open())}
                toxic = {r["task_id"]: r for r in map(json.loads, files["toxic_seed0"].open())}
                ev = []
                for tid, task in p3.items():
                    for label, run, want in ((0, clean.get(tid), None), (1, toxic.get(tid), True)):
                        if run is None: continue
                        for e, preview, y in events_from_run(run, task["user_query"], want):
                            ev.append({"text": make_text(task["user_query"], e["args"].get("code", ""), preview), "t": signed_log(y), "y": y,
                                       "table": task["dataset"], "source": "p4_eval", "task_id": tid, "tier": tier_dir.name, "agent": agent_dir.name,
                                       "label": label, "severity": task["meta"]["severity_logratio"], "template": task["meta"]["template"]})
                            break
                (OUT / f"eval_{agent_dir.name}_{tier_dir.name}.jsonl").write_text("\n".join(json.dumps(r) for r in ev) + "\n")
                stats[f"eval_{agent_dir.name}_{tier_dir.name}"] = len(ev)
    (OUT / "train.jsonl").write_text("\n".join(json.dumps(r) for r in train) + "\n")
    by_table = Counter(r["table"] for r in train)
    stats["train_total"] = len(train)
    stats["train_p3_tables"] = {t: by_table[t] for t in sorted(P3_TABLES)}
    stats["train_tb_tables"] = len([t for t in by_table if t not in P3_TABLES])
    (OUT / "stats.json").write_text(json.dumps(stats, indent=1, default=str))
    print(json.dumps(stats, indent=1, default=str))


if __name__ == "__main__":
    main()
