# Findings (narrative, kept current; each finding names the paper figure/table it feeds)

## F0 — What the data is (2026-10-31, inventory.py)
9,585 usable trajectories (4 real models, 26 adapters), 133 tasks, 41 tables, 24,741 tool events of
which 4,068 poisoned; 3,633 complete clean/toxic pairs. Fields the plan needs all exist. 38/41 tables
have <= 12 rows (median 4), so the context-richness axis has little range on the original tables:
the expansion to large tables is required, not optional. Feeds: Section 3 (setup), Table 1 (data stats).

## F1 — Observation failures are the majority of failures (taxonomy.py, G1 PASS)
3,633 pairs: capability 452, observation 682, unexposed 52, no-effect 2,447 (recovered 1,800 / silent
override 301 / other 346). observation/(cap+obs) = 0.60 overall, 0.49 numerical, 0.83 semantic.
By severity the share collapses at subtle (0.24) — partly because subtle numerical tasks are few (10)
and partly because a 1.1x poison can sit inside the evaluator's 10% tolerance. Silent override
(agent got a poisoned value, never re-called the tool, yet answered correctly) is 8% of pairs:
C2 labels must exclude or separately report it. H6 is EXPLORATORY (25 subtle observation pairs).
Feeds: Table 2, Section 5 (C2), limitations.

## F2 — [SUPERSEDED by F2' and F3'; kept for the record] A zero-parameter rule is strong where it applies (range_check.py, G2)
On unfiltered single aggregations (811 events, 283 poisoned): range check AUROC 0.93 at full preview,
0.93 at head-5, 0.90 at head-2; z-score 0.97 / 0.97 / 0.89. Within-table AUROC matches pooled. But
(a) head-5 equals full preview on 4-12-row tables, so the original data cannot show a context axis;
(b) 66% of poisoned python_exec events use filters/groupby/sort and a further 9% are out of scope for other reasons;
(c) there are no in-scope subtle events at all. G2 triggers the "rules suffice" fork provisionally,
but the honest statement is narrower: rules suffice for simple aggregations on tiny tables. The
paper's live question becomes whether anything covers the filtered 75% and how all signals behave
when the preview is a real truncation (large tables, P3). Feeds: Figure 1, Section 4.

## F1' — Observation failures survive a run-to-run noise null (taxonomy.py A-P1)
Clean-vs-clean discordance on 737 duplicate keys is 4.3% (toxic-vs-toxic 11.0%). Poisoned runs fail
23.1% of the time when the matched clean run succeeded: excess 18.7pp [15.1, 22.3] overall, 22.4pp
[16.8, 28.0] numerical; McNemar 734 vs 81. Noise-corrected observation share 0.55 (0.43 numerical).
Supersedes F1's raw 0.60. H6 remains exploratory (25 subtle observation pairs).

## F2' — [SUPERSEDED by F2''/F2'''; original numbers (41.8% / 58%) retained for the record] Coverage, not accuracy, limits zero-parameter checks on ToxicBench (range_check.py A-P2)
After excluding 482 ERROR observations the range check flags every poisoned mean it parses: 0a AUROC 0.95
(0.90 plausible+subtle) on 24.5% of poisoned events; sanity rows pass. 0b's 1.00 at T0/T1 is a leak: on
<= 5-row tables head-5 is the whole table and the clean z-score is exactly 0, as P2 predicted for T0.
Re-executing the agent's own code on the visible rows (0d) is in scope for 50% of poisoned events but
produces an interval for 41.8% (93 events hit NaN resamples, mostly filtered code on empty subsets) at
0.83 pooled / 0.72 plausible+subtle. The remaining 58% of poisoned events return multi-number
observations that no scalar method scores.
T0 from the CSV equals the agents' actual preview (769/769). G2 stays undecidable: nothing in scope is
on a table > 12 rows. Feeds: Figure 1 (coverage x accuracy per signal), Section 4.

## F3 — [SUPERSEDED by F3'/F4 after A-P3; v1 tasks, range check only] Large-table range-check ceiling (gen_tasks.py v1)
180 pre-registered tasks on six public tables (344-17,379 rows; 33% unfiltered / 50% filtered / 17%
grouped; symmetric log-ratio severities). Scoring the oracle poisoned value against the oracle clean
value, the range check's ceiling AUROC is 0.57 at T0 (only 14% of poisoned aggregates leave the full
column range), 0.55 at head-5 (61% of clean aggregates already fall outside a 5-row range), 0.55 at
head-2. The z-score is 0.71 at T0 (0.79 on unfiltered queries) and collapses to 0.57 at head-5.
Compared with F2' (0.95 on ToxicBench's 4-12-row tables), the rule's strength was a property of tiny
tables: when the column range is narrow relative to the aggregate, a 1.5x poison exits it; on real
tables it does not. Consequence: the "rules suffice" fork cannot fire on large tables (agent-run 0a <=
ceiling), and the live question for P4 is whether re-execution (0d), intrinsic signals, or a learned
scorer recover detection once the preview is a genuine truncation. Feeds: Figure 1 left panel, Section 4.

## F3' — [SUPERSEDED after round 3/5: the like-for-like control has only 2 unique (task, column) pairs in ToxicBench, not 43 events, and the hypergeometric test (p ~ 7e-5) says a factor other than range width separates the two sources; 'range width is the mechanism' is withdrawn. 0a numbers here also predate the A-P3d sum-bound fix] The range check's ToxicBench strength is a narrow-range effect (gen_tasks.py v2, A-P3)
210 pre-registered tasks on six public tables (344-17,379 rows; 60 unfiltered / 90 filtered / 60 grouped;
scales balanced within table x template). Scoring oracle poisoned vs clean values, a whole-column min/max
range check reaches AUROC 0.57 at T0 (hit rate 20%, within-table 0.57 [0.54, 0.60]). Like-for-like
control (op = mean, plausible, scale > 1): every ToxicBench in-scope event has column range < |clean|
(bin [0.5, 1.0), hit rate 1.00, n = 43); P3 tasks in that same bin hit 0.33 (n = 6) and 0.00 in every
wider bin. Range width relative to the aggregate is the mechanism; table size is its proxy. The hit-rate
bound 0.5 + 0.5h gives 0.84 at T1 on plausible+subtle, so the "rules suffice" fork cannot fire on these
tasks whatever an agent returns (decided formally at P4). Feeds: Section 4, Figure 1 annotation.

