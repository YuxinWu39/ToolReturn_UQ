# Re-score after fixes: pilot P1/P2 + P3 large-table generation

Reviewer roles: ARA rigor-reviewer (D1-D6) + devil's advocate (checkpoint 2). Date: 2026-10-31.
Prior review: `docs/REVIEW_2026-10-31_pilot.md` (D1-D6 = 2, 3, 2, 3, 4, 2; mean 2.67; GO-WITH-CHANGES).

**Method note.** This session had no shell tool, so I could not run the venv Python or `git log`. I read
`.git/logs/HEAD` for commit order and recomputed numbers in two ways: (1) exact line counts over the JSONL files,
where each row has a fixed key order, and (2) a closed-form identity. For a score that is 0 on most items,
AUROC = 0.5·(1 + TPR − FPR) when every positive with a non-zero score ranks above every negative. Each
recomputed number below says which method produced it. I did **not** recompute `clean_value` with pandas; see c.

## Verdict

**GO-WITH-CHANGES.** The fixes the first review asked for were made, and each one is backed by a dated
amendment committed before the result that uses it. G1 now tests the right null and passes clearly.
The new finding F3 is computed correctly, and its main consequence holds: the "rules suffice" fork cannot
fire on the P3 tasks. But the stated reason is wrong, and F3 is worded more broadly than what was computed.
It measures a whole-column **min/max range check** on **oracle values**. It does not measure
"zero-parameter rules" as a class, and it does not measure "the full preview". The single
CPU-only experiment that decides how far F3 generalizes has not been run: 0d (re-execution) on the P3 tasks.

New mean **3.5** (D1 3, D2 4, D3 3, D4 4, D5 4, D6 3). That maps to Weak Accept as a pilot artifact.

## A. Protocol fidelity: amendments vs commit order

Epoch times from `.git/logs/HEAD`, converted to UTC using init `571f732` = 23:31:29.

| Commit | UTC | Content | Precedes the result it governs? |
|---|---|---|---|
| `bfcc88e` | 23:45:04 | A-P1, A-P2 amendments | yes, before `316a94b` (23:54:00) |
| `316a94b` | 23:54:00 | P1/P2 re-run results | n/a |
| `4cfcecf` | 00:00:15 | P3, H1/H6/C3 rewordings, single threshold | yes, before `f21468e` (00:02:46) |
| `f21468e` | 00:02:46 | P3 tasks + ceiling | n/a |
| `9fb93e4` | 00:08:16 | within-table CI (review item A8) | reporting-only change, not pre-registered; harmless |

Residual issues:
- P3 says it was "committed before `gen_tasks.py` exists". The script (13 KB) has mtime 00:01. The P3 commit
  is at 00:00:15 and the results commit at 00:02:46. Writing, downloading and running the script in about
  150 s is only plausible if it was drafted before the commit and left uncommitted. Mtimes cannot prove
  either way. **Fix:** commit drafts of analysis scripts together with the protocol, or say in the log that
  the script was drafted in parallel. [writing-only]
- The A-P2 sanity rule says "**each** content-aware signal must reach > 0.95". Only 0a is checked
  (`range_check.py` builds fake rows for `0a_*` only). 0b and 0d were never sanity-checked. [CPU-only]
- `research-state.yaml` sets G2 to `refuted-by-ceiling` and calls the P4 re-decision "a formality". P3 says
  explicitly: "it does not decide G2". That is a protocol deviation in the state file. [writing-only]
- Master plan line 20 (Contributions) still states the old fork ("> 0.90 at 5-row-no-minmax"). Line 81
  (Timeline) was updated and strikes 0.95. The plan's H6 still contains the 0a arm that PREREGISTRATION
  removed. [writing-only]

## Spot-checks

### a. Taxonomy (pairs.jsonl)
| Quantity | Claimed | Recomputed | How |
|---|---|---|---|
| b, numerical (clean ok, toxic fail) | 415 | **415** | line count, `numerical` with class in {observation_consumed, observation_exposed_only, unexposed} |
| c, numerical (clean fail, toxic ok) | 56 | **56** | line count, `cap_clean_only_fail` |
| exact McNemar p, numerical | 8.64e-69 | **≈ 8.7e-69** | Stirling estimate of 2·Σ_{k≤56} C(471,k)/2^471 (ln C(471,56) ≈ 168.9; 471·ln 2 = 326.5; geometric tail factor 1.16) |
| overall b / c | 734 / 81 | 734 = 609 + 73 + 52 ✓ | arithmetic from the summary classes |

