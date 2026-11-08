# Research log (append-only; one STEP GATE per step, format in program.md)

## 2026-10-31 — init
Scaffolded repo; cloned ToxicBench; inventory run (see findings F0).
Protocol P1 (taxonomy) and P2 (range check) written before their scripts exist.

## 2026-10-31 — step 2 taxonomy.py (P1)
Note: PREREGISTRATION.md landed in the init commit 571f732 (git add -A), so the "protocol" commit
43247bb is empty; the protocol text still precedes any result commit, which is the property that matters.
```
Step: taxonomy (P1, gate G1)
1 Protocol-before-results  571f732/43247bb precede this results commit                  [x]
2 Hypothesis served        G1 pilot gate; H6 power check; paper Table 2 (failure classes) [x]
3 Sanity check             class counts sum to pairs (3633); unexposed=52 (poison never fired) is plausible;
                           831 keys had duplicate runs -> first used, logged                 [x]
4 Confirmatory/exploratory G1 confirmatory (PASS: 0.60 overall, 0.49 numerical). Strata exploratory. [x]
5 Claim scope              C2 stands. H6 pre-labelled EXPLORATORY: only 25 observation-failure pairs
                           at subtle/numerical (< 50). Plan already carries this rule.          [x]
6 Reviewer objection       "Your 'observation failure' label depends on ToxicBench's frozen scorer;
                           a 1.1x poison inside a 10% tolerance is graded correct." True: 1 of 4 subtle
                           aggregate_scale tasks has |scale-1| <= tolerance. Add to limitations;
                           report tolerance-adjusted labels as a robustness check in P3.           [x]
7 Workshop fitness         Yes: Table 2 + the silent-override count (301 pairs, 8%) is a concrete
                           reusable observation for Section 5.                                   [x]
Verdict: PASS
```

## 2026-10-31 — step 3 range_check.py (P2)
```
Step: range check (P2, gate G2)
1 Protocol-before-results  same as above                                                   [x]
2 Hypothesis served        G2 pilot gate; H2 signals 0a/0b; paper Figure 1 (context axis)    [x]
3 Sanity check             T0 (full min/max) AUROC 0.93/0.97 as expected for a leaked bound; unit_conversion
                           = 1.0 (1000x); within-table AUROC (0.95, 9 tables) ~= pooled, so not a
                           difficulty-oracle artifact (2610.05572). Coverage is the problem: in-scope
                           811/4993 python_exec events (16.2%); poisoned coverage 283/1153 = 24.5%; 66% of poisoned
                           events skipped for filters/groupby.                                [x]
4 Confirmatory/exploratory G2 confirmatory on the covered subset: 0a@T1 aggregate_scale = 0.923 > 0.90
                           -> fork PROVISIONALLY activated per P2. Everything else exploratory.      [x]
5 Claim scope              Two narrowings: (a) T0 ~= T1 (0.929 vs 0.928) confirms head-5 is not a
                           truncation on 4-12-row tables, so no context-axis claim from this data (as
                           pre-stated). (b) ZERO in-scope subtle events: only 32 subtle aggregate_scale
                           events exist in all of ToxicBench, from 4 tasks, all filtered queries. H1's
                           subtle-tier test is impossible on the original data. Plan amended.        [x]
6 Reviewer objection       "0.92 AUROC from a rule means the learned signals are pointless." Response:
                           the rule covers 25% of poisoned events (unfiltered single aggregations); the
                           other 75% need something that reads the code/context. This reframes C3's job:
                           not beat the rule where it applies, but cover what it cannot.             [x]
7 Workshop fitness         Yes: coverage-vs-accuracy of the rule is itself a figure, and it sharpens
                           the paper's question.                                                    [x]
Verdict: PASS-AS-EXPLORATORY for the context axis; PASS for G2 on the covered subset
```

## 2026-10-31 — independent review of the pilot (docs/REVIEW_2026-10-31_pilot.md)
Verdict GO-WITH-CHANGES. Accepted and applied as PREREGISTRATION amendments A-P1/A-P2 (commit bfcc88e),
then both scripts rewritten and re-run. Key corrections: G1 tested the wrong null; G2 undecidable on
tables <= 12 rows; error strings parsed as scalars; sanity row never run; 0d re-execution baseline missing;
coverage numbers mis-stated (16.2% / 24.5% / 66%).

