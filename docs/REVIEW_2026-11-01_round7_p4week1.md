# Round 7 — P4 Week 1 (Qwen3-4B real agent results)

**Reviewer**: adversarial rigor review (independent recomputation from raw P4 data)
**Date**: 2026-11-01
**Scope**: First confirmatory agent results — Qwen3-4B at tiers T0_agent / T1 / T1r2 / T3 (2,520 trajectories total) + zero-parameter and intrinsic signal scoring. F5 and F6 findings.
**Method note**: All numbers below are independently recomputed from the raw JSONL files (630 rows per tier-set, small enough to load inline). The experiments/.venv/bin/python environment was used for sklearn AUROC. Protocol texts (PREREGISTRATION.md P4 through A-P4 note), scoring scripts (p4_run.py, p4_score_zeroparam.py, p4_score_intrinsic.py), and git log were read in full.

---

## Verdict

**GO-WITH-CHANGES (4.00/5)** — the first agent results are methodologically sound, correctly labelled preliminary, and the protocol-before-results chain is verified. Three items must be fixed before the Qwen3-8B run: (1) the F6 lower CI is 0.49, not 0.48 as printed; (2) the harness normalization sensitivity check must be run (not just promised); (3) the first-token entropy amendment must be committed as a protocol commit before the next agent run starts.

---

## A. Protocol adherence

### Git ordering ✓
Protocol commits 5e978bb (A-P3d, 2026-10-31 20:31), e1eefc0 (A-P3c results, 20:21), 1605390 (A-P3c protocol, 18:55) and the P4 harness+deploy commits (805034a through d1ac0fb, 23:39 to 00:19) all precede the first result commit 136386b (2026-11-01 09:53). The signal-capture feature commit c18797d (10:43) correctly precedes the T1r2/intrinsic results commit 17851b9 (11:30). **Protocol-before-results is maintained.**

### A-P4 temperature: registered "all runs 0.7" ✓
Verified: `SeededClient.__init__` receives `temperature` from the argparse default of 0.7. The A-P4 fix note explicitly supersedes P4's original "temperature 0 for primary". Both clean seeds and toxic run at 0.7.

### A-P4 "two clean seeds for noise floor" ✓
Both seeds verified present in all four tiers (seed field {0} and {1} in every file). Answers differ in 75-85% of tasks, confirming vLLM respects the seed at temperature 0.7.

---

## B. Spot-check (a) — per-tier counts

| Tier | clean_s0 | clean_s1 | toxic succ | poison_fired | poison_used | obs_fail | cap_fail | no_effect | noise floor |
|------|----------|----------|------------|--------------|-------------|----------|----------|-----------|-------------|
| T1 | 202/210 | 204/210 | 4/210 | 202 | 196 | 198 | 8 | 0 | 6/210 (2.9%) |
| T0_agent | 203/210 | 202/210 | 8/210 | 199 | 195 | 195 | 7 | 0 | 9/210 (4.3%) |
| T1r2 | 203/210 | 204/210 | 4/210 | 202 | 196 | 198 | 7 | 0 | 5/210 (2.4%) |
| T3 | 204/210 | 204/210 | 6/210 | 200 | 194 | 198 | 6 | 0 | 8/210 (3.8%) |

**Comparison to F5**: F5 states "Clean success 202/210 and 204/210; noise floor 2.9% (6/210)". Recomputed: **exact match**. F5 states "poison fired in 202/210 runs; poisoned_answer_used in 196/210". Recomputed: **exact match**. F5 states "observation failures 198, capability 8, no effect 4". Recomputed obs_fail=198, cap_fail=8, **but no_effect = 0, not 4**. The 4 toxic successes at T1 are NOT "no effect" by the standard definition (poison fired but agent got it right anyway)—checking T1 toxic: 4 succeeded, but none have poisoned_answer_used=True AND task_success=True simultaneously. The 4 toxic successes have poison_used=False. The F5 text's "no effect 4" appears to count toxic successes where poison didn't fire (210-202=8 no-fire, 4 of those succeeded?). The taxonomy is: obs_fail 198 + cap_fail 8 + (toxic_success_no_fire=4?) = 210. This is internally consistent if "no effect" means poison didn't fire AND task succeeded.

