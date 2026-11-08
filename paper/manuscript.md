# Agents See the Rows but Accept the Number: Runtime Checks for Silently Corrupted Tool Returns

*Working manuscript, November 8, 2026 (revision 3: adds the Experiment A monitor intervention for Gemini Flash and Qwen3-8B). Anonymous submission draft for Trust4RSI-Agent @ AAAI 2027, 4-page short paper. Generated tables are produced by `experiments/export_paper_evidence.py` from saved results.*

## Abstract

When an agent's tools are updated, regressed, or swapped, a call can return a well-formed but wrong number. No error is raised, so the agent gets no explicit signal to retry. We ask where a check for such returns should sit. On 210 scalar queries over six public tables, the first numeric return is silently multiplied by 1.05 to 2 (or its reciprocal). In free-running ReAct trajectories, Qwen3-4B and Qwen3-8B report the corrupted value in 97–99% of the runs where the corruption fired, and Gemini Flash in 56%. Qwen adopts it at similarly high rates whether or not it had previewed table rows. With five random rows, a bootstrap check that uses only the visible rows reaches within-table AUROC 0.62; with two hundred, 0.84. We then intervene on 30 queries shown with twenty query-matched rows. Supplying the check's interval and flag to the model raises clean-versus-corrupted acceptance discrimination by +0.094 [0.050, 0.133] for Gemini and +0.550 [0.306, 0.756] for Qwen3-8B. For Qwen this comes at a cost of 6.7 points of clean acceptance, so its registered joint benefit rule fails. In both models the aided decision converges to the flag. It does not exceed simply acting on the flag: the differences are −0.017 and −0.028. These results suggest that numeric return checks can be a runtime service whose output drives the accept or reject decision, rather than something left to the model's own judgment.

## 1. Introduction

Agents that evolve gain and replace tools, rewrite skills, and depend on registries they do not control. Each change can introduce a *quiet* failure, such as an analysis tool that returns a plausible scalar that is off by 10% or 50%. Unlike a crash or a schema error, a quiet numeric failure does not expose an error to the agent's retry logic. Recent audits find that tool-using agents largely accept such outputs [Tao and Yin, 2026; Yang et al., 2026; Kraishan, 2026]. The systems question is who should catch them: the model reading the return, or a check in the layer that delivers it.

We study this at a narrow boundary: a single scalar returned by a pandas tool. We separate four quantities: what agents *do* with a corrupted return; how much *evidence* the visible rows hold for a tested check; whether a model *uses* a check's output when it is given; and how the aided model compares with the check alone. Our contributions:

1. **Behavior across preview tiers.** Across three preview tiers and three models (seven configurations, including a T1 replicate), Qwen adopts a silently corrupted scalar in 97–99% of fired runs and Gemini in 56%. Qwen's adoption is high whether or not it had previewed rows.
2. **Evidence budget.** Under the tested bootstrap check, signal grows with the number of visible rows k, from 0.62 at k=5 to 0.84 at k=200.
3. **Monitor intervention.** In a frozen paired experiment, giving the model the check's output improves acceptance discrimination for both models. Qwen's clean acceptance falls, failing the registered joint rule, and neither aided model exceeds the flag alone.
4. **Negative instrument results.** Verbalized confidence and token entropy lack live sanity controls, so we make no detector claim for them. A small learned scorer failed its own eligibility gates.

## 2. Setup

**Tasks and corruption.** We generate 210 scalar queries (unfiltered, filtered, and grouped aggregates) over six public tables with 344–17,379 rows (Appendix D). In a corrupted run the environment multiplies the first scalar return by s ∈ {1.05, 1.10, 1.20, 1.35, 1.50, 2.00} or 1/s. It does so once (*poison-once*): re-issuing the call returns the true value. Source data is never modified.

**Agents and preview tiers.** A ReAct agent from ToxicBench [Tao and Yin, 2026] answers each query with a `python_exec` tool and an optional `preview` tool. The harness fixes what `preview` reveals:

- **T0:** the first five rows plus whole-column min/max.
- **T1:** the first five rows.
- **T3:** schema only.

We run Qwen3-4B (T0, T1, T3, plus a T1 replicate) and Qwen3-8B (T0, T1) on vLLM at temperature 0.7, and Gemini 3.8 Flash at T1 with low reasoning effort. Each configuration has two clean runs and one corrupted run per task, giving 4,410 trajectories. Adoption is the automatic `poisoned_answer_used` metric, counted over runs where the corruption fired. From the logs we reconstruct which rows the agent had actually seen before the corrupted call.

