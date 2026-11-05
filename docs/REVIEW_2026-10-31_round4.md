# Round-4 review: A-P3b / A-P4 execution, F4', and the CPU-only ceiling

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's advocate (checkpoint 2). Date: 2026-10-31.
Prior reviews: pilot 2.67 → rescore 3.5 → round-3 3.33 (D1 3, D2 3, D3 3, D4 4, D5 4, D6 3).

**Method note.** This session had no shell, so I could not run `git -P log` or the venv Python, and I
could not recompute any AUROC from `events.jsonl` (14.8 MB, ranking needs execution). What I did:
- Commit order from `.git/logs/HEAD` (epoch seconds; 2026-11-01 00:00 UTC = 1793491200) and file mtimes.
- Exact line counts over `data/ours/ksweep/events.jsonl` with anchored regexes (pandas `to_json` lines,
  fixed key order `task_id … tier, draw, label, computable_0d, t_signed, 0a, 0b, 0d, 0r`). These give
  computable fractions, clean false-positive rates and support sizes exactly.
- AUROC values and gaps are read from `summary.json` / `ksweep.log`; they are reported, not recomputed.
- Code paths read line by line in `zeroparam.py` and `ksweep.py`.

Each number below says how it was obtained.

## Verdict

**GO-WITH-CHANGES. The CPU-only ceiling has not been reached.** New mean **3.5** (3, 4, 3, 4, 4, 3).

Actions 1 and 2 were executed and the protocol came first again (e71e8e3 at 00:37 UTC, results e2f0f5a at
01:38 UTC). The shared implementation, size-k resampling, n/k scaling, per-k sanity rows, 20-draw
k-sweep, direction split, agent-real T0 and most of A-P4 are in place. The weak point is the one result
this round was designed to produce: **the A-P3b design-vs-data test**. F4' concludes "the small-k limit
is the information in k rows, not 0d's estimator". That conclusion rests on:

1. a reference (0r) that fails its own sanity row at every k and is therefore withheld by A-P3b's rule;
2. a reference that is misspecified for 150 of 210 tasks (it uses unfiltered column statistics for
   filtered and grouped queries) and that deviates from the registered log-ratio form;
3. a comparison on different supports (0d is scored on 79% of k=5 draws, 0r on 100%; the missing 21% are
   all filtered tasks);
4. a margin of 0.0005 at k=20 on the pooled metric, which flips on the primary within-table metric (0.0503).

The T0_agent result ("leaked bounds add nothing") is also reported from withheld cells. Its combined score
(0.534) is below its own min/max component alone (FULL_reference 0a 0.567), which points to a broken
combination rule rather than a data property.

All of this is fixable on CPU in about half a day plus a writing pass.

## A. Did round-3 actions 1 and 2 land?

| Round-3 item | Status | Evidence |
|---|---|---|
| 1a sanity rows per tier on P3, withhold failures | ✅ with a deviation | `ksweep.py` computes s_hi/s_lo per tier and signal; `withheld` list is populated. The definition changed from A-P3b's "y := 0, y := 10y" to "10 column-spans outside the whole column" (logged in research-log; reason: 0 is a legitimate value for 66 tasks). The change makes the test easier to pass; justified, but it is a post-protocol change |
| 1b one shared 0d implementation | ⚠️ partial | `zeroparam.py` exists and `ksweep.py` imports it. **`range_check.py` and `gen_tasks.py` do not import it** (grep: only `ksweep.py` has `from zeroparam`). A-P3b says all three plus P4 use it. Disclosed in findings as deferred to before P4 |
| 1b size-k resampling, sums ×n/k, >20% rule | ✅ | `bootstrap_0d`: `sample(n=k)`, `factor = n/k if scale_sum`, `failed > 0.2*B → None`; `ksweep.py` passes `scale_sum=(op in ("sum","count"))` |
| 1c k-sweep, repeated draws, direction split, calibrated reference | ⚠️ | k ∈ {5..200}, **20** draws (round 3 asked 50; A-P3b registered 20, so compliant with own protocol), B = 50, direction split present. The "calibrated reference" 0r is neither calibrated nor as registered (see a, H) |
| 1d 0d at agent-real T0; full table relabelled | ✅ implemented, ⚠️ combined badly | `T0_agent` = max(0a on whole-column [min,max], 0d on head-5); `FULL_reference` label used |
| 1e headroom control at scale 1.5 | ✅ run, small n | P3 n = 8, ToxicBench n = 2 unique (task, column) pairs (see d) |
| 2 A-P4 amendment | ✅ mostly | see e |
| 2 findings / plan / state rewrites | ⚠️ partial | F4' replaces F4; H1/H2/C1 in the plan are aligned. Stale: plan "Central claim → Evidence so far" still says "like-for-like control … confirms range width is the mechanism", "0.54 on five rows", "every zero-parameter method is near chance"; plan C3 line still cites "0.93 at full-table … ~0.55 at five rows"; MATH4AI line still says "all 5 tiers"; F3' is not marked superseded and still says "Range width … is the mechanism" with n = 43; `research-state.yaml` gen_tasks_002 row still says "confirms range-width mechanism", evidence_gaps still says "180 tasks" |