## 2026-10-31 — step 2' taxonomy.py (A-P1)
```
Step: taxonomy with noise null (A-P1, gate G1 amended)
1 Protocol-before-results  bfcc88e precedes this commit                                   [x]
2 Hypothesis served        G1; H6 power; Table 2                                            [x]
3 Sanity check             clean-vs-clean discordance measured directly on 737 duplicate keys (4.3%),
                           toxic-vs-toxic 11.0%; same-source pairs 3631/3633; class counts sum to 3633 [x]
4 Confirmatory/exploratory G1 confirmatory: excess toxic-failure rate 18.7pp [15.1, 22.3] overall,
                           22.4pp [16.8, 28.0] numerical; McNemar b=734 c=81 p<1e-100. PASS.      [x]
5 Claim scope              "60% of failures" -> "noise-corrected 55% (43% numerical)"; the reviewer's
                           homogeneous-p bound (0.47 null) was pessimistic: measured floor is 0.043. [x]
6 Reviewer objection       "exposure != consumption": observation class still does not require the
                           poisoned value to be used. Trace check deferred to P3 (needs final-answer parse).
                           Class renamed no_effect_exposed_unexplained (301).                       [x]
7 Workshop fitness         Table 2 now has a defensible paired test.                              [x]
Verdict: PASS
```

## 2026-10-31 — step 3' range_check.py (A-P2)
```
Step: range check + 0d re-execution (A-P2)
1 Protocol-before-results  bfcc88e precedes this commit                                   [x]
2 Hypothesis served        H2 (0a/0b/0d columns); Figure 1 (coverage x accuracy); G2 status      [x]
3 Sanity check             sanity rows y:=0 -> 0.97-1.00, y:=10y -> 1.00 (> 0.95 PASS); preview T0 check:
                           769 match / 0 mismatch / 21 no-preview, so CSV-derived T0 == what agents saw;
                           482 clean ERROR observations now excluded (were scored as 2.0 before)      [x]
4 Confirmatory/exploratory All exploratory on original tables (G2 undecidable: max table 12 rows).      [x]
5 Claim scope              Fixing the parser raised 0b to 1.000 pooled and 0a to 0.954 (0.896 on
                           plausible+subtle). 0d (re-execute agent code on visible rows) covers 575/1153
                           poisoned events (50%) vs the rule's 283 (24.5%), at AUROC 0.83 pooled, 0.72 on
                           plausible+subtle, 0.57 at subtle (n small). The remaining 50% of poisoned events
                           print multiple numbers (dataframes) and no zero-parameter scalar method applies. [x]
6 Reviewer objection       "0d bootstrap on 3-12 visible rows is a toy interval". Agreed; its real test is
                           P3 on >= 50-row tables where head-5 is a genuine truncation.                 [x]
7 Workshop fitness         Yes: coverage x accuracy now has three honest points (rule 24.5%/0.95,
                           re-exec 50%/0.83, nothing 100%/-). This is the shape of Figure 1.            [x]
Verdict: PASS-AS-EXPLORATORY
```

## 2026-10-31 — step 4a gen_tasks.py (P3) + A-P1 consumption split
```
Step: large-table tasks + rule ceiling (P3)
1 Protocol-before-results  4cfcecf (P3) precedes this commit                              [x]
2 Hypothesis served        G2 re-decision ceiling; H1/H2 testability; Figure 1 context axis   [x]
3 Sanity check             180/180 tasks; 5 dropped for oracle mismatch/zero (logged); template mix
                           60/90/30 = 33/50/17% as pre-committed; severity 60/90/30; pandas vs stdlib
                           oracle cross-check passed for all kept tasks; 6 tables sha256 recorded;
                           sample tasks read correctly (clean/poison/scale/displacement)           [x]
4 Confirmatory/exploratory Exploratory, descriptive of the benchmark we built (as pre-registered).  [x]
5 Claim scope              The ToxicBench 0a result INVERTS on large tables: ceiling AUROC 0.57 at full
                           preview (hit rate 14%), 0.55 at head-5 (clean false-positive 61%), 0.55 at
                           head-2. 0b: 0.71 / 0.57 / 0.56. "Rules suffice" cannot fire on large tables
                           regardless of agent: an agent-run 0a <= ceiling 0.57 << 0.90. The 0.95 on
                           ToxicBench was a tiny-table artefact. Plan amended.                      [x]
6 Reviewer objection       "Your head-5 bootstrap for 0d resamples to n and will be overconfident at
                           truncated tiers." Agreed in advance: P4 amendment will set the resample size
                           to the visible count for location statistics. Also: all six tables are
                           memorizable public data (disclosed in P3).                                [x]
7 Workshop fitness         Yes. This is Figure 1's left panel: zero-param ceiling vs context tier on
                           tables where truncation hides information. It makes the learned/intrinsic
                           comparison necessary rather than decorative.                           [x]
Verdict: PASS (exploratory by design)
```
A-P1 addition run: observation_consumed 609 / exposed_only 73 (numerical 316 / 59). Excess rate unchanged.

