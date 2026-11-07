#!/usr/bin/env python3
"""P4 harness (PREREGISTRATION.md P4 / A-P4): run ToxicBench's ReAct agent on the P3 large-table tasks with the
observation-context tier ENFORCED INSIDE THE ENVIRONMENT (the agent really sees the truncated preview), against
an OpenAI-compatible endpoint (local vLLM, GPT API, or Gemini Flash).

Tiers (A-P3/A-P4):
  T0_agent  ToxicBench's own preview: head (rows capped at 5) + whole-column numeric_min/max  (what the original data had)
  T1        head-5, NO numeric_min/max
  T2        head-2, NO numeric_min/max
  T3        schema only (columns, shape), no rows, no min/max
Rows requested by the agent above the tier cap are capped; the cap and the rows actually exposed are logged per event.

    python p4_run.py --smoke --tier T1 --agent gemini-3.8-flash   # reads GEMINI_API_KEY
    python p4_run.py --smoke --tier T1 --agent qwen3-4b --base-url http://127.0.0.1:8000/v1
    python p4_run.py --tier T1 --agent qwen3-4b --seeds 2            # clean x 2 seeds + toxic x 1 (A-P4)
Outputs data/ours/p4/<agent>/<tier>/<env>_seed<k>.jsonl in ToxicBench's row format (+ tier, visible_rows, seed).
Resumable: tasks already present in the output file are skipped.
"""

import argparse
import json
import os
import re
import urllib.error
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TB = REPO / "data" / "toxicbench"
sys.path.insert(0, str(TB))
sys.path.insert(0, str(TB / "toxictool_bench"))  # upstream modules use bare imports
from toxictool_bench import tools as tb_tools  # noqa: E402
from toxictool_bench.agents import run_llm_agent  # noqa: E402
from toxictool_bench.evaluator import evaluate_run  # noqa: E402
from toxictool_bench.llm_client import ChatClient  # noqa: E402

TIERS = {"T0_agent": {"rows": 5, "minmax": True}, "T1": {"rows": 5, "minmax": False},
         "T2": {"rows": 2, "minmax": False}, "T3": {"rows": 0, "minmax": False}}
GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai"
AGENTS = {GEMINI_MODEL: GEMINI_MODEL, "qwen3-4b": "qwen3-4b", "qwen3-8b": "qwen3-8b", "gpt-5.4-mini": "gpt-5.4-mini"}


