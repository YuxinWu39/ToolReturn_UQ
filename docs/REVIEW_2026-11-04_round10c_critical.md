# Round 10c — Scientific Critical Thinking Appraisal

**Framework**: Scientific Agent Skills — Scientific Critical Thinking SKILL v1.5 (Kassis et al. 2026, arXiv:2609.00065)
**Appraisal Workflow**: 6-step (fix question and unit; extract evidence; assess design and analysis; choose framework; synthesize with scope; traceable critique)
**Date**: 2026-11-04
**Prior reviews**: 9 rounds (protocol adherence, venue fit). This review uses a DIFFERENT lens: named biases, named statistical pitfalls, named logical fallacies, and whether each conclusion is licensed by the evidence.

---

## 1. Summary

**Question fixed (PICO-analogue):**
- **Population**: Numeric tool-return events in LLM agent trajectories (python_exec over CSV tables).
- **Intervention/Exposure**: Observation context richness — the number and selection of data rows visible to a checker at the time the tool return arrives.
- **Comparator**: Seven+ uncertainty signals (range check, z-score, bootstrap re-execution, token entropy, verbalized confidence, clean-trained scorer, oracle references) compared against each other and against chance.
- **Outcome**: Within-table AUROC for separating poisoned from clean returns.
- **Setting**: ToxicBench benchmark (41 small tables, 9,585 trajectories) + 210 generated tasks on 6 large public tables (344–17,379 rows), two open-weight agents (Qwen3-4B, Qwen3-8B).

**Claims evaluated (from plan and findings):**
1. Agents blindly follow corrupted returns 83–93% of the time, invariant to observation context tier.
2. All agent-intrinsic signals (verbalized confidence, token entropy) are at chance under head-5 context.
3. The information in the observation context is the ceiling on detection (the "information-capacity" claim).
4. ~55% of agent failures (noise-corrected) are observation-caused, not capability-caused.

**Independent unit**: 210 tasks nested in 6 tables.

---

## 2. Strengths

1. **Exemplary pre-registration discipline.** Every hypothesis, signal definition, threshold, and stopping rule is committed to git before the evaluating code runs. Predictions are committed and honest when missed (P5 prediction [0.55, 0.70] vs observed 0.50–0.52; A-P3d prediction 0.03–0.10 vs observed 0.111). This is well above the norm for ML workshop papers and directly addresses **HARKing** (Pitfall 20, Bias 2) and **p-hacking** (Bias 19). The 6 protocol amendments are themselves pre-registered and logged, not silent post-hoc changes.

2. **Within-table AUROC as the primary metric** correctly addresses the **ecological fallacy** (Fallacy 8, Pitfall 16) that pooled AUROC can inflate via cross-table difficulty variation (citing 2610.05572). This is a methodological strength most papers in this space lack.

3. **Sanity-row hard rule** (every content-aware signal must reach AUROC > 0.95 on synthetic fully-corrupted observations, or it is withheld as a headline) is an effective guard against **measurement bias** (Bias 12) — a broken pipeline that scores randomly would be caught before the result is reported.

