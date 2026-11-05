# Independent review: Day 1-3 pilot (P1 taxonomy, P2 range check)

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's-advocate (checkpoint 2, after analysis).
Date: 2026-10-31. Scope: `program.md`, `PREREGISTRATION.md` (P1, P2), `experiments/{common,taxonomy,range_check}.py`,
both `summary.json`, `pairs.jsonl`, `events.jsonl`, `findings.md`, `research-log.md`, `research-state.yaml`,
`results.tsv`, `.git/logs/HEAD`, and `agent-uq-plan-FINAL.md`.

**Method note.** This review session had no shell tool, so I could not run `git log` or the venv Python.
I read `.git/logs/HEAD` directly for commit order and recomputed numbers with regex line counts over
`pairs.jsonl` and `events.jsonl` (each line is one JSON row with fixed key order, so a count of matching
lines is an exact count). Every recomputed number below says how it was obtained.

## Verdict

**GO-WITH-CHANGES. Do not activate the "rules suffice" fork. Re-decide G1 before C2 is kept.**

- G1 PASS is real arithmetic but tests the wrong null. With one clean and one toxic run per pair, run-to-run
  noise alone produces an observation share near 0.45, far above the 0.15 threshold. G1 cannot fail for a
  high-success agent, so it does not support C2 yet.
- G2 is not decidable on this data. All 811 in-scope events are on 3-12-row tables (zero on the 3 large
  tables). On 340 of them T1 is identical to T0, and the rest differ only slightly. So the G2 statistic is,
  in practice, the T0 number that P2 itself labelled "expected, not a finding". On the plan's own primary
  slice (plausible+subtle) the same statistic is 0.862, below the threshold.