## 2026-10-31 — re-score review (docs/REVIEW_2026-10-31_rescore.md): 2.67 -> 3.5
Accepted. Applied as A-P3 (commit 85270e2) before gen_tasks v2 / range_check / taxonomy re-runs.

## 2026-10-31 — step 4a' gen_tasks.py v2 + ceilings 0a/0b/0d (A-P3)
```
Step: P3 v2 + ceilings (A-P3)
1 Protocol-before-results  85270e2 precedes this commit                                   [x]
2 Hypothesis served        H2 (which zero-param check works at which context tier); G2 bound; Fig 1 [x]
3 Sanity check             210 tasks, 4 dropped (logged with spec); grouped = 60 (power rule met);
                           scales 3-6 per value within unfiltered (balanced); 0d computable 100% at T0;
                           like-for-like control reproduces ToxicBench hit rate 1.00 in its own bin (n=43) [x]
4 Confirmatory/exploratory Exploratory (descriptive of the benchmark we built), as P3/A-P3 say.          [x]
5 Claim scope              F3 narrowed to F3' (range-width mechanism, hit-rate bound 0.84). NEW F4: 0d
                           0.935 at T0 vs ~0.55 at head-5/head-2 and 0.59 at random-5. The claim "zero-param
                           rules fail on large tables" is WRONG as stated: re-execution with the full table
                           is near-perfect; what fails is every zero-param method once only 5 rows are
                           visible. Plan's central claim and C3 bar updated accordingly.                 [x]
6 Reviewer objection       "0d at T0 has the whole table, which is the oracle; of course it works." Yes:
                           T0 is the upper end of the context axis and 0d there is the honest ceiling. The
                           paper's question lives at T1/T3, and P4 enforces those tiers in the harness.   [x]
7 Workshop fitness         Figure 1 now has its x-axis (context) and its y-range (0.93 -> 0.55) from zero-
                           param methods alone; P4 fills in intrinsic and learned lines.                [x]
Verdict: PASS (exploratory)
```

## 2026-10-31 — step 3'' range_check.py (A-P3 sanity + NaN accounting) and taxonomy noise floor by model
Sanity rows: 0a/0b/0d all > 0.95 at T0 and T1. 0d at T2 (2 rows) FAILS (0.84 / 0.90): the 2-row bootstrap
interval is degenerate, so 0d_T2 on original tables is not reported as a real number. 0d NaN drops: 93 of
575 poisoned in-scope events; scored coverage 482/1,153 = 41.8%. Noise floor by model: gpt-5.4-mini 6.5%
(n=449 keys), claude-sonnet 1.1% (277), Qwen3.6 0.0% (11), haiku none; pair-reweighted 4.8% vs pooled 4.3%.
G1 unchanged.

## 2026-10-31 — round-3 review (docs/REVIEW_2026-10-31_round3.md): 3.33; actions 1-2 applied as A-P3b/A-P4
```
Step: k-sweep + shared zero-param implementation (A-P3b)
1 Protocol-before-results  e71e8e3 precedes this commit                                      [x]
2 Hypothesis served        H2 (context axis), C3 bar, Figure 1 x-axis                          [x]
3 Sanity check             sanity rows redefined (0 / 10x clean were legitimate values for 66 tasks);
                           0a/0b/0d pass at every k; filtered-count bug found and fixed (count is not n);
                           degenerate-interval normalization floor added; 20 draws x 6 tables CIs +/-0.015 [x]
4 Confirmatory/exploratory Exploratory (oracle values), as pre-registered.                          [x]
5 Claim scope              F4 rescoped to F4': monotone 0.62 -> 0.83 -> 0.94; 0d ~ 0r at k <= 20 so the
                           small-k limit is information, not estimator; T0_agent 0.53; mechanism claims
                           limited to the headroom identity.                                        [x]
6 Reviewer objection       "0r is withheld, so the design-vs-data test leans on a withheld signal." True;
                           0r's s_lo failure comes from filtered sums (reference assumes unfiltered stats);
                           its s_hi passes and agreement with 0d is reported with that caveat.          [x]
7 Workshop fitness         Figure 1 now has a continuous x-axis from CPU alone.                     [x]
Verdict: PASS (exploratory)
```