4. **Transparent handling of superseded findings.** F2/F2'/F2''/F2''', F3/F3', F4/F4'/F4''/F4''' are each marked superseded with the replacement named. This is open-science best practice (Bias 14, Reporting Bias). A published paper would not carry this trail, but the audit trail is commendable for reproducibility.

5. **The 0o*/0d decomposition** is a genuine conceptual contribution. Separating estimator loss (what 0d leaves on the table) from oracle knowledge (what no k-row checker can recover) provides a principled framework for understanding why detection fails at low context, rather than merely reporting that it fails.

---

## 3. Concerns

### 3.1 Critical (threaten main conclusions)

#### C1. The "information capacity is the ceiling" claim equivocates between descriptive, predictive, and causal

| Field | Value |
|-------|-------|
| **Source** | findings.md "Central claim, reconciled"; plan "Central claim" |
| **Observation** | The claim "what bounds detection of a corrupted numeric tool return is the information in the observation context" is stated in causal language ("what bounds"), but the evidence is descriptive: a k-sweep on oracle values at k ∈ {5, 10, 20, 50, 100, 200} with random row draws, plus agent results at head-5 only. The k-sweep shows 0o* rises monotonically with k (random rows). The agent results show all signals are near chance at head-5. But head-5 ≠ random-5: 0o* = 0.73 at random-5 vs 0.58 at head-5 (F5). This 0.15 AUROC gap is not explained by "information quantity" — both conditions have exactly 5 rows. |
| **Named issue** | **Confounding of row-count with row-selection** (Pitfall 15: Correlation ≠ Causation; Pitfall 17: Simpson's Paradox risk). The k-sweep varies k (number of rows) and simultaneously varies row composition (random draws). The agent experiment varies row selection (head vs random) but not k. No experiment varies k while holding selection fixed, or varies selection while holding k fixed across a range of k values. The claim that "information quantity" is the bounding factor is confounded with row-ordering effects: head rows of Bike (ordered by hour) and Wine (red-then-white) are systematically unrepresentative. |
| **Consequence** | The monotonic k-sweep curve may reflect (a) more rows = more information (the claimed mechanism), (b) more rows = more representative sample (a sampling-quality effect), or (c) both. The claim "information in the observation context is the ceiling" is not licensed as causal. It is descriptive: "detection improves with k random rows, and the k-sweep's 0o* curve is an upper bound for checkers using the template statistic on random k-row subsets." The paper conflates "rows visible" with "information available," but head-5 demonstrates these are not the same thing. |
| **Uncertainty** | Medium. The decomposition on random rows is sound. The causal language is the problem, not the numbers. |
| **Feasible remedy** | (1) Run agent trajectories at T1_rand5 (random 5 rows) to measure whether 0o* ≈ 0.73 is achieved when agents actually see random rows — this would separate row-count from row-ordering. (2) Restate the claim as descriptive: "on random k-row subsets, the achievable AUROC (0o*) rises from 0.73 to 0.90; under the default head-5 preview, agents and all checkers achieve ≤ 0.58." (3) Explicitly name **ecological validity** (Fallacy 8, Core Capability 1 — external validity) as a limitation: the k-sweep's random-draw setting does not match the head-5 setting agents actually face. |

#### C2. The independent unit is 6 tables, but CIs are presented as if the unit is tasks or (task, draw) pairs

| Field | Value |
|-------|-------|
| **Source** | findings.md F4''': "estimator loss 0o\* - 0d = +0.11 [0.095, 0.130]"; plan "Central claim": "0o\* rises monotonically from 0.73 at five rows to 0.90 at 200" |
| **Observation** | The 210 tasks are nested within 6 tables (35 per table, perfectly balanced). The CIs are computed by bootstrap over 6 table-level clusters. With n = 6 clusters, a percentile bootstrap CI has poor coverage properties — the bootstrap distribution of a 6-point mean is discrete and may systematically undercover. The F4''' table reports the 6-table CI [0.095, 0.130] for estimator loss at k = 5, which is strikingly narrow for 6 clusters. The (table, draw) CI is secondary and has many more units but treats tasks within the same table as exchangeable, which they are not (they share the same column distributions). |
| **Named issue** | **Pseudoreplication** (Pitfall 43). 210 tasks from 6 tables treated as if tasks are independent units, when tasks sharing a table share column distributions, row ordering, and filter-value availability. The 6-table bootstrap is the correct clustering level, but n = 6 is below the threshold where the percentile bootstrap is well-calibrated. **Small Sample Fallacy** (Pitfall 11): trusting CIs from 6 clusters. |
| **Consequence** | The estimator-loss CI [0.095, 0.130] may be anti-conservative. The claimed precision ± 0.018 on 6 clusters is suspiciously tight. The monotonicity of 0o* across k is robust (it must be monotone by construction for any fixed task set), but the specific numbers and CI widths may not generalize to a different set of tables. The "0.11 at k = 5" is a property of these 6 tables, not necessarily a universal constant. |
| **Uncertainty** | Medium-High. The direction is almost certainly correct (0o* > 0d at small k), but the magnitude 0.11 and the narrow CI are both table-set-dependent. |
| **Feasible remedy** | (1) State explicitly that the 6-table bootstrap has poor small-sample coverage and that [0.095, 0.130] should be interpreted as approximate. (2) Report a bias-corrected accelerated (BCa) bootstrap or a t-interval with Satterthwaite df as a sensitivity check. (3) Report per-table values so the reader can see heterogeneity directly (F4''' does this partially by template but not by table). (4) In the paper, present the 6-table CI as exploratory and recommend expansion to ≥ 20 tables for confirmatory status. |

