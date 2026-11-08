# Visible Evidence and Statistical Checks for Corrupted Numeric Tool Returns

*Working manuscript, November 8, 2026. Evidence cutoff: November 7, 2026. Authors and affiliations pending. Venue-neutral author draft; not submitted. All reported outcomes already exist in the repository.*

## Abstract

A numerically plausible tool return can remain incorrect even when an agent sees relevant source rows. We examine how displayed evidence relates to checking behavior in a controlled audit of scalar table queries. Twelve filtered-mean queries from six public tables receive three evidence conditions and paired clean or multiplicatively corrupted returns. Gemini Flash and Qwen3-8B each produce 72 responses. Changing twenty random rows to twenty query-matching rows yields acceptance-discrimination contrasts of 0.083 [−0.167, 0.333] and 0.000 [−0.333, 0.333], respectively. These exploratory intervals do not establish a stable benefit. A bootstrap check applied to the exact original matching-row packets achieves equal-table AUROC 0.917 [0.833, 1.000], flagging 10/12 corrupted and 1/12 clean returns. With twenty additional row draws per query, its query/draw-mixture AUROC is 0.818 [0.718, 0.915], with 161/240 corrupted flags and 14/240 clean flags. Those draws add no model responses or independent queries. The results identify statistical signal available to a tested program in the selected evidence while leaving its reliable use by prompted models unresolved. They support separating evidence exposure, checking procedures, and observed decisions; they do not establish a detection bound or an internal model mechanism.

## 1. Introduction

An agent answering a table question may execute correct code and still receive an incorrect scalar from the tool interface. A well-formed number offers no execution error to trigger a retry. The source rows visible beside that number could support an independent check, but the existence of those rows does not establish that the agent uses them effectively.

