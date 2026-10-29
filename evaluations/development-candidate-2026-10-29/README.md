# Development candidate acceptance

Frozen October 29, 2026: **2026-10-29-c1**, sci **0.4.0.dev20261029**,
APW **0.3.2.dev20261029**, RKS **0.2.0**. This is a local development
candidate, not a release or scientific approval. The first development action
is to evaluate this exact combined source snapshot and retain its failures.

## Candidate identity and scope

The candidate includes project evidence search, comparisons, discovery, living
project history, draft analysis handoffs, and the continuous PDF reader. Source
archives and file-by-file SHA-256 inventories are retained at
`C:/Users/yangm11/github/.development-candidate/2026-10-29-c1/`.
[manifest.json](manifest.json) is the reviewable inventory. Re-run the frozen
`scripts/freeze_development_candidate.py --verify` against that directory to check
every retained source byte and archive. Archives, not the mutable working trees,
are the inputs to candidate builds. Any code correction requires a new child
candidate identity and new receipts; never replace this baseline's artifacts.

| Component | Base commit | Included changes |
| --- | --- | --- |
| sci | `5e8e50f3b2fdc31b6361fd0badbf29f6ad977897` | Existing analysis feature/resources/examples; freshness and shared state changes; guides and CI; candidate version and freeze utility |
| APW | `3ea2a5290f25dbc86a7ea178d0c0ed92849b2ba0` | Existing continuous scrolling renderer, page selection/search/annotation changes and built assets; candidate version |
| RKS | `44a8f33f47d9e867a03a8cff9e07a7b021e04cea` | Unchanged source |

The Git indexes and existing user changes are preserved. Per-user agent settings
and this evolving evaluation directory are excluded from source archives. The
staged removal of sci's personal `.claude/settings.local.json` is not product
work. Website and Cell Wonderland are outside this candidate and unchanged.

**Known publication blocker:** sci metadata and browser CI both pin APW
`3ea2a529...`, which does not contain the local continuous reader. Local wheel
testing must install all three recorded wheels with `--no-deps`. That deliberately
tests the combined candidate; it cannot pass the public-install gate. Publish a
validated immutable APW commit, coordinate both pins, and freeze a successor
before an ordinary install can qualify. RKS's immutable pin already matches.

## Contracts and migration expectations

- Workspace: `scientific-tooling.workspace.v2`; the existing v1 upgrade remains
  the only manifest migration. No additional candidate schema migration is intended.
- RKS: migrations through `0015_comparisons.sql`, including imported evidence
  (`0014`). Explicit comparison creation may migrate an existing older database;
  read-only commands must never create or migrate missing/older databases.
- APW: existing database initialization/migrations unchanged; reader changes must
  preserve session and annotation records. The manifest records the whole source.
- Brief history: `project-snapshot.v1`, `brief-edition.v1`, `project-update.v1`
  and `brief-request.v1` in the `scientific-tooling` namespace. Older outputs and
  their exact historical bytes must survive the freshness changes.
- Analysis: `analysis-request.v1`, `analysis-handoff.v1`, `analysis-check.v1`.
  This adds draft records, never execution or review approval. Inputs remain at
  their original absolute paths; file identity does not validate H5AD/RDS contents.

## Concrete acceptance and failure matrix

Status here records the **pre-test freeze**. Candidate execution results belong
in [results.md](results.md), with raw logs and command receipts. `NOT RUN` is not
a pass. Every row blocks release unless explicitly marked nonblocking.

