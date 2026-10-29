# Imported evidence evaluation and source review

This slice evaluates the actual imported-evidence search endpoint and prepares
independent review of its reference questions and the existing scientific
comparison. The application under test is frozen candidate **2026-10-29-c1**;
its runtime code is unchanged. The original corpus and labels are retained; a
separate source revision fixes one truncated excerpt without changing questions
or relevance targets. See [measured results and corrections](results.md).

Start with the [human review packet](review-final/review.md). It contains all 20
reference questions, all 23 canonical source excerpts, six comparison cells and
ten unique PDF supporting passages. [Review responses](review-final/responses.json)
contain **26 pending decisions, zero approvals and no invented held-out questions**.

## What is implemented

[research_imported_evidence.py](../../scripts/research_imported_evidence.py)
provides `freeze`, `run`, `review-packet`, `check-packet` and `review-status`.

- `freeze` binds 24 records to the ten-paper corpus: 23 exact excerpts plus its
  existing whitespace duplicate. It preserves attribution, JATS selectors,
  transformations, table structure, original source hashes and question revisions.
- `run` verifies cached XML/PDF bytes and installed candidate files before
  creating a new disposable project. It creates APW notes, previews/applies their
  selection through native RKS evidence import, and checks exact replay. It runs
  all 20 verbatim questions through `Workspace.search` and the real hosted search
  handler, retaining full responses, note-to-excerpt mappings and query timings.
- `review-packet` reads the existing pilot comparison through public interfaces.
  It retains exact interpretation, condition, source, evidence and review
  revisions; verifies all referenced PDF bytes; and refuses a changed snapshot.
  It writes no evidence or reviews into the original project.
- `check-packet` checks the retained packet against current comparison/support
  and source bytes. It returns exit 2 for changed content and fails explicitly
  for unavailable/inconsistent sources. It does not start a reader or infer approval.
- `review-status` validates every response against the sealed packet and exact
  target revision. Missing, duplicate, foreign and stale targets fail. Completed
  decisions require actual independent human provenance, timezone and notes.
  It never promotes scientific evidence or marks the release gate passed.

The new tests run automatically in the existing `test_research_*.py` CI suite.
They cover source integrity before writes, foreign/changed results, review
provenance and staleness, complete excerpt rendering, source support identity,
immutable evaluator capture and native-result cutoff semantics.

## Source representation and metrics

The corpus excerpts are derived from pinned **JATS XML**. They have not all been
matched to exact PDF pages. They therefore enter the imported-evidence contract
as **unlinked notes**, with the original text in `markdown` and an empty title.
Search reports their role as **commentary**, never as a verified PDF quotation.
Attribution/selector metadata remain in the fixture and packet, outside searchable
text. No answer, question wording or review judgment is added to the index.
The entire disposable project is identified as an evaluation fixture.

The benchmark calls `rks note search-evidence` through installed sci orchestration.
It does not import prepared claims or reuse the older claim-search scores.
The hosted checks call the real server handler; HTTP transport and browser
rendering are separate gates. All imported records remain unreviewed.

Rankings preserve the first ten native evidence records. **Top-five metrics use
the first five native result slots, then collapse canonical duplicates within
that window.** A duplicate cannot earn extra evidence credit or move a sixth
native result into the top five. `hit_at_5` reports its numerator and denominator;
`recall_at_5` reports coverage of the draft targets separately. The two
insufficient-evidence questions are retained but excluded from answerable-query
denominators. Precision, scientific accuracy and abstention accuracy are not
inferred from these incomplete draft labels.

The result is an engineering baseline against **agent-drafted references**.
The six public reserved questions are not blind holdouts. Independent review
and at least ten newly authored human questions remain required for S02. The
recorded query timings include CLI overhead and are not the 10,000-record/100-query
performance gate S03.

## Reproduce

Run from the Structured Intelligence checkout using the frozen candidate's
installed Python environment. On this Windows workspace its interpreter is
`../.development-candidate/2026-10-29-c1/installed/Scripts/python.exe`.
The commands below use `python` to denote that interpreter.

