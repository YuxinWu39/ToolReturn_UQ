# Round-3 review: A-P3 execution, F3'/F4, and P4

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's advocate (checkpoint 2). Date: 2026-10-31.
Prior reviews: `docs/REVIEW_2026-10-31_pilot.md` (2, 3, 2, 3, 4, 2; mean 2.67) and
`docs/REVIEW_2026-10-31_rescore.md` (3, 4, 3, 4, 4, 3; mean 3.5).

**Method note.** This session again had no shell, so I could not run `git -P log` or the venv Python.
Commit order comes from `.git/logs/HEAD` (epoch seconds; 2026-11-01 00:00 UTC = 1793491200). Numbers were
recomputed with exact line counts over `ceiling_events.jsonl` (one JSON object per line, fixed key order)
and with closed-form AUROC bounds. Clean values were checked by counting matching rows in the CSVs and
reading extreme values. I could not compute a filtered mean (that needs arithmetic over about 100 rows),
and I could not compute exact AUROCs at truncated tiers, where most scores are non-zero on both classes.
Each number below says how it was obtained.

## Verdict

**GO-WITH-CHANGES.** The rescore's three actions were executed, and protocol came before results again.
Most of the specific findings were fixed. Two new claims are weaker than they read:

- **F3' says the like-for-like control "confirms range width is the mechanism". The control shows the opposite.**
  In the only bin where both sources have data, ToxicBench hits 43/43 and P3 hits 2/6
  (hypergeometric p ≈ 7×10⁻⁵). The two sources also define "plausible" differently.
- **F4's five-row collapse comes largely from 0d's design, not only from the data.** At k ≤ 5, 0d is
  numerically identical to the range check 0a for median and max (and for every op at k = 2). Its
  nominal 95% interval misses the clean value for 70% of tasks even with five *random* rows. Its
  unsigned score also reverses sign with the poison direction. F4's T0 number (0.935) is the oracle
  with bootstrap noise added, and no agent tier in P4 corresponds to it.

None of this needs agent runs to fix. P4 is mostly complete, but four of its decisions are either decided
in advance or can be tuned after seeing data (section H).

New mean **3.33** (D1 3, D2 3, D3 3, D4 4, D5 4, D6 3), which maps to Weak Accept. D2 dropped because
P4 added tests that cannot fail.

## A. Did the rescore's actions and findings land?

| Rescore item | Status | Evidence |
|---|---|---|
| Action 1: amendment before the 0d/0b ceilings | ✅ | A-P3 `85270e2` at 00:17:04 UTC; `gen_tasks.py` mtime 00:18, `ceiling.json` 00:19; results `79ad44a` at 00:25:19 |
| Action 1: 0d/0b by tier × template × severity, within-table CI | ✅ | `ceiling.json` has every cell, with a table-bootstrap CI over 6 tables |
| Action 1: like-for-like control | ⚠️ run, but conclusion overstated | see c |
| Action 1: NaN handling | ⚠️ only half done | `gen_tasks.py` uses the >20%-failure rule and reports the computable fraction. `range_check.py` still drops the interval when **any** resample fails, and still resamples size **n for every op**. F2' (0.83, 41.8%) and P4's 0d are therefore two different signals with one name |
| 0d coverage 41.8% / 58% | ✅ | A-P3 corrections, F2', plan line 20, `research-state.yaml` evidence_gaps |
| 0b leak | ✅ | labelled in F2' and A-P3 ("leak upper bound") |
| P3 power deviation | ✅ | grouped = 60 |
| Unbalanced scales | ✅ | per-(table, template) shuffled 12-cycle; unfiltered gets 3-6 tasks per scale (1.2 has only 3) |
| Filtered-sum inconsistency | ✅ | one rule: n × [min, max] for all templates |
| Head-order bias | ⚠️ | R1_rand5 added, but drawn **once per table** (`rand_rows`, 6 draws total), so "head order explains a few points" has no uncertainty attached |
| Sanity rows for 0b/0d | ⚠️ partial | done on the original tables only, with the old 0d. **0d_T2 fails** (0.84 / 0.90). **No sanity rows exist for the P3 ceiling at any tier** (see d) |
| Noise floor by model | ✅ with a gap | gpt 6.46% (n = 449), sonnet 1.08% (277), Qwen 0.0% (n = 11), haiku none. The reweighted 4.84% reproduces as (0.0646·2261 + 0.0108·602 + 0·290)/3153. Haiku's 480 pairs are silently left out |
| G2 "refuted" overreach | ✅ | `expected-to-fail-by-bound` |
| Plan line 20, plan H6 | ✅ | both updated |
| F2 marked superseded | ✅ | also F3 |
| Action 3: P4 before any agent run | ✅ | `7a5ce00` has no trajectories; see e and H |

