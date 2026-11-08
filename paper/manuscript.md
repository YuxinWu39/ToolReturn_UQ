# Agents See the Rows but Accept the Number: The Case for Runtime Checks on Silently Corrupted Tool Returns

*Working manuscript, November 8, 2026 (revision 2: reframed for Trust4RSI-Agent @ AAAI 2027, 4-page short paper). Evidence cutoff: November 7, 2026. Anonymous submission draft. All reported outcomes already exist in the repository; generated tables are produced by `experiments/export_paper_evidence.py`.*

## Abstract

When an agent's tools and skills are updated, regressed, or swapped in a registry, a call can return a well-formed but wrong number. Because nothing raises an error, nothing triggers a retry. We ask where a check for such returns should sit in the agent stack. On 210 scalar queries over six public tables, the first numeric return is silently multiplied by a factor between 1.05 and 2 (or its reciprocal). Across 4,410 ReAct trajectories, Qwen3-4B and Qwen3-8B report the corrupted value in 97–99% of the runs where the corruption fired. They adopt it at the same rate whether or not they had previewed table rows. Gemini Flash adopts it in 56%. An offline sweep shows that default five-row previews are a weak basis for any checker: a bootstrap check that uses only the visible rows reaches within-table AUROC 0.62 at five random rows and 0.84 at two hundred. When the evidence is adequate, the remaining gap is in how it is used. On twelve audit queries shown with twenty query-matched rows, the same check flags 10/12 corrupted and 1/12 clean returns (AUROC 0.917; 0.818 over 240 fresh row draws). Prompted models shown the identical rows show no stable gain in accept/reject discrimination: +0.083 and 0.000, with both 95% intervals including zero. We argue that return verification belongs in the runtime. The system should supply query-relevant evidence and run an explicit check rather than rely on the model to verify itself.

## 1. Introduction

Agents that evolve gain and replace tools, rewrite skills, and depend on registries they do not control. Every such change can introduce a *quiet* failure: an analysis tool that returns a plausible scalar that is off by 10% or 50%. Unlike a crash or a schema error, a quiet numeric failure produces no signal that an agent's retry logic can act on. Recent audits find that tool-using agents largely accept such outputs [Tao and Yin, 2026]. The open systems question is who should catch them: the model reading the return, or a check in the layer that delivers it.

We study this question at the narrowest useful boundary, a single scalar returned by a pandas tool. We separate three things that are often conflated: (i) what the agent *does* with a corrupted return, (ii) how much *evidence* the agent's observation context actually contains, and (iii) whether a model *uses* that evidence when it is sufficient. Our contributions are:

1. **Behavior across preview tiers.** Across three models and four observation-context tiers (4,410 trajectories), agents adopt a silently corrupted scalar in 97–99% (Qwen) and 56% (Gemini) of fired runs. Previewing rows does not lower Qwen's adoption.
2. **Evidence budget.** An offline sweep over the number of visible rows k shows that a check using only the visible rows improves steadily from k=5 to k=200. Default head-five previews give any checker, human, model, or program, little to work with.
3. **Same-evidence gap.** With twenty query-matched rows, a twenty-line bootstrap check separates clean from corrupted returns well, but prompted models shown the same rows do not reliably improve.
4. **Runtime implication and negative instrument results.** We outline a return-monitor interface for the agent runtime. We also report that the agent-intrinsic signals we tried (verbalized confidence, token entropy) and a small learned scorer did not pass their own eligibility gates.

## 2. Setup

**Tasks and corruption.** We generate 210 scalar queries (unfiltered, filtered, and grouped aggregates) over six public tables of 344–17,379 rows (Appendix D). In a corrupted run the environment multiplies the first scalar return by s ∈ {1.05, 1.10, 1.20, 1.35, 1.50, 2.00} or 1/s. This is *poison-once*: re-issuing the call returns the true value. Source data is never modified.

**Agents and observation tiers.** A ReAct agent from ToxicBench [Tao and Yin, 2026] answers each query with a `python_exec` tool and an optional `preview` tool. The harness fixes what `preview` reveals: **T0** shows the first five rows plus whole-column min/max; **T1** shows the first five rows; **T3** shows the schema only. We run Qwen3-4B (T0, T1, a T1 replicate, T3) and Qwen3-8B (T0, T1) on vLLM at temperature 0.7, and Gemini 3.8 Flash at T1 with low reasoning effort. Each configuration has two clean seeds and one corrupted run per task. Adoption is the automatic `poisoned_answer_used` metric over runs where the corruption fired. For each run we reconstruct from the logs which rows the agent had actually seen before the corrupted call.

