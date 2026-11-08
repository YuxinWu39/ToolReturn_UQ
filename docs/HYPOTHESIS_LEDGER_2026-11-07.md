# Hypothesis and protocol version ledger — 2026-11-07

This ledger preserves protocol differences; it does not retrospectively create a unique confirmatory rule. All newly computed cached metrics are retrospective diagnostics (A-REVISION-CACHED, commit 27ab078).

| Item / version | Population, statistic and rule | Current status |
|---|---|---|
| H1 A-P4 | Open agents, T1, subtle; AUROC<0.60 and AUPRC<2×base; first-token entropy + negated confidence. General metrics paragraph instead calls P+S primary. | Conflicting slice definitions; original first-token statistic formatting-degenerate. No unqualified confirmation. |
| H1 A-P4b / 4B | Mean-token entropy replaces first-token after inspecting 4B; P+S upper table-CI<0.60; AUPRC omitted. | Mean entropy exploratory; cannot relabel as unchanged A-P4. |
| H1 A-P4b / 8B | Same mean-token/P+S rule, documented as before later-agent runs. | Documented prospective intention; original history timestamps not independently verified here. No live sanity, efficacy/confirmation withheld. |
| H1 cache audit | Both subtle and P+S, same-task finite pairs per signal; equal-table AUROC/CI and AP, all tiers labelled. | Diagnostics only; no live sanity for intrinsic signals. T0 is not a primary T1 H1 test. |
| H2 A-P4 | Separate 0d/7 contrasts to content-free prior 4 by tier. | Not evaluated as registered: prior 4 is not implemented. P5 is not this test. |
| H3 | Transfer to held-out sign_flip/label_swap vs BCE. | Not run; no transfer claim. |
| H4 | Cross-agent ranking Kendall tau>0.7. | Not established; incomplete signals and efficacy gates prevent a complete ranking claim. |
| H5 A-P4-Gemini | Closed-agent subtle/T1 confidence, scalar pairs; upper CI<0.60. | Not confirmed: 7/73 tasks, 3 tables, 0.556 [0.500,0.667]; sanity not collected. |
| H6 amended | Consumed-observation vs capability failure, effect sizes by signal; exploratory if class<50. | Exploratory, not a confirmed mechanism; historical small-class restriction retained. |
| G1 initial | Observation-failure share≥15%. | Retired by A-P1. |
| G1 A-P1 | Noise-corrected excess toxic-failure lower CI>0, overall and numerical. | Supported under recorded taxonomy: excess 18.7pp overall, 22.4pp numerical; does not identify human intent. |
| G2 A-P4 | T1 P+S equal-table 0a lower CI>0.90 AND coverage≥50%. | Rules-suffice fork not established; old expected-to-fail-by-bound status retired. No general information bound follows. |
| P5 | Validated LOTO scalar scorer; sanity>0.95 high AND low; coverage [0.80,0.98]; then common-support AUC7−max(AUC0d,AUC0r)>0 lower paired CI. | All six cached scorer configurations fail gates. Common support counted; real gain withheld, general learned-UQ failure unsupported. Multi-number observations not covered. |

The original AP integration convention/aggregation was underspecified. This audit explicitly uses average precision; paired base rate is 0.5, making AP<2×base a weak criterion. Four-B confidence on P+S has paired upper CI 0.606, illustrating why a single global H1 confirmation is inappropriate even as a diagnostic reading.

Input SHA-256, per-severity/template results, eligible and paired counts, constant tables, sanity and coverage denominators are in [the cached audit](../data/ours/revision_cached/20261107/summary.json). Missing support is not a neutral detector result. Historical paragraphs remain as provenance; this ledger governs current interpretations.