- The paper question survives. What the pilot actually shows is that detection on ToxicBench is limited
  by coverage, and the coverage limit is partly an artifact of a regex parser. A stronger zero-parameter
  baseline (re-executing the agent's code on visible rows) has to be tested before claiming learned
  signals are needed for the filtered 66%.

## Spot-checks (recomputed)

| Quantity | Claimed | Recomputed | How |
|---|---|---|---|
| observation pairs | 682 | 682 | count `"class": "observation"` in pairs.jsonl |
| capability pairs | 452 | 452 | same |
| observation share | 0.6014 | 682/1134 = 0.6014 | from the two counts |
| numerical observation | 375 | 375 | `"family": "numerical".*"class": "observation"` |
| silent override | 301 (8%) | 301/3633 = 8.3% | count `no_effect_override` |
| poisoned in-scope events | 283 | 283 | `"poisoned": true` in events.jsonl |
| poisoned events flagged by 0a at T1 | n/a | 257/283 = 90.8% (mean op 201/201, sum op 56/82) | 0a_T1 > 0 |
| clean events flagged by 0a at T1 | n/a | 20/528 = 3.8%; **all 20 have y = 2.0** | 0a_T1 > 0 and y = 2.0 |
| in-scope events on public (large) tables | n/a | **0** | `"dataset": "public_` |
| in-scope events on tables > 5 rows | n/a | 471/811 (140 poisoned); the other 340 have T1 ≡ T0 exactly | dataset list from inventory.json |
| plausible aggregate_scale flagged at T1 | n/a | 99/125 = 79%; summary AUROC 0.862 | severity filter |

Consistency check: if 0a is treated as a binary flag, AUROC ≈ 0.5·(1 + TPR − FPR) = 0.5·(1 + 0.908 − 0.038)
= 0.935, close to the reported 0.928. On these tables, 0a@T1 behaves as a binary "outside the column's range" flag.

**Bug found while spot-checking.** The 20 clean false positives all score y = 2.0. In
`20260707-181347_smolagents_toolcalling_Qwen3.6...` the returned observation is
`ERROR: FileNotFoundError: [Errno 2] No such file or directory: 'toy_sales.csv'`. `scalar()` takes the single
number in the string, so `[Errno 2]` becomes the "result" 2.0. Error strings are in scope as clean negatives.
This lowers AUROC (poisoned events are never errors, because the poisoner only fires on the oracle line), so
the reported 0.92 is conservative on this point. It still violates the "sanity check" gate item that was ticked.

## A. Protocol fidelity

Commit order (from `.git/logs/HEAD`, epoch converted to UTC): init `571f732` and protocol `43247bb` both at
23:31:29; results `0b60ad6` at 23:35:27; state update `b17c7f0` at 23:36:05. File mtimes: `common.py` 23:31,
`taxonomy.py` 23:32, `range_check.py` 23:33, `taxonomy/summary.json` 23:32, `range_check/summary.json` 23:34.
The protocol text does precede the results commit. But `experiments/results/` and `results.tsv` are
gitignored, so git cannot show that results came after the protocol; only mtimes do. The log admits the
protocol commit is empty because P1/P2 went in with init. Scripts were finalised after the protocol commit,
which is the correct order. `run_day1.sh` still has both steps commented out, so the exact command lines
(including `--boot`) are not recorded.

| # | Deviation | Where | Class |
|---|---|---|---|
| A1 | Error strings parsed as scalars (`[Errno 2]` → 2.0); 20 clean negatives get high scores | `range_check.scalar` | **needs fix + disclosure** (conservative bias, but the ticked sanity gate was wrong) |
| A2 | Out-of-scope regex is broader than P2: also excludes `.iloc[`, `.where(`, `nlargest/nsmallest`, `sort_values`, `idxmax/idxmin`. P2 lists only `df[df[`, `.groupby`, `.loc[`, `.query(` | `OUT_OF_SCOPE` | needs disclosure (moves events from in-scope to "filter_or_groupby") |
| A3 | Column must be accessed on a variable named `df`; any other name is `no_match`. Coverage then depends on adapter code style, not on query type | `COL_OP` | needs disclosure |
| A4 | The op-aware rule is promised for 6 ops; only mean (609), sum (201) and count (1) occur. median/min/max are untested | ops in summary | needs disclosure |
| A5 | T0 is computed from the CSV in `datasets/`, not from the preview event the agent received. P2 asserts these are identical "because tables are frozen" but this was not checked against the 7,858 preview events, and runs without a preview call are scored at T0 anyway | `Table.visible` | needs disclosure; check before P3 (one join on preview `numeric_min/max`) |
| A6 | G2 per-type AUROC uses aggregate_scale positives against **all** 528 negatives, from every table and task. P2's "pooled AUROC ... on aggregate_scale events" is ambiguous, and the within-table version of the G2 statistic was not computed | `per_poison_type` | needs disclosure; ambiguity in the pre-reg itself |
| A7 | Bootstrap: the code default is 2,000, matching P2. I found no evidence of a 1,000-resample run, but the command line was not recorded, so the count cannot be confirmed. P2 also promised 10,000 for the paper run | `--boot` | harmless if 2,000; record the command |
| A8 | Within-table AUROC uses 9 tables, unweighted mean, no CI | `within_table` | needs disclosure |
| A9 | Sanity row (fully corrupted return → AUROC > 0.95) not run. `program.md` makes this a hard rule before any real number is reported | absent | **needs fix** |
| A10 | 0b with std = 0: the plan specifies `|y−mean|/(|mean|+1e-6)` plus a flag; the code divides by `std+1e-9`, which creates extreme scores at T2 (2 rows) | `scores` | harmless for ranking at T0/T1; disclose for T2 |
| A11 | The plan's column fallback ("first numeric column, logged") is replaced by dropping the event | `parse_code` | harmless (consistent with P2), disclose vs plan |
| A12 | The plan's Day 1-3 says "existing **Qwen3-4B** trajectories". None exist; the pilot uses gpt-5.4-mini (63% of pairs), Sonnet, Haiku, Qwen3.6-35B | data | needs disclosure; affects which agent G2 speaks for |
| A13 | Threshold conflict in the master plan: Contributions says fork at **> 0.90**, Timeline says GO/NO-GO at **> 0.95**. P2 picked 0.90. The observed 0.923 lies between them, so the fork fires only under the lower threshold | plan vs P2 | **invalidates the fork activation** until a single threshold is set by a dated amendment |
| A14 | The plan's primary metric is "subtle+plausible tiers". G2 pools obvious events, which are 158 of 283 positives. On plausible alone, 0a@T1 = 0.862 | P2 vs plan | **invalidates** reading G2 as satisfying the plan's fork rule |
| A15 | P1 "first by file order": `sorted(glob)` puts timestamped files before named files (`autogen_guarded_..._combined`), and clean and toxic are chosen independently. A pair's clean and toxic runs can come from different batches. 831 keys are affected. Not checked | `pair_runs` | needs disclosure + a same-source check |
| A16 | P1 has no tolerance handling. ToxicBench's ~10% tolerance grades some 1.1x poisons as correct, so they land in no_effect. The log acknowledges this | `classify` | needs disclosure (already in limitations) |
| A17 | "Exposed" means any `was_poisoned` event in the toxic run, not that the poisoned value was consumed. `observation` does not require `poisoned_answer_used` | P1 itself | needs disclosure; validity issue, see C(i) |
| A18 | The plan's harness-limit class (budget exhaustion excluded from capability, per 2610.21098) is not implemented | P1 vs plan | needs disclosure |
| A19 | Research log reports coverage as "811/4182 python_exec events". 4,182 is the number **skipped**. The true total is 811 + 4,182 = 4,993, so in-scope coverage is **16.2%**, not 19.4% | research-log.md | needs correction |
| A20 | findings F2(b) says "75% of poisoned python_exec events use filters/groupby". Filters/groupby/sort account for 764/1153 = **66%**. 75% is the share out of scope for any reason (multi-aggregation 6.8%, no match 1.8%, non-scalar 0.6% make up the rest) | findings.md | needs correction |

## B. Are the gate decisions correct?

### G1 PASS: arithmetically correct, statistically uninformative

Under the null that the poison has **no effect**, a pair's clean and toxic runs are two independent draws
with success probability p. Then P(capability) = 1 − p and P(observation-like) ≈ p(1 − p), so the expected
share is p/(1 + p). The observed clean success rates give:

| Slice | clean success p | null share p/(1+p) | observed share | P(toxic fails \| clean ok): observed vs null 1−p |
|---|---|---|---|---|
| overall | 1 − 452/3633 = 0.876 | **0.467** | 0.601 | 734/3181 = 23.1% vs 12.4% |
| numerical | 1 − 387/1888 = 0.795 | **0.443** | 0.492 | 415/1501 = 27.6% vs 20.5% |

The 0.15 threshold sits far below the null, so G1 would pass with zero poison effect. The real signal is the
excess: about +10.6 pp overall and +7.1 pp numerical. Under homogeneous p, up to 54% (overall) and 74%
(numerical) of "observation" pairs could be run-to-run noise. This is an upper bound: if p varies across
tasks, discordance under the null is E[p(1−p)] < p̄(1−p̄), so the true noise share is smaller. It has to be
measured, not assumed.

The fix needs no new runs:
1. Split `capability` into `cap_both_fail` and `cap_clean_only_fail` (clean fails, toxic succeeds). The second
   group is the mirror-image discordant cell. A McNemar test on (clean ok, toxic fail) vs (clean fail, toxic ok)
   is the correct paired test.
2. Use the 831 keys with duplicate runs to estimate clean-vs-clean discordance directly. That is the
   empirical noise floor.
3. Restate G1 as "excess toxic-failure rate over the noise floor, with a clustered CI that excludes 0", and
   report a noise-corrected observation share.

### G2 fork: not meaningful on this data

- **T0 ≈ T1 by construction.** 340/811 in-scope events are on ≤5-row tables, where head-5 is the whole
  table. The other 471 are on 6-12-row tables. No in-scope event is on the 3 large tables. P2 pre-stated that
  T0 "is near 1.0 because the preview leaks the exact bound" and called it "not a finding". G2's T1 statistic
  measures nearly the same thing.
- **The rule's output is set by the poison generator.** Every poisoned `mean` event (201/201) falls outside
  the column range. Misses come only from `sum`, where [n·min, n·max] is wide. So the AUROC measures what
  share of ToxicBench's aggregate_scale magnitudes exceed a tiny table's range. That is a property of the
  benchmark, not of the signal.
- **Fixed slice and threshold matter.** Plausible-only gives 0.862. Under the plan's 0.95 timeline threshold
  the fork fails even pooled.
- **Coverage is ignored.** "Rules suffice" is a claim about all corrupted returns. A statistic computed on 25%
  of poisoned events, selected by query simplicity, cannot support it.

Recommended state change: G2 `supported-provisional` → `undecidable-on-original-tables`. Do not pull env-2 forward.

### What P3 should pre-register so G2 can be re-decided cleanly

1. **Single decision statistic and threshold.** Within-table AUROC of 0a at T1 (head-5, min/max removed) on
   aggregate_scale, **plausible+subtle only**, tables ≥ 50 rows (report ≥ 200 separately). The fork fires
   only if the **lower** 95% clustered-CI bound exceeds one threshold (choose 0.90 or 0.95 in a dated
   amendment that also fixes the plan text).
2. **Coverage condition in the fork.** "Rules suffice" also requires coverage ≥ X% of poisoned events
   (pre-commit X, for example 50%). Also report a **system-level AUROC** over all python_exec events, where
   events the rule cannot parse get a fixed neutral score. This is the only number that compares fairly with
   learned signals, which score every event.
3. **Task mix that preserves query complexity.** `gen_tasks.py` must emit filtered, grouped and
   multi-aggregation queries in pre-committed proportions, for example matching the original 66% filter
   share. Otherwise the generator inflates 0a's coverage by producing only unfiltered `df['c'].mean()` tasks.
   The `evidence_controls_v4.py` recipe already supports equality filters, so use them.
4. **Severity defined relative to the visible data, not only as a scale.** Keep {1.05, 1.1, 1.2, 1.35, 1.5, 2.0}
   and add the mirrored values (0.95 ... 0.5). Also log the displacement in units of the visible column's
   std and range, because 0a is deterministic in that displacement. Report 0a as a ceiling curve against
   displacement rather than as a pooled number. Note that ToxicBench's `infer_severity` is asymmetric
   (×0.75 counts as plausible, ×1.25 as subtle); either keep it for comparability and disclose it, or use
   symmetric log-ratio bins.
5. **Parser and sanity rules fixed in advance.** Error/exception observations are out of scope. Scalar
   extraction must handle thousands separators and scientific notation (the current `NUMBER` regex turns
   `1.2e+05` into 5.0). The sanity row (return = 0 and return = 10× clean) must reach > 0.95 before any real
   number is reported.
6. **T0 from the actual preview event**, joined on run and step, with a logged fallback to the CSV.
7. **A re-execution baseline 0d** (see E). Pre-register it now so it cannot be added later as a convenient
   comparison.
8. **Power.** Minimum events per (severity × table-size) cell, and minimum tables, for the within-table CI.
   The plan's 60-table requirement for H1 applies here too.

## C. The three headline findings

### (i) "Observation failures are 60% of failures"
- **Computed correctly** from P1's definitions (682/1134).
- **Over-claimed.** The label includes run-to-run noise (see G1), counts exposure rather than consumption
  (A17), and averages over an unbalanced design: gpt-5.4-mini is 63% of pairs; Haiku's share is 0.23,
  pandasai's 0.92.
- **Strongest alternative explanation:** stochastic agents produce discordant clean/toxic outcomes at about
  p(1−p) regardless of poison. The 0.60 is mostly p/(1+p) ≈ 0.47 plus a real but modest excess.
- **Wording that the evidence supports today:** "Poisoned runs fail 10.6 pp more often than the matched clean
  runs' failure rate would predict (7.1 pp on numerical tasks); the noise-corrected share of failures
  attributable to the observation is TBD."

### (ii) "Silent override is 8% of pairs"
- **Computed correctly** (301/3633).
- **Over-claimed in name.** The class is a residual: toxic succeeded, `recovery` false,
  `poisoned_answer_used` false, at least one poisoned event. The plan's rule (check whether the corrupted
  value appears in the final reasoning or answer) was not implemented, and nothing shows the agent "used the
  correct value without re-calling".
