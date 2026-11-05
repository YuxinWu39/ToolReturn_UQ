# Round 8 — Acceptance Calibration Review

**Reviewer**: rigor-reviewer / devil's advocate / simulated ICLR-workshop area chair
**Date**: 2026-11-02
**Scope**: Full project state including F0-F8 (C3 scorer NEGATIVE), two open-weight agents (Qwen3-4B, Qwen3-8B), 3,780 trajectories, P4/P5 pre-registrations and outcomes. Question: is this publishable at a top-venue workshop?

---

## Method note

All numbers below are either independently recomputed from raw JSONL files using `experiments/.venv/bin/python` with `sklearn.metrics.roc_auc_score`, or read directly from the logs/findings with the source identified. The scorer eval files use a `label` field (0=clean, 1=poisoned) with `surprise` as the scorer score. Git ordering verified via `git merge-base --is-ancestor`. Protocol and findings texts read in full.

---

## Verdict

| Venue | Acceptance probability | One-sentence justification |
|-------|----------------------|---------------------------|
| **ICLR 2027 Agent Reliability Workshop (6-8p, Feb 1)** | **0.40-0.50** | A systematic negative result with a mechanism (information-capacity curve) on an unoccupied evaluation unit, with honest pre-registration and rigorous protocol; weakened by only 2 same-family open models, 1 benchmark, and no positive C3 result. At the workshop accept-rate boundary. |
| **AAAI MATH4AI (4p, Nov 20)** | **0.25-0.35** | The mathematical content (oracle decomposition, information-capacity bound) is real but thin for a math-focused venue; the paper is fundamentally an empirical study of agent reliability, not a mathematical contribution. Below the typical accept rate. |

---

## A. Protocol adherence

### Git ordering ✓
```
12595dc  P5 protocol (2026-11-01 12:32:39 -0800)  ←  BEFORE
75af363  P5 results  (2026-11-01 22:25:06 -0800)  ←  AFTER
```
`git merge-base --is-ancestor 12595dc 75af363` → YES. Protocol-before-results maintained throughout the project. All 7 prior rounds verified this; round 8 confirms it holds for the C3 scorer as well.

### Pre-registered predictions

| Prediction | Committed | Observed | Hit? |
|-----------|-----------|----------|------|
| P5: scorer AUROC at T1 in [0.55, 0.70] | 12595dc | 0.50 [0.49, 0.52] | **MISS** (below range) |
| A-P3d: 0o*-0d at k=5 in [0.03, 0.10] | 5e978bb | 0.111 [0.095, 0.130] | **Marginal miss** (point above, CI lower in range) |
| A-P4: H1 verbalized upper CI < 0.60 | P4 protocol | 4B: 0.61 (miss by 0.01); 8B: 0.57 (pass) | **Split** |
| G2 at T1: expected to fail by hit-rate bound (0.84) | A-P3 | max zero-param 0.58 (confirmed fail) | **HIT** |
| Blind compliance >50% | implicit | 83-93% across all | **HIT** (dramatically so) |

Assessment: Two clean misses (P5 scorer, A-P3d marginal), both honestly reported. The P5 miss is the larger finding — the scorer failed its own sanity rules, not just the detection bar.

---

## B. Spot-checks

### B1. Compliance rates (recomputed from raw toxic_seed0.jsonl)

| Model/Tier | Recomputed | F5/F7 claims | Match? |
|-----------|-----------|-------------|--------|
| 4B/T1: pau | 196/210 = 93.3% | 196/210 (93%) | ✓ |
| 4B/T1: anom | 0 | 0 | ✓ |
| 4B/T0_agent: pau | 195/210 = 92.9% | 195 | ✓ |
| 8B/T1: pau | 194/210 = 92.4% | 194 (92%) | ✓ |
| 8B/T1: anom | 0 | 0 | ✓ |
| 8B/T0_agent: pau | 175/210 = 83.3% | 175 (83%) | ✓ |
| 8B/T0_agent: poison_fired | 176 | 176 | ✓ |

All compliance numbers reproduce exactly.

### B2. Scorer AUROC (recomputed from eval_*_scorer.jsonl)

| Eval set | F8 claims within-table | Recomputed within-table | Match? |
|---------|----------------------|------------------------|--------|
| 4B T1 | 0.503 [0.49, 0.52] | 0.5028 | ✓ (within rounding) |
| 8B T1 | 0.505 [0.49, 0.52] | 0.5047 | ✓ |
| 4B T1 sanity s_hi | 0.847 | 11.682 (raw score, not AUROC) | ⚠ different metric |