**Visible-row checks.** A checker may use only what the agent saw plus the returned value. We exclude re-querying, which trivially wins under poison-once. The main check, **0d**, re-executes the query statistic on bootstrap resamples of the visible rows and scores how far the return lies outside the 2.5–97.5% percentile interval. Sums and counts are rescaled by n/k. It flags any return outside the interval.

Two *privileged* references use the full table by Monte Carlo. **0o\*** knows the sampling law of the k-row statistic and centers on the observed draw; **0o** knows the population answer. They aid interpretation; they are not proven optimal detectors or information bounds.

Real-corruption AUROC is reported only for checks that pass a sanity gate (AUROC above 0.95 against ×1000 and ÷1000 corruptions). The primary metric is within-table AUROC with a six-table bootstrap interval.

## 3. Results

### 3.1 Agents adopt corrupted scalars, with or without having seen rows

<!-- BEGIN GENERATED:adoption -->
| Agent | Preview tier | Poison fired / runs | Corrupted value used | Used, rows previewed | Used, no rows previewed |
|---|---|---|---|---|---|
| qwen3-4b | T0_agent | 199/210 | 195/199 (98%) | 140/141 (99%) | 55/58 (95%) |
| qwen3-4b | T1 | 202/210 | 196/202 (97%) | 141/144 (98%) | 55/58 (95%) |
| qwen3-4b | T3 | 200/210 | 194/200 (97%) | n/a | 194/200 (97%) |
| qwen3-8b | T0_agent | 176/210 | 175/176 (99%) | 175/176 (99%) | n/a |
| qwen3-8b | T1 | 196/210 | 194/196 (99%) | 194/196 (99%) | n/a |
| gemini-3.8-flash | T1 | 128/210 | 72/128 (56%) | 26/50 (52%) | 46/78 (59%) |
<!-- END GENERATED:adoption -->

**Table 1.** Adoption among toxic runs where the corruption fired. "Rows previewed" means at least one data row was shown before the corrupted call. The Qwen3-4B T1 replicate (196/202) is omitted here but included in the 4,410 total.

Qwen adopts the corrupted value in 97–99% of fired runs at every tier (Table 1). At T1, Qwen3-4B adopted it in 141/144 runs where it had previewed five rows and in 55/58 where it had not. At T0, where whole-column min/max were also shown, the figure was 140/141. Qwen3-8B always previewed. These are stratified observations of self-selected preview behavior, not a causal effect of previewing. Clean success was 182–204 of 210 per run, so the failure is specific to the corrupted return.

Gemini adopts less often (72/128), but its runs differ in two ways. First, 93 of its 128 first corrupted outputs were not single scalars, which our checks cannot score. Second, of its 50 recoveries, the first subsequent Python call succeeded in 23 and errored in 27. A recovery may therefore come from a retry, which under poison-once returns the true value, rather than from verification. We treat Gemini as a replication with a different evaluation unit.

### 3.2 Signal in the visible rows grows with the row budget

<!-- BEGIN GENERATED:ksweep -->
| Check (within-table AUROC) | k=5 | k=10 | k=20 | k=50 | k=100 | k=200 |
|---|---:|---:|---:|---:|---:|---:|
| 0d bootstrap check (visible rows only) | 0.617 | 0.647 | 0.689 | 0.745 | 0.793 | 0.839 |
| 0o* privileged reference (knows k-row sampling law) | 0.724 | 0.739 | 0.774 | 0.826 | 0.870 | 0.896 |
| 0o privileged reference (knows population answer) | 0.793 | 0.811 | 0.856 | 0.906 | 0.931 | 0.957 |
| min sanity AUROC (0d, high/low) | 0.976 | 0.988 | 0.995 | 0.998 | 1.000 | 1.000 |
<!-- END GENERATED:ksweep -->

**Table 2.** Offline sweep over k random rows (20 draws per task), on the 168 tasks computable at every k. The sanity row is the pooled per-k gate on all computable events. The privileged rows use full-table information that no visible-row checker has.

Under 0d, signal rises from 0.62 at k=5 to 0.84 at k=200 (Table 2). On the head-five rows the Qwen agents actually saw, the tested visible-row checks score 0.53–0.62 (Appendix C). Head rows are not a random sample, either. Weak detection on default previews therefore does not by itself show that agents ignore usable evidence. The 0d–0o\* gap is a descriptive difference between two specified scores, not an information decomposition.