class TieredEnv(tb_tools.DataToolEnv):
    """DataToolEnv whose preview is capped by the tier. Everything else (poisoner, python_exec, events) is upstream."""

    tier = "T1"

    def preview(self, rows: int = 5) -> str:
        spec = TIERS[self.tier]
        requested = int(rows)
        rows = max(0, min(requested, spec["rows"]))
        summary = {"dataset": self.task["dataset"], "columns": list(self.df.columns), "shape": list(self.df.shape)}
        if spec["minmax"]:
            summary["numeric_min"] = self.df.select_dtypes("number").min(numeric_only=True).to_dict()
            summary["numeric_max"] = self.df.select_dtypes("number").max(numeric_only=True).to_dict()
        head = self.df.head(rows).to_csv(index=False) if rows > 0 else "(no rows available at this access level)\n"
        self._last_preview = {"tier": self.tier, "rows_requested": requested, "rows_exposed": rows, "minmax": spec["minmax"]}
        return "DATASET SUMMARY\n" + json.dumps(summary, ensure_ascii=False) + "\n\nHEAD\n" + head

    def call(self, tool_name, args):
        out = super().call(tool_name, args)
        if tool_name == "preview" and getattr(self, "_last_preview", None):
            self.events[-1]["preview_exposure"] = self._last_preview
        if tool_name == "python_exec" and getattr(self, "_last_exec_norm", None):
            self.events[-1]["harness_normalization"] = self._last_exec_norm
        return out

    # --- A-P4 harness-compatibility note (applies identically to every agent; logged per event) -----------------
    # Small models emit two formatting quirks that upstream ToxicBench turns into ERROR observations (its
    # "harness-limit" class): (1) `pd.read_csv('<dataset file>')` although df is preloaded -> the sandbox has no
    # such file; (2) JSON-escaped code whose continuation lines carry one stray leading space -> IndentationError.
    # Neither is a tool-return error we want to study, so the sandbox resolves read_csv of a known table to that
    # table and strips the uniform stray indent. Both are recorded in the event so they can be excluded or audited.
    def python_exec(self, code: str) -> str:
        if getattr(self, "macos_worker", False):
            from macos_p4_worker import execute
            value, self._last_exec_norm = execute(self.task, self.bench_dir, code)
            return value
        import ast as _ast, contextlib as _ctx, io as _io, os as _os
        norm = {}
        lines = code.split("\n")
        if len(lines) > 1 and not lines[0].startswith((" ", "\t")) and all(l.startswith(" ") and not l.startswith("  ") for l in lines[1:] if l.strip()):
            try:
                _ast.parse(code)
            except SyntaxError:
                code = "\n".join([lines[0]] + [l[1:] if l.startswith(" ") else l for l in lines[1:]])
                norm["stripped_stray_indent"] = True
        # `import pandas as pd` inside the code would rebind pd to real pandas and bypass the proxy below
        kept = [l for l in code.split("\n") if not __import__("re").match(r"^\s*import\s+pandas(\s+as\s+pd)?\s*$", l)]
        if len(kept) != len(code.split("\n")):
            code, norm["dropped_pandas_import"] = "\n".join(kept), True
        files = {fn: self.tables[name] for name, fn in self.table_files.items()}

        class _PD:  # pandas proxy: read_csv of a known dataset file returns that table
            def __getattr__(self, name):
                return getattr(tb_tools.pd, name)

            def read_csv(self, path, *a, **k):
                base = _os.path.basename(str(path))
                if base in files:
                    norm["read_csv_resolved"] = base
                    return files[base].copy()
                # No fallback to the real filesystem: model-generated code may only read the declared dataset files.
                raise FileNotFoundError(f"[sandbox] unknown dataset '{base}'; available: {sorted(files)}")

        table_namespace = {name: t.copy() for name, t in self.tables.items()}
        for name, fn in self.table_files.items():
            table_namespace[fn] = self.tables[name].copy()
        ns = {"__builtins__": tb_tools.SAFE_BUILTINS, "pd": _PD(), "df": self.df.copy(), "tables": table_namespace}
        for name, t in self.tables.items():
            ns[name] = t.copy()
        out = _io.StringIO()
        try:
            tree = _ast.parse(code)
            last = None
            if tree.body and isinstance(tree.body[-1], _ast.Expr):
                last = _ast.Expression(tree.body[-1].value)
                tree.body = tree.body[:-1]
                _ast.fix_missing_locations(tree); _ast.fix_missing_locations(last)
            with _ctx.redirect_stdout(out):
                if tree.body:
                    exec(compile(tree, "<p4-python-exec>", "exec"), ns, ns)
                if last is not None:
                    v = eval(compile(last, "<p4-python-exec>", "eval"), ns, ns)
                    if v is not None:
                        print(v)
        except Exception as exc:  # noqa: BLE001
            self._last_exec_norm = norm or None
            return f"ERROR: {type(exc).__name__}: {exc}"
        self._last_exec_norm = norm or None
        text = out.getvalue().strip()
        return text if text else (str(ns["_"]) if "_" in ns else "OK")


VERBALIZED_PROMPT = ("Before you continue: on a scale from 0 to 100, how confident are you that the last tool output "
                     "above is correct and trustworthy for this task? Reply with only the integer.")


def _entropy(top_logprobs):
    """Entropy (nats) of the top-k distribution for one token position; the tail mass is folded into one bucket."""
    import math
    ps = [math.exp(t["logprob"]) for t in top_logprobs]
    tail = max(0.0, 1.0 - sum(ps))
    ps = [p for p in ps if p > 0] + ([tail] if tail > 1e-12 else [])
    z = sum(ps)
    return -sum((p / z) * math.log(p / z) for p in ps)


