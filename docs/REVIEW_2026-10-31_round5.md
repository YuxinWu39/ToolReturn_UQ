# Round-5 review: A-P3c execution, F4'', and the CPU-only ceiling

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's advocate (checkpoint 2). Date: 2026-10-31.
Prior reviews: pilot 2.67 → rescore 3.5 → round-3 3.33 → round-4 3.5 (D1 3, D2 4, D3 3, D4 4, D5 4, D6 3).

**Method note.** This session again had no shell. I could not run `git -P log` or the venv Python, so no
AUROC below was recomputed by ranking. What I did instead:
- Commit order from `.git/logs/HEAD` (epoch seconds; 2026-11-01 00:00 UTC = 1793491200) and file mtimes.
- Raw rows of `data/ours/ksweep2/events.jsonl` read with anchored regexes (k = 5, draw 0, unfiltered
  mean/median; one task across draws 0-2; grouped clean rows).
- AUROCs, CIs and template/direction splits read from `summary.json` and `ksweep2.log`.
- Code read line by line: `zeroparam.py`, `ksweep2.py`, `range_check.py`, `gen_tasks.template_code`.
- `is_sum_type` and `FastTemplate` traced by hand on example inputs.

Each number says how it was obtained.

## Verdict

**GO-WITH-CHANGES. The CPU-only ceiling has not been reached.** New mean **3.17** (3, 3, 3, 3, 4, 3).

The round executed almost everything round 4 asked for, and the process trail is clean (protocol 1605390
at 01:55 UTC, results e1eefc0 at 03:21 UTC). The new score is lower than round 4 for one reason, and the
reason is partly mine: **the 0o reference that round 4 proposed and A-P3c registered does not measure the
information in k rows.** `oracle_0o` is computed once per (task, k), outside the draw loop, from the full
table. It never looks at the visible rows. It centres on the median of the k-row statistic's population
sampling distribution, which for unbiased statistics is the true answer. On the unfiltered mean/median
rows I could read, 0o separates clean from poisoned perfectly, while the analytic t-test that sees the
same five rows (0r_log) scores 0.70. So the 0.17 gap between 0o and 0d is mostly "knowing the answer's
centre", not "0d's estimator". Under this design, A-P3c's "information" outcome could fire only if 0d were
almost perfect, so the registered test could not have returned "information" in practice.

F4'' therefore draws the wrong conclusion from a correctly applied rule: "the gap is estimator, not
information", "information ceiling 0.79", "~0.17 of headroom to recover without seeing more rows", and
"the C3 bar is the 0o curve" are all unsupported. The fix is CPU-only and small (an oracle that conditions
on the observed draw, section H). Separately, the sum-type rule that A-P3c says "also binds P4"
misclassifies the P3 grouped template itself, and F3' was not marked superseded although the log says it
was.

## A. Did round-4 actions 1 and 2 land?

| Round-4 item | Status | Evidence |
|---|---|---|
| 1a 0o oracle reference | ✅ implemented as registered; ❌ invalid as an information bound | `oracle_0o` draws M = 300 k-subsets of the full table, once per (task, k). See a, b |
| 1b 0r in log form, unfiltered mean/median only | ✅ | `reference_0r_log` returns None for filtered/grouped and for ops other than mean/median |
| 1c common support, within-table primary, paired CI, table clustering | ✅ | `paired_ci_tables` (6 tables), `paired_ci_table_draw`; 164-task curve computed |
| 1d T0_agent recombined + sanity | ✅ passes (0.966) but still below its 0a component | see d |
| 1e B = 500 and floor sensitivity | ✅ null effect | k5: 0.622 → 0.620 (B), floor ≤ 0.0003; clean FP 35.5% → 33.3% |
| 1f `range_check.py` on `zeroparam.py` | ⚠️ partial | imports `bootstrap_0d`, `is_sum_type`; keeps its own `interval_score` (no floor) and `rule_scores` (own 0a) |
| 2 F4' rewrite | ✅ F4' marked superseded | but F4'' overreaches (H) |
| 2 F3' superseded, n = 43 → 2 | ❌ **not done in findings** | F3' header has no marker and still says "Range width … is the mechanism … n = 43". research-log says "F3' superseded (n=2 pairs)". The original F4 header ("every zero-parameter method is near chance") is also unmarked |
| 2 plan/state | ⚠️ | central-claim paragraph fixed; new overclaim added (e); C3 line, MATH4AI "all 5 tiers", Figure 1 "T0-T4" and `research-state.yaml` evidence_gaps still stale |
| 2 deviation note | ✅ | A-P3c logs the three A-P3b clarifications |
| 2 A-P4 fixes | ✅ mostly | H2(0d) pre-decided, slice (a) negatives, clustering, temperature, LOTO. Two contradictions remain (e) |