### 3.3 A monitor intervention: the aided model converges to the flag

We froze a paired experiment before collecting any responses. Its 30 filtered-mean queries are five per table, chosen by a fixed rule. Each query has three independent draws of twenty query-matched rows, and each draw is crossed with a clean, a ×1.10 and a ×1.50 candidate. In the **rows only** arm, the model receives the query, code, rows, and candidate. In the **rows + check** arm, it also receives 0d's interval, score, and flag computed from those same rows. The model returns a strict JSON accept/reject/uncertain decision with no tool calls; there is one completion per cell. The registered primary outcome is the change in acceptance discrimination (clean acceptance minus mean corrupted acceptance), averaged over draws, queries, and tables. Its joint rule also requires that clean acceptance not fall by more than 5 points, judged by the lower interval bound. Gemini ran first; the Qwen3-8B replication reused the identical frozen inputs under a protocol committed beforehand.

<!-- BEGIN GENERATED:monitor -->
| Decision maker | Clean accepted | x1.10 accepted | x1.50 accepted | Discrimination change [95% interval] |
|---|---:|---:|---:|---|
| gemini-3.8-flash, rows only | 88/90 | 60/90 | 25/90 | reference |
| gemini-3.8-flash, rows + check | 90/90 | 52/90 | 20/90 | 0.094 [0.050, 0.133] vs raw |
| qwen3-8b, rows only | 90/90 | 90/90 | 83/90 | reference |
| qwen3-8b, rows + check | 84/90 | 49/90 | 13/90 | 0.550 [0.306, 0.756] vs raw |
| 0d flag alone (no model) | 87/90 | 50/90 | 13/90 | 0.111 [0.078, 0.156] vs gemini-3.8-flash raw; 0.578 [0.367, 0.756] vs qwen3-8b raw |
<!-- END GENERATED:monitor -->

<!-- BEGIN GENERATED:flagonly -->
| Model | Rows + check minus flag alone [95% interval] | Flagged candidates accepted | Compatible candidates rejected |
|---|---|---:|---:|
| gemini-3.8-flash | -0.017 [-0.078, 0.039] | 17/120 | 0/150 |
| qwen3-8b | -0.028 [-0.061, 0.000] | 0/120 | 0/150 |
<!-- END GENERATED:flagonly -->

**Table 3.** Top: acceptances out of 90 per candidate type, with the change in acceptance discrimination relative to each model's rows-only arm. The "0d flag alone" row accepts exactly the unflagged candidates. Bottom: exploratory comparison of the aided model with the flag alone, together with how often the model overrode the flag. This comparison was registered after the Gemini results were seen.

The check helps both models, in different ways (Table 3). Gemini rejects some large errors unaided. With the check, its corrupted acceptance falls from 85/180 to 72/180 while clean acceptance holds (88→90/90), so the joint rule is met. Qwen3-8B accepts nearly everything unaided (173/180 corrupted candidates). With the check, it follows the flag exactly: it accepts 0 of 120 flagged candidates and rejects 0 of 150 unflagged ones. Its discrimination gain is large, but so is its clean cost: it rejects the 3/90 clean candidates that 0d falsely flags and is uncertain on 3 more. Its clean-acceptance change is −0.067 [−0.111, −0.022], so its joint rule fails. Neither model ever rejected an unflagged candidate, and neither aided model beat acting on the flag directly. The aided decision therefore adds no detection beyond the flag in this setting. Gemini also overrides 17 of 120 flags, 14 of them on corrupted values.

The gains come from rejection and abstention, not correction: no aided model produced the true value for a corrupted candidate. Even with the check, 72/180 (Gemini) and 62/180 (Qwen) corrupted candidates were accepted. The flag itself misses 63/180, mostly at ×1.10, where 0d flags only 40/90. Gemini's count is higher because it overrides 14 flags on corrupted values.

## 4. Implications for the agent runtime

These results support a division of labor, which we state as a design hypothesis rather than a deployed system.

- **Provision evidence.** Within the tested check, signal depends on the row budget and its relevance (Table 2, Appendix A). The runtime already parses the tool call, so it could attach a query-matched sample to numeric returns.
- **Let the check drive the decision.** Given the check, both models converged to it, and neither exceeded it. An explicit policy on the flag makes the trade-off visible and tunable: re-query, abstain, or escalate on a flag. The clean cost is the flag's false-positive rate (3/90 here; 14/240 in Appendix A), and a model in the loop does not remove it.
- **Log for observability.** Recording flags with tool versions would let operators track flag rates across tool updates. We have not tested whether this attributes failures correctly.