#### C3. H1 "agents carry no information" is tested by AUROC on heavily quantized data — absence of evidence, not evidence of absence

| Field | Value |
|-------|-------|
| **Source** | findings.md F6: "verbalized confidence 0.55 [0.49, 0.61]" at plausible+subtle; F7: "0.53 [0.48, 0.57]" |
| **Observation** | Verbalized confidence for Qwen3-4B is quantized: ~85% of mass on {75, 80, 85} (F6 reports mode 80, mean 77.7 clean vs 76.7 poisoned). AUROC with heavily tied scores is degenerate — the ROC curve has very few distinct operating points. The test "upper 95% CI < 0.60" is an equivalence test with a bound that was set without a power analysis. For Qwen3-4B the upper CI is 0.61 (misses by 0.01); for Qwen3-8B it is 0.57 (passes). So H1(verbalized) is agent-dependent, and the threshold itself was not justified as a scientifically meaningful equivalence margin. |
| **Named issue** | **Absence of evidence ≠ evidence of absence** (Pitfall 2, Fallacy 34 — Argument from Ignorance). The conclusion "intrinsic signals carry no information" is stated as a positive finding, but the evidence is a non-significant result on a measure (AUROC) that is insensitive to the signal's structure (heavily quantized). **Measurement Bias** (Bias 12 — Instrument Bias): AUROC is the wrong instrument for a 3-point discrete signal; the rank-based metric has almost no power to detect a small shift in the probability mass across three tied values. |
| **Consequence** | The H1 conclusion is not "agents carry no information about poisoned returns." It is "AUROC on a 3-point quantized signal with n ≈ 200 events does not exceed 0.60." These are different statements. A Fisher exact test on the contingency table of (confidence = 85 vs not) × (poisoned vs clean) might detect a shift AUROC cannot. The 1-point clean/poisoned mean difference (77.7 vs 76.7) is not zero — it is small and masked by quantization. |
| **Uncertainty** | Medium. The point estimates are genuinely close to chance. But the instrument choice (AUROC on quantized data) and the threshold choice (0.60 without power justification) weaken the strength of the negative claim. |
| **Feasible remedy** | (1) Supplement AUROC with a test on the raw category probabilities (chi-squared or Fisher exact on the multinomial distribution of confidence values). (2) Report the equivalence test explicitly as TOST (two one-sided tests) with a pre-justified margin, noting the power for the observed n and quantization. (3) Restate H1 as "AUROC < 0.60" rather than "carry no information," which is a stronger claim than the test supports. |

### 3.2 Important (affect interpretation but not fatally)

#### I1. C3 scorer negative: absence of evidence, not evidence of absence (Pitfall 2, Fallacy 34)

| Field | Value |
|-------|-------|
| **Source** | findings.md F8: "C3 as specified in P5 is a negative result" |
| **Observation** | The scorer used 0.5B parameters, ~1,741–1,772 LOTO-fold training examples (total pool 2,533), one hyperparameter configuration (lr 2e-4, LoRA r=16, 3 epochs), one target formulation (raw log-value prediction). It failed its own sanity rules (coverage 0.15–0.18 vs 0.80–0.98 required; sanity AUROC 0.81–0.85 vs 0.95). F8 lists P5b candidates (residual target, larger backbone, more data) but none were tested. |
| **Named issue** | **Argument from Ignorance** (Fallacy 34): "We didn't find X with this tool, therefore X doesn't exist." The scorer's catastrophic miscalibration (x6 magnitude error) means it never had a fair chance to detect 1.1–2× poisons. This is an **underpowered study** (Pitfall 9) for the C3 claim, not evidence that learned scorers in general fail. |
| **Consequence** | The paper cannot claim "learned signals add no value" from a single undertrained scorer that failed its own sanity checks. It can claim "this specific scorer configuration failed, and the failure mode (coarse magnitude estimation) suggests the task is harder than raw-value prediction can address." |
| **Uncertainty** | Low — F8 already states this honestly. The concern is about how it is framed in the plan/abstract. |
| **Feasible remedy** | Frame C3 as "the naive scorer fails; the failure mode (insufficient resolution) is informative about the task's difficulty" rather than as evidence that learned detection is infeasible. Avoid any language suggesting C3 generalizes to all learned approaches. |

