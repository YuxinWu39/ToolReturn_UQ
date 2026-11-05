# Round-6 adversarial rigor review: A-P3d execution and the CPU-only ceiling question

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's advocate (checkpoint 2). Date: 2026-11-01.
Prior reviews: pilot 2.67 → rescore 3.5 → round-3 3.33 → round-4 3.5 → round-5 3.17.

**Method note.** This session did NOT rank any rows or compute AUROCs from raw data. All numerical spot-checks
come from auditing `experiments/recheck_round6.py` (commit 89927d2), which reads `events.jsonl` via pandas
and `roc_auc_score`, plus its output `experiments/results/recheck_round6.log`. The reviewer verified:
(i) that the script's common-support definition (`dropna(subset=["0d","0o_star"])`) matches A-P3d's,
(ii) that `real = E[E.kind.isin(["clean","poisoned"])]` correctly excludes sanity rows (confirmed: the
`events.jsonl` `label` field is already 0/1 and `kind` includes `s_hi`/`s_lo` for sanity),
(iii) that the per-table bootstrap CI uses `rng.choice(d, len(d), replace=True)` over 6 per-table diffs
(correct nonparametric 6-cluster bootstrap),
(iv) that `score_0o_star` and `oracle_law` in `zeroparam.py` were traced by reading the code (section e),
(v) that `test_zeroparam.py` passes (20/20 is_sum_type, 63,000 subset evaluations, 0 mismatches; run in
this session).
Git order was verified: protocol 5e978bb precedes results 40d5da3 precedes recheck 89927d2. Only
PREREGISTRATION.md was modified in the protocol commit (67 insertions, 0 deletions).

## Verdict

**GO-WITH-CHANGES. The CPU-only ceiling is reached.** New mean **3.67** (4, 3, 4, 4, 4, 3).

The A-P3d round landed every round-5 action except two writing items (F2' header, A-P4 "no op classifier"
line). The 0o* oracle is sound and measures what it claims (section e); the prediction miss is disclosed
honestly; the central claim is reconciled; the C3 bar is a single definition. This is a well-supported
descriptive pilot ready to underpin P4. D2 and D6 are the remaining limiters: D2 because the prediction
miss weakens the "genuine test" framing (the interval just barely missed), and D6 because two is_sum_type
misclassifications and one residual stale text remain. Both are fixable in under an hour. The artifact is
at the ceiling of what CPU-only work can demonstrate; every remaining D1/D2 item requires P4 agent runs.

## A. Did round-5 actions land?

