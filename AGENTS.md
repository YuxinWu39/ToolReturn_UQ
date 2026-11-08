# AGENTS.md — guide for coding agents working in this repo

Read this first. It explains what the project measures, the end-to-end pipeline, what every file does, and the
rules that keep the reported numbers valid.

## 1. What the project measures

An LLM agent answers a question about a CSV table by calling `python_exec` (pandas code) and reporting the number
the tool returns. In a **toxic** run the environment multiplies that returned number by a scale in
{1.05, 1.10, 1.20, 1.35, 1.50, 2.00} or its reciprocal (`aggregate_scale`, first poisoned call only, so a re-query
would return the true value). In a **clean** run the return is untouched. A **signal** scores each tool return;
detection quality is AUROC (positive = poisoned).

Independent variable: the **observation-context tier**, i.e. what the agent's `preview` tool shows:

| tier | preview content |
|---|---|
| `T0_agent` | first 5 rows + whole-column min/max (ToxicBench's default) |
| `T1` | first 5 rows, no min/max |
| `T2` | first 2 rows |
| `T3` | schema only (columns, shape), no rows |
| k-sweep | k random rows, k in {5, 10, 20, 50, 100, 200} (simulation only, no agent) |

Severity bins on |log2 scale|: `subtle` < 0.2 (1.05, 1.10), `plausible`, `obvious` (2.0).
Threat model: a checker may only use what the agent saw (preview rows + the returned value). Re-calling the tool
is excluded because under `poison_once` it trivially wins.

## 2. Signal glossary (names used in code, findings and logs)

| name | kind | definition (implementation in `experiments/zeroparam.py` unless noted) |
|---|---|---|
| `0a` | zero-parameter | range check: distance of y outside [min, max] of visible values (op-aware; sums use n * bounds) |
| `0b` | zero-parameter | z-score of y against visible values (original tables only) |
| `0d` | zero-parameter | re-execute the agent's own code on bootstrap resamples (size k) of the visible rows; distance outside the percentile interval; sums/counts scaled by n/k (`is_sum_type`) |
| `0r_log` | zero-parameter reference | analytic log-ratio t-score; unfiltered mean/median only |
| `0o` | privileged reference | finite full-table Monte Carlo bias/spread score, population-centred; not an optimality bound |
| `0o*` / `0o_star` | privileged reference | finite full-table Monte Carlo bias/spread score, draw-centred; no proven achievable ceiling |
| signal 1 | agent-intrinsic | mean token entropy over the action following the observation (A-P4b; first-token entropy is degenerate) |
| signal 3 | agent-intrinsic | shadow verbalized confidence (0-100), negated |
| signal 7 / C3 | learned | clean-only scorer, `experiments/scorer/`: predicts 5 quantiles of signed-log10 value; surprise = distance of y |

AUROC differences 0o* − 0d and 0o − 0o* are descriptive gaps between specified scores, not identified information components. See A-REVISION-CACHED and `docs/CURRENT_CONCLUSIONS.md`.

## 3. End-to-end pipeline

Each stage = one pre-registered protocol section (`PREREGISTRATION.md`) -> one script -> one finding (`findings.md`).
Run scripts from `experiments/` with the venv python. All scripts are resumable or deterministic (fixed seeds).

| # | stage | protocol | script | reads | writes | finding |
|---|---|---|---|---|---|---|
| 0 | inventory of ToxicBench fields and counts | — | `inventory.py` | `data/toxicbench/` | `results/inventory.json` | F0 |
| 1 | failure taxonomy (capability vs observation) with run-to-run noise null, G1 gate | P1, A-P1 | `taxonomy.py` | ToxicBench trajectories | `results/taxonomy/` | F1, F1' |
| 2 | zero-parameter checks on original (tiny) tables, G2 gate | P2, A-P2, A-P3d | `range_check.py` | ToxicBench trajectories | `results/range_check/` | F2''' |
| 3 | generate 210 large-table tasks + rule-specific references | P3, A-P3 | `gen_tasks.py` | public CSVs | `data/ours/{datasets,tasks,ceiling*.json*,dropped_tasks.jsonl}` | F3 |
| 4 | k-sweep: specified score comparison (0d, 0r_log, 0o, 0o*) | A-P3b-d | `ksweep2.py` | `data/ours/tasks/large_tables_v2.jsonl` | `data/ours/ksweep2/` | F4''' |
| 5a | agent runs at each tier (GPU) | P4, A-P4, A-P4b | `p4_run.py` (+ `scripts/serve_vllm.sh`) | tasks + ToxicBench agent | `data/ours/p4/<agent>/<tier>/{clean_seed0,clean_seed1,toxic_seed0}.jsonl` | F5-F7 |
| 5b | zero-parameter signals on real agent events | A-P4 | `p4_score_zeroparam.py --agent A --tier T` | P4 trajectories | `.../zeroparam_scores.jsonl` | F5, F7 |
| 5c | agent-intrinsic signals 1 and 3 | A-P4, A-P4b | `p4_score_intrinsic.py --agent A --tier T` | P4 trajectories (runs with logprobs) | `.../intrinsic_scores.jsonl` | F6, F7 |
| 6a | build scorer train (clean only) / eval sets | P5 | `scorer/build_dataset.py` | ToxicBench + P4 | `data/ours/scorer/{train,eval_*}.jsonl, stats.json` | F8 |
| 6b | train LOTO ensemble (6 held-out tables x K seeds, GPU) | P5 | `scorer/train_scorer.py` via `scorer/run_loto.sh` | `train.jsonl` | `models/scorer/<table>_s<k>/` (not committed) | F8 |
| 6c | score eval events with the ensemble | P5 | `scorer/score_scorer.py` | members + `eval_*.jsonl` | `data/ours/scorer/eval_*_scorer.jsonl` | F8 |

Shell entry points: `experiments/run_day1.sh` (stages 0-2), `experiments/scorer/run_loto.sh` (stage 6).
Stages 0-2 and 6a need ToxicBench (`bash scripts/setup_toxicbench.sh`). Stages 3-4 and 5b/5c run on committed
data only. Stage 5a needs an OpenAI-compatible endpoint; 6b needs a GPU (~8 min/member on an A10G).

Reproduce a number: `p4_score_zeroparam.py --agent qwen3-4b --tier T1` reproduces F5 byte-for-byte
(0a 0.54, 0d 0.55, 0o* 0.58 within-table). `test_zeroparam.py` must print `ALL PASS` after any change to `zeroparam.py`.

## 4. File map

```
README.md                 public overview and headline numbers
AGENTS.md                 this file
PREREGISTRATION.md        protocols P1-P5 and dated amendments (A-P1 ... A-P4b); hypotheses H1-H6, gates G1/G2
findings.md               results narrative F0-F8; superseded findings are kept and labelled [SUPERSEDED by ...]
research-log.md           append-only log, one STEP GATE checklist per step (format in program.md)
research-state.yaml       hypothesis status and experiment trajectory (machine-readable)
program.md                the research loop and its hard rules
scripts/
  setup_toxicbench.sh     clone ToxicBench into data/toxicbench at the pinned commit
  serve_vllm.sh           start a loopback-only vLLM server (Qwen3-4B default; MODEL/SERVED env for 8B)
experiments/
  requirements.txt        pinned versions used for every reported number
  common.py               ToxicBench trajectory iterator, pair keys, adapter families (stages 1-2)
  inventory.py            stage 0
  taxonomy.py             stage 1
  range_check.py          stage 2 (regex-scoped 0a/0b, sandboxed 0d, sanity rows, actual-preview check)
  gen_tasks.py            stage 3; also defines sandbox_exec used by later stages
  zeroparam.py            THE shared implementation of 0a/0b/0d/0r_log/0o/0o*, is_sum_type, FastTemplate
  test_zeroparam.py       unit tests for zeroparam.py (is_sum_type cases, template alignment)
  ksweep2.py              stage 4
  p4_run.py               stage 5a: tier-enforcing wrapper around ToxicBench's ReAct agent + logprob/verbalized capture
  p4_score_zeroparam.py   stage 5b
  p4_score_intrinsic.py   stage 5c
  run_day1.sh             runs stages 0-2
  scorer/build_dataset.py stage 6a
  scorer/train_scorer.py  stage 6b (Qwen2.5-0.5B + LoRA r=16, 5-quantile pinball head, bootstrap member)
  scorer/score_scorer.py  stage 6c (LOTO application, surprise/epistemic, sanity rows, coverage)
  scorer/run_loto.sh      runs stage 6
data/ours/
  datasets/               6 public tables (verbatim) + PROVENANCE.json (license, citation, sha256)
  tasks/large_tables_v2.jsonl   the 210 P3 tasks used everywhere (v1 = 180 tasks, superseded, kept for F3)
  ceiling.json, ceiling_events.jsonl, dropped_tasks.jsonl   stage 3 outputs
  ksweep2/                stage 4 events + summary
  p4/<agent>/<tier>/      stage 5 trajectories and scores. Tiers present: qwen3-4b {T0_agent, T1, T1r2, T3},
                          qwen3-8b {T0_agent, T1}. Qwen3-4B intrinsic signals exist only for T1r2 (the replication
                          run with logprobs); qwen3-8b has them for both tiers.
  scorer/                 stage 6 train/eval sets and scored eval files
docs/
  REVIEW_*.md             independent review of each round; amendments in PREREGISTRATION.md cite them
  references_verified.bib bibliography with verified entries
```

Not committed (see `.gitignore`): `data/toxicbench/` (external), `experiments/results/` (logs and stage 0-2
outputs, regenerated by `run_day1.sh`), `models/` (scorer members), `.venv/`.

## 5. Data schemas

P4 trajectory row (ToxicBench format + tier fields): `task_id, dataset, model, agent, tier, seed, environment
(clean|toxic), poison{type, scale, severity, poison_once}, oracle{clean_answer, ...}, tool_events[], final_answer,
metrics{task_success, poisoned_answer_used, recovery, anomaly_detection, ...}`.
Each `tool_events[]` item: `step, tool_name, args, clean_observation, returned_observation, was_poisoned,
poison_type, harness_normalization`.
Task row (`large_tables_v2.jsonl`): `task_id, dataset, user_query, poison{type, scale, severity, poison_once},
oracle{clean_value, poisoned_value, tolerance, ...}, meta{template (unfiltered|filtered|grouped), op, column,
filter, group, log2_scale, severity_logratio, code}`. Score files: one row per scored event with `label`
(1 = poisoned), `task_id, dataset, template, op, severity, y`, and one column per signal (e.g. `0a, 0d, 0o_star, 0r_log`).

## 6. Rules (do not break these)

1. **Protocol before results.** A new measurement gets a PREREGISTRATION.md section (or dated amendment) committed
   before the script produces numbers. Never edit an earlier section; append an amendment.
2. **Within-table AUROC is primary**, with a table-clustered bootstrap CI (6 tables). Pooled AUROC is secondary.
   Always report per template / severity, not only pooled.
3. **Sanity rows**: a signal's real number is reported only if it flags obviously corrupted values (AUROC > 0.95).
   Failing signals are reported as withheld/negative, not dropped.
4. **One implementation per signal**: all zero-parameter signals come from `zeroparam.py`. Run `test_zeroparam.py` after changes.
5. `data/toxicbench/` is read-only. Generated data goes under `data/ours/`.
6. No credentials in the repo. `p4_run.py` reads the API key from `$OPENAI_API_KEY`; vLLM binds to 127.0.0.1.
7. Summary tables in `findings.md` are written from script output, never hand-edited numbers.

## 7. Gotchas

- `findings.md` keeps every superseded version (e.g. F4 -> F4' -> F4'' -> F4'''). Cite the latest unsuperseded one.
  Current interpretation overrides historical claims as specified in F13 and `docs/CURRENT_CONCLUSIONS.md`.
  F4' refers to `ksweep.py`, which was removed (superseded by `ksweep2.py`).
- Commit SHAs quoted in PREREGISTRATION.md / research-log.md refer to the original development history, which is
  not part of this repository. "The plan" / `agent-uq-plan-FINAL.md` refers to private planning notes, not included.
- The k-sweep's 0o* = 0.73 at k = 5 uses **random** rows; agents see **head** rows, where 0o* is 0.58. Do not
  compare the two as if they were the same condition.
- `p4_run.py` applies three harness normalizations to agent code (drop `import pandas`, map `pd.read_csv(<known
  table>)` to the preloaded `df`, strip a stray indent). They are logged per event in `harness_normalization`;
  `p4_score_zeroparam.py` re-applies them so re-execution runs the code the agent ran.
- Pairing: the negative for each poisoned event is the first scalar `python_exec` event of the clean seed-0 run
  of the same task; in 4.2% of pairs the agent's code differs between the two runs (disclosed in F6).
- Only single-scalar returns are scored; multi-number returns are out of scope for every scalar signal.
- `gpt-5.4-mini` is registered in `p4_run.py` but has not been run.

## 8. Current revision / cached analysis

`experiments/audit_cached_revision.py` reads cached intrinsic/scorer/baseline files, validates support and writes a separate audit. `experiments/cached_metrics.py` carries same-task finite pairing and gate-aware reporting. `scorer/score_scorer.py --cached PATH` needs no torch/model weights. Intrinsic H1/H5 efficacy is withheld without live sanity; no global H1-confirmed label is valid across conflicting protocol versions. All six cached P5 configurations fail their own gates. Qwen context-pilot raw replies are missing; auxiliary scored records must not be represented as a full raw archive. No fresh model calls are required for these revisions.