## Spot-checks

### a. k-sweep numbers and the A-P3b decision rule

| Quantity | Reported | Recomputed / read | How |
|---|---|---|---|
| k5 clean rows | n/a | 4,200 | line count (210 tasks × 20 draws) |
| k5 0d computable | 0.789 | **3,314 / 4,200 = 0.789** ✓ | 886 clean rows with `"0d":null` |
| k5 0d clean FP rate | 35% | **1,172 / 3,314 = 0.354** ✓ | 2,142 computable clean rows have `"0d":0.0` |
| k200 0d clean FP rate | 14% | **579 / 4,155 = 0.139** ✓ | 45 null, 3,576 zero |
| k5 rows where 0d is null | n/a | **886 / 886 are `template = filtered`** | anchored count; = 49% of the 1,800 filtered draws |
| k5 rows where 0r is null | n/a | **0** | 0r is scored on every row |
| 0d AUROC k5 / k200 (pooled) | 0.62 / 0.83 | 0.6182 / 0.8273 from `summary.json`; **not recomputed** | needs ranking |
| 0d − 0r, pooled | "0.02-0.05" | k5 **0.0221**, k10 **0.0373**, k20 **0.0495** | arithmetic on `summary.json` |
| 0d − 0r, within-table | not reported | k5 0.0227, k10 0.0373, **k20 0.0503** | arithmetic on `summary.json` |

**Was the decision rule applied correctly? No, for four reasons.**

1. **0r is withheld at every tier.** `summary.json` `withheld` contains `k5:0r … k200:0r` and
   `FULL_reference:0r` (s_lo 0.927-0.928 at every k). A-P3b: "any signal-k cell below 0.95 is withheld
   from findings". F4' quotes 0r's values (0.60 / 0.61 / 0.64) and decides the rule from them. The
   research-log acknowledges this ("reported with that caveat"). Honest, but under the registered rule the
   comparison is **not decidable**, not "information".
2. **Different supports.** 0d's AUROC at k5 excludes 21% of draws, all filtered tasks whose filter value is
   absent from the k rows. 0r is scored on those draws with an unfiltered reference, which is close to
   uninformative there. The 0.022 gap mixes "0d on easier rows" with "0r on all rows". The rule must be
   evaluated on the common support (rows where both are non-null).
3. **Point estimates at the threshold.** The k20 gap is 0.0495 pooled and 0.0503 within-table. The plan
   makes within-table AUROC primary (2610.05572 lesson). On the primary metric, "agree within 0.05 at
   k = 5-20" fails at k = 20. With per-signal CIs of ±0.015, a difference of 0.05 is not distinguishable
   from 0.035 or 0.065. A pre-registered rule should be decided on the CI of the paired difference.
4. **The rule is one-sided in what it can conclude.** It names an outcome for "0r > 0d by > 0.05" and for
   "agree within 0.05", but not for "0d > 0r by > 0.05". That case is the one that occurs at k ≥ 50, and
   F4' explains it post hoc ("the reference assumes unfiltered statistics"). That explanation is an
   admission that 0r is not a valid reference for filtered/grouped tasks at any k, small k included.

