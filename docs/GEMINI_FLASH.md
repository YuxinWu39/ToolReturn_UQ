# Gemini Flash T1 replication

The A-P4-Gemini protocol was committed as `4fa7740` before generation.
This run uses Google's `gemini-3.8-flash` via its official OpenAI-compatible endpoint,
low reasoning effort, provider-default sampling, and independent clean repeats.
The model's sampling parameters differ from the Qwen runs. The request omits
temperature, seed and token logprobs. The integer stored in `seed` identifies the
replicate. The live response limit is 2,048 tokens and the shadow limit is 512.
Shadow calls retain the existing confidence prompt and must return exactly one
integer from 0 through 100. Other responses are stored and counted as missing.

## Run

Restore the pinned ToxicBench dependency and activate the Python analysis environment.
Set `GEMINI_API_KEY` in that environment. The runner also accepts `GOOGLE_API_KEY`.

```bash
bash scripts/setup_toxicbench.sh
python -B experiments/test_p4_gemini.py
python -B experiments/p4_run.py --agent gemini-3.8-flash --tier T1 --smoke
python -B experiments/p4_run.py --agent gemini-3.8-flash --tier T1 --run-tag _pilot --seeds 1 --limit 2
python -B experiments/p4_run.py --agent gemini-3.8-flash --tier T1 --seeds 2
python -B experiments/p4_summarize_gemini.py
```

Smoke defaults to `T1_smoke`. The four paired pilot trajectories go to `T1_pilot`.
The formal collection goes to `T1` and contains 210 rows in each of
`clean_seed0.jsonl`, `clean_seed1.jsonl` and `toxic_seed0.jsonl`.
Use a single writer per output directory and keep settings fixed when resuming.
Completed task IDs are skipped. An incomplete JSON line from a terminated write
requires inspection before resuming.

On macOS, Gemini-generated Python runs in a separate Seatbelt process.
The child receives the task and loads its datasets before installing the policy,
then evaluates model code with filesystem writes and networking denied.
The child environment excludes credentials. It has a 20-second CPU limit and
a 30-second wall-clock timeout. Other platforms use the existing tool environment
and require an appropriately isolated execution environment.

## Recorded evidence

Each completion records returned model ID, finish reason and token usage.
Shadow requests record their own metadata and raw answer. `after_observation.step`
identifies the tool event preceding the completion, including tool error events.
`generation_config` records the Gemini sampling and signal settings on each trajectory.

The summary checks for exactly one row per task per run, then matches confidence
to the selected scalar event by step. Primary H5 uses paired subtle tasks.
Plausible plus subtle is secondary. Constant scores within a table receive AUROC 0.5.
The interval resamples contributing tables 2,000 times with RNG seed 1.
The summary reports eligible and paired tasks and every contributing table.
Low scalar coverage or missing tables limits the scope of the estimate.

The upstream `anomaly_detection` metric checks terms in the final answer.
Its count is reported as a detector flag. Manual interpretation of actual
checking behavior requires examining the tool calls and final text.

## Pilot observations

The fixed 20 clean smoke tasks all produced final answers and passed the upstream
task-success check. Two tool returns were scalar under the existing parser.
Nineteen of 20 confidence requests returned a valid integer. The remaining response
appended a JSON action to the number and was counted as missing.

Both of the first two tasks succeeded in clean mode. Both toxic runs triggered
poisoning, failed task success, and matched the upstream poisoned-answer-used flag.
One paired task had scalar returns on both sides. These observations are integration
checks and are excluded from the formal H5 calculation.

The local execution environment uses Python 3.11.13, NumPy 1.26.4 and pandas 2.2.3.
It differs from the original pinned requirements. Actual run metadata records the
task-file hash and runner hashes. The formal collection uses twelve disjoint task
shards and verifies all 630 task/replicate combinations before merging.

[Google model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)
and [OpenAI compatibility documentation](https://ai.google.dev/gemini-api/docs/openai).