## 2026-10-31 — round-4 review (docs/REVIEW_2026-10-31_round4.md): 3.5; CPU-only ceiling not reached; actions 1-2 applied as A-P3c
```
Step: 0o oracle reference + common-support paired decision (A-P3c)
1 Protocol-before-results  1605390 precedes this commit                                      [x]
2 Hypothesis served        settles F4 design-vs-data; sets the C3 bar per k; Figure 1 reference lines  [x]
3 Sanity check             T0_agent recombined passes (0.97); B=500 and floor sensitivities ~0 effect;
                           common-support fraction and 164 always-computable tasks reported; table-level
                           and (table,draw) CIs agree                                                   [x]
4 Confirmatory/exploratory Exploratory (oracle values) but decided by a pre-registered CI rule.           [x]
5 Claim scope              F4' WITHDRAWN: 0o exceeds 0d by 0.13-0.18 at every k, CIs above 0.05 -> the
                           small-k limit was 0d's estimator. Information ceiling at 5 rows ~0.79.
                           Plan central-claim evidence and C3 line rewritten; F3' superseded (n=2 pairs). [x]
6 Reviewer objection       "0o is an oracle no real checker has." Correct: it is an upper bound by design
                           and is labelled as such; the paper's question is where learned/intrinsic signals
                           fall between 0d and 0o.                                                       [x]
7 Workshop fitness         Figure 1 now has two reference lines bracketing the space P4 signals must land in. [x]
Verdict: PASS (exploratory; decision rule applied as registered)
```

## 2026-10-31 — retroactive log entries (round-5 review, section f)
- 02:00 UTC `ksweep2_smoke.log` (3 draws, B=20, M=60): 166 always-computable tasks, k5 0o-0d gap 0.118,
  T0_agent sanity returned None/None.
- 02:01 UTC post-smoke fix to `ksweep2.py`: the clean slice was taken before the combined T0_agent column
  existed, so the sanity rows had no scores; re-sliced after the column is built. Bug fix only; did not touch
  the 0o/0d decision path. Made after seeing smoke output, after the A-P3c protocol commit, and should have
  been logged here at the time.
- 03:18 UTC `range_check.py` re-run on the shared 0d (F2''): logged in findings but not here. Head-5 0.81 was
  quoted in F2'' although withheld (sanity 0.94); the quote is removed in F2'''.
- research-log row 5 of the A-P3c gate said "F3' superseded (n=2 pairs)" but findings.md carried no marker
  until now; marker added with the F4 and F4'' markers in this round.

## 2026-10-31 — round-5 review (docs/REVIEW_2026-10-31_round5.md): 3.17; GO-WITH-CHANGES; CPU-only ceiling not reached
Substance: the A-P3c 0o oracle is computed from the full table once per (task, k) and never conditions on the
visible draw; on unfiltered mean/median it separates clean/poisoned perfectly where a five-row t-test gets
0.70, so the 0o-0d gap measures knowledge of the answer, not 0d's estimator. The A-P3c decision ran as
registered but the reference could not distinguish the two readings. "0.17 recoverable" and "C3 bar = 0o
curve" withdrawn (A-P3d). Also: is_sum_type misclassifies the P3 grouped template; 0a sum bound n*[min,max]
fires on clean filtered/grouped sums; FastTemplate/template_stat disagree on three edge rules; F3'/F4 not
marked superseded; C3 bar defined twice; central claim and F4'' contradicted each other.
Actions: A-P3d protocol commit 5e978bb; fixes + tests (test_zeroparam.py: 20/20 sum-type cases, 63,000
subset evaluations with 0 FastTemplate/template_stat mismatches); ksweep2.py and range_check.py re-run.

## 2026-10-31 — A-P3d executed: 0o* draw-conditioned oracle, decomposition, rule fixes, re-runs
```
Step: 0o* reference + estimator/oracle-knowledge decomposition + is_sum_type/0a-sum/FastTemplate fixes (A-P3d)
1 Protocol-before-results  5e978bb (A-P3d, incl. prediction 0o*-0d in [0.03, 0.10] at k=5) precedes this commit [x]
2 Hypothesis served        H2 reference lines; C3 bar (single definition); central-claim evidence       [x]
3 Sanity check             sanity rows for 0a/0d/0o/0o*/0r_log at every k all >= 0.95 (nothing withheld in
                           F4'''); T0_agent 0d head-5 0.945 withheld; range_check head-5 0d now 0.95 pass;
                           test_zeroparam.py 20/20 sum-type cases, 63,000 subset evaluations 0 mismatches;
                           B/floor sensitivities ~0; table-level and (table,draw) CIs agree               [x]
4 Confirmatory/exploratory Exploratory (oracle values), decided by the pre-registered CI rule.             [x]
5 Claim scope              F4'' WITHDRAWN (0o never sees the draw). F4''': achievable ceiling 0.73@k5, 0d 0.62,
                           estimator loss 0.11 [0.10,0.13], oracle knowledge 0.06 [0.05,0.08]; on unfiltered
                           mean/median 0r_log ~ 0o* so the analytic route recovers the loss there. Observed
                           0.11 is just above the committed prediction range (0.03-0.10): reported as such.
                           Central claim reconciled (information bound + estimator within it). C3 bar single.
                           F3'/F4/F4''/F2'' marked superseded in findings headers.                           [x]
6 Reviewer objection       "0o* is still an oracle (knows the exact sampling law)." Yes; it is the bound for a
                           checker with a perfect prior on the column, which is what a scorer trained on clean
                           returns could approach, not exceed. Also: 0r_log exceeds 0o* at k >= 100 because it
                           uses the draw's spread (different information set); stated in F4'''.           [x]