The noise floor is computed on 737 keys: the 821 keys with duplicate clean runs where the first run
succeeded. F1' says "737 duplicate keys", which is slightly wrong; it should say 737 of 821.
**Open validity question:** those 821 keys are 23% of all keys. If their model and adapter mix differs from
the 3,633 pairs, the 4.3% floor does not represent them. The toxic-vs-toxic discordance (11.0%) is 2.5× the
clean-vs-clean discordance, which supports a real poison effect. **Fix:** report the floor per model and a
version reweighted to the pair composition. [CPU-only]

### b. Range check (events.jsonl)
| Check | Result | How |
|---|---|---|
| rows with y = 2.0 | **0** (was 20) | line count `"y": 2.0,` |
| clean rule-scope events | 508 (was 528; the 20 error strings are gone) | line count |
| 0d scope, poisoned | **575** ✓ | line count `poisoned true … 0d_scope true` |
| 0d **actually scored**, poisoned | **482 at T0/T1, 493 at T2** | `n_pos` in `range_check.log` |
| 0a_T1, plausible+subtle | **0.896** ✓ | 99/125 poisoned plausible have 0a_T1 > 0 (26 at 0.0). **0/508** clean have 0a_T1 > 0. So 0.5·(1 + 0.792 − 0) = 0.896. There are no subtle events in scope. |

Two findings from these checks:
1. **0d coverage is overstated.** 93 of the 575 in-scope poisoned events get NaN, because a bootstrap
   resample raised an error or printed `nan` (the `RuntimeWarning: invalid value … scalar divide` lines in
   the log). `reexec_interval` then returns None and the event is dropped silently. 0d's scored coverage is
   **482/1153 = 41.8%**, not 50%. That makes the uncovered remainder **58%**, not "~50%". The C3 amendment
   and F2' cite the wrong number. The NaN drops are also not random: they come mostly from filtered code
   whose resampled subset is empty, so 0d's AUROC is measured on its easier cases.
2. **On these tables, 0a@T1 is a binary flag with zero false positives.** 0b's 1.000 at T0 and T1 is
   leakage. On tables of 5 rows or fewer, head-5 is the whole table, so for `mean` events the clean z-score
   is exactly 0. F2' calls the rule "near-perfect where it parses". It should say the 0b number reflects a
   leaked mean, as P2 itself predicted for T0.

### c. Ceiling (ceiling_events.jsonl)
| Check | Claimed | Recomputed | How |
|---|---|---|---|
| 0a T0, template = unfiltered | 0.583 | **0.583** | 10/60 poisoned > 0, 0/60 clean > 0, so 0.5·(1 + 0.167) |
| 0a T0, severity = subtle | 0.542 | **0.542** | 5/60 poisoned > 0, so 0.5·(1 + 0.083), with FP = 0 |
| clean FP at T1 | 0.61 | **109/180 = 0.606** | 71 of 180 clean rows have 0a = 0 |
| `clean_value`, 9 tasks | n/a | not pandas-recomputed | Seven values match published palmerpenguins summaries: mean body_mass_g 4201.75, mean flipper 200.92, median bill_length 44.45, max flipper 231, max body_mass 6300, sum body_mass 1,437,000 (= 4201.75 × 342), Dream island count 124, female max flipper 222. The by-year means (2008: 4266.67, 2009: 4210.29) look plausible, but I could not confirm them without execution. |

Caveat on the oracle cross-check: pandas and stdlib share the same filter logic
(`astype(str) == val`), so the check validates the arithmetic, not the filter. If the string form of a
float-typed categorical did not match the CSV text, both sides would get an empty subset and the task would
be dropped. The 5 `oracle_mismatch_or_zero` drops may be exactly this case. Log which tasks were dropped. [CPU-only]

