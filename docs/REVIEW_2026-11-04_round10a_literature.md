# Literature Review Round 10a — 2026-11-04

Sweep date: 2026-11-04. Prior sweep: 2026-10-31 (round 9, 4-strategy deep search covering arXiv 10/15–10/31, citation-graph forward, non-arXiv NeurIPS/ACL/GitHub/SDK, devil's advocate). This review covers 2026-10-31 through 2026-11-04 and re-checks ToxicBench adoption.

---

## 1. Search Log

| Date | Source | Query | Hits | Notes |
|------|--------|-------|------|-------|
| 2026-11-04 | arXiv API | `all:tool AND all:output AND all:verification AND all:agent AND all:uncertainty` | 6 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:corrupted AND all:tool AND all:return AND all:detection AND all:LLM` | 2 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:tool AND all:poisoning AND all:agent AND all:benchmark` | 41 | **2611.03555** (11/02) new |
| 2026-11-04 | arXiv API | `all:observation AND all:uncertainty AND all:agent AND all:abstention` | 5 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:tool AND all:call AND all:result AND all:validation AND all:hallucination` | 10 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:agent AND all:trust AND all:tool AND all:output AND all:calibration` | 7 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:ToxicBench` | 2 | Only the original paper + unrelated (toxic text in images) |
| 2026-11-04 | arXiv API | `all:tool AND all:return AND all:anomaly AND all:detection AND all:agent` | 2 | No new post-10/31 |
| 2026-11-04 | arXiv API | `all:observation AND all:context AND all:information AND all:capacity AND all:detection` | 11 | None relevant to agent UQ |
| 2026-11-04 | arXiv API | `all:tool AND all:output AND all:corruption AND all:agent AND all:detection` | 10 | **2610.41191** (10/30), **2610.40913** (10/29) new |
| 2026-11-04 | Semantic Scholar | arXiv:2609.37153 (ToxicBench) citations | 1 citation | Only 2610.30491 (already known) |
| 2026-11-04 | Semantic Scholar | arXiv:2608.22676 citations | 1 | 2610.11514 (already known) |
| 2026-11-04 | Semantic Scholar | arXiv:2608.19303 citations | 3 | **2611.01930** (11/01) new; 2609.39989, 2609.33153 (pre-10/31, check if missed) |
| 2026-11-04 | Semantic Scholar | arXiv:2610.09115 (VoS) citations | 1 | 2610.29135 (LaVGuard, value drift, not UQ) |
| 2026-11-04 | Semantic Scholar | arXiv:2608.27750 citations | 0 | — |
| 2026-11-04 | Semantic Scholar | arXiv:2608.07528 citations | 1 | 2609.31788 (CT report, unrelated) |
| 2026-11-04 | Semantic Scholar | arXiv:2610.30491 citations | 0 | — |
| 2026-11-04 | Semantic Scholar | arXiv:2608.11552 citations | rate-limited | Not retrieved after 3 retries |
| 2026-11-04 | Semantic Scholar | arXiv:2610.21624 citations | rate-limited | Not retrieved after 3 retries |
| 2026-11-04 | Semantic Scholar | Mao ACL-SRW search | rate-limited | Not retrieved after 3 retries |
| 2026-11-04 | OpenAlex | `title.search:ToxicBench` | 0 | Not indexed yet |
| 2026-11-04 | GitHub API | turambar928/Toxic_Tool_Bench | 0 stars, 0 forks | Unchanged since 09/30 |
| 2026-11-04 | GitHub API | repo search `ToxicBench OR Toxic_Tool_Bench` | 3 repos | 2 unrelated (sprintml = toxic images; L46 = course project) |

**Limitations**: Semantic Scholar rate-limited (429) on 5 of 13 queries despite 4–10s delays and retries. The 3 anchors not retrieved (2608.11552, 2610.21624, Mao) were checked in the prior round 9 sweep (10/31) and had 0 new citations at that time; the gap is 4 days. GitHub code search requires authentication and was not completed.

---

## 2. Screening

**Records found**: 10 arXiv queries returned 70 entries (deduplicated to ~55 unique). S2 citation-graph returned 8 citing papers across reachable anchors.

**Excluded (with reason)**:
- 48 arXiv results: pre-10/31 and already in the plan's ~46 known papers OR topically unrelated (anomaly detection in video/network/medical, RL for weather, materials simulation, coding backdoors, face detection, etc.)
- 2610.29135 (LaVGuard): value drift in preference alignment, not tool-return UQ
- 2609.31788 (SelfCue): CT report generation, unrelated
- 2609.39989 (Component Replacement scoping review): reviews skill/tool replacement, no UQ signals
- 2609.33153 (Skill estimands): evaluation validity for tool use, no detection signals
- 2611.00138 (Kerkoporta): structured-output backdoors in coding agents, attack paper not detection
- 2610.27244 (AutoRedClaw): red-teaming for persistent agents, security evaluation not UQ
- 2610.27115 (PROVISO): provenance-tracking controller for action selection, systems/prevention not UQ measurement
- 2610.01349 (PACE): provenance-aware capability enforcement, systems/prevention not UQ

**Included for detailed assessment**: 4 papers (below).

---

## 3. New Papers Since 10/31 or Missed

### 3.1. 2611.03555 — MCP Tool Poisoning in Agentic AI Frameworks (2026-11-02)
**What it does**: First cross-framework measurement of MCP tool poisoning with real tool execution. 25-class root-cause taxonomy. 9,720-cell susceptibility matrix across 12 frameworks x 5 models x 27 attack types. Measures model compliance with poisoned tool descriptions/schemas/responses AND confirms real execution.

**Overlap with C1/C2/C3/mechanism**: **NONE**. This paper studies *tool description poisoning* (attacker controls the tool's metadata to trick the agent into calling it or misusing it) — a supply-chain attack on the *input* to the tool call. Our work studies *tool return poisoning* (the tool's *output* is corrupted) and whether the agent or a checker can *detect* the corruption. Different threat model, different evaluation unit, no UQ signals measured.

**What it means for us**: Cite as motivation ("tool outputs are another unvalidated surface; even the protocol itself carries attacker-controlled content"). Does not compete with any contribution.

**URL**: https://arxiv.org/abs/2611.03555

### 3.2. 2611.01930 — RECEIPT: Measuring and Repairing the Return Assumption of LLM Agents (2026-11-01)
**What it does**: Studies the "return assumption" — that each tool call returns within bounded time with its action finished. Measures how agents handle commands that ask questions before acting (stdin blocking). Proposes harness repairs (pty wrapping, timeout policies).

**Overlap with C1/C2/C3/mechanism**: **NONE**. This is about *tool execution semantics* (did the command actually run?) not *tool output correctness* (is the returned value right?). No UQ signals, no corruption, no detection.

**What it means for us**: Tangentially related as another "things that go wrong at the tool boundary" paper. Optionally cite in passing. Does not compete.

**URL**: https://arxiv.org/abs/2611.01930

### 3.3. 2610.41191 — When AI Investigators Cannot Trust Their Tools: Conflict-Aware Evidence Verification (2026-10-30)
**What it does**: Studies conflicts *among* multiple detection tools in a cyber-threat-investigation agent. On CIC-IDS2017, corrupts tool outputs under varying threat models (number of corrupted tools, persistence, confidence). Measures whether the agent detects conflicting evidence and recovers.

**Overlap with C1/C2/C3/mechanism**: **PARTIAL (C1 surface-level only)**. This paper does corrupt tool outputs and measure detection — but in a *multi-tool conflict resolution* setting (4 IDS detectors, discrete labels), not a single numeric return. No UQ signals compared; no preview-context axis; no scorer; no paired clean/poisoned taxonomy. The detection mechanism is cross-tool consistency checking, not observation-level uncertainty estimation.

**What it means for us**: Should cite. Positioning: "they study *inter-tool conflicts* in a security domain with discrete labels; we study *intra-return anomaly* on a single numeric tool with continuous severity and ask which uncertainty signals detect it." Complementary, not competing.

**URL**: https://arxiv.org/abs/2610.41191

### 3.4. 2610.40913 — Coupled or Independent? Fault Coupling in Agentic Medical Vision Systems (2026-10-29)
**What it does**: Tests whether intermediate tool outputs (segmentation, retrieval) in a medical vision agent can provide a safety check when the sensor input is itself faulty. Defines a coupling taxonomy (single-channel vs joint errors). Shows 81% of joint errors are "agreement errors" — tool and reasoning both fail the same way.

**Overlap with C1/C2/C3/mechanism**: **PARTIAL (C2 surface-level only)**. The fault coupling taxonomy (single-channel / joint-agree / joint-disagree) has structural similarity to our capability/observation taxonomy, but in a vision domain with continuous visual inputs, not numeric tool returns. No UQ signals, no corruption detection, no information-capacity analysis.

**What it means for us**: Cite in related work. Positioning: "they taxonomize fault coupling across vision channels; we taxonomize failure source (capability vs observation) in numeric tool returns with paired clean/poisoned labels."

**URL**: https://arxiv.org/abs/2610.40913

### 3.5. Previously missed (found via S2 citation graph, pre-10/31)

- **2609.39989** (2026-09-30) — Component Replacement scoping review. Not relevant (no UQ signals). Excluded.
- **2609.33153** (2026-09-27) — Skill estimands and evaluation validity. Not relevant (evaluation methodology, no detection). Excluded.

---

## 4. ToxicBench Adoption

| Metric | Value | Source | Date |
|--------|-------|--------|------|
| S2 citation count | **1** | https://api.semanticscholar.org/graph/v1/paper/arXiv:2609.37153 | 2026-11-04 |
| Citing paper | 2610.30491 "What the Trace Shows and What the Label Says" (already in our plan) | S2 | pub 2026-10-21 |
| OpenAlex indexing | **Not indexed** (0 results for title search) | OpenAlex API | 2026-11-04 |
| GitHub: turambar928/Toxic_Tool_Bench | **0 stars, 0 forks** | GitHub API | 2026-11-04 |
| Last push | 2026-09-30 | GitHub API | — |
| Other repos with "ToxicBench" | 2 unrelated: sprintml/ToxicBench (toxic text in images, 5 stars), chrisschnabl/L46-ToxicBench (course project, 0 stars) | GitHub API | 2026-11-04 |
| Experiments by others on ToxicBench | **None found** | All sources | 2026-11-04 |

**Assessment**: ToxicBench remains essentially uncited (1 citation that uses it as a motivating example, not as a benchmark) and unforked. No one has run experiments on it. The repo has not been updated since the paper's submission date. We remain the first to run a systematic study on it.

### Mao ACL-SRW (2026.acl-srw.78)

S2 was rate-limited for this query (3 retries failed). However:
- The paper was a doctoral **proposal** with zero experiments, published at ACL-SRW (student research workshop)
- As of the 10/31 sweep it had 0 S2 citations
- No arXiv follow-up found in any of our 10 queries
- Risk assessment unchanged: the proposal sketches step-wise UQ in think-act-observe loops but has produced no experimental follow-up in the ~4 months since publication

---

## 5. Verdict per Contribution

### C1 (Signal matrix at the observation step) — **STILL OPEN**

**Evidence**:
- No new paper since 10/31 compares multiple UQ signals at the tool-return/observation step
- 2610.41191 (conflict-aware verification) corrupts tool outputs but uses cross-tool consistency, not per-return UQ signals — different evaluation unit
- 2608.22676 (nearest prior, 2 signals in 1 domain) has only 1 new citation (2610.11514, about test validity, not signal comparison)
- ToxicBench still has 0 experimental users besides us
- The continuous observation-context-richness axis (k visible rows → AUROC) remains unoccupied by any paper

**Verdict**: **STILL OPEN**. The gap is real and unchanged.

### C2 (Capability vs observation failure taxonomy) — **STILL OPEN**

**Evidence**:
- No new paper separates capability failures from observation failures using paired clean/poisoned runs
- 2610.40913 (fault coupling) has a structural analogy (single-channel vs joint error) but in vision, with no paired corruption and no UQ signal comparison
- AgentDrift 2603.12564 (info-channel vs memory-channel) remains the nearest, but decomposes by mechanism not by outcome
- The free-label insight (ToxicBench pairs give failure-source labels without annotation) remains unique

**Verdict**: **STILL OPEN**. No competition.

### C3 (Clean-trained predictive scorer) — **NEGATIVE RESULT (unchanged)**

**Evidence**:
- Our own F8 shows the K=5 Qwen2.5-0.5B scorer is at chance (0.50–0.52) on every agent and tier
- No other paper has attempted a clean-only predictive scorer for tool-return anomaly detection
- The negative result itself is a contribution: it establishes that a 0.5B model trained on ~1,800 clean examples learns column scale but not the statistic within the resolution needed for detection at ToxicBench poison strengths

**Verdict**: **STILL OPEN as a negative-result column**. No one has tried this and failed, so reporting the failure with the reason (resolution vs poison magnitude) is novel.

### Information-capacity mechanism (0o* curve, estimator loss decomposition) — **STILL OPEN**

**Evidence**:
- No paper characterizes how detection AUROC varies with the number of visible context rows (k)
- No paper decomposes the detection gap into "estimator loss" (what the checker leaves on the table) vs "oracle knowledge" (what no k-row checker can have)
- The draw-conditioned oracle 0o* as an achievable ceiling concept appears nowhere in the agent-UQ literature
- 2610.32110 (Warped Formatters) and 2610.11514 (SSCBench) are cited as real-world analogues of context reduction, but neither measures the AUROC–vs–k curve

**Verdict**: **STILL OPEN**. This is the most distinctive analytical contribution and remains entirely unoccupied.

---

## 6. Overall Assessment

### Is the work still worth publishing?

**Yes.** All four contributions remain open:
- C1 (signal comparison at observation step): no competitor in the 4-day window; ToxicBench still unused
- C2 (failure-source taxonomy): no competitor
- C3 (scorer negative result): honest reporting of a failed approach, novel as a data point
- Information-capacity mechanism (0o* curve): no competitor; the most analytically distinctive piece

The 4 new papers found (2611.03555, 2611.01930, 2610.41191, 2610.40913) are all in adjacent spaces (MCP protocol security, harness semantics, multi-tool conflict, vision fault coupling) and do not overlap with our evaluation unit (single numeric tool return × multiple UQ signals × context-richness axis).

### Positioning sentence changes

**No changes needed.** The two-sentence pitch and central claim from the plan remain accurate. Two optional additions for related work:

1. **Add cite**: 2610.41191 as "conflict-aware verification across multiple tools" (complementary: they detect inter-tool conflicts, we detect intra-return anomalies)
2. **Add cite**: 2610.40913 as "fault coupling taxonomy in vision agents" (complementary: structural analogy to C2 in a different domain)
3. **Add cite**: 2611.03555 as motivation (MCP tool poisoning confirms tool outputs carry attacker-controlled content into model context)

### Risk update

- **Scooping risk**: LOW (unchanged from 10/31). No paper in the 4-day window moves toward our evaluation unit.
- **ToxicBench adoption risk**: LOW. Still 0 forks, 0 experimental users. If someone does fork it, they are more likely to run it as a benchmark (validating our choice) than to do a multi-signal UQ study.
- **Mao follow-up risk**: LOW–MEDIUM. S2 was rate-limited so we could not confirm 0 citations, but no arXiv follow-up found. The proposal is 4 months old with no experiments. Even if Mao publishes, her framing ("when does an agent know it is lost") is trajectory-level step confidence, not observation-level UQ with context-richness.

### Next sweep

Schedule for 2026-11-07 (before MATH4AI 11/20 deadline if targeting a 4p submission). Re-check S2 for the 3 rate-limited anchors (2608.11552, 2610.21624) and Mao.