**Noise floor sensitivity (arithmetic).** If Qwen and haiku had gpt's 6.46%, the reweighted floor would be
(152.56 + 0.0646·770)/3633 = 5.6%. The excess would then be 23.1 − 5.6 = 17.5 pp. G1 still passes easily.
Report the excess per model (stratified), not pooled-minus-pooled, so a model-mix difference between
duplicate keys and pairs cannot cause a Simpson-style artefact. [CPU-only]

## Spot-checks

### a. `ceiling_events.jsonl` recomputation

| Quantity | Reported | Recomputed | How |
|---|---|---|---|
| 0d T0 AUROC | 0.9350 | **in [0.9268, 0.9351]; equals 0.9350 when 362 of the 366 possible wins against 2 non-zero clean scores occur** ✓ | Clean: 208/210 score 0. Poisoned: 27/210 score 0. AUROC = (183·208 + ½·27·208 + W)/210², with W ≤ 366 |
| 0d T0 clean false-positive rate | n/a | **2/210 = 1%** (both are grouped sums) | count |
| 0d T1 computable | 0.78 | **164/210 = 0.781** ✓ | 46 null rows per label |
| 0d T1 clean false-positive rate | not reported | **136/164 = 83%** | 28 of 164 clean rows score 0 |
| 0d T1 AUROC | 0.540 | **not recomputed**: 136 clean and 143 poisoned rows are non-zero, so the ranking needs execution | |
| 0a T1 clean false-positive rate | 0.686 | **144/210 = 0.686** ✓ | 66 clean rows have 0a = 0 |
| 0a T1 hit rate | 0.690 | **145/210 = 0.690** ✓ | 65 poisoned rows have 0a = 0 |
| R1_rand5 exists | yes | **420 rows** ✓ | count |
| R1 0d computable | 0.84 | **176/210 = 0.838** ✓ | |
| R1 0d clean false-positive rate | not reported | **123/176 = 70%** | 53 clean rows score 0 |
| R1 0d AUROC | 0.587 | not recomputed (same reason as T1) | |

**The two unreported false-positive rates matter most.** 0d's interval is a nominal 95% bootstrap interval.
With five *random* rows it misses the clean value for 70% of tasks. A calibrated interval would miss about
5% for unbiased location statistics. Sections G and D explain why.

### b. `clean_value` against the CSVs (grep counts and extremes, not pandas)

| Task | Template / op | Oracle | CSV | ✓ |
|---|---|---|---|---|
| `lt_penguins_v3_fil_017` | filtered count, species = Gentoo | 124 | 124 rows `^Gentoo,` | ✓ |
| `lt_penguins_v3_fil_025` | filtered count, year = 2007 | 110 | 110 rows `,2007$` | ✓ |
| `lt_auto_mpg_v4_fil_012` | filtered count, model_year = 78 | 36 | 36 rows | ✓ |
| `lt_penguins_v3_fil_018` | filtered max flipper, Gentoo | 231 | max over Gentoo rows 231; no row ≥ 232 | ✓ |
| `lt_auto_mpg_v4_gro_027` | grouped max mpg by cylinders | 46.6 | global max 46.6 (mazda glc) | ✓ |

I did not recompute a filtered or grouped **mean**. Two findings came out of this check:
- **Grouped × max is a degenerate template.** `groupby(g)[c].max().max()` is the column max, so the 5
  grouped-max tasks are unfiltered max tasks under another label. Re-draw them or disclose them. [CPU-only]