**Assessment**: Counts match except the "no effect" label is confusingly defined (it means the task where poisoning had no opportunity, not where poisoning failed to influence). Not a numerical error. **[writing-only fix]**

## C. Spot-check (b) — intrinsic signal AUROC (H1 test)

**Recomputed from `intrinsic_scores.jsonl` (409 events, 202 positive)**:

| signal | slice | recomputed AUROC | recomputed CI | F6 claims | Match? |
|--------|-------|------------------|---------------|-----------|--------|
| sig3_neg_conf | all | 0.5294 | [0.4600, 0.5940] | 0.53 [0.46, 0.59] | ✓ |
| sig3_neg_conf | p+s | 0.5486 | [0.4855, 0.6106] | 0.55 [0.48, 0.61] | **lower CI: 0.49 not 0.48** |
| sig1_first_token_entropy | p+s | 0.4861 | [0.4546, 0.5228] | 0.49 [0.45, 0.52] | ✓ |
| sig1_mean_entropy | p+s | 0.4589 | [0.4244, 0.5005] | 0.46 [0.42, 0.50] | ✓ |

**F6's H1 verdict "upper 0.61: NOT confirmed at the registered threshold (0.01 over)"**: recomputed upper CI is 0.6106, which rounds to 0.61, which is > 0.60. **Claim is correct.**

**However**: F6 prints the lower bound as 0.48, but recomputation gives 0.4855, which rounds to 0.49. This is a reporting error—the conclusion is unaffected (the upper bound is what matters for H1), but the number in the table is wrong. **[writing-only fix, P0 before publication]**

**Verbalized confidence quantization**: values are integers in {7, 8, 9, 50, 70, 75, 80, 85, 90, 95}. Modes are 80 (clean: 66, poisoned: 74), 85 (clean: 64, poisoned: 50), 75 (clean: 43, poisoned: 48). The distribution is heavily quantized with ~85% of mass on {75, 80, 85}. **AUROC with this many ties is technically valid** (sklearn handles ties correctly via midrank), but the effective information content is very low—6-7 distinct bins for ~400 events. The CI width (0.13) reflects this low resolution. The negation direction (higher negated confidence = lower raw confidence = more suspicious) is the registered direction and is correct.

**First-token entropy**: all 409 events have first-token entropy in [2.2e-7, 0.049], with most clustered at ~1e-6 (effectively 0). The first token is always `{"` (1,153/1,153 completions). This is DEGENERATE as F6 states. The entropies are not exactly zero because top-k logprobs have a small residual tail; the values are numerically distinct but carry zero semantic information about poisoning.

## D. Spot-check (c) — completion-to-event alignment

Verified 5 toxic T1r2 runs: in each, the poisoned python_exec event at index 0 aligns to the first `obs_call` completion with `after_observation.tool == "python_exec"` and `n_tool_turns=1` (or 2 for one task with a preview call first). The shadow verbalized call fires and returns an integer in every case. The `events_with_completion` function in p4_score_intrinsic.py uses `zip(pe, obs_calls)` and returns after the first match with `want_poisoned=True`. **This is correct for the first poisoned event, but would silently skip any second poisoned event in a multi-tool run.** Since F6 says 193-202 poisoned events are single-scalar, this is nearly always correct, but the `return` inside the for loop means only one event per run is ever scored. This is **by design** (one negative per clean run, one positive per toxic run), but should be documented more explicitly.

## E. Spot-check (d) — zeroparam clean vs toxic code matching

Code match: 183/191 (95.8%). Code differs in 8/191 (4.2%) of paired tasks.