## Spot-checks

### a. Common-support AUROCs, the decision rule, and where 0o's advantage comes from

| Quantity | Value | How |
|---|---|---|
| Common support at k5 / k200 | 0.750 / 0.985 | `summary.json` |
| 0d / 0o pooled, common support, k5 | 0.622 / 0.790 | `summary.json`, not recomputed |
| 0d / 0o pooled, common support, k200 | 0.825 / 0.958 | `summary.json`, not recomputed |
| 0o − 0d, mean over tables, k5 | +0.173, table CI [+0.156, +0.190] | `summary.json` |
| Lower table CI at k5 / 10 / 20 | 0.156 / 0.150 / 0.159 | all > 0.05 |

**Was the A-P3c rule applied correctly? Yes, mechanically.** `decide()` uses the table-level CI, the
threshold is 0.05, and all three registered k values clear it. The rule ran as written. The problem is what
it was applied to (b).

**Is the advantage uniform?** By template at k5 (common support, pooled, from `summary.json`):

| Template | 0o | 0d | 0o − 0d |
|---|---|---|---|
| unfiltered | 0.878 | 0.660 | +0.218 |
| filtered | 0.828 | 0.566 | +0.262 |
| grouped | 0.685 | 0.620 | **+0.065** |

By direction: up +0.156, down +0.184. The gap comes from unfiltered and filtered queries. On grouped
queries it is barely above the 0.05 threshold, because 0o itself is weak there (below). `summary.json` has
no op split for 0o, so I could not check ops. The table-level CI is narrow (±0.017 around 0.173), which
implies all six tables sit near the mean, but a percentile bootstrap over 6 values understates the
uncertainty. With a gap of 0.17 that does not matter here.

**Why grouped is the exception (verified from rows).** At k5, grouped clean rows have large 0o scores:
`lt_penguins_v3_gro_026` (sum) 0o_signed −1.33, `gro_030` (sum) −1.43, `lt_auto_mpg_v4_gro_027` (max)
+1.52. The top-group statistic on 5 rows is biased (winner's curse for scaled sums, under-estimate for
max), and 0o centres on the biased median, so it penalises the clean answer. 0o's k-dependence therefore
comes mostly from estimator bias in biased ops, not from information.

### b. Is 0o a fair upper bound? Comparison with 0r_log

**0o does not depend on the visible rows.** In `ksweep2.py`, `dist = oracle_0o(fast, k, ...)` is computed
before the `for d in range(args.draws)` loop. The rows confirm it: `lt_penguins_v3_unf_001` at k5 has
0o = 0.0885 (clean) and 3.4757 (poisoned) in draws 0, 1 and 2, while 0r_log changes (0.077, 0.216, 1.287
for clean). 0o is a population oracle with a k-dependent tolerance. It is not "what k rows can tell you".

**On unfiltered mean/median, 0o is near perfect and the analytic route does not reach it.** From the k5,
draw-0 rows I could read (15 of the 34 unfiltered mean/median tasks; penguins, auto-mpg, bike):
- 0o clean scores: 0.009-0.135. 0o poisoned scores: 0.21-8.85. **Every poisoned score exceeds every clean
  score, so 0o's AUROC on these 15 tasks is 1.00** (hand count over 225 pairs; 0o is constant across draws).
- 0r_log on the same template, all 34 tasks, all draws: **0.701** (`summary.json`). On the same draw-0 rows,
  clean 0r_log reaches 2.32 (bike) and poisoned 0r_log drops to 0.29-0.49, so the two classes overlap.