- **Strongest alternative explanation:** the answer did not depend on the poisoned value. 102 of the 301
  overrides are sign_flip, where a magnitude-only or rank-only answer is unaffected by sign. Other causes:
  the poison fired on an intermediate call whose value was not needed, or the value was inside the 10%
  tolerance.
- **Suggestion:** rename it `no_effect_exposed_unexplained` until a trace check (value appears in later
  reasoning vs a correct value appears without a re-call) splits it.

### (iii) "A zero-param rule reaches 0.92 AUROC, covers 25% of poisoned events, zero subtle events in scope"
- **AUROC and 25% computed correctly** (283/1153 = 24.5%). Two numbers in the write-ups are wrong: total
  coverage is 16.2% (A19), and "75% filtered" should be 66% (A20).
- **Zero subtle in scope:** confirmed. `per_severity` has only obvious and plausible keys.
- **Over-claimed in "the rule works where it applies".** On these tables, where the rule applies is decided
  by the poison magnitude relative to a 3-12-row range, so 100% of poisoned means are flagged. The pilot
  cannot separate "the rule is good" from "ToxicBench's poisons are large relative to tiny tables".
- **Also confounded:** coverage is selected by task, not by agent. The poisoner fires on the oracle line, so
  in-scope poisoned events come from tasks with unfiltered oracles. Poisoned coverage (24.5%) is almost twice
  clean coverage (13.8%), and the in-scope base rate (0.349) is higher than overall (0.231).