Note: The scorer eval logs report sanity as AUROC (0.847), while the raw JSONL stores the raw surprise score. The log's 0.847 is the AUROC of s_hi values against the label, computed by score_scorer.py. This is below the 0.95 hard rule — **sanity FAIL confirmed**.

### B3. Clean coverage (recomputed)

| Set | F8 claims | Recomputed | Match? |
|-----|----------|-----------|--------|
| 4B T1 | 0.18 | 34/193 = 0.176 | ✓ |
| 8B T1 | 0.15 | 29/197 = 0.147 | ✓ |

Coverage 0.15-0.18 vs the P5 requirement of 0.80-0.98: **catastrophic miscalibration confirmed**. The scorer's 90% prediction intervals contain only ~17% of clean values.

### B4. Scorer surprise direction (recomputed)
Mean surprise: clean 3.462, poisoned 3.428 (4B T1). Clean events are *more* surprising than poisoned — the scorer's error dominates. **F8's claim "clean events get higher median surprise" confirmed.**

---

## C. Story coherence

**The question**: Is a paper where the main proposed solution (C3 scorer) failed still a workshop paper, or does it read as "we tried things and nothing worked"?

**Assessment: The story is coherent, but only if framed correctly.**

The paper's story after C3's failure:

1. **Behavioural finding** (strong): agents blindly follow bad returns 83-93% of the time with 0 challenges across 3,780 trajectories, across all context tiers. This alone is publishable as a workshop finding — it quantifies the gap identified qualitatively by APEX-Agents/Loud-Quiet/ToxicBench.
2. **Signal comparison** (strong as negative result): all signal families — zero-parameter checks, agent-intrinsic confidence/entropy, and a clean-trained learned scorer — are at chance under the default head-5 observation context. This is C1.
3. **Mechanism** (the differentiator): the information-capacity curve (0o* 0.73@k5-random → 0.90@k200, vs 0d 0.62→0.85) explains *why* everything fails at head-5: the observation context doesn't contain enough information. The estimator loss (0.11 at k=5) shows there IS recoverable signal in those rows, but the scorer couldn't access it.
4. **C2 taxonomy** (supporting): 95% of failures are observation-failures (bad data), not capability-failures (agent incompetence).

**The risk**: A reviewer who reads this as "negative result paper" will say "we knew agents are bad with tools, what's new?" The paper must lead with the *mechanism* (observation-context information is the ceiling) and position the negative results as evidence for that claim, not as the findings themselves.

**Coherence verdict**: 7/10. The mechanism saves it from being a pure negative, but the paper needs a strong lead paragraph making the information-capacity argument the central contribution, with the comprehensive signal failures as supporting evidence.

---

## D. Ranked reviewer objections with honest answers

### D1. Only 2 open models, same family (Qwen3-4B, Qwen3-8B), no closed model
**Severity: HIGH**
**Honest answer**: H5 (closed-source control) is registered but not run — gpt-5.4-mini needs an API key the authors don't have yet. The two Qwen models are the same architecture at different scales, so "consistent across agents" really means "consistent across model sizes of one family." This is the single weakest point.
**In the artifact?** Listed as pending in the plan's drop order and in F7 as "gpt-5.4-mini (API key)". Partially addressed by the ToxicBench trajectories (gpt-5.4-mini, claude-sonnet-4-6, haiku) in F0/F1, but those are on the original 4-12-row tables, not the P3 tasks.
**Would a reviewer accept the answer?** Marginally, for a workshop. The blind compliance finding is so strong (83-93%) that model-family diversity matters less for C1; it matters more for the intrinsic-signal hypothesis H1.

### D2. One benchmark, numeric tools only
**Severity: HIGH**
**Honest answer**: The scope is explicitly "numeric tool returns" and env-2 was dropped from the minimum viable set. This is an honest scope limitation, not an overclaim. The real question is whether the mechanism (information-capacity ceiling) generalizes beyond numbers — and the paper cannot answer it.
**In the artifact?** Yes, in the plan's Limitations section: "Scope: numeric-return tools; quantify fraction of real tool returns that are numeric using ToolBench/API-Bank tool-type distributions."
**Would a reviewer accept?** For a workshop, yes — workshops expect focused scope. For a main venue, no.

