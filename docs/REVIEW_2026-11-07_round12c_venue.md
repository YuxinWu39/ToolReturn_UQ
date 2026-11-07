# Round 12c — Workshop Venue Review and Submission Plan

**Reviewer**: independent workshop reviewer (round 12c)
**Date**: 2026-11-07
**Snapshot**: ecc4109 (read-only)
**Venue**: AAAI 2027 Workshop on Trustworthy Evolution of AI Agents (Trust4RSI-Agent)
**Format target**: 4-page short paper, double-blind, non-archival, deadline 2026-11-20 AoE

---

## 1. Dennett-Rule Restatement

In my own words, the paper would claim:

When an LLM data-analysis agent receives a single corrupted numeric value from a tool (the tool's returned scalar is silently multiplied by 1.05–2×), nothing the agent or an external checker can see — not the returned number compared to the few visible table rows, not the agent's own verbalized confidence, not its token-level entropy, not a small learned scorer — reliably distinguishes the corrupted return from a legitimate one, provided the agent's observation context is the default head-5 rows of the table.

The paper shows this through 4,410 trajectories (3,780 Qwen + 630 Gemini) on 210 tasks across 6 public tables:
- Agents adopt the corrupted value in 83–93% of poisoned runs with zero challenges (Qwen) and 56% adoption conditional on firing for Gemini (with confounding from non-scalar output format and tool errors).
- Every tested signal — range checks (0a), bootstrap re-execution (0d), draw-conditioned oracle (0o\*), verbalized confidence, token entropy, and a 0.5B learned scorer — sits between 0.47 and 0.62 AUROC on the head-5 observation context.
- An offline k-sweep shows detection rises monotonically with visible rows: bootstrap 0d goes from 0.62 at k=5 random rows to 0.85 at k=200; the draw-conditioned oracle 0o\* goes from 0.73 to 0.90. The ~0.11 gap between 0d and 0o\* at k=5 is "estimator loss" — signal left in the rows that the bootstrap does not extract. The ~0.06 gap between 0o\* and the population oracle 0o is knowledge of the true answer that no k-row-limited checker can recover.
- A 30-member leave-one-table-out scorer (Qwen2.5-0.5B + LoRA) trained on ~1,800 clean examples scores 0.50–0.52 on every eval set: it learned column scale (~6× precision) but not the statistic within the 10–50% resolution that these poison magnitudes require. This is a pre-registered negative result.

The mechanism proposed is that the head-5 rows of a sorted/ordered file are not representative of the column's distribution, and no tested signal can compensate for this representativeness deficit.

---

## 2. Scores (4-page short paper at Trust4RSI-Agent)

| Criterion | Score | Justification |
|-----------|-------|---------------|
| **Quality** | 3.5/5 | 3,780+630 trajectories with pre-registered protocols; three scoring bugs found and fixed with full before/after disclosure; however, two model families only, one corruption type, and six tables. |
| **Clarity** | 2.5/5 | No paper draft exists — findings.md is 400+ lines of versioned lab-notebook prose with superseded findings left inline; README headlines are stale post-correction; a reader would struggle to extract the clean story without significant rewriting. |
| **Significance** | 3.0/5 | Directly relevant to the workshop's Topic 2 (tool interfaces, verification) and Topic 5 (observability, auditing); practical negative result for runtime monitoring design. Limited by scope (numeric-only, multiplicative-only, tabular data). |
| **Originality** | 3.5/5 | No prior work compares multiple UQ signals at the tool-return boundary with a controlled observation-context axis. The k-sweep decomposition (0d/0o\*/0o) is a novel analytical device. However, "agents trust bad tool outputs" is well-established (ToxicBench itself, Overreliance 2609.05587, Loud/Quiet Failures 2610.10062). |

**Acceptance probability: 55–60%** at this workshop. Rationale: (a) workshop explicitly welcomes negative results; (b) tool-interface verification is a named topic; (c) the observation-budget axis is novel; (d) the main risk is that reviewers may view the scope (six tables, one corruption type, two same-family models) as too narrow for even a 4-page paper. The Gemini addition partially addresses the model-diversity concern.

---

## 3. Gemini Verdict: RAISES Probability (Conditionally)

**Verdict: RAISES** the acceptance probability from ~50% (Qwen-only) to ~55–60% (with Gemini), but only if presented correctly.

**Why it helps:**
- Breaks the "single model family" objection — the most predictable reviewer complaint
- 56% adoption (vs 83–93% Qwen) is an interesting calibration point: less blind compliance under this model+format combination, but still majority-adopting
- The 97% verbalized-confidence-equals-100 finding is striking and independently interesting
- H5 not confirmed on 7 paired tasks provides another honest negative-result data point

**Why it's dangerous if mishandled:**
- 93/128 first poisoned outputs are non-scalar → the zero-parameter signals cannot score them → the evaluation unit differs fundamentally from the Qwen experiments
- 37/50 recovery cases involved a Python error under poison_once → recovery may be retry-driven, not verification-driven; conflating these inflates apparent agent competence
- H5 has 7 paired tasks from 3 tables — statistically meaningless for a standalone claim
- Different sampling parameters (low reasoning effort, no custom temperature, no seed) make the comparison confounded

**How the paper must present Gemini:**
1. **As an external replication with a different evaluation unit**, not as a direct comparison row in the main results table. The scalar coverage (35/128 = 27%) must be prominently disclosed.
2. **Report adoption conditional on firing AND on scalar format separately**: 26/35 scalar adoption vs 46/93 non-scalar adoption. The non-scalar results cannot use the same signal suite.
3. **Recovery must be stratified**: 37/50 recoveries had tool errors → only 13/50 are potentially intentional verification. State this.
4. **H5 goes to the appendix** with the full table of 7 tasks. Do not claim confirmation or non-confirmation in the abstract; say "insufficient coverage for the registered test."
5. **Frame as boundary of the evaluation unit**: "our signal suite assumes scalar returns; Gemini's output formatting pushes most returns outside this assumption, revealing a scope boundary."

---

## 4. Four-Page Budget

### Section Budget (4 pages AAAI format ≈ 3,200 words body)

| Section | Space | Content |
|---------|-------|---------|
| **1. Introduction** | 0.5 page | Motivation (agents trust tool returns), gap (no systematic signal comparison at the observation step with context control), contribution summary (5 claims below) |
| **2. Setup** | 0.5 page | ToxicBench + 6-table extension, threat model (single multiplicative corruption, poison_once), 3 agents (4B, 8B, Flash), tiers (T0_agent, T1), signal definitions (0a, 0d, 0o\*, verbalized, entropy, scorer) in a compact table |
| **3. Results** | 1.5 pages | **Figure 1** + **Table 1** + **Table 2** + prose connecting them |
| **4. Related Work** | 0.5 page | 4 nearest papers + positioning |
| **5. Discussion & Limitations** | 0.5 page | Scope (numeric, tabular, multiplicative, 6 tables, 2+1 models, poison_once), honest scorer failure, what the k-curve means for runtime monitor design |
| **References** | ~0.5 page (excluded from count per CFP) | ~15–20 references |

### Figure (1 only)

**Figure 1: Detection AUROC vs. observation budget (k visible rows)**
- X-axis: k ∈ {5, 10, 20, 50, 100, 200}
- Y-axis: within-table AUROC
- Lines: 0d (bootstrap), 0o\* (draw-conditioned oracle), 0o (population oracle, dashed)
- Points: actual agent T1 results for 4B, 8B, Flash (at k=5, head rows, marked distinctly from random-k)
- Annotation: the 0.11 estimator-loss gap and 0.06 oracle-knowledge gap at k=5
- Source: k-sweep from F4''' (offline, 210 tasks × 20 draws × 6 tables)

### Tables (2 only)

**Table 1: Agent behaviour and signal performance at T1 (head-5)**

| | Qwen3-4B | Qwen3-8B | Gemini Flash |
|---|---|---|---|
| Trajectories | 630 | 630 | 630 |
| Poison fired / toxic | 202/210 | 196/210 | 128/210 |
| Adopted / fired | 196/202 (97%) | 194/196 (99%) | 72/128 (56%) |
| Scalar coverage | ~70% | 100% | 27% |
| 0a (range check) | 0.54 | 0.53 | — |
| 0d (bootstrap) | 0.55 | 0.53 | — |
| 0o\* (oracle) | 0.61 / 0.57¹ | 0.57 | — |
| Verbalized (P+S) | 0.55 FAIL | 0.53 PASS | insuff. |
| Mean entropy | 0.46 | 0.49 | N/A |
| Scorer | 0.50 | 0.51 | — |

¹ 4B actual-exposure / protocol denominator. Gemini dashes = insufficient scalar events for the signal suite.

**Table 2: Failure taxonomy (Qwen, noise-corrected)**

| Category | Share | Definition |
|----------|-------|------------|
| Observation (consumed) | 55% | Clean succeeds, toxic fails, agent used poisoned value |
| Capability | 40% | Clean also fails |
| Unexposed / no effect | 5% | Poison didn't fire or agent recovered |

### What goes to appendix/repo (not in 4 pages)

- F0 (data inventory), F1' (noise floor details), F2/F2'/F2''/F2''' (original-table range check evolution)
- F3/F3' (large-table ceiling, superseded)
- F4/F4'/F4''/F4''' full decomposition tables (k-sweep by op, direction, severity)
- F8 full scorer training details (30 members, sanity rows, calibration)
- F9 Gemini full breakdown (recovery stratification, non-scalar analysis)
- All pre-registration amendments (A-P1 through A-P4-Gemini)
- H1 per-tier per-model decision table
- Before/after correction table (F5/F6/F7 correction section)

### 5 Claims That Fit (in order)

1. **C1: Blind compliance is near-universal under default observation context.** Qwen agents adopt corrupted values in 92–97% of fired-poison runs with zero challenges; Gemini adopts in 56% (but 73% of its returns are non-scalar). No agent re-queried or flagged a suspicious return across 4,410 trajectories.

2. **C2: All tested detection signals are at or near chance on head-5 rows.** Zero-parameter checks (0a, 0d) ≤ 0.56, agent-intrinsic signals (verbalized, entropy) ≤ 0.56, learned scorer 0.50–0.52, and even the draw-conditioned oracle 0o\* reaches only 0.57–0.62, all within-table on the agent's actual observation context.

3. **C3: Detection tracks visible-context representativeness, not signal choice.** The offline k-sweep shows 0d rising from 0.62 (k=5 random) to 0.85 (k=200), and 0o\* from 0.73 to 0.90. Head-5 performs worse than random-5 because the file's row order is non-representative.

4. **C4: The gap decomposes into estimator loss (0.11) and irrecoverable oracle knowledge (0.06).** At k=5, 0o\*−0d ≈ 0.11 is signal the bootstrap leaves on the table; 0o−0o\* ≈ 0.06 is knowledge of the population answer no k-row checker can have.

5. **C5 (negative): A clean-only predictive scorer fails at the required resolution.** The 0.5B scorer learns column scale but not the statistic within 10–50%: AUROC 0.50–0.52 against a pre-registered prediction of [0.55, 0.70].

### Claims from findings.md that must NOT appear in 4 pages

- **"Information capacity ceiling"** framing: the rebase readiness review (P1) correctly notes 0o\* is a specific privileged reference, not a proven Bayes-optimal bound. Use "empirical detection curve" and "privileged reference" instead.
- **Head-5 vs random-5 causal claims**: the 0.03 shift when restricting to actual-exposure events changes task composition; cannot claim a causal effect of seeing rows in 4 pages without the full stratification.
- **H6 (observation vs capability UQ signal difference)**: only 25 subtle observation pairs; exploratory and underpowered.
- **0b (z-score) claims**: labelled a leak at T0/T1 on small tables; adds confusion without space to explain.

---

## 5. Three Most Likely Reviewer Objections

**Objection 1: "Six tables and one corruption type — how do I know this generalizes?"**
> Answer: "We test 210 tasks spanning 344–17,379 rows with 12 symmetric log-ratio scales on 6 public tables from 4 domains. The k-sweep shows detection is a monotone function of visible rows across all 6 tables (within-table CI ±0.015 at each k). The corruption type (multiplicative scaling) is the continuous-severity type in ToxicBench; discrete corruptions (label swap, sign flip) are structurally different and disclosed as out of scope."

**Objection 2: "Two Qwen models from one family — maybe a different architecture would detect corruption."**
> Answer: "We add Gemini 3.8 Flash (different architecture, different training, different provider) and observe 56% adoption with 97% of confidence reports being exactly 100. The detection signals we test (range check, bootstrap, confidence) are model-external or model-intrinsic measurements on the observation; the k-sweep ceiling (0o\*, computed without any model) shows the bound is in the data, not the model."

**Objection 3: "The negative results are unsurprising — of course 5 rows aren't enough to detect a 5% perturbation."**
> Answer: "The contribution is not that 5 rows are insufficient (which is indeed intuitive for statisticians) but that: (a) the default observation context of a production benchmark and real agents is exactly this regime; (b) agents never request more rows or challenge the return (0 of 4,410 trajectories); and (c) the precise decomposition (0.11 estimator loss + 0.06 oracle knowledge at k=5) quantifies what additional rows would buy, which is actionable for runtime monitor design."

---

## 6. Venue Decision

**Recommendation: Submit 4-page short paper to Trust4RSI-Agent @ AAAI 2027.**

Reasons:

| Factor | Trust4RSI-Agent 4p (Nov 20) | ICLR 2027 Workshop (Feb 1) |
|--------|---------------------------|---------------------------|
| Topic fit | ★★★★★ Tool interface verification is a named topic; negative results explicitly welcomed | ★★★ Agent UQ is relevant but ICLR workshops lean toward methods/models |
| Non-archival | Yes — can resubmit an expanded version anywhere | Yes for most ICLR workshops |
| Deadline | 13 days — tight but feasible with existing experiments and no new runs needed | ~85 days — allows more experiments but delays publication signal |
| Model diversity | Sufficient for a 4p workshop paper with 2+1 models | ICLR reviewers may demand 3+ diverse models |
| Speaker relevance | Yoshua Bengio (AI safety), Yue Zhao (USC, anomaly detection) — alignment with our framing | Unknown |
| Acceptance rate | ~50–60% for workshops accepting negative results | ~40–50% for competitive ICLR workshops |
| 8-page option | Available but not recommended — current material fits 4p and 8p would require new experiments to fill without padding | N/A until CFP |

**Do not submit 8-page full.** The current evidence (2+1 models, 1 corruption type, 6 tables) fills a strong 4-page paper but would feel thin at 8 pages. An 8-page version should add: (a) a third open-weight family (e.g., Llama), (b) discrete corruption types, or (c) a successful lightweight detector — none of which can be completed by Nov 20.

**Do not wait for ICLR 2027 workshop.** The field is moving fast (4 new papers in 4 days per round 10a); non-archival publication at Trust4RSI-Agent establishes priority without preventing a stronger ICLR submission later. The 85-day gap to ICLR creates scooping risk with no countervailing benefit.

---

## 7. Punch List (by 2026-11-20 AoE)

### Title
**Detecting Corrupted Numeric Tool Returns Under Limited Evidence**

### Abstract (≤150 words)

> When an LLM agent receives a corrupted numeric value from a data-analysis tool, can it or an external checker tell? We study this under controlled observation budgets: agents see only the first five rows of a table before the tool returns a scalar. Across 4,410 trajectories on 210 tasks from six public tables, three agents (Qwen3-4B, Qwen3-8B, Gemini Flash) adopt the corrupted value in 56–97% of poisoned runs, with zero instances of requesting additional evidence. We compare six detection signals — range checks, bootstrap re-execution, verbalized confidence, token entropy, a draw-conditioned oracle, and a learned scorer — finding all at or near chance (AUROC 0.47–0.62) on the default five-row context. An offline sweep over observation budgets shows detection rises monotonically with visible rows, decomposing into recoverable estimator loss (~0.11) and irrecoverable oracle knowledge (~0.06) at five rows. These results quantify the cost of limited evidence for runtime tool-output monitors.

(148 words)

### Figure Spec
- **Figure 1**: Detection AUROC vs. k visible rows (k ∈ {5,10,20,50,100,200}). Three curves (0d, 0o\*, 0o dashed). Agent T1 points overlaid. Shaded 6-table bootstrap CI. Annotation arrows for the two gap components. Single-column width. Generated from ksweep2.py output.

### Table Specs
- **Table 1**: Agent behaviour + signal AUROC at T1 (3 models × ~8 rows). As specified in §4.
- **Table 2**: Failure taxonomy (3 rows: observation/capability/other, with noise-corrected shares). Compact.

### Related Work Paragraph (4 nearest papers)

The related-work paragraph must name and position against these four papers:

1. **ToxicBench** (Tao et al., 2609.37153): Introduced the corruption benchmark and blind-compliance measurement. We extend it with a controlled observation-budget axis, systematic signal comparison, and an external replication. ToxicBench measures whether agents comply; we measure whether anything can detect the corruption and how detection varies with context.

2. **Robustness Analysis of Agentic AI** (Xu et al., 2608.22676): Tests two signals (schema likelihood, context likelihood) against inconsistent and incomplete tool responses in one domain. We test six signal families across a continuous severity range with an observation-budget axis that their work does not vary.

3. **SSCBench** (He et al., 2610.11514): Evaluates whether fault-injection evidence is visible to the agent before the faulty action. We operationalize "visibility" as a concrete row-count budget with measured detection curves, complementing their binary visible/invisible classification.

4. **What the Trace Shows and What the Label Says** (Adeniji et al., 2610.30491): Audits behavioral detectors in agent evaluation, finding that trace metrics and outcome labels can diverge. Our paired clean/toxic design provides ground-truth failure-source labels (observation vs. capability), and the Gemini recovery-vs-retry distinction illustrates their concern about label fidelity.

### Remaining Production Tasks

| Task | Est. hours | Dependency |
|------|-----------|------------|
| Write 4-page LaTeX draft (AAAI format) | 8–10 | None (all experiments done) |
| Generate Figure 1 from ksweep2.py output | 1 | matplotlib script |
| Format Tables 1–2 | 1 | Existing scored data |
| Anonymize repo link for supplementary | 1 | Create anonymous GitHub/OpenReview |
| Write appendix (pre-registration summary, Gemini details, scorer details) | 3 | None |
| Proofread + double-blind check | 2 | Draft complete |
| Submit on OpenReview | 0.5 | All above |
| **Total** | **~17 hours** | Feasible in 13 days |

---

## Summary

| Item | Value |
|------|-------|
| Quality | 3.5/5 |
| Clarity | 2.5/5 |
| Significance | 3.0/5 |
| Originality | 3.5/5 |
| Acceptance probability (4p workshop) | **55–60%** |
| Gemini effect | **RAISES** probability (~+5–10pp) if presented as replication with scope boundary, not as a direct comparison |
| Recommended venue | Trust4RSI-Agent 4-page short, Nov 20 |
| Abstract | 148 words (see §7) |
| Figure | 1 (AUROC vs k) |
| Tables | 2 (behaviour+signals; taxonomy) |
| Claims | 5 (C1 blind compliance, C2 all signals near chance, C3 context-representativeness mechanism, C4 gap decomposition, C5 scorer negative) |
| Production estimate | ~17 hours |
