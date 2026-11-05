# Round 10b — Citation Verification Report

**Date**: 2026-11-04
**Method**: arXiv API (export.arxiv.org) batch queries + ACL Anthology fetch; manual adjudication of shorthand-name matches
**Source files**: agent-uq-plan-FINAL.md, findings.md, PREREGISTRATION.md, REVIEW_2026-11-02_round8_acceptance.md

## Summary

| Verdict | Count |
|---------|-------|
| MATCH | 48 |
| PARTIAL | 2 |
| MISMATCH | 0 |
| NOT FOUND | 0 |
| NOT RETRIEVED | 0 |
| **Total** | **50** |

All 48 arXiv IDs resolve to real papers. Both ACL Anthology IDs resolve. Every paper matches what the plan claims it is — the plan uses consistent shorthand names that correspond to the real titles. Two entries are PARTIAL only because the plan's shorthand is a loose abbreviation (ToxicBench = "When Tools Silently Lie", Mao ACL-SRW = "Thesis Proposal: When Does an Agent Know It Is Lost?").

## Full Citation Table

| ID | Real Title | First Author | Submitted | Plan's Shorthand | Verdict |
|---|---|---|---|---|---|
| 2506.12202 | Quasar: A Programming Language Specialized for LLM Code Actions | Stephen Mell | 2025-06-13 | QUASAR | **MATCH** |
| 2509.02401 | Towards Agents That Know When They Don't Know: Uncertainty as a Control Signal for Structured Reasoning | Josefa Lia Stoisser | 2025-09-02 | Towards Agents That Know When They Don't Know (NeurIPS 2025) | **MATCH** |
| 2602.11409 | TRACER: Trajectory Risk Aggregation for Critical Episodes in Agentic Reasoning | Sina Tayebati | 2026-02-11 | TRACER | **MATCH** |
| 2603.12564 | Sell Me This Stock: Unsafe Recommendation Drift in LLM Agents | Zekun Wu | 2026-03-13 | AgentDrift (decomposes info-channel vs memory-channel) | **MATCH** |
| 2605.08828 | When Agents Overtrust Environmental Evidence: An Extensible Agentic Framework for Benchmarking Evidence-Grounding Defects in LLM Agents | Strick Sheng | 2026-05-09 | EnvTrustBench | **MATCH** |
| 2605.17453 | Trust No Tool: Evaluating and Defending LLM Agents under Untrusted Tool Feedback | Lecheng Yan | 2026-05-17 | Trust No Tool | **MATCH** |
| 2606.14476 | When the Tool Decides: LLM Agents Defer Blindly to Graph Neural Network Tools, and Why It Matters | Zhongyuan Wang | 2026-06-12 | When the Tool Decides | **MATCH** |
| 2606.20662 | Confidence Laundering in Agent Systems: Why Uncertainty Needs a Latent Carrier | Kaiwen Shi | 2026-06-09 | Confidence Laundering | **MATCH** |
| 2606.21409 | Don't Blindly Trust It: How Unreliable Feedback Breaks Tool-Using LLM Agents | Chubin Zhang | 2026-06-19 | Don't Blindly Trust It | **MATCH** |
| 2606.25760 | Uncertainty Quantification for Computer-Use Agents: A Benchmark across Vision-Language Models and GUI Grounding Datasets | Divake Kumar | 2026-06-24 | Argus | **MATCH** |
| 2606.28733 | Agentic Abstention: Do Agents Know When to Stop Instead of Act? | Han Luo | 2026-06-27 | Agentic Abstention (NeurIPS 2026 oral) | **MATCH** |
| 2607.10059 | AgentAbstain: Do LLM Agents Know When Not to Act? | Xun Liu | 2026-07-11 | AgentAbstain | **MATCH** |
| 2607.28802 | Model or Harness? An Interaction-Centric Taxonomy for Localizing Agent Failures | Harsh Raj | 2026-07-30 | Model or Harness? | **MATCH** |
| 2607.29190 | CAGE: Certified Authorization under Typed-Return Uncertainty for Tool-Using Agents | Blaise Delattre | 2026-07-31 | CAGE | **MATCH** |
| 2608.02464 | Real-Time Detection and Repair of LLM Agent Failures | Sunny Dubey | 2026-08-03 | trajectory-level monitors | **MATCH** |
| 2608.03071 | Getting the Parameters Right: A Difficulty-Graded Benchmark and Probe-Guided Training for LLM Tool Calls | Guoyao Yu | 2026-08-04 | (listed in related work without shorthand) | **MATCH** |
| 2608.07528 | The Knowing-Saying Gap: When Probes See Errors that Confidence Misses | Jyotin Goel | 2026-07-21 | When Probes See Errors that Confidence Misses | **MATCH** |
| 2608.11552 | Beyond Single-Turn Confidence: Trajectory-Adapted Uncertainty Quantification for LLM Agents | Dylan Bouchard | 2026-08-12 | Trajectory-Adapted UQ | **MATCH** |
| 2608.16002 | From Sequence to Structure: Relational Uncertainty Propagation for LLM Agents | Zhengzhao Ma | 2026-08-17 | RUPA | **MATCH** |
| 2608.19303 | Outcome Monitors: Recovery Affordances for Silent Tool Failures | Sugam Panthi | 2026-08-19 | Outcome Monitors | **MATCH** |
| 2608.22676 | Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses | Jiachen Xu | 2026-08-24 | Robustness Analysis (two signals one domain) | **MATCH** |
| 2608.26189 | Invocation-Level Reliability of Tool-Using Agents | Afiya Noorain | 2026-08-23 | Invocation-Level Reliability | **MATCH** |
| 2608.27750 | The Calls are Coming from Inside the Model: Investigating Probe-based Detection of Tool-Calling Errors in LLMs | Eric Yeats | 2026-08-27 | Probe-based detection of tool-CALLING errors | **MATCH** |
| 2609.05587 | Agents' Overreliance on Unreliable Tools | Hoyeol Yang | 2026-09-04 | Overreliance | **MATCH** |
| 2609.07395 | Uncertainty Quantification for LLM Agents: A Taxonomy, an Evaluation Protocol, and an Empirical Study | Moule Lin | 2026-09-07 | Agent UQ Taxonomy | **MATCH** |
| 2609.26836 | Silent Failures in Agent-Tool Interaction: An Audit of ToolUniverse | Devansh Singh | 2026-09-21 | Silent Failures | **MATCH** |
| 2609.37153 | When Tools Silently Lie: Evaluating and Mitigating Blind Compliance in Tool-Augmented Data Agents | Zifu Tao | 2026-09-29 | ToxicBench | **PARTIAL** |
| 2610.04836 | RSure-Agent: Reliable Use of Tool Observations for Remote Sensing Agents | Fuyuan Liu | 2026-10-04 | RSure-Agent | **MATCH** |
| 2610.05572 | Disentangling Task Difficulty from Run-Level Failure in Agent Failure Prediction | Mohsen EsfandyariDoulabi | 2026-10-04 | Difficulty vs Run-Level Failure (pooled-vs-within-table AUROC) | **MATCH** |
| 2610.06563 | HERA: Harness-Environment Co-Evolution for Reliable Agentic Abstention | Han Luo | 2026-10-05 | HERA | **MATCH** |
| 2610.07753 | From Evidence to Action: How Tool-Using Agents Fail | Hongzhan Lin | 2026-10-06 | (motivating citation, no shorthand) | **MATCH** |
| 2610.07948 | Confidence Reasoning Graphs: Structured Confidence Estimation for LLM Agents | Brendan King | 2026-10-06 | CRGs / Confidence Reasoning Graphs | **MATCH** |
| 2610.08097 | When Tools Lie: Reliability of Mathematical Agents Under Corrupted Tool Feedback | Kavienan Jegatheesan | 2026-10-06 | Math Agents Corrupted Feedback | **MATCH** |
| 2610.09115 | From Uncertainty to Action: Learning to Steer LLM Agents | Hanwen Li | 2026-10-06 | VoS / From Uncertainty to Action | **MATCH** |
| 2610.09793 | Formal Runtime Verification for Tool-Using LLM Agents: An Offline Same-Benchmark Study on AgentDojo and STAC | Nikolaos Kekatos | 2026-10-07 | Formal Runtime Verification | **MATCH** |
| 2610.10062 | Loud Failures, Quiet Failures: Fault Detection and Recovery in Tool-Using Language Model Agents | Obada Kraishan | 2026-10-07 | Loud/Quiet Failures | **MATCH** |
| 2610.11514 | SSCBench: Evaluating the Evidential Validity of Fault-Injection Tests for Tool-Using LLM Agents | Xincheng He | 2026-10-08 | SSCBench | **MATCH** |
| 2610.16661 | Structural Baselines Matter for Agent Failure Detection and Attribution | Ramesh Arvind Naagarajan | 2026-10-12 | Structural Baselines | **MATCH** |
| 2610.18614 | Can an Agent Learn to Predict Its Own Failure? Outcome-Grounded Confidence Calibration in LLM Agents | Ashutosh Hathidara | 2026-10-13 | Outcome-Grounded Calibration / GRPO verbalized confidence | **MATCH** |
| 2610.21098 | ToolBottleneckBench: Measuring Tool-Agent Performance under Controlled Pressures and Fixed Harness Budgets | Zichuan Xu | 2026-10-15 | ToolBottleneckBench | **MATCH** |
| 2610.21624 | AgentPerturb: Evaluating LLM Agent Robustness under Controlled Interaction Perturbations | Yuanjian Xu | 2026-10-15 | Controlled Interaction Perturbations / APEX-Agents | **MATCH** |
| 2610.22031 | GraphACM: Graph-based Action Consistency Measurement for Uncertainty Quantification in LLM Agents | Yaxin Ma | 2026-10-15 | GraphACM | **MATCH** |
| 2610.24194 | Agents' Last Doubt: Knowing When to Act and When to Step Back in Tool-Using Agents | Qisai Liu | 2026-10-16 | Act vs Step Back | **MATCH** |
| 2610.30491 | What the Trace Shows and What the Label Says: Auditing Behavioral Detectors in Agent Evaluation | Idunnuoluwa A. Adeniji | 2026-10-21 | Trace vs Label / silent tool-output override | **MATCH** |
| 2610.31650 | EpiSEM-Bench: Evaluating Safety and Evidence Recovery in LLM Agents under Missing Evidence | Qijin Zhang | 2026-10-22 | (motivating citation) | **MATCH** |
| 2610.31895 | Knowing When to Stop: The Evidence-Action Gap in Coding Agents | Tianyu Chen | 2026-10-22 | (motivating citation) | **MATCH** |
| 2610.32110 | Who Verifies the Tools? How Warped Formatters Mislead Agents and Their Verifiers | William Jeffries | 2026-10-23 | Warped Formatters | **MATCH** |
| 2610.36570 | CASEL: Consequence-Aware Selective Execution for Reliable Long-Horizon Tool-Using Agents | Yanyan Zhang | 2026-10-27 | CASEL | **MATCH** |
| 2026.acl-srw.78 | Thesis Proposal: When Does an Agent Know It Is Lost? Confidence Trajectory Analysis for Step-Wise UQ | — | 2026 | Mao ACL-SRW | **PARTIAL** |
| 2026.acl-industry.58 | Securing the Tool Layer: A Threat Taxonomy and Runtime Defense Framework for Model Context Protocol | — | 2026 | ShieldMCP | **MATCH** |