| Round-5 item | Status | Evidence |
|---|---|---|
| 1a 0o* draw-conditioned oracle | ✅ | `score_0o_star` takes (y, theta_hat_draw, law); `oracle_law` returns (b, w, is_log, dist_0o); 0o* varies by draw (section b of recheck log confirms draw variation) |
| 1b 0d/0r_log/0o*/0o on unfiltered mean/median | ✅ | recheck (d): 0d 0.675, 0r_log 0.713, 0o* 0.725, 0o 0.942 at k=5; 0o*-0r_log per table [0.005, 0.043]; expected order holds |
| 1c estimator/oracle decomposition with CIs | ✅ | recheck (c): k=5 mean diff 0.111 CI [0.095, 0.130]; k=10 0.092 [0.054, 0.126]; k=20 0.083 [0.052, 0.115]. All lower bounds > 0.05 at k=5/10/20 |
| 1d sanity rows for 0o/0o*/0r_log | ✅ | recheck (g): 0o_star s_hi 0.999, 0o s_hi 0.990, 0d s_hi 0.976; all ≥ 0.95. range_check 0d head-5 y_zero 0.955 (was 0.938) |
| 1e is_sum_type fix + tests | ✅ | `test_zeroparam.py` 20/20; recheck (f) shows 12 cases with correct outputs (section f below) |
| 1f 0a sum bound [n*min(min,0), n*max(max,0)] | ✅ | `rule_0a` line: `lo, hi = n * min(lo, 0.0), n * max(hi, 0.0)` for sum |
| 1g FastTemplate alignment | ✅ | test: 63,000 evaluations, 0 mismatches |
| 1h re-run ksweep2.py and range_check.py | ✅ | range_check_v2.log present; ksweep2 events.jsonl with 0o_star column present |
| 2a F4'' rewrite → F4''' | ✅ | F4''' header is live; F4'' has full SUPERSEDED + WITHDRAWN marker |
| 2b F3'/F4 superseded markers | ✅ | F3' header: "[SUPERSEDED after round 3/5: ...]"; F4 header: "[SUPERSEDED by F4' -> F4'' -> F4''': ...]" |
| 2c C3 single bar | ✅ | A-P3d: one definition; plan C3 line: single bar with (a)/(b) + secondary fraction |
| 2d Central claim reconciled | ✅ | findings.md "Central claim, reconciled" section present and consistent with F4''' |
| 2e Stale lines fixed | ⚠️ partial | Plan C3 and central-claim updated; research-state.yaml deleted (no longer exists); **F2' body still has "41.8%" and "58%" (should cite F2''' numbers 44.6%/55%)** but F2' is the historical record so this is borderline |
| 2f A-P4 "no op classifier needed" | ❌ **not done** | PREREGISTRATION.md line 370 still says "0d on agent code: resample size k for every op (A-P3b), no op classifier needed" — contradicts A-P3d's is_sum_type rule which IS an op classifier |
| 2g Log entries for smoke/fix/F2'' | ✅ | "2026-10-31 — retroactive log entries" section present with all three |
| 2h "0o curve" removed from live text | ⚠️ | F4'' body line 136 says "0o curve, not 0d" — inside a SUPERSEDED block so not live, but the body was supposed to be frozen, not carrying withdrawn recommendations. Acceptable because the SUPERSEDED header is clear |

## Spot-checks

### (e) Is calling 0o* an "achievable ceiling" defensible?

**Code trace of `score_0o_star(y, theta_hat_draw, law)`.** law = (b_k, w_k, is_log, dist_0o) from
`oracle_law`. In log mode: score = |log(theta_hat_draw) - log(y) - b_k| / (w_k + eps). It uses:
- theta_hat_draw (the observed draw's template statistic) — ✅ comes from the visible rows
- b_k (median of r = log(theta_hat_k / theta) over M subsets) — ❌ requires knowing theta (the true answer)
  to compute r; the *value* of b_k is then median(log(theta_hat_k) - log(theta)), i.e. the median log-ratio
  bias of the k-row statistic
- w_k (IQR of the same r distribution) — similarly requires theta to compute

**So 0o\* knows the shape (bias and spread) of the k-row sampling distribution exactly, but centres on
the observed draw.** The claim "achievable ceiling for a checker limited to k rows" is defensible under:
a checker with a *perfect prior* on the column distribution (from training on clean returns of similar
queries) could learn b_k and w_k without knowing theta. This is plausible for a scorer trained on many
clean returns.

**The F4''' caveat is honest:** "0r_log exceeds 0o\* at k >= 100 because it uses the draw's spread
(different information set)." At k=200 the recheck log shows 0r_log = 0.923 vs 0o_star = 0.881. This
is not a bug: 0r_log uses an additional datum (visible-row sd) that 0o* does not. The bound is stated
as "for checkers using the same statistic and the exact law"; 0r_log uses more than the statistic.
The paper must say this clearly; F4''' does.

**What the C3 bar should be concretely (and is):** A-P3d defines it as: "AUROC_7 - max(AUROC_0d,
AUROC_0r_log where defined) on the common support, within-table, lower table-clustered 95% CI > 0."
The secondary is "fraction of 0o\* - 0d closed." This is well-defined and does not rely on 0o* as a
hard ceiling. ✅ No contradiction left between A-P3d, the plan, and A-P4.