**By-op view (from `summary.json`, k5, 0d vs 0r):** mean 0.658 vs 0.663, median 0.655 vs 0.654, sum
0.618 vs 0.566, count 0.605 vs 0.536, max 0.540 vs 0.502. 0d and 0r agree on the two ops where 0r is a
real t-test (mean, median). The pooled gap comes from count (0r is the [0, n] range check there), sum
(0r misspecified for filtered sums) and max (0r one-sided). This partially supports the "information"
reading for location ops, but the by-op cells still pool unfiltered, filtered and grouped templates, so
it is not a clean test.

### b. Sanity-row redefinition and withheld cells

- **Implementation matches the stated redefinition.** `sanity_values`: span = max − min + 1 of the whole
  column; s_hi = max + 10·span, s_lo = min − 10·span; ×n for sums; count uses 10n and −1. ✓
- **The test is now very easy.** A value 10 column-spans outside the whole column is a gross-bug detector,
  not a calibration check. 0r still fails it on the low side at every k, which shows how far 0r is from a
  calibrated reference.
- **The withheld cells are not actually withheld in F4'.**
  - 0r: values quoted and used for the decision (above).
  - T0_agent 0a/0d (sanity s_lo 0.933 / 0.934): F4' says "T0_agent … scores 0.53-0.54: the leaked bounds
    add nothing once the column range is wide" and in the same paragraph lists them as withheld. Plan C1
    and `research-state.yaml` (ksweep_001: "T0_agent 0.53") repeat the number. This breaks program.md's
    hard rule ("Every signal must pass the sanity row … before its real number is reported").
- **Why T0_agent fails, and why its number is suspect.** The score is `max(0a_full, 0d_head)`. The two
  terms are normalized by different widths (whole-column range vs a 5-row bootstrap interval), so clean
  head-5 scores can exceed a sanity value's whole-column score. The combination drops below its own parts:
  T0_agent 0d 0.534 < FULL_reference 0a 0.567 (the min/max component alone). A sound OR-combination
  should not lose to its own component. Fix: combine flags, not raw distances (e.g. score = max of
  per-component scores each standardized against that component's clean distribution, or report
  head-5 0d and whole-column 0a side by side). Then re-run sanity. [CPU-only]

### c. `bootstrap_0d`, filtered count, and the degenerate-interval floor

- **Resample size k for every op** ✓ (`vis_df.sample(n=k, replace=True)`).
- **Sum and count scaled by n/k** ✓, including grouped and filtered variants through `template_stat`.
- **Filtered-count fix** ✓: `template_stat` returns `len(sub)` of the resample, scaled by n/k, so a filtered
  count is a proportion estimate. Unfiltered count gives the exact interval [n, n].
- **Still unfixed: 0d ≈ 0a for median/max at k = 5.** At k5, median rows have 0d == 0a to 10 digits in some
  draws (`lt_penguins_v3_unf_001` k5 draw 1 poisoned: 1.5554247418 both) and nearly equal in others
  (draw 0: 1.169 vs 1.133). With B = 50, the 2.5/97.5 percentiles of a size-5 bootstrap median sit at
  or near the sample's order statistics. Round-3 mechanism 1 (identity) survives for median/max at k = 5.
- **B = 50 is thin for 2.5/97.5 percentiles.** The interval endpoints are interpolations between the 1st/2nd
  and 49th/50th order statistics, so endpoint noise contributes to the 35% clean FP rate. Registered as
  B = 50, so not a protocol breach. Report a B = 500 sensitivity at k = 5 and 20. [CPU-only]
- **Degenerate-interval floor.** `range_score` width = (hi − lo) + 0.01·(|lo| + |hi|)/2. It is disclosed in
  F4' only as "degenerate-interval floor"; the 1% value is in the docstring, not in findings.
  **Does it bias 0d?** It cannot change the clean FP rate (the numerator is untouched, so "score > 0" is
  unchanged), and it cannot change any within-task ranking (monotone rescaling per task). It rescales
  scores across tasks, which affects pooled and within-table AUROC. Tasks with near-degenerate intervals
  (unfiltered counts, large-k sums) have their poisoned scores capped, which lowers their rank against
  other tasks' clean false positives. The likely net effect is a small **downward** bias on pooled 0d,
  not an inflation. It also applies to 0a and to 0r's count branch, so it does not favour 0d over the
  others. Verdict: acceptable; state the 1% value in findings and add a {0, 0.1%, 1%} sensitivity row.
  [writing-only + CPU-only]