```text
python scripts/research_imported_evidence.py --corpus evaluations/imported-evidence-2026-10-29/corpus-source-complete freeze --output ../.imported-evidence/new-fixture.json
python scripts/research_imported_evidence.py --corpus evaluations/imported-evidence-2026-10-29/corpus-source-complete run --fixture evaluations/imported-evidence-2026-10-29/fixture-source-complete.json --cache .research-eval/sources --candidate-manifest ../.development-candidate/2026-10-29-c1/manifest.json --run-dir ../.imported-evidence/new-run
python scripts/research_imported_evidence.py --corpus evaluations/imported-evidence-2026-10-29/corpus-source-complete review-packet --fixture evaluations/imported-evidence-2026-10-29/fixture-source-complete.json --cache .research-eval/sources --candidate-manifest ../.development-candidate/2026-10-29-c1/manifest.json --workspace ../.living-project-pilot/single-cell-de --comparison-id cmp_0f45d3e27fa044729c08b9a906132f57 --output ../.imported-evidence/new-review
python scripts/research_imported_evidence.py check-packet evaluations/imported-evidence-2026-10-29/review-final/packet.json --candidate-manifest ../.development-candidate/2026-10-29-c1/manifest.json
python scripts/research_imported_evidence.py review-status evaluations/imported-evidence-2026-10-29/review-final/packet.json evaluations/imported-evidence-2026-10-29/review-final/responses.json
```

The fixture and corpus revisions must match. `run` and `review-packet` require
new output directories and never silently overwrite or repair a prior result.
They capture evaluator/helper source bytes at process startup into `harness/`
and record their SHA-256 values. Cached source acquisition remains the separate,
explicit `research_corpus.py fetch` command; evaluation itself is offline.
The evaluator imports the installed application directly and rejects editable,
outside-environment or mismatched module locations before creating a project.
For the original-source baseline, omit `--corpus` and use `fixture-v2.json`.

Local reader passage links require the original pilot project and reader at its
saved address. The packet also supplies original publisher PDF page links,
article links, hashes and attribution. Browser quote matching is not implied by
a valid backend source identity. The original project retains its absolute path;
the review JSON is a snapshot, not a portable project backup.

## Complete the review

Keep `packet.json` unchanged and copy `responses.json` for the actual reviewer.
For each question inspect the complete excerpt set, not only suggested relevance
targets. For each comparison cell inspect every selected PDF passage and record
whether its numbers, experimental unit, negation, conditions and applicability
support the interpretation. Use `approved`, `revise` or `exclude` with actual
reviewer, `method: human`, timezone-qualified `reviewed_at`, an explicit
`independent_of_implementation: true` assertion and substantive notes.

Changing scientific targets requires a new corpus/question/fixture revision and
fresh review. Do not edit the sealed packet or reinterpret a stale approval.
Run `check-packet` before reviewing and after completing the response. A response
can describe the frozen snapshot while the live project has since changed;
`review-status` alone does not check live freshness.

`held_out_questions` is deliberately empty. New independent questions must be
authored and frozen separately before retrieval evaluation. This slice reports
submitted questions but does not validate or score them, and cannot satisfy the
held-out release gate. It does not contact reviewers or record decisions on their
behalf.

## Retained revisions

- `fixture.json` and `review/` retain the first exploratory artifacts.
- [fixture-v2.json](fixture-v2.json) makes native-slot cutoffs explicit. The corpus,
  question text, labels and numeric acceptance threshold are unchanged. A
  regression test demonstrates why deduplicating before the cutoff is incorrect.
- [Source correction](corpus-source-complete/change.json) extends q02's source
  slice from 767 to 1,052 characters in the same pinned JATS paragraph. It adds
  the missing asymmetry/method comparison sentences. The question, target IDs,
  other passages and acceptance threshold are unchanged. Review is pending.
- `review-v2/`, `review-source-complete/` and `run/` retain earlier artifacts
  whose legacy helper selected checkout imports. They are superseded for
  installed-package qualification; their reported module hashes matched c1.
- [review-final](review-final/review.md), [original-source installed run](run-installed-original/results.json)
  and [corrected-source installed run](run-installed-corrected/results.json)
  verify actual installed module locations and hashes. The final packet renders
  all canonical excerpts once, retaining table boundaries and units as fenced TSV.
- Original native runs and full command diagnostics remain under the umbrella
  `.imported-evidence/`. The final measured result and disposition are in
  [results.md](results.md).

All quoted author text/tables retain their CC BY 4.0 attribution and license
links. Original PDFs and third-party images are not redistributed here.