#### I2. Selection and survivorship: the 4.2% pairing impurity, ~95% sandbox normalizations, ERROR exclusions, and common-support restriction

| Field | Value |
|-------|-------|
| **Source** | F6 round-7 additions: "4.2% of task pairs the clean seed-0 run's first scalar python_exec code differs from the toxic run's poisoned code"; F5: "Harness normalizations fired in 630 (pandas re-import), 615 (read_csv resolved) and 51 (stray indent)"; A-P2: "Observations starting with ERROR or Traceback are out of scope"; F4''': "common support: 168 tasks computable at every k" |
| **Observation** | Multiple filtering steps reduce the analysis population: (a) 4.2% code-impure pairs where clean and toxic code differ; (b) ~95% of runs needed sandbox normalizations (pandas re-import, read_csv resolution); (c) ERROR observations excluded; (d) common support restricts from 210 to 164–168 tasks. Each individually is small, but they compound, and every filter removes observations that are more likely to be "difficult" or unusual. |
| **Named issue** | **Selection Bias** (Bias 9 — Attrition/Survivorship). The common-support restriction to 168/210 tasks drops 42 tasks where some signal is not computable, which are precisely the tasks where filtered/grouped queries interact with small visible subsets. These are the tasks where detection is hardest and where signal differences would be most informative. The impure pairs (4.2%) are left in — the direction of bias is unclear but uncontrolled. **Survivorship Bias**: only tasks where all signals can be computed appear in the primary curve. |
| **Consequence** | The primary k-sweep curve (168 tasks) may overstate detection performance by excluding the hardest tasks. The direction of bias for the information-capacity claim is ambiguous: excluding hard tasks could inflate 0o* (ceiling looks higher than it is on the full set) or deflate 0d (bootstrap works better on "nice" tasks). The 4.2% impurity means some zero-parameter scores are computed on a different code path than the one that produced the observation — invalidating the "re-execute the agent's own code" interpretation for those pairs. |
| **Uncertainty** | Medium-Low. Each filter is disclosed and counts are reported. The bias direction is unclear, which is itself a concern — biases that could go either way should be bounded, not ignored. |
| **Feasible remedy** | (1) Report the 210-task curve alongside the 168-task common-support curve (assigning a neutral score of 0.5 to uncomparable tasks). (2) Report the zero-parameter AUROC with and without the 4.2% impure pairs. (3) For the normalizations, the existing sensitivity check (29/630 unnormalized T1 runs show the same compliance pattern) is adequate, but should be in the main text, not a parenthetical. |

#### I3. Multiplicity: ~10 signals × 4 tiers × 2 agents × severity bins, with no correction — but the conclusion is null

| Field | Value |
|-------|-------|
| **Source** | F5, F6, F7 — per-signal per-tier per-agent AUROC tables |
| **Observation** | Approximately 10 signal variants × 4 context tiers × 2 agents × 3 severity bins = ~240 AUROC estimates, with no family-wise error rate or FDR correction. The conclusion is that "everything is null," so multiple testing works in the conservative direction: under multiplicity, the probability of at least one false positive increases, which would create a spurious "significant" signal, not a spurious null. |
| **Named issue** | **Multiple Comparisons** (Pitfall 6, Fallacy 27). However, the direction of the multiplicity bias is reversed from the usual concern: here, the more tests performed without finding anything, the stronger the evidence that nothing is there (assuming adequate power per test). But this reversal has a subtlety: **if any individual comparison had low power (see C3 above for the quantized verbalized confidence), multiplicity does not rescue it**. |
| **Consequence** | Multiplicity does not threaten the "everything is null" conclusion. It would threaten any future claim that a single signal "breaks through." The concern is proportionate: minor. The paper should note that the all-null pattern is robust to multiplicity correction (no comparison would become significant even without it) and that any future positive result from this dataset would need Bonferroni or FDR correction. |
| **Uncertainty** | Low. |
| **Feasible remedy** | One sentence: "Because every signal is at or below chance, multiplicity correction would not change any conclusion; it would apply to any future claim of a positive signal from this dataset." |

#### I4. Researcher degrees of freedom: 6 amendments, 2 withdrawn headlines, prediction misses — does pre-registration constrain or rationalize?

| Field | Value |
|-------|-------|
| **Source** | PREREGISTRATION.md: A-P1, A-P2, A-P3, A-P3b, A-P3c, A-P3d, A-P4, A-P4b, P5; findings.md: F4' SUPERSEDED, F4'' SUPERSEDED |
| **Observation** | Six protocol amendments were made between the initial pre-registration and the final results. Two headline findings (F4' "information, not estimator" and F4'' "~0.17 recoverable") were stated and then retracted. The A-P3d prediction (0.03–0.10 for estimator loss) was missed (observed 0.111). The P5 prediction was missed. The amendment chain is transparent and each is dated, but the practical effect is that the analysis was iteratively refined in response to intermediate results. |
| **Named issue** | **P-Hacking / Researcher Degrees of Freedom** (Bias 19, Pitfall 6). Pre-registration constrains analysis only if the protocol is frozen before data. Here, the protocol was amended 6 times during the study, each time incorporating lessons from prior analyses. The amendments are defensible individually (fixing bugs, adding a better oracle), but cumulatively they allow the analysis to converge on a narrative that fits the data. The question is whether the final protocol would have been written identically if designed de novo without seeing any intermediate results. The answer is almost certainly no. |
| **Consequence** | The pre-registration trail provides an audit trail but does not provide the confirmatory guarantee that a frozen protocol would. The honest framing is "iteratively pre-registered with full amendment trail," not "pre-registered." The strongest test in the project is H1 (intrinsic signals), which was defined in the original protocol and its test applied without amendment to Qwen3-8B; the weakest is the information-capacity claim, which was iteratively refined through 4 superseded findings. |
| **Uncertainty** | Medium. The amendments are transparently logged, which mitigates but does not eliminate the concern. |
| **Feasible remedy** | (1) Label the k-sweep and information-capacity findings as exploratory (they were iteratively developed). (2) Label H1 for Qwen3-8B and the blind-compliance finding as confirmatory (tested against the originally registered definition, with A-P4b's signal-1 replacement the only change, applied before the 8B run). (3) In the paper, describe the amendment trail as an open-science transparency measure, not as equivalent to a frozen pre-registration. |

### 3.3 Minor

#### M1. Generalization: 2 same-family models, 1 benchmark, numeric tools — **Hasty Generalization** (Fallacy 5)

| Field | Value |
|-------|-------|
| **Source** | Plan "Agents" section; F5/F7 |
| **Observation** | Qwen3-4B and Qwen3-8B are the same architecture at different scales. The claim "agents blindly follow" uses the general term "agents." One benchmark (ToxicBench), one tool type (python_exec over CSV), numeric returns only. |
| **Named issue** | **Hasty Generalization** (Fallacy 5). Two models from one family cannot establish a model-general claim. The plan's H5 (closed-source control) is registered but unexecuted. |
| **Consequence** | The paper is licensed to say "two open-weight Qwen models blindly follow corrupted numeric returns on ToxicBench," not "agents" in general. |
| **Uncertainty** | Low — this is straightforward scope. |
| **Feasible remedy** | Use "the tested agents" or "both tested models" throughout. Add one non-Qwen model (gpt-5.4-mini is registered) before claiming generality. |

#### M2. "No SDK ships a tool-output confidence hook" as evidence of importance — **Argument from Ignorance** (Fallacy 34)

| Field | Value |
|-------|-------|
| **Source** | Plan novelty check: "No agent SDK (OpenAI Agents SDK, LangGraph ValidationNode, LlamaIndex, MCP spec) ships a tool-OUTPUT confidence hook; LangGraph validates tool inputs only" |
| **Observation** | The absence of a feature in current SDKs does not establish that the feature is important. It could reflect low demand, implementation difficulty, or different architectural priorities. |
| **Named issue** | **Argument from Ignorance** (Fallacy 34): inferring importance from the absence of a solution. |
| **Consequence** | Minor — this is a motivational framing, not an evidence claim. But the paper should cite the problem (agents accept bad returns, quantified) as the motivation, not the absence of a solution. |
| **Uncertainty** | Low. |
| **Feasible remedy** | Frame as "no existing solution" rather than "the gap proves the problem is important." The importance comes from the 83–93% compliance rate, not from SDK feature gaps. |

#### M3. The McNemar G1 noise-floor design: clean-vs-clean discordance as a null

| Field | Value |
|-------|-------|
| **Source** | findings.md F1': "Clean-vs-clean discordance on 737 duplicate keys is 4.3%" |
| **Observation** | The noise floor uses within-environment discordance (clean₁ vs clean₂) as the null for the excess toxic-failure rate. This is methodologically sound. However, the 4.3% noise floor is estimated from 737 keys with ≥ 2 clean runs, which may not be representative of the full 3,633 pairs — keys with multiple runs may be from more-tested adapters or models. |
| **Named issue** | **Selection Bias** (Bias 9): the 737 multi-run keys are a subset, and the noise floor estimated on them may not apply to the 2,896 single-run keys. |
| **Consequence** | Minor — the excess (18.7pp) is so large relative to the floor (4.3%) that even doubling the floor would not change the conclusion. The McNemar test (734 vs 81) is robust. |
| **Uncertainty** | Low. |
| **Feasible remedy** | Acknowledge that the noise floor is estimated on a convenience subset and that generalization to single-run keys is an assumption. |

#### M4. The sum-type reclassification changed 163 events — potential **Outcome Switching** (Bias 14)

| Field | Value |
|-------|-------|
| **Source** | findings.md F2''': "The A-P3d sum-type rule reclassifies 163 of the 1,568 scored python_exec events" |
| **Observation** | Reclassifying 163 events (10.4% of scored events) changes the 0d interval computation (sum-type uses n/k scaling, location-type does not). The reclassification was made to fix real bugs (grouped sums misclassified) and is accompanied by unit tests, but it was made after seeing results on the original classification. |
| **Named issue** | **Outcome Switching** (Pitfall 8, Bias 14): changing the analysis pipeline after seeing intermediate results. The amendment (A-P3d) is logged, but the reclassification was motivated by observed anomalies, not by prior specification. |
| **Consequence** | Minor — the changes are in the conservative direction (sum-type intervals are wider, which reduces false positives), the unit tests justify the fix, and the original numbers are preserved in superseded findings for comparison. |
| **Uncertainty** | Low. |
| **Feasible remedy** | Already handled by the amendment trail. In the paper, state that the classification rule was refined during development (citing the test suite) and report the sensitivity of results to the original rule. |