- **0r deviates from the registered form, and that deviation is not logged.** PREREGISTRATION line 320
  registers a log-ratio t for mean and sum ("linear t if any value <= 0"). `reference_0r` uses the linear
  t for every y ("A-P3b clarification: one branch for every y", code comment only; nothing in
  research-log or findings). Poisons are symmetric in log ratio (×1.5 and ×1/1.5). A linear t gives the
  upward shift 0.5m and the downward shift 0.333m, so **the downward poison is harder by construction**.
  0r's direction split (k200 up 0.714 vs down 0.620, never converging) fits this artifact. F4' reports
  "upward poisons are easier than downward at small k" as a finding; part of that is the scoring scale.
  0d's unsigned linear distance has the same tilt at small k. [CPU-only to fix; writing-only to disclose]
- **0r ignores the filter.** `reference_0r(op, y, vis_values, n)` receives the whole visible column, not
  the filtered subset. For 90 filtered and 60 grouped tasks, it tests a filtered/grouped aggregate against
  the unfiltered column mean. It is not a reference for those tasks at any k.

### d. Headroom control

- `summary.json`: P3 **n = 8** tasks (mean, scale 1.5), quantiles 0.31 / 1.08 / 5.04, predicted hit 0.25;
  ToxicBench **n = 2** unique (task, column) pairs, 0.27 / 0.30 / 0.33, predicted hit 1.00.
- F4' states "ToxicBench 0.30 (n = 2 unique tasks)" but **does not state P3 n = 8** and does not label the
  control descriptive. 10th/90th percentiles of 8 and 2 values are interpolated extremes and should not be
  printed as quantiles.
- **"hit = 1[0.5 > headroom] holds in both" is an algebraic identity, not a verification.** The script
  computes only the predicted hit rate; it never compares against observed 0a hits. For op = mean at
  scale 1.5 with positive clean values, 0a(full) fires iff 1.5c > max, i.e. iff 0.5 > headroom. "Holds"
  is true by definition. A-P3b itself says "no mechanism claim beyond that identity", so the honest
  wording is: "the only empirical content is the headroom distribution; n = 8 vs n = 2; descriptive".
- **New disclosure needed.** Round 3's like-for-like "43/43 ToxicBench events" collapses to **2 unique
  (task, column) pairs** after dedup. F3' still prints n = 43 as if it were 43 independent observations.
  Mark F3' superseded and correct the n. [writing-only]

### e. A-P4: round-3 gameable items

| Round-3 item | Status in A-P4 | Remaining gap |
|---|---|---|
| H2 signal choice | ✅ "for each of 0d and 7 separately" | Say whether H2 is confirmed only if both pass, or report per signal with no joint claim |
| H2 T0 arm decided in advance | ⚠️ **flipped, still decided in advance** | With 0d visibility = T0_agent, the oracle ceiling is 0.53 (withheld). "0d − prior > 0.20" at T0_agent is now near-certain to **fail**, and "< 0.10" at T1 is near-certain to pass. H2's 0d arms are pre-decided by the k-sweep; only signal 7 is a live test. Label H2(0d) "pre-decided by ceiling", as G2 is |
| H1 upper CI | ✅ | n = 73 subtle tasks × 3 runs per agent stated |
| Scorer leave-one-table-out | ✅ | With 6 tables, LOTO = 6 folds; state that the scorer also trains on ToxicBench clean returns (allowed, but disclose) |
| Temperatures | ✅ all 0.7 | P4 body still says "temperature 0 for the primary run"; add "superseded by A-P4" inline |
| Adapter fallback trigger | ✅ < 90% parseable on a 20-task smoke set | |
| Event selection | ⚠️ | Negatives = clean events "that yield a scalar". **C3 slice (a) is multi-number observations, so slice (a) has no negatives under this rule.** Define negatives for (a). "Both environments" is ambiguous (P4 runs one environment) |
| Clustering | ⚠️ | Task-nested-in-table is specified for G2 only. H1, H2, C3 and C2 CIs do not name a clustering unit |
| Per-agent decisions | ✅ | |
| Contamination rule | ✅ > 0.10 AUROC → subset primary for H1/H2 | |
| 0d on agent code | ⚠️ | "Resample size k for every op, no op classifier needed" is incomplete: the n/k scaling still requires knowing whether the agent's statistic is sum-type (sum/count) or location-type. Commit a rule (e.g. AST final call in {sum, count, len, size, value_counts} → ×n/k) before the runs |