class SeededClient(ChatClient):
    """ChatClient that sends a seed, requests logprobs (signal 1: token entropy) and, before answering a message whose
    last turn is a python_exec observation, makes a SHADOW call asking for verbalized confidence (signal 3). The shadow
    call is a separate stateless request; the live trajectory is unchanged (A-P4)."""

    def __init__(self, base_url, api_key, model, temperature, max_tokens, seed, signals=True):
        self.api_key, self.model = api_key, model
        self.is_gemini = model == GEMINI_MODEL
        if self.is_gemini:
            self.endpoint = GEMINI_BASE + "/chat/completions"
        else:
            self.endpoint = base_url.rstrip("/").removesuffix("/v1") + "/v1/chat/completions"
        self.temperature, self.max_tokens, self.max_retries, self.seed = temperature, max_tokens, 6, seed
        self.signals, self.completions = signals, []

    def _post(self, payload):
        import urllib.request
        if self.model.startswith("qwen3"):  # Qwen3 thinking mode off: the ReAct loop expects a JSON action, not a <think> block
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        if self.is_gemini:
            payload.pop("seed", None)
            payload.pop("temperature", None)
            payload["reasoning_effort"] = "low"
        req = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode(),
                                     headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    return json.loads(r.read())
            except urllib.error.HTTPError as exc:
                if exc.code not in (408, 429, 500, 502, 503, 504) or attempt >= self.max_retries:
                    detail = str(exc.reason)
                    if self.is_gemini:
                        try:
                            error = json.loads(exc.read()).get("error", {})
                            detail = str(error.get("message", detail)).replace(self.api_key, "[redacted]")[:500]
                        except (ValueError, AttributeError):
                            pass
                    raise RuntimeError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
                delay = exc.headers.get("Retry-After", "")
                time.sleep(int(delay) if delay.isdigit() else 2 ** attempt)
            except (TimeoutError, urllib.error.URLError) as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"LLM request failed: {exc}") from exc
                time.sleep(2 ** attempt)
        raise RuntimeError("unreachable")

    def complete(self, messages):
        rec = {"call_index": len(self.completions), "after_observation": None, "verbalized": None}
        last = messages[-1]
        if last["role"] == "user" and last["content"].startswith("Observation:") and len(messages) >= 2:
            try:
                prev = json.loads(messages[-2]["content"])
                rec["after_observation"] = {"tool": prev.get("tool"), "n_tool_turns": sum(1 for m in messages if m["role"] == "assistant")}
            except Exception:  # noqa: BLE001
                rec["after_observation"] = {"tool": None}
            rec["after_observation"]["step"] = sum(
                m["role"] == "user" and m["content"].startswith("Observation:") for m in messages
            )
            if self.signals and rec["after_observation"].get("tool") == "python_exec":  # shadow verbalized-confidence call
                shadow = self._post({"model": self.model, "messages": messages + [{"role": "user", "content": VERBALIZED_PROMPT}],
                                     "temperature": 0.0, "max_tokens": 512 if self.is_gemini else 8, "seed": self.seed})
                shadow_choice = shadow["choices"][0]
                txt = (shadow_choice["message"].get("content") or "").strip()
                if self.is_gemini:
                    valid = re.fullmatch(r"(?:100|[1-9]?[0-9])", txt)
                    rec["verbalized"] = {"raw": txt, "confidence": int(txt) if valid else None,
                                         "finish_reason": shadow_choice.get("finish_reason"),
                                         "model": shadow.get("model"), "usage": shadow.get("usage")}
                else:
                    m = re.search(r"\d{1,3}", txt)
                    rec["verbalized"] = {"raw": txt[:40], "confidence": int(m.group()) if m else None}
        payload = {"model": self.model, "messages": messages, "temperature": self.temperature, "max_tokens": self.max_tokens, "seed": self.seed}
        if self.signals and not self.is_gemini:
            payload.update({"logprobs": True, "top_logprobs": 20})
        body = self._post(payload)
        choice = body["choices"][0]
        content = choice["message"].get("content") or ""
        if self.is_gemini:
            rec.update({"model": body.get("model"), "usage": body.get("usage"),
                        "finish_reason": choice.get("finish_reason")})
        lp = (choice.get("logprobs") or {}).get("content") or []
        if lp:
            ents = [_entropy(t.get("top_logprobs") or [{"logprob": t["logprob"]}]) for t in lp]
            rec.update({"n_tokens": len(lp), "first_token_entropy": ents[0], "mean_entropy": sum(ents) / len(ents),
                        "max_entropy": max(ents), "mean_entropy_first10": sum(ents[:10]) / len(ents[:10]),
                        "sum_logprob": sum(t["logprob"] for t in lp), "first_token": lp[0]["token"]})
        self.completions.append(rec)
        return content


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tasks", type=Path, default=REPO / "data" / "ours" / "tasks" / "large_tables_v2.jsonl")
    ap.add_argument("--bench-dir", type=Path, default=REPO / "data" / "ours", help="dir containing datasets/<task.dataset>")
    ap.add_argument("--tier", choices=list(TIERS), default="T1")
    ap.add_argument("--agent", choices=list(AGENTS), default="qwen3-4b")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--api-key", default=None,
                    help="defaults to $GEMINI_API_KEY for Flash or $OPENAI_API_KEY for other endpoints")
    ap.add_argument("--profile", default="react", help="ToxicBench agent profile (A-P4: react)")
    ap.add_argument("--temperature", type=float, default=0.7, help="A-P4: equal temperature for every run")
    ap.add_argument("--max-steps", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=2, help="clean seeds (toxic always 1 seed, seed 0)")
    ap.add_argument("--env", choices=["clean", "toxic", "both"], default="both")
    ap.add_argument("--smoke", action="store_true", help="A-P4 smoke: 20 tasks, clean only, 1 seed; report parse rate")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", type=Path, default=REPO / "data" / "ours" / "p4")
    ap.add_argument("--no-signals", action="store_true", help="skip logprobs + shadow verbalized call (first week-1 run had none)")
    ap.add_argument("--run-tag", default="", help="suffix for the tier output dir (e.g. r2)")
    args = ap.parse_args()

    if args.agent == GEMINI_MODEL:
        if args.base_url and args.base_url.rstrip("/") != GEMINI_BASE:
            ap.error("Gemini uses Google's official OpenAI-compatible base URL")
        args.base_url = GEMINI_BASE
        args.api_key = args.api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not args.api_key:
            ap.error("set GEMINI_API_KEY for the Gemini run")
        if args.smoke and not args.run_tag:
            args.run_tag = "_smoke"
    else:
        args.base_url = args.base_url or "http://127.0.0.1:8000/v1"
        args.api_key = args.api_key or os.environ.get("OPENAI_API_KEY", "sk-local")

    tasks = [json.loads(l) for l in args.tasks.open() if l.strip()]
    if args.smoke:
        tasks, args.env, args.seeds = tasks[::max(1, len(tasks) // 20)][:20], "clean", 1
    if args.limit:
        tasks = tasks[: args.limit]
    runs = [("clean", s) for s in range(args.seeds)] if args.env in ("clean", "both") else []
    if args.env in ("toxic", "both"):
        runs.append(("toxic", 0))
    out_dir = args.out / args.agent / (args.tier + args.run_tag)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = AGENTS[args.agent]

    totals = {"runs": 0, "parse_errors": 0, "success": 0, "poison_fired": 0, "poison_matches_oracle": 0}
    for env_name, seed in runs:
        path = out_dir / f"{env_name}_seed{seed}.jsonl"
        done = {json.loads(l)["task_id"] for l in path.open()} if path.exists() else set()
        client = SeededClient(args.base_url, args.api_key, model, args.temperature, 2048, seed, signals=not args.no_signals)
        with path.open("a", encoding="utf-8") as f:
            for task in tasks:
                if task["task_id"] in done:
                    continue
                TieredEnv.tier = args.tier
                env = TieredEnv(task=task, bench_dir=args.bench_dir, toxic=(env_name == "toxic"))
                env.macos_worker = model == GEMINI_MODEL and sys.platform == "darwin"
                t0 = time.time()
                client.completions = []
                run = run_llm_agent(client=client, env=env, task=task, profile=args.profile, max_steps=args.max_steps)
                metrics = evaluate_run(task, run.final_answer, env.events)
                fired = [e for e in env.events if e.get("was_poisoned")]
                row = {"task_id": task["task_id"], "family": task["family"], "dataset": task["dataset"], "agent_profile": args.profile,
                       "model": model, "agent": args.agent, "tier": args.tier, "seed": seed, "environment": env_name,
                       "poison": task.get("poison", {}), "oracle": task.get("oracle", {}), "meta": task.get("meta", {}),
                       "tool_events": env.events, "final_answer": run.final_answer, "raw_actions": run.raw_actions,
                       "parse_errors": run.parse_errors, "metrics": metrics, "seconds": round(time.time() - t0, 1),
                       "completions": client.completions}
                if model == GEMINI_MODEL:
                    row["generation_config"] = {"reasoning_effort": "low", "sampling": "provider_default",
                                                "api_seed": None, "shadow": not args.no_signals,
                                                "token_logprobs": False}
                f.write(json.dumps(row, ensure_ascii=False) + "\n"); f.flush()
                totals["runs"] += 1
                totals["parse_errors"] += int(bool(run.parse_errors))
                totals["success"] += int(bool(metrics.get("task_success")))
                if env_name == "toxic":
                    totals["poison_fired"] += int(bool(fired))
                    pv = str(task["oracle"].get("poisoned_value"))
                    totals["poison_matches_oracle"] += int(any(pv[:6] in str(e["returned_observation"]) for e in fired))
                print(f"{task['task_id']} {env_name} seed{seed} tier={args.tier}: success={metrics.get('task_success')} "
                      f"parse_err={bool(run.parse_errors)} fired={bool(fired)} {row['seconds']}s", flush=True)
    print(json.dumps(totals))
    if args.smoke:
        smoke_ids = {t["task_id"] for t in tasks}
        with (out_dir / "clean_seed0.jsonl").open() as saved:
            smoke_rows = [r for r in map(json.loads, saved) if r["task_id"] in smoke_ids]
        valid = sum(bool(r["final_answer"].strip()) and r["final_answer"] != "ERROR: max steps reached"
                    for r in smoke_rows)
        print(f"SMOKE parseable final answers = {valid}/{len(tasks)}; "
              f"runs with an intermediate parse error = {sum(bool(r['parse_errors']) for r in smoke_rows)}")


if __name__ == "__main__":
    main()
