# ToolReturn_UQ

**Which checks can distinguish corrupted numeric tool returns using the evidence visible to an agent?**

We study scalar pandas-tool returns on six public tables. Corruption multiplies the return by 1.05–2 or its reciprocal while leaving source data unchanged. Agent trajectories, fixed-return context pilots, and offline statistical checks answer different questions and are reported separately.

## Current findings and limits

New: [Gemini Experiment A](docs/EXPERIMENT_A_RESULTS_2026-11-08.md) completed 810 paired cells on 30 selected queries. Check-aid versus raw discrimination improves by 0.094 [0.050, 0.133], with clean acceptance 88/90 to 90/90. Gains primarily involve rejection/abstention, not correcting corrupted numeric answers; C is mixed-runtime diagnostic only.

The current interpretation is in [CURRENT_CONCLUSIONS.md](docs/CURRENT_CONCLUSIONS.md). A full-structure [working manuscript](paper/manuscript.md) and [writing status](paper/README.md) now organize the existing evidence; this is an author draft, not a submission PDF. It supersedes stronger historical claims in the append-only findings log.

| Evidence | Result | Scope |
|---|---|---|
| Fixed-return context pilots, 12 queries / 6 tables | Gemini primary contrast +0.083 [−0.167, 0.333]; Qwen 0.000 [−0.333, 0.333] | No stable cross-model benefit established; not evidence of equivalence or no context effect |
| Bootstrap check on the original matched20 packets | Flags 10/12 corrupt and 1/12 clean returns; within-table AUROC 0.917 [0.833, 1.000] | Same visible rows; structured query and extra computation differ from model prompting |
| Independent matched20 draws, same 12 queries | Flags 161/240 corrupt and 14/240 clean; within-table mixture AUROC 0.818 [0.718, 0.915] | 20 draws/query, still only 6 table clusters; no new model responses |
| Learned scorer, six saved agent/tier evaluations | All fail sanity and clean coverage gates | This training configuration did not yield an eligible detector; no general learned-UQ failure claim |
| Agent confidence / entropy | Cached diagnostics available; efficacy withheld | Missing live sanity; H1 protocol versions conflict; Gemini subtle paired coverage 7/73 |

On the selected tasks, some statistical checks extract signal from the displayed evidence, while merely supplying query-related rows has not established reliable model checking. These experiments do not prove an information ceiling, identify an internal model mechanism, establish a new algorithm, or measure deployment benefits. The privileged Monte Carlo scores 0o/0o* are empirical references, not optimality bounds.

## Reproduce cached analyses

```bash
bash scripts/setup_toxicbench.sh
python3 -m venv experiments/.venv
experiments/.venv/bin/pip install -r experiments/requirements.txt
experiments/.venv/bin/python experiments/audit_cached_revision.py --out /tmp/toolreturn-cached-audit
experiments/.venv/bin/python experiments/scorer/score_scorer.py --cached data/ours/scorer/eval_qwen3-4b_T1_scorer.jsonl --out /tmp/toolreturn-scorer-summary.json
```

The revision audit needs cached files and CPU libraries, not model weights or API calls. It records input hashes, paired support, table-bootstrap intervals, AP and sanity gates. See the [audit report](data/ours/revision_cached/20261107/report.md), [version ledger](docs/HYPOTHESIS_LEDGER_2026-11-07.md), [nearest-work comparison](docs/RELATED_WORK_POSITIONING.md), and [revision response](docs/REVISION_2026-11-07.md). The original five-seat review remains in [docs/final_review_2026-11-07/](docs/final_review_2026-11-07/).

Historical protocols are preserved in [PREREGISTRATION.md](PREREGISTRATION.md), with appended corrections. The latest cached audit is retrospective, not a new confirmatory experiment. Within-table AUROC is primary; pooled values are secondary. Failed or absent sanity gates withhold efficacy headlines.

## Archive and licenses

Main P4 trajectories and scores are committed under `data/ours/`. Both fixed-return pilots now archive all 72 original replies per model. The Qwen originals were recovered in `e9e3577`; manifest/request hashes, provider metadata, strict parsing and saved scoring were verified, and its full summary was regenerated without model calls. See the [raw archive audit](docs/QWEN_RAW_ARCHIVE_2026-11-07.md). The 12-query/six-table exploratory scope and absent live sanity controls remain. Gemini instructions: [GEMINI_FLASH.md](docs/GEMINI_FLASH.md). Pipeline guide: [AGENTS.md](AGENTS.md).

- ToxicBench dependency: MIT code, CC BY 4.0 data; cloned rather than redistributed, except derived scorer events.
- Six public tables: Palmer Penguins CC0; UCI Auto MPG, Bike Sharing, Wine Quality, Abalone and Student Performance CC BY 4.0. [Sources, licenses and hashes](data/ours/datasets/PROVENANCE.json).
- Open-model agent outputs: Qwen3-4B and Qwen3-8B (Apache 2.0); additional Gemini Flash outputs are separately archived.
