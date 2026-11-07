# Round 12b — Scientific Critical Thinking Appraisal (post-Gemini, post-bug-fixes)

**Framework**: Scientific Agent Skills — Scientific Critical Thinking SKILL v1.5 (Kassis et al. 2026, arXiv:2609.00065)
**Date**: 2026-11-07
**Snapshot**: ToolReturn_UQ clean copy HEAD ecc4109; dev repo ToolReturnUQ HEAD fe76a81
**Prior reviews**: Round 10c (pre-Gemini critical thinking), rebase readiness review (collaborator 30a7825)
**Scope**: Q1–Q4 as posed, then 4-claim verdicts.

---

## Q1: Is the scope sufficient for a 4-page AAAI 2027 Trust4RSI-Agent workshop short paper?

### Sufficient

1. **Three agents across two families.** Qwen3-4B, Qwen3-8B (open, same family but different parameter counts) + gemini-3.8-flash (closed, different vendor, different architecture). This exceeds the one-agent or two-same-family scope of many workshop papers. The closed-source addition is the single largest scope improvement since round 10c.

2. **210 tasks on 6 public tables, pre-registered protocol.** The task set, corruption scheme (multiplicative aggregate_scale x1.05–2.0), and evaluation criteria were committed to git before runs. The amendment trail (A-P1 through A-P4-Gemini) is transparently logged. For a non-archival workshop that explicitly accepts negative results, this is above the methodological norm.

3. **Three signal families.** Zero-parameter range/re-execution (0a, 0d, 0o*), agent-intrinsic (verbalized confidence, token entropy), and learned (C3 scorer). The k-sweep provides a continuous offline reference. This covers the space the paper claims to survey.

4. **4,410 total trajectories** (3,780 Qwen + 630 Gemini) with machine-readable summaries, trajectory-level metrics, and published evaluation scripts. Sufficient for a workshop contribution.

5. **The venue explicitly accepts negative results.** Trust4RSI-Agent's CFP lists "Stability and Reliability of Agentic AI Systems" and negative/empirical findings. The C3 scorer failure and the signals-at-chance results are in scope.

### Thin

1. **Gemini coverage for signal evaluation is critically thin.** Only 35/128 first-poisoned returns are scalar under the existing parser. H5 (verbalized confidence on subtle) has 7 paired tasks from 3 tables. The AUROC CI [0.500, 0.667] spans chance to moderately informative — this is **underpowered** (Pitfall 9) and cannot support any directional claim about Gemini's signal quality. The paper must present Gemini's H5 as "insufficient data for the registered test" rather than as a confirmation or refutation.

2. **6 tables.** The k-sweep and all within-table CIs rest on 6 clusters. As round 10c noted (concern C2), a percentile bootstrap on 6 points has poor coverage properties. The CI [0.095, 0.130] for estimator loss at k=5 is narrower than justified by n=6. This is **pseudoreplication** (Pitfall 43) at the inferential level even though the bootstrap correctly identifies the cluster. Sufficient for a workshop; would be fatal for an archival venue.

3. **Qwen-only for the complete signal matrix.** Gemini lacks logprobs (no token entropy), and verbalized confidence is 100 in 711/731 replies (completely degenerate — see Q2b). So the full 3-signal comparison exists only for two same-family models. This limits the generalization claim to "Qwen models" for intrinsic signals.

4. **Single benchmark, numeric tools only.** ToxicBench with python_exec over CSV. No SQL, no API-call, no text-return tools. Disclosed in the plan but still a scope restriction a reviewer will name.

### Would be fatal if claimed

1. **"Gemini is more robust than Qwen."** Fatal. The 56% adoption rate (72/128) vs Qwen's 93% is confounded by: (a) 93/128 first returns are non-scalar — Gemini's output format is fundamentally different, not its reasoning; (b) 37/50 recoveries follow a Python error under poison_once, so the retry returns the true value, not a genuine verification; (c) sampling parameters differ (provider-default vs temperature 0.7). The named bias is **Confounding** (Pitfall 15) — output format, retry behavior, and sampling are confounded with agent identity. Any cross-model comparison must be restricted to the scalar-output subset with matched conditions, which has n=35 (too small for a claim).

2. **"Information capacity is a proven bound."** Fatal. As the collaborator's rebase review correctly argues, 0o* has no optimality proof. It bounds checkers that use the template statistic on observed rows and know the exact sampling law. 0r_log exceeds 0o* at large k because it uses the visible rows' spread (a different information set). The k-sweep is descriptive, not a theorem. Calling 0o* a "ceiling" or "bound" in a causal/theoretic sense is **Overgeneralization** (Fallacy 5) and **Confusing Descriptive with Explanatory** (Core Capability 7).