End-to-end benefit depends on the response policy and on the threat. Under poison-once, a re-query after a flag would recover the answer; under persistent corruption, only the evidence check remains. We measured neither cost nor latency.

## 5. Limitations

The scope is scalar aggregates over six public tables, with one multiplicative corruption family that fires once. The intervention reuses 30 selected queries from the task pool. It tests upward errors only, with one completion per cell. Its three draws per query are not additional tasks, and its intervals rest on six table clusters. The two models use different sampling settings, so we make no model-comparison test. The intervention tests the whole check package; it cannot separate the warning text from the statistical content.

Public tables may appear in pretraining. Agent-intrinsic signals (verbalized confidence, mean token entropy) scored 0.46–0.56 within-table but lack live sanity controls. A clean-trained 0.5B scorer failed its gates (Appendix C). These results concern the instruments we built, not uncertainty quantification in general. A code-execution arm run for Gemini spans two sandbox versions, so it is excluded as a uniform comparison.

## 6. Related work

**Adoption of unreliable tool outputs.** ToxicBench [Tao and Yin, 2026] introduces corrupted-evidence adoption and recovery for data agents, including public-table evidence controls. Yang et al. [2026] find that many LLMs adopt plausible but incorrect outputs from search, sub-agent, and code tools. Kraishan [2026] finds that agents react to explicit errors more than to plausible wrong values, and that a "check each result" prompt does not close that gap. We add preview tiers with actual-exposure accounting, an evidence-budget sweep, and a monitor intervention.

**Runtime checks.** Outcome Monitors [Panthi and Abdelfattah, 2026] flag outputs that violate mined outcome contracts and report recovery gains. Kekatos et al. [2026] replay trajectories through a temporal-logic security monitor. Jegatheesan and Lihinikaduarachchi [2026] intercept math-tool results and compare verification designs. Among the methods we compared, none judges a returned number against the rows the agent saw, which is the check we measure.

**Intrinsic signals.** Xu et al. [2026] score inconsistent tool responses with content likelihood and action-distribution entropy for Qwen3-8B in a retail domain. That entropy differs from ours, so our weak intrinsic results do not bear on theirs. Bootstrap resampling is standard [Efron, 1979]; our contribution is the measurement, not a new algorithm.

## 7. Conclusion

Qwen adopts silently corrupted numeric returns in 97–99% of fired runs, and Gemini in 56%. Under the tested check, signal in the visible rows grows with the number of rows. When the check's output is given to the model, both models move toward it, and neither does better than acting on it directly; for Qwen, the gain also costs clean acceptance. For tool-using agents whose tools evolve, this points to numeric return verification as a runtime service whose explicit, logged flag drives the decision.

## References

Efron, B. (1979). Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics*, 7(1), 1–26. doi:10.1214/aos/1176344552.

Jegatheesan, K., and Lihinikaduarachchi, G. (2026). When Tools Lie: Reliability of Mathematical Agents Under Corrupted Tool Feedback. arXiv:2610.08097. MathAI Workshop at NeurIPS 2026.

Kekatos, N., Basagiannis, S., Chintri, M., Lekidis, A., Nianios, T., Seitoglou, I., Temperekidis, A., and Katsaros, P. (2026). Formal Runtime Verification for Tool-Using LLM Agents: An Offline Same-Benchmark Study on AgentDojo and STAC. arXiv:2610.09793. CPSIoTSec '26.

Kraishan, O. (2026). Loud Failures, Quiet Failures: Fault Detection and Recovery in Tool-Using Language Model Agents. arXiv:2610.10062.

Panthi, S., and Abdelfattah, R. (2026). Outcome Monitors: Recovery Affordances for Silent Tool Failures. arXiv:2608.19303.

Yang, H., Song, W., Kim, T., Song, J., Park, S., and Jo, Y. (2026). Agents' Overreliance on Unreliable Tools. arXiv:2609.05587 (v2).

Tao, Z., and Yin, C. (2026). When Tools Silently Lie: Evaluating and Mitigating Blind Compliance in Tool-Augmented Data Agents. arXiv:2609.37153 (v1).

Xu, J., Pedersen, T. B., Yao, Z., Zhang, X., and Li, Y. (2026). Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses. arXiv:2608.22676 (v2).