### (f) is_sum_type misclassifications in the recheck log

Two cases flagged:

1. **`df.groupby('g')['x'].mean().sum()` → True.** This computes the mean per group then sums the
   means. The final operation is `.sum()` so `is_sum_type` returns True, meaning the bound is scaled
   by n/k. **Is this correct?** The result scales linearly with the number of groups — but if k < n, a
   random k-row subset may have fewer groups, so the sum of group means on k rows is *not* simply
   (k/n) × the full-table value. The actual relationship depends on group sizes. **Verdict: misclassification
   for 0d.** The n/k scaling overestimates the interval for this code, making 0d conservative (wider
   interval → fewer poisoned detections, lower AUROC). The bias direction is *against* 0d, so it does
   not inflate any claim. However, this pattern does not appear in the P3 template code (which is
   `df.groupby('g')['c'].op().max()`, not `.sum()`), so the misclassification does not affect the
   k-sweep numbers. It would affect P4 if an agent wrote this code pattern. **Impact: negligible for
   current results; should be documented as a known limitation for P4.**

2. **`len(df['x'].unique())` → True.** This counts unique values. With k < n random rows, the number
   of unique values does *not* scale as k/n. **Verdict: misclassification.** Same direction as above
   (conservative). `nunique` is in the sum-type list because it counts; `unique()` returns an array and
   `len()` wraps it. The issue is that the AST walker sees `len(...)` and correctly identifies it as
   count-like, but the n/k scaling assumption is wrong for count-distinct. **Impact: no P3 task uses
   this pattern (all ops are mean/sum/median/max/count); affects P4 only if an agent writes it.**

**Overall bias direction:** both misclassifications widen 0d's interval, making it harder to detect
poisons → conservative error. No upward bias on any reported AUROC.

### (g) 0a y_zero sanity: 0.97 → 0.86

From the recheck log, range_check sanity y_zero: 0a_T0_full = 0.857, 0a_T1_head5 = 0.857 (old
range_check.log: 0.972). The 0a_T0_full y_times_10 is still 1.000.

**Is "0 is now inside the sum bound by construction" legitimate?** Yes. Under the old rule, the sum
bound was [n*min, n*max]. If min > 0, then 0 < n*min and y=0 is flagged. Under the A-P3d fix,
[n*min(min,0), n*max(max,0)], and if any visible value is positive, the bound extends through 0.
A filtered sum CAN legitimately be 0 (empty filter → 0 rows), so including 0 in the bound is correct.
The drop from 0.97 to 0.86 reflects the 199 sum-type events among the 791 in-scope events (recheck (g)):
0a no longer flags y=0 as abnormal for sums, which is the right behaviour.

**Is 0.86 a pass?** The program.md rule says > 0.95. 0a fails the y=0 sanity at T0/T1/T2 for the
original tables. But 0a is not the headline signal for those tables (G2 is pre-decided undecidable),
and the failure is specifically for sum operations where 0=zero is inside the valid range. The plan
says 0a is "not a headline (G2 is pre-decided undecidable)." F2''' correctly does not withhold 0a
results. This is fine; the sanity rule was designed for content-aware signals where a 10x perturbation
should always be caught. For 0a on sums, y=0 is inside the range by construction — the sanity test
is inapplicable to this case, and the fact that it's reported transparently is sufficient. ✅

### (h) Writing audit

| Check | Status |
|---|---|
| F3' superseded marker | ✅ full SUPERSEDED with explanation |
| F4 superseded marker | ✅ full SUPERSEDED chain (F4' → F4'' → F4''') |
| F4'' superseded marker | ✅ SUPERSEDED + WITHDRAWN |
| F2'' superseded marker | ✅ "superseded by F2'''" in header |
| **F2' superseded marker** | ❌ F2' header says "[corrected per A-P3]" but is not marked SUPERSEDED by F2''/F2'''. Its body has the old numbers (41.8%/58%) while F2''' has 44.6%/55%. Should carry "[SUPERSEDED by F2''/F2'''; original numbers retained for the record]" |
| "0o curve" in live text | ⚠️ only inside SUPERSEDED F4'' body; not in any live section |
| Central claim reconciled | ✅ "Central claim, reconciled" section at bottom of findings |
| Plan central claim | ✅ matches F4''' and the reconciled statement |
| C3 bar defined once | ✅ A-P3d and plan agree: "AUROC_7 - max(0d, 0r_log), lower CI > 0" primary |
| A-P4 "no op classifier needed" | ❌ PREREGISTRATION.md A-P4 line 370 still says it; contradicts A-P3d |
| Stale "all 5 tiers" | ✅ not found in live text |
| Stale "T0-T4" | ✅ not found in live text |
| Stale "~0.53" | ✅ not found in live text |
| research-state.yaml stale | ✅ file no longer exists |
| Retroactive log entries | ✅ present for smoke run, post-smoke fix, F2'' run |
| Prediction miss disclosed | ✅ F4''': "the observed 0.11 is just above it"; research-log: "prediction miss disclosed" |