- **Strongest alternative explanation for the 75% "out of reach":** that limit comes from the regex parser,
  not from rules in general. Running the agent's own code on the visible rows (or on bootstrap resamples of
  them) gives an expected range for any pandas expression, including filters and groupbys, with zero
  parameters. Until 0d is tested, "learned signals are needed for the filtered 75%" is unsupported.

## D. Rigor-reviewer scores

| Dimension | Score | Reason |
|---|---|---|
| D1 Evidence relevance | **2** | G1 does not test its claim (no noise null), and G2's statistic measures the leaked bound that P2 itself ruled "not a finding". |
| D2 Falsifiability (H1-H6 as worded) | **3** | Thresholds are numeric and actionable, but H1's subtle tier is untestable on current data, G1's threshold sits below the null, and H6's 0a arm is close to tautological (0a depends only on the returned value and table, so class differences reflect task and poison mix). |
| D3 Claim scope vs evidence | **2** | "Majority of failures", "silent override" and "75% filtered" all reach past what was computed. To its credit, F2 narrows G2 honestly. |
| D4 Logical flow (problem → gaps → contributions → evidence) | **3** | The plan's arc is coherent, but the pilot quietly redefines C3 ("cover what rules cannot") without a pre-registered amendment, and the plan has two fork thresholds. |
| D5 Exploration integrity | 4 | Negative constraints (tiny tables, no subtle events, T0 ≈ T1) were found and recorded, not hidden. |
| D6 Methodological rigor | 2 | Sanity row skipped, parser bug, single-run pairs with no noise estimate, 9-table within-table metric without CI. |