3. **"All agents never flag an anomaly."** anomaly_detection=0 across 4,410 trajectories rests on a keyword flag whose detection rule is not defined in any document I can find. If it's a grep for "anomaly" or "suspicious" in the agent's text, then it measures keyword use, not behavioral verification. Gemini made 55 subsequent-evidence calls (the `validation` field) and recovered in 50/128 cases. Claiming "zero anomaly detection" while Gemini demonstrably re-queried the tool is a **Definitional Ambiguity** — the keyword and the behavior measure different things.

---

## Q2: What is the paper's conclusion?

### Three candidate one-sentence conclusions, most to least defensible

**Rank 1 (most defensible):**
> "On 210 numeric data-analysis tasks across three LLM agents (two open-weight, one closed-source), all tested uncertainty signals — verbalized confidence, token entropy, and bootstrap re-execution — fail to discriminate corrupted from clean tool returns when the checker sees only the default 5-row preview (within-table AUROC ≤ 0.62 everywhere), while an offline k-sweep on random row subsets shows detection improves monotonically with sample size (0o* from 0.73 at k=5 to 0.90 at k=200)."

*What would break it:* A new signal achieves AUROC > 0.70 at head-5 on these same tasks without access to additional rows. This would show the ceiling is not inherent in head-5 but in the tested signals.

**Rank 2:**
> "Agent-intrinsic signals (verbalized confidence, token entropy) carry no detectable information about poisoned numeric tool returns regardless of model size or vendor, as both Qwen models and Gemini produce near-constant confidence scores that are uninformative by construction."

*What would break it:* A Fisher exact test on the multinomial confidence distribution (not AUROC) detects a shift at p < 0.01 for any agent. AUROC on a 3-value (Qwen) or 1-value (Gemini) signal has essentially zero power — the claim is supported by the instrument's insensitivity, not by absence of the phenomenon. Named bias: **Measurement Bias / Instrument Insensitivity** (Bias 12).

**Rank 3 (least defensible):**
> "Detection of corrupted tool returns is bounded by the information in the observation context, with a draw-conditioned oracle establishing the achievable ceiling."

*What would break it:* Already broken. The head-5 vs random-5 gap (0.58 vs 0.73 for 0o*) shows that row selection quality — not row count alone — determines achievable detection. 0r_log exceeds 0o* at large k. The collaborator correctly identifies 0o* as a "privileged reference" not a proven bound. And 4B's actual-exposure 0o* is 0.61–0.62 (CI to 0.69), not the previously reported 0.58.

### Resolution of the four named tensions

**(a) "Gemini is more robust" — or just outside the evaluation unit?**

Mostly outside. 93/128 first-poisoned outputs are non-scalar. Among scalar outputs: 26/35 adopted the poison (74%), which is lower than Qwen's 93% but on n=35. 37/50 recovery cases had a preceding Python error, meaning poison_once returned the true value on retry. The named bias is **Survivorship Bias** (Bias 9) — only the 35 scalar cases enter the Qwen-comparable evaluation unit, and these are not a random subsample of Gemini's behavior (they are the tasks where Gemini happened to produce scalar output). The defensible statement: "Gemini produced non-scalar first responses in 73% of exposed runs, preventing direct comparison; among the 35 scalar cases, adoption was 74% (n too small for a formal test). 37/50 recoveries co-occurred with a tool error under poison_once."

**(b) Gemini's verbalized confidence = 100 in 711/731: does this strengthen or weaken the null claim?**

It **strengthens the empirical pattern** (three agents, three flavors of uninformative: Qwen4B mode 80, Qwen8B mode 95, Gemini mode 100) but **does not strengthen the inferential claim**. A constant signal has AUROC = 0.5 by definition, not by evidence — you cannot distinguish "the signal carries no information" from "the signal is unmeasurable because there is no variance." Named issue: **Trivially True Null** (related to Pitfall 2 — absence of evidence). The paper should say: "Verbalized confidence was uninformative for all three agents: Qwen models produced heavily quantized responses (85% of mass on 3 values) and Gemini responded 100 in 97% of cases, making AUROC degenerate by construction. The pattern is consistent with — but does not prove — the claim that agents do not encode observation quality in their verbalized confidence."

**(c) Can the paper say "detection is bounded by information in the observed context"?**

No, not as a theoretical claim. What it CAN say:

> "Among the tested signals, detection performance on the default head-5 preview did not exceed within-table AUROC 0.62 for any agent (0o* on actual-exposure events: 0.56–0.62 for Qwen, coverage 48–100%). An offline k-sweep on random row subsets shows the draw-conditioned oracle reference (0o*) rising from 0.73 at k=5 to 0.90 at k=200, establishing that **more representative row samples improve detection for the template-statistic family**. The 0.11–0.15 gap between random-5 and head-5 reflects row ordering effects (Bike hourly-sorted, Wine red-then-white), not information quantity alone. 0o* is a reference for the template-statistic class, not a proven Bayes-optimal bound: 0r_log uses visible-row spread (a different information set) and exceeds 0o* at large k."

**(d) "All three agents never flag an anomaly" — what does anomaly_detection=0 mean?**

It means the keyword-based flag in the evaluation harness found zero instances of the agent explicitly mentioning anomaly/suspicious/unexpected (or whatever the detection rule is — the definition is not in findings.md, PREREGISTRATION.md, or the plan). It does NOT mean agents never re-queried, never showed hesitation, or never recovered. Gemini made 55 subsequent-evidence calls (validation field). The paper should define what anomaly_detection measures in one sentence (the grep rule or equivalent), report it, and separately report the validation/recovery/subsequent-call counts. Claiming "agents never challenged a poisoned return" while Gemini's subsequent-evidence rate is 43% (55/128) is **Equivocation** (Fallacy 21 — using one word for two meanings).

---

## Q3: Is it sufficient — genuinely non-obvious measured facts vs intuitive-but-now-measured?

### Genuinely non-obvious (a careful reader could NOT have predicted these)