---

## 4. Specific Recommendations (ordered by impact)

1. **Restate the central claim as descriptive, not causal.** Replace "what bounds detection is the information in the observation context" with a scoped version: "On random k-row subsets, the achievable within-table AUROC rises from 0.73 (k=5) to 0.90 (k=200); under the default head-5 preview, all tested signals achieve ≤ 0.58. The gap between random-5 (0.73) and head-5 (0.58) demonstrates that row representativeness, not just row count, determines detection capability." Name the confound (row-ordering with row-count) explicitly.

2. **Run T1_rand5 agent trajectories.** This single experiment separates the row-count effect from the row-ordering effect and resolves concern C1. If agent signals reach ~0.70 at random-5, the information-capacity claim is strongly supported. If they remain at ~0.58, the mechanism is about row representativeness, not information quantity.

3. **Acknowledge the 6-table CI limitation.** State that "CIs from 6-cluster bootstrap are approximate and may undercover; the specific magnitude 0.11 [0.095, 0.130] should be interpreted as indicative, not precise." Report per-table estimator loss values to show heterogeneity. Consider a BCa or t-interval as a sensitivity check.

4. **Supplement AUROC for verbalized confidence with a discrete-distribution test.** The quantized signal ({75, 80, 85} covers ~85% of mass) defeats AUROC. Add a chi-squared or Fisher exact test on the multinomial distribution of confidence categories to H1's evidence. This does not require new data.