### f. Git order

| Commit | UTC | Content |
|---|---|---|
| `e71e8e3` | 2026-11-01 00:37:10 | A-P3b + A-P4 protocol |
| files | 00:37 `PREREGISTRATION.md`; 00:58 `zeroparam.py`, `ksweep.py`; 01:07 `events.jsonl`; 01:08 `summary.json`; 01:38 `findings.md`, `research-log.md`, `research-state.yaml` | |
| `e2f0f5a` | 2026-11-01 01:38:05 | A-P3b results |

- Protocol precedes code and results. ✓ `PREREGISTRATION.md` mtime equals the protocol commit, so the
  registered text was not edited afterwards. ✓
- Three "clarifications" were made in code after the protocol (linear t for 0r; sanity redefinition; 0r
  count as [0, n] range). Only the sanity redefinition is logged. I cannot tell from mtimes whether any of
  them followed a first look at results. Record all three as a dated A-P3b deviation note. [writing-only]

## G. Re-scored dimensions

| Dim | Round 3 → now | One sentence | Blocking item if < 4 |
|---|---|---|---|
| D1 Evidence relevance | 3 → **3** | The monotone 0d curve, its FP rates and the computable fractions are solid and reproduce. F4''s headline (information, not estimator) and the T0_agent statement rest on withheld, misspecified or wrongly combined signals scored on mismatched supports. | Oracle sampling-distribution reference + protocol-conformant 0r on common support; fixed T0_agent combination with sanity (I.1). **[CPU-only]** |
| D2 Falsifiability | 3 → **4** | A-P4 names one statistic per decision with CI-bound rules, and G2 is labelled pre-decided. H2's 0d arms are now decided by the ceiling, the A-P3b rule is decided on point estimates at a 0.0005 margin, and slice (a) has no negatives. | n/a (writing-only fixes listed in I.2) |
| D3 Scope calibration | 3 → **3** | "The small-k limit is the information in k rows", "the leaked bounds add nothing" and "upward poisons are easier" each overreach the evidence; the plan's central-claim evidence paragraph, C3 line, MATH4AI tiers and F3' still carry claims the project has withdrawn. | Rescope F4' (H), supersede F3', update plan/state (I.2). **[writing-only]** |
| D4 Argument coherence | 4 → **4** | The arc from context → reconstruction → P4 is clear and P4 matches the plan's H1/H2/C1; the commit message says "plan/state aligned" while the plan's central claim contradicts F4'. | n/a |
| D5 Exploration integrity | 4 → **4** | The sanity redefinition, the filtered-count bug and the "0r is withheld" objection are all logged; the linear-t deviation from the registered 0r appears only in a code comment. | n/a |
| D6 Methodological rigor | 3 → **3** | Size-k resampling, n/k scaling, per-k sanity rows, 20-draw sweeps and direction splits are real gains; the key comparison uses different supports, a misspecified reference, B = 50 percentiles and (table, draw) CIs that treat 20 draws over the same 6 tables as 120 independent clusters, and `range_check.py` still runs a different 0d. | I.1 plus: table-clustered CIs for the k-curve; port `range_check.py` to `zeroparam.py` and re-run F2'. **[CPU-only]** |

Mean 21/6 = **3.5**, Weak Accept (mean < 3.8, no dimension < 2).

