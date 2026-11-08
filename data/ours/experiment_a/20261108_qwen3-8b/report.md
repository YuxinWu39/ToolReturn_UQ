# Qwen3-8B Experiment A replication (raw/check arms)

540 completed trajectories on the frozen Gemini Experiment A inputs; 30 queries, three row draws, six tables.

| Arm | Candidate | Accept | Reject | Uncertain | Invalid | Correct numeric | Null |
|---|---|---:|---:|---:|---:|---:|---:|
| raw | clean | 90/90 | 0 | 0 | 0 | 90 | 0 |
| raw | scale110 | 90/90 | 0 | 0 | 0 | 0 | 0 |
| raw | scale150 | 83/90 | 6 | 1 | 0 | 0 | 7 |
| check | clean | 84/90 | 3 | 3 | 0 | 84 | 6 |
| check | scale110 | 49/90 | 40 | 1 | 0 | 0 | 41 |
| check | scale150 | 13/90 | 77 | 0 | 0 | 0 | 77 |

## Registered primary: check minus raw

- discrimination: 0.550 [0.306, 0.756]
- clean_acceptance: -0.067 [-0.111, -0.022]
- Joint benefit rule met: False.

## Exploratory: flag-only policy (accept iff 0d flag absent)

| Model | check minus flag-only [95%] | flag-only minus raw [95%] |
|---|---|---|
| qwen3-8b | -0.028 [-0.061, 0.000] | 0.578 [0.367, 0.756] |
| gemini-3.8-flash | -0.017 [-0.078, 0.039] | 0.111 [0.078, 0.156] |

Flag following (check arm): accepted 0/120 flagged candidates; rejected 0/150 compatible candidates.

## Limits

- Same 30 reused queries/six tables as Gemini Experiment A; no fresh-table generalization.
- Three row draws/query are not extra queries or tables; one completion per cell.
- B-A tests the full check-aid package, not warning text versus statistical content.
- Flag-only comparison was specified after seeing Gemini results; exploratory.
- Qwen and Gemini sampling settings differ; no model-comparison test.
- No end-to-end recovery, cost or runtime-placement claim; null is not correct.
