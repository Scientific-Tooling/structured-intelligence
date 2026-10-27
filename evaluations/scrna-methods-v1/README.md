# Single-cell RNA-seq methods: candidate evaluation corpus

This is a ten-paper starter corpus for the source-reading workflow and retrieval
evaluation. It contains 23 attributed text/table excerpts, one deliberately
duplicated whitespace representation, and 20 bounded questions. All ten papers
have article-specific CC BY 4.0 license evidence and pinned original PDF/JATS
fingerprints. Article text is historical (2016-2022), not a current best-practice
recommendation or a representative sample of all single-cell research.

**Reference status: agent-drafted and pending independent domain review.** Source
identity, quotations, and license records were checked against retrieved sources.
The question answers and relevance labels are candidate annotations, not an
expert gold standard. The review template contains zero approvals.

## Files and attribution

- `corpus.json`: titles, full author attribution from JATS metadata, DOI/PMCID,
  article/publisher links, per-article license evidence, exact source fingerprints,
  excerpt transforms/slices, table cells, and the derived duplicate.
- `questions.json`: 14 development and six reserved questions, frozen against the
  corpus revision before the baseline run. Eighteen are answerable from the
  selected excerpts; two require acknowledging insufficient supplied evidence.
- `review-template.json`: revision-bound pending review records. Reviewer names,
  times, human-review method, and decisions must be entered only after review.
- `journey.json`: three unreviewed reading notes and separately verified page/quote
  anchors for original PDFs, rather than assumed pagination of JATS excerpts.
- `baseline-results.json`: measured retrieval results with per-question rankings,
  split aggregates, native-interface limits, runtime provenance, and code hashes.
- `ranked-term-results.json`: separate rerun after the RKS ranked-term fix, retaining
  the original baseline and unchanged source/question revisions.
- `journey-validation.json`: portable receipt of original-PDF source/brief/browser
  checks. Local handoffs, briefs, databases, cached PDFs, screenshots, and complete
  native responses remain under the ignored `.research-eval/` directory.