| ID / owner | Acceptance case and required result | Failure case that must be rejected or reported | Frozen status / evidence |
| --- | --- | --- | --- |
| C01 Release engineering | Retained source inventories, three wheel hashes, installed versions/module paths and resources all match this candidate | Missing file, changed source/archive, editable/source-tree import, wrong dependency or mismatched skill hash fails qualification | NOT RUN; manifest created and archive bytes verified |
| C02 Release engineering | Ordinary public-dependency install and browser CI use the exact published candidate APW commit | Current old APW pin cannot qualify; no floating branch/local-path substitution | BLOCKED: current pin omits reader changes |
| S01 RKS and sci | CLI/HTTP search returns identical scoped note/revision/source identities; paper, review and match filters work; zero foreign-project hits | Foreign workspace/source, duplicate text, local note edits, corruption and empty queries have explicit outcomes | NOT RUN; installed workflow and RKS evidence-search suites |
| S02 RKS and domain reviewer | Imported-evidence endpoint reaches hit_at_5 >= 90% on answerable independently reviewed queries; report numerator/denominator and recall_at_5 separately | Unreviewed or claim-search labels cannot qualify; unanswerable questions reported separately | BLOCKED: independent labels and >=10 newly authored held-out questions absent |
| S03 RKS and sci | Fixed 10,000-evidence project; 100 warm queries; p95 <=2.0 seconds; retain raw timings, hardware and cold measurements | Smaller project, unrecorded warmup, dropped slow queries or startup mixed into search does not qualify | NOT RUN; benchmark fixture required |
| P01 APW and sci | All ten unchanged real pilot citations open the exact retained PDF/page/highlight | Changed/missing PDF, deleted/ambiguous anchor or incorrect page clearly rejects navigation and preserves quoted text | NOT RUN; full ten-citation candidate rerun required |
| R01 APW | Scroll a 30-page PDF, select on multiple pages, search, zoom, switch paper and reopen source; zero wrong-page annotations and zero stale cross-paper responses | Visible page drift, wrong-page highlight/search, unresolved blank page, stale callback or growing raster cache fails | NOT RUN; installed browser measurement required |
| R02 APW | At most 7 active raster canvases while scrolling 30 pages at 1440x1000, fit-width and 100% zoom; zero prior-document raster after switch; record placeholder count, pixel bytes and JS heap separately | Unbounded raster growth or foreign-document page state fails; heap values without supported measurement marked unavailable | NOT RUN; protocol revision 2 corrects the pre-test DOM-count metric |
| Q01 RKS and sci | Comparison create/edit/review/export/restart preserve exact versions; exact retry creates one receipt/version | Stale writers, changed request IDs, foreign source, changed support and conflicting edits fail; only affected reviews stale | NOT RUN; synthetic reviews test mechanics only |
| Q02 Domain reviewer | Inspect 3-paper/6-cell comparison and all 10 supports for values, conditions, negation, contradictions and applicability; retain actual decisions | Agent-written or synthetic identities cannot establish independent review; unsupported cells explicit | BLOCKED: actual reviewer decisions needed |
| D01 sci and APW | Saved runs reopen offline; exact selection/retry fetches once and creates one work/version; changed PDF creates a separate version | No PDF, invalid bytes, ambiguous identifier, competing attribution, interrupted acquisition, timeout and rate limit leave explicit recoverable states | NOT RUN; installed discovery suite/browser; audit timeout/rate-limit coverage |
| D02 sci and domain reviewer | Live PubMed query/PMID and Crossref query/DOI, with at least 2 identifiers per provider, preserve raw responses/query translation/date/hashes | Multiple/no full text and provider failure reported; no abstract promoted to PDF or silent alternate source | NOT RUN; broaden live receipt set and independent selection |
| M01 sci | Source/evidence/review mutations identify affected entries; unchanged display wording stays current; saved reports never refresh old brief | Missing DB, partial preparation, missing source or failed check preserves prior outputs and never creates a database or says current | NOT RUN; installed maintenance suite |
| M02 sci | Two editions retain exact canonical/Markdown bytes; lost publication resumes once; older retry cannot replace latest | Tampered history, stale observations, duplicate replay and silent overwrite fail | NOT RUN; installed maintenance/recovery and browser history checks |
| M03 sci and APW | Browser displays failed freshness check, changed brief, exact history and resumable failed request; bounded repeat selects nothing | Old-session responses and lost replies cannot falsely mark current or duplicate records | NOT RUN; existing browser journey only partially covers these faults |
| A01 sci | Installed create/list/show/check and exact replay preserve selected evidence/reviews, dataset SHA/size, parameters, environment bytes and packaged skill revision | Missing/changed inputs/support, malformed parameters, altered artifacts, foreign workspace or stale selection are explicit; original record unchanged | NOT RUN; installed analysis suite and valid synthetic dataset demo |
| A02 sci and domain reviewer | Unselected cell edit stays current; selected review/support edit becomes outdated; `not_run` and `not_recorded` preserved | Hash-only checks must never claim semantic input validity, resolved environment, approval or executed analysis | NOT RUN engineering; independent guide-only inspection still required |
| U01 Release engineering | Create a disposable 0.3.1 workspace, stop owned reader, back up entire workspace and hashes, upgrade at same absolute path; no lost or duplicate records | Missing backup, active writer, relocation or changing original pilot data cannot qualify | NOT RUN; retained stopped legacy fixture required |
| U02 Release engineering | Restore backup to its supported original path after stopping candidate reader; legacy install reopens original evidence and output bytes | Incomplete DB/PDF restore, duplicate records or unrecoverable output fails rollback claim | NOT RUN; no rollback claim before demonstrated restore |
| X01 Release engineering | Windows/Linux/macOS Python 3.14 installed suites; Linux 3.12/3.13/3.15; adapter Windows/Linux 3.12-3.15; browser CI and dependency checks all pass | Unsupported skip, mismatched pins or old-run results cannot satisfy candidate gate | NOT RUN; local Windows first, other platforms pending |
| H01 Research coordinator | Three researchers, including one domain reviewer, each complete guide-only discovery/search/comparison/change/handoff journey without developer repair | Developer-operated demo does not count; record assistance/time/corrections and rerun blocking failure | BLOCKED: three independent sessions required |
| G01 Documentation owner | Guides name actual dev versions, shipped scope and remaining limits; commands/resources work in wheel | Released availability claims or execution-ready analysis wording fails | NOT RUN; release labels remain unchanged |
| N01 Product owner | Automatic recurrence, portable export/restore and analysis execution remain explicit separate work | Implementing these as hidden acceptance dependencies expands scope | NONBLOCKING deferred scope |

