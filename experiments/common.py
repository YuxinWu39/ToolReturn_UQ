"""Shared data access for ToxicBench trajectories. Definitions follow PREREGISTRATION.md P1/P2."""

import collections
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TB = REPO / "data" / "toxicbench" / "toxictool_bench"
RESULTS_DIR = TB / "results"
TASKS_DIR = TB / "tasks"
DATASETS_DIR = TB / "datasets"

SMOKE = re.compile(r"smoke|local-", re.I)
ADAPTER_FAMILIES = ("langgraph", "dataframe_router", "autogen", "smolagents", "pandasai", "da_agent")


def iter_runs():
    """Yield (run_id, record): every non-smoke trajectory, rescored copies skipped, adapter filled."""
    for path in sorted(RESULTS_DIR.glob("*.jsonl")):
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
                if "tool_events" not in record or SMOKE.search(str(record.get("model", ""))):
                    continue
                if "adapter" not in record:
                    m = re.match(r"\d{8}-\d{6}_(.+)_[^_]+_both$", path.stem)
                    record["adapter"] = m.group(1) if m else None
                yield f"{path.stem}#{index}", record


def adapter_family(adapter):
    for fam in ADAPTER_FAMILIES:
        if adapter and adapter.startswith(fam):
            return fam
    return "other"


def load_tasks():
    """task_id -> task dict, later task files override earlier ones (iclr2027 files carry severity)."""
    tasks = {}
    for path in sorted(TASKS_DIR.glob("*.jsonl")):
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    task = json.loads(line)
                    tasks[task["task_id"]] = task
    return tasks


def infer_severity(task):
    """ToxicBench's own rule (generate_iclr2027_tasks.infer_severity), applied when severity is null."""
    poison = task.get("poison", {})
    if poison.get("severity"):
        return poison["severity"]
    ptype = poison.get("type", "")
    oracle = task.get("oracle", {})
    if ptype == "sign_flip":
        return "obvious"
    if ptype in {"rank_swap", "label_swap", "treatment_control_flip", "column_semantic_swap", "stale_metadata", "biased_retrieval"}:
        return "plausible"
    if ptype == "aggregate_scale":
        try:
            ratio = abs(float(oracle.get("poisoned_value")) / float(oracle.get("clean_value")))
        except (TypeError, ValueError, ZeroDivisionError):
            ratio = float(poison.get("scale", 2.0))
        if ratio >= 2.0 or ratio <= 0.5:
            return "obvious"
        if ratio >= 1.4 or ratio <= 0.75:
            return "plausible"
        return "subtle"
    return "plausible"


def pair_runs():
    """(task_id, adapter, model) -> {'clean': [runs], 'toxic': [runs]} in file order."""
    pairs = collections.defaultdict(lambda: {"clean": [], "toxic": []})
    for rid, r in iter_runs():
        env = r.get("environment")
        if env in ("clean", "toxic"):
            r["_run_id"] = rid
            pairs[(r["task_id"], r["adapter"], r["model"])][env].append(r)
    return pairs