### D3. Scorer is undertrained (1.8k examples, 0.5B, 3 epochs), so the negative result is weak
**Severity: MEDIUM-HIGH**
**Honest answer**: This is the strongest objection against the C3 negative. The scorer's catastrophic miscalibration (17% coverage, x6 magnitude error) could plausibly be fixed with more data, a larger backbone, or a residual target (predict deviation from 0d, not the raw value). F8 lists these as P5b candidates. The training loss converged and per-table correlation is up to 0.94, so the model *learns the scale* — it just doesn't have the resolution for 1.1-2x poisons.
**In the artifact?** F8 states this honestly: "Not tested here (would be P5b, requires a protocol amendment first): more data, a larger backbone, a target that predicts the deviation from a zero-parameter estimate."
**Would a reviewer accept?** A charitable reviewer says "the negative result is informative about the difficulty of the task." A skeptical one says "train it properly before claiming nothing works." For a workshop: marginal. The paper should frame C3 as "the naive scorer fails; we enumerate why and what P5b would need," not as "learned scorers can't work."

### D4. Harness normalizations changed the benchmark
**Severity: MEDIUM**
**Honest answer**: Without normalizations, Qwen3-4B gets FileNotFoundError on ~95% of tasks (clean success ~0-10/210). The normalizations are model-formatting quirks (write `pd.read_csv` instead of using the preloaded `df`), not tool-return behaviour. They're applied identically to clean/toxic, logged per event, and the poisoning path is verified unchanged. The no-normalization subset (29/630 at T1) shows the same compliance pattern.
**In the artifact?** Yes, in F5 round-7 additions and the research log.
**Would a reviewer accept?** Yes, if the paper includes one paragraph explaining why and reports the zero-normalization subset.