**Checks restricted to visible evidence.** Our threat model lets a checker use only what the agent saw plus the returned value; re-querying is excluded because under poison-once it trivially wins. The main check, **0d**, re-executes the agent's own statistic on bootstrap resamples of the visible rows and scores how far the return lies outside the 2.5–97.5% percentile interval (sums and counts are rescaled by n/k). **0a** is a range check. Two *privileged* references are computed from the full table by Monte Carlo: **0o\*** knows the sampling law of the k-row statistic but centers on the observed draw, and **0o** knows the population answer. They are reference scores for interpretation, not proven optimal detectors or information bounds. A method's real-corruption AUROC is reported only if it passes a sanity gate: AUROC above 0.95 against ×1000 and ÷1000 corruptions. The primary metric is within-table AUROC with a six-table bootstrap interval.

## 3. Results

### 3.1 Agents adopt corrupted scalars, with or without having seen the rows

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

**Table 1.** Adoption of the corrupted value among toxic runs where the corruption fired. "Rows previewed" means at least one data row was shown before the corrupted call.

Qwen adopts the corrupted value in nearly every fired run at every tier (Table 1). Seeing rows did not help. At T1, Qwen3-4B adopted it in 141/144 runs where it had previewed five rows and in 55/58 where it never previewed. At T0, where whole-column min/max were also shown, it adopted it in 140/141 previewed runs. Qwen3-8B always previewed and still adopted in 99% of runs. This is a stratification, not a randomized effect of previewing. Clean success was 182–204 of 210 per seed, so the failure is specific to the corrupted return, not general incompetence.

Gemini adopts less often (72/128). Two features of its runs limit the comparison. First, 93 of its 128 first corrupted outputs were not single scalars, so our scalar checks cannot score them. Second, 37 of its 50 recoveries had a later Python error, so some recoveries may come from retrying rather than from verification. Under poison-once, any retry returns the true value. We therefore treat Gemini as an external replication with a different evaluation unit, not as a stronger checker.

### 3.2 Default previews carry little evidence for any checker

<!-- BEGIN GENERATED:ksweep -->
| Check (within-table AUROC) | k=5 | k=10 | k=20 | k=50 | k=100 | k=200 |
|---|---:|---:|---:|---:|---:|---:|
| 0d bootstrap check (visible rows only) | 0.617 | 0.647 | 0.689 | 0.745 | 0.793 | 0.839 |
| 0o* privileged reference (knows k-row sampling law) | 0.724 | 0.739 | 0.774 | 0.826 | 0.870 | 0.896 |
| 0o privileged reference (knows population answer) | 0.793 | 0.811 | 0.856 | 0.906 | 0.931 | 0.957 |
| min sanity AUROC (0d, high/low) | 0.976 | 0.988 | 0.995 | 0.998 | 1.000 | 1.000 |
<!-- END GENERATED:ksweep -->

**Table 2.** Offline sweep on the 168 tasks computable at every k, with k random rows and 20 draws per task. 0d passes the sanity gate at every k. The privileged rows use full-table information that no visible-row checker has.

With k random rows, 0d rises steadily from 0.62 to 0.84 (Table 2). On the rows the Qwen agents actually saw in their trajectories, the head five, all visible-row checks stay between 0.53 and 0.62 (Appendix C). Head rows are also not a random sample. Default previews therefore leave little for *any* checker to work with, and weak detection under them does not show that agents ignore usable evidence. The gap between 0d and the 0o\* reference (0.11 at k=5) is a descriptive difference between two specified scores, not a decomposition into recoverable and unrecoverable information.

### 3.3 With adequate evidence, a program uses it and prompted models do not reliably

To isolate evidence *use*, we froze an audit set before collecting any responses. It has two filtered-mean queries per table (twelve in total), three displayed-evidence conditions (head5; random20, twenty random rows; matched20, twenty rows that satisfy the query filter), and a clean and a corrupted candidate for each. The two queries in each table use factors 1.10 and 1.50, respectively. Each model receives the query, the code, the displayed CSV, and the candidate, and must return a strict JSON accept/reject/uncertain decision without further tool calls. That gives 72 responses per model. The behavioral outcome is acceptance discrimination: the clean acceptance rate minus the corrupted acceptance rate, averaged within tables. The 0d check reads the exact CSV embedded in each frozen message.

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

**Table 3.** Top: change in prompted acceptance discrimination from random20 to matched20 (Appendix A gives per-cell decisions). Bottom: visible-row checks on the matched20 evidence, on the original frozen packets and over 20 fresh draws per query. Only the matched20 checks pass the sanity gate; the head5 and random20 checks fail it, and their efficacy is withheld (Appendix A).