5. **Reframe the C3 negative result.** The paper is licensed to say "this scorer specification failed" not "learned detection fails." List the specific failure mode (coarse magnitude resolution relative to poison strength) and explicitly note that the single configuration (0.5B, one target, one hyperparameter setting) is insufficient to close the question.

6. **Label the k-sweep findings as exploratory.** The k-sweep was iteratively refined through 4 superseded findings (F4→F4'→F4''→F4'''). The blind-compliance finding and H1(Qwen3-8B) are the confirmatory results; the information-capacity decomposition is exploratory-with-audit-trail.

7. **Report the 210-task full curve alongside the 168-task common-support curve.** Assign neutral scores to the 42 excluded tasks to show the common-support restriction does not materially change the picture (or, if it does, acknowledge the survivorship bias).

8. **Add one non-Qwen agent.** The gpt-5.4-mini control is registered and budgeted at ~$50–100. Without it, every generalization claim beyond "Qwen models" is a hasty generalization.

---

## 5. Overall Assessment

### Conclusion 1: Blind compliance is tier-invariant (83–93% across all context tiers)

**Verdict: SUPPORTED**

*Licensed sentence*: "Both tested Qwen agents accepted and used poisoned numeric returns in 83–93% of runs, with zero anomaly-detection challenges across 3,780 trajectories, and this rate did not vary with observation context tier (T0_agent through T3)."

