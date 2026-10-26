# Generate a brief with supporting passage links

After [importing selected evidence](evidence-import.md), generate a reading brief
from durable RKS records. The brief retains imported interpretations and their
review status, quotes the recorded source passages, and links to the exact APW
page and annotation revision.

```bash
python scripts/research_brief.py p_000001 --question "What does this source support about the bounded question?" --workspace-id review-a --rks-data-dir /path/to/rks-data --source-id reader-a --apw-db /path/to/events.db --output reading-brief.md
```

Pass `--rks-python` and `--apw-python` for separate Python environments. Optional
`--rks-note-id n_000001` flags select particular imported RKS notes. Without them,
the brief includes this paper's imported evidence from the named APW source
workspace. The workspace IDs must match the import. The output path must be new.

The generator calls only RKS/APW CLIs. It reads the current imported records,
checks each live APW passage revision, and verifies the retained PDF bytes. It
never imports, reviews, or promotes evidence. Merged RKS paper IDs resolve to
their canonical paper while citations retain their original APW source identity.

Each section includes the imported note ID, interpretation, source quote/page,
evidence revision, and PDF hash. Unreviewed material is labelled explicitly.
Recorded human reviews include the asserted reviewer, actual recorded time, and
statement of what was checked. No scientific synthesis or inferred claims are
introduced. Imported Markdown/HTML is escaped so it cannot replace the generated
source citation links.

## Open the supporting passage

Start a compatible APW viewer with the same database and persistent PDF cache:

```bash
apw-viewer-server --db-path /path/to/events.db --pdf-root /path/to/pdfs
```

The default link base is `http://127.0.0.1:8790`; pass `--viewer-url` when using
another address. The generator verifies local data, not server availability or
whether that server is using the intended database. A wrong database produces a
missing/mismatched citation in the viewer, rather than selecting another source.

A link binds the session, PDF hash, annotation ID, page, and hash of the exact
recorded passage. It overrides saved reading position, selects the quote, and
survives reload. If the original session is closed, the viewer opens another
reading session for the same paper and source revision.

The viewer checks PDF bytes, page bounds, and an unambiguous text anchor before
reporting success. Preflight cannot establish PDF text layout: a link can pass
database/hash checks yet report a missing or ambiguous quote when rendered.
APW's `docs/passage-navigation.md` defines the link and error behavior.

## Missing or changed sources

When preflight finds a missing/deleted annotation, edited passage, or inaccessible
or corrupt PDF, the brief preserves the imported quote and displays an actionable
**Passage unavailable** message in place of an active citation. It does not
substitute another document or delete RKS evidence. Unlinked notes state that no
source passage was recorded. The JSON result reports linked/unavailable passage
counts; an unavailable passage does not prevent an inspectable brief from being
written.

Restore the correct database/cache backup or explicitly repair and review a new
source anchor. After accepting an updated RKS import, generate a new brief. Old
briefs remain historical artifacts; they are not silently rewritten.

## Engineering demonstration and limits

Run the cross-repository integration suite with `RKS_TEST_PYTHON` and
`APW_TEST_PYTHON` set. It generates a redistributable PDF, ingests it, opens a
reading session, creates synthetic reading material, exports/previews/imports it,
generates a brief, and resolves its actual citation parameters through APW. A
deleted APW annotation then produces an unavailable-passage brief while keeping
the imported quotes. APW's browser suite independently exercises real two-page
PDF rendering and citation failure/recovery scenarios.

This is a generated engineering fixture. A representative scientific corpus,
qualified scientific review, and a researcher pilot remain later requirements.
The brief is an evidence inventory suitable for inspection, not a validated
scientific answer.

The next [scientific evaluation workflow](scientific-evaluation.md) supplies a
rights-cleared single-cell methods starter corpus, frozen draft questions, a
retrieval baseline, and an original-PDF journey. Its reference judgments still
require independent domain review.