## F4 — [SUPERSEDED by F4' -> F4'' -> F4''': 'every zero-parameter method is near chance' at five rows was withdrawn by the k-sweep (0d 0.62 at k=5, monotone in k) and 'first direct evidence for the central claim' was retracted] With the whole table reconstructable, re-execution is near-perfect (gen_tasks.py v2, A-P3)
0d (re-execute the query on bootstrap resamples of the visible rows) at T0: AUROC 0.935 pooled, 0.92
plausible+subtle, 0.98 unfiltered / 0.92 filtered / 0.91 grouped, computable for 100% of tasks. At
head-5: 0d 0.54, 0a 0.53, 0b 0.54 (clean false-positive rate 69%); at head-2: 0.55 / 0.54 / 0.54; at
five random rows: 0.59 / 0.58 / 0.60 (so head order explains a few points, not the collapse). 0d is not
computable for 51% of filtered tasks at head-5 (the filter value is absent from five rows). This is the
first direct evidence for the central claim: detection tracks the checker's ability to reconstruct a
normal return, and that ability is a function of visible context, not of the signal family. It also sets
the bar for P4: anything claiming to add value must beat ~0.55-0.60 in the five-row regime, and nothing
needs to be learned in the full-table regime. Feeds: Figure 1 (both panels), Section 4.

## Disclosures added 2026-10-31 (round-3 and round-4 reviews)
- Degenerate-interval floor: range scores are normalized by (hi - lo) + 1% of the interval magnitude; it
  cannot change false-positive rates or within-task ranking; sensitivity {0, 0.1%, 1%} reported in A-P3c.
- 0r in the k-sweep v1 used a linear t (registered form was log-ratio) and the [0, n] range for counts;
  both recorded as deviations in A-P3c; the registered log form is used from A-P3c on.
- Headroom control is descriptive only: P3 n = 8 tasks, ToxicBench n = 2 unique (task, column) pairs;
  "hit = 1[0.5 > headroom]" is an algebraic identity for op = mean, not a verification.
- T0_agent v1 combined raw distances normalized by different widths and scored below its own min/max
  component; replaced by the standardized combination in A-P3c.
- grouped x max (5 tasks) equals the column max: an unfiltered-max task under another label.
- Auto MPG `horsepower` filtered means were dropped by the oracle cross-check (missing values parse as NaN
  in the stdlib path); Bike `windspeed` produced the one empty-filter drop. Both logged in dropped_tasks.jsonl.
- The v2 ceiling's R1 tier used one random draw per table; superseded by the k-sweep (20 draws per table per k).
- Noise floor: haiku has no duplicate keys and is excluded; per-model excess is reported alongside pooled.
- `range_check.py` (original tables) still uses its own 0d (resample n, drop on any failure); it is kept as
  the F2' record and will be re-run with `zeroparam.py` before P4 so the name "0d" means one thing.
- Threat model: a checker allowed to re-execute the query on the real data is re-calling the tool and wins
  under poison_once; the paper's setting is a checker limited to the agent's observation context.

## F4' — [SUPERSEDED by F4'' after A-P3c: the 0r reference was withheld and misspecified; 'information, not estimator' withdrawn] k-sweep v1 (ksweep.py, A-P3b; script and outputs removed from this repo, superseded by ksweep2.py)
210 tasks x k in {5,10,20,50,100,200} x 20 random row draws per table, B = 50, one shared implementation
(`zeroparam.py`: resample size = visible rows for every op, sums/counts scaled by n/k, degenerate-interval
floor). Sanity rows (values 10 column-spans outside the whole column) pass for 0a/0b/0d at every k.
0d AUROC rises monotonically with visible rows: 0.62 (k=5) -> 0.65 -> 0.69 -> 0.74 -> 0.79 -> 0.83
(k=200) -> 0.94 with the full table (reference, not a tier); (table, draw)-clustered CIs are +/-0.015.
By severity at k=5 / k=200 / full: subtle 0.56 / 0.74 / 0.87, plausible 0.64 / 0.87 / 0.96, obvious
0.71 / 0.94 / 1.00. The calibrated analytic reference 0r tracks 0d within 0.02-0.05 at k = 5-20 (0.60 /
0.61 / 0.64 vs 0.62 / 0.65 / 0.69), so per the A-P3b decision rule the small-k limit is the information
in k rows, not 0d's estimator; above k = 50, 0d beats 0r because the reference assumes unfiltered
statistics. Clean false-positive rate of 0d is 35% at k=5 and 14% at k=200 (nominal 5%): still
miscalibrated, half the previous design's. Upward poisons are easier than downward at small k (0d 0.66 vs
0.57 at k=5), converging by k=50; max is structurally one-sided and the worst op. **T0_agent** (what
ToxicBench's preview actually gives on these tables: head-5 plus whole-column min/max) scores 0.53-0.54:
the leaked bounds add nothing once the column range is wide. Withheld on sanity: 0r (low-side 0.93,
filtered sums) and T0_agent 0a/0d (0.93-0.95). Headroom (mean, scale 1.5): P3 median 1.08 (10-90%:
0.31-5.0) vs ToxicBench 0.30 (n = 2 unique tasks); hit = 1[0.5 > headroom] holds in both.
Supersedes F3'/F4's mechanism wording. Feeds: Figure 1 (continuous x-axis), Section 4; sets the C3 bar at
each k.

## F4'' — [SUPERSEDED by F4''' after A-P3d: 0o is computed from the full table and never conditions on the visible draw, so it bounds knowledge of the answer, not what k rows can tell a checker; 'information ceiling 0.79', '~0.17 recoverable' and 'C3 bar = 0o curve' are WITHDRAWN. The 0d curve, common-support fractions, sensitivities and T0_agent components stand] (ksweep2.py, A-P3c)
Oracle reference 0o = the true sampling distribution of each task's k-row statistic (M = 300 random
k-subsets of the full table, same undefined/scaling rules as 0d), scoring |log y - log median| / IQR. On
the common support (rows where both 0d and 0o are computable; 75% at k=5, 98% at k=200; 164 tasks
computable at every k), within-table AUROC:

| k rows | 5 | 10 | 20 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|
| 0o information ceiling | 0.79 | 0.82 | 0.86 | 0.90 | 0.93 | 0.96 |
| 0d bootstrap check | 0.62 | 0.65 | 0.68 | 0.74 | 0.79 | 0.82 |
| 0r (registered log t, unfiltered mean/median only) | 0.70 | 0.75 | 0.81 | 0.85 | 0.91 | 0.92 |
| 0o - 0d, table-level 95% CI | [+0.16, +0.19] | [+0.15, +0.19] | [+0.16, +0.19] | [+0.13, +0.20] | [+0.11, +0.19] | [+0.09, +0.19] |