### d. Was P3 implemented as pre-registered?
| P3 item | Implemented | Assessment |
|---|---|---|
| op mix 40/20/15/15/10 | Independent weighted draws; `grouped` + `count` is silently changed to `mean`. Realised mix: mean 76 (42%), sum 36 (20%), median 30 (17%), max 23 (13%), count 15 (8%) | Acceptable as a random draw; disclose the count→mean substitution |
| symmetric scales, balanced | A fixed 12-cycle `scale_cycle[len(tasks) % 12]` in generation order: 15 per scale, severities 60/90/30 ✓ | Balanced overall, but **not within template**. Each table's 10 unfiltered tasks cover 10 consecutive cycle positions, which include exactly one of {2.0, 0.5}. So unfiltered has only about **6 obvious tasks**, while filtered gets the full set. Template×severity comparisons are confounded. |
| power: ≥ 60 per template, "generate more with next seed" | grouped = **30**, and no regeneration happened | **Deviation.** P3 contradicts itself: 5 grouped per table × 6 tables = 30 < 60. The rule P3 committed to was not executed. |
| 0a interval for filtered/grouped | Whole-column visible rows (`visible_stats(df, …)`; the `df if template != "filtered" else df` branch does nothing) | **Correct design** for "what a range check knows from the preview". ToxicBench's preview shows whole-table `numeric_min/max` and head rows, and the whole-column range is a valid conservative bound for a subset's mean, median or max. P3 implies it ("T0 (full column)") but does not say it explicitly. |
| sum multiplier | filtered sum: × **subset count** (information the preview does not give); grouped sum: × **full n** (a very loose interval) | **Inconsistent and not in P3.** Pick one: either preview-only (× n, disclosed as loose), or an exec-capable checker (× subset count, which is 0d territory). Report both. |
| 0b at T0 | whole-column mean and std | **Uses information the preview does not show** (P2: the preview leaks min/max only). For unfiltered `mean` tasks, clean 0b = 0 exactly, so the 0.79 unfiltered figure for 0b is inflated by this leak. |
| T1/T2 = head-k | head of the file as stored | Several tables are ordered (Bike by hour, Penguins by species, Wine red then white). Head-5 is a **biased** sample, not just a smaller one, so the 61% clean FP partly measures table order. Add a random-k tier to separate the two. [CPU-only] |

## E. Re-scored dimensions