Mean 2.67 → **Weak Reject as a paper artifact today**, which is normal for a day-1 pilot. Every item above can
be fixed without GPU time except P3 itself.

## E. Workshop fitness

**Does the story survive?** Yes, but the central claim has to move. "Which signal wins" on ToxicBench is
dominated by two artifacts: tiny tables (no context axis) and parser-limited coverage. A reviewer will accept
a coverage-vs-accuracy figure only if (a) coverage is limited by query structure rather than by a regex, and
(b) accuracy is measured where truncation actually hides information. Today neither holds, so that Figure 1
would read as a benchmark artifact.

**Proposed central claim, framed as a hypothesis for P3:** *Detecting a corrupted numeric tool return depends
less on the uncertainty signal than on whether the checker can reconstruct what a normal return looks like.
That ability falls with observation context richness and with query complexity. Agent-intrinsic signals do
not recover what the reconstruction loses.*

**Figure 1 candidate:** a 2-D grid, context richness (T0 ... T4) × query complexity (unfiltered / filtered /
grouped / multi-step), with within-table AUROC per signal and coverage in each cell. 0a, 0d, 1, 3 and 7 are
plotted as lines across the grid. This keeps C1, uses the pilot's real discovery (coverage), and makes the
rule-vs-learned comparison fair. It does not require a pivot.

**Why not PIVOT:** the question (observation-step detection as a function of context) is unaffected by
anything found today. What changed is that the pilot cannot answer it, which P3 was always meant to fix.

