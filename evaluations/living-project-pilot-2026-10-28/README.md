# Real-paper pilot: replicated single-cell differential expression

Run on October 28, 2026. **The living-project state and history checks passed;
citation navigation has blockers.** Six of ten retained passage links opened at
their verified page/quote. Four failed text matching and cleared the reader to
an empty workspace. This run does not qualify milestones 1-4 for release.

**Follow-up:** the [remediation below](#remediation) fixes those engineering
blockers and records a separate rerun. The original observations and
`results.json` remain unchanged.

This was an agent-operated engineering pilot with three real historical papers,
not an independent researcher trial. All ten imported interpretations and all six
comparison entries remain unreviewed. Scientific accuracy and researcher-effort
improvement were not measured. The machine-readable receipt is
[results.json](results.json); the existing corpus/questions/reference labels were
not changed.

## Question and reading set

For replicated single-cell RNA-seq comparisons within a cell type, how do biological
replication and benchmark conditions affect the reported strengths and limitations
of pseudobulk and mixed-model differential expression?

| Paper | Source | Verified PDF pages |
| --- | --- | --- |
| Zimmerman, Espeland and Langefeld (2021), *A practical solution to pseudoreplication bias in single-cell studies* | [Article](https://doi.org/10.1038/s41467-021-21038-1), [PDF](https://www.nature.com/articles/s41467-021-21038-1.pdf) | 1, 3, 6 |
| Squair et al. (2021), *Confronting false discoveries in single-cell differential expression* | [Article](https://doi.org/10.1038/s41467-021-25960-2), [PDF](https://www.nature.com/articles/s41467-021-25960-2.pdf) | 1, 2, 8 |
| Crowell et al. (2020), *muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data* | [Article](https://doi.org/10.1038/s41467-020-19894-4), [PDF](https://www.nature.com/articles/s41467-020-19894-4.pdf) | 3, 4 |

PDF byte counts and SHA-256 identities match the pinned single-cell corpus. Text
was extracted from those actual PDFs with pypdf; complete relevant pages were
rendered and visually inspected. Quotes retain PDF text-extraction artifacts,
with Unicode compatibility normalization and collapsed whitespace. Full author
attribution, source fingerprints and article-specific license evidence are retained
in the receipt. Selected article text is under its authors' [CC BY 4.0
license](https://creativecommons.org/licenses/by/4.0/); it is not relicensed under
the repository's software license. No third-party figures or PDFs are bundled here.

## What the workflow demonstrated

1. Saved live PubMed discovery and three Crossref DOI lookups. Explicitly selected
   the three matching, verified local PDFs from the existing licensed cache. This
   did not test a fresh PDF download or establish completeness of the reading set.
2. Read the sources, saved nine initial annotations, inspected their import
   previews, and imported exactly those selections through the installed CLI.
3. Created a three-paper, two-criterion comparison: **Experimental unit and
   benchmark** and **Method finding and limits**. Each entry is explicitly
   agent-origin and linked to selected imported evidence.
4. Retained the first brief with nine unreviewed items. Its initial freshness check
   reported `current`, zero changes, and six comparison entries needing review.
5. Added Zimmerman's page-6 qualification about imbalance and relative within-/
   between-individual variability. Updated the corresponding comparison entry
   from its initial abstract-level interpretation. This was an explicit staged
   refinement, not an actual human review or an invented scientific reversal.
6. Saved a change report: the old brief became `outdated`, with one evidence
   addition and one changed comparison. Its Markdown and canonical record remained
   byte-for-byte unchanged.
7. Generated a second brief with ten unreviewed items. Retrying that request
   returned the same edition without creating a third. The original edition's
   exact text and supporting snapshot remained readable. No pending brief remained.
8. Repeated the saved Zimmerman DOI lookup. Its single candidate was unchanged;
   the project still contained three papers. The final freshness check reported
   `current` and zero changes, while all six comparisons still needed review.

The comparison preserves different reference standards. Zimmerman uses a
simulation-based variance/power analysis; Squair's main comparison uses matched
bulk/single-cell concordance and separately examines GLMM settings; Crowell
evaluates several types of differential-state changes with multi-sample
simulations. The proposed interpretations do not collapse these into a universal
method ranking. They require independent domain review against the cited pages.

## Citation checks and root-cause evidence

All ten records passed the backend's PDF identity and annotation-revision checks.
That contract explicitly leaves page-text matching to the browser. Browser
verification produced the following distinct result:

| Evidence | Paper/page | Browser result |
| --- | --- | --- |
| n_000001, n_000002, n_000003 | Zimmerman 1, 3, 1 | Passed |
| n_000004 | Squair 2 | Failed: spacing around quoted text |
| n_000005 | Squair 1 | Passed |
| n_000006 | Squair 8 | Failed: split ligature/word spacing |
| n_000007 | Crowell 4 | Passed |
| n_000008 | Crowell 3 | Failed: mathematical text and spacing |
| n_000009 | Crowell 3 | Passed |
| n_000010 | Zimmerman 6 | Failed: split ligature/word spacing |

The observed passages are present on the retained source pages. APW's
`frontend/src/pdf/pdf-layer.ts:readTextFromPdfItems` inserts a space between every
PDF.js text item. The text-layer offset loop in `usePdfReader.ts` also advances by
one extra character per item. The anchor resolver collapses whitespace but does
not reconcile these boundaries with independently extracted quotes. For example,
the Squair PDF quote contains `‘pseudobulks’`, while the reader constructs
`‘ pseudobulks ’`. Ligatures and formula fragments also differ between extractors.
This is a text-representation contract mismatch, not evidence that the quotation
is absent from the PDF.

The second defect is separate: `usePaperSession.ts:attachToSession` catches the
failure of `focusPassage` together with document/session loading failures, calls
`resetToEmptyViewer()`, and removes the session from the URL. A quote mismatch
therefore discards a successfully loaded paper instead of retaining it with a
specific citation error.

These failures are preserved in the pilot. Neither quotes nor matching thresholds
were changed to make the recorded run pass. `current` freshness means the captured
project inputs match; it does not mean every link opened successfully or that the
scientific interpretation is valid.

## Other observations

The broad PubMed query, `single cell differential expression biological
replicates`, returned 917 hits and five initially displayed candidates outside the
three selected methods papers. Its recorded automatic translation expanded terms
such as `single person`, `cell differentiation`, and `DNA replication`. A second,
explicit title/abstract query returned 244 hits, but its first five also did not
contain this curated reading set. Both original responses were retained; DOI
lookups supplied the selected works. This is a query-design/provider-ranking
observation, not a measured relevance or recall score.

Freshness checks took **17.843-18.763 seconds**; the two brief publications took
**17.383 and 18.445 seconds**. Exact brief replay took **0.576 seconds**, and original
edition retrieval took **0.319 seconds**. These are individual Windows wall-clock
observations, including process startup, not controlled performance benchmarks.
The implementation performs serial public-tool calls and repeated source checks;
profiling should establish their individual costs before changing that design.

## Recommended next slice

Fix citation reliability before roadmap #5:

1. Establish a shared text/anchor representation for source reading and citation
   verification. Preserve a map to the rendered PDF and compatibility with retained
   anchors. Keep punctuation, numerical signs, units and ambiguity checks; do not
   weaken matching to hide the four failures.
2. Separate passage-validation errors from session/document-loading errors so the
   exact retained paper remains visible when its quote cannot be resolved.
3. Rerun these ten fixed cases and negative/ambiguous-anchor tests. Then profile
   change checks and reduce repeated work while preserving both consistency
   observations and the public evidence-ownership boundaries.

After those fixes, have a domain reviewer inspect the six comparison entries and
record their actual decisions. Actual researcher usability observations, release
validation, opt-in recurrence, and analysis handoff remain separate acceptance work.

## Local continuation and provenance

The pilot installation and workspace are separate from the earlier demo:

```powershell
& C:/Users/yangm11/github/.living-project-pilot/venv/Scripts/sci.exe resume `
  --workspace C:/Users/yangm11/github/.living-project-pilot/single-cell-de
```

The workspace holds original PDFs, RKS evidence, APW sessions, selections,
comparison versions, saved searches, two brief editions and the change report.
The adjacent `receipts/`, `operations.jsonl`, `source-checks/`,
`browser-passages.json`, `review-packet.json`, and screenshots preserve local
verification details. The review packet has six pending entries and no approvals.
Stop its owned reader before backing up the complete workspace; preserve its
absolute location for the current implementation.

Installed from SI `0b957a1305cfb9f9d2197814a74452e0d5497183`, with APW
`2806a6c182a0ae442b39e68015a9bf76d31a3af5` and RKS
`44a8f33f47d9e867a03a8cff9e07a7b021e04cea`. The installed distributions'
`direct_url.json` records verified the two dependency pins. The package version
still reads 0.3.1; these development features are newer than that release tag.

## Remediation

The follow-up uses APW `3ea2a5290f25dbc86a7ea178d0c0ed92849b2ba0` and the
same RKS revision, PDFs, annotations, citation URLs and two retained brief
editions. Its separate machine-readable receipt is [remediation.json](remediation.json).

- **Citation fidelity:** all ten original links now open at the expected page
  with visible highlight geometry. PDF fragment boundaries are distinguished
  from real word spaces, with a map back to the existing text-layer offsets.
  Only typographic ligatures and permitted spacing are reconciled; numerical
  signs, units, punctuation, superscripts and ambiguity checks remain intact.
- **Reader recovery:** absent and ambiguous quotes were also tested in a
  separate synthetic project. Both produce a specific error and no selected
  highlight while retaining the loaded PDF, citation URL and usable workspace.
- **Freshness cost:** profiling found 72 subprocess launches in one inspection,
  accounting for 16.96 of 17.45 seconds. Inspection now calls the same native
  read-only RKS/APW operations within the installed process. Each observation
  opens a fresh RKS read transaction and has its own passage-check cache; both
  independent observations and all source/revision checks remain. The rerun
  receipt records **0.85-0.88 seconds** across three checks and zero subprocess
  launches. These are local
  observations, not a controlled benchmark or a claim about larger projects.
- **Discovery transparency:** the reader displays the saved provider query
  translation, total count and warnings. PubMed guidance explains how to inspect
  expansion and narrow a query. The original provider responses and ordering
  are retained; this does not establish improved retrieval relevance.

Validation includes 95 frontend tests, TypeScript, lint, formatting and the
production asset build; 13 maintenance integration tests (including missing
databases, foreign scope and edits between observations); 19 installed workflow
tests, including comparison recovery; and six standalone brief tests. A fresh
installation resolved both exact public dependency revisions, and its reader
passed all ten unchanged browser citations. The original brief hashes and latest
edition's complete snapshot still match, with two editions, ten unreviewed
evidence items and six unreviewed comparison entries. No scientific review was
recorded.

The active pilot reader now uses the fresh installation at
`.living-project-pilot/verified-venv`. The earlier pilot environment remains at
`.living-project-pilot/venv`, and the original run receipts are retained.
Resume this checked installation with:

```powershell
& C:/Users/yangm11/github/.living-project-pilot/verified-venv/Scripts/sci.exe resume `
  --workspace C:/Users/yangm11/github/.living-project-pilot/single-cell-de
```

The next acceptance work is independent domain review and researcher usability
evaluation. These fixes resolve the observed engineering blockers without
claiming scientific accuracy, retrieval quality or completion of milestones 1-4.
