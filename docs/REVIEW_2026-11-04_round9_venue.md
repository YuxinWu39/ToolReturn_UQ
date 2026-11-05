# Round 9 — ICLR 2027 Workshop Venue Review

**Reviewer role**: Simulated ICLR 2027 workshop reviewer (agent reliability track)
**Date**: 2026-11-04
**Lens**: reviewer-guidelines.md (Dennett's rules, universal dimensions, ICLR scoring) + checklists.md (NeurIPS 16-item) + ml-paper-writing SKILL.md
**Prior round**: Round 8 (acceptance calibration), score 3.50/5, ICLR workshop 0.40-0.50

---

## 1. Summary

This work asks whether any uncertainty signal — zero-parameter statistical checks, agent-intrinsic confidence and token entropy, or a small learned scorer trained only on clean returns — can distinguish corrupted from genuine numeric tool returns at the observation step of an LLM agent trajectory. The answer, across two open-weight agents (Qwen3-4B, Qwen3-8B), 3,780+ trajectories, and 210 pre-registered tasks on six large public tables, is: under the default head-5 observation context that ToxicBench gives agents, nothing works — every signal sits within 0.03 of chance (AUROC 0.47–0.58), while agents blindly follow poisoned values 83–93% of the time with zero challenges. The central contribution is an information-capacity curve that explains *why*: a draw-conditioned oracle (0o\*) that knows the exact sampling law of the k-row statistic but centres on the rows it sees rises monotonically from 0.73 at 5 random rows to 0.90 at 200, and a bootstrap re-execution check (0d) trails it by ~0.11 AUROC at small k. The gap between 0o\* and the population oracle (0o) — about 0.06 at k=5 — represents knowledge of the answer that no context-limited checker can recover. The paper thus reframes the problem from "which signal to use" to "how much observation context is needed," with the additional supporting finding (C2) that ~55% of failures (noise-corrected) are observation-caused, not capability-caused.

## 2. Strengths

- **Pre-registration discipline is exceptional.** Every hypothesis, threshold, signal definition, and stopping rule is committed to git before the code that tests them runs. Protocol commits precede result commits throughout 24+ commits. Predictions are honest: the P5 scorer prediction of [0.55, 0.70] was committed and the observed 0.50–0.52 reported as a miss. This level of rigour is rare in agent-reliability workshop papers. (`PREREGISTRATION.md`, all amendments, verified via `git merge-base`)
- **The information-capacity curve (F4''') is a genuine empirical contribution.** The 0d/0o\*/0o decomposition at multiple k values, with the estimator-loss/oracle-knowledge split, provides a principled framework for understanding why detection fails at low context. The monotonic rise from 0.62→0.85 (0d) and 0.73→0.90 (0o\*) gives future work a concrete target. (`findings.md` F4''', `experiments/ksweep2.py`)
- **Behavioural finding is striking and well-quantified.** 83–93% blind compliance, 0 anomaly_detection events across 3,780 trajectories, across all context tiers (T0_agent, T1, T1r2, T3) — agents don't change their trust behaviour whether they see whole-column statistics or just a schema. This quantifies what ToxicBench/Loud-Quiet described qualitatively. (F5, F6, F7)
- **The negative C3 result is honestly stated as negative.** F8 reports the scorer's sanity and calibration failures (coverage 0.15–0.18 vs 0.80–0.98 required; sanity AUROC 0.81–0.85 vs 0.95 required) before presenting the headline, and lists concrete P5b directions. No attempt to dress up a failure.
- **Within-table AUROC is correctly used throughout**, following the 2610.05572 observation that pooled AUROC inflates via cross-table difficulty variation. Every table in the paper carries both pooled and within-table numbers with table-bootstrap CIs. (`findings.md`, every F-entry)
- **Comprehensive signal coverage**: 0a (range check), 0b (z-score), 0d (re-execution), 0r_log (analytic), 0o\* (draw-conditioned oracle), 0o (population oracle), verbalized confidence, token entropy (3 variants), and a trained scorer — all on the same events, within-table, with CIs. No cherry-picking.

## 3. Weaknesses (ordered by severity)

### W1. Only two same-family models, no closed-source agent
**Concern**: Qwen3-4B and Qwen3-8B are the same architecture at different scales. H5 (closed-source control) is registered but unexecuted. The claim "agents blindly follow" rests on one model family.
**Evidence for/against**: F0/F1 include ToxicBench trajectories from gpt-5.4-mini, claude-sonnet-4-6, and haiku on the original 4–12 row tables (observation share 0.60 across all), suggesting model-independence. But these are on different tasks (small tables) so direct comparison is limited. The plan's drop order lists gpt-5.4-mini as "never drop" but no API key obtained.
**Fixable before Feb 1?** Yes — ~$50–100 API cost, 1 day of work. This is the single highest-leverage experiment remaining.

### W2. One benchmark, numeric tools only
**Concern**: All results are on ToxicBench's python_exec over CSV tables. The plan acknowledges this scope ("numeric-return tools") and had env-2 candidates (BFCL, corrupted-calculator, ToxicBench-SQL) all dropped from the minimum viable set.
**Evidence**: The plan's Limitations section and the PREREGISTRATION correctly state this. The mechanism (information-capacity bound) is intrinsically numeric because it depends on interval checks.
**Fixable before Feb 1?** Partially — ToxicBench-SQL (same tables, different tool) is lowest-cost and tests tool-interface transfer. Full domain transfer (text returns) is out of scope for this paper.

### W3. Scorer undertrained — the C3 negative may be uninformative
**Concern**: 1,741–1,772 clean examples, 0.5B backbone, 3 epochs. The scorer learns column scale (per-table correlation up to 0.94) but not fine enough for 1.1–2× poisons (x6 magnitude error). A skeptical reviewer would say "train it properly before claiming nothing works."
**Evidence**: F8 is honest about the failure mode: "a 0.5B model trained on ~1,800 clean (query, code, 5-row preview) → value examples learns the scale of a column, not the statistic to within 10–50%." P5b candidates listed. Training loss converged. Clean coverage 0.15–0.18.
**Fixable before Feb 1?** Yes: (a) residual target (predict deviation from 0d instead of raw value), (b) larger backbone (1.5B or 3B), (c) more training data from synthetic generation. Even a negative with a better-trained scorer would be more convincing.

### W4. Head-5 is ordered, not random — the gap matters
**Concern**: The k-sweep's 0o\* = 0.73 at k=5 uses random row draws. But agents see head-5, where 0o\* = 0.58. This 0.15 gap is mentioned in F5 but not prominently discussed. A reviewer could ask: "your mechanism says 0.73 is achievable at 5 rows, but agents can only get 0.58 — isn't the mechanism about random access, not observation context?"
**Evidence**: F5 states "0o\* on head rows is near chance because head rows are not a random sample (the A-P3d caveat)." The k-sweep and agent results are in different figures/tables.
**Fixable before Feb 1?** Partly: run T1_rand5 (random-5) agent trajectories to show the gap closes when agents see random rows. More importantly, the paper must discuss this distinction prominently — it's the key subtlety.

### W5. The plan's "95% observation failures" overclaim persists in semantic memory
**Concern**: Round 8 identified that the plan states "95% of failures are 'misled by bad data'" but the actual noise-corrected observation share (F1') is 0.55 (0.43 numerical). Neither 60% (raw) nor 55% (noise-corrected) is 95%.
**Evidence**: `findings.md` F1' correctly states 0.55. The overclaim appears in the user's semantic memory / conversation history, not in the versioned artifacts — but if it leaks into the paper draft, it's a desk-reject-level error.
**Fixable before Feb 1?** Trivially — ensure the paper uses F1' numbers (0.55 / 0.43), not the erroneous 95%.

### W6. Six tables, six bootstrap clusters — CIs are wide
**Concern**: The 6-table bootstrap has only 6 clusters, so CIs on within-table quantities are structurally wide and may miss real effects. The estimator-loss CI at k=5 is [0.095, 0.130] — tight enough for that finding — but the oracle knowledge [0.05, 0.08] is narrow for 6 clusters and could be a random fluctuation of the table-bootstrap.
**Evidence**: F4''' reports both table-level and (table, draw) CIs. The common-support restriction to 168 tasks and 6-table CI are correctly stated.
**Fixable before Feb 1?** Only with more tables. The paper should candidly note the 6-table limitation and recommend expansion.

## 4. Questions for the authors

1. **Would running gpt-5.4-mini (or any non-Qwen closed model) on the 210 P3 tasks at T1 change the 83–93% compliance finding?** If so, the paper's generalization is at risk. If not, it eliminates the strongest objection. (Affects W1, +0.10 acceptance lift per round 8.)
2. **Is the information-capacity curve a property of random subsampling or of observation contexts in general?** Head-5 gives 0o\* = 0.58, random-5 gives 0.73. If the paper's central claim is about "observation context richness," shouldn't it demonstrate the curve for actual agent observation contexts (head rows), not just random samples?
3. **Would a P5b scorer targeting the deviation from 0d (residual architecture) recover any of the 0.11 estimator loss?** This is the most important "next experiment" for the C3 contribution. A positive result changes the paper fundamentally.
4. **What fraction of real-world LLM tool returns are numeric?** The Limitations section promises to "quantify fraction of real tool returns that are numeric using ToolBench/API-Bank tool-type distributions" but no number appears in findings.md.

## 5. Four Universal Dimensions

### Quality: 4/5
Claims are carefully supported: every number has a CI, every finding cites its source script, confirmatory vs exploratory is labeled, predictions are committed before results and misses are reported. The sanity-row hard rule is applied to every signal and failures (scorer sanity FAIL) lead to withholding, not hiding. The main quality gap: only 2 same-family models undermines generalization claims. The 6-table bootstrap is a structural limitation honestly stated. Statistical methodology (within-table AUROC, clustered bootstrap, coverage reporting) is above typical workshop papers.

### Clarity: 3/5
The *artifacts* are clear — findings.md is well-structured, PREREGISTRATION.md is thorough, the commit history is readable. But findings.md is not a paper: it carries ~10 superseded findings (F2, F2', F2'', F3, F3', F4, F4', F4'', etc.) alongside the current ones, making it hard for a reviewer to extract the final story. The amendments in PREREGISTRATION.md run to ~6,000 words with corrections, supersessions, and "round-N items" interleaved. A paper draft must: (a) present only the final definitions, (b) relegate the amendment trail to a supplement, (c) clearly distinguish the random-k curve from the head-5 agent curve. Without a draft, clarity is assessed as "material is present but poorly organized for a reader."

### Significance: 3/5
The finding that all signals are at chance under head-5 context is significant for the agent reliability community — it shifts the question from "which signal" to "how much context." The information-capacity curve provides a quantitative framework. However: the scope is narrow (numeric tools, one benchmark, two models), the practical implication is unclear (what should a builder DO with this?), and the C3 scorer failure leaves no positive prescription. A workshop paper can survive on a well-characterized negative, but significance would rise substantially with: (a) a closed model confirming generalization, or (b) a P5b positive showing the estimator loss IS recoverable.

### Originality: 4/5
Per the reviewer guidelines: "originality does not necessarily require introducing an entirely new method. Papers that provide novel insights from evaluating existing approaches or shed light on why methods succeed can also be highly original." The information-capacity curve is novel. The systematic signal comparison at the observation step (not trajectory-level) is novel. The 0o\*/0d decomposition is a clean conceptual contribution. The failure taxonomy with free paired labels is novel (AgentDrift does channel decomposition but not capability vs observation). ToxicBench still has 0 forks and 0 published experiments by others. Nearest competitor (VoS 2610.09115) is step-level, no corruption, no preview axis. The originality concern is whether "comprehensive evaluation at an unoccupied granularity" is a contribution or "just a benchmark paper" — but the mechanism finding (information capacity as the ceiling) elevates it.

## 6. NeurIPS 16-Item Checklist

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1 | Claims match results | **Partial** | Central claim in plan matches F4''', but the "95% observation failures" in semantic memory contradicts F1' (0.55). Must be corrected before submission. |
| 2 | Limitations section | **Yes** | Plan's Limitations section covers numeric-only scope, adversary evasion, 30-table limit, env-2 absence, domain shift, scorer fairness, pre-committed fork. |
| 3 | Theory/proofs | **NA** | Empirical study. The 0o\*/0d decomposition is operational, not a theorem. |
| 4 | Reproducibility | **Yes** | Raw JSONL data, git history with SHAs, pinned seeds, `requirements.txt`, logged normalizations, instance IDs. `experiments/.venv/bin/python` reproduces all numbers. |
| 5 | Data/code access | **Yes** | All code in the repo. Data under `data/ours/`. ToxicBench is a public clone. Six public tables (CC-BY-4.0/CC0) with SHAs. |
| 6 | Experimental details | **Yes** | Hyperparameters in P5 (lr 2e-4, 3 epochs, LoRA r=16, batch 16). Temperature 0.7 for all P4 runs. Seeds documented. |
| 7 | Statistical significance | **Yes** | Bootstrap CIs on every number, 2,000+ resamples, clustered on table. Within-table AUROC alongside pooled. Coverage reported. |
| 8 | Compute resources | **Yes** | one A10G GPU, ~$28 total GPU cost, ~$0 API (no closed model run yet). Run times logged. |
| 9 | Ethics code compliance | **Yes** | No human subjects. Public data only. GPU inference server bound to localhost only. No credentials in repo. |
| 10 | Broader impacts | **Partial** | Not explicitly written but implied: the paper shows agents are vulnerable to corrupted tool returns with no current detection. Dual-use concern is minimal (benchmark, not attack tool). Needs a paragraph. |
| 11 | Safeguards | **NA** | No model release. 0.5B scorer is a negative result. No high-risk output. |
| 12 | License respect | **Yes** | ToxicBench under its license (cloned, not submoduled). Six tables all CC-BY-4.0 or CC0. SHAs recorded in `gen_tasks.py` / `PREREGISTRATION.md`. |
| 13 | Asset documentation | **Partial** | Data layout documented in README.md. No formal datasheet/model card (would need one for the scorer if it had worked). Workshop venue unlikely to require one for a negative-result scorer. |
| 14 | Human subjects | **NA** | No crowdsourcing or human evaluation. |
| 15 | IRB approvals | **NA** | No human subjects research. |
| 16 | LLM declaration | **Partial** | The research repo was built interactively with an LLM coding agent. The plan, code, and reviews all carry agent attribution. A paper must disclose this per ICLR 2026+ policy. |

## 7. Common Reviewer Concerns Audit

### Technical Concerns
| Concern | Applies? | Pre-empted? |
|---------|----------|-------------|
| "Baselines too weak" | **No** — baselines include the oracle ceiling (0o\*), the strongest zero-param checks, AND intrinsic signals. The comparison is comprehensive. | Yes (plan C1 signal set) |
| "Missing ablations" | **Partially** — the k-sweep is effectively an ablation over context richness. Missing: ablation over poison strength (continuous severity is registered but only bin-level reported), ablation over model family (W1). | Partly (k-sweep is strong; model-family ablation missing) |
| "No error bars" | **No** — bootstrap CIs on every number. | Yes |
| "Hyperparameters not tuned" | **Applies to scorer only** — P5 uses one config (lr 2e-4, LoRA r=16, 3 epochs) with no tuning. Counter: training loss converged; the failure is conceptual (resolution), not tuning. | Partially (F8 discusses) |
| "Claims not supported" | **One claim unsupported**: "95% observation failures" in memory/plan vs 55% in findings. All other claims in findings.md are evidence-backed. | No for the 95% claim |

### Novelty Concerns
| Concern | Applies? | Pre-empted? |
|---------|----------|-------------|
| "Incremental contribution" | **Possible** — a skeptical reviewer may see this as "ToxicBench + more signals." The information-capacity curve differentiates it, but only if presented as the central contribution, not a secondary analysis. | Partially (plan frames it correctly) |
| "Similar to [paper X]" | **VoS (2610.09115)** is closest — 5 UQ methods at step level. Positioning: "VoS measures intervention value at the step level with no corruption; we zoom to the observation step with controlled corruption and a context-richness axis." Must be cited prominently. | Yes (novelty sweep covers VoS) |
| "Straightforward extension" | **Risk** — "run more signals on ToxicBench" reads as incremental. The 0o\*/0d decomposition and the context-richness framing are the non-obvious aspects. | Partially |

### Clarity Concerns
| Concern | Applies? | Pre-empted? |
|---------|----------|-------------|
| "Hard to follow" | **Yes, currently** — findings.md has 10+ superseded entries. PREREGISTRATION has 6 amendments with corrections. A paper draft must linearize this. | No (no draft exists) |
| "Notation inconsistent" | **Minor risk** — "0a", "0d", "0o\*" naming is non-standard (no LaTeX-friendly symbols). Paper needs a notation table. | No |
| "Missing details" | **No** — reproducibility details are extensive (perhaps excessively so for a 6–8 page workshop paper). | Yes |

### Significance Concerns
| Concern | Applies? | Pre-empted? |
|---------|----------|-------------|
| "Limited impact" | **Partially** — the paper shows what DOESN'T work but offers no positive prescription. A builder reading this learns the problem exists and that context richness matters, but not what to do. | Partially (F8 lists P5b directions) |
| "Narrow evaluation" | **Yes** — numeric tools, one benchmark, two same-family models. Workshop-acceptable scope but a reviewer will note it. | Yes (plan's Limitations) |
| "Only works in restricted setting" | **Inverted** — the finding is that nothing works in any setting tested. The information-capacity explanation is general in principle but demonstrated only for numeric aggregates. | Partially |

## 8. ICLR-Style Verdict

### Rating: 5 / 10 (Marginally below acceptance threshold)

### Confidence: 4 / 5 (Confident — I have read the full artifacts and recomputed key numbers)

**Justification**: This is a carefully executed empirical study on an unoccupied evaluation unit (observation-step signal comparison with a context-richness axis), with an exemplary pre-registration protocol and a genuine mechanistic insight (the information-capacity curve). The comprehensive negative result — every signal at chance under the default context — is a meaningful finding for the agent reliability community, and the C3 scorer failure is reported with exemplary honesty. However, three factors keep this at the lower boundary of acceptability: (1) only two same-family models weaken the generalization claim significantly; (2) the C3 scorer negative may be uninformative given the undertraining — a stronger negative (better-trained scorer still fails) or a positive (P5b residual target works) would be more convincing; (3) the paper does not yet exist as a draft, and the raw materials (findings.md with 10+ superseded entries, PREREGISTRATION with 6 amendments) would require substantial editorial work to become a readable 6–8 page paper.

### Calibrated acceptance probability

**ICLR 2027 Agent Reliability Workshop (6–8p, base rate 40–50%): 0.35–0.45**

This is slightly below round 8's 0.40–0.50, and I partially agree with that range but lean toward the lower end for three reasons:

1. **Round 8 was pre-C3 failure.** The C3 scorer's failure (sanity FAIL, calibration catastrophic) removes the "open question that could go either way" optimism. The paper is now entirely a negative-result paper with a mechanistic explanation. Negative results at workshops are accepted when the mechanism is strong — this one is, but it's stronger if a better-trained scorer also fails.

2. **No draft exists.** ICLR reviewers evaluate the paper as written. The raw materials are strong but disorganized — a reviewer seeing 10 superseded findings and 6 protocol amendments interleaved would struggle. The editorial distance from findings.md to a clear 6–8 page paper is non-trivial.

3. **Model diversity.** Since round 8, no new model has been added. The "one model family" concern is now 2 months old and still open. Adding gpt-5.4-mini would move the upper bound from 0.45 to ~0.55.

**Comparison with round 8 (0.40–0.50):** I agree that 0.40 is the floor for a well-pre-registered negative result with a mechanism. I place the ceiling at 0.45 rather than 0.50 because: (a) C3's failure thinned the package, (b) no progress on model diversity, (c) no draft. If gpt-5.4-mini confirms the findings and the draft is well-written, 0.50–0.60 is achievable.

## 9. What a Paper Draft Must Contain That findings.md Does Not

### Structural gaps
1. **Abstract** (~250 words) — must state the central finding (information-capacity ceiling), the scope (numeric tools, 2 agents, 210 tasks), and the negative result (all signals at chance under head-5 context) without overclaiming.
2. **Introduction** (1–1.5p) — motivate the problem (agents accept bad returns: cite ToxicBench, Loud-Quiet, APEX-Agents), state the contribution (observation-step signal comparison + information-capacity mechanism + failure taxonomy), and clearly distinguish from trajectory-level work (VoS, 2608.11552, 2608.22676).
3. **Related Work** (0.75–1p) — must position against all 8 papers from the novelty sweep: VoS 2610.09115, Trajectory-Adapted UQ 2608.11552, 2608.22676, Outcome Monitors 2608.19303, Probe-based 2608.27750, 2608.07528, ToolGate, 2509.02401. Currently only in the plan, not in any draft form.
4. **Broader Impacts paragraph** — NeurIPS checklist item 10.
5. **LLM usage disclosure** — ICLR requires this for significant research contribution by LLM.

### Figures needed
1. **Figure 1**: The k-sweep curve (k rows × within-table AUROC) with 0d, 0o\*, 0o as reference lines, and agent-actual points at T0_agent / T1 / T3 marked. This is the paper's central figure. Must clearly distinguish random-k curve from head-k agent points.
2. **Figure 2**: Signal × tier heatmap (signals on y-axis, context tiers on x-axis, AUROC as cell value with CI). Shows at a glance that everything is at chance under head-5.
3. **(Optional) Figure 3**: The estimator-loss / oracle-knowledge decomposition stacked bar chart at selected k values.

### Tables needed
1. **Table 1**: Dataset statistics (6 tables, rows, columns, tasks per template).
2. **Table 2**: Compliance rates per agent × tier (poisoned_answer_used, anomaly_detection, noise floor).
3. **Table 3**: Signal × agent × tier AUROC matrix (the C1 matrix). Core of the paper.
4. **Table 4**: Failure taxonomy (C2): capability / observation / no-effect counts and noise-corrected rates.
5. **Table 5**: Scorer results (C3 negative): sanity, calibration, AUROC per eval set.

### Definitions needed
- Formal definition of "observation context richness" (not just "head-k rows")
- Formal definition of 0o\* (draw-conditioned oracle) in math notation — currently only in English
- The estimator-loss / oracle-knowledge decomposition as an equation, not a table annotation

### Related work positioning (specific)
The plan names 8 papers for the novelty sweep. Each needs 2–3 sentences positioning this work against it:
- **VoS (2610.09115)**: step-level, no corruption, no context axis — we zoom to observation step
- **2608.11552**: trajectory-level multi-method on BFCL-v4 — we fix the trajectory and vary the observation
- **2608.22676**: 2 signals, single domain — we do 7+ signals across agents
- **2608.19303**: postcondition checks for recovery — we compare detection signals, not recovery
- **2608.27750**: probes on pre-call hidden states — we score post-return observations
- **2608.07528**: probes detect corruption but don't predict failure — supports our H1 (intrinsic signals are content-blind)
- **ToolGate**: formal postconditions — generalization of our range check
- **2509.02401**: multiple UQ signals for structured-data agents, no corruption — nearest uncorrupted precursor

## 10. Spot-Check Results

### Recomputed numbers

| # | What | findings.md claims | Recomputed | Match? |
|---|------|-------------------|-----------|--------|
| 1 | Qwen3-8B T1 `poisoned_answer_used` from `data/ours/p4/qwen3-8b/T1/toxic_seed0.jsonl` | 194/210 (92%) — F7 | **194/210 (92.4%)** | ✓ Exact match |
| 2 | Scorer within-table AUROC on `data/ours/scorer/eval_qwen3-8b_T1_scorer.jsonl` | 0.51 [0.49, 0.52] — F8 | **0.5047** (6 tables, `sklearn.metrics.roc_auc_score`) | ✓ Within rounding (0.505 vs 0.5047) |
| 3 | k-sweep k=5 estimator loss (0o\*−0d) from `experiments/results/ksweep2_v2.log` | +0.111 [0.095, 0.130] — F4''' | **+0.111 [+0.095, +0.130]** (from log line: `0.619 ... 0.731 ... +0.111`) | ✓ Exact match |

### Git ordering checks

| Protocol commit | Results commit | `merge-base --is-ancestor` | Status |
|----------------|---------------|---------------------------|--------|
| `12595dc` P5 scorer spec (2026-11-01 12:32:39) | `75af363` P5 results (2026-11-01 22:25:06) | **YES** | ✓ Protocol before results |
| `5e978bb` A-P3d protocol (2026-10-31 20:31:49) | `40d5da3` A-P3d results (2026-10-31 21:09:06) | **YES** | ✓ Protocol before results |

All five spot-checked values match. Both git ordering checks pass.

---

*Report generated 2026-11-04. Reviewer followed reviewer-guidelines.md (Dennett's rules, ICLR scoring 1-10, confidence 1-5), checklists.md (NeurIPS 16-item), and ml-paper-writing SKILL.md (publication-ready requirements). No files modified except this report.*