*Basis*: Directly measured, replicated across two model sizes and four tiers, noise floor quantified (2.9–5.2%), methodology sound (McNemar on discordant pairs). The only scope restriction is model family (Qwen only) and benchmark (ToxicBench P3 tasks only).

---

### Conclusion 2: All agent-intrinsic signals are at chance under head-5 context

**Verdict: SUPPORTED WITH SCOPE RESTRICTION**

*Scope restriction*: "AUROC of verbalized confidence and token entropy variants, on the specific quantized distributions these two Qwen models produce, does not exceed 0.60 (plausible+subtle, within-table). For Qwen3-4B verbalized confidence specifically, the registered threshold is missed by 0.01 on the upper CI bound."

*Licensed sentence*: "For both tested agents, verbalized confidence (AUROC 0.53–0.55) and token entropy (AUROC 0.46–0.50) do not discriminate poisoned from clean returns at head-5, though the AUROC instrument has limited sensitivity to the heavily quantized verbalized-confidence signal."

*Basis*: The point estimates are genuinely near chance. The scope restriction is needed because (a) AUROC on a 3-point signal has low power to detect small probability shifts, (b) only one model family tested, (c) the "carry no information" phrasing exceeds what a non-significant AUROC supports (absence of evidence).

---

### Conclusion 3: Information in the observation context is the detection ceiling

**Verdict: SUPPORTED WITH SCOPE RESTRICTION**

*Scope restriction*: "On random k-row subsets of the 6 tested tables, the draw-conditioned oracle (0o*) rises monotonically from 0.73 to 0.90 as k increases from 5 to 200, and the bootstrap re-execution check (0d) trails it by ~0.11 at k=5. Under the default head-5 preview, all signals achieve ≤ 0.58. The claim that 'information quantity is the bounding factor' is descriptive; the 0.15 gap between random-5 and head-5 shows that row representativeness, not just row count, determines the achievable ceiling. The magnitudes are estimated from 6 table clusters and should be treated as approximate."

*Licensed sentence*: "Detection of corrupted numeric returns improves monotonically with the number of randomly sampled visible rows, and the draw-conditioned oracle 0o* provides an upper bound for checkers using the template statistic; but the default head-5 preview yields substantially worse detection than random-5, indicating that row selection quality matters alongside row quantity."

*Basis*: The k-sweep is methodologically sound on random draws. The head-5 vs random-5 gap (C1 above) means the causal claim needs qualification. The 6-table CI is approximate (C2 above).

---

### Conclusion 4: ~55% of failures (noise-corrected) are observation-caused

**Verdict: SUPPORTED**

*Licensed sentence*: "After correcting for the run-to-run noise floor (4.3% clean-vs-clean discordance), 55% of excess toxic failures overall (43% in the numerical family) are observation-caused — the agent would have succeeded had it received a clean return."

*Basis*: McNemar test (734 vs 81, p ~ 1.4e-40), noise-corrected share 0.55 [0.43, 0.67 implicit from CI on excess]. Methodology sound. Note: the plan's semantic memory erroneously states "95% of failures are observation failures" — this must be corrected to the F1' value of 0.55 before any paper draft.

---

*This review was guided by the Scientific Critical Thinking SKILL v1.5 appraisal workflow. No files were modified except this report.*