| Dim | Before → now | One sentence | Single most important remaining fix (if < 4) |
|---|---|---|---|
| D1 Evidence relevance | 2 → **3** | G1 now uses a paired test against a measured noise floor, and G2 is correctly marked undecidable. But F3's consequence ("zero-parameter rules fail on large tables") rests on a range check alone, and 0d's coverage is misreported. | Run 0d (re-execution with bootstrap over head-k) and 0b (head-k statistics only) on the 180 P3 tasks per tier × template × severity, with within-table CIs, so F3's claim has evidence of the type it asserts. **[CPU-only]** |
| D2 Falsifiability | 3 → **4** | G1, G2, H1, H6 and C3 now have numeric, scope-matched criteria with CI bounds. Remaining weakness: on P3 tasks the G2 coverage condition (≥ 50%) cannot be met when only 33% of tasks are unfiltered, so the fork is decided by the design and is no longer a real test. | (state it explicitly in P4) |
| D3 Scope calibration | 2 → **3** | F1' and the renamed classes are well calibrated. New over-claims: F3 "at chance even with the full preview" and "a property of tiny tables"; G2 "refuted"; 0d "50%"; C3 "~50% uncovered"; 0b "near-perfect". | Rewrite F2', F3, `research-state.yaml` and the C3 line: whole-column min/max (not "full preview"); 0d 41.8%; 58% uncovered; 0b leakage; G2 = "expected to fail by the hit-rate bound, decided at P4". **[writing-only]** |
| D4 Argument coherence | 3 → **4** | The new Central-claim section, the C3 amendment and the single threshold make the arc consistent, and F3 supports the central claim. Two leftovers: plan line 20 and the plan's H6. | (writing-only cleanup, listed in A) |
| D5 Exploration integrity | 4 → **4** | Reversals are recorded rather than buried (F1 → F1', fork inverted). F2 is not marked as superseded and still says "fork provisionally" and "filtered 75%". | (mark F2 superseded) |
| D6 Methodological rigor | 2 → **3** | Noise floor, McNemar, clustered and within-table CIs, sanity rows, SHA-256 provenance and the oracle cross-check are real improvements. Open problems: the P3 power rule was not executed, template×severity is unbalanced, the ceiling has no CI or within-table version, 0d drops NaNs silently, sanity checks cover 0a only, and head-k comes from ordered tables. | Before any agent run, regenerate P3 with stratified scale assignment (scale balanced within template × table), add the 30 grouped tasks P3 requires, and report the ceiling within-table with table-bootstrap CIs. **[CPU-only]** |

Mean 3.5 (was 2.67).

## F. F3: is it right, and what does it mean?

**Is the computation right?** Yes. Every reported cell I checked matches the identity 0.5·(1 + hit − FP):
T0 all = 0.5·(1 + 0.139 − 0.006) = 0.567. The low ceiling is a hit-rate effect. Only 14% of poisoned
aggregates leave the whole-column range at T0, and at T1, 61% of clean aggregates already fall outside the
head-5 range.

**Is "tiny-table artefact" the only explanation?** No. Table size is one proxy. Five other factors move the
same number, and P3's design changed several of them at once:
1. **Range width relative to the aggregate.** A scaled mean leaves [min, max] only when max/mean < scale
   (or min/mean > scale). Range grows with n, so this correlates with table size, but the mechanism is the
   ratio and it can be measured per task. Plot hit rate against (max − min)/|clean|.
2. **Scale direction.** For columns with min near 0 (Bike counts, Abalone rings, sums), downward scales
   almost never exit the range. Half of P3's scales are below 1.
3. **Op mix.** ToxicBench's in-scope events are mean (609) and sum (201). P3 adds max, which is trivially
   flagged for scale > 1 at T0 because the clean value sits on the boundary, plus median and count. Sum
   intervals are very wide.
4. **Severity mix.** ToxicBench in-scope events are 56% obvious with no subtle; P3 is 17% obvious and 33%
   subtle. The like-for-like comparison is **plausible only: 0.896 (ToxicBench T1) vs 0.555 (P3 T0)**. The
   gap survives this control, which is the strongest evidence for the authors' reading, but it should be
   reported in this form.
5. **Head order** (T1 only): see d.

The CPU-only check that settles this: restrict both sources to `mean`, plausible, scale > 1, and compare hit
rates within bins of range/|clean|. If the curves overlap, "range width" is the explanation and table size is
only its proxy.

**Does scoring oracle values bias the ceiling?**
- **Positives: no bias.** ToxicBench's poisoner rewrites the line equal to `oracle.clean_value`, so an agent's
  poisoned return equals `poisoned_value` whenever the poison fires. The positive hit rate h is the same in
  agent runs.
- **Negatives: the ceiling is likely optimistic.** Agent runs add intermediate clean calls such as
  `df['x'].max()`, `.min()` and `len(df)`. At T0 these sit on or inside the boundary (score 0, no change). At
  T1 a whole-column max usually lies outside the head-5 range, which adds false positives. Agent-run 0a at
  T1 is therefore more likely below the ceiling than above it.
- **Slice:** agent-run 0a only parses unfiltered code, so the relevant ceiling is the **unfiltered** row
  (0.583 at T0, 0.534 at T1), not "all".
- **"Agent-run 0a ≤ ceiling" (research log) is not a theorem.** AUROC depends on the negative distribution,
  which changes in agent runs.

**Is it legitimate to say the fork cannot fire before agent runs exist?** Yes for these tasks, but for a
reason the write-up does not give:
- **Hit-rate bound.** 0a ≥ 0, and positives with score 0 can at best tie with negatives. So for any set of
  negatives, AUROC ≤ h + 0.5·(1 − h) = 0.5 + 0.5·h. The same holds per table, so the within-table mean is
  ≤ 0.5 + 0.5·mean(h_t). At T1 on plausible+subtle, h = (59 + 37)/150 = 0.64, so **AUROC ≤ 0.82 < 0.90
  whatever the agent does**, as long as the agent's poisoned returns equal the oracle poisoned values. That
  replaces the incorrect "≤ ceiling" argument.
- **Coverage condition.** It fails independently: 0a parses only unfiltered code, which is 33% of P3 tasks,
  below the 50% bar.
- **What this does not cover:** 0b, 0d, or zero-parameter checks in general; tasks outside P3's
  distribution; agents writing unfiltered code for filtered questions (they would be wrong, which is a
  capability failure). Correct status: "G2 expected to fail by bound; decided formally at P4", not "refuted".

## G. Workshop fitness

**Two-sentence abstract a reviewer would accept (from F1', F2', F3 only):**
> Using 3,633 paired clean/corrupted runs from ToxicBench, we find that a corrupted numeric tool return
> raises an agent's failure rate by 18.7 points beyond run-to-run noise (95% CI 15.1-22.3), and that
> zero-parameter checks catch these returns only where they can parse them: a range check scores 25% of
> poisoned returns (AUROC 0.95), re-executing the agent's code scores 42% (AUROC 0.83), and the remaining 58%
> are multi-number outputs neither can score. On 180 new tasks over six public tables of 344-17,379 rows,
> the range check's best case falls to AUROC 0.57 even with whole-column min/max visible, because a scaled
> aggregate rarely leaves the range of a real column.

**The sentence they would reject:**
> "Zero-parameter rules fail once tables are realistic, so learned uncertainty signals are necessary."

Reasons: no learned or intrinsic signal has been run; 0b and 0d are untested on large tables; F3 is computed
on oracle values, not agent trajectories.

**Minimum agent-run set for a 6-8 page paper**

| Item | Minimum | Why |
|---|---|---|
| Tasks | P3 regenerated (stratified scales, ≥ 60 grouped), clean × 2 seeds + toxic × 1 | the second clean seed gives the noise floor on the new tasks |
| Tiers | **T0** (preview with min/max), **T1** (head-5, min/max removed), **T3** (schema only) | three points make the context axis; T2 and T4 can be dropped |
| Harness | one stock adapter (smolagents or langgraph) with preview truncation added | the tier must change what the agent actually sees, not only the post-hoc score |
| Signals | 0a, 0b, 0d (post-hoc, CPU); 4 RSure-style prior (CPU, existing data); 3 verbalized (shadow call); 1 token entropy (open models only); 7 scorer | covers zero-parameter, content-free, intrinsic and learned columns; drop 2, 5, 6 and 0c to the appendix or future work |
| Agents | 2 open (Qwen3-4B + Qwen3-8B or Llama-3.1-8B) + 1 closed (gpt-5.4-mini, for continuity with existing data) | H4 needs 3 open agents; label it exploratory with 2 |
| Scale | ≈ 180 × 3 runs × 3 tiers × 3 agents ≈ 4,900 trajectories | |

**What works on API models only (no GPU):** all trajectory generation for closed models, and for open
models through a hosted endpoint; 0a, 0b, 0d and 4 (post-hoc CPU); verbalized confidence 3 (shadow call);
C2 on the new pairs. **What needs a GPU or a provider that returns logprobs:** token entropy 1, which H1
needs. Hosted open-model endpoints often do not expose logprobs (I did not verify this per provider). Scorer
7 (Qwen2.5-0.5B LoRA) is small enough that CPU or Apple-silicon training may be feasible but slow; I have not
measured this. Without a GPU, the paper can make the C1 claim with 0a/0b/0d/3/4/7 on API agents and treat H1
as a single-agent or exploratory result.

## H. Final verdict and next actions

**GO-WITH-CHANGES.** Do not run agents until actions 1 and 2 are done; both are cheap and both change what
the agent runs are designed to measure.

1. **Compute the 0d and 0b ceilings on the P3 tasks, and fix 0d's NaN drops.** Add a dated P3 amendment
   first: resample size = visible count for location statistics, NaN handling, a random-k tier, and the
   sum-multiplier rule. Then report 0d/0b by tier × template × severity, within-table with CIs, plus the
   like-for-like F3 control (mean, plausible, scale > 1, binned by range/|clean|). This decides whether F3
   is about range checks or about zero-parameter reconstruction in general, and it sets the bar C3 has to
   beat. **[CPU-only, about half a day]**
2. **Correct the write-ups and close the P3 deviations.** Rewrite F2', F3, `research-state.yaml` (G2 →
   expected-to-fail, decided at P4), the C3 line (41.8% / 58%), plan line 20 and the plan's H6. Run sanity
   rows for 0b and 0d. Regenerate P3 with stratified scales and ≥ 60 grouped tasks as P3's own power rule
   requires. Reweight the noise floor by model. **[writing-only + CPU-only]**