## Frozen evaluation protocol

Protocol revision **1** is [protocol.json](protocol.json). Its SHA-256 is retained
in the build/test receipts before any candidate evaluation. [Revision 2](protocol-v2.json)
corrects only the reader raster metric after source inspection and before reader
measurement; the original protocol remains intact. Keep original failures
and thresholds; a justified protocol change gets a new revision and rerun. Evidence
retrieval labels, independent reviews and participants cannot be supplied by the
agent. Engineering work can continue while those inputs remain pending.

For reader memory, seven active raster canvases is an explicit ceiling at the
specified viewport and zoom. Empty canvas placeholders retain page geometry and
must be counted separately. This is an engineering acceptance bound, not a claim
about total browser memory. Record actual raster bytes and the renderer window.

## Immediate development sequence

1. Build and verify the frozen local wheels, run installed CLI/recovery suites,
   reader unit checks and existing browser journeys; retain each failure.
2. Trace failures to their cause. Freeze a child candidate for fixes, preserving
   this baseline and its failed receipts. Do not broaden feature scope.
3. Prepare imported-evidence and review fixtures, long-reader and history fault
   checks, then upgrade/restore evidence. Keep independent and platform gates open.
4. Publish dependencies and coordinate pins only after the release gates pass.

Reviewed inputs: [October 29 completion plan](../../docs/sci-roadmap.md#development-feature-completion-plan),
[evidence search](../../docs/evidence-search.md), [comparisons](../../docs/comparisons.md),
[discovery](../../docs/discovery.md), [living projects](../../docs/living-projects.md),
[draft handoffs](../../docs/analysis-handoffs.md), the October 28 umbrella handoff,
APW's reader plan, and existing `.living-project-pilot`/`.analysis-handoff` receipts.
Earlier receipts establish context, not results for this new candidate.