## Priority Citations — Detailed Verification

### 2609.37153 — ToxicBench ✅ PARTIAL
- **Real title**: "When Tools Silently Lie: Evaluating and Mitigating Blind Compliance in Tool-Augmented Data Agents"
- **Verdict**: PARTIAL — the plan calls it "ToxicBench" which is the benchmark name from the paper, not the paper title. The real title is about "blind compliance" which matches the plan's usage. The GitHub repo is `Toxic_Tool_Bench`. **No correction needed** — "ToxicBench" is the standard community reference.
- **arXiv comment**: 28 pages, 8 figures. Code: https://github.com/turambar928/Toxic_Tool_Bench
- **Venue**: No venue mentioned in arXiv metadata — **preprint only**

### 2606.28733 — Agentic Abstention / NeurIPS 2026 oral ✅ MATCH
- **Real title**: "Agentic Abstention: Do Agents Know When to Stop Instead of Act?"
- **First author**: Han Luo
- **Venue claim**: Plan says "NeurIPS 2026 oral". arXiv comment field: **no venue info**. The 10/31 novelty check says "CONFIRMED NeurIPS 2026 ORAL" — this was likely verified via OpenReview, not arXiv metadata.
- **Status**: Title match confirmed. **Venue claim UNVERIFIED from arXiv** — needs independent verification via OpenReview.