Query-matched rows give the bootstrap check usable signal. On the frozen packets it flags 10/12 corrupted and 1/12 clean candidates. Over fresh draws, it flags 161/240 corrupted and 14/240 clean candidates, with per-query corrupted flag rates from 2/20 to 20/20. The prompted models do not convert the same rows into reliably better decisions. Gemini rejects more corrupted candidates under matched20 (5/12 accepted vs 7/12 under random20). Qwen does not: it accepts 11/12 under matched20 vs 9/12 under random20. Neither contrast excludes zero.

These measurements compare a structured program with a prompted model on identical rows, not at equal computational budget. 0d receives the parsed filter and performs 2,000 resamples, and the models answer in a single pass without code. That asymmetry is the point for system design: computation the runtime can run cheaply, with no model call, should not be delegated to the model's judgment.

## 4. Implications for the agent runtime

The results point to a division of labor in which return checking is a runtime service:

- **Evidence provisioning.** A checker can only be as good as its evidence (Table 2). The runtime, which already parses the tool call, can attach a query-matched row sample to each numeric return. Our matched20 condition does exactly this. A default head preview does not.
- **Explicit checks with a flag.** A cheap, interpretable check (here, bootstrap re-execution of the agent's own code) yields a per-return flag. This is a trigger for an action such as re-query, abstain, or escalate, not a correction.
- **Observability across tool evolution.** Logging the flag with the tool version lets operators attribute a shift in flag rates to a tool update, which fits continuous monitoring of evolving tool registries.

We have not deployed such a monitor end to end. Its benefit depends on the response policy. Under poison-once, a flag followed by a re-query would recover the answer. Under persistent corruption, only the evidence check remains. Its false-positive cost also matters: 14/240 clean flags in Table 3.

## 5. Limitations

The scope is scalar aggregates over six public tables, with one multiplicative corruption family that fires once. The audit set has twelve deterministically selected queries, with one response per model and cell. In it, severity is tied to query identity and direction to table, so neither has a causal reading. The six-table bootstrap intervals are descriptive. The two models also use different sampling settings. Public tables may appear in pretraining. Agent-intrinsic signals (verbalized confidence, mean action-token entropy) scored 0.46–0.56 within-table but lack live sanity controls, so their efficacy is withheld. A clean-trained 0.5B quantile scorer failed its sanity and coverage gates (Appendix C). These results concern the instruments we built, not uncertainty quantification in general.

## 6. Related work

**Adoption of unreliable tool outputs.** ToxicBench [Tao and Yin, 2026] introduces corrupted-evidence adoption and recovery for data agents, including public-table evidence controls. Yang et al. [2026] find that many LLMs adopt plausible but incorrect outputs from search, sub-agent, and code tools. Kraishan [2026] finds that agents react to explicit errors far more than to plausible wrong values, and that a "check each result" prompt does not close the gap. Our results agree with theirs and add the observation-tier axis, actual-exposure accounting, and an evidence-budget sweep.

**Runtime checks.** Outcome Monitors [Panthi and Abdelfattah, 2026] flag outputs that violate mined outcome contracts. Kekatos et al. [2026] replay trajectories through a temporal-logic monitor for security policies. Jegatheesan and Lihinikaduarachchi [2026] intercept math-tool results and compare verification designs. None of these judges a returned number against the data the agent actually saw, which is the check we measure.

**Intrinsic signals.** Xu et al. [2026] score inconsistent tool responses with content likelihood and action-distribution entropy for Qwen3-8B in a retail domain. Their action entropy differs from our token entropy, so our weak intrinsic results do not bear on theirs. Bootstrap resampling is standard [Efron, 1979]. We introduce no new algorithm; the contribution is the measurement and the systems argument it supports.

## 7. Conclusion

Agents accept silently corrupted numeric returns almost always, and previewing rows does not change that. Default previews contain too little evidence for any checker. When query-relevant evidence is present, a simple program extracts it, but prompted models do not reliably do so. For trustworthy evolution of tool-using agents, numeric return verification should be a runtime responsibility that combines evidence provisioning with an explicit, logged check.

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

## Appendix A. Audit-set decisions and sanity gates

Gemini produced 67/72 strictly valid replies and Qwen 72/72. Invalid replies count as non-acceptances in the primary analysis. Of Gemini's five invalid replies, three were complete JSON inside Markdown fences and two hit the length limit. None were repaired.

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

Protocols and dated amendments, raw trajectories, frozen audit requests with all 72 raw replies per model, scores, and generation scripts will be released in an anonymized artifact. Palmer Penguins is CC0; the five UCI tables are CC BY 4.0. AI coding assistants helped with code, evidence checks, and drafting; the authors verified all reported numbers against script output.
