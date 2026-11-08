# Updated-paper evidence review — 2026-11-08

## Scope and provenance

Reviewed HEAD `2cf023c`, on `main` synchronized with `origin/main`. New commits: `25e8b8d` (Qwen protocol), `103cc17` (540 saved Qwen replies), `2cf023c` (manuscript revision 3). No pull, rebase, model calls, manuscript edits, or push was needed for this review.

This is a bounded evidence audit and submission-readiness assessment using academic-paper-reviewer's criterion rubric, not a completed five-seat review or contract-governed Stage 3′ verification. It does not close the historical 22-item Roadmap or change its mechanical decision. Calibration status: **NOT_CALIBRATED**. No acceptance probability is estimated. The root reviewer inspected manuscript/data; a separate subagent, `updated_paper_rigor`, performed the milestone check required by program.md. These are separate execution contexts, not independent human reviewers or evidence of independent errors.

## Overall assessment

The revised paper has a defensible four-page empirical workshop contribution. It is substantially stronger than a paper centered on the twelve-query pilot: the new paired intervention has thirty queries with within-query severity crossing, shared evidence, saved raw replies, a clean-acceptance guard, and a second-model replication. It also reports the negative Qwen joint result and an exploratory deterministic-policy baseline. These are substantive improvements, not merely added volume.

**My submission advice is to repair the specific claims below, then submit a four-page empirical short paper.** I did not find an error in the new A main-result counts or registered primary analysis that invalidates those results. I would not submit the current wording unchanged, and the evidence does not establish a new verification algorithm, optimal runtime placement, or end-to-end recovery benefit. Actual acceptance remains a committee judgment; percentages such as 55–65% or 70% have no calibration basis here.

## What was verified

- Gemini archive: 810/810 completed trajectories, including the mixed-runtime code arm. This review rechecked all 540 raw/check primary-arm provider replies against frozen messages, saved parsing and decisions; it does not re-certify the code sandbox.
- Qwen3-8B archive: 540/540 completed raw/check trajectories. Reparsed provider responses, manifest/message/payload hashes and saved scores agree. Qwen's frozen units are exactly the raw/check subset of the Gemini manifest, not a fresh sample with a similar description.
- Parent canonical manifest SHA-256: `350f5a3b18b97b434b517e9b08011f19c6c92c682e71abebde214ef66dcc6a07`.
- Qwen primary effect, clean effect, cell counts and valid-triplet sensitivity reproduced. Both models' exploratory flag-only contrasts reproduced numerically (floating-point tolerance 1e-14). Thirty queries, ninety evidence units and six tables remain the analysis units; 540 replies are not 540 independent tasks.
- Qwen protocol commit is dated 2026-11-08 10:45:35 UTC; first main reply sequence started 10:52:41 UTC, result commit 11:00:45 UTC. This supports prospective registration for Qwen; it does not turn the post-Gemini flag-only idea into a pre-Gemini confirmation.
- `python experiments/export_paper_evidence.py --check`: **PASS**, 28 evidence entries, 16 hashed inputs, 11 manuscript tables. This checks generated artifacts, not every narrative claim.
- No `.tex` or PDF submission artifact exists in `paper/` at this snapshot. Layout and final anonymity are not yet verified.

## The central results in ordinary language

| Model | Corrupted candidates accepted, rows only → rows + check | Clean accepted | Change in discrimination, descriptive 95% interval | Registered joint rule |
|---|---|---|---|---|
| Gemini Flash | 85/180 → 72/180 | 88/90 → 90/90 | +9.4 points [5.0, 13.3] | Met |
| Qwen3-8B | 173/180 → 62/180 | 90/90 → 84/90 | +55.0 points [30.6, 75.6] | Not met |

Discrimination here is clean acceptance minus mean corrupted acceptance. The joint rule requires positive discrimination change and a lower clean-acceptance interval bound of at least −5 points. Qwen's clean change is −6.7 points [−11.1, −2.2], so a large improvement in corrupted rejection is not an unconditional successful replication of the joint claim. Different sampling settings prohibit treating the two gains as a controlled ranking of model quality.

The improvement consists of rejection/abstention, not repaired answers: neither aided model supplied the true numeric value for a corrupted candidate. Considerable residual error remains. A direct flag policy accepts 63/180 corrupted candidates and 87/90 clean candidates. Model mediation changes that trade-off:

| Check-arm decisions | Direct flag policy | Gemini + check | Qwen + check |
|---|---:|---:|---:|
| Clean accepted | 87/90 | 90/90 | 84/90 |
| Flagged clean candidates accepted | 0/3 | 3/3 | 0/3 |
| Flagged corrupted candidates accepted | 0/117 | 14/117 | 0/117 |
| Unflagged candidates uncertain, all types | 0/150 | 4/150 | 4/150 |