7 Workshop fitness         Figure 1 reference lines are now both achievable (0d, 0o*) with 0o dashed; the P4
                           landing zone for signal 7 is 0.62-0.73 at five rows.                            [x]
Verdict: PASS (exploratory; decision rule applied as registered; prediction miss disclosed)
```

## 2026-10-31 — round-6 review (docs/REVIEW_2026-10-31_round6.md): 3.67; GO-WITH-CHANGES; CPU-only ceiling REACHED
D1 4, D2 3, D3 4, D4 4, D5 4, D6 3. Reviewer audited a one-off recomputation script (not included; all F4'''
numbers reproduce; 0o* varies by draw, 0o constant) rather than ranking itself; the earlier round-6 attempt
timed out reading events.jsonl row by row. Items done this round: A-P4 "no op classifier" marked superseded
(A-P3d note); F2' superseded marker; is_sum_type tightened for nunique/len(unique)/mean().sum() with 25/25
tests and 0 ToxicBench events affected; F4''' prediction-miss sentence. Everything remaining needs P4 agent
runs. Note for the loop: reviewers that must recompute get the default agent (has a shell), with
precomputed numbers supplied, not the devils-advocate profile.

## 2026-11-01 — P4 week 1 executed (Qwen3-4B on one A10G GPU)
```
Step: P4 tiers T0_agent / T1 / T1r2 / T3 for Qwen3-4B (2,520 trajectories); zero-param + intrinsic signals on real events
1 Protocol-before-results  P4 (7a5ce00), A-P4 (e71e8e3), A-P3d C3 bar (5e978bb), A-P4 smoke note precede 136386b+ [x]
2 Hypothesis served        C2 on P3 pairs (observation failures 195-198/210 at every tier); G2 at T1 (closed: max
                           zero-param 0.58 << 0.90); H1 (verbalized 0.55 upper-CI 0.61; entropy <= 0.50)        [x]
3 Sanity check             smoke 18/20 after sandbox normalizations (logged per event); noise floor 2.9-4.3%;
                           poison fired 199-202/210 and matched oracle; parse errors 0-1 per 630 runs          [x]
4 Confirmatory/exploratory C2/G2/H1 confirmatory per P4; mean-entropy variants exploratory; first-token entropy
                           DEGENERATE (fixed first token) -> amendment required before the next agent run       [x]
5 Claim scope              F5/F6 marked preliminary (one agent). H1(verbalized) NOT claimed passed (0.61 > 0.60).
                           T0_agent = T1 = T3 behaviourally: context richness does not change what THIS agent
                           does; it changes what a checker can do (0a 0.54 -> 0.57 with min/max).               [x]
6 Reviewer objection       "Harness normalizations changed the task." They resolve FileNotFound/indent errors that
                           upstream counts as harness-limit failures; applied to every agent; recorded per event;
                           poisoning path verified unchanged.                                                     [x]
7 Workshop fitness         Figure 1 now has real agent points at three tiers plus four signal columns.           [x]
Verdict: PASS (preliminary; Qwen3-8B and gpt-5.4-mini needed for per-agent H1/C2 decisions)
Cost: instance ran 07:00 -> ~19:30 UTC (~12.5 h, ~9 h idle after T1 finished at 08:58) ~ $15; stopped at
19:28 UTC.
```

## 2026-11-02 — P5 executed: C3 scorer K=5 LOTO (30 members, A10G, ~4.5 h)
```
Step: C3 scorer train + eval on 6 P4 eval sets (P5)
1 Protocol-before-results  P5 (12595dc) incl. committed prediction [0.55, 0.70] precedes this commit     [x]
2 Hypothesis served        C3 bar (A-P3d): beat max(0d, 0r_log) on slice (b); fraction of 0o*-0d closed [x]
3 Sanity check             FAILED by the hard rule: s_hi 0.81-0.85, s_lo 0.62-0.66 (< 0.95); clean coverage
                           0.15-0.18 (< 0.80). Surprise column WITHHELD as headline; reported as negative.  [x]
4 Confirmatory/exploratory Confirmatory (pre-registered); prediction missed (observed 0.50-0.52).        [x]
5 Claim scope              C3 = negative result for the P5 specification. No claim that learned scorers in
                           general fail; P5b candidates listed in F8, none run.                            [x]