0r_log is a real checker: it centres on the mean of the five visible rows. 0o centres on the population
answer. The roughly 0.3 AUROC between them on the simplest queries is the value of knowing the centre,
which no checker limited to k rows can have. **So the "estimator" loss is not specific to the bootstrap,
and the analytic route does not recover it.** On these tasks the real estimator loss is 0r_log − 0d. I
could not compute it because 0d is not reported on that subset. The unfiltered 0d over all ops is 0.660,
which suggests a few points, not 0.17.

**What the round-4 proposal got wrong.** Round 4 asked for "signed log-ratio distance from the
distribution's median". That centres the test on the population quantity. The bound needed for "information
in k rows" keeps the oracle's knowledge of the *shape* of the sampling law (spread and bias) and takes the
*centre* from the observed draw. Section H gives the construction. A-P3c's statement "0o is an upper bound
on any checker that uses that statistic and k rows" is true in a trivial sense, but it is far from tight,
so the gap to 0o measures oracle knowledge, not estimator quality.

### c. `FastTemplate.on_subset` vs `template_stat`, and `is_sum_type`

| Rule | `template_stat` (0d) | `FastTemplate` (0o) | Match? |
|---|---|---|---|
| Filtered, non-count, filter value absent | None | None | ✅ |
| **Filtered count, filter value absent** | `float(len(sub))` = **0.0** (the count branch runs before the empty check) | **None** | ❌ 0d treats it as defined, 0o as undefined. This changes the common support only, not scores on it |
| Unfiltered count | k × n/k = n | k × n/k = n | ✅ |
| Sum / count scaling | ×n/k after `max` (in `bootstrap_0d`) | ×n/k inside each group | ✅ equivalent (positive factor) |
| **Grouped count** | `_agg` counts non-null values of the column | `len(sel)` counts rows | ❌ when the column has NaN (penguins, auto-mpg `horsepower`) |
| **Grouped NaN keys** | pandas `groupby` drops NaN keys | `factorize(astype(str))` makes `"nan"` a group | ❌ when the group column has NaN (penguins `sex`: 11 rows) |
| Grouped top group | max over groups | max over groups | ✅ |

The mismatches are edge cases and probably move few rows. They still mean "same rules as 0d" (A-P3c) is not
exactly true. Unit-test both functions on the same subsets. [CPU-only]

**`is_sum_type`, traced by hand:**

| Code | Result | Correct? |
|---|---|---|
| `len(df[df['species'] == 'Adelie'])` (filtered count) | True (`len`) | ✅ |
| `df[df['species'] == 'Adelie']['bill_length_mm'].count()` | True (`count`) | ✅ |
| `round(df['x'].mean(), 2)` | False (`round` wrapper → `mean`) | ✅ |
| **`df.groupby('g')['x'].sum().max()`, the P3 grouped template** (`gen_tasks.template_code`) | **False** (final call `max`) | ❌ grouped sums and counts are sum-type |
| `df['x'].sum().round(2)` | False (method-form `round`: the code takes `args[0]` = the constant 2) | ❌ |
| `total = df['x'].sum()` then `print(total)` | False (`print` wrapper → a Name, loop exits) | ❌ common agent pattern |
| `df.shape[0]` | False (Subscript, not Call) | ❌ |

The three cases the protocol names work. The rule fails on the P3 grouped template, which is exactly what
P4 agents will be asked to compute. A-P3c says this rule "also binds P4". As written, 0d on agent code at
T1 would leave every grouped sum/count unscaled, giving intervals near k/n of the true value and flagging
every clean event. `ksweep2.py` is unaffected because it uses `op`. `range_check.py` (F2'' head-5) is
affected for grouped sums in ToxicBench code, by an unmeasured amount. Fix before P4: treat
`groupby(...).{sum,count,size}().{max,idxmax,…}` as sum-type, look through method-form wrappers via
`func.value`, resolve a final `print(name)` to the expression assigned to `name`, and add `shape[0]`.
Commit the unit tests with the rule. [CPU-only]

### d. T0_agent

- Values (`summary.json`): recombined **0.551**, 0a on whole-column [min, max] **0.567**, 0d on head-5
  **0.549**. Sanity s_hi = s_lo = 0.966 (pass).
- **Two columns?** A-P3c requires two columns only if the sanity row fails. It passed, so one number was
  allowed. F4'' chooses two columns anyway because the combination is below its component, which is the
  right call. But it prints only the 0a component (0.57) and the combined 0.55, not the 0d head-5 column
  (0.549). Print both components and drop the combined number from the headline. [writing-only]