Gemini rescues all three false flags on clean values, but also overrides fourteen true flags on corrupted values. Qwen rejects every flagged candidate and additionally abstains on four unflagged candidates (three clean, one corrupted). This is more informative than saying both models simply follow the flag exactly.

## Criterion-bound assessment

Criteria are from the skill's seven-dimension rubric and empirical-research framework, applied to a focused workshop short paper, not converted into a score.

| Dimension | Judgment and criterion source | Evidence and rationale | Scope/uncertainty; decision bearing |
|---|---|---|---|
| Originality | PARTLY_MEETS; contribution relative to prior work | §3.1–3.3 combine actual-preview accounting, the row-budget sweep and same-input intervention; §6 acknowledges ToxicBench and runtime monitors | No new bootstrap method; no claim that runtime monitoring itself is novel. Limited but defensible empirical novelty affects venue positioning. |
| Methodological rigor | MEETS for the bounded B−A contrast; empirical internal-validity/reporting criterion | Frozen paired inputs, within-query clean/×1.10/×1.50 crossing, saved provider replies, six-table equal-weight analysis, explicit failed Qwen guard | Six tables, reused queries and one completion per cell limit generalization; whole-package intervention does not isolate statistical content. Supports the narrow result, not deployment. |
| Evidence sufficiency | PARTLY_MEETS; evidence must match material claims | Table 3 raw counts and effects reproduce; Table 1/2 supply complementary evidence | §3.3/§4 still overstate exact flag following, absence of incremental gain, and unavoidable clean harm. These specific sentences need repair. |
| Argument coherence | PARTLY_MEETS; conclusions must follow from measured outcomes | Stronger progression from behavior to evidence budget to intervention | §4's clean-cost claim contradicts Gemini's own results. Runtime placement is a design hypothesis. Decision bearing until repaired. |
| Writing quality | PARTLY_MEETS; precise interpretation and venue requirements | New pilot placement and Qwen negative outcome improve the narrative | Current manuscript is Markdown; no rendered four-page PDF, anonymity check or completed anonymous artifact. Submission readiness is incomplete. |
| Literature integration | MEETS for the bounded comparison; relevant-prior-work criterion | §6 recognizes existing corrupted-output adoption and runtime verification work | This audit rechecked ToxicBench and Outcome Monitors, not an exhaustive systematic search. Preserve narrow difference: numeric consistency against visible rows. |
| Significance and impact | MEETS for an empirical boundary study; workshop invites benchmarks/negative results | §3.3 shows substantial Qwen error-acceptance reduction with clean harm, and smaller Gemini benefit; flag-only comparator makes the policy trade-off concrete | Long-term tool evolution, runtime placement, recovery and deployment prevalence were not tested. Supports workshop discussion, not a validated production monitor. |

## Revisions needed before submission

### R1. “Follows the flag exactly” is factually inaccurate

**Anchor:** text: manuscript.md:97, “it follows the flag exactly”.
**Severity:** Minor for the local wording; important for interpretation. **Confidence:** 5, raw-reply and crosstab verification.

Qwen rejects 120/120 flagged candidates, but accepts only 146/150 unflagged candidates; the other four are uncertain. Its explicit accept/reject decisions agree with the flag, while its abstentions distinguish it from the deterministic policy. The Qwen report/commit wording repeats this shorthand; do not propagate it into the final paper.

Suggested wording: “Qwen rejects all 120 flagged candidates, accepts 146 of 150 unflagged candidates, and is uncertain on the other four.”

### R2. Observed non-superiority does not establish zero incremental value

**Anchor:** text: manuscript.md:97, “adds no detection beyond the flag”. Related places: abstract, §4 and conclusion.
**Severity:** Major for an inferential headline if kept as a general conclusion; repairable with existing evidence. **Confidence:** 5, contrast intervals and design.

The exploratory Gemini check-minus-flag discrimination contrast is −0.017 [−0.078, 0.039], which includes a positive gain. Qwen's is −0.028 [−0.061, 0.000]. Neither establishes equivalence, and no equivalence margin was registered. The observed point estimates do not favor aided decisions, but that is not a proof of no value from a model.

Suggested wording: “Neither aided model had higher observed discrimination than the flag-only policy; the exploratory intervals do not establish equivalence or rule out small gains.”

### R3. The model can remove false-positive harm in this sample

**Anchor:** text: manuscript.md:106, “a model in the loop does not remove it”.
**Severity:** Major for the stated system implication; repairable without new model calls. **Confidence:** 5, direct contrary evidence.

This sentence is contradicted by Gemini: it accepts all three falsely flagged clean candidates, yielding 90/90 clean acceptance versus 87/90 for the flag-only policy. It also accepts fourteen flagged corrupted values, trading fewer false rejections for more false acceptances. Qwen instead inherits all three false rejections and adds three clean abstentions. The flag's false-positive rate is not the fixed clean cost of every model-mediated policy.

