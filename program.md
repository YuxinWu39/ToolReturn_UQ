# program.md — how experiments are run in this repo

Adapted from karpathy/autoresearch `program.md` (commit-before-run, results.tsv, keep/discard) and
AI-research-SKILLs `0-autoresearch-skill` (two loops, protocol-lock commits, confirmatory vs
exploratory, findings.md as memory). Goal that every rule serves: **a 6-8 page ICLR 2027 workshop
paper by 2027-02-01**. Anything that does not feed a figure, table, or claim in that paper is scope creep.

## Files

| File | Role | Who edits |
|---|---|---|
| `PREREGISTRATION.md` | hypotheses, thresholds, operational definitions. Committed BEFORE the code that tests them runs. | agent, with human sign-off before the first GPU run |
| `research-state.yaml` | current hypothesis status, experiment trajectory, outer-loop decisions | agent after every step |
| `findings.md` | the paper's narrative in progress: what we know, what it rules out, what figure it becomes | agent after every result |
| `research-log.md` | append-only: one entry per step with the step gate filled in | agent |
| `results.tsv` | one row per experiment run (karpathy format), untracked | agent |
| `experiments/*.py` | one script per stage, resumable, writes to `experiments/results/` | agent |

## Loop

```
1. Pick the next step from research-state.yaml (highest-priority pending hypothesis / pilot gate).
2. Write or update PREREGISTRATION.md for exactly what this step measures and what counts as pass/fail.
3. git commit  -m "research(protocol): ..."          <- protocol commit, no results in it
4. Write the script. Run it:  ./run_*.sh > run.log 2>&1   (never tee into context)
5. Read results via grep / the script's summary JSON, not the raw log.
6. Fill the STEP GATE (below) in research-log.md. If any gate item fails, fix or mark exploratory.
7. Update findings.md (narrative) and research-state.yaml (status, trajectory).
8. git commit  -m "research(results): ..."           <- results commit, separate from protocol
9. Outer loop every ~3 steps or whenever a gate fails: deepen / broaden / pivot / conclude, written to research-log.md as "research(reflect)".
```

Karpathy rules kept verbatim in spirit: the first run of anything is the baseline; simpler beats
complex at equal result; crashes are logged not hidden; results.tsv is tab-separated and untracked.

## STEP GATE (fill for every step; copy into research-log.md)

```
Step: <name>                          Date:
1 Protocol-before-results  commit <sha> precedes <sha>?                      [ ]
2 Hypothesis served        which of H1-H6 / pilot gate / paper figure?       [ ]  (if none -> scope creep, stop)
3 Sanity check             what was checked, what would a bug look like?     [ ]
4 Confirmatory/exploratory which label, and why?                              [ ]
5 Claim scope              does this result widen or narrow a claim in       [ ]
                           agent-uq-plan-FINAL.md? update the plan if so
6 Reviewer objection       strongest one-line objection to this step's       [ ]
                           output, and the response or the limitation added
7 Workshop fitness         does it bring the 6-8 page paper closer, or is it [ ]
                           a nice-to-have? (MATH4AI 11/20 and ICLR 02/01 are the clocks)
Verdict: PASS / PASS-AS-EXPLORATORY / FAIL(->fix)
```

Items 5-7 are the rigor-reviewer dimensions (evidence relevance, claim scope, logical flow) from
`22-agent-native-research-artifact/rigor-reviewer`, collapsed to what a single step can answer.
At milestones (end of day 1-3 pilot, first matrix, scorer trained, before writing) dispatch an
independent reviewer subagent with the full rigor-reviewer checklist instead of self-grading.

## Hard rules

- Protocol commit before result commit, always. The git log is the pre-registration.
- Pooled numbers are never the only numbers: per table, per severity, per adapter, within-table AUROC.
- Every signal must pass the sanity row (fully corrupted observation -> flagged) before its real number is reported.
- `data/toxicbench/` is read-only. Our generated tasks and CSVs live under `data/ours/`.
- No credentials in the repo. API keys and endpoints come from the environment or an untracked `api` file.
- Do not ask the human for routine go-aheads; ask only when a gate fails in a way that changes the paper's claim, or when money/accounts are involved (GPU, API spend).
