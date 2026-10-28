# Compare and review findings

Milestone 2 implementation, October 28, 2026. Available from repository `main`,
with matching RKS and APW commits pinned in `pyproject.toml`. This development
feature is not included in the tagged sci 0.3.1 release. Independent domain review
and release validation remain pending.

## Reader workflow

Open a prepared project with `sci resume --workspace review`. Import selected
passages through Evidence, then open **Compare**:

1. Create a comparison with a title and your criteria, one per line: dataset,
   assumptions, evaluation metric, limitations or applicability.
2. Inspect a paper/criterion entry. Write an interpretation, record experimental
   conditions, identify its human or agent origin, and choose imported evidence
   from that paper. Save the interpretation.
3. Inspect its original quotations and supporting passage links. The matrix
   keeps each paper's conditions separate. It labels gaps, drafts without
   supporting quotes, changed sources and review state explicitly.
4. A person can record a review of the **saved** entry with their name, scope,
   decision and statement, affirming that they performed the review. Unsaved edits
   must be saved first. Acceptance requires current supporting quotations.
5. Download the comparison as Markdown or reopen it from Saved comparison.

Criteria and paper sets are fixed at creation so existing reviews cannot be
retargeted. Create another comparison to change criteria or include papers added
later; the reader identifies those excluded papers. All entries start as gaps.
No agreement, contradiction or scientific comparability is inferred automatically.

## CLI and agents

The CLI and reader use the same RKS operations and stored identities:

```bash
sci compare create --workspace review --title "Method comparison" \
  --criterion "Dataset" --criterion "Assumptions" --criterion "Limitations" --json
sci compare list --workspace review --json
sci search "normalization" --workspace review --paper p1 --json
sci compare show COMPARISON_ID --workspace review --json
sci compare set COMPARISON_ID --workspace review --paper p1 --criterion c1 \
  --expected-revision COMPARISON_REVISION --text "Your bounded interpretation" \
  --conditions "Dataset, population, units and evaluation conditions; identify unknowns" \
  --origin agent --evidence NOTE_ID@EVIDENCE_REVISION --json
```

Replace uppercase placeholders with exact returned identities. Criterion IDs
(`c1`, `c2`, etc.) come from `create`/`show`; note IDs and evidence revisions come
from `search`. Repeat `--evidence` for selected records. Omitting evidence creates
an unsupported draft. Empty `--text` leaves a gap. Preserve numbers, units and
negation; original quotes remain separate from imported commentary and synthesis.

After inspection, a human can record their decision:

```bash
sci compare review COMPARISON_ID --workspace review --paper p1 --criterion c1 \
  --expected-revision CURRENT_COMPARISON_REVISION --reviewer "Actual reviewer" \
  --scope "What the person checked" --decision accepted \
  --statement "Their actual conclusion and limitations" --json
sci compare show COMPARISON_ID --workspace review --history --json
```

`needs_changes` is the other decision. Agent proposals must use `--origin agent`.
Agents must never invent a human reviewer, scope, decision or attestation; recording
an actual human decision requires explicit authorization. Reviewer names are
recorded assertions, not authenticated credentials. Acceptance does not change
agent origin or promote imported evidence's review status. Traceable source links
do not establish scientific validity.

Plain `show` prints Markdown and the current revision. JSON uses
`scientific-tooling.comparison.v1`: fixed criteria/papers, per-cell interpretation,
conditions, origin, exact evidence snapshots, support/review states, checked
passages and review history. `--history` adds all saved content versions. Reviews
record exact cell/evidence revisions and timestamps.

## Revision safety and recovery

RKS owns append-only comparison history, reviews and request receipts. A single
write transaction checks scope and the inspected revision before saving.
Concurrent or outdated writes fail with a reload instruction. Every cell edit,
including restoring earlier text, makes that cell's old review stale. Editing a
different cell leaves an unchanged cell's review valid. Changed imported evidence,
edited/deleted RKS notes, unavailable PDFs or unavailable APW passages make affected
support/reviews stale while retaining selected quotes and previous decisions.
Repair or explicitly select a fresh revision; evidence is never silently replaced.

Mutations save a request file before calling RKS. The response supplies its
`request_id` and path under `comparisons/requests/`. Recover a lost response with:

```bash
sci compare retry REQUEST_ID --workspace review --json
```

An identical request in the same exact project scope cannot duplicate versions or
reviews. A reused ID with different content/scope fails. A stale edit requires fresh
inspection and a new request. The reader reuses an identical failed request when
retried without changing its form. Saved requests remain available after closing
the browser.

Reads never initialize/migrate databases, start a reader or write project state.
Creating a comparison explicitly migrates an existing RKS database to schema 0015.
For an older project, create its first comparison to perform that migration; an
earlier list/read may report migration is required. Restore missing databases.
Stop writers and back up the entire project; RKS snapshots include comparison
versions, reviews and receipts. Passage links require the reader at its saved
address (`sci resume`).

## Acceptance still pending

Engineering fixtures cover transactions, scope, literal preservation, staleness,
recovery, source navigation and browser usability. Synthetic review records are
not scientific reviews. Independent domain reviewers must still assess real
comparisons for numerical values, conditions, negation and claimed contradictions,
followed by researcher pilots and coordinated release/installation checks.
Milestone 2 remains in progress until those gates pass.