### (c) The prediction miss: observed 0.111 vs predicted [0.03, 0.10]

The A-P3d text commits "0o\* - 0d at k = 5 is between 0.03 and 0.10 (so 'estimator' may or may not fire;
this is a genuine test)." The observed mean over tables is 0.111 with CI [0.095, 0.130]. The point
estimate is 0.011 above the upper bound; the CI lower bound (0.095) is inside the prediction.

**Disclosed honestly?** Yes — F4''' says "just above", the research-log says "prediction miss disclosed",
and the CI overlap is implicit but clear from the numbers.

**Does it matter?** Not for the decision (the CI lower bound > 0.05 is what matters, and it clears).
It slightly weakens the "genuine test" framing: the prediction range was narrow and the result landed
just outside, suggesting either the prediction was well-calibrated but unlucky, or 0d is slightly
worse than the author expected. For the paper, the prediction miss should be stated in one sentence
with the CI overlap noted. **No action needed beyond what's already written.**

### (i) head-5 0d sanity: 0.938 → 0.955

From range_check.log: 0d_T1_head5 y_zero = 0.938. From range_check_v2.log: 0d_T1_head5 y_zero = 0.955.
The delta is +0.017, caused by the is_sum_type reclassification of 163/1568 events (sum-type events
get n/k scaling, which widens the interval for y=0, reducing the score → fewer clean events with high
scores → sanity improves).

**Is 0.955 a legitimate pass?** The threshold is 0.95. The margin is 0.005 — knife-edge. But:
(a) the 163 reclassified events are correctly reclassified (the old rule missed grouped sums, print(var),
.round(), etc.); (b) y_times_10 at T1 is 0.998, so the signal is healthy for large perturbations; (c) the
y=0 case is the hardest because 0 is inside many sum intervals by construction. **Verdict: legitimate
pass, barely.** The paper should note that 0d's y=0 sanity at head-5 is 0.955, and that head-2 (0.853)
fails. F2''' does this correctly.

## G. Re-scored dimensions