- **Is the standardization sound?** It is defensible but fragile. A max of components each divided by its
  clean 95th percentile behaves almost lexicographically when one component is zero on most clean rows:
  0a ranks first wherever it fires, and 0d orders the rest. The combined score falls below 0a because 0d at
  head-5 is at or below chance on the rows where 0a does not fire (0.567 = 0.5 + 0.5h for hit rate
  h ≈ 0.13; the combined 0.551 implies head-5 0d ≈ 0.48 on the residual). That is a data property, so the
  combination is not broken this time. A cleaner OR is a flag rule at a matched false-positive rate
  (fires if c0a > 0 or c0d > q95), reported as TPR at FPR 5%.
- **Side finding: 0a's sum bound is misspecified for filtered and grouped sums.** `rule_0a` uses
  n·[min, max] for every sum. A filtered or top-group sum over m < n rows is about m·mean, which falls below
  n·min whenever m/n < min/mean (penguins body mass: min/mean ≈ 0.64; Adelie is 44% of rows). Rows confirm
  clean false positives at k5: grouped-sum clean 0a = 1.19, 0.44, 0.75, 0.08 in the four rows I read. At
  T0_agent these clean outliers are the likely cause of the sanity AUROC being 0.966 and not 1.0, with
  identical s_hi and s_lo values (inferred, not verified). The bound should be
  [n·min(min, 0), n·max(max, 0)]. This lowers 0a in F3', the k-sweep and T0_agent by an unknown amount.
  G2 stays pre-decided by the hit-rate bound. [CPU-only]

### e. Findings, plan and state

| Check | Status |
|---|---|
| F4' superseded marker | ✅ |
| **F3' superseded marker** | ❌ absent; F3' still says "Range width relative to the aggregate is the mechanism" with n = 43. The original F4 (near chance, "first direct evidence for the central claim") is also unmarked. research-log row 5 claims F3' was superseded |
| F4'' states common-support fractions | ✅ 75% at k5, 98% at k200 |
| F4'' states the 164-task curve | ⚠️ it names "164 tasks computable at every k" but prints the per-k common-support table, not the 164-task curve (0d 0.62/0.66/0.70/0.76/0.81/0.85; 0o 0.79/0.83/0.87/0.91/0.94/0.96, from `summary.json`). A-P3c names that curve primary. The curve has pooled AUROC only, no within-table values or CI |
| Headroom labelled descriptive with n = 8 / n = 2 | ✅ in Disclosures |
| Plan no longer says "confirms range width is the mechanism" | ✅ |
| Plan no longer says "every zero-parameter method is near chance" | ✅ |
| **New overclaim in the plan** | ❌ "the gap between 0d and 0o is the room a context-aware checker could recover" (b shows it is not) |
| **Plan central claim vs F4''** | ❌ "depends less on which uncertainty signal is used than on whether the checker can reconstruct…" while F4'' says two zero-parameter signals with identical rows differ by 0.17 because of the estimator. Both cannot stand; after the fix in H, the true estimator gap is probably small and the central claim survives |
| **C3 bar defined twice** | ❌ A-P4: parity on slice (b) means \|AUROC_7 − AUROC_0d\| < 0.05. Plan and F4'': "the C3 bar is the 0o curve". These are different tests |
| Stale lines | Plan C3 "58% … 0d scores 41.8%" (F2'' now 55% / 44.6%); MATH4AI "all 5 tiers"; Figure 1 "T0-T4"; `research-state.yaml` evidence_gaps "41.8% … 58%"; A-P4 "0d on agent code: … no op classifier needed" (superseded by the sum-type rule, not marked); A-P4 fixes "T0_agent 0d ~0.53" (now 0.549) |

### f. Git order and unlogged changes

| Event | UTC | Source |
|---|---|---|
| A-P3c protocol `1605390` | 01:55:15 | `.git/logs/HEAD` |
| `PREREGISTRATION.md`, `zeroparam.py` mtime | 01:55 | ls |
| `ksweep2_smoke.log` | 02:00 | ls |
| `ksweep2.py`, `range_check.py` mtime | **02:01** | ls |
| `ksweep2.log` | 02:16 | ls |
| `research-log.md`, `research-state.yaml` | 02:45 | ls |
| `range_check.log` | 03:18 | ls |
| `findings.md`; results `e1eefc0` | 03:21 | ls, `.git/logs/HEAD` |