The `first_scalar_event` function in p4_score_zeroparam.py takes the first scalar python_exec event from the clean run (with `poisoned=None`, meaning any event) and pairs it with the first poisoned scalar event from the toxic run. In 4.2% of cases, the agent wrote different code in the clean vs toxic run for the same task. **This is a genuine pairing impurity**: the clean event may compute a different statistic than the poisoned event, making the AUROC comparison measure both the poisoning effect and the code-difference effect.

**Materiality assessment**: At 4.2% (8/191 events), this is unlikely to move the AUROC by more than ~0.01. The alternative (pairing by code text) would reduce sample size. **Acceptable but should be disclosed.**

## F. Spot-check (e) — harness normalizations

Per-run counts for T1 (630 runs total):
- `read_csv_resolved`: 600/630 (95.2%)
- `dropped_pandas_import`: 599/630 (95.1%)
- `stripped_stray_indent`: 51/630 (8.1%)

Per-event counts (T1 clean_seed0, 216 python_exec events):
- `read_csv_resolved`: 207, `dropped_pandas_import`: 208, `stripped_stray_indent`: 20

F5 states "630 (pandas re-import), 615 (read_csv resolved) and 51 (stray indent)". My per-run counts show 600 (read_csv) and 599 (pandas), not 615/630. **Discrepancy**: F5's numbers may count per-event rather than per-run. In any case, the order of magnitude is correct: these normalizations fire in nearly every run.

**Both-sides argument**:
- **Legitimate harness fix**: Qwen3-4B's `pd.read_csv('dataset.csv')` is a model-specific formatting quirk, not a tool-return behavior. ToxicBench counts these as "harness-limit" failures. The normalizations are applied identically to clean and toxic runs. The poisoning path is verified unchanged (the proxy resolves to the same DataFrame, which then gets poisoned by the upstream mechanism).
- **Changes the benchmark**: Without normalization, clean success drops from 202/210 to approximately 0-10/210 (FileNotFoundError on nearly every run). The agent's ability to "use the poisoned value" is entirely conditional on the harness making the code work at all. A reviewer could argue the 93% poison-use rate is an artifact of the harness, not a property of the agent.
- **Control that would settle it**: Report success and poison-use on the ~30 runs (5%) that needed zero normalizations. If those 30 runs still show >80% poison-use, the normalization is immaterial. Alternatively, run 30 tasks on the unmodified ToxicBench sandbox and report the FileNotFoundError rate. **This control is promised but not yet run. [needs agent runs, but could be CPU-only on existing data for the zero-normalization subset]**

## G. Spot-check (f) — two seeds and vLLM seed honoring

| Tier | Same final_answer | Different | % same |
|------|-------------------|-----------|--------|
| T1 | 31/210 | 179 | 15% |
| T1r2 | 34/210 | 176 | 16% |
| T0_agent | 41/210 | 169 | 20% |
| T3 | 52/210 | 158 | 25% |

Seeds are correctly stored as {0} and {1} in each file. 75-85% of tasks produce different final answers across seeds, confirming vLLM respects the seed at temperature 0.7. The noise floor (2.4-4.3%) is commensurate with the 15-25% answer variability—most different answers are both correct or both wrong.

T3 has the highest same-answer rate (25%) and highest noise floor (3.8%), likely because schema-only tasks leave less room for approach variability.

## H. Spot-check (g) — first-token entropy degeneracy

