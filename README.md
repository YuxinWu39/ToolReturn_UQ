# ToolReturn_UQ

**Can anything tell a corrupted tool return from a clean one, at the moment an LLM agent receives it?**

A data-analysis agent writes pandas code, a `python_exec` tool runs it on a CSV table and returns a number, and
the agent reports that number as its answer. We corrupt the returned number (multiply it by 1.05-2x or the
reciprocal) and ask which uncertainty signals can flag it, as a function of how much of the table the agent
(and any checker limited to the agent's context) has seen.

## Headline results

| Finding | Number |
|---|---|
| Agents (Qwen3-4B, Qwen3-8B) use the corrupted value as their answer | 83-93% of poisoned runs; 0 challenges in 3,780 trajectories |
| Observation failures (misled by the return, not incapable), noise-corrected, original ToxicBench | 55% of failures (43% numerical) |
| Zero-parameter checks on the rows the agent saw (head-5) | within-table AUROC 0.53-0.58 |
| Agent-intrinsic signals (verbalized confidence, token entropy) | 0.46-0.56 |
| Clean-only learned scorer (Qwen2.5-0.5B + LoRA, quantile head) | 0.50-0.52 (pre-registered prediction 0.55-0.70 missed) |
| Information curve, k random visible rows: bootstrap check 0d / draw-conditioned oracle 0o* | 0.62 / 0.73 at k=5 -> 0.85 / 0.90 at k=200 |

Reading: under the default observation context (first 5 rows) nothing tested separates poisoned from clean
returns; the k-sweep shows the limit is the information in the visible rows, which rises with k.
Scope: numeric, single-scalar tool returns on tabular data; one corruption type (scaling); two open-weight
agents from one model family. Full narrative and every caveat: [findings.md](findings.md).

## Quick start

```bash
bash scripts/setup_toxicbench.sh                       # clone the ToxicBench dependency at the pinned commit
python3 -m venv experiments/.venv
experiments/.venv/bin/pip install -r experiments/requirements.txt
cd experiments
.venv/bin/python test_zeroparam.py                     # unit tests (no GPU)
.venv/bin/python p4_score_zeroparam.py --agent qwen3-4b --tier T1   # reproduces F5 from committed trajectories
```

All agent trajectories and scored events are committed under `data/ours/`, so every number in
`findings.md` except the agent runs themselves can be recomputed on a CPU. See [AGENTS.md](AGENTS.md) for the
end-to-end pipeline and what every file does.

## Method in one paragraph

Every step is pre-registered: the hypothesis, the statistic and the pass/fail threshold are written to
[PREREGISTRATION.md](PREREGISTRATION.md) before the script that tests them produces a number, and amendments are
appended rather than rewritten. AUROC is reported within-table (table-clustered bootstrap CI) as well as pooled,
and every signal must pass a sanity row (an obviously corrupted value is flagged with AUROC > 0.95) before its
real number is reported. Independent reviews of each round are in [docs/](docs/).

## Data and licenses

- ToxicBench (turambar928/Toxic_Tool_Bench): MIT code, CC BY 4.0 data; cloned, not redistributed, except for
  derived events in `data/ours/scorer/`.
- Six public tables in `data/ours/datasets/` (Palmer Penguins CC0; UCI Auto MPG, Bike Sharing, Wine Quality,
  Abalone, Student Performance, CC BY 4.0). Sources, citations and SHA-256 hashes: `data/ours/datasets/PROVENANCE.json`.
- Agent outputs were generated with Qwen3-4B and Qwen3-8B (Apache 2.0).