6 Reviewer objection       "Underpowered / under-trained scorer, not a fair test." Partly fair: 1.8k examples,
                           0.5B, 3 epochs. Counter: training loss converged and magnitude is learned (corr up to
                           0.94); the gap is resolution (x6 error vs x1.1-2 poison), which more epochs do not fix.
                           Stated as the limitation it is.                                                   [x]
7 Workshop fitness         Figure 1 now has the learned-signal column at chance alongside the others.        [x]
Verdict: PASS (negative result, pre-registered, honestly reported)
Cost: GPU instance 20:03 -> 06:25 UTC (~10.4 h incl. 8B T0_agent + idle gaps) ~ $12.6; stopped 06:25.
```


## 2026-11-07 — scoring fixes from the d0e7ba4 code review (no new runs; re-scored all six eval sets)
Review (collaborator, 2026-11-06) found: zeroparam scored on tier cap not actual preview exposure; intrinsic
misaligned shadow calls when an ERROR step preceded the scored event; constant-score tables dropped instead of 0.5;
sandbox read_csv fell back to the real filesystem. All reproduced (4B: ~30% of scored events had seen 0 rows;
lt_penguins_v3_unf_009 alignment confirmed) and fixed:
  experiments/p4_common.py          shared: exposure_before, completion_after, auc_or_none, within_table, paired_tasks
  experiments/p4_score_zeroparam.py --exposure actual|protocol; k and min/max per event; paired column; same-task severity controls
  experiments/p4_score_intrinsic.py positional alignment incl. ERROR events; scalar check; paired column
  experiments/p4_run.py             read_csv of an undeclared file -> FileNotFoundError (no filesystem fallback)
  experiments/test_p4_common.py     unit tests for the four fixed behaviours (ALL PASS); test_zeroparam.py still ALL PASS
Before/after table and text consequences: findings.md "F5/F6/F7 correction (2026-11-07)". Raw outputs in
data/ours/p4/_recheck/{before,after}_{zeroparam,intrinsic}.txt. H1 verdicts unchanged; 4B head-5 0o* on
actually-seen rows is 0.61-0.62 (was reported 0.58) with coverage 0.48 — "no head-5 reference above 0.58" must be
reworded. Preview-seen vs not compliance: 98-99% vs 95%.
Still open from the review (not done here): worker-process isolation for model code (SAFE_BUILTINS audit), the
anomaly_detection flag definition in the paper, both compliance denominators in Table 1, Gemini protocol (collaborator).

## 2026-11-07 — Gemini Flash T1 external replication

```
Step: A-P4-Gemini, 630 trajectories and paired scalar confidence summary
1 Protocol-before-results  4fa7740 precedes all Gemini generation. Collection code f01f8bf. [x]
2 Hypothesis served        H5 external replication; 7/73 subtle tasks paired, upper CI 0.667. [x]
3 Sanity check             20/20 clean smoke success; paired pilot poison delivered.
                           Four Flash regression tests pass. 630 rows, no missing/duplicate
                           task-replicates; all upstream metrics and event steps rechecked.
                           Six table checksums match provenance. Dedicated confidence
                           sanity corruption control uncollected; H5 diagnostic only. [x]
4 Confirmatory/exploratory Registered H5 statistic not confirmed. Coverage and behavioral
                           diagnostics qualify scope. No signal-quality headline. [x]
5 Claim scope              72/128 exposed runs adopt poison, 50 recover. 35 exposures scalar.
                           Strong closed model does further tool work under poison_once.
                           No universal blind-compliance or intentional-detection claim. [x]
6 Reviewer objection       Different return formatting, sampling and tool-error retries.
                           Per-format counts, raw traces and runtime versions reported. [x]
7 Workshop fitness         Adds a closed-family boundary to F5-F8. Results recorded as F9. [x]
Verdict: PASS for collection; H5 not confirmed and limited by scalar coverage.
Recorded formal usage: 1,260,597 input / 125,680 output tokens.
Estimated formal API usage cost: $1.42; pilot approximately $0.04.
```


## 2026-11-07 — fixed-return context feasibility pilot

```
Step: A-CTX-PILOT, 12 queries x 3 contexts x 2 returns
1 Protocol-before-results  bfaf713; request freeze 5da0d36 and clarification 41473be precede calls. [x]
2 Hypothesis served        Query-relevant-evidence feasibility gate; does not amend H5. [x]
3 Sanity check             Four new treatment/parser/resume/failure tests; four existing
                           Gemini adapter tests. Frozen packets and hashes validated.
                           Live extreme-corruption sanity absent; AUROC withheld. [x]
4 Confirmatory/exploratory Exploratory selected-query pilot, one completion per cell. [x]
5 Claim scope              Main contrast crosses zero and is format-sensitive. No stable
                           semantic-checking benefit or free-agent recovery claim. [x]