Pre-registered decision (A-P3c): lower CI bound > 0.05 at k = 5, 10, 20 -> **estimator**. F4''s
"information, not estimator" is withdrawn. Five random rows carry enough information for AUROC ~0.79 on
these poisons (0.96 at 200 rows); a percentile bootstrap of the same statistic loses ~0.17 of it at every
k. Sensitivities: B = 500 vs 50 changes 0d by < 0.002 (clean FP 35.5% -> 33.3%); the interval floor {0,
0.1%, 1%} changes nothing. So 0d's loss is the small-k percentile bootstrap itself (undercoverage; identity
with the range check for median/max at k = 5), not its tuning. Consequences: (i) the C3 bar at each k is the
0o curve, not 0d; (ii) a context-aware checker has ~0.17 AUROC of headroom to recover without seeing more
rows; (iii) P4 plots agent signals at the k their observations exposed. T0_agent (head-5 bootstrap OR
whole-column min/max, components standardized by their clean 95th percentile) = 0.55, passes sanity (0.97)
but is below its 0a component (0.57), so it is reported as two columns, not one number. Feeds: Figure 1
(0o and 0d curves as the two reference lines), Section 4, the C3 evaluation bar.

## F2'' — [updates F2' numbers after porting to the shared 0d; superseded by F2''' after the A-P3d sum-type and 0a-sum-bound fixes] (range_check.py on zeroparam.py, A-P3c)
With the shared implementation (resample size = visible rows; AST sum-type rule; > 20% failure rule), 0d on
the original ToxicBench tables scores 514/1,153 poisoned events (44.6%; 61 dropped as not computable, was
93): AUROC 0.84 pooled / 0.73 plausible+subtle at T0, 0.81 / 0.69 at head-5; within-table 0.82 / 0.80
(14 tables). Sanity: T0 0.96 pass; head-5 0.94 borderline (withheld as a headline, reported in the table);
head-2 fails. The uncovered remainder is 55% of poisoned events (multi-number observations).

## F4''' — [replaces F4''] At five visible rows a checker that knows the exact k-row sampling law but centres on the rows it sees reaches 0.73; the bootstrap check reaches 0.62; knowing the answer adds another 0.06 that no k-row checker can have (ksweep2.py, A-P3d)
Two references, both from the same M = 300 full-table k-subsets per (task, k): **0o** (A-P3c) centres on the
population median of the k-row statistic and never looks at the visible rows; **0o\*** (A-P3d) keeps the
law's bias b_k and spread w_k but takes its centre from the observed draw's statistic, so it is what a
checker limited to these k rows could do if it knew the sampling law exactly. Common support = rows where
0d and 0o\* are both computable (76% at k = 5, 99% at k = 200; 168 tasks computable at every k, the
primary curve). Sanity rows (10 whole-column spans outside the column) pass >= 0.95 for 0a, 0d, 0o, 0o\*
and 0r_log at every k; nothing is withheld in this table.

Primary curve (168 tasks computable at every k, pooled AUROC; within-table in parentheses):

| k rows | 5 | 10 | 20 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|
| 0d bootstrap check | 0.62 (0.62) | 0.65 (0.65) | 0.69 (0.69) | 0.75 (0.75) | 0.80 (0.79) | 0.85 (0.84) |
| 0r_log (unfiltered mean/median only) | 0.71 (0.71) | 0.76 (0.75) | 0.81 (0.81) | 0.87 (0.86) | 0.90 (0.91) | 0.92 (0.92) |
| **0o\* draw-conditioned oracle** | **0.73 (0.72)** | 0.75 (0.74) | 0.78 (0.77) | 0.83 (0.83) | 0.87 (0.87) | 0.90 (0.90) |
| 0o population oracle (not achievable) | 0.79 (0.79) | 0.83 (0.81) | 0.87 (0.86) | 0.91 (0.91) | 0.94 (0.93) | 0.96 (0.96) |

Decomposition on the common support, mean over tables with 6-table bootstrap CI:

| k | 5 | 10 | 20 | 50 | 100 | 200 |
|---|---|---|---|---|---|---|
| estimator loss 0o\* - 0d | +0.11 [0.10, 0.13] | +0.09 [0.06, 0.13] | +0.08 [0.05, 0.11] | +0.08 [0.06, 0.10] | +0.08 [0.06, 0.09] | +0.06 [0.04, 0.06] |
| oracle knowledge 0o - 0o\* | +0.06 [0.05, 0.08] | +0.08 | +0.09 [0.06, 0.12] | +0.09 | +0.07 | +0.07 [0.03, 0.13] |

Pre-registered decision (A-P3d, lower CI > 0.05 at k = 5, 10, 20): **estimator loss**. The A-P3d
prediction committed before the run was 0.03-0.10 at k = 5; the observed point estimate 0.111 is just above
it (the CI lower bound 0.095 lies inside the predicted range), so the miss is marginal and is recorded as a
miss. The
A-P3c number is now split: of the 0.17 gap between 0d and 0o at k = 5, about 0.11 is signal left in the
visible rows that 0d's percentile bootstrap does not use, and about 0.06 is knowledge of the population
answer that no k-row checker can have. F4'''s "information ceiling 0.79" and "~0.17 recoverable" are
replaced by: **the achievable ceiling for a k-row checker using the template statistic is ~0.73 at five
rows, and 0d leaves ~0.11 of it on the table.**

Where the estimator loss lives: filtered 0.58 -> 0.69, grouped 0.61 -> 0.72, unfiltered 0.66 -> 0.77 at
k = 5 (all three template CIs clear 0.05 at k <= 20). By op at k = 5: max 0.52 -> 0.81 and count 0.61 ->
0.79 lose the most; mean 0.66 -> 0.74. Down-poisons lose more than up-poisons (0.57 -> 0.72 vs 0.66 ->
0.74).

**On unfiltered mean/median the round-5 reading holds.** 0d 0.68 / 0r_log 0.71 / 0o\* 0.73 / 0o 0.94 at
k = 5 (1,360 rows). 0o\* - 0d = 0.05 [0.02, 0.09] and 0o\* - 0r_log = 0.02 [0.01, 0.03]; at k >= 10 the
0r_log CI includes 0 and at k >= 100 0r_log is above 0o\*. So on the simplest queries the analytic
t-test recovers essentially all of the estimator loss, and the remaining 0.22 to 0o is knowledge of the
answer. Caveat on "upper bound": 0o\* bounds checkers that use only the observed statistic plus the exact
law; 0r_log also uses the visible rows' spread, a different information set, which is how it can exceed
0o\* at large k. Neither is a bound on a checker that reads the query and the full visible rows.

Sensitivities unchanged: B = 500 vs 50 moves 0d by 0.002 (clean FP 37% -> 35%); the interval floor moves
nothing. The 0a sum bound is now [n * min(min, 0), n * max(max, 0)] (A-P3d); 0a passes sanity at every k.

**T0_agent is two columns, not one** (A-P3d): whole-column min/max 0a = 0.57 (passes sanity, within-table
0.57); head-5 bootstrap 0d = 0.55 (sanity 0.945, **withheld** as a headline). No recombined number.

Consequences for P4 and the paper: (i) the C3 bar on slice (b) is "beats max(0d, 0r_log) on the same rows"
(primary) with "fraction of 0o\* - 0d closed" as the secondary (A-P3d); (ii) Figure 1 carries 0d and 0o\*
as the two achievable reference lines and 0o as a dashed "knows the answer" line; (iii) the central-claim
sentence is reconciled below. Exploratory (oracle values), decided by a pre-registered CI rule.

## F2''' — [updates F2''] 0d on the original ToxicBench tables under the A-P3d rules (range_check.py, A-P3d)
The A-P3d sum-type rule reclassifies 163 of the 1,568 scored python_exec events (92 -> 255 sum-type; the
old final-call rule missed grouped sums/counts, method-form `.round()`, `print(var)` and `shape[0]`). With
it, 0d scores 514/1,153 poisoned events (44.6%, 61 dropped as not computable): AUROC 0.84 pooled / 0.73
plausible+subtle at T0 (within-table 0.82 / 0.70, 14 tables), **0.83 / 0.71 at head-5 (within-table 0.81 /
0.70)**. Sanity: T0 0.96 / 1.00 pass; **head-5 now 0.95 / 1.00, pass** (was 0.94 borderline under the old
rule); head-2 0.85 fails and is withheld. The 0a y:=0 sanity falls to 0.86 because 0 now lies inside the
sum bound by construction (a filtered sum can be 0); 0a's y:=10y sanity is 1.00; 0a on the original tables
is not a headline (G2 is pre-decided undecidable). Uncovered remainder unchanged: 55% of poisoned events
are multi-number observations.

