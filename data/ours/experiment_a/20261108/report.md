# Gemini Experiment A: paired monitor intervention

Final analysis of 810 completed trajectories; 30 selected queries, three row draws, six tables.

| Arm | Candidate | Accept | Reject | Uncertain | Invalid | Correct numeric | Null |
|---|---|---:|---:|---:|---:|---:|---:|
| raw | clean | 88/90 | 0 | 0 | 2 | 88 | 0 |
| raw | scale110 | 60/90 | 8 | 8 | 14 | 0 | 10 |
| raw | scale150 | 25/90 | 52 | 6 | 7 | 0 | 53 |
| check | clean | 90/90 | 0 | 0 | 0 | 90 | 0 |
| check | scale110 | 52/90 | 30 | 3 | 5 | 0 | 32 |
| check | scale150 | 20/90 | 66 | 1 | 3 | 0 | 66 |
| code (runtime-mixed diagnostic) | clean | 82/90 | 0 | 0 | 8 | 82 | 0 |
| code (runtime-mixed diagnostic) | scale110 | 48/90 | 15 | 6 | 21 | 1 | 14 |
| code (runtime-mixed diagnostic) | scale150 | 14/90 | 47 | 3 | 26 | 0 | 48 |

## Registered primary: check minus raw

- discrimination: 0.094, descriptive interval [0.049999999999999996, 0.13333333333333333].
- clean_acceptance: 0.022, descriptive interval [0.0, 0.044444444444444446].
- Joint benefit rule met: True.

Joint rule requires discrimination lower bound >0 and clean-acceptance lower bound >=−0.05. Passing does not establish population noninferiority or deployed net benefit.

## Request and tool cost

| Arm | Logical requests | HTTP attempts | Python calls | Python errors | Prompt tokens | Completion tokens | Reported total tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| raw | 270 | 271 | 0 | 0 | 436377 | 20058 | 522577 |
| check | 270 | 270 | 0 | 0 | 477214 | 20845 | 545146 |
| code | 490 | 490 | 220 | 16 | 851534 | 37640 | 891821 |

Usage fields are preserved as returned; total may include reasoning categories not separately itemized. HTTP time includes failed attempts; tool time is separate. No currency-cost or equal-budget claim.

## Limits

- Reused selected queries/six public tables; no fresh-table generalization.
- Three row draws/query are not extra queries or tables; one model sequence/cell.
- B-A tests a full check-aid package, not a warning-versus-statistical-content mechanism.
- C has extra computation and requests; no equal-cost or placement-superiority claim.
- No end-to-end recovery policy evaluated; null is not correct; confidence efficacy withheld.
- Six-table bootstrap intervals are descriptive; no calibrated noninferiority or acceptance probability.
- C spans a synthetic-demonstrated pre-repair internal-import limitation and a repaired runtime; no identifiable main internal-import errors were observed. Do not infer model computation limits or fair C superiority. All pre-repair replies retained byte-for-byte.