Dataset citations: Cortez (2008), Student Performance, doi:10.24432/C5TG7T; Cortez et al. (2009), Wine Quality, doi:10.24432/C56S3T; Fanaee-T (2013), Bike Sharing, doi:10.24432/C5W894; Horst et al. (2020), palmerpenguins, doi:10.5281/zenodo.3960218; Nash et al. (1994), Abalone, doi:10.24432/C55C7W; Quinlan (1993), Auto MPG, doi:10.24432/C5859H.

## Appendix A. Earlier twelve-query audit (fixed-return pilot)

Before Experiment A, a frozen pilot used twelve filtered-mean queries, two per table, under head5, random20 and matched20 evidence. Each query had one clean and one corrupted candidate, giving 72 responses per model. The two queries in each table used ×1.10 and ×1.50, so severity was tied to query. Changing from random20 to matched20 produced no stable gain in prompted acceptance discrimination. On the matched20 packets, 0d flagged 10/12 corrupted and 1/12 clean candidates. Over 20 fresh draws per query it flagged 161/240 corrupted and 14/240 clean. Gemini produced 67/72 strictly valid replies and Qwen 72/72. Invalid replies count as non-acceptances, and none were repaired.

<!-- BEGIN GENERATED:contrasts -->
| Model | Matched20 minus random20 | Descriptive 95% interval | Queries / tables |
|---|---:|---|---|
| gemini-3.8-flash | 0.083 | [-0.167, 0.333] | 12 / 6 |
| qwen3-8b | 0.000 | [-0.333, 0.333] | 12 / 6 |
<!-- END GENERATED:contrasts -->

<!-- BEGIN GENERATED:statistics -->
| Evidence | Check | Sanity AUROC | Within-table AUROC [95% interval] | Pooled AUROC | Corrupt flags | Clean flags | Unscorable (clean / corrupt) |
|---|---|---:|---|---:|---|---|---|
| Original matched20 | 0a | 0.958 | 0.583 [0.500, 0.667] | 0.583 | 2/12 | 0/12 | 0 / 0 |
| Original matched20 | 0d | 1.000 | 0.917 [0.833, 1.000] | 0.882 | 10/12 | 1/12 | 0 / 0 |
| 20 draws/query | 0a | 0.956 | 0.615 [0.529, 0.698] | 0.615 | 55/240 | 0/240 | 0 / 0 |
| 20 draws/query | 0d | 0.996 | 0.818 [0.718, 0.915] | 0.820 | 161/240 | 14/240 | 0 / 0 |
<!-- END GENERATED:statistics -->

<!-- BEGIN GENERATED:pilot -->
| Model | Context | Clean accept / 12 | Corrupted accept / 12 | Uncertain (clean / corrupt) | Invalid (clean / corrupt) |
|---|---|---:|---:|---|---|
| gemini-3.8-flash | head5 | 12 | 9 | 0 / 0 | 0 / 1 |
| gemini-3.8-flash | random20 | 12 | 7 | 0 / 1 | 0 / 1 |
| gemini-3.8-flash | matched20 | 11 | 5 | 0 / 0 | 1 / 2 |
| qwen3-8b | head5 | 12 | 10 | 0 / 2 | 0 / 0 |
| qwen3-8b | random20 | 10 | 9 | 2 / 3 | 0 / 0 |
| qwen3-8b | matched20 | 12 | 11 | 0 / 1 | 0 / 0 |
<!-- END GENERATED:pilot -->

Sanity gates by displayed-evidence condition. Real-corruption efficacy is reported only where the gate passes.

<!-- BEGIN GENERATED:gates -->
| Context | Check | Sanity AUROC | Paired queries / tables (sanity) | Real-corruption efficacy |
|---|---|---:|---|---|
| head5 | 0a | 0.792 | 5 / 3 | withheld |
| random20 | 0a | 0.885 | 12 / 6 | withheld |
| matched20 | 0a | 0.958 | 12 / 6 | eligible |
| head5 | 0d | 0.875 | 3 / 2 | withheld |
| random20 | 0d | 0.938 | 11 / 6 | withheld |
| matched20 | 0d | 1.000 | 12 / 6 | eligible |
<!-- END GENERATED:gates -->

The audit protocol was frozen before collection. The same-evidence statistical analysis was specified after the model outcomes were seen. The row-draw follow-up was locked before its draws were computed. All three are exploratory analyses of the same twelve queries.

## Appendix B. Row-draw severity slices

Subtle and plausible slices contain different queries, so their difference is not a within-query severity effect.