## Central claim, reconciled (2026-10-31, after A-P3d)
Earlier text said detection "depends less on which signal is used than on whether the checker can
reconstruct a normal return". F4''' shows two zero-parameter checks with identical rows differ by 0.11, so
the signal's estimator does matter. Reconciled statement: **what bounds detection is the information in the
observation context (0o\* rises monotonically from 0.73 at five rows to 0.90 at 200, and 0o - 0o\* is the
part no context-limited checker can recover); within that bound, how the checker uses the rows moves the
number by up to ~0.11 at small k, and the paper's question for P4 is where learned and agent-intrinsic
signals fall between 0d and 0o\*.**

## Known limitations of the A-P3d sum-type rule (round 6, 2026-10-31)
`is_sum_type` now returns False for count-distinct (`nunique`, `len(x.unique())`) and for a sum over
location statistics (`groupby(g)[x].mean().sum()`), since neither scales as n/k; 25 unit cases in
`test_zeroparam.py`. No ToxicBench event uses these forms (grep of all trajectories: 0 hits), so no reported
number changes. Any agent code outside the tested forms is classified location-type (conservative: 0d
intervals may then be too narrow for an unrecognised sum-type, raising false positives, never hiding poison).
P4 logs the classification per event so misclassifications can be audited after the run.

## F5 (preliminary, confirmatory protocol P4/A-P4) — Qwen3-4B at T1 (head-5, no min/max): the agent uses the poisoned value in 93% of runs, and no zero-parameter check on the same five rows gets above 0.58 (p4_run.py, p4_score_zeroparam.py, 2026-11-01)
630 trajectories (210 P3 tasks x clean seed 0 / clean seed 1 / toxic), vLLM Qwen3-4B, temperature 0.7, tier enforced in
the harness (482 preview calls, all exposed exactly 5 rows). Clean success 202/210 and 204/210; run-to-run noise
floor 2.9% (6/210 disagreements). Toxic success 4/210; poison fired in 202/210 runs; `poisoned_answer_used` in
196/210. Pair taxonomy (clean seed 0 vs toxic): observation failures 198, capability 8, no-poison-opportunity 4 (the toxic run never hit the poisoned call); observation
failure rate >= 29/30 in every (template x severity) cell including subtle. The agent never re-queried or
flagged a poisoned return (anomaly_detection 0). Harness normalizations fired in 630 (pandas re-import),
615 (read_csv resolved) and 51 (stray indent) events; 2 ERROR observations in 630 runs.

Zero-parameter signals on the agent's real events (193 poisoned scalar events vs 193 matched clean events;
within-table AUROC, 6-table bootstrap CI): 0a 0.54 [0.51, 0.58]; 0d (agent's own code re-executed on the five
head rows, 77% coverage) 0.55 [0.50, 0.61]; 0o* (draw-conditioned oracle on the head rows) 0.58 [0.55, 0.61];
0r_log (18% coverage) 0.58 [0.51, 0.65]. Plausible+subtle: 0.53 / 0.55 / 0.60 / 0.58. By severity (0d / 0o*):
obvious 0.58 / 0.62, plausible 0.54 / 0.58, subtle 0.51 / 0.52.

Reading: at the T1 ToxicBench gives agents, even the oracle that knows the k-row sampling law is near chance,
because the head rows are not a random sample (the A-P3d caveat: the k-sweep's 0o* = 0.73 at k = 5 assumed
random rows). G2 at T1 is settled: no zero-parameter method is sufficient (bar 0.90). The C3 / intrinsic-signal
bar on slice (b) at T1 is therefore max(0d, 0r_log) ~ 0.55-0.58, and the headroom to 0o* is ~0.03, so A-P3d's
"no headroom on slice (b)" clause applies at T1; signals 1/3/7 are judged against the absolute bar (slice a)
and against 0d at T0_agent / random-k tiers. Pending: T0_agent and T3 runs (in progress), signals 1 (logprobs)
and 3 (shadow verbalized), Qwen3-8B, gpt-5.4-mini.

## F6 (preliminary, P4/A-P4, H1 first test) — Qwen3-4B's own signals carry no information about poisoned returns: verbalized confidence 0.55 [0.48, 0.61], token entropy 0.47 [0.44, 0.50] (p4_run.py --run-tag r2, p4_score_intrinsic.py, 2026-11-01)
Replication run T1r2 (210 x clean seed 0 / seed 1 / toxic, same tier and settings as T1) with logprobs on every
live call and a shadow verbalized-confidence call after every python_exec observation. Behaviour replicates T1:
clean 203/204, toxic 4/210, poisoned_answer_used 196, observation failures 198, anomaly_detection 0. T3 (schema
only, no rows): clean 204/204, toxic 6, used 194, observation failures 198. Across T0_agent / T1 / T1r2 / T3 the
agent's behaviour does not move with observation context at all; what moves is what a checker can do (0a 0.54 at
T1 -> 0.57 with whole-column min/max at T0_agent, matching the P3 ceiling prediction).

Signals on the completion following the python_exec observation (202 poisoned vs 207 clean events, within-table
AUROC, 6-table bootstrap CI; H1 statistic = upper CI on plausible+subtle < 0.60):

