#!/usr/bin/env python3
"""A-CTX-PILOT: freeze, run and summarize a fixed-return context audit.

No generated code execution. Run with `python experiments/context_pilot.py --help`.
The manifest is model-independent so Gemini and a later Qwen run see identical inputs.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from zeroparam import FastTemplate

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261107
CONTEXTS = ("head5", "random20", "matched20")
SYSTEM = """You are completing a data-analysis task at the boundary after a tool returned a scalar.
Assess whether this tool result is trustworthy using the query, code and partial table evidence supplied.
The table rows shown are a sample, not the full population. The requested mean is for all matching rows
in the full table. You cannot run another tool or access the full table. Do not assume the tool is
correct or incorrect. You may accept, reject or remain uncertain, and you may abstain from a final
numeric answer if the available information is insufficient. If you give an answer, it must answer
the full-table query, not just compute a sample mean.
Return exactly one JSON object, without markdown, with these fields:
decision: "accept", "reject", or "uncertain" about the supplied tool result;
confidence: an integer from 0 to 100 rating how confident you are that the supplied tool value is correct;
answer: a finite JSON number for your final answer to the original query, or null to abstain;
reason: a brief string explaining your assessment. No other fields."""


def encoded(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()


def digest(x):
    return hashlib.sha256(encoded(x)).hexdigest()


def filehash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path, x):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(encoded(x) + b"\n")
    tmp.replace(path)


def sources(root):
    return {name: filehash(root / "experiments" / name)
            for name in ("context_pilot.py", "p4_run.py", "zeroparam.py")}


def prepare(root):
    tasks_path = root / "data/ours/tasks/large_tables_v2.jsonl"
    tasks = [json.loads(s) for s in tasks_path.read_text().splitlines()]
    rng = np.random.default_rng(SEED)
    selected, units, data_hashes = [], [], {}
    for table_i, dataset in enumerate(sorted({t["dataset"] for t in tasks})):
        path = root / "data/ours/datasets" / dataset
        data_hashes[dataset] = filehash(path)
        df = pd.read_csv(path)
        seen = set()
        chosen = 0
        for task in tasks:
            m = task["meta"]
            if task["dataset"] != dataset or m["op"] != "mean" or not m.get("filter"):
                continue
            key = (m["column"], tuple(m["filter"]))
            if key in seen:
                continue
            fast = FastTemplate(df, "mean", m["column"], m["filter"], None)
            eligible = np.flatnonzero(fast.mask & np.isfinite(fast.vals))
            y = fast.on_subset(np.arange(len(df)))
            tol = task["oracle"]["tolerance"]
            if len(eligible) < 20 or y is None or not math.isfinite(y) or y <= 0 or y-y/1.1 <= 2*tol:
                continue
            assert math.isclose(y, task["oracle"]["clean_value"], rel_tol=1e-12, abs_tol=1e-12)
            seen.add(key)
            factor = (1.1, 1.5)[chosen]
            scale = factor if table_i % 2 == 0 else 1 / factor
            q = {"task_id": task["task_id"], "dataset": dataset, "query": task["user_query"],
                 "code": m["code"], "column": m["column"], "filter": m["filter"],
                 "template": "filtered", "severity": ("subtle", "plausible")[chosen],
                 "scale": scale, "truth": float(y), "corrupted": float(y*scale), "tolerance": tol}
            selected.append(q)
            indices = {"head5": np.arange(5), "random20": rng.choice(len(df), 20, replace=False),
                       "matched20": rng.choice(eligible, 20, replace=False)}
            rules = {"head5": "First five rows of the full table, in original order.",
                     "random20": "20 rows uniformly sampled without replacement from the full table.",
                     "matched20": "20 rows uniformly sampled without replacement from rows satisfying "
                                  "the query filter and having a finite numeric target."}
            for context, idx in indices.items():
                evidence = {"shape": list(df.shape), "columns": list(df.columns),
                            "dtypes": {c: str(t) for c, t in df.dtypes.items()}, "sampling_rule": rules[context],
                            "rows_csv": df.iloc[idx].to_csv(index=False)}
                for label in (0, 1):
                    value = float(y*scale if label else y)
                    packet = {"value": value}
                    content = ("QUERY\n" + q["query"] + "\nTOOL CODE\n" + q["code"] +
                               "\nPARTIAL TABLE EVIDENCE\n" + encoded(evidence).decode() +
                               "\nTOOL RESULT\n" + encoded(packet).decode())
                    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}]
                    units.append({"unit_id": f"{q['task_id']}__{context}__{label}", "task_id": q["task_id"],
                                  "dataset": dataset, "context": context, "label": label,
                                  "severity": q["severity"], "truth": float(y), "tolerance": tol,
                                  "delivered_value": value, "tool_packet": packet,
                                  "row_indices": idx.tolist(), "context_hash": digest(evidence),
                                  "messages": msgs, "messages_hash": digest(msgs)})
            chosen += 1
            if chosen == 2:
                break
        if chosen != 2:
            raise ValueError(f"Insufficient qualifying queries: {dataset}")
    rng.shuffle(units)
    manifest = {"protocol": "A-CTX-PILOT", "seed": SEED, "selected_queries": selected, "units": units,
                "task_file_hash": filehash(tasks_path), "dataset_hashes": data_hashes,
                "source_hashes": sources(root), "python": platform.python_version(),
                "numpy": np.__version__, "pandas": pd.__version__,
                "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()}
    validate_manifest(manifest)
    return manifest


def validate_manifest(m):
    units, queries = m["units"], m["selected_queries"]
    assert len(units) == 72 and len(queries) == 12
    assert len({u["unit_id"] for u in units}) == 72
    assert len({q["dataset"] for q in queries}) == 6
    for q in queries:
        group = [u for u in units if u["task_id"] == q["task_id"]]
        assert len(group) == 6
        for c in CONTEXTS:
            pair = sorted((u for u in group if u["context"] == c), key=lambda u: u["label"])
            a, b = pair
            assert [u["label"] for u in pair] == [0, 1]
            assert a["row_indices"] == b["row_indices"] and a["context_hash"] == b["context_hash"]
            assert len(a["row_indices"]) == (5 if c == "head5" else 20)
            assert len(set(a["row_indices"])) == len(a["row_indices"])
            for u in pair:
                expected = q["corrupted"] if u["label"] else q["truth"]
                assert u["tool_packet"] == {"value": expected}
                assert u["delivered_value"] == expected
                assert digest(u["messages"]) == u["messages_hash"]
                prefix, suffix = u["messages"][1]["content"].split("\nTOOL RESULT\n")
                assert json.loads(suffix) == {"value": expected}
                assert prefix == a["messages"][1]["content"].split("\nTOOL RESULT\n")[0]


def parse_reply(raw):
    try:
        x = json.loads(raw)
        if not isinstance(x, dict) or set(x) != {"decision", "confidence", "answer", "reason"}:
            return None
        if x["decision"] not in ("accept", "reject", "uncertain"):
            return None
        if type(x["confidence"]) is not int or not 0 <= x["confidence"] <= 100:
            return None
        a = x["answer"]
        if a is not None and (type(a) not in (int, float) or not math.isfinite(a)):
            return None
        if not isinstance(x["reason"], str):
            return None
        return x
    except (TypeError, ValueError):
        return None


def settings(model, base):
    return {"model": model, "base_url": base, "max_tokens": 2048,
            "sampling": "provider_default_low_reasoning" if model == "gemini-3.8-flash" else "temperature_0.7_seed_0"}


def run(m, out, model, base, workers):
    from p4_run import SeededClient
    validate_manifest(m)
    if sources(ROOT) != m["source_hashes"]:
        raise ValueError("Source hashes differ from frozen manifest; do not resume with changed code")
    key = os.environ.get("GEMINI_API_KEY") if model == "gemini-3.8-flash" else os.environ.get("OPENAI_API_KEY", "local")
    if not key:
        raise ValueError("GEMINI_API_KEY is required")
    out.mkdir(parents=True, exist_ok=True)
    config = {"manifest_hash": digest(m), "source_hashes": sources(ROOT), **settings(model, base)}
    cfg = out / "config.json"
    if cfg.exists() and json.loads(cfg.read_text()) != config:
        raise ValueError("Resume config mismatch")
    save(cfg, config)
    todo = []
    for u in m["units"]:
        p = out / "responses" / (u["unit_id"] + ".json")
        if p.exists():
            old = json.loads(p.read_text())
            if old["manifest_hash"] != config["manifest_hash"] or old["messages_hash"] != u["messages_hash"]:
                raise ValueError("Saved response hash mismatch")
        else:
            todo.append(u)
    print(json.dumps({"pending": len(todo), "completed": 72-len(todo)}), flush=True)

    def request(u):
        client = SeededClient(base, key, model, .7, 2048, 0, signals=False)
        payload = {"model": model, "messages": u["messages"], "max_tokens": 2048}
        if model != "gemini-3.8-flash":
            payload.update(temperature=.7, seed=0)
        # Mirror the existing transport transformations before hashing the actual payload.
        if client.is_gemini:
            payload["reasoning_effort"] = "low"
        if model.startswith("qwen3"):
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        rec = {"unit_id": u["unit_id"], "manifest_hash": digest(m), "messages_hash": u["messages_hash"],
               "payload_hash": digest(payload), "started_utc": utc()}
        started = time.monotonic()
        try:
            body = client._post(payload)
            choice = (body.get("choices") or [{}])[0]
            raw = (choice.get("message") or {}).get("content") or ""
            rec.update(status="completed", raw=raw, parsed=parse_reply(raw), provider_response=body,
                       response_model=body.get("model"), usage=body.get("usage"), finish_reason=choice.get("finish_reason"))
        except Exception as exc:
            rec.update(status="transport_failure", error=str(exc).replace(key, "[redacted]")[:1200])
        rec.update(ended_utc=utc(), elapsed_seconds=time.monotonic()-started)
        return rec

    pool = cf.ThreadPoolExecutor(max_workers=workers)
    pending, cursor, completed = {}, iter(todo), 72-len(todo)
    failures, fatal = 0, False
    try:
        for _ in range(workers):
            u = next(cursor, None)
            if u:
                pending[pool.submit(request, u)] = u
        while pending:
            ready, _ = cf.wait(pending, return_when=cf.FIRST_COMPLETED)
            for future in ready:
                u = pending.pop(future)
                rec = future.result()
                if rec["status"] == "completed":
                    save(out / "responses" / (u["unit_id"] + ".json"), rec)
                    completed += 1
                else:
                    failures += 1
                    with (out / "transport_failures.jsonl").open("ab") as f:
                        f.write(encoded(rec)+b"\n")
                    error = rec["error"]
                    fatal |= any(s in error for s in ("HTTP 400", "HTTP 401", "HTTP 403", "HTTP 404"))
                    print(json.dumps({"unit": u["unit_id"], "transport_error": error}), flush=True)
                if completed % 6 == 0 or failures:
                    print(json.dumps({"completed": completed, "transport_failures": failures}), flush=True)
            if fatal:
                # Drain already-issued requests, but send no further units.
                cursor = iter(())
            for _ in range(workers-len(pending)):
                u = next(cursor, None)
                if u:
                    pending[pool.submit(request, u)] = u
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    if failures:
        raise RuntimeError(f"{failures} transport failures retained; resume only unresolved cells")


def close(a, b, tol):
    return a is not None and abs(a-b) <= tol


def cluster_stats(values):
    """Equal-table mean and percentile table bootstrap; values keyed by dataset."""
    means = np.array([np.mean(v) for _, v in sorted(values.items()) if len(v)], dtype=float)
    if not len(means):
        return {"mean": None, "ci95": None, "tables": 0}
    boots = np.random.default_rng(1).choice(means, (2000, len(means)), replace=True).mean(axis=1)
    return {"mean": float(means.mean()), "ci95": np.quantile(boots, [.025, .975]).tolist(), "tables": len(means)}


def summarize(m, out):
    validate_manifest(m)
    rows = []
    for u in m["units"]:
        p = out / "responses" / (u["unit_id"] + ".json")
        if not p.exists():
            continue
        r = json.loads(p.read_text())
        if r["manifest_hash"] != digest(m) or r["messages_hash"] != u["messages_hash"]:
            raise ValueError("Result/manifest mismatch")
        parsed = parse_reply(r["raw"])
        a = parsed["answer"] if parsed else None
        rows.append({k: u[k] for k in ("task_id", "dataset", "context", "label", "severity", "unit_id")}
                    | {"valid": parsed is not None, "decision": parsed["decision"] if parsed else "invalid",
                       "confidence": parsed["confidence"] if parsed else None, "answer": a,
                       "correct": bool(parsed and close(a, u["truth"], u["tolerance"])),
                       "adopted_wrong": bool(parsed and u["label"] and close(a, u["delivered_value"], u["tolerance"])
                                             and not close(a, u["truth"], u["tolerance"])),
                       "usage": r.get("usage") or {}, "response_model": r.get("response_model"),
                       "finish_reason": r.get("finish_reason")})
    def cells(subset):
        ans = {}
        for c in CONTEXTS:
            ans[c] = {}
            for label in (0, 1):
                s = [r for r in subset if r["context"] == c and r["label"] == label]
                conf = [r["confidence"] for r in s if r["confidence"] is not None]
                ans[c][str(label)] = {"n": len(s), "valid": sum(r["valid"] for r in s),
                    **{d: sum(r["decision"] == d for r in s) for d in ("accept", "reject", "uncertain", "invalid")},
                    "correct": sum(r["correct"] for r in s), "adopted_wrong": sum(r["adopted_wrong"] for r in s),
                    "null_answers": sum(r["valid"] and r["answer"] is None for r in s),
                    "confidence_median": float(np.median(conf)) if conf else None,
                    "confidence_mean": float(np.mean(conf)) if conf else None}
        return ans
    def contrasts(subset, valid_only=False):
        paired, lookup = {}, {(r["task_id"], r["context"], r["label"]): r for r in subset}
        for q in m["selected_queries"]:
            vals = {}
            for c in CONTEXTS:
                pair = [lookup.get((q["task_id"], c, i)) for i in (0, 1)]
                if any(r is None for r in pair) or (valid_only and not all(r["valid"] for r in pair)):
                    continue
                vals[c] = int(pair[0]["decision"] == "accept") - int(pair[1]["decision"] == "accept")
            if vals:
                paired[q["task_id"]] = {"dataset": q["dataset"], **vals}
        result = {}
        for a, b in (("matched20", "random20"), ("random20", "head5"), ("matched20", "head5")):
            v = {}
            for q in paired.values():
                if a in q and b in q:
                    v.setdefault(q["dataset"], []).append(q[a]-q[b])
            result[a+"_minus_"+b] = {**cluster_stats(v), "queries": sum(map(len, v.values())),
                                      "per_table": {d: float(np.mean(x)) for d, x in v.items()}}
        return result
    usage = {k: sum(r["usage"].get(k, 0) or 0 for r in rows)
             for k in ("prompt_tokens", "completion_tokens", "total_tokens")}
    summary = {"protocol": "A-CTX-PILOT", "manifest_hash": digest(m), "n": len(rows),
        "expected": 72, "valid": sum(r["valid"] for r in rows), "cells": cells(rows),
        "primary_acceptance_discrimination_contrasts": contrasts(rows),
        "valid_pair_sensitivity": contrasts(rows, True),
        "per_severity": {s: {"cells": cells([r for r in rows if r["severity"] == s]),
                              "contrasts": contrasts([r for r in rows if r["severity"] == s])}
                         for s in ("subtle", "plausible")},
        "per_table": {d: cells([r for r in rows if r["dataset"] == d]) for d in sorted({r["dataset"] for r in rows})},
        "usage": usage, "response_models": sorted({r["response_model"] for r in rows if r["response_model"]}),
        "finish_reasons": {str(f): sum(r["finish_reason"] == f for r in rows) for f in {r["finish_reason"] for r in rows}},
        "packet_delivery": {"constructed": 72, "corrupted": 36, "same_context_per_pair": True},
        "confidence_auroc": {"estimate": None, "status": "withheld: no live extreme-corruption sanity arm"},
        "feasibility_pass": len(rows) == 72 and sum(r["valid"] for r in rows) >= 65}
    save(out / "summary.json", summary)
    save(out / "scored_responses.json", rows)
    print(json.dumps({k: summary[k] for k in ("n", "valid", "cells", "primary_acceptance_discrimination_contrasts", "usage", "feasibility_pass")}, indent=2))
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("prepare", "run", "summarize"))
    p.add_argument("--manifest", type=Path, default=ROOT / "data/ours/context_pilot/20261107/manifest.json")
    p.add_argument("--output", type=Path, default=ROOT / "data/ours/context_pilot/20261107/gemini-3.8-flash")
    p.add_argument("--model", default="gemini-3.8-flash")
    p.add_argument("--base-url", default="https://generativelanguage.googleapis.com/v1beta/openai")
    p.add_argument("--workers", type=int, choices=range(1, 5), default=4)
    a = p.parse_args()
    if a.action == "prepare":
        if a.manifest.exists():
            raise ValueError("Manifest already exists: never overwrite a frozen design")
        m = prepare(ROOT)
        save(a.manifest, m)
        print(json.dumps({"manifest_hash": digest(m), "units": len(m["units"]),
                          "queries": [q["task_id"] for q in m["selected_queries"]]}, indent=2))
    else:
        m = json.loads(a.manifest.read_text())
        if a.action == "run":
            run(m, a.output, a.model, a.base_url, a.workers)
        else:
            summarize(m, a.output)


if __name__ == "__main__":
    main()