<!-- BEGIN GENERATED:severity -->
| Check | Query slice | Corrupt flags | Clean flags | Within-table AUROC [95% interval] |
|---|---|---|---|---|
| 0a | subtle | 0/120 | 0/120 | 0.500 [0.500, 0.500] |
| 0a | plausible | 55/120 | 0/120 | 0.729 [0.558, 0.896] |
| 0d | subtle | 50/120 | 5/120 | 0.692 [0.551, 0.841] |
| 0d | plausible | 111/120 | 9/120 | 0.949 [0.846, 1.000] |
<!-- END GENERATED:severity -->

## Appendix C. Head-five checks in agent trajectories and instrument diagnostics

On the head-five rows the agents actually saw, within-table AUROC was as follows. Qwen3-4B at T1: 0a 0.544, 0d 0.554, 0o\* 0.611 (events with at least one previewed row; 0d coverage 53%). Qwen3-8B at T1: 0a 0.533, 0d 0.535, 0o\* 0.565. These are descriptive. Head-five 0d sits at the edge of the sanity gate (0.945 in the T0 component of the sweep), so we do not headline it.

Verbalized confidence scored 0.527–0.558 and mean token entropy 0.455–0.488 within-table on the Qwen sets that have them. Neither has live extreme-corruption sanity controls, and two protocol versions of hypothesis H1 disagree on the primary severity slice, so no detector claim is made. Gemini reported confidence 100 in most runs. Its subtle-severity paired coverage (7/73 pairs) is too low for the registered test.

The clean-only quantile scorer (Qwen2.5-0.5B + LoRA, table-held-out) failed its high/low sanity checks and its clean-interval coverage window of [0.80, 0.98] on all six evaluation sets:

<!-- BEGIN GENERATED:scorer -->
| Cached scorer | Clean interval coverage | Gate | Common P+S tasks / tables | Real-corruption gain |
|---|---:|---|---|---|
| qwen3-4b_T0_agent | 0.167 | fail | 15 / 5 | withheld-scorer-gate-failed |
| qwen3-4b_T1 | 0.176 | fail | 15 / 5 | withheld-scorer-gate-failed |
| qwen3-4b_T1r2 | 0.183 | fail | 14 / 4 | withheld-scorer-gate-failed |
| qwen3-4b_T3 | 0.185 | fail | 0 / 0 | withheld-scorer-gate-failed |
| qwen3-8b_T0_agent | 0.176 | fail | 29 / 6 | withheld-scorer-gate-failed |
| qwen3-8b_T1 | 0.147 | fail | 29 / 6 | withheld-scorer-gate-failed |
<!-- END GENERATED:scorer -->

## Appendix D. Source datasets

<!-- BEGIN GENERATED:datasets -->
| Versioned CSV export | Rows | License | Dataset citation | SHA-256 prefix |
|---|---:|---|---|---|
| `public_penguins_v3.csv` | 344 | CC0 | [Horst et al. palmerpenguins](https://doi.org/10.5281/zenodo.3960218) | `f204db2c753b` |
| `public_auto_mpg_v4.csv` | 398 | CC BY 4.0 | [UCI 9, doi:10.24432/C5859H](https://doi.org/10.24432/C5859H) | `240f4657d747` |
| `public_bike_v4.csv` | 17379 | CC BY 4.0 | [UCI 275, doi:10.24432/C5W894](https://doi.org/10.24432/C5W894) | `e03de4ee4ef4` |
| `public_wine_quality.csv` | 6497 | CC BY 4.0 | [UCI 186, doi:10.24432/C56S3T](https://doi.org/10.24432/C56S3T) | `428bd8df7313` |
| `public_abalone.csv` | 4177 | CC BY 4.0 | [UCI 1, doi:10.24432/C55C7W](https://doi.org/10.24432/C55C7W) | `25f3dc964447` |
| `public_student.csv` | 649 | CC BY 4.0 | [UCI 320, doi:10.24432/C5TG7T](https://doi.org/10.24432/C5TG7T) | `5be7b02f13f5` |
<!-- END GENERATED:datasets -->

## Data, code, and disclosure

Protocols and dated amendments, raw trajectories, frozen pilot and Experiment A requests with all raw replies, scores, and generation scripts will be released in an anonymized artifact. Palmer Penguins is CC0; the five UCI tables are CC BY 4.0. AI coding assistants helped with code, evidence checks, and drafting; the authors verified all reported numbers against script output.
