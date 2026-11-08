# Submission build and revision checks — 2026-11-08

## Result

`output/pdf/submission.pdf` is the anonymous AAAI 2027 layout export of manuscript revision 4. It has **5 pages total**. The body conclusion is on page 3, and its final core table (Table 3) is at the top of page 4; references and appendices occupy the remainder of pages 4–5. All main content is within the first four pages. References and appendices are treated as outside the workshop body limit; the workshop's current wording is “usually” excluded, so verify the final submission-form interpretation.

## Scientific changes explicitly authorized by the author

The author accepted the preceding review and its proposed corrections. These are evidence-scope repairs, not merely grammar edits:

- Replaced “follows the flag exactly” with 120/120 flagged rejections, 146/150 unflagged acceptances and four uncertain decisions.
- Replaced “adds no detection” with the observed discrimination comparison and the explicit absence of an equivalence conclusion.
- Removed the claim that a model cannot remove false-positive harm. Gemini accepts all three falsely flagged clean values and fourteen flagged corrupted values. Qwen retains all three false rejections and adds three clean abstentions.
- Kept Qwen's failed registered joint rule, Gemini's different P4 output-unit mix, the observation-only preview comparison and the diagnostic-only code arm visible. Deployment cost/recovery and optimal runtime placement remain untested.
- Synchronized the abstract, contribution list, discussion, conclusion and README. Existing results and generated evidence blocks are preserved.

## Build

From the repository root, with a working TeX Live/TinyTeX installation:

```bash
python experiments/export_paper_evidence.py --check
python paper/build_submission.py --check
python paper/build_submission.py --compile
```

If pdfLaTeX/BibTeX are outside PATH, add `--tex-bin /path/to/tex/bin`. This session used a portable TinyTeX distribution under `/private/tmp/toolreturn-paper-build/tex/TinyTeX/bin/universal-darwin`; it is a temporary build dependency, not part of the artifact. **pdfTeX is required by the official 2027 style. Tectonic/XeTeX cannot compile this style.** Standard dependencies include newtxtext, helvet, courier, placeins, natbib, caption, url, graphicx, booktabs and array.

`build_submission.py` deterministically exports the LaTeX source from manuscript.md, compiles in a temporary directory, runs BibTeX, resolves citations in repeated passes and refuses to deliver a PDF with overflow, missing glyphs or undefined citations. It makes no model calls or numerical estimates. The compilation log is temporary and is not bundled into the anonymous PDF deliverable.

The PDF uses the exact official `aaai2027.sty` and `aaai2027.bst`, unmodified, obtained from [AAAI-27 Author Kit](https://aaai.org/authorkit27/) via the [official submission instructions](https://aaai.org/conference/aaai/aaai-27/submission-instructions/). The workshop points to these instructions. Template provenance and final artifact hashes are in `submission_checks.json`.

The Markdown contains eleven generated table blocks. The PDF combines monitor/flag-only into one two-panel Table 3, yielding ten numbered tables. The k-sweep is transposed for a single column. Appendix tables use shorter headers or split panels while retaining their values; repeated uniform eligibility/missingness values appear in captions. The PDF omits the two exploratory flag-only-minus-raw effect estimates from the wide Markdown row, labels it “policy reference,” and preserves the policy's acceptance counts, the primary intervention effects and the check-minus-flag contrasts. The complete estimates remain in manuscript.md and evidence.json.

## Checks completed

- Evidence export: **PASS**, 28 evidence entries, 16 hashed input files, eleven Markdown table blocks.
- Source drift check: **PASS**, submission.tex matches the Markdown and formatting rules.
- Official style and bibliography style byte comparison: **PASS**; no font-size, spacing or margin override is used. Tables are 9pt, captions and body use the official style.
- Compilation: **PASS**, no overfull boxes, missing characters or unresolved citations. ArXiv entries use the bibliography style's native eprint output; duplicate IDs and empty-journal warnings were repaired.
- PDF: US Letter, five pages; all used fonts are embedded Type 1. Author/title metadata is empty, the official anonymous-submission heading is used, and no local paths or account/repository identifiers were found in extracted text or metadata. No embedded files or URI annotations were found.
- Visual QA: the root reviewer rendered and inspected **all five final pages**, including every main and appendix table. No clipping, overlap, missing symbols or blank-page defect was observed. Some legal LaTeX float placement puts appendix tables above their section text; captions identify their content.
- A separate milestone execution context (`updated_paper_rigor`) rechecked the three substantive claim repairs, generated TeX and PDF text and ran both checks. It found no new substantive numerical issue. This is not a completed five-seat review, a contract-governed re-review, or evidence of independent reviewer errors.

## Before uploading

The PDF itself is anonymized, but **an externally accessible anonymous reproduction artifact has not been created or uploaded**. The data-availability wording is prospective and contains no fabricated link. Do not substitute the identifying public repository URL in a double-blind submission. Prepare the anonymous material and verify the exact PDF that is uploaded; author identity, authorship order and declarations must be supplied through the venue's author-facing form as appropriate. The current PDF is a reviewable submission draft, not proof of workshop acceptance or an executed submission.

No new model experiment is needed for the bounded claims in this version. A generic-caution control, uniform code-access study or measured recovery policy would be a separate claim expansion requiring a new protocol.