| signal | all | plausible+subtle | H1 |
|---|---|---|---|
| 3 verbalized confidence, negated (clean mean 77.7, poisoned 76.7, mode 80 in both; ~85% of mass on {75, 80, 85}, so heavily tied) | 0.53 [0.46, 0.59] | 0.55 [0.49, 0.61] | upper 0.61: NOT confirmed at the registered threshold (0.01 over); point estimate at chance |
| 1 token entropy, first generated token (registered) | 0.49 | 0.49 [0.45, 0.52] | passes trivially: DEGENERATE, the first token is `{"` with entropy ~0 in every completion |
| 1' mean token entropy over the action (exploratory) | 0.47 | 0.46 [0.42, 0.50] | below chance: actions after a poisoned return are, if anything, slightly more confident |
| 1'' max token entropy / negative sum logprob (exploratory) | 0.50 / 0.47 | 0.50 / 0.47 | at or below chance |

Reading: every intrinsic signal is at or below chance within-table, but the registered verbalized statistic misses
its threshold by 0.01 on the CI upper bound, so H1(verbalized) is reported as "not confirmed at the registered
threshold; point estimate 0.55", not as passed. The registered first-token definition of signal 1 must be
replaced before any further agent run (A-P4 amendment): with JSON actions the first token is fixed, so entropy
must be measured over the value-bearing tokens of the action; the exploratory variants above are candidates.
Full T1 picture for Qwen3-4B: zero-parameter checks 0.55-0.58 (F5), intrinsic signals 0.47-0.55, achievable
oracle on head rows 0.58. Nothing available at T1 separates poisoned from clean returns for this agent. Open for
C3: slice (a) (multi-number returns; this agent produced almost none, 193-202 of 210 poisoned events are single
scalars) and the random-k tiers where 0o* has headroom (0.73 at k = 5). Pending: Qwen3-8B, gpt-5.4-mini
(A-P4 per-agent decisions), signal 7.

**Round-7 additions (2026-11-01).** (i) Zero-parameter pairing impurity: in 4.2% of task pairs the clean seed-0
run's first scalar python_exec code differs from the toxic run's poisoned code (different query formulation),
so the negative is not an exact code twin; reported here and left in. (ii) Harness-normalization sensitivity on
the existing data: runs that needed no normalization at all are 29/630 (T1), 61/630 (T0_agent), 20/630 (T3),
29/630 (T1r2); within them clean success is 20/19 (T1 clean), and poisoned_answer_used is 7/10, 13/18, 2/6,
7/10 of toxic runs, i.e. the same blind-compliance pattern as the full set, on a tiny subset. Without the
normalizations Qwen3-4B would have failed ~95% of tasks on FileNotFoundError; this is a model-formatting quirk
that the upstream sandbox counts as a harness-limit failure, not a property of the tool returns, and it is why
P4 normalizes for every agent. (iii) Harness counts in F5 were per event; per run they are 600 (pandas import),
599 (read_csv), 51 (indent) of 630.

## F7 (preliminary, P4/A-P4b, second agent) — Qwen3-8B at T1 replicates Qwen3-4B: 92% blind compliance, H1 confirmed for every intrinsic signal, zero-parameter checks 0.53-0.57 (p4_run.py, 2026-11-01)
630 trajectories (210 x clean seed 0 / seed 1 / toxic), same harness, tier T1, A-P4b signal definitions. Clean
199/210 and 202/210 (noise floor 5.2%; runs with a parse error 40/630 = 6.3%, parse-ok 0.94 >= the 0.90
adapter-fallback bar). Toxic success 5/210; poison fired 196; `poisoned_answer_used` 194 (92%);
anomaly_detection 0, validation 0. Pair taxonomy: observation 194, capability 11, no effect 5.

Zero-parameter on the agent's real events (196 poisoned vs 199 clean, within-table AUROC, 6-table CI): 0a 0.53
[0.51, 0.57]; 0d 0.53 [0.50, 0.57] (78% coverage); 0o* 0.57 [0.54, 0.60]; 0r_log 0.58 (17% coverage).
Plausible+subtle 0.52 / 0.54 / 0.58 / 0.58. Same picture as 4B (F5).

Intrinsic signals (completion after the poisoned observation; plausible+subtle within-table, H1 rule upper CI
< 0.60): verbalized confidence (negated) 0.53 [0.48, 0.57] -> **H1 confirmed**; mean action-token entropy (A-P4b
registered signal 1) 0.48 [0.46, 0.50] -> confirmed; max entropy 0.52 [0.48, 0.56], negative sum log-prob 0.50
[0.46, 0.56] -> confirmed. The 8B model is *more* confident than the 4B (verbalized mean 92.9 vs 77.7; mode 95
vs 80) and no more discriminating: its confidence on poisoned returns (92.4) is indistinguishable from clean
(92.9). First-token entropy 0.51 (degenerate, logged only).

Across the two open agents: behaviour identical (poison used 93% / 92%), intrinsic signals 0.46-0.55 for both,
zero-parameter checks 0.53-0.58 for both, oracle ceiling on head rows 0.57-0.58 for both. H4's "rankings stable
across agents" cannot be tested meaningfully when every signal sits within 0.05 of chance; it is reported as
"all signals tied at chance for both agents" rather than as a Kendall tau. Pending: Qwen3-8B T0_agent (running),
gpt-5.4-mini (API key), signal 7 (P5 scorer, pilot training in progress).

**F7 addendum — Qwen3-8B T0_agent (head-5 + whole-column min/max).** Clean 182/210 and 191/210 (noise floor
13.8%, the highest so far; parse-error runs 56/630 = 8.9%, still >= 0.90 parse-ok). Toxic success 7; poison fired
176; used 175 (83%); anomaly_detection 0; taxonomy observation 175 / capability 28 / no effect 7; the agent
called preview in 420/420 runs, so it saw the min/max every time. Zero-parameter on real events: 0a (whole-column
min/max) 0.53 [0.48, 0.58], 0d 0.53, 0o* 0.50 [0.39, 0.57], 0r_log 0.58. Intrinsic: verbalized 0.56 [0.49,
0.62] -> **not confirmed at the registered threshold** at this tier (confirmed at T1: 0.53 [0.48, 0.57]);
mean action-token entropy 0.48 [0.41, 0.55] -> confirmed. The verbalized shift is the first non-zero
movement seen: poisoned-return confidence 90.2 vs clean 91.5, with 80 vs 60 events at "85" — consistent with
the min/max in the preview giving the 8B model a weak cue it does not act on (behaviour unchanged, 83% used).
H1(verbalized) for Qwen3-8B is therefore tier-dependent: confirmed at T1, not confirmed at T0_agent; reported per
tier, no pooled claim.