| Dim | Round 5 → now | One sentence | Blocking item if < 4 |
|---|---|---|---|
| D1 Evidence relevance | 3 → **4** | The 0d k-curve, 0o* decomposition, estimator/oracle-knowledge split, within-table primary metric, table-clustered CIs, sanity rows for every reference, and the unfiltered mean/median side-by-side (0d/0r_log/0o*/0o) are a complete CPU-only evidence set for the paper's central claim. | n/a — P4 agent runs are the next frontier, not a D1 deficiency. [CPU-only ceiling reached] |
| D2 Falsifiability | 3 → **3** | The A-P3d prediction (0.03-0.10 at k=5) was a genuine test that the result barely failed (0.111 vs 0.10 upper bound), disclosed honestly. C3 bar is single-defined. But the prediction miss slightly undermines "this was a real prediction" for a sceptical reviewer, and A-P4 still says "no op classifier needed" which contradicts A-P3d. | Mark A-P4 line 370 superseded. Consider widening future predictions or noting that 95% CIs overlapped. **[writing-only]** |
| D3 Scope calibration | 3 → **4** | F4''' claims are tight: "achievable ceiling ~0.73 at five rows", "0d leaves ~0.11 on the table", "~0.06 is knowledge no k-row checker can have". Every superseded finding is marked. The caveat that 0r_log exceeds 0o* at large k is stated. | n/a |
| D4 Argument coherence | 3 → **4** | The central claim, F4''', and the C3 bar all use the same decomposition (0d / 0o* / 0o) and tell the same story. No contradictions found between the plan, protocol, and findings. | n/a |
| D5 Exploration integrity | 4 → **4** | Protocol 5e978bb precedes results 40d5da3; prediction committed and missed; retroactive log entries present; recheck script committed as an independent verification. | n/a |
| D6 Methodological rigor | 3 → **3** | All round-5 fixes landed and test_zeroparam.py passes. But: (a) `is_sum_type` misclassifies `groupby.mean().sum()` and `len(df['x'].unique())` (conservative bias, no current impact but blocks P4 correctness); (b) F2' lacks a SUPERSEDED marker; (c) A-P4 "no op classifier" is stale. | Fix (a) with two test cases; add F2' marker; fix A-P4 line. **[writing-only + one code fix]** |

Mean 22/6 = **3.67**, Accept (mean ≥ 3.5, no dimension < 2).

## H. C3 bar assessment

The C3 bar defined in A-P3d is concrete and sound:
- **Slice (b), scalar:** AUROC_7 - max(AUROC_0d, AUROC_0r_log) > 0 (lower table-clustered CI).
  Secondary: fraction of (0o* - 0d) closed by signal 7.
- **Slice (a), multi-number:** lower CI > 0.70 AUROC, >= 100 events.
- **Contingency:** if 0o* - 0d < 0.05 at the agent's k, report "no headroom on (b)."

This is the right bar. It asks signal 7 to beat the best zero-parameter method that sees the same rows,
and uses the 0o* decomposition as colour (how much of the gap it closes), not as a hard target. The A-P3d
definition, the plan C3 line, and A-P4 (with the exception of line 370) all agree. No contradiction.

## I. Verdict and next actions

**GO-WITH-CHANGES.** The CPU-only ceiling is reached. D1, D3, D4, D5 are at 4; D2 and D6 are at 3 with
small writing/code fixes. After those fixes, the score would be 3.83-4.00 — the theoretical CPU-only
maximum, since every remaining improvement (H1 tests, H2 tests, C3 evaluation, C2 on P3 pairs) requires
P4 agent runs.

### Remaining items (ranked by score impact)

1. **[writing-only, 10 min] A-P4 line 370: mark "no op classifier needed" superseded by A-P3d's
   is_sum_type rule.** Raises D2 toward 4. Add one sentence: "Superseded by A-P3d: is_sum_type
   determines resample size; see test_zeroparam.py."

2. **[writing-only, 5 min] F2' header: add "[SUPERSEDED by F2''/F2'''; original numbers retained for
   the record]".** Raises D6 toward 4. The body keeps the old 41.8%/58% as the historical snapshot.

3. **[code + test, 30 min] is_sum_type edge cases: `groupby.mean().sum()` (should be False — the sum
   is over group means, which are location statistics) and `len(df['x'].unique())` (should be False —
   count-distinct does not scale as n/k).** Add the two test cases; if fixing the AST walker is complex,
   document them as known limitations for P4. Conservative bias, so no current number changes.

