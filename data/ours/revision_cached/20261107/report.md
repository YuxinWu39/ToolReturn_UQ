# Cached-output revision audit

Retrospective diagnostics, not a new confirmatory test. No model calls.

AP is average precision. Paired controls use the same task; primary AUROC equally weights tables.

## H1 version diagnostics

All intrinsic efficacy headlines withheld: no live sanity controls. Original A-P4 subtle/AP and A-P4b P+S/upper-CI rules differ.

| Agent/tier | Signal | Slice | Pairs/eligible | Tables | AUROC [CI] | AP | Base |
|---|---|---|---:|---:|---|---:|---:|
| gemini-3.8-flash/T1 | sig3_neg_conf | severity:subtle | 7/73 | 3 | 0.556 [0.5, 0.667] | 0.556 | 0.500 |
| gemini-3.8-flash/T1 | sig1_mean_entropy | severity:subtle | 0/73 | 0 | NA  | NA | NA |
| gemini-3.8-flash/T1 | sig3_neg_conf | plausible+subtle | 17/178 | 5 | 0.520 [0.5, 0.56] | 0.520 | 0.500 |
| gemini-3.8-flash/T1 | sig1_mean_entropy | plausible+subtle | 0/178 | 0 | NA  | NA | NA |
| qwen3-4b/T1r2 | sig3_neg_conf | severity:subtle | 65/73 | 6 | 0.521 [0.469, 0.574] | 0.540 | 0.500 |
| qwen3-4b/T1r2 | sig1_mean_entropy | severity:subtle | 65/73 | 6 | 0.455 [0.387, 0.532] | 0.521 | 0.500 |
| qwen3-4b/T1r2 | sig3_neg_conf | plausible+subtle | 162/178 | 6 | 0.555 [0.505, 0.606] | 0.553 | 0.500 |
| qwen3-4b/T1r2 | sig1_mean_entropy | plausible+subtle | 162/178 | 6 | 0.442 [0.393, 0.493] | 0.494 | 0.500 |
| qwen3-8b/T0_agent | sig3_neg_conf | severity:subtle | 54/73 | 6 | 0.572 [0.534, 0.61] | 0.551 | 0.500 |
| qwen3-8b/T0_agent | sig1_mean_entropy | severity:subtle | 62/73 | 6 | 0.524 [0.413, 0.629] | 0.593 | 0.500 |
| qwen3-8b/T0_agent | sig3_neg_conf | plausible+subtle | 124/178 | 6 | 0.578 [0.538, 0.619] | 0.556 | 0.500 |
| qwen3-8b/T0_agent | sig1_mean_entropy | plausible+subtle | 150/178 | 6 | 0.506 [0.434, 0.577] | 0.547 | 0.500 |
| qwen3-8b/T1 | sig3_neg_conf | severity:subtle | 67/73 | 6 | 0.521 [0.467, 0.582] | 0.519 | 0.500 |
| qwen3-8b/T1 | sig1_mean_entropy | severity:subtle | 67/73 | 6 | 0.469 [0.4, 0.535] | 0.534 | 0.500 |
| qwen3-8b/T1 | sig3_neg_conf | plausible+subtle | 164/178 | 6 | 0.533 [0.498, 0.565] | 0.522 | 0.500 |
| qwen3-8b/T1 | sig1_mean_entropy | plausible+subtle | 164/178 | 6 | 0.483 [0.449, 0.515] | 0.531 | 0.500 |

The balanced-pair base rate is 0.5: AP < 2×base means AP < 1, a weak/non-discriminating criterion. AP aggregation was not fully specified originally.

## P5 gates and common support

| Cache | Coverage | High sanity | Low sanity | Constant surprise tables (all) | Common P+S pairs/tables | Gain |
|---|---:|---:|---:|---:|---|---|
| eval_qwen3-4b_T0_agent_scorer | 0.167 | 0.845 | 0.664 | 0 | 15/5 | withheld-scorer-gate-failed |
| eval_qwen3-4b_T1_scorer | 0.176 | 0.852 | 0.673 | 0 | 15/5 | withheld-scorer-gate-failed |
| eval_qwen3-4b_T1r2_scorer | 0.183 | 0.851 | 0.679 | 0 | 14/4 | withheld-scorer-gate-failed |
| eval_qwen3-4b_T3_scorer | 0.185 | 0.826 | 0.698 | 0 | 0/0 | withheld-scorer-gate-failed |
| eval_qwen3-8b_T0_agent_scorer | 0.176 | 0.866 | 0.640 | 0 | 29/6 | withheld-scorer-gate-failed |
| eval_qwen3-8b_T1_scorer | 0.147 | 0.854 | 0.650 | 0 | 29/6 | withheld-scorer-gate-failed |

All rows above are diagnostics. Gate-failed scorer instances cannot establish learned UQ failure or the registered gain. Constant dual-class tables now contribute 0.5; missing-class tables do not.

Full JSON includes per table/severity/template metrics, finite paired coverage, pooled secondary metrics, baseline support and input SHA-256. Baseline matching checks cached return and metadata, not full raw event identity.