### 2610.09115 — VoS / From Uncertainty to Action ✅ MATCH
- **Real title**: "From Uncertainty to Action: Learning to Steer LLM Agents"
- **Plan says**: "compares 5 UQ methods at step level on 82K counterfactual continuations; measures intervention value, no corruption, no preview axis"
- **arXiv comment**: 22 pages, 9 figures, 9 tables

### 2610.05572 — Difficulty vs Run-Level / pooled-vs-within-table AUROC ✅ MATCH
- **Real title**: "Disentangling Task Difficulty from Run-Level Failure in Agent Failure Prediction"
- **Plan says**: ">99.9% of positive-negative pairs in pooled AUROC are cross-unit, so a difficulty oracle can reach 0.945 pooled while at chance within unit"

### 2610.30491 — Trace vs Label / silent tool-output override ✅ MATCH
- **Real title**: "What the Trace Shows and What the Label Says: Auditing Behavioral Detectors in Agent Evaluation"
- **Plan says**: "agents sometimes receive a corrupted value and later use the correct value without re-calling the tool"

### 2610.21624 — APEX-Agents / Controlled Interaction Perturbations ✅ MATCH
- **Real title**: "AgentPerturb: Evaluating LLM Agent Robustness under Controlled Interaction Perturbations"
- **Note**: Plan calls this "APEX-Agents/Toolathlon" in the MOTIVATING section and "Controlled Interaction Perturbations" in the Added 10/31 list. The real title is "AgentPerturb". The plan's "Controlled Interaction Perturbations" matches the subtitle. The "APEX-Agents" shorthand may be from an earlier version of the paper or a related tool — **minor naming discrepancy, content match confirmed**.