| Source ID | Paper | DOI |
| --- | --- | --- |
| vieth2019 | A systematic evaluation of single cell RNA-seq analysis pipelines | [10.1038/s41467-019-12266-7](https://doi.org/10.1038/s41467-019-12266-7) |
| hafemeister2019 | Normalization and variance stabilization of single-cell RNA-seq data using regularized negative binomial regression | [10.1186/s13059-019-1874-1](https://doi.org/10.1186/s13059-019-1874-1) |
| townes2019 | Feature selection and dimension reduction for single-cell RNA-Seq based on a multinomial model | [10.1186/s13059-019-1861-6](https://doi.org/10.1186/s13059-019-1861-6) |
| lause2021 | Analytic Pearson residuals for normalization of single-cell RNA-seq UMI data | [10.1186/s13059-021-02451-7](https://doi.org/10.1186/s13059-021-02451-7) |
| squair2021 | Confronting false discoveries in single-cell differential expression | [10.1038/s41467-021-25960-2](https://doi.org/10.1038/s41467-021-25960-2) |
| zimmerman2021 | A practical solution to pseudoreplication bias in single-cell studies | [10.1038/s41467-021-21038-1](https://doi.org/10.1038/s41467-021-21038-1) |
| crowell2020 | muscat detects subpopulation-specific state transitions from multi-sample multi-condition single-cell transcriptomics data | [10.1038/s41467-020-19894-4](https://doi.org/10.1038/s41467-020-19894-4) |
| luecken2022 | Benchmarking atlas-level data integration in single-cell genomics | [10.1038/s41592-021-01336-8](https://doi.org/10.1038/s41592-021-01336-8) |
| lun2016 | Pooling across cells to normalize single-cell RNA sequencing data with many zero counts | [10.1186/s13059-016-0947-7](https://doi.org/10.1186/s13059-016-0947-7) |
| zappia2017 | Splatter: simulation of single-cell RNA sequencing data | [10.1186/s13059-017-1305-0](https://doi.org/10.1186/s13059-017-1305-0) |

Source excerpts remain under their authors' [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
licenses. They are not relicensed by this repository's code license. Attribution
and the source/DOI/license links must travel with redistributed excerpts. Changes
are explicit: selected slices, whitespace normalization, simple tables serialized
as TSV, and one whitespace-only duplicate. No third-party images are redistributed.
Original PDFs are fetched into a local cache, not bundled in Git.

## Reproduce

Run from the Structured Intelligence checkout. The validator, BM25 baseline, and
review commands need only Python 3.12+ (3.14 recommended). The native benchmark also needs the RKS
CLI; the original-PDF journey needs RKS/APW environments and a local APW viewer.

```bash
python scripts/research_corpus.py validate
python scripts/research_corpus.py fetch --cache .research-eval/sources --include-pdf
python scripts/research_corpus.py verify-sources --cache .research-eval/sources --include-pdf
python scripts/research_rks_benchmark.py --cache .research-eval/sources --run-dir .research-eval/new-baseline --rks-python /path/to/rks/python
python scripts/research_corpus.py evaluate --rankings .research-eval/new-baseline/native-rankings.json --output .research-eval/new-baseline/results.json
```

Fetch is the only command here that accesses the network. It checks pinned bytes
before publishing cache files. Existing corrupt files and changed remote sources
fail explicitly; preserve them and review a new corpus revision. Validation and
evaluation never download, repair, overwrite, or delete an existing workspace.
Use a new run directory for each native evaluation. The native runner verifies
all source bytes before creating its disposable RKS workspace. It explicitly
imports prepared excerpts as `extracted` records with `evaluation_only` provenance,
not as reviewed graph facts. No live extraction, paid model, or API evaluation is
performed. Native responses and claim-to-excerpt maps remain inspectable.

For the original retained baseline, RKS was at `b5aac77` and APW at `7715497`. The
current native runner requires versioned ranked-term/phrase metadata and records
`rks-bm25-terms-v1`, `rks-literal-phrase-v1` and `rks-local-hash-v1` separately.
Use RKS with that search contract for new runs; the old `rks-lexical-v1` scores
remain in `baseline-results.json` and are never relabeled as the new method.
Separate virtual environments are supported via explicit Python paths. On Windows, paths
end in `Scripts/python.exe`; on Linux, usually `bin/python`. CPU timings include
CLI startup and normal command overhead; they are not isolated search-kernel timings.

## Metric definitions and limits

`hit_at_1`/`hit_at_5` mean at least one draft-relevant canonical passage appears
within the first one/five results. `recall_at_5` is the fraction of the question's
distinct draft relevance targets present in the first five results. `mrr_at_10`
uses the first matching canonical passage within ten. The duplicate representation
is collapsed before scoring and never earns extra evidence credit. A hit does
not establish a complete answer. No precision claim is made from incomplete
candidate relevance labels.

Two unanswerable probes are retained in recorded rankings but excluded from
retrieval denominators. Retrieval ranks alone cannot assess abstention accuracy.
Scientific answer accuracy and abstention accuracy are `null`, not zero or a
lexical similarity proxy. Tables retain headers, row/cell boundaries, units, and
footnotes; a runtime in seconds cannot be interchanged with the hours column.

The fixed passage BM25 baseline uses `k1=1.2`, `b=0.75`, ASCII alphanumeric tokens,
case-folding, no stemming, and no stop-word removal. RKS receives each full
question verbatim. The original lexical interface performed substring matching;
the updated interface ranks Unicode-normalized complete query terms with BM25,
and explicit phrase mode matches literal substrings. Its `local-hash-v1`
interface uses 64 dimensions and a global top-ten cap shared
by paper, claim, and concept results. The benchmark preserves those exposed
interfaces, does not backfill after non-passage/duplicate hits, and reports that
comparison limit. It does not claim an isolated identical-candidate ranker contest.

The reserved split groups source papers apart from development questions. Its
questions and sources are public and were authored during corpus construction.
It is **not a sealed, blind, or independently authored test set**. No retrieval
thresholds or methods were tuned to these questions. The observed scores are an
exploratory baseline; obtain independently reviewed and newly held-out questions
before using scores to justify a scientific release or choosing a new model.

## Original-PDF reading journey

Start APW with a disposable database and persistent snapshot directory:

```bash
apw-viewer-server --db-path /path/to/evaluation/events.db --pdf-root /path/to/evaluation/pdfs --port 8794
python scripts/research_corpus_journey.py --cache .research-eval/sources --benchmark-run .research-eval/new-baseline --output-dir .research-eval/new-journey --apw-db /path/to/evaluation/events.db --pdf-cache /path/to/evaluation/pdfs --rks-python /path/to/rks/python --apw-python /path/to/apw/python
node scripts/verify_research_passages.mjs .research-eval/new-journey/journey-results.json /path/to/apw-checkout .research-eval/new-journey/browser
```

The browser verifier loads Playwright from that APW checkout, which needs its
locked Node dependencies and matching Chromium installed. The journey checks that
the viewer serves the selected session/snapshot before writing annotations. It
creates only explicitly unreviewed notes, previews/applies the native imports,
replays them, generates briefs, and verifies actual citation links. Reusing an
unchanged annotation preserves its timestamps; edited corpus annotations fail
instead of overwriting a reading decision. Each artifact output directory must
be new. Reading sessions/databases/snapshots remain under caller control.

JATS text and publisher PDF text are distinct pinned encodings of each article.
Do not infer PDF pagination or identical text from JATS selectors. The three
journey anchors were checked in the original PDFs and through the actual viewer.

## Independent review procedure

```bash
python scripts/research_corpus.py review-packet --output .research-eval/reviewer-copy.json
python scripts/research_corpus.py review-status .research-eval/reviewer-copy.json
```

For every question, a qualified reviewer should inspect the original source and
selected excerpts, then check answerability, all relevant passages, numerical
values/units, negation, experimental unit, benchmark conditions, and required
qualifications. Pay particular attention to the different evaluation designs in
the Zimmerman/Squair comparison and the limits of an incomplete abstract.
Use `revise`/`exclude` for unsuitable cases; changes require an explicit corpus or
question revision and fresh review. The packet records `method: human`, actual
reviewer, timestamp with timezone, decision, and substantive notes. These are
caller assertions, not authenticated identities. Never fill approvals on behalf
of a reviewer or reuse an approval after the source/question revision changes.

Following that review, collect independently authored evaluation questions and
researcher pilot observations. Do not report a qualified review, measured
scientific answer accuracy, or researcher-effort improvement from these engineering
checks. The retrieval failures identify a next engineering target; they do not
establish that any normalization or DE method is scientifically superior.