6 Reviewer objection       Six table clusters; fixed samples; standard-data priors;
                           confidence semantics; invalids. Independent reviewer checked
                           protocol and all replies; limitations and sensitivity added. [x]
7 Workshop fitness         Tests a candidate intervention and exposes measurement issues;
                           Qwen same-manifest reproduction left to owner. [x]
Verdict: PASS-AS-EXPLORATORY; feasibility only, no detector efficacy headline.
```

Completed 72 cells, 67 schema-valid; primary effect +8.3pp [-16.7, +33.3]pp. Usage fields: prompt_tokens=101889, completion_tokens=5878, total_tokens=128020; fields do not sum, no price estimate. Internal transport retry count unknown; no final transport failures recorded. See F10 and docs/CONTEXT_PILOT_2026-11-07_gemini.md.


## 2026-11-07 — Qwen context replication verification and research reflection

```
Step: Verify A-CTX-PILOT paired-model matrix at feeda57
1 Protocol-before-results  Recompute only: existing A-CTX-PILOT protocol, no new collection. [x]
2 Hypothesis served        Query-relevant-evidence feasibility; primary not reproduced. [x]
3 Sanity check             Unique 72-cell IDs, manifest/config/source hashes, answer grading,
                           counts, all contrasts and valid-pair sensitivity match.
                           Gemini raw re-parsed; Qwen raw not archived locally. [x]
4 Confirmatory/exploratory Existing exploratory pilot; verification does not upgrade evidence. [x]
5 Claim scope              Primary +8.3pp versus 0.0pp is not a direction reversal or proof
                           of no effect. Qwen confidence semantic violation unsupported. [x]
6 Reviewer objection       Independent reviewer confirms two overstatements and raw gap;
                           append-only findings clarification, current state corrected. [x]
7 Workshop fitness         Distinguish evidence sufficiency from model evidence extraction
                           before more API collection. No acceptance probability asserted. [x]
Verdict: PASS-AS-EXPLORATORY at scored layer; Qwen raw-response audit pending archive.
```

research(reflect): prioritize a separately preregistered offline same-sample statistical
baseline with sanity, clean false alarms and missing-score coverage. If it extracts useful
signal, test raw rows versus same-row statistical summaries on fresh generated/transformed
tables; otherwise investigate sampling/budget first. This is a proposed plan, not a newly
registered or executed experiment. No new API calls. Methods citation for Scientific Agent
Skills is in docs/REVIEW_2026-11-07_qwen_context_next.md.


## 2026-11-07 — same-evidence statistical feasibility, F11

```
Step: A-CTX-EVIDENCE, exact displayed rows only
1 Protocol-before-results  f94ffbb precedes code a5b6e07 and all baseline measurements. [x]
2 Hypothesis served        Evidence adequacy versus extraction/use feasibility. [x]
3 Sanity check             Nine synthetic tests; shared helper's three groups ALL PASS.
                           Primary sanity 1.000, 12 queries/6 tables.
                           Four failing method/context cells and all cross-context
                           comparisons withheld, including inherited severity gates. [x]
4 Confirmatory/exploratory Reused selected pilot; prospectively locked new analysis,
                           not a fresh confirmatory task sample. [x]
5 Claim scope              Accessible signal in this matched20 sample; no identified
                           internal mechanism, universal bound, new method or 95% guarantee. [x]
6 Reviewer objection       Independent reader recomputed all 288 score formulas and
                           paired-ranking AUROCs from stored artifacts. Query structure,
                           computation/cost differ from model audit; disclosed. [x]
7 Workshop fitness         Adds same-evidence statistical counterpoint to F10, motivating
                           fresh-table raw-versus-derived-summary controls. [x]
Verdict: PASS-AS-EXPLORATORY.
```

Primary within-table AUROC=0.916667, descriptive CI=[0.8333333333333334, 1.0];
clean false flags=1/12, corruption flags=10/12.
No API calls, no outcome-driven sample expansion. Shared zeroparam.py unchanged.
CPU-only run, B=2000 per each of 36 query/context pairs. Events, feature cache, source/input
hashes, environment versions and timestamps archived. Generated report and PNG/PDF diagnostic:
docs/CONTEXT_EVIDENCE_2026-11-07.md. Methods skill citation included there.

research(reflect): the fixed matched20 sample supports further evidence-extraction work.
First check independent row-draw robustness and fresh generated/transformed tables; then
compare raw rows against statistics from the identical rows, retaining 0d and clean/sanity
controls. No next-stage collection started, no data replaced. Existing workshop CFP was
checked: negative results and four-page short papers welcome, but this single-return study
must not be framed as an evaluated long-horizon evolution system.


## 2026-11-07 — independent matched-row draws, F12

```
Step: A-CTX-RESAMPLE, 12 original queries x 20 independent matched20 draws
1 Protocol-before-results  7f6400e precedes code 0494e7f, evidence freeze b192a58 and checks. [x]
2 Hypothesis served        Row-sampling stability, not new-task/model confirmation. [x]
3 Sanity check             Two provider/cluster tests; original checker unchanged.
                           Primary sanity 0.995938; 1920 unique events,
                           240 features. No missing matched scores. [x]