Suggested replacement: “Acting directly on the flag rejects 3/90 clean candidates here. Model mediation changes the trade-off: Gemini accepts those three candidates but also overrides fourteen flags on corrupted values; Qwen rejects the three falsely flagged clean candidates and abstains on three additional unflagged clean candidates.”

### R4. Preserve the boundary between intervention and runtime design

**Anchors:** manuscript.md §§3.3–5, especially lines 103–109 and 113–115.
**Severity:** Minor while the existing “design hypothesis” limitation remains explicit. **Confidence:** 4, scope audit.

A tests an auxiliary information package in isolated audit prompts. It does not randomize runtime versus prompt-level placement, run a recovery policy, isolate warning text, or establish net benefit at real fault prevalence. Existing limitations are useful; keep the system proposal visibly conditional. The runtime-mixed Gemini C arm cannot answer a fair computation-access comparison. No new C efficacy claim is justified.

### R5. Keep Gemini trajectory denominators distinct

**Anchors:** manuscript.md:7 and §3.1, especially line 57.
**Severity:** Minor with existing §3.1 disclosure; material if treated as a model ranking. **Confidence:** 5, documented audit scope.

Gemini has 93 non-single-scalar first poisoned outputs among 128 fired trajectories. Its 56% adoption headline is not a uniform scalar-event comparison with Qwen. The new A inputs are shared; this strengthens model-within-arm evidence without repairing the old P4 unit mismatch. Make the abstract's “scalar” wording consistent with this boundary.

### R6. Finish the submission artifact and synchronize supporting prose

**Anchors:** paper/README.md and paper/ directory inventory.
**Severity:** Minor scientific issue, necessary submission task. **Confidence:** 5, current file inventory.

README still says “any checker” has insufficient evidence and that the manuscript has not incorporated A, despite revision 3 doing so. It also has obsolete artifact/table counts. Fix these stale summaries. Use the official AAAI template, verify the actual four-page body, supply an anonymous artifact, and inspect PDF metadata/links and artifact paths for identity leaks. Existing review/audit files are internal material and should not be dumped indiscriminately into a double-blind artifact.

## What has improved since the earlier review

The old universal information-bound interpretation is gone; preview behavior is correctly described as observational; three context tiers are distinguished from the replicate; intrinsic missing sanity is separated from a learned scorer's failed gates; Gemini recovery sequencing is more precise; pilot uncertainty and numerical-answer coverage remain visible. The new thirty-query severity crossing fixes the earlier pilot's severity/query confounding for A. The paper now presents Qwen's failed joint criterion instead of hiding it. These are genuine repairs, though they are not a formal closure of the historical Roadmap.

## Strongest likely rejection argument and proportionate response

“This is an ordinary bootstrap interval plus prompting; agents trusting bad tools and runtime monitors are already known.” That objection remains credible for a main-conference method paper. For this workshop, the defensible response is narrower: a reproducible measurement of the boundary between visible evidence, model decisions and an explicit statistical policy, including a two-model intervention and its clean-versus-corrupt trade-off. Do not answer it by presenting standard bootstrap as algorithmic innovation or by claiming deployed system value.

Outcome Monitors already measures runtime interventions and recovery, including warning-content controls. ToxicBench already measures corrupted evidence adoption and verification. The new work should distinguish its specific visible-row consistency constraint and evidence-budget measurements. The combined boundary study can be worthwhile even when the simplest policy is competitive.

## Next action

No additional large Gemini/Qwen run is required to make the current bounded short-paper claims defensible. First repair R1–R3, synchronize the abstract/conclusion/README, format and anonymize the four-page submission, then review that exact PDF. This is higher priority than adding another broad matrix.

If the authors want a stronger claim that statistical content itself beats a warning, a separately registered generic-caution control would be needed. If they want equal-computation comparison, register a uniform code-access replication. If they want deployment benefit, define and measure the follow-up action, costs and clean/error trade-off. These are optional claim expansions, not retroactive conditions for the present descriptive intervention study.

## Venue and primary-source checks

As checked on 2026-11-08, the workshop is non-archival, welcomes empirical benchmarks and negative results, offers four-page short/position papers, and requires AAAI 2027 format and double-blind submission. Deadline: **2026-11-20 AoE**. The tool verification/observability fit is reasonable; long-horizon evolution remains proposed context rather than a measured outcome.

- [Official workshop call](https://trust4rsi-agent.github.io/AAAI2027/)
- [ToxicBench: When Tools Silently Lie](https://arxiv.org/html/2609.37153v1)
- [Outcome Monitors](https://arxiv.org/html/2608.19303)