4. **[writing-only, 5 min] F4''' prediction miss: add one sentence noting the 95% CI lower bound
   (0.095) is inside the predicted range, so the miss is marginal.** Optional polish, not blocking.

### Does anything in A-P3d or the plan still let P4 "not lose"?

Yes. The plan's P4 protocol (PREREGISTRATION.md) is well-designed to avoid a wasted experiment:
- P4 is the formal G2 gate (pre-decided to fail by the hit-rate bound, so "failing G2" is expected).
- H1 and H2 are tests of agent signals, not of the oracle references; null results are informative.
- C3 has both an absolute bar (slice a, multi-number) and a relative bar (slice b, vs 0d/0r_log). If
  no headroom exists on (b), the paper reports it as such without claiming failure.
- The budget drop order ensures the minimum-viable paper (one agent, T0+T1, C1 figure) runs first.
- The 4p MATH4AI version is scoped to C1 only (one agent, context-richness axis, 0d/0o* references).

The only "lose" scenario is: C3 scorer fails slice (a) (< 0.70 AUROC on multi-number, or < 100 events)
AND no agent-intrinsic signal beats 0d on slice (b). In that case, the paper becomes a negative-result
empirical study of the 0d/0o*/0o curves + failure taxonomy, which is still publishable at a workshop.

### Three next actions

1. Fix items 1-3 above (45 min). Commit.
2. Set up vLLM with Qwen3-4B or obtain an API key for the first P4 agent. Run the 20-task smoke test
   (A-P4) with `smolagents_toolcalling` adapter; if < 90% parseable, switch to `langgraph_react_full`.
3. Run P4 week 1: Qwen3-4B at T0_agent and T1 on the 210 P3 tasks (clean × 2 seeds + toxic × 1 = 630
   trajectories). Score 0a/0b/0d/4/3/7. If 0d+7 at T0_agent and T1 is ready by 11/10, submit the 4p
   MATH4AI version.

### (1) Is the CPU-only ceiling NOW reached?

**Yes.** D1 is at 4. Every remaining evidence gap (H1/H2 tests, C3 evaluation, C2 on P3 pairs, the
Figure 1 agent signal lines) requires agent trajectories that only P4 can produce. The oracle-value
analysis (0d/0o*/0o curves, estimator-loss decomposition, sanity rows, sensitivities, common-support
fractions, within-table CIs, template/op/direction splits, the F2'''/F4''' findings) is complete.

### (2) Does anything in A-P3d or the plan still let P4 "not lose"?

Yes — see above. The plan explicitly handles every null-result scenario, and the budget drop order
ensures the minimum paper runs first.

### (3) Verdict

**GO-WITH-CHANGES.**
- Fix items 1-3 (one commit, < 1 hour).
- Then P4. GPU/API key needed from user.

**Strongest part:** the cumulative pre-registration discipline through 6 rounds. Each round's protocol
committed before results, each prediction tested, each miss disclosed. A reviewer seeing the git log
(5e978bb → 40d5da3 → 89927d2) can verify the entire chain.

**Single most important improvement now:** get an agent endpoint running and start P4 trajectories. The
CPU-only analysis is defensible; the paper's value depends on whether the signal matrix fills in.

## Sources
- `experiments/recheck_round6.py` (commit 89927d2) and `experiments/results/recheck_round6.log` — audited 2026-11-01
- `experiments/zeroparam.py`: `score_0o_star`, `oracle_law`, `is_sum_type`, `rule_0a` — code-traced 2026-11-01
- `experiments/test_zeroparam.py` — run in this session (20/20, 63000/0)
- `experiments/results/range_check.log` and `range_check_v2.log` — sanity line comparison
- `PREREGISTRATION.md` (A-P3d, A-P4, all amendments) — read 2026-11-01
- `findings.md` (F2', F2'', F2''', F3', F4, F4', F4'', F4''', central claim) — read 2026-11-01
- `research-log.md` (last 60 lines) — read 2026-11-01
- `docs/REVIEW_2026-10-31_round5.md` — read 2026-11-01
- private planning notes (not included in this repository)
- `git -P log --oneline -n 5` and `git -P show --stat 5e978bb` — run 2026-11-01