- **Auto MPG `horsepower` is silently excluded.** All 3 `oracle_mismatch_or_zero` drops are horsepower
  filtered means where the stdlib path returned NaN (missing values that parse as `nan`). The check worked
  as designed, but it removes the one column with missing data. Disclose it in P3. The `empty_filter` drop
  is Bike `windspeed`, a float column used as a categorical. [writing-only]

### c. Is the like-for-like comparison sound?

No. The data:

| rel_range bin | ToxicBench hit (n) | P3 hit (n) |
|---|---|---|
| [0, 0.5) | n/a | 1.00 (2) |
| **[0.5, 1.0)** | **1.00 (43)** | **0.33 (6)** |
| ≥ 1.0 | n/a | 0.00 (16) |

1. **In the one bin that both sources share, the hit rates differ.** Under equal rates, the probability that
   all 4 misses fall among P3's 6 is C(6,4)/C(49,4) = 15/211,876 ≈ **7×10⁻⁵**. So something other than
   range width separates the sources. Where the bins do not overlap (≥ 1.0) the data cannot separate
   "range width" from "source", because ToxicBench has no events there.
2. **"Plausible" means different scales in the two sources.** The ToxicBench events use ToxicBench's
   `infer_severity` (`range_check.py` line 205): plausible with scale > 1 is [1.4, 2.0). P3 uses
   log-ratio bins: 1.20, 1.35, 1.50. The control therefore compares mostly 1.5× poisons against a mix that
   includes 1.2× and 1.35×.
3. **The mechanism is an identity.** For `mean`, 0a fires iff `scale > max/clean` (or `scale < min/clean`).
   The right covariate is **headroom** = (max − clean)/|clean| together with the exact scale, not range/|clean|.
   Given both, the hit is determined; there is nothing left to "confirm".