**Has the CPU-only ceiling been reached? No.** Round 3 put it at about 4 on every dimension for a
zero-parameter ceilings report. D2, D4 and D5 are there. D1, D3 and D6 are not, and every item holding
them at 3 is CPU-only or writing-only:

- **D1 → 4 [CPU-only]:** an information reference that is valid for all templates (oracle sampling
  distribution of the k-row statistic, I.1), compared with 0d on common support with a paired CI; T0_agent
  re-combined and passing sanity.
- **D3 → 4 [writing-only]:** F4' rewritten as in H; F3' superseded with n = 2 unique pairs; plan
  central-claim evidence, C3 line and MATH4AI line updated; `research-state.yaml` T0_agent number removed;
  headroom labelled descriptive with n = 8 / n = 2; floor value and linear-t deviation disclosed.
- **D6 → 4 [CPU-only]:** common-support evaluation, table-level (6-cluster) or task-level CIs on the
  k-curve alongside the (table, draw) CIs, a B = 500 sensitivity at k ∈ {5, 20}, a floor sensitivity, and
  `range_check.py` on `zeroparam.py`.

Round-3's caveat still applies: judged by the paper's own contributions (H1, H2-for-7, C3, C2 on P3
pairs), D1 and D6 stay at 3 until P4 runs.

## H. F4': is "information, not estimator" warranted?

**No, not yet.** The registered test cannot be decided: the reference is withheld, misspecified for 71%
of tasks (150/210 filtered or grouped), uses a different functional form than registered, and is scored
on a different support than 0d.

**Strongest alternative reading.** At k ≤ 20, 0d and 0r are weak for *different, estimator-specific*
reasons, and their agreement within 0.05 is a coincidence of two biases:
- 0d: percentile bootstrap undercoverage at small k with B = 50 (35% clean FP vs nominal 5%), near
  identity with the range check for median/max at k = 5, filtered tasks dropped when the filter value is
  absent, unsigned linear distances.
- 0r: unfiltered reference for filtered/grouped queries, linear t against log-symmetric poisons, the
  range check for counts, one-sided for max.

Under this reading the information available in k rows is unknown, and the bar for C3 at k = 5 could be
well above 0.62. The by-op data (mean/median agree at k5) is the best evidence against this reading, but
it pools templates where 0r is misspecified.

**The test that separates the two readings [CPU-only].** For each task and k, draw M = 1,000 k-row subsets
from the *full* table and compute the statistic (with the same n/k scaling and the same "filter absent →
undefined" rule). This is the true sampling distribution of the k-row estimate. Score y by its signed
log-ratio distance from the distribution's median, standardized by its IQR (or by the likelihood ratio of
clean vs poisoned under it). Call this **0o**. It is an upper bound on what any checker using that
statistic and k rows can do, because it knows the population sampling variability that a real checker has
to estimate. Then:
- 0d ≈ 0o on common support → the small-k limit is information; F4' stands.
- 0o ≫ 0d → F4' describes 0d's estimator, and the C3 bar at each k is the 0o curve.

Register it first (A-P3c), decide it on the paired-difference CI, and report it within-table as primary.
It replaces 0r as the reference; keep 0r only for unfiltered mean/median, in log form, as registered.

**Is the monotone k-curve a legitimate Figure 1 x-axis?** As a reference panel, yes; as the agent's
context axis, not as drawn.
- It is legitimate as "rows visible to a zero-parameter checker", with random draws, 20 per table, and it
  shows a clean dose-response (0.62 → 0.83, then 0.94 as a separate full-table reference).
- **It conflicts with the paper's threat model.** A-P3b says the checker sees only the agent's observation
  context. Agents in P4 see head-5 (T1), head-5 + min/max (T0_agent) or schema (T3). Rows 10-200 exist only
  if the agent's own observations exposed them (e.g. `print(df.head(50))`) or if the checker queries the
  tool, which A-P3b rules out. Plot agent signals only at the k they actually saw, and in P4 record the
  number of rows each agent's observations exposed before the poisoned call, so agent events can be placed
  on the same axis empirically.
- **Random rows are not head rows.** Round-2's head-5 vs random-5 gap (0.54 vs 0.59) means k5-random is not
  the T1 point. Mark the T1 point separately.