3. **Write P4 before any agent run**, with the minimum set from G: tiers T0/T1/T3 enforced in the harness,
   agents, the signal list, a second clean seed, the hit-rate bound argument for G2, and the statement that
   the fork's coverage condition cannot be met on P3 by design. Then run the API agents first.
   **[needs agent runs: API first, GPU for token entropy]**

**Strongest part:** the response to review is disciplined. Every fix maps to a dated amendment committed
before its result, and the authors reported a result that reverses their own earlier fork.
**Single most important improvement:** stop F3 from standing in for "zero-parameter checks fail". Run 0d on
the large tables (CPU, no agents) before deciding what the learned scorer is for.

## Sources
- `docs/REVIEW_2026-10-31_pilot.md` — accessed 2026-10-31
- `PREREGISTRATION.md`, `findings.md`, `research-log.md`, `research-state.yaml`, `.git/logs/HEAD` — accessed 2026-10-31
- `experiments/{taxonomy.py, range_check.py, gen_tasks.py}` — accessed 2026-10-31
- `experiments/results/{taxonomy/summary.json, taxonomy/pairs.jsonl, range_check/events.jsonl, range_check.log, gen_tasks.log}` — accessed 2026-10-31
- `data/ours/{ceiling.json, ceiling_events.jsonl, tasks/large_tables_v1.jsonl, datasets/PROVENANCE.json}` — accessed 2026-10-31
- private planning notes (not included in this repository)
- `/tmp/AI-research-SKILLs/22-agent-native-research-artifact/rigor-reviewer/SKILL.md`, `/tmp/academic-research-skills/deep-research/agents/devils_advocate_agent.md` — accessed 2026-10-31