**What would make it convincing:** report the *distribution of headroom* in ToxicBench in-scope columns
against P3 columns, as the empirical claim ("real tables leave more headroom above the mean than 4-12-row
toy tables"). Show hit = 1[s − 1 > headroom] holding in both sources at a fixed scale (1.5). With n = 6
in the shared cell, no statement about mechanism should appear in F3' or in the plan's Central claim.
[CPU-only + writing-only]

### d. A-P3's 0d resample rule and the sanity hard rule

- **The resample rule matches A-P3 in `gen_tasks.py`.** `size = len(vis) if op in LOCATION_OPS else n`,
  with `LOCATION_OPS = {mean, median, max}`; a task-tier is not computable when > 20% of resamples fail. ✓
- **The rule makes 0d at k ≤ 5 the same as 0a.** At T1, median and max rows have 0d == 0a to 10 digits
  (e.g. `lt_penguins_v3_unf_001` T1: 1.1527777775 / 1.1527777775; `unf_002`, `unf_010` likewise). At T2,
  mean rows are identical too (`unf_003` T2: 2.9830409351 both). A size-k bootstrap of a k-row sample puts
  its 2.5/97.5 percentiles at about the sample min and max. F4's "0d 0.54, 0a 0.53" is one method reported
  twice, not two methods agreeing.
- **The sum rule gives a point, not an interval.** Resampling n (up to 17,379) rows from 5 rows gives
  n·mean(head-5) ± a negligible width. That is a z-like distance from a point estimate. A-P3's own
  justification ("the interval must express sampling uncertainty of the visible subset") applies to sums
  as well. Use size k and scale by n/k. [CPU-only, needs a dated amendment]
- **The sanity failure was handled on the original tables only.** On the original tables, 0d_T2 fails the
  sanity row (0.84 / 0.90). The log says it is "not reported as a real number", F2' does not cite it, and
  `summary.json` still lists it in `pooled` without a flag. On the P3 ceiling, `gen_tasks.py` computes **no
  sanity rows**, yet F4 reports 0d, 0a and 0b at head-5, head-2 and random-5. That breaks program.md's hard
  rule ("Every signal must pass the sanity row ... before its real number is reported"). The original-table
  T1 pass does not carry over: on ≤ 12-row tables head-5 is nearly the whole table, and that 0d used
  resample size n. **Fix:** add y := 0 and y := 10y rows per tier to `gen_tasks.py`, and withhold any
  tier-signal that fails. 0d at T2 will probably fail. [CPU-only]

### e. Git order

| Commit | UTC | Content |
|---|---|---|
| `85270e2` | 00:17:04 | A-P3 protocol |
| (files) | 00:18-00:22 | `gen_tasks.py` 00:18, `ceiling.json` 00:19, `range_check.py`/`taxonomy.py` 00:20, `PREREGISTRATION.md` 00:21, `range_check.log` 00:22 |
| `79ad44a` | 00:25:19 | A-P3 results |
| `7a5ce00` | 00:25:19 (same second) | P4 protocol |

- A-P3 precedes its scripts and results. This fixes the rescore's "script mtime vs protocol" concern. ✓
- P4 contains no agent results, and no trajectory directory exists. ✓
- **P4 was written after F4.** `PREREGISTRATION.md` mtime is 00:21 and `findings.md` is 00:20; P4 quotes
  0.84 and 29%. That is legitimate for outcomes that do not exist yet. It also means two P4 tests were set
  with their answers in view (H). Run `git -P diff 85270e2 7a5ce00 -- PREREGISTRATION.md` and confirm that
  only P4 was appended and the A-P3 text is unchanged. I could not run git. [CPU-only]

## F. Re-scored dimensions

| Dim | Rescore → now | One sentence | Blocking item if < 4 |
|---|---|---|---|
| D1 Evidence relevance | 3 → **3** | F1' and the hit-rate bound are sound. F3' cites a control that contradicts it in the shared bin. F4's "every zero-parameter method is near chance at five rows" rests on one method counted two or three times and on an interval with 70-83% clean misses. | Rerun F4 with sanity rows, a k-sweep over repeated random draws, AUROC split by scale direction, and a calibrated reference score (G). **[CPU-only]** |
| D2 Falsifiability | 4 → **3** | Thresholds are numeric and scoped, but in P4 G2 is decided by bound, H2's T0 arm is decided by the 0d@full ceiling, H1 confirms a null on point estimates, and H2 lets the author choose between 0d and 7. | Amend P4 so each decision can fail and names one statistic (H). **[writing-only]** |
| D3 Scope calibration | 3 → **3** | The earlier over-claims are fixed. New ones: "confirms range width is the mechanism", "first direct evidence for the central claim", "nothing needs to be learned in the full-table regime", and 0d@T0 described as a context tier. | Rewrite F3', F4, Central claim and the plan's C3 line per c and G. **[writing-only]** |
| D4 Argument coherence | 4 → **4** | The arc from the central claim to P4 decisions is clear. Leftover contradictions: plan H2 (0a/0b/7, < 0.05 at schema-only) vs P4 H2 (0d/7, < 0.10 at T1); plan C1 "3 open + 2 closed × 2 envs" and MATH4AI "all 5 tiers" vs P4's 2 + 1 agents and 3 tiers; `research-state.yaml` H2/H6 still use the old wording. | n/a (writing-only cleanup) |
| D5 Exploration integrity | 4 → **4** | Reversals are recorded rather than hidden: F3 is superseded, the log says "the claim ... is WRONG as stated", and the 0d_T2 sanity failure is logged. The integrity gap is that the same 0d_T2 then appears in F4 on new tables without a sanity check. | n/a |
| D6 Methodological rigor | 3 → **3** | Stratified scales, the power rule, the random tier, within-table CIs and the bound are real improvements. Open problems: no sanity rows on P3, R1 drawn once, CIs over only 6 clusters, two 0d implementations, a point-interval for sums, max structurally inverted, and unsigned scores averaging out opposite poison directions. | Same CPU bundle as D1, plus one shared 0d implementation used by `range_check.py`, `gen_tasks.py` and P4. **[CPU-only]** |

Mean 20/6 = **3.33**. Grade: Weak Accept (mean ≥ 3.0, no dimension < 2).

**Can D1, D3 and D6 reach 4/5 without agent runs?**
- **D3 = 4 is reachable now, by writing alone.** D3 = 5 needs per-agent generalisation boundaries, which
  only P4 can supply.
- **D1 and D6 can reach 4 CPU-only, but only for an artifact whose claims are limited to oracle-value
  ceilings** (F1', F2', F3', F4 as descriptive results). For the paper as planned, the central claim
  ("agent-intrinsic signals do not recover what reconstruction loses"), H1, H2 and C3 have no evidence
  until P4 runs. In that frame D1 and D6 are capped at **3**.
- **5 on any of D1, D3 or D6 is not reachable without agent runs.**
- **CPU-only ceiling:** about 4, 4, 4, 4, 4, 4 for a "zero-parameter ceilings" pilot report; about 3 on
  D1/D6 when the paper's own contributions are the measure.

## G. F4: right computation, wrong reading

**Is the computation right?** The parts I could check are. 0d T0 0.935 is reproduced within its tie bound;
computable fractions (1.00 / 0.78 / 0.84) and 0a hit and false-positive rates match exactly. T1 and R1
AUROCs need execution.

**Is the T0 result trivial?** Yes, and it is not a point on the agent's context axis.
- At T0, 0d runs the oracle's own template code on the full table. Deterministic re-execution (B = 0)
  returns `clean_value` exactly and scores AUROC = 1.0 on every task. The 0.935 measures how much a 100-draw
  bootstrap band hides a 5-10% shift: 27/210 poisoned values fall inside it, mostly subtle sums and counts.
  It is "oracle plus noise", and it describes the bootstrap's tolerance rather than detection.
- **No agent tier matches it.** P4's agent T0 is "DATASET SUMMARY with numeric_min/max + head 5". The 0d
  ceiling's T0 is the whole table. Plotting 0d@T0 = 0.93 on the same x-axis as agent signals at T0 compares
  a checker that sees all the data with an agent that sees five rows and two bounds. Relabel it
  "full-data reference", and compute 0d at the agent's real T0 (head-5, plus min/max as clipping bounds).
- **Threat model.** ToxicBench poisons are `poison_once`. A checker that may re-execute code on the real
  data is re-calling the tool, and under this corruption model it wins outright. A reviewer will ask why the
  checker cannot just re-query. The paper must state the setting in which a checker sees only the agent's
  observation context: the data reachable only through the tool, persistent corruption, or cost. It should
  also include a "re-query the tool" reference row that is perfect under `poison_once` and useless under
  persistent corruption. [writing-only, plus one P4 row]

**Is the five-row collapse a property of the data or of 0d's design?** Mostly the design, partly the data.
Four mechanisms, each verified in `ceiling_events.jsonl`:

1. **Identity with 0a.** At k = 5, 0d's interval is the sample range for median and max; at k = 2 it is the
   range for every op. "0d ≈ 0a ≈ 0b ≈ 0.54" is mostly one statistic.
2. **Miscalibration.** The clean value falls outside the "95%" interval for 83% of computable tasks at
   head-5 and **70% at random-5**. The causes: a percentile bootstrap undercovers badly at k = 5; the sum
   interval is a point; for max the clean value is above the visible max by construction; for grouped tasks
   the top group in five rows is often not the true top group.
3. **Direction cancellation.** The score is unsigned distance outside an interval that already excludes the
   clean value. When the visible rows sit low (Penguins head-5 is light Adelie birds), an upward poison moves
   y further out and a downward poison moves it **in**. Examples at T1: `unf_003` (× 1.35) poisoned 7.42 >
   clean 0.64, but `unf_007` (× 0.952) poisoned 0.48 < clean 0.93, and `unf_008` (× 0.909) 0.12 < 0.68. For
   max, any scale < 1 moves the clean max toward the visible range, which inverts the ranking at any k < n
   (`unf_002`, `unf_010`, at T1 and R1). Symmetric scales then average an above-chance half and a
   below-chance half to about 0.5. That is information pointing the wrong way, not missing information.
4. **Data (real, but smaller than 0.54 suggests).** For a 5% poison on a column with CV ≈ 0.3, the shift is
   0.17σ while the standard error of a 5-row mean is 0.45σ; that case is undetectable. For low-CV columns
   at plausible scales, five random rows carry signal. On Penguins R1 unfiltered means, 0b ranks poisoned
   above clean in 5/5 pairs I read (`unf_003`, 004, 005, 007, 008).

Also, the pooled 0.54 includes unfiltered **count** tasks. Those are perfectly separated at every tier,
because the interval is [n, n] and the shape is visible. The non-count figure is therefore lower still.

**The single CPU-only analysis that makes F4 robust:** a **k-sweep with repeated random draws, split by
poison direction, with a calibrated reference score.**
- k ∈ {5, 10, 20, 50, 100, 200, full}; 50 random draws per table per k.
- Signals: 0a, 0b, 0d (size-k resampling for every op, sums scaled by n/k), plus an analytic reference: a
  signed log-ratio t-score, (log y − log m̂_k) / (ŝ_k / (m̂_k √k)), for mean and sum, and an order-statistic
  interval for median. Max is reported separately as structurally one-sided.
- Report AUROC and clean false-positive rate by k × op × direction (scale > 1 vs < 1) × severity, with
  draw-and-table bootstrap CIs, plus the sanity rows at each k.

If 0d tracks the reference curve, the collapse belongs to the data and F4 stands (rescoped). If the reference
is well above 0d at k = 5-20, F4 describes 0d's design. In that case the bar for C3 is the reference curve,
not 0.55. The sweep also gives Figure 1 a continuous x-axis instead of three points, without any agent runs.

**Suggested F4 rewrite:** "With all rows available, re-executing the query detects plausible poisons (AUROC
0.92; this is the oracle plus bootstrap tolerance and is a reference, not a context tier). With five visible
rows, range-, z- and bootstrap-based checks fall to 0.53-0.60. These checks coincide at k ≤ 5 and are
miscalibrated (70-83% clean false positives), so this measures these estimators, not the information
available in five rows; see the k-sweep."

## H. P4 as pre-registered

**What is complete:** tasks, tiers enforced in the harness, the agent list, the signal list, the primary
slice, a second clean seed, the budget and drop order, and the contamination subset. That is enough to run.

**Decisions that are still underspecified or already decided:**

| Decision | Problem | Fix |
|---|---|---|
| **G2** | Decided before data: bound 0.84 < 0.90 and coverage 29% < 50%. Not a test. | Keep it, but label it "pre-decided by bound" and do not count it as a confirmatory result |
| **H2, T0 arm** | Uses "A-P3 rules", so 0d at T0 = full table, about 0.93. Beating a ~0.5-0.6 prior by > 0.20 is near-certain. | Define 0d's visible rows per tier as **exactly the preview the agent saw**; report full-data 0d only as a reference |
| **H2, which signal** | "content-aware signals (0d, 7) beat ... by > 0.20" does not say whether one, both, or the max must pass. That can be tuned after the data. | Name the statistic: e.g. max(0d, 7) for the T0 arm and each signal separately for T1, or require both |
| **H1** | "AUROC < 0.60" on point estimates confirms a null, so an underpowered run passes. | Confirm iff the **upper** 95% CI bound < 0.60; state n per agent in the subtle bin (73 tasks) |
| **C3** | Training data includes "P3 clean runs". Those are the evaluation tasks, so the scorer can memorise per-task clean values. "Parity on (b)" has no margin. Slice (a) (multi-number observations) has no power rule; on template tasks most poisoned returns are scalars. | Train on tables disjoint from the evaluation tables (leave-one-table-out); parity = \|Δ\| < 0.05 with the CI inside ±0.10; minimum n for slice (a) or it becomes exploratory |
| **Noise floor** | Primary runs at temperature 0, second clean seed at 0.7, so the noise null mixes temperature with run-to-run variation. | All three runs at the same temperature, or two clean runs at each temperature |
| **Clustering** | The G2 lower CI is a bootstrap over 6 tables, which is coarse and anti-conservative. | Cluster on task, nested in table; report both |
| **Event selection** | Which python_exec events count as negatives (all clean events, or the target-matching one)? Are unexposed toxic runs excluded? | State it; P2's "all python_exec events" rule plus an explicit exclusion list |
| **0d on agent code** | The resample size depends on the op ("location op"), but agent code is arbitrary. | A fixed classifier (AST: final call in {mean, median, max, min} → k; anything else → k with ×n/k), committed before the runs |
| **Pooling across agents** | H2, C3 and G2 do not say per-agent or pooled. | Per agent; pooled only as secondary |

**Where P4 could be gamed after seeing data:**
- The adapter fallback (`smolagents_toolcalling` → `langgraph_react_full`) has no trigger condition.
- The H2 signal choice (above).
- The budget drop order can be applied after early results; "second clean seed on toxic-only tasks" is
  ambiguous.
- The scorer split is not fixed.
- The contamination subset has no decision rule if it disagrees with the originals.

Fix each with one sentence in an A-P4 amendment committed before the first run.

## I. Final verdict and next actions

**GO-WITH-CHANGES.** The process discipline is good and the agent-run plan is close to ready. The
zero-parameter story the agent runs will be measured against has two weak spots: the T0 reference and the
k = 5 estimator. Fix them first; they are cheap.

1. **Make F4 robust before any agent run [CPU-only, about half a day].** Add a dated A-P3b amendment, then:
   (a) sanity rows per tier on P3 for 0a/0b/0d, withholding failures; (b) one shared 0d implementation for
   `range_check.py`, `gen_tasks.py` and P4 (size-k resampling for every op, sums scaled by n/k, >20%-failure
   rule); (c) the k-sweep with 50 random draws per k, split by poison direction, with the analytic t-score
   reference; (d) 0d at the agent's real T0 (head-5 + min/max), with full-table 0d relabelled as a
   reference; (e) a headroom-based replacement for the like-for-like control at fixed scale 1.5.
2. **Amend P4 (A-P4) and fix the write-ups [writing-only].** In P4: per-tier 0d visibility equal to the
   agent's preview; one named statistic per decision; the H1 upper-CI rule; a leave-one-table-out scorer;
   equal temperatures; the adapter fallback trigger; event selection; task-level clustering; per-agent
   decisions; and the threat-model paragraph with a "re-query the tool" reference row. In findings, the plan
   and `research-state.yaml`: remove "confirms range width is the mechanism", rescope F4 (G), align plan
   H1/H2/C1/MATH4AI tiers with P4, update the stale H2/H6 wording, and disclose grouped × max and the
   horsepower exclusion.
3. **Then run P4, API agents first [needs agent runs].** gpt-5.4-mini plus hosted Qwen3-4B at T1 first,
   since T1 is the primary slice and the only tier where every claim lives. Add T0 and T3 next, and the GPU
   (token entropy) last. Check after the first 210 × 3 trajectories that the poison fires and that the
   positives equal the oracle poisoned values. The hit-rate bound argument depends on that.

**Strongest part:** the protocol trail. Every result since the first review follows a dated amendment, and
the authors withdrew their own F3 headline when the data contradicted it.
**Single most important improvement:** stop F4 from standing for "five rows carry no information". At
k ≤ 5 the three methods are one miscalibrated estimator. Until a calibrated reference has been run, the bar
the learned scorer must beat is unknown.

## Sources
- `docs/REVIEW_2026-10-31_pilot.md`, `docs/REVIEW_2026-10-31_rescore.md` — accessed 2026-10-31
- `PREREGISTRATION.md` (P1-P4, A-P1-A-P3), `findings.md`, `research-log.md`, `research-state.yaml`, `program.md`, `.git/logs/HEAD` — accessed 2026-10-31
- `experiments/{gen_tasks.py, range_check.py}` — accessed 2026-10-31
- `experiments/results/{gen_tasks.log, range_check.log, taxonomy/summary.json}` — accessed 2026-10-31
- `data/ours/{ceiling.json, ceiling_events.jsonl, dropped_tasks.jsonl, tasks/large_tables_v2.jsonl, datasets/public_penguins_v3.csv, datasets/public_auto_mpg_v4.csv}` — accessed 2026-10-31
- private planning notes (not included in this repository)
- `/tmp/AI-research-SKILLs/22-agent-native-research-artifact/rigor-reviewer/SKILL.md`, `/tmp/academic-research-skills/deep-research/agents/devils_advocate_agent.md` — accessed 2026-10-31