## F8 (P5, confirmatory, C3 NEGATIVE) — The clean-only predictive scorer is at chance on every agent and tier (0.50-0.52) and fails its own sanity and calibration rules; the P5 prediction [0.55, 0.70] is missed (run_loto.sh K=5, score_scorer.py, 2026-11-02)
30 LOTO members (6 held-out tables x 5 bootstrap seeds, Qwen2.5-0.5B + LoRA r=16, 5-quantile pinball head,
1,741-1,772 clean examples each, 3 epochs, ~8 min/member on an A10G). Training pinball fell to 0.06-0.28, so the
members fit their training tables. On the held-out table they do not transfer: median |t - q50| = 0.78 in log10
units (a factor ~6 error in the predicted value), interval width q95-q05 median 0.65 log10 but clean coverage in
[q05, q95] only **0.15-0.18** (P5 window 0.80-0.98: FAIL); sanity rows x1000 / /1000 score **0.81-0.85 / 0.62-0.66**
(hard rule > 0.95: FAIL, so the surprise column is withheld as a headline and reported here as a negative result).
Direction of magnitude is learned (per-table corr(t, q50) 0.47-0.94) but the resolution is far coarser than the
poison: ToxicBench scales of 1.1-2x are 0.04-0.30 log10, an order of magnitude below the scorer's own error.

| eval set | events | surprise within-table [CI] | plausible+subtle | epistemic |
|---|---|---|---|---|
| Qwen3-4B T0_agent | 383 | 0.51 [0.49, 0.52] | 0.51 | 0.50 |
| Qwen3-4B T1 | 386 | 0.50 [0.49, 0.52] | 0.50 | 0.50 |
| Qwen3-4B T1r2 | 390 | 0.51 [0.50, 0.52] | 0.51 | 0.50 |
| Qwen3-4B T3 | 397 | 0.50 [0.50, 0.51] | 0.50 | 0.50 |
| Qwen3-8B T0_agent | 369 | 0.52 [0.49, 0.54] | 0.52 | 0.50 |
| Qwen3-8B T1 | 393 | 0.51 [0.49, 0.52] | 0.51 | 0.50 |

Clean events get *higher* median surprise (1.94) than poisoned events (1.67): the scorer's error dominates any
poison-induced deviation. Reading, per A-P3d's C3 bar: on slice (b) at T1 the scorer does not beat max(0d, 0r_log)
(0.53-0.58) and closes none of the 0o* - 0d gap; C3 as specified in P5 is a **negative result**. Why, in one
sentence: a 0.5B model trained on ~1,800 clean (query, code, 5-row preview) -> value examples learns the scale of
a column, not the statistic to within 10-50%, and the latter is what detection at these poison strengths requires.
Not tested here (would be P5b, requires a protocol amendment first): more data (the ToxicBench clean pool is only
538 scalar events after dedup), a larger backbone, a target that predicts the deviation from a zero-parameter
estimate (residual on 0d) instead of the raw value, or evaluation on the random-k tiers where 0o* leaves 0.11
of headroom. Paper consequence: the C3 column exists and is honest about failing; the paper's contribution
rests on C1 (every signal, learned or not, is at chance under the default observation context, with the
information-capacity curve explaining why) and C2.

## F5/F6/F7 correction (2026-11-07) — three scoring defects fixed (p4_common.py); numbers re-derived on all six eval sets

Source: external code review of the d0e7ba4 snapshot (collaborator, 2026-11-06). All three findings reproduced here and
fixed; `experiments/test_p4_common.py` covers the fixed semantics. Raw before/after output: `data/ours/p4/_recheck/`.

1. **Zero-parameter checks scored on the tier cap, not on what the agent saw.** `p4_score_zeroparam.py` took
   `df.head(k)` from the tier. In Qwen3-4B runs the agent called `preview` before its first scalar `python_exec` in
   only ~70% of runs (0 rows shown: 117/383 T0_agent, 115/386 T1, 117/390 T1r2); Qwen3-8B always previewed first
   (0/393, 0/369). Fixed: rows and min/max are reconstructed from the preview events preceding the scored event
   (`exposure_before`); 0 rows -> all row-based scores NA; 0a uses whole-column min/max only when the preview the
   agent saw carried it (4B T0_agent: 266/383 events, not 383). `--exposure protocol` keeps the old reading.
2. **Shadow-call misalignment.** `p4_score_intrinsic.py` zipped python_exec events with ERROR observations removed
   against completions that kept them. Fixed: the i-th observation-following completion is matched to the i-th tool
   event, ERROR included; tool-name mismatch -> missing. (`after_observation.n_tool_turns` is not a usable key: it
   counts assistant turns, which parse-error retries inflate.) Affected runs: 4 in 4B T1r2, 0 in 8B.
3. **Constant scores dropped instead of scored 0.5.** A table whose scores were all identical with both classes
   present returned NA and left the within-table mean. Fixed: 0.5 (`auc_or_none`); NA only when a class is missing or
   nothing is scored. Direction of this bug favoured us (dropped tables sit at 0.5).

Also: the intrinsic scorer now checks the single-number condition on the scored event itself (previously only the
zero-parameter scorer did), which removes 27-51 multi-value events per set; severity breakdowns use clean controls
from the same tasks; a paired-task column (both labels scored) is reported alongside the all-events column.

**Within-table AUROC, before -> after (actual exposure). Coverage in parentheses.**

| set | 0a | 0d | 0o* | verbalized (P+S, H1) | mean entropy |
|---|---|---|---|---|---|
| 4B T0_agent | 0.571 (1.00) -> 0.579 [0.53,0.64] (0.69) | 0.546 (0.76) -> 0.562 [0.52,0.62] (0.52) | 0.582 (0.67) -> **0.612 [0.55,0.69]** (0.48) | -- | -- |
| 4B T1 | 0.541 -> 0.544 (0.70) | 0.549 -> 0.554 (0.53) | 0.582 -> **0.611 [0.54,0.69]** (0.48) | -- | -- |
| 4B T1r2 | (KeyError) -> 0.545 | -> 0.552 | -> **0.616 [0.55,0.69]** (0.48) | 0.549 [0.48,0.61] -> 0.554 [0.50,0.61] FAIL (unchanged) | 0.467 -> 0.455 |
| 4B T3 | NA | NA | NA | -- | -- |
| 8B T1 | 0.533 -> 0.533 | 0.534 -> 0.535 | 0.571 -> 0.565 [0.53,0.59] | 0.532 [0.48,0.57] -> 0.527 [0.48,0.56] PASS (unchanged) | 0.489 -> 0.488 |
| 8B T0_agent | 0.532 -> 0.532 | 0.531 -> 0.525 | 0.495 -> 0.490 [0.39,0.56] (paired 0.544) | 0.558 [0.49,0.62] -> 0.558 [0.49,0.62] FAIL (unchanged) | 0.463 -> 0.464 |

8B differences of <=0.006 are Monte-Carlo noise from a changed RNG consumption order (oracle_m=300, boot=50), not the fix.