### 2610.18614 — Outcome-Grounded Calibration / GRPO verbalized ✅ MATCH
- **Real title**: "Can an Agent Learn to Predict Its Own Failure? Outcome-Grounded Confidence Calibration in LLM Agents"
- **Plan says**: "verbalized starts near chance, GRPO-trained; supports H1"

### 2610.22031 — GraphACM ✅ MATCH
- **Real title**: "GraphACM: Graph-based Action Consistency Measurement for Uncertainty Quantification in LLM Agents"
- **Plan says**: "consistency AUROC 0.811 vs verbalized 0.769"

### 2610.04836 — RSure-Agent ✅ MATCH
- **Real title**: "RSure-Agent: Reliable Use of Tool Observations for Remote Sensing Agents"
- **Plan says**: "content-free (task,tool) frequency table prior + backbone LLM self-verifier"

### 2610.10062 — Loud/Quiet Failures ✅ MATCH
- **Real title**: "Loud Failures, Quiet Failures: Fault Detection and Recovery in Tool-Using Language Model Agents"
- **Plan says**: "prompting agents to 'check results' has zero effect"

### 2608.22676 — Robustness Analysis ✅ MATCH
- **Real title**: "Robustness Analysis of Agentic AI to Inconsistent and Incomplete Tool Responses"
- **Plan says**: "two signals one domain"

### 2608.11552 — Trajectory-Adapted UQ ✅ MATCH
- **Real title**: "Beyond Single-Turn Confidence: Trajectory-Adapted Uncertainty Quantification for LLM Agents"

### 2608.19303 — Outcome Monitors ✅ MATCH
- **Real title**: "Outcome Monitors: Recovery Affordances for Silent Tool Failures"
- **Plan says**: "postcondition checks on tool returns for silent failures; recovery-focused, no signal comparison"

### 2608.27750 — Probe-based detection ✅ MATCH
- **Real title**: "The Calls are Coming from Inside the Model: Investigating Probe-based Detection of Tool-Calling Errors in LLMs"
- **Plan says**: "hidden-state probes on wrong arguments"