### D5. Head-5 is a ToxicBench artifact, not a general observation context
**Severity: MEDIUM**
**Honest answer**: Partly true — ToxicBench's preview uses `df.head(20)` which on 4-12 row tables is the whole table. On the P3 large tables, head-5 is a genuine truncation. But head rows are ordered (Bike by hour, Wine red-then-white), not random — and the k-sweep shows 0o*=0.73 for random-5 vs ~0.58 for head-5, a 0.15 gap. The paper should present both: "the default preview (head-5) AND random-k rows" with the ordering effect documented.
**In the artifact?** A-P3b introduces R1_rand5 and the k-sweep; F4''' reports the full random-k curve. The head-vs-random difference is in the data but not prominently discussed.
**Would a reviewer accept?** Yes, if the paper clearly states that head-5 is a lower bound on detection and random-k is the achievable reference.

### D6. Blind compliance is already known from ToxicBench/Loud-Quiet/APEX
**Severity: MEDIUM-LOW**
**Honest answer**: Prior work shows qualitatively that agents follow bad returns. This paper quantifies it: 83-93% across all context tiers, 0 challenges in 3,780 trajectories, same rate at schema-only as at full preview. The tier-invariance is new — it shows agents aren't making observation-context-dependent trust decisions. The 0-challenge count across ALL runs is striking (no prior paper reports this explicitly).
**In the artifact?** F5/F7 report the numbers. The plan's two-sentence pitch cites ToxicBench/Loud-Quiet/APEX as motivation.
**Would a reviewer accept?** Yes, if positioned as "quantifying and extending" not "discovering."

---

## E. Novelty

**Is the gap still real?** Yes, checked against the 10/31 novelty sweep (18 new citations including VoS, GraphACM, APEX, Mao ACL-SRW).

The specific contributions:
1. **Systematic signal comparison at the tool-return step**: VoS (2610.09115) does 5 signals at step level but not at the observation step, no corruption, no preview axis. 2608.22676 does 2 signals on one domain. **Gap confirmed**: no paper does 7+ signals × multiple agents × multiple context tiers × within-table AUROC at the observation step.
2. **Information-capacity curve**: The 0o*/0d decomposition and the k-sweep establishing the ceiling is genuinely novel. No paper has characterized observation-context richness as the variable that bounds detection. **The differentiator**.
3. **Failure taxonomy with free paired labels**: 2610.30491 does silent override, AgentDrift does channel decomposition. The capability-vs-observation split using ToxicBench pairs is new. **Gap confirmed**.
4. **ToxicBench as experimental platform**: Still 0 forks, 0 experiments by others.

**Is it enough for a workshop?** The information-capacity curve is a genuine empirical finding. Combined with the comprehensive negative results and the pre-registered protocol, it's workshop-quality novelty. Not enough for a main conference track.

**Against Mao ACL-SRW**: The biggest future risk. If Mao publishes experiments before Feb 1, we lose priority on step-level UQ. But Mao's proposal is think-act-observe loops (trajectory-level), not observation-step signals, and has zero experiments as of today.

---

## F. The one experiment to run next

**Ranked by acceptance probability lift:**

| Rank | Experiment | Cost | Lift | Why |
|------|-----------|------|------|-----|
| **1** | **gpt-5.4-mini (H5, closed-source control)** | ~$50-100 API, 1 day | **+0.10** | Kills objection D1 entirely. If a closed model also shows 90%+ compliance and chance-level intrinsic signals, "it's not a Qwen artifact" is settled. Single highest-leverage experiment. |
| 2 | Random-k tier agent runs (T1_rand5) | ~$30, 0.5 GPU-day | +0.05 | Fills the gap between 0o*=0.73 (random-5) and agent-actual 0.58 (head-5). Shows whether the head-ordering effect persists with agents. Strengthens the information-capacity narrative. |
| 3 | P5b scorer with residual target (predict deviation from 0d) | ~$10, 2h A10G | +0.03 | Addresses D3 partially, but a positive result (AUROC>0.60) would change the paper's story from "everything fails" to "something works" — which might be better or worse for coherence. |
| 4 | A second benchmark | ~$30, 2 GPU-days | +0.05 | Addresses D2 but high implementation cost, and workshop scope makes single-domain acceptable. |

**Recommendation**: Run gpt-5.4-mini on the P3 tasks at T1 and T0_agent (420 trajectories). This addresses the single strongest objection and takes ~1 day + ~$50-100.

---

## G. Overclaim audit

Systematic check of F5-F8 and the plan for overclaims:

| Claim | In F5-F8 | Assessment |
|-------|----------|------------|
| "no zero-parameter check on the same five rows gets above 0.58" (F5) | 0o* at head-5 = 0.58 | **Accurate** — recomputed max zero-param is 0.58 |
| "the agent never re-queried or flagged a poisoned return" (F5) | anomaly_detection = 0 at every tier | **Accurate** — recomputed 0 in all files |
| "83-93% blind compliance across all experiments" (plan) | 4B: 93%/93%/93%/92%; 8B: 92%/83% | **Accurate** — 8B T0_agent is 83%, lower bound |
| "0 poison challenges across 3,780 trajectories" (plan) | anomaly_detection = 0 everywhere | **Accurate** |
| "95% of failures are observation failures" (plan) | F1': noise-corrected 0.55 (0.43 numerical) | **OVERCLAIM**: 55% overall, 43% numerical — not 95%. The "95%" appears to come from a different calculation. In the plan's semantic memory, "95% of failures are 'misled by bad data' not 'incapable'" — this probably refers to the observation/(observation+capability) ratio AFTER excluding no-effect runs, where 682/(682+452)=0.60 overall. Neither figure is 95%. |
| "C3 as specified in P5 is a negative result" (F8) | 0.50-0.52 AUROC, sanity FAIL | **Accurate and honest** — the result is genuinely negative |
| "the scorer's error dominates any poison-induced deviation" (F8) | Clean surprise 3.46 > poisoned 3.43 | **Accurate** — confirmed by recomputation |
| "information-capacity curve explaining why" (plan) | 0o* 0.73→0.90 at random-k | **Careful claim** — the k-sweep is on oracle values, not agent events. The head-5 agent values are 0.58, not 0.73. The plan's framing should clarify that 0.73 is random-row-draw, not what agents see |

**Critical finding**: The plan's "95% observation failures" is wrong and must be corrected. The noise-corrected observation share is 0.55 (0.43 numerical). Even the raw share (F1: 682/1134=0.60) is not 95%. The "95% misleading-data" number in the semantic memory appears to be a calculation error or a different definition. This needs fixing before any paper draft.

**One spin concern**: The plan says "the question P4 answers is where learned and agent-intrinsic signals fall between 0d and 0o*." Now that C3 has failed, all signals fall AT or BELOW 0d. This is not "between 0d and 0o*" — it's "at 0d or below." The framing should be updated to reflect the actual finding: nothing reaches 0o*, everything is at chance.

---

## H. 4-page MATH4AI cut

**Is there a 4-page cut?** Marginal.

The math content is:
- The 0o*/0d decomposition (draw-conditioned oracle, estimator loss)
- The information-capacity bound as a function of k
- The pinball-loss quantile regression (standard ML, not novel math)

**Proposed 4-page structure:**
1. **Intro (0.75p)**: Agents accept corrupted numeric returns. Can any signal detect them? We show the answer depends on observation-context information, not signal choice.
2. **Setup (0.5p)**: ToxicBench, 6 large tables, 2 agents, tiers T0/T1/T3. Signals: range check, bootstrap re-execution, verbalized confidence, token entropy, oracle sampling distribution.
3. **The information-capacity bound (1.5p)**: Define 0o* (draw-conditioned), 0o (population), 0d (bootstrap). Present the k-sweep decomposition: estimator loss = 0o*-0d, oracle knowledge = 0o-0o*. Figure 1 (k × AUROC with all reference lines).
4. **Agent results (0.75p)**: At head-5, all signals 0.47-0.58 (chance). 83-93% blind compliance. Table with per-signal per-tier AUROC. H1 confirmed for 8B.
5. **Discussion (0.5p)**: The ceiling is information quantity, not signal quality. The 0.11 estimator loss at k=5 is real headroom but nothing tested recovers it. Limitations (2 models, 1 benchmark, numeric only).

**Fitness**: 3/10 for MATH4AI. The math is a tool for understanding the empirical result, not the contribution itself. A math venue wants theorems, bounds, convergence — not "we computed AUROCs at different k values." The oracle decomposition is clean but straightforward (median/IQR of bootstrap samples). A reviewer at MATH4AI would say "this is an experiment, not a mathematical contribution."

**Recommendation**: Do not submit to MATH4AI. Focus entirely on ICLR 2027 workshop.

---

## I. Dimension scores

| Dimension | Score | Note |
|-----------|-------|------|
| **D1 Protocol fidelity** | 4 | Exemplary pre-registration discipline. All protocol-before-results. Predictions committed and honestly reported when missed. The 7 rounds of independent review are unusual and commendable. |
| **D2 Statistical rigour** | 4 | Within-table AUROC (correct for pooling bias), bootstrap CIs, coverage reporting, sanity rows. The 6-table bootstrap is narrow (only 6 clusters) but correctly stated. |
| **D3 Claim-evidence alignment** | 3 | The "95% observation failures" claim is wrong (55% noise-corrected). The "between 0d and 0o*" framing needs updating now that everything is at 0d or below. F8's negative result is honestly stated. |
| **D4 Reproducibility** | 4 | Raw JSONL, git history, pinned seeds, logged normalizations. All scorer numbers reproduce from the eval files. Instance IDs and costs documented. |
| **D5 Threat model completeness** | 3 | Head-5 is not random-5 and the gap (0.58 vs 0.73) needs more prominent discussion. The scorer's failure mode (magnitude resolution too coarse for subtle poisons) is correctly identified but the "would P5b fix it?" question is unanswered. Only 2 same-family models. |
| **D6 Novelty/significance** | 3 | The information-capacity curve is the genuine novelty. The comprehensive signal failure at head-5 is a contribution. But: 2 models, 1 benchmark, no closed model, and a failed learned signal make the package thin for a strong accept. Workshop-caliber, not above. |

**Mean: 3.50/5**

Down from round 7's 4.00 — the C3 failure removes the "open question for C3" optimism and the overclaim on "95% observation failures" is a new finding.

---

## Sources

- **Recomputed**: poisoned_answer_used/anomaly_detection from `data/ours/p4/qwen3-{4b,8b}/{T1,T0_agent}/toxic_seed0.jsonl`; scorer within-table AUROC from `data/ours/scorer/eval_qwen3-{4b,8b}_T1_scorer.jsonl`; clean coverage from same files
- **Read vs recomputed**: scorer eval logs (read) match recomputed AUROC within rounding (0.503 vs 0.5028, 0.505 vs 0.5047)
- **Git ordering**: `git merge-base --is-ancestor 12595dc 75af363` → YES
- **Protocol**: PREREGISTRATION.md sections P4, A-P4, A-P4b, P5
- **Findings**: findings.md F0-F8 in full
- **Plan**: agent-uq-plan-FINAL.md (contributions, central claim, novelty sweep, related work)
- **Prior review**: docs/REVIEW_2026-11-01_round7_p4week1.md (4.00)
- **Research log**: last 80 lines (P4 week 1 + P5 step gates pass)
- **Scorer logs**: experiments/results/scorer_eval_*.log (6 files, all at chance)