### Top 3 changes before `gen_tasks.py`

1. **Re-decide G1 with a noise-corrected test.** Add a dated P1 amendment: split capability into both-fail
   and clean-only-fail, run McNemar on the discordant cells, and estimate clean-vs-clean discordance from the
   831 duplicate keys. Report the excess failure rate with a clustered CI. C2 stays in the paper only if the
   excess is clearly above zero, especially in the numerical family (currently +7.1 pp). This is CPU only,
   about an hour of work.
2. **Fix the rule and add the competing zero-parameter baseline before generating anything.** Patch the
   parser (error strings, scientific notation, separators, variable names other than `df`), run the sanity
   row, join T0 to the actual preview events, and implement **0d = re-execute the agent's code on the
   visible rows** (plus a bootstrap interval). Re-run P2 on the original data as exploratory. If 0d covers
   the filtered queries, C3's role changes; better to learn that before writing the scorer.
3. **Write P3 before `gen_tasks.py` exists.** Include: one fork threshold (amend the 0.90/0.95 conflict in the
   plan), the decision statistic from section B (within-table, plausible+subtle, lower CI bound, coverage
   condition, system-level AUROC), a task mix that keeps the original 66% filter/groupby share, mirrored
   continuous severities logged as displacement in visible-std units, table size ≥ 50 rows (≥ 200 reported
   separately), and minimum events per cell. Then commit, then generate.

Smaller fixes: correct A19 and A20 in `research-log.md` and `findings.md`; set G2 to `undecidable`; record exact
command lines (uncomment `run_day1.sh`); change the gate items marked [x] for sanity (step 3) to [ ] until the
parser is fixed.

## Strongest counter-argument a hostile reviewer would write

"The paper's headline results come from a benchmark whose tables are 3-12 rows and whose poisons are large
relative to those tables. A regex range check flags every poisoned mean, and the 'observation failure'
taxonomy is indistinguishable from run-to-run noise without a replicate baseline. The signals are not being
compared; the benchmark's construction is being measured."

## Stress test

| Test | Result |
|---|---|
| Remove the strongest evidence (obvious-severity events), does G2 hold? | No: plausible-only 0.862 |
| Apply the plan's other threshold (0.95), does the fork hold? | No |
| Replace the 0.15 threshold with the no-effect null, does G1 hold? | Only marginally: +10.6 pp overall, +7.1 pp numerical, CI not yet computed |
| Apply to large tables, does the 0.92 transfer? | Untested: 0 events on large tables |
| "So what?" | Survives if reframed around context richness × query complexity |

## Overall assessment

**Strongest part:** the honesty of the narrowing. P2 pre-stated the tiny-table limitation, `findings.md` F2
refuses the broad "rules suffice" reading, and the within-table metric was computed. That makes this review
possible.

**Single most important fix:** do not let either gate stand as decided. G1 needs a noise null and G2 needs data
where truncation hides something. Both fixes have to be pre-registered (P1 amendment, P3) before
`gen_tasks.py` runs, or the next pilot will repeat this one's problem: thresholds that pass because of how the
benchmark was built.

## Sources
- `program.md`, `PREREGISTRATION.md`, `findings.md`, `research-log.md`, `research-state.yaml`, `results.tsv`, `.gitignore`, `.git/logs/HEAD`: accessed 2026-10-31
- `experiments/common.py`, `taxonomy.py`, `range_check.py`, `run_day1.sh`: accessed 2026-10-31
- `experiments/results/{inventory.json, taxonomy/summary.json, taxonomy/pairs.jsonl, range_check/summary.json, range_check/events.jsonl, *.log}`: accessed 2026-10-31
- `data/toxicbench/toxictool_bench/results/20260707-181347_smolagents_toolcalling_Qwen3.6-35B-A3B-no-thinking_both.jsonl` (Errno-2 parse artefact): accessed 2026-10-31
- private planning notes (not included in this repository)
- `/tmp/AI-research-SKILLs/22-agent-native-research-artifact/rigor-reviewer/SKILL.md`, `/tmp/academic-research-skills/deep-research/agents/devils_advocate_agent.md`: accessed 2026-10-31