- **The support changes along the axis.** 0d's computable fraction rises from 0.79 to 0.99, so part of the
  rise is harder filtered tasks entering the denominator, which works against the trend, and the curve
  mixes "more information" with "different tasks". Plot the common-support curve (tasks computable at
  every k) as primary.

**Suggested F4' rewrite.** "0d AUROC rises monotonically with the number of randomly drawn visible rows,
from 0.62 at k = 5 to 0.83 at k = 200 (0.94 full-table reference; (table, draw) CIs ±0.015, table-level
CIs wider). Its clean false-positive rate falls from 35% to 14% against a nominal 5%. Whether the small-k
limit reflects the information in k rows or 0d's estimator is undecided: the registered reference (0r) fails
its sanity row and is misspecified for filtered and grouped queries; an oracle sampling-distribution
reference is registered in A-P3c. T0_agent (head-5 + whole-column min/max) is withheld pending a fixed
combination rule."

## I. Verdict and next actions

**GO-WITH-CHANGES.** The process trail is again clean, and A-P4 is close to runnable. Do not let F4''s
"information" sentence become the bar that P4's learned scorer is judged against until 0o exists.

1. **Settle information vs estimator [CPU-only, about half a day].** Commit A-P3c first, then:
   (a) the 0o oracle sampling-distribution reference with signed log-ratio scoring;
   (b) 0r in the registered log form, restricted to unfiltered mean/median;
   (c) all comparisons on common support, within-table primary, with a CI on the paired 0d − 0o difference
       and table-level clustering;
   (d) T0_agent recombined from standardized components and re-sanity-checked;
   (e) B = 500 and floor {0, 0.1%, 1%} sensitivity at k ∈ {5, 20};
   (f) `range_check.py` ported to `zeroparam.py` and F2' re-run.
2. **Writing pass [writing-only].** Rewrite F4' per H. Mark F3' superseded and correct n = 43 → 2 unique
   pairs. Update the plan's central-claim evidence paragraph, C3 line and MATH4AI tiers, and
   `research-state.yaml`. Label the headroom control descriptive (P3 n = 8, ToxicBench n = 2). Disclose the
   1% floor and the three code-level clarifications as a dated deviation note. In A-P4: label H2(0d)
   "pre-decided by ceiling"; define negatives for C3 slice (a); name the clustering unit for every decision;
   commit the sum-type rule for 0d on agent code; mark the P4 temperature line superseded; say whether H2
   needs both signals.
3. **Run P4 [needs agent runs].** API agents first (gpt-5.4-mini + hosted Qwen3-4B) at T1, then T0_agent and
   T3, GPU last. In the harness, log the rows each agent's observations exposed before the poisoned call, and
   check on the first 210 × 3 trajectories that the poison fires and equals the oracle poisoned value.

**Strongest part:** the self-correction loop. Every amendment precedes its results, withheld cells and the
0r caveat are written down rather than hidden, and the k-sweep turned a three-point story into a dose-response
curve in one round.

**Single most important improvement:** replace 0r with a reference that is valid for every template (0o) and
decide the information-vs-estimator question on common support with a CI. That decision sets the bar for C3,
which is the paper's main learned contribution.

## Sources
- `docs/REVIEW_2026-10-31_{pilot,rescore,round3}.md` — accessed 2026-10-31
- `PREREGISTRATION.md` (P4, A-P3b, A-P4), `findings.md` (F3', F4', Disclosures), `research-log.md`, `research-state.yaml`, `program.md`, `.git/logs/HEAD` — accessed 2026-10-31
- `experiments/{zeroparam.py, ksweep.py}`, `experiments/results/ksweep.log`, `experiments/results/taxonomy/summary.json` — accessed 2026-10-31
- `data/ours/ksweep/{summary.json, events.jsonl}` — accessed 2026-10-31
- private planning notes (not included in this repository)
- `/tmp/AI-research-SKILLs/22-agent-native-research-artifact/rigor-reviewer/SKILL.md`, `/tmp/academic-research-skills/deep-research/agents/devils_advocate_agent.md` — accessed 2026-10-31