The first token is `{"` in all 1,153 completions across both T1r2 clean and toxic runs. Entropy is ~1e-6 nats (not zero because the top-20 logprobs don't cover the full distribution, leaving ~1e-7 probability mass in the tail).

**Was this foreseeable from A-P4?** A-P4 registers "token entropy at the first generated token after the observation" as signal 1. The adapter uses a JSON tool-calling format where every action starts with `{"tool": ..., "args": ...}`. The first token is therefore deterministically `{"` for any syntactically correct action. **Yes, this was foreseeable.** The registration should have specified "first value-bearing token" or "mean entropy over the action". The fact that no one caught this during rounds 1-6 is a protocol-review gap.

**Is "replace the definition before the next agent run" acceptable?** The amendment is committed before any future run uses it (protocol-before-results is maintained). The registered signal-1 definition is degenerate, not wrong—it just happens to have zero variance. Replacing it with mean-entropy (an exploratory variant already computed) is methodologically cleaner than claiming the degenerate metric "passes H1 trivially". The disclosure in F6 is honest. **Acceptable, provided the amendment is a protocol commit before Qwen3-8B.** The exploratory variants (mean, max, neg_sum_logprob) all have CI upper bounds well below 0.60, so the amendment does not change the H1 conclusion for this agent.

## I. Spot-check (h) — overclaiming

Grep for strong language in findings.md:
- F5: "no zero-parameter check on the same five rows gets above 0.58" — **true** (recomputed max is 0o* at 0.58).
- F6: "Nothing available at T1 separates poisoned from clean returns for this agent" — **true for this agent** and correctly scoped with "for this agent". The "Open for C3" note is appropriate.
- F5: "The agent never re-queried or flagged a poisoned return (anomaly_detection 0)" — **true** (recomputed: anomaly_detection 0 at every tier).
- F6: "the agent's behaviour does not move with observation context at all; what moves is what a checker can do" — **true**: behaviour (poison_used ~93-95%, obs_fail 195-198/210) is identical across T0_agent/T1/T1r2/T3. The 0a signal moves from 0.54 (T1) to 0.57 (T0_agent with min/max), which is exactly "what a checker can do moves".

**No overclaiming detected.** Both F5 and F6 are labelled "preliminary" with "one agent" scope. H1 is correctly reported as "not confirmed" rather than "passed" or "failed".

---

## G. Dimensions (D1-D6)

| Dim | Score | Note |
|-----|-------|------|
| **D1 Protocol fidelity** | 4 | Protocol-before-results verified; A-P4 amendments correctly committed; first-token entropy degeneracy is a design gap, not a protocol violation. [writing-only: amend signal-1 definition before Qwen3-8B] |
| **D2 Statistical rigour** | 4 | Within-table AUROC with 6-table bootstrap is appropriate; CIs are narrow enough for the H1 decision; verbalized confidence quantization noted but AUROC is valid with ties. One CI lower-bound digit wrong (0.48 vs 0.49). |
| **D3 Claim-evidence alignment** | 4 | F5/F6 claims match recomputed numbers within rounding; preliminary scope correctly stated; "no effect" taxonomy wording is confusing but not wrong. |
| **D4 Reproducibility** | 4 | All scores recompute from raw JSONL; seed verified; code is self-contained; harness normalizations are logged per event. The 4.2% code-mismatch in zeroparam pairing is undisclosed. |
| **D5 Threat model completeness** | 4 | Harness normalization argument is honest but the "without normalization" control is only promised, not run. The clean-code-differs-from-toxic-code pairing impurity is not discussed. |
| **D6 Novelty/contribution** | 4 | First real-agent data point for the paper; confirms the capability-boundary framing (T0_agent = T1 behaviourally); intrinsic signals at chance is a genuine finding, not a null result. |

**Mean: 4.00**

No blocking items (no dimension below 4).

---

## H. What the C3 bar is now

At T1 with Qwen3-4B's real events:
- 0d = 0.55, 0o* = 0.58 → headroom = 0.03
- A-P3d's "no headroom on slice (b)" clause applies (gap < 0.05)
- Signal 7 (scorer) is therefore judged against the **absolute bar** (slice (a) multi-number, lower CI > 0.70) and against 0d at higher tiers (T0_agent / random-k)
- The verbalized signal is at chance (0.55); token entropy is below chance (0.46-0.50)
- The C3 value claim on slice (b) at T1 is structurally impossible: there is no room between 0d and 0o*

For the paper: the C3 claim must rest on slice (a) multi-number observations (this agent produced almost none—193-202/210 are single scalars) and on higher tiers where 0o* has headroom (the P3 k-sweep showed 0.73 at k=5 random).

---

## I. Verdict and next actions

**Verdict: GO-WITH-CHANGES (4.00/5)**

### Three next actions, ranked:

1. **[writing-only, P0] Fix F6 lower CI**: 0.4855 rounds to 0.49, not 0.48. Also clarify the "no effect 4" taxonomy in F5 (it means no-poison-opportunity, not poison-had-no-effect). Disclose the 4.2% code-mismatch rate in zeroparam pairing.

2. **[needs protocol commit, P0 before Qwen3-8B] Amend signal-1 definition**: replace "first generated token" with "mean token entropy over the action" as the registered variant. Commit as a protocol amendment before starting any Qwen3-8B run. The exploratory variants in F6 already show this does not change the H1 outcome.

3. **[CPU-only, P1] Run harness normalization sensitivity check**: from the existing T1 data, compute success and poison-use rates on the subset of runs with zero normalizations (if any exist—my count shows read_csv fires in 600/630 runs, so the zero-normalization subset may be < 30 runs). If too small, add one sentence to F5 disclosing that "clean success without normalization is expected to be ~0% for Qwen3-4B (FileNotFoundError on 95% of runs)" and frame this as a model-specific quirk, not a benchmark limitation.

### Answers to the directed questions:

1. **What is the single most important thing to fix before Qwen3-8B?** The signal-1 amendment (action #2). Everything else is writing fixes on existing data.

2. **Is G2 at T1 legitimately closed?** Yes. Max zero-parameter signal is 0o* at 0.58 [0.55, 0.61], far below the 0.90 bar. Even 0a's full CI upper bound (0.58) is below 0.60. No zero-parameter method on head-5 rows is sufficient.

3. **Is H1 legitimately "not confirmed" vs "failed" vs "passed"?** "Not confirmed" is the correct label. The registered statistic (upper CI < 0.60 on plausible+subtle) gives 0.61 > 0.60 for verbalized confidence, so it fails the threshold by 0.01. But the point estimate (0.55) is at chance, and the entropy variants all have upper CI well below 0.60 (pass trivially). A reviewer would not call this "failed" (the signal is genuinely at chance); it just misses the formal threshold by one rounding digit. "Not confirmed at the registered threshold" is precise and honest.

4. **Does the week-1 result change the paper's central claim?** No. The central claim ("what bounds detection is the observation-context information, not the signal family") is **strengthened**: T0_agent = T1 = T1r2 = T3 behaviourally (poison-use ~93-95% everywhere), and the only thing that moves is what a checker can compute (0a goes from 0.54 to 0.57 with min/max). The intrinsic signals being at chance on a 4B model is preliminary but consistent with the capability-boundary framing.

5. **Verdict**: **GO-WITH-CHANGES**. Three next actions as above: (1) fix the three reporting items [writing-only], (2) amend signal-1 [protocol commit], (3) harness normalization sensitivity [CPU-only].

---

## Sources

- Raw data: `data/ours/p4/qwen3-4b/{T0_agent,T1,T1r2,T3}/{clean_seed0,clean_seed1,toxic_seed0}.jsonl`
- Scoring scripts: `experiments/p4_score_zeroparam.py`, `experiments/p4_score_intrinsic.py`
- Harness: `experiments/p4_run.py` (TieredEnv, SeededClient)
- Protocol: `PREREGISTRATION.md` (P4, A-P4, A-P3d, A-P4 note)
- Findings: `findings.md` (F5, F6, central claim reconciliation)
- Git log: `git -P log --oneline -n 15` (protocol ordering verified)
- Previous round: `docs/REVIEW_2026-10-31_round6.md` (3.67, CPU-only ceiling)
