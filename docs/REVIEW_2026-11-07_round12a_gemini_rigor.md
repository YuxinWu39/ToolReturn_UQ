# Round 12a — Gemini Rigor Recompute (recomputed by main agent; the dispatched reviewer timed out)

**Date**: 2026-11-07
**Snapshot**: ToolReturn_UQ HEAD ecc4109 (read-only)
**Method**: direct recomputation from raw trajectories with the project venv (numpy/pandas/sklearn). The dispatched
rigor-reviewer subagent exceeded its 1800 s deadline at turn 26 without writing a report; these numbers were recomputed
by the orchestrator from `data/ours/p4/gemini-3.8-flash/T1/{clean_seed0,clean_seed1,toxic_seed0}.jsonl` and `summary.json`.

## Agreement with F9 (all confirmed)

| F9 claim | Recomputed | Verdict |
|---|---:|---|
| Clean success 200 / 198 | from summary by_run | AGREE |
| Toxic task success 131 | 131 | AGREE |
| Poison fired / toxic | 128 / 210 | AGREE |
| Adopted / fired | 72 / 128 (56.2%) | AGREE |
| Legacy poisoned_answer_used | 73 / 210 | AGREE |
| Recovery | 50 / 128 | AGREE |
| Recovery with a post-poison python_exec ERROR | **37 / 50** | AGREE |
| First poisoned return scalar / non-scalar | **35 / 93** | AGREE |
| Clean-repeat success disagreements | 4 / 210 (noise floor 1.9%) | AGREE |
| Verbalized confidence = 100 | **711 / 731** (others: 16×0, 2×95, 1×90) | AGREE |
| H5 subtle paired | 7 tasks / 3 tables, AUROC 0.556 [0.50, 0.67] | AGREE (from summary.primary_subtle) |

## Why poison fired in only 128/210 (the central rigor question)

The 82 non-fired toxic runs break down as:
- **3** — the agent never called `python_exec` at all.
- **79** — the agent's computation path never produced the value the poisoner targets. ToxicBench's poisoner
  corrupts only a return that matches the task's target computation; when Gemini computed the answer a different
  way (e.g. a multi-step or reformatted computation), there was no matching scalar to corrupt, so no poison fired.

Consequence: Gemini's lower fire rate (128/210 vs Qwen ~195-202/210) is a **computation-path / output-format
effect, not evidence of robustness**. The poison can only fire when the agent emits the targeted scalar; Gemini
emits it less often because 93/128 of its first returns are non-scalar (labelled prints, multi-number output,
DataFrame-style text). This is the same mechanism that pushes 93/128 fired returns outside our scalar signal
evaluation unit.

## Recovery is confounded with retry under poison_once

Of 50 recoveries, 37 had a `python_exec` ERROR after the poisoned return. Under poison_once the poison fires exactly
once, so any subsequent successful re-execution returns the TRUE value. A recovery that follows a tool error is
therefore consistent with blind retry (the agent re-ran after an error and happened to get the clean value), not
with detection or verification. At most 13/50 recoveries are candidates for intentional cross-checking, and even
those are not confirmed as verification without reading the agent's stated reason. "Recovery" must NOT be read as
"detection" in the paper.

## Scalar coverage is the evaluation-unit boundary

68/420 Gemini scored events are scalar under the parser (16%), vs ~93% for Qwen. Running the fixed scorers on the
Gemini T1 set gives coverage 0.32-0.40 for the zero-parameter signals and 4-6 tables with both classes, CIs spanning
[0.2, 1.0] — not reportable. The honest framing (per 12c): Gemini is an external replication with a DIFFERENT
evaluation unit, not a comparison row.

## Verbalized confidence is degenerate

711/731 valid shadow replies are exactly 100. An AUROC on a signal that is constant in 97% of cases is 0.5 by
construction, not by evidence. Report as "uninformative by construction" (12b Rank-2 caveat), not as a measured null.

## Protocol-before-results

In the rebased linear history: `1a1c3ee` (register Gemini protocol) precedes `1eb6b14` (collection code) and
`30a7825` (results). F9/audit cite the pre-rebase SHAs `4fa7740`/`f01f8bf`, pinned by the trajectory and analysis
SHA-256 hashes in `audit.json`. Order holds. Minor provenance gap: the `codex/gemini-pre-rebase-20261107` branch
the collaborator says preserves the original chain is not present in this clone — the pre-rebase commit objects are
not independently inspectable here, only the hashes in audit.json. Note it; it does not invalidate the order.

## Step gate

7-item autoresearch STEP GATE: protocol committed before results PASS; numbers independently reproduced PASS;
negative/limited result honestly labelled PASS (H5 "insufficient coverage", not confirmed); claims scoped PASS with
the one correction that the low fire rate and recovery must be attributed to format/retry, not robustness. Overall:
the Gemini step is rigorous AS A REPLICATION; it is NOT a clean cross-model robustness comparison and must not be
written as one.