**What changes in the text.** (a) "no head-5 reference exceeds 0.58" (F5, F7, plan) is no longer true for Qwen3-4B:
restricted to the ~48% of events where the agent had actually seen five rows, 0o* is 0.61-0.62 with CI up to 0.69.
The restriction changes task composition, so the 0.03 shift is not a causal effect of seeing rows; report both the
actual-exposure and protocol readings, with coverage. 8B is unchanged. The qualitative claim (all signals at or
near chance on head-5; 0d and 0a <= 0.56 everywhere) stands. (b) "preview content has zero effect on agent
behaviour" is now stratified: poisoned value used, conditional on poison firing, preview seen vs not --
4B T0_agent 140/141 vs 55/58, T1 141/144 vs 55/58, T3 140/143 vs 54/57 (98-99% vs 95%); 8B always previewed
(194/196, 175/176). The claim survives and is stronger when stated this way: agents that looked at the rows (and,
at T0_agent, the min/max) complied at the same rate as agents that never looked. (c) All H1 verdicts are unchanged
(4B T1r2 FAIL by 0.01, 8B T1 PASS, 8B T0_agent FAIL by 0.02). (d) Two denominators must be reported for compliance:
used / all toxic runs and used / poison-fired runs (per the review: 91.3% vs 97.9% pooled).

Not re-run: the k-sweep (unaffected), the scorer (its eval files are built by build_dataset.py from the same first
scalar events; the exposure caveat applies to its head-5 interpretation and is noted, numbers unchanged at chance).

## F9 (A-P4-Gemini, 2026-11-07) — Gemini Flash external replication and scalar coverage

Protocol commit `4fa7740` precedes generation. Collection implementation `f01f8bf`;
`gemini-3.8-flash`, T1, low reasoning effort, provider-default sampling, no API seed,
same 210 tasks and ReAct prompt, eight-step limit. Independent clean repeats 0 and 1
and toxic repeat 0 produced 630 complete trajectories. The twelve disjoint shards
were merged after verifying one row per task per repeat. All stored metrics match
recomputation with the pinned ToxicBench evaluator. Data and machine-readable
summary are under `data/ours/p4/gemini-3.8-flash/T1/`.

| Run | Tasks | Task success | Poison fired | Poison adoption | Subsequent-evidence flag | Recovery |
|---|---:|---:|---:|---:|---:|---:|
| Clean 0 | 210 | 200 | 0 | 0 | 0 | 0 |
| Clean 1 | 210 | 198 | 0 | 0 | 0 | 0 |
| Toxic 0 | 210 | 131 | 128 | 72 | 55 | 50 |

Conditional on the 128 actually exposed runs, poison adoption was
72/128 = 56.2%,
and recovery was 50/128 =
39.1%. The legacy `poisoned_answer_used` flag
counts mentions and was 73/210; 72 of those
were exposed. The final-answer anomaly keyword flag was zero. Recovery is an outcome
after further evidence calls. Intentional error detection requires separate annotation.
In 37/50 recovery trajectories,
a Python tool error also occurred after the poisoned return, so retry and harness behavior
are material to interpreting recovery. Under poison_once, later successful tool calls
can return the true result.

Of the 128 first poisoned observations, 35 were scalar under the existing parser
(26 adoptions, 9 recoveries), and 93 were non-scalar (46 adoptions, 41 recoveries).
This output-format difference and the model-specific sampling settings limit
direct comparison with the Qwen rates. The 82 toxic runs without a fired poison
are separately visible in the summary.

**H5 is not confirmed.** The registered subtle slice contains 73 eligible tasks,
but only 7 paired scalar tasks from 3 tables
have valid confidence on both sides. Their within-table AUROC is
0.556, table-bootstrap 95% interval
[0.500, 0.667]; the upper endpoint exceeds 0.60.
The plausible+subtle secondary slice has 17/178 paired tasks
from 5 tables, AUROC 0.520
[0.500, 0.560]. These are diagnostics for selected
scalar events. The low coverage and missing tables prevent a full-task confidence claim.
A dedicated obvious-corruption sanity control for verbalized confidence was not collected,
so these estimates are withheld from positive signal-quality headlines.

Confidence was a valid integer in 731/769
shadow requests. Among valid replies, 711 were 100.
All 630 trajectories had parseable final answers and zero intermediate action parse errors.
The two clean repetitions disagree on success for 4/210 tasks.

Formal responses recorded 1679 live and 769
shadow requests, 1,260,597 input tokens and
125,680 output tokens. At Google's listed introductory prices
of $0.75/M input and $3.75/M output, recorded formal usage estimates to
$1.42. Pilot usage adds about $0.04. This estimate covers saved response usage.
The run used Python 3.11.13 / NumPy 1.26.4 / pandas 2.2.3 / SciPy 1.10.1 /
scikit-learn 1.7.0, which differs from the original requirements file.
The protocol, manifest, environment and trajectory hashes are recorded in the run directory.