- The protocol precedes the results ✅, and `PREREGISTRATION.md` was not edited after the protocol commit ✅.
- **`ksweep2.py` was edited after the smoke run produced output.** The smoke log shows T0_agent sanity
  `{'s_hi': None, 's_lo': None}`. The final code has a `# re-slice after the combined column exists` fix,
  and the final log shows 0.966. The smoke log also showed the "estimator" decision before the full run.
  The fix looks like a genuine bug fix that does not touch the decision path, but it is a post-protocol code
  change made after seeing output, and it is not logged. The smoke parameters (166 vs 164 always-computable
  tasks, k5 gap 0.118 vs 0.173) are not recorded either. [writing-only]
- **The `range_check.py` re-run (F2'') has no research-log entry.** The log was last written at 02:45; the
  range-check run finished at 03:18. F2'' also reports head-5 0.81 while saying head-5 is "withheld as a
  headline, reported in the table", which repeats the round-4 pattern of quoting a withheld cell.
  [writing-only]
- I cannot tell from mtimes whether the A-P3c functions in `zeroparam.py` were part of commit 1605390.
  Run `git -P show --stat 1605390` to settle it.

## G. Re-scored dimensions

| Dim | Round 4 → now | One sentence | Blocking item if < 4 |
|---|---|---|---|
| D1 Evidence relevance | 3 → **3** | The 0d k-curve, the common support, the null B/floor sensitivities and the T0_agent components are solid; the round's headline (estimator, 0.79 information ceiling, 0.17 recoverable) rests on a reference that never sees the visible rows and scores 1.00 where a real five-row checker scores 0.70. | Draw-conditioned oracle 0o* and the 0d / 0r_log / 0o* comparison on unfiltered mean/median (H). **[CPU-only]** |
| D2 Falsifiability | 4 → **3** | A-P4's per-decision statistics are good, but the round's main registered test could not return "information" under this 0o, and the C3 bar now has two incompatible definitions (A-P4 parity vs "the 0o curve"). | Re-register the information test against 0o* and give C3 one bar per slice in the protocol. **[writing-only]** |
| D3 Scope calibration | 3 → **3** | F4'''s title, its "information ceiling" label, the "~0.17 headroom" sentence and the plan's "room a context-aware checker could recover" overreach; F3' and F4 still carry withdrawn claims. | Rewrite F4'' per H, mark F3'/F4 superseded, fix the stale plan/state/A-P4 lines. **[writing-only]** |
| D4 Argument coherence | 4 → **3** | The plan's central claim (the signal matters less than reconstruction) and its new evidence paragraph (two zero-parameter signals with the same rows differ by 0.17) contradict each other, and the plan and A-P4 define the C3 bar differently. | Reconcile once 0o* exists: one central-claim sentence and one C3 bar. **[writing-only]**, after the CPU item in D1 |
| D5 Exploration integrity | 4 → **4** | F4' was withdrawn openly and the three A-P3b deviations are now logged; the post-smoke code fix and the F2'' re-run are unlogged, and the log says F3' was superseded when it was not. | n/a (fix in I.2) |
| D6 Methodological rigor | 3 → **3** | Common support, table-level paired CIs, B/floor sensitivities and the shared bootstrap are real gains; the reference is invalid as an information bound, 0o and 0r_log have no sanity rows (program.md hard rule), the sum-type rule fails on the P3 grouped template, 0a's sum bound is wrong for filtered/grouped sums, and `FastTemplate` and `template_stat` disagree on three edge rules. | 0o* + sanity rows for 0o/0o*/0r_log + `is_sum_type` fix with tests + 0a sum bound + `FastTemplate` alignment, then re-run `ksweep2.py` and `range_check.py`. **[CPU-only]** |

Mean 19/6 = **3.17**, Weak Accept (mean ≥ 3.0, no dimension < 2).

**Is the CPU-only ceiling reached? No.** For a zero-parameter-ceilings pilot report, D1, D3 and D6 are not
at 4, and D2 and D4 dropped back to 3 this round. Every item holding a dimension below 4 is CPU-only or
writing-only:
- **CPU-only (D1, D6, and D4 indirectly):** 0o* (H); 0d, 0r_log and 0o* on the same unfiltered mean/median
  subset, to split the 0o − 0d gap into estimator loss and oracle knowledge; sanity rows for every reported
  reference; `is_sum_type` fix with unit tests; 0a sum bound; `FastTemplate` / `template_stat` alignment;
  re-run the k-sweep and `range_check.py` head-5.
- **Writing-only (D2, D3, D4, D5):** F4'' rewrite; F3'/F4 superseded markers; 164-task curve printed as
  primary; a single C3 bar per slice in A-P4; central-claim sentence reconciled; stale plan/state/A-P4
  lines; log entries for the smoke run, the post-smoke fix and the F2'' run.

Round 3's caveat still holds: judged against the paper's own contributions (H1, H2 for signal 7, C3, C2 on
P3 pairs), D1 and D6 stay at 3 until P4 runs.

## H. F4'': what is the right bar for C3?

**"The C3 bar is the 0o curve" is too strict.** 0o knows the population answer up to the k-row statistic's
bias. For unbiased statistics it is essentially perfect at every k (1.00 on the 15 unfiltered mean/median
tasks I read), so its shortfall from 1.0 measures bias in biased ops (grouped top group, max), not
information. No checker limited to the agent's observation context can reach it. A learned scorer judged
against it would fail by construction, and "fraction of the 0o gap closed" would be small for any method.

**"0d" alone as the bar is too lax.** 0r_log reaches 0.70 on unfiltered mean/median at k5 with the same
rows, so 0d's percentile bootstrap is beatable on at least that slice. Beating 0d does not show that a
learned signal extracted anything a simple analytic test would miss.

**The bar that matches the threat model: a draw-conditioned oracle, 0o\*.** Keep the oracle's knowledge
of the *shape* of the k-row sampling law and take the *centre* from the observed rows:

1. From the M full-table k-subsets already drawn, record the log ratio r = log(θ̂_k / θ) between the
   k-row statistic and the full-table value θ. Its median b_k is the bias and its IQR w_k is the spread.
2. For a candidate y and the observed draw's statistic θ̂_k(draw), score
   |log θ̂_k(draw) − log y − b_k| / w_k, i.e. how implausible the observed rows are if y were the truth.
   For non-positive values use the linear analogue, or an exact likelihood under the empirical law of r.
3. Same undefined and scaling rules as 0d (after the c fixes), same common support, sanity rows,
   table-level paired CIs.

0o\* upper-bounds any checker that uses this statistic on these k rows and knows the sampling law
exactly. It varies by draw, and it is achievable in the limit by a checker with a good prior on the
column's distribution, which is what a learned scorer trained on clean returns could plausibly learn.
Expected order: 0d ≤ 0r_log ≤ 0o\* ≪ 0o on unfiltered mean/median. Register the decomposition (estimator
loss = 0o\* − 0d; oracle knowledge = 0o − 0o\*) and the same ±0.05 CI rule against 0o\* in an A-P3d before
running it. Keep 0o in the figure as a labelled "population oracle, not achievable" line, or drop it.

**What P4 should report as the bar for signal 7 at k = 5 (scalar slice b):**
- Primary: AUROC_7 − max(AUROC_0d, AUROC_0r_log where defined), on the common support, within-table,
  lower table-clustered 95% CI > 0. This is "beats the best zero-parameter check with the same rows".
- Secondary: the fraction of the 0o\* − 0d gap that signal 7 closes, with a CI. If 0o\* − 0d is under
  0.05, say there is no headroom on slice (b) and drop the parity test's "expected" framing.
- Slice (a) (multi-number): no zero-parameter reference exists; keep A-P4's absolute bar (lower CI > 0.70,
  ≥ 100 events).
- k = 5 random rows is not T1. At T1 the references must be computed on head-5 (0d head-5 0.549, and
  0o\* using the head rows as the "draw", with a note that head rows are not a random sample, so the
  oracle shape is approximate). Use the k-sweep only to place agents whose observations exposed k random-ish
  rows.

**Suggested F4'' rewrite.** "On the common support, 0d rises from 0.62 (k = 5) to 0.82 (k = 200),
within-table. A population oracle that knows each statistic's k-row sampling distribution around the
true value (0o) scores 0.79 to 0.96. It does not use the visible rows and separates unfiltered means
perfectly, while an analytic t-test on the same five rows scores 0.70. So the 0o − 0d gap measures
knowledge of the answer, not only 0d's estimator. The pre-registered A-P3c rule returns 'estimator', but the
registered reference cannot distinguish the two readings. A draw-conditioned oracle (0o\*) is registered in
A-P3d to split the gap into estimator loss and information loss. B and the interval floor do not affect 0d.
T0_agent: whole-column min/max 0.57, head-5 bootstrap 0.55; their combination adds nothing."

## I. Verdict and next actions

**GO-WITH-CHANGES.** The artifact keeps improving on process, and the k-curve for 0d is now a well-supported
descriptive result. Do not let "C3 bar = 0o curve" or "0.17 recoverable" reach P4's protocol or the paper.

1. **Fix the reference and the sum-type rule [CPU-only, about half a day].** Commit A-P3d first, then:
   (a) 0o\* as in H, with sanity rows for 0o, 0o\* and 0r_log;
   (b) 0d, 0r_log, 0o\* and 0o side by side on unfiltered mean/median, and the gap decomposition with
       table-level CIs, by template and by op;
   (c) `is_sum_type` handles grouped `…sum().max()`, method-form wrappers, `print(var)` after assignment
       and `shape[0]`, with committed unit tests;
   (d) 0a sum bound [n·min(min, 0), n·max(max, 0)] for filtered and grouped sums;
   (e) `FastTemplate` aligned with `template_stat` on filtered count, grouped count and NaN keys, with a
       test that both return the same value on 1,000 random subsets per task;
   (f) re-run `ksweep2.py` and `range_check.py` (head-5).
2. **Writing pass [writing-only].** Rewrite F4'' per H and print the 164-task curve as primary. Mark F3' and
   F4 superseded and correct n = 43 → 2 unique pairs in F3'. Give C3 one bar per slice in A-P4 and remove
   "the C3 bar is the 0o curve" from the plan, state and findings. Reconcile the central-claim sentence with
   the decomposition. Mark A-P4's "no op classifier needed" superseded and update "T0_agent 0d ~0.53".
   Update the plan C3 line (55% / 44.6%), MATH4AI tiers and Figure 1 axis. Add log entries for the smoke
   run, the post-smoke T0_agent fix and the F2'' run, and drop the head-5 F2'' number from the headline.
3. **Run P4 [needs agent runs].** API agents first (gpt-5.4-mini + hosted Qwen3-4B) at T1, then T0_agent
   and T3, GPU last. Use the fixed sum-type rule from day one. Log the rows each agent's observations
   exposed before the poisoned call, and check on the first 210 × 3 trajectories that the poison fires and
   equals the oracle poisoned value.

**Strongest part:** the pre-registration discipline under pressure. The agent registered a decision rule,
ran it, and withdrew its own previous headline (F4') when the rule went against it. That is the behaviour
reviewers trust.

**Single most important improvement:** replace 0o with a draw-conditioned oracle before any C3 bar is set.
As it stands, the bar measures knowledge of the answer, and the learned scorer would be judged against a
target no observation-limited checker can reach.

## Sources
- `docs/REVIEW_2026-10-31_round4.md` (and pilot, rescore, round3) — accessed 2026-10-31
- `PREREGISTRATION.md` (A-P4, A-P3c, A-P4 fixes) — accessed 2026-10-31
- `experiments/zeroparam.py`, `ksweep2.py`, `range_check.py`, `gen_tasks.py` (`template_code`) — accessed 2026-10-31
- `data/ours/ksweep2/summary.json`, `events.jsonl` (regex row reads) — accessed 2026-10-31
- `experiments/results/ksweep2.log`, `ksweep2_smoke.log`, `range_check/summary.json` — accessed 2026-10-31
- `findings.md` (F2'', F3', F4, F4', F4'', Disclosures), `research-log.md`, `research-state.yaml`, `.git/logs/HEAD` — accessed 2026-10-31
- private planning notes (not included in this repository)
- `/tmp/AI-research-SKILLs/22-agent-native-research-artifact/rigor-reviewer/SKILL.md`, `/tmp/academic-research-skills/deep-research/agents/devils_advocate_agent.md` — accessed 2026-10-31
