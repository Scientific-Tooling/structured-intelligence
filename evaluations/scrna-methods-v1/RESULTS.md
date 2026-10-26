# Initial source-passage retrieval and workflow results

Measured October 26, 2026 against corpus revision
`1914a020d82932ebb8b38deb4fec326ea44aa825237d55a4ccfdc35d4a394112`.
See `baseline-results.json` for the exact question/source revisions, per-question
rankings, implementation fingerprints, and timing provenance.

## What was measured

Ten original scientific PDFs and their JATS sources were acquired from the
publishers/Europe PMC and verified against pinned byte counts and SHA-256 values.
All 23 selected text/table passages matched their source selectors/transforms;
the title, author, DOI, license evidence, and source links were also checked.

Twenty questions were frozen before the baseline: 14 development and six public
reserved questions, grouped by source paper. Eighteen have draft relevant excerpts;
two are insufficient-context probes. Each complete question was passed verbatim
to native RKS search. The native workspace contained 24 prepared passage records,
including one deliberately duplicated representation. No live claim extraction,
answer-generation model, semantic-provider migration, or scientific review was run.

## Retrieval observations

These scores measure agreement with **agent-drafted relevance labels**. They are
not scientific answer accuracy, proof of entailment, or a release qualification.

| Exposed retrieval method | Relevant target first | Any relevant target in top five | Mean target recall at five | MRR at ten |
| --- | --- | --- | --- | --- |
| Fixed BM25 passage baseline | 17/18 | 17/18 | 0.9074 | 0.9506 |
| RKS lexical interface | 0/18 | 0/18 | 0.0000 | 0.0000 |
| RKS `local-hash-v1` | 5/18 | 9/18 | 0.4352 | 0.3858 |

The BM25 top-five hits were 12/13 on development and 5/5 on the reserved split;
native hash retrieval produced 6/13 and 3/5 respectively. The reserved questions
are public and were authored during corpus construction, so these are not blind
generalization estimates. No method or threshold was tuned after seeing scores.
The two unanswerable probes were excluded from retrieval denominators; abstention
accuracy and scientific answer accuracy remain unavailable (`null`).

The native lexical result has a specific code-level explanation: RKS's current
claim search uses `LIKE '%<complete query>%'`. The full natural-language questions
are not substrings of the passages. This is an interface/query-interpretation
limitation, not a finding that the source material contains no relevant evidence.

The 64-dimensional hash interface also returned weak rankings. For example, q01
(library protocols/pipeline counts) ranked the Zimmerman type-I-error caption
first, and q02 (normalization under asymmetry) ranked the Lun assumption excerpt
first. BM25 also failed q02 at five: its first result was the Lause caveat excerpt.
Failures remain in the checked-in results. They are not hidden by excluding
questions, changing thresholds, or choosing a new relevance list after scoring.

BM25 ranks passages directly. Native RKS semantic results share a global top-ten
cap with papers/concepts; the harness preserves this cap and does not backfill.
The scores therefore compare exposed behavior, not isolated rankers with identical
candidate selection. Duplicate source representations are collapsed before scoring.

## Original-PDF workflow checks

Three original-paper cases completed the full existing workflow: RKS source
identification, APW reading, explicit unreviewed annotation, selected export,
dry-run/native transactional import, replay, and a source-linked brief. Chromium
opened the actual generated links and selected the intended page/quote in all
three original PDFs. Their screenshots were visually inspected. The Lause
runtime table was separately checked on original PDF page 10, preserving seconds,
hours, column/row context, and the machine description.

The complete three-case journey was repeated into a new artifact directory. All
three first imports on that second journey were unchanged, and each same-bundle
replay was also unchanged. Existing APW annotation timestamps were preserved.
No reviewer identity or scientific approval was generated. See
`journey-validation.json` for the portable checks and original PDF fingerprints.

## What remains unresolved

All 20 reference questions still need independent domain review. The corpus is
a purposively chosen historical starter set, and its relevance lists may omit
valid alternatives or require correction. A generated brief is an inventory of
recorded evidence, not a validated scientific synthesis. No researcher-effort
improvement, clinical inference, or scientific release quality was established.

The next engineering target is explicit, ranked term retrieval for natural-language
questions in RKS. Address query interpretation in the shared search layer and
retain an explicit phrase-search option, instead of silently switching methods
only after empty results. Compare any implementation under a new method identity
against these retained baselines, then validate on independently reviewed and
newly held-out questions. A new embedding provider should be considered only with
measured benefits and its own model/index/reindex provenance.

The reviewer packet, representative-corpus expansion, an independent question set,
and a real researcher pilot remain the scientific acceptance path. Full Linux
backend suites, installed-wheel smoke checks, and hosted cross-repository CI are
separate reproducibility work; this checkpoint ran the research suite on Windows
and Ubuntu and verified the three original-paper journeys locally.