Tool-return corruption and checking already have direct precedents. ToxicBench studies adoption and recovery under altered tool evidence, including controlled evidence conditions [Tao and Yin, 2026](https://arxiv.org/html/2609.37153v1). Return-boundary signals have also been studied using content likelihoods and legal-action distributions [Xu et al., 2026](https://arxiv.org/html/2608.22676v2). Our question concerns a narrower empirical distinction: does changing the displayed row sample produce reliable checking behavior, and can a specified statistical program extract signal from that same sample?

We organize the study around two measurements. The first records prompted decisions when the model receives a fixed query, tool code, partial table evidence, and scalar candidate. The second scores candidates with checks restricted to the displayed rows. A subsequent row-draw study examines the statistical check across fresh samples of the same selected queries. It does not provide another model replication.

This design yields an empirical case study of evidence exposure and evidence use. It also makes several boundaries visible: relevant rows may be sparse in a random sample; a structured program has different representation and computation from a prompted model; and an instrument that fails a sanity check cannot support a general conclusion about the absence of useful uncertainty signals. We report those boundaries alongside the measured outcomes.

## 2. Study design

### 2.1 Queries, source data, and corruption

The source pool contains 210 tasks on six public tables: Abalone, Auto MPG, Bike Sharing, Palmer Penguins, Student Performance, and Wine Quality. The fixed-return pilot selected two distinct filtered-mean queries per table by a deterministic rule. Each query required at least twenty matching rows with finite target values, a positive finite full-table mean, and a perturbation separated from the numerical scoring tolerance. Selection followed the existing task order and excluded duplicate column/filter combinations. The resulting twelve queries are a selected set, not a random sample of analytical tasks. Dataset citations and versioned export sizes appear in Appendix D.

Let \(\theta_q\) be the full-table filtered mean for query \(q\). The clean candidate is \(\theta_q\); the corrupted candidate is \(s_q\theta_q\). One selected query per table uses a factor of 1.10 or its reciprocal, termed *subtle*; the other uses 1.50 or its reciprocal, termed *plausible*. Direction alternates by table. Thus severity is tied to query identity and direction to table identity. Neither comparison identifies a causal effect of corruption magnitude or direction.

The source table remains unchanged. A frozen JSON packet carries the candidate as its sole numeric value. Queries, code, row indices, source hashes, candidate values, message hashes, and request order are recorded in a model-independent manifest. This fixed-return task measures an explicitly requested audit at the tool boundary. It does not measure whether a free-running agent spontaneously chooses to verify.

### 2.2 Displayed evidence

Each query has three conditions:

- **head5:** the first five rows in original table order;
- **random20:** twenty rows sampled uniformly without replacement from the full table;
- **matched20:** twenty rows sampled uniformly without replacement among query-matching rows with finite target values.

Evidence includes the displayed CSV rows, schema, full-table shape, and a description of the sampling rule. Clean and corrupted candidates for a query/context use identical evidence and differ only in the delivered scalar. The conditions change both row content and the sampling-rule description; head5 additionally differs in sample size. Matched20 versus random20 therefore concerns relevance under a fixed displayed row count, not a pure intervention on context length. The provider knows the query filter to construct matched20; it does not supply the population mean to the checker.

### 2.3 Models, response format, and outcomes

The archived model identifiers are `gemini-3.8-flash` and `qwen3-8b`. Each receives all twelve queries, three evidence conditions, and two candidates, giving 72 completed responses per model. Gemini uses low reasoning effort and provider-default sampling. Qwen uses temperature 0.7, seed 0, and disabled thinking through the served chat template. Each request permits 2,048 output tokens. These sampling settings differ and do not constitute equal computational budgets.

The prompt forbids another tool call or full-table access and requires a strict JSON decision (`accept`, `reject`, or `uncertain`), integer confidence in the supplied scalar's correctness, a finite numerical answer or null, and a reason. Invalid outputs remain in the primary denominator and do not count as acceptances. Valid-pair sensitivity results remain archived. A null answer represents abstention from a numeric response; it is not automatically evidence that the model detected a corruption.

For query \(q\), context \(c\), and candidate label \(l\), let \(A_{qcl}\) indicate an `accept` decision. Acceptance discrimination is \(D_{qc}=A_{qc0}-A_{qc1}\). The primary behavioral contrast averages \(D_{q,\mathrm{matched20}}-D_{q,\mathrm{random20}}\) within each table, then equally across tables. A model that stops accepting clean values can therefore lose discrimination even if it accepts fewer corrupted values. This outcome differs from AUROC and is not a detector-quality estimate from the confidence field.

### 2.4 Statistical checks on the same displayed rows

The offline checks parse the exact CSV embedded in each frozen message and verify the evidence hash. They receive the query target/filter and displayed table metadata, but no source-table path, truth, corruption label, model decision, or full matching-population count. Ground truth is used only for evaluation and constructing sanity candidates.

The sample-range check, **0a**, measures whether the candidate lies outside the finite matching values' displayed range. This sample range is not a full-population bound. The primary bootstrap check, **0d**, reuses the repository's established nonparametric resampling procedure. Bootstrap resampling is a standard technique [Efron, 1979](https://doi.org/10.1214/aos/1176344552); the present work introduces no new bootstrap algorithm.

For each query/context, 0d resamples the entire displayed row frame with replacement at its displayed size 2,000 times, applies the filtered-mean operation, and caches the 2.5th and 97.5th percentiles \([L,U]\). Resamples without a defined statistic fail; the check is unscorable if more than 20% fail. The same cached interval is reused for all candidates of that query/context. For finite \([L,U]\), the score is

\[
S(y)=\frac{\max(L-y,\;y-U,\;0)}{U-L+0.01(|L|+|U|)/2+10^{-9}}.
\]

A candidate is flagged when its score exceeds \(10^{-9}\). Compatibility means that this check did not flag the value; it does not certify correctness. The program uses structured query information and substantial additional computation. Equality of displayed rows therefore does not imply equal representation, computation, or cost across the program and models.

### 2.5 Eligibility gates and descriptive uncertainty

For each statistical method/context, synthetic sanity candidates multiply or divide the clean value by 1,000. The registered gate requires equal-table AUROC strictly above 0.95 for clean versus the combined extreme candidates, on common support. High-only and low-only diagnostics are also archived. Real-corruption efficacy is withheld when the gate fails; an undefined score is not converted into a neutral score. Passing this gate does not establish interval calibration or a controlled false-positive rate.

Primary statistical performance is the equal-weight mean of per-table AUROCs on complete same-query candidate pairs. Pooled AUROC is secondary. Both-class constant scores contribute AUROC 0.5. Intervals use 2,000 bootstrap resamples of the represented table scores, with seed 1, and are descriptive because there are only six selected table clusters. They do not provide a population-generalization guarantee. No equivalence or multiplicity-adjusted significance claim is made.

The context pilot was frozen before collection. The same-evidence statistical follow-up was specified after inspecting the model outcomes, and the row-draw follow-up was locked before its draws/checks were computed. These are exploratory analyses of reused queries, even though their respective procedures were committed before execution. A separate cached H1/P5 audit was retrospective.

## 3. Results

### 3.1 Relevant rows did not establish stable cross-model checking gains

Table 1 reports observed decisions with all twelve candidate conditions retained per cell. Gemini produced 67/72 strictly valid replies and Qwen 72/72. Of Gemini's five invalid outputs, three contained complete JSON within Markdown fences and two ended with the `length` finish reason. Scoring did not repair these outputs or replace them with new samples.

**Table 1. Prompted checking decisions.** Clean/corrupted acceptance uses all twelve query conditions as denominator. Rejections are the remaining decisions after acceptance, uncertainty, and invalidity. A corrupted acceptance matched the delivered wrong value in these archived cells.

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

Gemini's corrupted acceptances decreased from 9/12 under head5 to 5/12 under matched20, while one matched20 clean response became invalid. Qwen's corrupted acceptances were 10/12, 9/12, and 11/12 across head5, random20, and matched20. These cell counts alone do not isolate an evidence-use mechanism.

**Table 2. Primary behavioral contrast.** The contrast is the equally weighted table mean of matched20-minus-random20 changes in clean-minus-corrupted acceptance. Positive values favor matched20. Invalid replies remain nonacceptances in the primary analysis.

<!-- BEGIN GENERATED:contrasts -->
| Model | Matched20 minus random20 | Descriptive 95% interval | Queries / tables |
|---|---:|---|---|
| gemini-3.8-flash | 0.083 | [-0.167, 0.333] | 12 / 6 |
| qwen3-8b | 0.000 | [-0.333, 0.333] | 12 / 6 |
<!-- END GENERATED:contrasts -->

Both intervals include zero and effects in either direction. We therefore do not establish a stable benefit across the two tested models. These results do not establish equivalence, prove that extra context has no effect, or identify a reversed primary effect between models. The two systems also use different sampling configurations.

### 3.2 The original matched20 packets contain extractable statistical signal

Both checks passed the registered sanity gate under matched20. On those exact packets, 0d flagged 10/12 corrupted values and 1/12 clean values, with equal-table AUROC 0.917 [0.833, 1.000]. The sample-range check flagged 2/12 corrupted values and no clean values. These results establish usable ranking signal for specified programs on this selected evidence. They do not prove that the displayed samples uniquely determine the full-table answer.

**Table 3. Eligible statistical checks.** Original matched20 uses one frozen sample per query. The row-draw mixture uses twenty additional samples per query and has no corresponding new model outputs. Counts describe flags at the fixed threshold; intervals apply to equal-table AUROC. All listed rows passed their respective sanity gates.

<!-- BEGIN GENERATED:statistics -->
| Evidence | Check | Sanity AUROC | Within-table AUROC [95% interval] | Pooled AUROC | Corrupt flags | Clean flags | Unscorable (clean / corrupt) |
|---|---|---:|---|---:|---|---|---|
| Original matched20 | 0a | 0.958 | 0.583 [0.500, 0.667] | 0.583 | 2/12 | 0/12 | 0 / 0 |
| Original matched20 | 0d | 1.000 | 0.917 [0.833, 1.000] | 0.882 | 10/12 | 1/12 | 0 / 0 |
| 20 draws/query | 0a | 0.956 | 0.615 [0.529, 0.698] | 0.615 | 55/240 | 0/240 | 0 / 0 |
| 20 draws/query | 0d | 0.996 | 0.818 [0.718, 0.915] | 0.820 | 161/240 | 14/240 | 0 / 0 |
<!-- END GENERATED:statistics -->

The model and statistical outcomes should be read with their different decision rules intact. A statistical flag and a prompted rejection can trigger different actions, and the study deploys neither as an end-to-end policy. The contrast establishes a case in which a known computation extracts information from the displayed evidence while prompted model checking remains unreliable; it is not an equal-budget method comparison or a claim of statistically established algorithmic superiority.

### 3.3 The statistical signal varies across row draws and queries

The row-draw follow-up sampled twenty matching finite-target rows without replacement, independently for each of twenty draws per selected query. Draws can overlap. The evidence provider loaded the full source to sample; the check received only each frozen twenty-row packet. The follow-up contains 240 query/draw units, 1,920 score events across two checks and four candidate roles, and still twelve queries in six tables.

For 0d, the query/draw-mixture equal-table AUROC was 0.818 [0.718, 0.915]. It flagged 161/240 corruptions and 14/240 clean values, leaving 79/240 corrupted candidates compatible. Per-query corrupted flags ranged from 2/20 to 20/20. The subtle-query slice had 50/120 corrupted flags and the plausible-query slice 111/120; because the slices contain different queries, this difference does not identify the effect of perturbation size. The full slice results appear in Appendix B.

The original 0.917 estimate conditions on the initial sample, whereas 0.818 describes a mixture over additional draws of the same selected queries. Their difference is not a measured bias or a formal performance-drop estimate. No Gemini or Qwen reply was collected for these additional samples, and the original replies were not reused against changed evidence.

## 4. Interpretation and limitations

The fixed-return study separates evidence exposure from checking outcomes. Its most direct positive result is narrow: a tested statistical procedure obtains ranking signal from selected matching-row evidence. The prompted-model contrasts do not establish reliable benefits from replacing random rows with matched rows. Together these observations make a blanket explanation based solely on unavailable evidence inadequate for this particular study. They leave open whether the model difficulty comes from representation, computation, calibration, task interpretation, sampling variation, or prior knowledge.

Public tables and recognizable schema names may have appeared in model training. Reasons sometimes refer to population-level quantities; an explanation alone cannot identify their origin or prove reliance on displayed rows. A fresh-table intervention comparing raw rows with statistics computed from those same rows would test a representation/computation aid. It would require its own protocol, query-level crossing of perturbation magnitude, clean and extreme controls, and explicit prompt/cost accounting. It is proposed work, not a result of this study.

The main scope is positive scalar filtered means under one synthetic multiplicative corruption family. It excludes multivalue outputs, semantic or schema corruption, persistent adversarial tools, and policy decisions about safe tool execution. Twelve deterministically selected queries offer limited heterogeneity; twenty row draws do not create twenty new tasks. Only one completion per model/cell was collected. A six-table bootstrap is descriptive and may miss uncertainty from model sampling, task selection, and unseen domains.

Neither sample ranges nor the percentile intervals establish finite-population coverage. The observed 14/240 clean flags should not be represented as a guaranteed operating point. The fixed threshold was not tuned on these row-draw outcomes. Zero observed flags in another condition do not establish a zero-error guarantee.

Earlier project analyses investigated confidence, action-token entropy, and a clean-trained quantile scorer. Intrinsic scores lack the required live extreme-corruption sanity controls, and H1 protocol versions disagree on their primary severity slice. The learned scorer instances failed their own sanity and clean-interval coverage gates. We keep those as instrument/protocol diagnostics in Appendix C rather than use them to argue that uncertainty quantification generally fails. Likewise, full-table Monte Carlo reference scores used in earlier analyses have no proved optimality and do not define an information ceiling or an identifiable recoverable-information decomposition.

The fixed-return audit forbids another tool call and has no runtime accept/retry/abstain controller. Earlier free-running trajectories allow clean re-querying after one-shot corruption and answer a different recovery question. The present study measures no deployment improvement, net error cost, or latency advantage.

## 5. Related work

[Tao and Yin (2026)](https://arxiv.org/html/2609.37153v1) introduce ToxicBench and distinguish corrupted-evidence adoption, checking, and recovery. Appendix E.2 already includes matched-parent public-table evidence controls and partial versus full target corruption. Our contribution therefore concerns the audit of displayed row samples, explicit statistical checks, and repeated row draws, rather than the discovery of corrupted-return adoption itself. Their controlled subsequent-evidence setting and our one-shot fixed-return judgments have different research units.

[Xu et al. (2026)](https://arxiv.org/html/2608.22676v2) score a retail domain with Qwen3-8B using schema/full-prefix content likelihood and legal-next-action distributions. Their action entropy differs from our historical mean token entropy, and their evidence conditions differ from the table-row intervention here. Low performance of the latter cannot refute the former. Both cited 2026 works are arXiv preprints; this manuscript makes no claim about their peer-review status beyond that record.

The statistical check uses an established resampling approach [Efron, 1979](https://doi.org/10.1214/aos/1176344552). Its role is an interpretable evidence-extraction comparator. The empirical audit, including failed gates and coverage, is the contribution; a new detector architecture is not introduced.

## 6. Conclusion

On twelve selected table queries, changing random displayed rows to matching rows did not establish a stable cross-model gain in prompted acceptance discrimination. A bootstrap program extracted statistical signal from the original matching-row packets, and signal remained observable across additional row samples of the same queries. Query-specific misses and clean false flags persisted. These results support evaluating visible evidence, checking procedures, and decisions separately, while leaving reliable model use and broader generalization unresolved.

## Data, code, and development disclosure

Source provenance and licenses are recorded in `data/ours/datasets/PROVENANCE.json`: Palmer Penguins is CC0 and the five UCI sources are CC BY 4.0. Original fixed-return replies, provider metadata, frozen requests, scores, and audit hashes are archived; raw consistency checks are not independent attestation of model weights. The selected-query manifest is shared across models. Offline scoring reads displayed CSV packets only. Protocol history, amendments, analysis code, and unresolved hypothesis status are retained in the repository.

Codex assisted with code, evidence checking, and manuscript drafting. Human authors must verify the manuscript and adapt the disclosure to the eventual venue's policy. Procedural evidence appraisal used Scientific Agent Skills [Kassis et al., 2026](https://doi.org/10.48550/arXiv.2609.00065), cited as a development resource rather than evidence for the study's empirical claims. No additional evaluation-model requests were made for this draft.

## References

Efron, B. (1979). Bootstrap Methods: Another Look at the Jackknife. *The Annals of Statistics*, 7(1), 1–26. [doi:10.1214/aos/1176344552](https://doi.org/10.1214/aos/1176344552).

Kassis, T., Agarwal, V., He, Y., Patel, D., and Brueckner, A. M. (2026). Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents. *arXiv preprint*, 2609.00065. [doi:10.48550/arXiv.2609.00065](https://doi.org/10.48550/arXiv.2609.00065). Latest record checked November 8, 2026.

Tao, Z., and Yin, C. (2026). When Tools Silently Lie: Evaluating and Mitigating Blind Compliance in Tool-Augmented Data Agents. *arXiv preprint*, 2609.37153, version 1. [Full text](https://arxiv.org/html/2609.37153v1).

Xu, J., Pedersen, T. B., Yao, Z., Zhang, X., and Li, Y. (2026). Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses. *arXiv preprint*, 2608.22676, version 2. [Full text](https://arxiv.org/html/2608.22676v2).

Cortez, P. (2008). Student Performance [Dataset]. UCI Machine Learning Repository. [doi:10.24432/C5TG7T](https://doi.org/10.24432/C5TG7T).

Cortez, P., Cerdeira, A., Almeida, F., Matos, T., and Reis, J. (2009). Wine Quality [Dataset]. UCI Machine Learning Repository. [doi:10.24432/C56S3T](https://doi.org/10.24432/C56S3T).

Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning Repository. [doi:10.24432/C5W894](https://doi.org/10.24432/C5W894).

Horst, A. M., Hill, A. P., and Gorman, K. B. (2020). palmerpenguins: Palmer Archipelago (Antarctica) Penguin Data. [doi:10.5281/zenodo.3960218](https://doi.org/10.5281/zenodo.3960218).

Nash, W., Sellers, T., Talbot, S., Cawthorn, A., and Ford, W. (1994). Abalone [Dataset]. UCI Machine Learning Repository. [doi:10.24432/C55C7W](https://doi.org/10.24432/C55C7W).

Quinlan, R. (1993). Auto MPG [Dataset]. UCI Machine Learning Repository. [doi:10.24432/C5859H](https://doi.org/10.24432/C5859H).

## Appendix A. Gates across the original evidence conditions

The four head5/random20 method/context combinations fail the registered sanity gate. Real-corruption efficacy and cross-context statistical performance contrasts are therefore withheld. Both matched20 methods pass. Parent-context gates also apply to severity slices; a favorable slice cannot bypass a failed parent gate. Failed conditions remain in the artifact, including unscorable counts.

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

## Appendix B. Row-draw severity slices

These are different selected queries, not within-query perturbation interventions. The plausible-slice perfect or near-perfect values and any degenerate empirical intervals describe observed cases only. Per-query counts and exact row indices are available in the archived follow-up.

<!-- BEGIN GENERATED:severity -->
| Check | Query slice | Corrupt flags | Clean flags | Within-table AUROC [95% interval] |
|---|---|---|---|---|
| 0a | subtle | 0/120 | 0/120 | 0.500 [0.500, 0.500] |
| 0a | plausible | 55/120 | 0/120 | 0.729 [0.558, 0.896] |
| 0d | subtle | 50/120 | 5/120 | 0.692 [0.551, 0.841] |
| 0d | plausible | 111/120 | 9/120 | 0.949 [0.846, 1.000] |
<!-- END GENERATED:severity -->

## Appendix C. Historical instrument diagnostics

The quantile scorer used clean-only training with table-held-out evaluation. None of the six saved configurations met its high/low sanity and clean coverage requirements. Its interval-coverage eligibility window was [0.80, 0.98]. The cached audit enumerated same-task finite common support with 0d and the restricted analytic reference, but withheld the real-corruption gain because the scorer gate failed. The result concerns this configuration, not a learned-method family. Both-class constant tables now contribute AUROC 0.5; metadata and returned values are checked before joining saved scores.

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

Historical H1 rules differ: the earlier decision specified subtle returns and AUROC plus AUPRC, whereas the later amendment described a plausible-plus-subtle upper-AUROC-CI rule as unchanged. Both slices are reported retrospectively in the cached audit; no global H1 confirmation is retained. For Gemini, subtle confidence has only 7/73 scalar pairs in three tables, with diagnostic AUROC 0.556 [0.500, 0.667]. Its absence of token logprobs and missing live sanity prevent a complete intrinsic detector comparison.

Confidence was defined as confidence in the candidate's correctness. Ten valid Gemini rejections nevertheless had confidence 95 or 98, which conflicts with that definition and is compatible with confidence in the decision instead. We do not flip or reinterpret those scores after observing outcomes. Qwen's archived replies now permit direct verification of its strict parsing and decisions; this resolves the earlier archive gap without adding observations.


## Appendix D. Source datasets

Sizes describe the versioned CSV exports used here, rather than a repository webpage's aggregate instance count. Full hashes and provenance are retained in the data archive.

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