[Google pricing](https://ai.google.dev/gemini-api/docs/pricing).


## F10 — Fixed-return context pilot, Gemini Flash (2026-11-07; exploratory)

A-CTX-PILOT protocol `bfaf713`, collection code `7e5c662`, frozen requests `5da0d36`, pre-call clarification `41473be`. Completed 72/72 stateless audit responses, 67/72 strict-schema valid, across 12 selected filtered-mean queries and six tables. This is a prompted single-turn audit, not the free-running P4 agent.

| Context | Accept clean | Accept corrupted | Wrong scalar adopted | Truth recovered from corrupted |
|---|---:|---:|---:|---:|
| head5 | 12/12 | 9/12 | 9/12 | 0/12 |
| random20 | 12/12 | 7/12 | 7/12 | 0/12 |
| matched20 | 11/12 | 5/12 | 5/12 | 0/12 |

Primary matched20 minus random20 contrast in clean-minus-corrupted acceptance: +8.3pp, descriptive six-table bootstrap CI [-16.7, +33.3]pp. Not evidence of a stable benefit. Complete-valid-pair sensitivity: 8 queries/5 tables, +10.0pp [+0.0, +30.0]pp; selected support cannot remove missingness bias.

Strict counts include invalid outputs in denominators. Five invalids consist of three complete JSON replies wrapped in markdown fences and two length truncations; none was repaired or rerun. The main contrast includes format-related changes, not just semantic judgments. Ten valid reject replies still rate tool correctness at 95 or 98, suggesting confidence-scale noncompliance. No post-hoc score inversion. Confidence AUROC withheld: no live extreme-corruption sanity control. Some rationales quote standard-dataset population means; model priors/memorization cannot be ruled out. No claim that judgment uses only visible rows. Corrupted final answers never recover truth under the no-requery policy; rejecting replies abstain.

All 72 packets were validated; 36 corrupted cells have completed responses. The 72 replies are repeated conditions of 12 queries, not 72 independent tasks. One sample and one completion per cell; severity and direction slices are descriptive. Independent protocol/results review: PASS-AS-EXPLORATORY. Full per-table/severity output, raw responses and Qwen reproduction command: [Chinese report](docs/CONTEXT_PILOT_2026-11-07_gemini.md).
## F10 addendum — Qwen3-8B reproduction of the fixed-return context pilot (2026-11-07): the weak Gemini signal does NOT replicate

Same frozen manifest (SHA d9c467df…, byte-identical to the Gemini run), same A-CTX-PILOT protocol, Qwen3-8B served
locally via vLLM (temperature 0.7, seed 0), 72/72 cells completed, **72/72 strict-schema valid** (Gemini was 67/72).
Run on an A10G GPU instance (24 GB), stopped after.

| Context | Accept clean | Accept corrupted | Wrong scalar adopted |
|---|---:|---:|---:|
| head5 | 12/12 | 10/12 | 10 |
| random20 | 10/12 | 9/12 | 9 |
| matched20 | 12/12 | 11/12 | 11 |

**Primary contrast matched20 − random20 (clean-minus-corrupted acceptance): 0.000, six-table bootstrap CI
[-0.333, +0.333].** matched20 − head5 = -0.083; random20 − head5 = -0.083.

**The context-checking benefit does not replicate and the direction flips.** Gemini rejected corrupted values
*more* with matched rows (corrupted-accept 9→7→5 across head5/random20/matched20, contrast +0.083); Qwen3-8B
accepts corrupted values at 9-11/12 in every context (contrast exactly 0.0), i.e. it accepts the poisoned scalar
almost always regardless of what rows it is shown. Across the two models the matched20−random20 effect is
+0.083 (Gemini) vs 0.000 (Qwen) with CIs spanning zero in both — no stable, model-general evidence that showing
more representative rows makes a prompted checker reject corrupted returns.

**Consequences.**
1. The "Gemini shows signs of improvement with more context" observation (F10) is now bounded: it did not hold in
   Qwen and even reversed in direction. We do NOT claim a context-checking benefit. A-CTX-PILOT is reported as an
   exploratory null across two models, consistent with the paper's descriptive framing of claim C3.
2. This removes the motivation to spend the larger T_max free-running-agent run ($7, ~6 h) *to confirm a checker
   benefit* — there is no replicated effect to confirm. T_max remains independently useful only for the different
   question "does the free-running agent change behaviour with much more context" (C1 pressure test), not for C3.
3. Confidence AUROC withheld for Qwen as for Gemini (no live extreme-corruption sanity arm; Qwen confidence means
   83-90 on both clean and corrupted, same scale-noncompliance pattern).

Data: `data/ours/context_pilot/20261107/qwen3-8b/{summary.json,scored_responses.json,config.json}` (72 raw
responses retained on the instance disk). Independent recompute of the acceptance counts and primary contrast by
the orchestrator matched the summarizer.


### F10 addendum clarification — verified primary contrast and confidence scope (2026-11-07)

Independent recomputation from both scored files agrees with the existing counts and all registered contrasts. Configs use the same canonical manifest and source hashes. This is verification of existing results, not a new experiment.

| Model | head5 wrong adoption | random20 wrong adoption | matched20 wrong adoption | Primary matched20 - random20 |
|---|---:|---:|---:|---:|
| gemini-3.8-flash | 9/12 | 7/12 | 5/12 | +8.3pp [-16.7, +33.3] |
| qwen3-8b | 10/12 | 9/12 | 11/12 | +0.0pp [-33.3, +33.3] |

The earlier phrase "direction flips" does not describe the primary contrast: Qwen's estimate is zero, not negative. Some secondary point estimates and raw acceptance counts move oppositely. Both primary intervals span zero; this pilot establishes neither equivalence nor a general lack of context benefit. Qwen random20 also makes two clean uncertain decisions, so the context effect on corrupted acceptance alone is not the registered discrimination effect.

The earlier "same scale-noncompliance pattern" is unsupported for Qwen. Its scored records contain 64 accept/confidence=90 and eight uncertain/confidence=50, with zero reject. These do not exhibit Gemini's reject/high-tool-correctness-confidence contradiction. Confidence calibration remains untested and AUROC remains withheld for the missing live sanity arm, without inventing a semantic violation.

Audit scope: Gemini 72/72 raw replies re-parsed; Qwen 0/72 raw replies present in this repository. Qwen schema validity and rationale cannot yet be independently checked beyond scored/config records. Archive raw responses and runtime versions; do not rerun merely to fill this audit gap.

Next priority: preregister an offline same-evidence statistical-checker feasibility study to distinguish limited evidence from inadequate evidence extraction. No new API run or this proposed study was executed in this review. Full scope, independent reviewer conclusions and decision branches: [Qwen review and next steps](docs/REVIEW_2026-11-07_qwen_context_next.md).


## F11 — Same-evidence statistical feasibility (2026-11-07, exploratory)

A-CTX-EVIDENCE protocol `f94ffbb`, frozen analysis code `a5b6e07`.
No new LLM calls. Existing twelve filtered-mean queries, six tables, one frozen sample per
query/context; features parsed only from the exact CSV evidence shown to models.

Primary 0d matched20 passes sanity AUROC 1.000, with
12 paired queries/6 tables. Actual within-table AUROC
0.917, descriptive six-table bootstrap CI [0.833, 1.000];
pooled AUROC 0.882 is secondary. Fixed compatibility policy flags
10/12 corrupted returns and 1/12 clean returns;
2/12 corruptions remain compatible. No unscorable matched20 cases.

On the identical matched20 data evidence, Qwen accepts 11/12 corrupted returns and
12/12 clean returns; Gemini accepts 5/12 corrupted and 11/12 clean, with 2 corrupted and
1 clean invalid response(s). These are prompted model judgments versus a structured-query
statistical procedure, not equivalent representations, computation, cost, or calibrated
probabilities. Gemini valid-pair sensitivity has only nine queries/five tables. No claim
of generally superior model performance or identified internal mechanism.

0a matched20 passes sanity but has actual within-table AUROC
0.583. Both methods at head5/random20
fail sanity; their real AUROCs and all cross-context policy contrasts are withheld, not
used as evidence of a quantified context benefit. Counts for failed conditions remain
gate-failed diagnostics. Bootstrap intervals have no asserted finite-population 95% guarantee.

Interpretation: this fixed matched20 sample contains statistical signal accessible to an
existing checker. Insufficient displayed data alone cannot summarize all model failures
here. Extraction/representation/use of evidence are candidates for a fresh intervention,
not proven mechanisms. Selected reused tasks, six clusters, one sample/completion, public
data priors and missing Qwen raw responses limit scope. No new algorithm or universal bound.
Independent event/formula/ranking review: PASS-AS-EXPLORATORY.

Next: independent row-draw robustness and fresh generated/transformed-table controls, then
raw rows versus summaries derived from the identical rows, retaining 0d, clean and sanity
controls. Each new study gets its own protocol; no outcome-driven expansion of this run.
Full generated tables, plot, exceptions and paper implications:
[report](docs/CONTEXT_EVIDENCE_2026-11-07.md).