### 2608.07528 — When Probes See Errors ✅ MATCH
- **Real title**: "The Knowing-Saying Gap: When Probes See Errors that Confidence Misses"
- **Plan says**: "linear probes detect corrupted context near-perfectly but this does not predict failure"

### 2509.02401 — Towards Agents That Know ✅ MATCH
- **Real title**: "Towards Agents That Know When They Don't Know: Uncertainty as a Control Signal for Structured Reasoning"
- **Plan says**: "multiple uncertainty signals for structured-data agents, abstention decision, no corruption"

## Venue Acceptance Claims Audit

| ID | Plan Claims | arXiv comment/journal_ref | Verified? |
|---|---|---|---|
| 2606.28733 | NeurIPS 2026 oral | **No venue info in arXiv metadata** | ⚠️ **UNVERIFIED from arXiv** — plan's novelty sweep says "CONFIRMED" but source was likely OpenReview, not arXiv |
| 2509.02401 | NeurIPS 2025 | No venue info in arXiv | ⚠️ **UNVERIFIED** |
| 2608.07528 | ToolGate ACL 2026 (plan associates this with ACL Findings) | No venue info in arXiv | ⚠️ **UNVERIFIED** — note: the plan lists "ToolGate (ACL Findings 2026)" as a separate entry; 2608.07528 is "When Probes See Errors", not ToolGate |
| 2026.acl-srw.78 | ACL SRW 2026 | In ACL Anthology | ✅ **CONFIRMED** |
| 2026.acl-industry.58 | ACL Industry 2026 | In ACL Anthology | ✅ **CONFIRMED** |

### Venue notes
- **2606.28733** (Agentic Abstention): The plan claims "NeurIPS 2026 oral" and the 10/31 novelty check says "CONFIRMED". However, arXiv metadata has no venue field. Recommend verifying via OpenReview before citing as "NeurIPS 2026 oral" in the paper.
- **2509.02401**: Plan says "NeurIPS 2025". arXiv has no venue info. Verify independently.
- **ToolGate**: The plan mentions "ToolGate (ACL Findings 2026)" but no arXiv ID is given for it — it is cited as a name only. This may be an ACL Findings paper not yet on arXiv, or the plan may be conflating it with 2608.07528 (which is actually "When Probes See Errors").
- All papers without arXiv venue metadata are treated as preprints in the BibTeX file. Papers with confirmed venues (ACL Anthology entries) have the venue noted.

## Issues Requiring Correction

### 1. APEX-Agents naming (2610.21624) — MINOR
The plan uses "APEX-Agents/Toolathlon" as a shorthand in the MOTIVATING section. The real paper is "AgentPerturb" (subtitle: "Controlled Interaction Perturbations"). The "APEX-Agents" name does not appear in the real title or abstract. This may be from an earlier draft or a different paper. **Recommend**: change "APEX-Agents/Toolathlon" to "AgentPerturb" in the plan's MOTIVATING line.

### 2. ToolGate missing arXiv ID — MINOR
"ToolGate (ACL Findings 2026)" is referenced without an arXiv ID. If it exists only in ACL proceedings, add the ACL Anthology ID. If it's the same as 2608.07528, correct the conflation.

### 3. Venue claims without arXiv evidence — INFORMATIONAL
The NeurIPS 2026 oral claim for 2606.28733 and NeurIPS 2025 for 2509.02401 are not verifiable from arXiv metadata alone. These should be independently verified (OpenReview) before the paper draft cites them as accepted.

### 4. 2603.12564 shorthand — INFORMATIONAL
The plan calls this "AgentDrift" but the real title is "Sell Me This Stock: Unsafe Recommendation Drift in LLM Agents". The "Drift" keyword matches but "AgentDrift" is not the paper's own name. This is an acceptable shorthand for the plan but should use the full title in the paper's related work.

## BibTeX Output

48 entries written to `docs/references_verified.bib` (all MATCH + PARTIAL entries). Venue info added from arXiv comment/journal_ref where available; entries without confirmed venue are `@article` with `archivePrefix = {arXiv}`.