4 Confirmatory/exploratory Known queries/initial outcomes; separate exploratory study,
                           original pilot retained, not expanded for significance. [x]
5 Claim scope              Query/draw mixture estimand, six parent-table clusters.
                           No comparison to models on these new rows, no 5% guarantee. [x]
6 Reviewer objection       Independent cached-formula and pairwise-AUROC recompute
                           agrees. Severity tied to query, zero-error CI degeneracy,
                           single-draw versus mixture distinction disclosed. [x]
7 Workshop fitness         Adds stability/error-trade-off evidence; motivates new-table
                           raw-versus-derived-statistics intervention. [x]
Verdict: PASS-AS-EXPLORATORY.
```

Primary within-table mixture AUROC=0.818437, descriptive CI=[0.7183333333333334, 0.9153125000000001].
Flags 161/240 corruptions and 14/240 clean values.
No new API calls; 240 draws are not 240 independent queries. All model comparisons remain
restricted to their original frozen evidence. Generated report/per-query frequencies:
docs/CONTEXT_EVIDENCE_RESAMPLING_2026-11-07.md.

research(reflect): signal exists beyond the single initial sample, but weak subtle-query
performance and heterogeneous false flags remain. New table and query generation is now
more useful than more draws of this fixed set. Next proposed protocol compares raw rows
against same-row summaries, crosses severity within each query, retains direct statistics,
clean and sanity, and controls added prompt/compute information. No new-table model run
started in these two offline steps. Workshop short-paper relevance is plausible; acceptance
and new-algorithm novelty are not inferred from pilot statistics.


## Step: author revision / cached-output audit — 2026-11-07

1. Protocol-before-results: A-REVISION-CACHED commit 27ab078 precedes this result commit.
   Reused, previously inspected outputs are retrospective diagnostics, not confirmatory.
2. Hypotheses served: H1 version reconciliation and P5 eligibility/common support;
   bounded F11/F12 paper narrative. No model calls or training runs.
3. Sanity/verification: 17 unit tests pass (6 cached-metric + 9 context evidence +
   2 resampling); p4_common exposure/alignment/AUROC groups ALL PASS; zeroparam
   regression ALL PASS including 25 sum cases and 63,000 alignment evaluations,
   zero mismatches. Standalone scorer --cached sanity equals audit. All 17 input
   hashes verified; original input files and five-seat review unchanged; append-only
   historical prefixes preserved. Syntax and git diff --check pass.
4. Interpretation: intrinsic efficacy withheld for absent live sanity; H1 global
   confirmation withdrawn for conflicting rules. All six cached scorer configurations
   fail sanity and coverage. P5 support enumerated, real-corruption gain withheld.
5. Claim scope: 0o/0o* are finite Monte Carlo privileged reference scores, not proven
   optimality bounds. Legacy score keys retained for compatibility but their current
   labels are descriptive. No general learned-UQ failure or internal-mechanism claim.
   Current conclusions/README/state and nearest-work positioning reconciled.
6. Reviewer objection: Qwen raw pilot replies missing and public-table/12-query
   selection restrict audit/generalization. Response: auxiliary scored-record result
   only; no regenerated originals, no broad mechanism or deployment claim.
   program.md milestone read-only subagent /root/revision_check found no blocking
   issue, independently recomputed six P5 gates and verified 17 hashes. This narrow
   check is not a formal five-seat re-review or a claim of independent human review.
7. Workshop fitness: fixes the existing empirical argument without more inference.
   No complete manuscript is present yet. Fresh-table raw-vs-derived-summary model
   experiments are needed only to add the untested new mechanism/transfer claim.
Verdict: PASS-AS-RETROSPECTIVE-AUDIT; Qwen raw archive gap remains disclosed.

Outputs: data/ours/revision_cached/20261107/{summary.json,report.md};
current conclusions docs/CURRENT_CONCLUSIONS.md; version ledger and 22-item author
resolution in docs/HYPOTHESIS_LEDGER_2026-11-07.md and REVISION_2026-11-07.{json,md}.
Actual analysis environment recorded in summary.json (Python 3.11.13, numpy 1.26.4,
pandas 2.2.3, sklearn 1.7.0); not represented as the historical pinned environment.