1. **The head-5 vs random-5 gap is 0.15 AUROC for 0o* (0.58 vs 0.73).** Most researchers would expect "5 rows is 5 rows." The fact that which 5 rows you see matters as much as how many is not intuitive and has direct implications for tool-preview design (randomize the sample, don't show the head).

2. **Seeing the preview does not change agent compliance.** 4B T0_agent: 140/141 used poison when they saw the preview, 55/58 when they didn't (98.6% vs 94.8%). Agents that looked at 5 rows and the column min/max complied at the same rate as agents that saw nothing. This is non-obvious — one would expect the additional context to at least weakly reduce compliance.

3. **The estimator loss (0o* - 0d ≈ 0.11 at k=5) is almost entirely in filtered/grouped queries.** Unfiltered mean/median: 0d 0.68, 0r_log 0.71, 0o* 0.73 (gap 0.05). Filtered: gap 0.11. This means the bottleneck for detection isn't the statistical estimation — it's the filter/group mismatch between what the query selects and what the 5 head rows happen to contain.

### Intuitive-but-now-measured (expected direction, value in the quantification)

1. **Agents blindly follow poisoned returns (83–93%).** Expected from ToxicBench's own results (26–39pt success drop) and Loud/Quiet Failures (2610.10062). The quantification with a noise floor (4.3%) and across tiers/models is the contribution, not the direction.

2. **Verbalized confidence is uninformative.** Multiple prior papers (Confidence Laundering 2606.20662, Outcome-Grounded Calibration 2610.18614, VoS 2610.09115) have shown confidence signals are weakly calibrated or uncalibrated for agents. The three-model pattern (constant or near-constant) confirms this but doesn't surprise.

3. **Detection improves with more visible rows.** That seeing more data helps a range check is statistically obvious. The value is in the decomposition (estimator loss vs oracle knowledge) and the specific curve shape, not the direction.

---

## Q4: The "too intuitive" risk — strongest reviewer objection and one-paragraph defense

### Strongest objection

"The paper measures things everyone already knows: agents trust tool returns, confidence signals are useless, and seeing more data helps detection. The k-sweep is standard statistics (more data → better estimates). The two Qwen models are the same family, the benchmark is one tool type, and the scorer failed its own sanity check. Where is the contribution beyond confirming prior expectations?"

### One-paragraph defense (using only supported claims)

The contribution is not the direction of these results but three specific measured quantities that were not predictable from prior work and have immediate design implications. First, the head-5 vs random-5 gap: at identical row counts, detection drops by 0.15 AUROC (from 0.73 to 0.58) solely because the default preview shows the first rows rather than a random sample — this means tool-preview API design, not signal sophistication, is the first-order lever for improving observation-level trust. Second, preview exposure has zero effect on agent compliance: agents that examined five rows plus column statistics adopted the poison at the same 98–99% rate as agents that skipped the preview entirely, ruling out the hypothesis that more context enables self-correction. Third, the estimator-loss decomposition shows that 0.11 AUROC of signal is recoverable from the same 5 rows 0d already sees, concentrated in filtered/grouped queries where 5 head rows rarely contain the filter value — identifying the specific mechanism (filter-value coverage, not statistical estimation) as the bottleneck for external detection. These three findings were not claimed by any of the 40+ papers in the related work and each maps to an actionable recommendation.

---

## 4-Claim Verdicts

### Claim 1: Blind compliance (83–93% across all context tiers, zero anomaly-detection challenges)

**Verdict: SUPPORTED WITH SCOPE**

The compliance rate is directly measured, replicated across two Qwen models and four tiers (T0_agent/T1/T1r2/T3), noise-floor-controlled (2.9–5.2%), and robust. The Gemini data adds a third agent at T1 with 56% adoption conditional on firing (72/128), though confounded by output format. The "zero anomaly-detection challenges" sub-claim requires defining what anomaly_detection measures; Gemini's 55 subsequent-evidence calls and 50 recoveries contradict a blanket "never challenged" reading.

**Allowed sentence:** "Both Qwen models accepted and used poisoned numeric returns in 83–93% of exposed runs across all tested context tiers, with the keyword-based anomaly-detection flag at zero in 4,410 trajectories; Gemini adopted the poison in 56% of exposed runs (72/128) but 73% of its first poisoned outputs were non-scalar, limiting direct comparison."

### Claim 2: Signals at chance on head-5

**Verdict: SUPPORTED WITH SCOPE**

Every tested signal achieves within-table AUROC ≤ 0.62 at head-5 for all agents (0a ≤ 0.58, 0d ≤ 0.56, verbalized ≤ 0.56, entropy ≤ 0.50). After the exposure fix, 4B's 0o* on actually-seen rows reaches 0.61–0.62 (CI to 0.69, coverage 48%), so "≤ 0.58 for everything" is no longer accurate. H1(verbalized) for 4B misses by 0.01. Gemini's H5 has 7 valid pairs (insufficient). The scope restriction is: (a) "at chance" means AUROC < 0.62 not literally 0.50, and the instrument (AUROC on quantized data) has low power; (b) 0o* on actual-exposure events for 4B reaches 0.62, which is above the pre-correction claim of 0.58.

**Allowed sentence:** "Under the default head-5 preview, no tested signal — including the draw-conditioned oracle reference on actual-exposure events — exceeded within-table AUROC 0.62 for any agent, with most at 0.50–0.56; the oracle reference on random 5-row subsets achieves 0.73, indicating the head-5 gap is partly a row-quality effect."

### Claim 3: Context information as the limiting factor

**Verdict: SUPPORTED WITH SCOPE (descriptive only; NOT as a causal or theoretic bound)**

The k-sweep shows monotonic improvement from k=5 to k=200 on random rows. The 0o*/0d decomposition separates estimator loss (0.11) from oracle knowledge (0.06). But: (a) 0o* has no optimality proof and is exceeded by 0r_log at large k; (b) the head-5 vs random-5 gap confounds row count with row quality; (c) the 6-table CI is approximate. The claim must be descriptive: "among the tested checkers and reference signals, detection tracks the amount and representativeness of visible context," not "information bounds detection."

**Allowed sentence:** "On random k-row subsets, the draw-conditioned oracle reference 0o* rises monotonically from 0.73 (k=5) to 0.90 (k=200), and the bootstrap re-execution check trails by ~0.11 at k=5, primarily in filtered/grouped queries; however, 0o* is a reference for the template-statistic class, not a proven information-theoretic bound, and the 0.15 gap between random-5 and head-5 shows row representativeness matters alongside row count."

### Claim 4: Failure taxonomy (55% noise-corrected observation failures)

**Verdict: SUPPORTED**

McNemar test on 737 duplicate keys: clean-clean discordance 4.3%, excess toxic-failure 18.7pp [15.1, 22.3]. Noise-corrected observation share 0.55 overall, 0.43 numerical. Methodology sound, replicated on the ToxicBench original data with the exposure fix not affecting taxonomy (taxonomy uses task-level outcomes, not event-level scores). Gemini adds a new failure mode: non-scalar output preventing evaluation in 73% of exposed cases.

**Allowed sentence:** "After correcting for a 4.3% run-to-run noise floor, 55% of excess toxic failures on ToxicBench's existing paired trajectories are observation-caused (the agent would have succeeded with a clean return), with 43% in the numerical family."

---

*This review was guided by the Scientific Critical Thinking SKILL v1.5 appraisal workflow and the named biases (Pitfalls 2, 9, 15, 43; Biases 9, 12; Fallacies 5, 21, 34), statistical pitfalls, and logical fallacies therein. No files were modified except this report.*
