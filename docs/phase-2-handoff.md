# Scientific Tooling: Phase 2 handoff

Updated October 29, 2026. Workspace: `C:\Users\yangm11\github`.

## Current publication checkpoint October 29

The development publication includes the accumulated sci implementation, guides,
analysis handoff, candidate records and imported-evidence evaluation. APW's
continuous reader is published at `4c3a379123847aff42e221013ae4c49a4149997d`;
sci's dependency and browser CI checkout both pin that commit. RKS stays at
`44a8f33f47d9e867a03a8cff9e07a7b021e04cea`. Versions remain sci
`0.4.0.dev20261029`, APW `0.3.2.dev20261029` and RKS `0.2.0`.

A fresh noneditable sci installation resolves those public Git dependencies.
Its module origins, installed checks and logs are recorded in the
[publication verification](../evaluations/publication-2026-10-29/README.md).
This is development source publication; no release tag or scientific approval
is implied. The frozen c1 sources, manifest and earlier receipts remain intact.
The published dependency metadata is newer than c1's original public pin, so
use the publication record for that install and freeze a successor before
qualifying further application changes as a candidate release.

The tracked handoff is
`structured-intelligence/docs/phase-2-handoff.md`; the umbrella file is its local
workspace copy. Preserve exact evaluation bytes: `.gitattributes` disables text
normalization for the candidate, imported-evidence and publication records so
their retained hashes survive cross-platform Git checkouts.

## Frozen candidate and imported evidence checkpoint

The current execution plan is the October 29 **Development feature completion
plan** in [the sci roadmap](../docs/sci-roadmap.md).
Candidate freezing and the imported-evidence fixture/review-packet implementation
are complete. Continue with the remaining acceptance gates below. The historical
checkpoints retain their original results; their clean-tree, dependency,
publication and next-step statements do not describe the current checkout.

The requested first action is complete: candidate **2026-10-29-c1** is frozen,
with a concrete 23-row acceptance/failure matrix, ownership, release-blocking
dispositions and frozen evaluation thresholds. Start with:

- [Candidate and acceptance matrix](../evaluations/development-candidate-2026-10-29/README.md)
- [Baseline results and remaining gates](../evaluations/development-candidate-2026-10-29/results.md)
- [Exact source manifest](../evaluations/development-candidate-2026-10-29/manifest.json)

This candidate includes existing evidence search, comparisons, discovery, living
project history, draft analysis handoffs and the continuous PDF reader. The
checkout at the freeze contained substantive uncommitted sci/APW implementation
and guide changes; the publication above includes them and the evaluation
tooling/records. The per-user `.claude/settings.local.json` removal is included,
with an ignore rule to keep it local. RKS is unchanged. The imported-evidence
slice changed sci scripts, tests, CI configuration and evaluation documentation,
without altering frozen c1 application code. The umbrella directory is not a
Git repository; the handoff is also retained in the sci repository.

Versions distinguish this local development build: sci `0.4.0.dev20261029`, APW
`0.3.2.dev20261029`, RKS `0.2.0`. Base commits are sci `5e8e50f3...`, APW
`3ea2a529...` and RKS `44a8f33f...`; their working-tree file hashes and full base
IDs are in the manifest. Frozen source archives, matching wheels, installed
environment, raw logs, screenshots and disposable projects are under
`.development-candidate/2026-10-29-c1/`. Reverification confirmed all frozen
source/archive bytes after the tests. Do not replace these artifacts with later
working-tree content; application corrections require a child candidate.

**Original candidate baseline:** 111 Python tests passed (19 installed workflow,
12 discovery, 4 atomic state, 21 maintenance, 9 analysis, 44 adapters, 2 native
boundaries), plus 103 reader unit tests and TypeScript/ESLint/Prettier. Both
installed browser journeys passed on desktop/mobile with real local HTTP and
frozen discovery fixtures. The 30-page fit-width smoke check peaked at 3 active
rasters and 10,956,960 canvas pixel bytes; 100% zoom and long-document annotation/
search gates remain pending. Protocol revision 2 preserves revision 1 and fixes
its original DOM-placeholder count to measure allocated rasters instead.

A disposable project created with the retained 0.3.1 installation was stopped
and backed up, upgraded with the candidate, and restored at its original absolute
path. Evidence replay remained one record, the legacy brief survived, and the
restored file hashes matched the complete backup. The old installation reopened
the restored brief. Both final readers were stopped at that checkpoint. The first fixture omitted
explicit legacy brief generation; its failure and backup remain retained, and
the corrected `upgrade-v2` exercise passed. It was a harness error, not data loss.

**Original c1 publication limitation:** the frozen sci metadata pinned APW
`3ea2a5290f25dbc86a7ea178d0c0ed92849b2ba0`, which lacks the continuous reader.
That candidate was tested with three matching local wheels and `--no-deps`.
The current publication above coordinates both public pins to `4c3a379...` and
checks a fresh ordinary install separately; it does not rewrite c1 or retroactively
qualify its old public dependency. Platform and independent-review gates remain.

**Imported-evidence slice implemented:** the [fixture, commands and reproduction guide](../evaluations/imported-evidence-2026-10-29/README.md),
[measured results and failure matrix](../evaluations/imported-evidence-2026-10-29/results.md),
and [source-linked review packet](../evaluations/imported-evidence-2026-10-29/review-final/review.md)
are ready. Native import/search runs cover 24 notes from ten papers and all 20
questions. Original-source hit at 5 is 17/18; a separately retained correction
completes a truncated q02 source paragraph and reaches 18/18, without changing
questions, relevance targets or ranking. Recall at 5 is 90.74% and 96.30%,
respectively. These remain draft-label measurements, not scientific validation.
The evaluator now checks actual installed module locations as well as candidate
hashes; earlier runs affected by a compatibility helper's checkout import are
retained but superseded. The final packet matched the pilot source identities at
the recorded October 29 check; rerun `check-packet` before using it for review.
It retains 26 pending decisions, zero approvals and zero new held-out questions.
Frozen c1 application code and source archives remain unchanged.

### Current implementation and command behavior

| File | Implemented responsibility |
| --- | --- |
| [research_imported_evidence.py](../scripts/research_imported_evidence.py) | `freeze`, `run`, `review-packet`, `check-packet` and `review-status`; sealed source/question mapping, native import/search evaluation and revision-bound review inputs |
| [research_corpus.py](../scripts/research_corpus.py) | Source validation, attribution and corpus helpers; imports `scientific_tooling.reading` directly without the compatibility wrapper's checkout-path insertion |
| [test_research_imported_evidence.py](../tests/test_research_imported_evidence.py) | 17 regression tests for identity, cutoff accounting, source correction, import isolation, review provenance and stale/unavailable support |
| [ci.yml](../.github/workflows/ci.yml) | Existing research-test discovery includes the new suite; source-only adapter and corpus checks explicitly set `PYTHONPATH: src` |

`freeze` records 23 canonical JATS excerpts and one whitespace duplicate from ten
papers. These enter APW/RKS as unlinked, unreviewed **commentary notes**, with no
fabricated PDF page anchors. Questions, draft answers and attribution metadata
are excluded from searchable note text. `run` verifies source bytes and actual
installed candidate modules before creating a fresh disposable project, imports
the selected notes, checks exact replay, and compares CLI orchestration with the
real hosted search handler. This slice does not test HTTP/browser transport.
Project state and both databases remain byte-identical across retrieval.

Top-five metrics use the first five native result slots, then collapse canonical
duplicates within that window. They never backfill from a sixth result. The two
insufficient-evidence questions are retained outside the 18-answerable-question
denominator. Hit rate and recall describe agreement with draft targets; precision,
scientific accuracy and abstention accuracy are not inferred.

The q02 correction extends one source slice from 767 to 1,052 characters through
the missing comparison sentences in the same pinned JATS paragraph. The original
corpus, all questions/relevance targets, other excerpts and ranking code remain
unchanged. The separately versioned correction requires independent review.

`review-packet` captures the existing comparison and all supports without changing
the original pilot. `check-packet` checks candidate identity, current comparison,
source bytes and available passage identities: exit 0 for current, 2 for changed
content, and 1 for an error such as unavailable/inconsistent support. It neither
launches the reader nor verifies browser quote matching. `review-status` rejects
missing, foreign, duplicate or stale targets and requires actual human provenance
for completed decisions. It does not check live freshness, authenticate identities,
write review into RKS or pass the release gate. Newly submitted held-out questions
are counted but are not validated or scored by this implementation.

### Authoritative artifacts and checks

Use `structured-intelligence/evaluations/imported-evidence-2026-10-29/`:

- [Original-source run](../evaluations/imported-evidence-2026-10-29/run-installed-original/results.json): `fixture-v2.json`, 17/18 hit at 5 and 90.74% recall at 5.
- [Corrected-source run](../evaluations/imported-evidence-2026-10-29/run-installed-corrected/results.json): `fixture-source-complete.json` with `corpus-source-complete/`, 18/18 hit at 5 and 96.30% recall at 5.
- [Final packet](../evaluations/imported-evidence-2026-10-29/review-final/packet.json), [readable review](../evaluations/imported-evidence-2026-10-29/review-final/review.md), [pending responses](../evaluations/imported-evidence-2026-10-29/review-final/responses.json) and [recorded freshness check](../evaluations/imported-evidence-2026-10-29/review-final/check.json).
- [Receipt index](../evaluations/imported-evidence-2026-10-29/receipts.json): retained files and implementation hashes; each final run also retains full responses, import receipts and the exact evaluator/helper source in `harness/`.

The final runs and packet verify sci `0.4.0.dev20261029`, APW `0.3.2.dev20261029`
and RKS `0.2.0` inside the candidate environment, including 16, 19 and 122 package
files respectively. `run/`, `review/`, `review-v2/` and `review-source-complete/`
are retained earlier artifacts, not the final installed-package qualification.
Full disposable projects remain under `.imported-evidence/c1-installed-original`
and `.imported-evidence/c1-installed-corrected`.

**Imported-evidence evaluation validation:** all 61 research adapter tests passed on Python
3.14 and Python 3.12, including the 17 new tests. The 3.12 run disables site
packages and explicitly selects checkout sources, matching the source-only CI
setup. [3.14 log](../evaluations/imported-evidence-2026-10-29/adapter-tests-final-installed.log),
[3.12 log](../evaluations/imported-evidence-2026-10-29/adapter-tests-python312-stdlib.log)
and [lint log](../evaluations/imported-evidence-2026-10-29/lint.log)
are retained. These follow-up counts replace 44 for the adapter suite; the original
111-test baseline above remains its own dated record. Hosted CI and unrelated
application suites were not rerun for this evaluation-only slice.

Use the frozen candidate interpreter for installed evaluation, without setting
`PYTHONPATH=src`. From the umbrella workspace, these checks are read-only:

```powershell
$candidatePython = '.\.development-candidate\2026-10-29-c1\installed\Scripts\python.exe'
$evaluationRoot = '.\structured-intelligence\evaluations\imported-evidence-2026-10-29'
& $candidatePython .\structured-intelligence\scripts\freeze_development_candidate.py .\.development-candidate\2026-10-29-c1 --verify
& $candidatePython .\structured-intelligence\scripts\research_imported_evidence.py check-packet "$evaluationRoot\review-final\packet.json" --candidate-manifest .\.development-candidate\2026-10-29-c1\manifest.json
& $candidatePython .\structured-intelligence\scripts\research_imported_evidence.py review-status "$evaluationRoot\review-final\packet.json" "$evaluationRoot\review-final\responses.json"
```

The [reproduction guide](../evaluations/imported-evidence-2026-10-29/README.md#reproduce)
has the `freeze`, `run` and `review-packet` commands. Global `--corpus` goes before
the subcommand; corrected fixtures require `corpus-source-complete/`. Use new
output directories, preserve frozen packets and copy responses for a real reviewer.
The original pilot is `.living-project-pilot/single-cell-de`, comparison
`cmp_0f45d3e27fa044729c08b9a906132f57`. Local passage URLs require that original
project and its reader at the saved address; publisher links are also retained.

### Remaining gates and next work

| Gate | Current disposition and next evidence |
| --- | --- |
| S01 imported-evidence search | Partial: native import/search, handler parity and identity/filter checks passed; broader fault/filter and HTTP coverage remain |
| S02 retrieval evaluation | Blocked on independent review of the 20 questions and at least 10 new independently authored frozen questions; draft scores do not qualify it |
| Q02 scientific comparison | Packet ready; actual domain review of six cells and all ten supports remains pending |
| M03 browser recovery | Add failed freshness-check and lost brief-publication-response cases against an installed candidate |
| P01 real citations | Recheck all ten real pilot passage links and deliberate failure cases in the browser on the candidate |

Keep the original 23-row matrix and the imported-evidence follow-up dispositions
together; preparing review inputs does not turn an independent-review gate green.

**Next engineering slice:** fill browser fault and real-citation coverage.
Actual independent labels, six-cell/ten-passage review, three researcher
sessions, 10,000-record latency, the ten real pilot citation rerun, full native
suites and Linux/macOS release checks remain open. No agent-operated fixture is
independent scientific review. Draft analysis remains `not_run` / `not_recorded`;
automatic recurrence, portable restore and analysis execution remain separate work.

## Historical checkpoints

The following records preserve prior work and its evidence. Commands, environment
advice, release statements and next actions in this historical section apply to
their original checkpoints. Use the current checkpoint above and the updated
next-session prompt at the end for continuation.

## Earlier objective and checkpoint

The user asked for an assessment and phased improvements across all five
repositories, prioritizing **overall research usefulness**. An earlier request
was to commit the changes, start Phase 2, and prepare a handoff if a new session
would help. Source reading, selected evidence import, exact source-passage
navigation, and source-linked reading briefs are now implemented and committed
locally. A licensed single-cell RNA-seq methods starter corpus and its initial
retrieval/original-PDF evaluation are also implemented and committed. All five
repository working trees are clean at this checkpoint. The measured RKS
whole-query retrieval bottleneck is now fixed and its frozen-question rerun is
committed. Continue with independent domain review and newly held-out questions;
do not restart the umbrella assessment or corpus collection. Phase 2 is not
scientifically validated.

The governing implementation preference is to fix root causes elegantly, tracing
the true source before adding fallbacks. Keep orchestration in Structured
Intelligence, durable evidence in RKS, and source reading/annotations in APW.

The umbrella directory is not a Git repository. This handoff and the umbrella
plan are local files outside the five repositories. The implemented workflow
documentation is tracked in Structured Intelligence.

## Previous work: sci roadmap milestone 3 (October 28, 2026)

The user requested **Discover and add relevant papers**. A local development slice
now spans Structured Intelligence and APW; RKS is unchanged. Nothing from this
milestone has been committed or pushed. The three main branches still start at
the milestone 2 commits listed below. No new release tag exists.

- `sci init` creates a question-only project. `discover search/lookup/list/show`
  provides bounded PubMed/Crossref queries and DOI/PMID lookup, saved raw responses,
  hashes, normalized candidates and exact query/provider/date provenance. The
  installed package reuses the existing NCBI skill's PubMed parser.
- Explicit `discover select`/`retry` creates bibliographic works with provider
  aliases, selection receipts and distinct PDF versions. Retained source hashes
  precede native RKS ingestion and APW session creation. Identical PDFs reuse a
  paper; changed bytes create a version. Conflicting identities fail explicitly.
  Unavailable full text remains a reference, never an abstract masquerading as a PDF.
- The reader offers capability-gated discovery in paper navigation, saved searches,
  metadata/source inspection, explicit selection, missing-full-text states and
  recovery. Lost selection replies reuse request IDs; old-session replies are
  discarded. The CLI also supports explicit local PDF attribution.
- Library-owned reader process handles now remain owned until shutdown/reaping,
  fixing ResourceWarnings exposed by direct installed recovery tests. Startup
  acknowledgements and instance-token shutdown ownership remain intact.

Read `structured-intelligence/docs/discovery.md` for commands, limits, source
contracts and acceptance gates. Question-only projects initially use the CLI;
the browser opens after the first PDF. PubMed does not imply a PDF from PMCID.
The retired PMC OA service is not used. Crossref-declared PDF links remain
unverified until acquisition; the client never silently tries another source.

Validation artifacts are under `.discovery/`, with matching local wheels and the
fresh Python 3.14 environment `.discovery/installed`. Installed workflow tests:
19 passed; research adapters: 44; native reading/evidence integrations: 2;
discovery tests: 11 (`discovery-state-fixed.log`); atomic record tests: 4
(`state-tests.log`). Final workflow recheck: `workflow-state-fixed.log`. The final
browser receipt and screenshots are in `.discovery/browser-state-fixed/`.
APW frontend: 64; backend: 118 passed, one Unix-specific
skip. TypeScript, ESLint, Prettier and Ruff checks passed. The initial backend run
hit the previously observed Windows socket abort in an existing request-guard
test; its 10-test group and a complete 119-test recheck passed. A Windows-locked
old output log required a fresh log name; no test failure was inferred from it.

Later discovery reruns exposed an independent Windows record-publication failure,
also reproducible without application imports or active reader processes. The
standalone diagnostic (`atomic_probe.py`, `atomic-probe.json`) recorded 62 access
errors in 3,000 `os.replace` writes. Switching to documented `FileRenameInfoEx`
POSIX replacement semantics gave zero in 3,000 (`atomic-posix-probe.json`). sci
now uses that operation on Windows and opens state readers with delete sharing;
other systems retain `os.replace`. This fixes the publication semantics rather
than retrying access errors. The initiating external holder was not identified;
Restart Manager reported none by inspection time. Exclusive locks and read-only
attributes still fail explicitly. Windows state publication requires modern
filesystem support for FileRenameInfoEx (validated on local NTFS).

The real HTTP browser fixture journey exercises explicit selection, lost-reply
replay without another PDF fetch, missing full text, selected-source navigation,
desktop/mobile layouts and zero page errors. Live Crossref and PubMed searches
also succeeded. Crossref lookup `10.1038/s41467-019-12266-7` returned the Nature
PDF, which was selected into `.discovery/live`. Its retained SHA-256 matches the
existing corpus (`112dcf8f...2940`, 3,995,480 bytes); exact replay succeeded.
These are engineering/source-integrity checks, not scientific relevance review.

**Publication gate:** publish the APW changes first, then update sci's dependency
pin and browser CI checkout to that exact published commit. The newly added CI
discovery checks require that coordinated pin update; current pins still resolve
the milestone 2 reader. Verify a new ordinary public-dependency install and CI
before release. Independent relevance, usability and full-text coverage evaluation
remain pending. The guide and roadmap deliberately mark milestone 3 in progress.

## Previous work: sci roadmap milestone 2 (October 28, 2026)

The user requested **Compare and review findings**, the second item in
`structured-intelligence/docs/sci-roadmap.md`. Both milestones were committed and
pushed to `origin/main` on October 28 at the user's request:

- RKS `44a8f33f47d9e867a03a8cff9e07a7b021e04cea`.
- APW `fe16190d51dfa410273bce3d2621af1a4ed2fb43`.
- Structured Intelligence `ab1af35f38fe7b812077471f022d4e3893212476`.

sci now pins those exact published RKS/APW commits, and its browser CI checks out
the same APW revision. A fresh ordinary installation fetched those public pins;
`direct_url.json` confirmed both commit IDs, `sci doctor` passed, and both comparison
recovery tests passed. Logs and environment: `.comparison-review/pinned-installed`,
`pinned-install.log`, and `pinned-comparison-tests.log`. This publishes source on
main; no release tag was created. Independent scientific acceptance remains pending.

- RKS schema 0015 owns comparison definitions, append-only cell versions, scoped
  human review assertions and exact request receipts. `rks comparison` exposes
  list/show/evidence/apply. One transaction validates exact project/source scope,
  selected revisions and optimistic concurrency; stale writers fail, exact retries
  do not duplicate history. Snapshots preserve comparison state. Reads never migrate.
- sci `compare create/list/show/set/review/retry` coordinates those native operations,
  records durable requests, checks APW passages and renders source-linked Markdown.
  Explicit creation migrates an existing RKS database; missing databases must be
  restored. Source failures preserve original quotations and invalidate affected
  support/review labels. Review identity is a recorded human assertion, not authentication.
- APW exposes a capability-gated Compare tab: researcher-defined criteria, paper
  matrix, explicit missing/unsupported entries, distinct agent/human interpretations,
  experimental conditions, selected source quotes, scoped review and Markdown export.
  Reviews require saved edits and human attestation. Changed selections are never
  silently replaced, agent origin remains explicit, and delayed old-session responses
  cannot update the current view. Saved text fields have stable accessible labels.
- Comparisons retain the paper set and criteria from creation; adding papers later
  requires a new comparison and is explicitly reported. Cell edits stale older
  reviews even when restoring earlier wording; other cells' reviews remain scoped.
  Underlying imported evidence review status is never promoted by comparison review.

Read `structured-intelligence/docs/comparisons.md`,
`research-knowledge-substrate/docs/comparisons.md`, and the updated APW host contract.
Independent domain review of real values, conditions, negation and contradictions
remains pending. Tests use explicitly synthetic reviewer identities only.

Verification uses fresh local wheels in `.comparison-review/installed` (Python 3.14),
installed together with `--no-deps`. RKS: 169 tests + 42 subtests; frontend: 61 tests,
TypeScript/ESLint/Prettier/build; sci: 44 adapters, 18 installed workflow tests,
2 installed boundary tests and native PowerShell manual syntax passed. Bash syntax
is skipped on this Windows host. An initial all-test discovery mixed source adapters
into the installed package tests; rerunning through the documented separate entry
points passed, including the packaged skill check. The initial APW backend run had
one Windows socket abort; all 10 request-guard tests passed immediately afterward.
The final APW backend run passed: 118 tests, one Unix-specific skip. The complete
two-paper Chromium journey passed on desktop and mobile, including matrix creation,
scoped synthetic review, restart persistence, stale review after edit, source links,
download, no viewport overflow and no page errors. Artifacts and receipt are in
`.comparison-review/browser-final/`; tests stopped their owned readers. Final
TypeScript, ESLint, Prettier, Ruff and whitespace checks passed.

Use `.comparison-review/installed/Scripts/sci.exe` for the coordinated local build.
The wheel filenames retain development baseline versions; they are not published
releases. `.comparison-review/wheels/` holds all three matching wheels. The hosted
comparison envelope was subsequently cleaned up to preserve its list schema;
the final installed comparison tests verify that exact rebuilt sci wheel.

The pushed sci commit starts the Windows/Linux/macOS normal-install CI matrix.
Before release, review those results and complete independent acceptance work.
Keep dependency and browser-checkout pins coordinated at exact published commits.

## Previous work: sci roadmap milestone 1 (October 27, 2026)

The user's next request was to follow the roadmap and get started. The selected
roadmap is `structured-intelligence/docs/sci-roadmap.md`; its first milestone is
project-scoped evidence search. A local implementation now spans RKS, APW and sci.
These three working trees have uncommitted changes; earlier clean/pushed statuses
below describe their own historical checkpoints. The website and Cell Wonderland
remain unchanged.

Implemented:
- RKS `note search-evidence`: required workspace/source and exact paper/hash scope,
  current imported quotations and commentary, paper/review filters, existing BM25
  or literal-phrase ranking, explicit match roles, stable pagination and identity.
  A read-only transaction validates current evidence/review revisions and reports
  locally edited/retargeted notes. Metadata cannot create text matches.
- sci `search` in text/JSON and a shared hosted GET operation. Scope comes from
  the project manifest. Source/annotation checks reuse the brief's APW contract;
  unavailable sources retain imported text without an active link. Search does not
  start a reader, initialize databases or modify the manifest.
- APW Evidence search at the top of the tab, with paper/review/match filters,
  source/commentary labels, identity details and passage links. A host advertises
  the capability explicitly. Query/filter/session changes discard delayed replies.
- Installed verification exposed a Windows startup race: a server ownership file
  could be visible before it was openable during publication. An isolated
  first-publication probe reproduced it. Startup now waits for a child-process
  acknowledgement after publication, verifies the same instance over HTTP and
  cleans up only its launched child on failure. It does not suppress permissions
  or retry file reads. Two tests enforce publication order and failure cleanup.

Read `structured-intelligence/docs/evidence-search.md`, the updated RKS evidence
import/search docs, and `agent-pdf-workbench/docs/workflow-host.md` for contracts.
Milestone 1 remains in progress: no independent scientific review or researcher
pilot occurred. The implementation and local wheel builds are unpublished.

Public dependency pins are intentionally still the released 0.3.1 baseline.
Before normal installation/release, publish compatible RKS/APW revisions, update
both exact sci dependency pins and its APW browser-checkout pin, then run the normal
Windows/Linux/macOS installation matrix. The local test environment installs all
three matching wheels with `--no-deps`; it is not a test of the old public pins.
Do not push sci alone or replace pins with floating branches/local paths.

Validation artifacts and the isolated Python 3.14 installation are under
`C:\Users\yangm11\github\.evidence-search`. Final Windows verification:
- RKS full suite: 162 passed plus 42 subtests before the additional merge-scope
  test. Final focused search suite: eight passed plus 16 subtests, including merge.
- APW backend: 119 tests, 118 passed and one Unix-only skip. Frontend: 57 passed;
  TypeScript, ESLint, Prettier, Ruff and production build checks passed.
- Existing sci source/corpus adapters: 44 passed; registry validation passed.
- Final isolated-wheel workflow suite: all 16 passed in 159.323 seconds, including
  search, migrations, recovery, source checks and the startup-publication fix.
- Final installed Chromium journey passed: two papers/tabs, browser selection,
  preview/import, briefs, project search, paper/review filters, commentary labels,
  desktop/mobile layouts and source citations after restart. Screenshots were
  visually inspected. All owned test readers were stopped.

Use `workflow-verified.log` and `browser-verified/receipt.json` for the final
installed outcomes. Earlier `workflow-final.log` records the reproduced startup
race before the acknowledgement fix, not the final result. No hosted CI, fresh
Linux/macOS run, scientific review, release, commit or push occurred in this turn.

## Previous checkpoint: PDF reader redesign (October 27, 2026)

The user authorized a full reader overhaul. APW and sci are now 0.3.1. The reader
has one project navigation area with its research question, more space for the
PDF, resizable sidebars, focus mode, and Evidence / Notes / Brief tabs. Mobile
drawers are exclusive and dismiss with Escape. Notes link to readable highlights;
technical IDs and activity logs remain expandable. Imported selections show a
status, with source links and downloads in the Brief tab.

The optional hosted workflow model is shared by navigation and evidence views,
and bound to the current session. Delayed responses cannot update another paper,
duplicate submissions are blocked, and rejected imports retain conflict details.
RKS ownership, source checks, import review semantics and workspace schemas are
unchanged. Continuous PDF scrolling remains future work.

Committed and pushed:
- APW: `1773e6b4b44fd9950f7a08399f480e653e8dbedf`
- Structured Intelligence: `aacee5c8c978d11c442ec24b83a74d2341258b5a`
- Website: `d7fa0fb5d5c67cc8a6a5cba54e6c2c05ac15990a`

Local verification: 54 frontend unit tests, 40 Chromium tests, TypeScript/lint/
format/build checks, and 119 Python tests (118 passed; one Unix-only test skipped
on Windows). After the final mobile styling adjustment, all 20 layout/theme tests
passed; expanded contrast assertions also passed. A fresh Python 3.14 installation
of the sci wheel fetched the exact public APW commit above and passed all 12
workflow/recovery tests and the two-paper browser journey, including separate
tabs, preview/import, downloads, mobile panels, and citations after restart.
The four website guide tests passed. All owned test reader processes were stopped.

Artifacts are under `.reader-redesign/`: `browser-installed/receipt.json`,
screenshots, test logs, `dist/`, and the fresh `installed/` environment. The website
guide and sci roadmap describe the current tabs and focus/resizing controls.
Upgrade using the quick-start install command after stopping an old reader;
resume the same workspace afterward. These are engineering checks, not scientific
validation of the corpus or imported interpretations.

Hosted checks all passed: APW `40565591181` (10 jobs), sci `40566032935`
(18 jobs, including Windows/Linux/macOS installations and the browser journey),
sci docs deployment `40566032990`, and website deployment `40566047224`.
The live guide returns HTTP 200 and includes version 0.3.1, the Evidence and Brief
tabs, and focus-mode instructions. All five repositories are clean and their
local main commits match remote main.

## Previous checkpoint: multi-paper projects (October 27, 2026)

The user's latest request was to implement multi-paper projects in `sci`. This
supersedes the earlier single-paper workflow limit. Scientific Tooling and APW
are now 0.3.0; RKS stays at 0.2.0. Python requirements are unchanged.

Committed and pushed:
- Structured Intelligence: `c3ee3329ee3ff8c3da23618b47ee648ebbfd46ff`
- APW: `36112db1776b8543a062f57234df7290309137dc`
- Website: `a8f7ac938cdc57cdaed725b067bb168a32e84ba5`
- RKS remains `fd44ad7388abb482a5980508531383cacf4da381`.

`sci start` accepts multiple PDF paths. `sci add`, `sci papers`, and `sci open p2`
grow, list, and navigate a project. All papers share one question, RKS database,
APW event store, and reader process. Each paper retains a separate hash identity,
session, handoff, import preview and progress. `annotate` and `preview` require
`--paper` in multi-paper projects; status/resume also accept it. Apply identifies
the paper from its preview. Browser actions use the tab's session, with no global
active-paper state. RKS imports remain native and transactional.

Workspace schema v2 contains a paper list. Legacy v1 workspaces migrate on a
locked save, retaining `workspace.v1.json` and all existing artifact paths,
identities and source links. Stop an old reader before upgrading; after migration
use sci >=0.3.0. Duplicate PDF bytes are reused; different revisions remain
separate papers. Interrupted additions recover via the native RKS source reference
and verified PDF hash, not filename/title matching. All selected input paths are
validated before a start/add changes the manifest.

Project briefs group verified imported evidence by paper and include a coverage
table. Papers without evidence are explicit gaps. No scientific agreement,
contradiction or conclusion is automatically inferred, and no human review is
fabricated. The website guide and bundled agent workflow describe these commands.

Validation completed locally:
- 12 installed workflow tests (recovery, duplicates, input validation, two-session
  isolation, project briefs, migration, ownership and prior single-paper behavior).
- 44 source/corpus adapter tests and both real RKS/APW adapter integration tests.
- Reader TypeScript/lint checks, 50 frontend tests, rebuilt packaged assets.
- Final wheel installed into a fresh Python 3.14 environment with exact public
  dependency commits; Chromium verified single/multi-paper highlights, two tabs,
  preview/import, downloads, mobile layout and both citations after restart.
- Actual 0.2.0-to-0.3.0 migration preserved previews, brief, session and links, then
  successfully added another paper. The preview response adds paper attribution;
  every pre-existing preview field remains unchanged.
- Four website tests and desktop/mobile/no-JavaScript guide checks passed.

Artifacts: `.multi-paper/browser-final/`, `.multi-paper/migration-receipt.json`,
`.multi-paper/installed/`, and `.multi-paper/wheels/` under the umbrella workspace.
All owned test readers were stopped. These are engineering checks, not scientific
validation of the single-cell corpus or an endorsement of imported interpretations.

Hosted checks all passed: APW `40558851954`, Structured Intelligence
`40559508912` (including Windows/Linux/macOS installed workflows and the
multi-paper Chromium journey), and website deployment `40559521497`. The live
guide passed desktop/mobile/no-JavaScript navigation and command-copy checks.
All five repositories are clean and their local main commits match remote main.

## Previous checkpoint: Python runtime upgrade

The user approved the proposed Python maintenance phase. The core tools now
require Python >=3.12 and recommend/default to 3.14. Each Python repository has
`.python-version` set to 3.14. RKS, APW and scientific-tooling are version 0.2.0.
The core test matrices cover 3.12, 3.13, 3.14 and 3.15; browser/native-shell and
release builds use 3.14. Site checks cover 3.12, 3.14 and 3.15.

Committed and pushed revisions:
- RKS: `fd44ad7388abb482a5980508531383cacf4da381`
- APW: `dec1c1602f4b20605dead4d6f504b0f3d53f66e3`
- Structured Intelligence: `983f7474694b64fe6dddbeb36bbe2c684faf44ee`
- Website: `7820b12dea7d7082c07b7982c8e1cad3e96784c4`

The workflow pins those exact RKS/APW commits. A fresh 3.14 environment installed
the final wheel and fetched both public Git revisions; their `direct_url.json`
identities, package metadata, bundled skill export and full browser journey
passed. Package installation, diagnostics, bootstrap version checks, linter
target, registry versions, current English/Chinese requirements and manual docs
agree on the minimum. APW uses the supported datetime.UTC alias. Historical
benchmark records retain their original Python versions.

Local verification:
- RKS: 155 tests + 26 subtests on each of 3.13.18, 3.14.10 and 3.15.2.
- APW: 70 unit tests including installed MCP, plus 49 integration tests on each
  version (one platform-specific integration skip).
- SI: 44 source-adapter tests and 8 installed-workflow tests on each version;
  PowerShell syntax passes. Both opt-in reading/evidence integration tests pass
  with RKS_TEST_PYTHON/APW_TEST_PYTHON set to the installed 3.14 interpreter.
  Those opt-in checks now run in installed-workflow CI as well.
- Old 0.1.1/Python 3.12.14 workspace -> 0.2.0/Python 3.14.10 migration preserves
  the session, viewer URL, unreviewed status, replay semantics and source links.
- The final public-pin installation passes desktop/mobile highlight, preview,
  import, brief download, source navigation, stop and resume in Chromium.
- The public guide is deployed with 3.14 recommended and 0.2.0 documented;
  command copying, agent links, old URLs and no-JavaScript navigation pass.

All hosted runs succeeded: RKS `40553949927`, APW `40553964194`, site
`40554445083`, and SI `40554428928`. All 18 SI jobs passed, including the
macOS Bash/zsh manual walkthrough, Windows/macOS installed workflow, Ubuntu
browser journey, and Python 3.12-3.15 compatibility coverage. The macOS manual
job briefly waited for a hosted runner and then passed without changes.
All five repository working trees were verified clean and their local HEADs
match remote main, including the unchanged Cell Wonderland repository.

Isolated runtimes, wheels, receipts and logs are under `.python-upgrade/` in the
umbrella workspace. Runtime installation used --no-bin and --no-registry;
system Python and existing virtual environments were preserved. Bioinformatics
Conda environments keep their separately pinned Python 3.11/scientific libraries;
they need their own coordinated dependency upgrade. Cell Wonderland is unchanged.
No PyPI release or tag was created; the documented Git installation is updated.

Verification setup details: build wheels once from clean snapshots before
installing them into multiple environments; concurrent pip builds of the same
checkout race on setuptools' shared build directory. SI source-adapter suites
insert src into sys.path, so run them separately from the installed-package suite
as CI does. Combining their discovery in one process shadows the installed skill
package and does not test the intended installation. No runtime fallback was
added for either test setup issue. The repository working trees are clean.

## Previous checkpoint: complete website redesign

The user explicitly requested a modern, professional, light, friendly redesign
from a new layout. Website commit `60fd8e0b01bab46be3443ae85c7f8c0cc3484010`
is committed and pushed to `main`; GitHub Pages run `40549139975` passed its
four Windows/Ubuntu and Python 3.10/3.12 validation jobs and deployment.
The website working tree is clean. Other repositories were not changed.

The homepage now leads with researcher tasks: a centered introduction, an
interactive Read / Collect / Brief example, three task paths, an agent prompt,
and a compact list of tools. Manrope typography, white surfaces, violet accents,
soft green/blue details, and new spacing replace the previous serif/teal layout.
The quick start, compatibility pages, 404 page, and social preview match.
The original commands, source Markdown, canonical guide URL and legacy routes
remain available.

The example uses an exact excerpt from Hafemeister and Satija (2019), DOI
`10.1186/s13059-019-1874-1`, original PDF page 1, under CC BY 4.0. Its page was
checked with PDF.js against the existing licensed corpus PDF. It is explicitly
an illustrative website workspace, with an unreviewed interpretation, not a
live backend session. `examples/single-cell-brief.md` is its attributed download.

Verification passed locally and on https://scientifictooling.org/: desktop,
tablet, mobile and 320px widths; 200% text size; keyboard tabs and stage links;
source anchors; example download; command copy; guide navigation and print;
legacy routes; no-JavaScript content/navigation. Render/source checks and all
four site tests pass. Local text contrast checks cover all three example stages,
quick start, legacy and 404, with no failures. Screenshots were visually inspected.
An initial live-test overflow was a test synchronization race: after click and
`document.fonts.ready`, the document was still interactive with no stylesheets.
Waiting for page load before measuring fixes the harness; live styles match the
committed files. No production fallback or overflow-hiding patch was needed.
Receipts and browser harnesses remain in ignored `.preview/`, especially
`verify_redesign.mjs`, `live-redesign-receipt.json`, and
`live-guided-site-receipt.json`.

## Previous checkpoint: website UI polish

The user requested a layout, typography and color polish of the GitHub Pages
site. Website commit `9c13ef7c77930bc6cf7059b2d695ec6d2ebedab1` is committed and
pushed. The site now uses warm
neutral backgrounds, dark ink, teal accents, simpler navigation, clearer project
cards and a PDF-to-brief workflow panel. Project capabilities use native details
controls. The quick start keeps its canonical source and command blocks, with
step shortcuts, numbered headings, a current-section sidebar, improved command
blocks and matching legacy/404 styling. The homepage now presents projects before
the background explanation. The quick start remains the main onboarding route.

Manrope and Source Serif 4 variable fonts are self-hosted under `assets/fonts/`
with their upstream SIL OFL licenses preserved. `theme.css` is still the shared
typography source; font URLs use the domain root for downstream project pages.
This change affects only the organization website; RKS/APW/CLI code is unchanged.

Local checks passed: the four existing site tests, JavaScript syntax and
Prettier checks, real browser navigation/copy/legacy-link checks, and a separate
UI pass at widths 1440, 834, 390 and 320 px. Browser checks covered font loading,
absence of external font requests, keyboard disclosures, step anchors/current
section, 200% text enlargement, print colors/wrapping, no horizontal overflow,
and navigation/disclosures without JavaScript. Text contrast sampling on the
homepage, guide, legacy page and 404 page passed applicable text thresholds
(minimum observed 4.79:1). Desktop/tablet/mobile screenshots were inspected.
This is a bounded UI verification, not a comprehensive accessibility audit.

Website run `40544153251` passed all four validation jobs and deployed
successfully. The public site passed the full UI checks at all four widths,
200% text enlargement, local font loading and navigation without JavaScript.
Live desktop/mobile guide copy, anchors, print controls and every legacy URL
also passed. The repository is clean and matches origin/main. Screenshots and
receipts are under the ignored website `.preview/` directory.

## Previous checkpoint: one onboarding route, advanced manual reference

The user accepted the recommendation to make the quick start the main onboarding
path and retain the detailed walkthroughs as advanced reference. Implemented and
pushed on October 27:

- Structured Intelligence `57c987029d790b4af812599bcded7fc0761715bd`: canonical
  manual documentation under `workflows/research/manual-operations/`, with
  Windows/PowerShell and Linux/macOS references and a shared index. All 15 shell
  command blocks are unchanged. The existing syntax checks and full Unix
  CLI/HTTP verification moved from the site into this repository and its CI.
- Website `edebf760d24d0700086c936f13c2fa3530ba9452`: homepage navigation, main
  action and project cards go directly to `/guides/paper-to-brief/`. The quick
  start has no platform tabs. Old chooser, Windows and Linux/macOS URLs remain
  lightweight landing pages linking to the quick start and the appropriate
  advanced reference. Old Markdown URLs remain as generated pointer documents.
  Legacy pages use the quick-start canonical URL and are excluded from the
  sitemap. Detailed manual content has one owner in Structured Intelligence.
- RKS `dd4a2c9d2590fc7b3a6325ae5df3bcca701bd0a1` and APW
  `a119f203cebaa9aa97d8a3406e222e069c2ecad7`: README onboarding links point directly
  to the shared quick start. These are documentation-only changes; the `sci`
  package, dependency pins and runtime behavior are unchanged.

Local verification passed: four site tests (generation, copy fidelity, discovery/
canonical destinations and owned links), native Windows/Linux manual syntax
checks, unchanged-block comparison, advanced-doc relative links, registry/YAML
validation, moved-test lint checks and whitespace checks. Desktop/mobile browser
checks verified direct discovery, no tabs, command copy, agent anchors, print,
all old-page destinations, overflow and navigation with JavaScript disabled.
Screenshots were inspected. All four repositories are clean and match origin/main.

Hosted Structured Intelligence run `40541162492` completed successfully,
including both relocated Unix walkthrough jobs and the installed/browser
workflow checks. Website run `40541223766` also succeeded and deployed. The
public website passed the same desktop/mobile and JavaScript-disabled navigation
checks, including every legacy URL and the advanced-reference destinations.
RKS `40541242473` and APW `40541260260` remain in progress for their README-only
commits; no failure has been reported at this checkpoint.

## Previous checkpoint: shorter `sci` command

The user requested a shorter command. Structured Intelligence
`8d89cd9e9627c525c4ad9728d723640657fd577c` publishes package version 0.1.1 with
`sci` as the preferred console entry point. `scientific-tooling` remains an
equivalent alias; the package name, Python namespace, schemas, dependency pins
and workspace formats are unchanged. The quick start and bundled agent skill
use `sci`, and their installation command includes `--upgrade` for existing users.
The repository's development environment and isolated installed-package Windows
and Linux environments were upgraded successfully.

Website `5728437520f93e9661d2ec1eaa605d36eeb02aae` updates the canonical guided
Markdown and generated HTML. Both commits are pushed; both repositories are
clean and match origin/main. The earlier suggestion to consolidate the manual
walkthroughs was advice only and has not been implemented.

Verification: built the sdist and wheel, upgraded an existing 0.1.0 installation,
checked both installed aliases and doctor, and passed all eight real workflow
tests through the installed `sci` launcher on Windows and Linux. The real browser
journey also passed using `sci` (highlight, preview/import, brief download,
passage link, stop/resume, and mobile controls). Site tests passed five cases
with the native Unix syntax test skipped on Windows. Registry validation,
targeted Python error checks, JavaScript syntax and whitespace checks passed.
A broader Ruff invocation found seven existing style findings; comparison with
the previous commit confirmed no new findings.

Hosted checks: website deployment run `40539436629` completed successfully;
the live guide was fetched and verified to contain `sci start` and the 0.1.1
upgrade note. Structured Intelligence run `40539399815` passed registry,
all four adapter jobs and installed-workflow jobs on Windows, macOS and Linux
(Python 3.10 and 3.12). Its hosted browser job subsequently passed; the entire
run is confirmed successful.

## Previous checkpoint: guided CLI, agent skill, and reader evidence controls

The user found the manual walkthrough too tedious and authorized the recommended
agent-led experience backed by a deterministic workflow CLI. The implementation
is committed and pushed:

- APW `6e95aadc58657b7e3e6ce1cb08472efc00491d81`: optional embedded workflow host
  and Evidence & brief panel, with built reader assets.
- Structured Intelligence `2d5a0a0bc752b0766cbb6f58c86b3ff3c5649c2e`: installable
  `scientific-tooling` package, resumable CLI, bundled `paper-to-brief` skill,
  cross-platform installed-wheel CI and real browser journey test.
- Website `bb7ef4b054be3cee9444179b32253fc675452b30`: guided quick start at
  `https://scientifictooling.org/guides/paper-to-brief/`, recommended from the
  existing walkthrough start page and both manual guides. Pages run `40533601706`
  passed all required validation jobs and deployed the new guide.

The CLI supports start/resume/status, selected preview/apply, unreviewed annotation
creation, brief generation, owned-reader stop, doctor and explicit skill installation.
One PDF and one question belong to each workspace. Workspace/source IDs, retained
PDFs, handoffs and previews are saved automatically. The reader starts in the
background on a remembered local port; no second terminal or ID transcription is
needed. Existing adapter scripts are compatibility shims for packaged implementations.

RKS remains the evidence owner. The package pins RKS `b204e74` and APW `6e95aad`
through public Git dependency URLs; no PyPI upload/tag was created. APW accepts
an optional local ReadingWorkflow host through a supported create_viewer_server
factory and routes that retain its Host/Origin, JSON and request-size validation.
The browser shows explicitly selected quotes/comments and an import preview;
importing also generates a brief. Agent instructions use the same CLI and preserve
unreviewed status. There is no embedded model or fabricated human review.

Recovery uses atomic manifests, process-owned kernel locks, native RKS replay
semantics, source hashes, saved previews, current APW revision checks and stable
reader port ownership. Lost ingestion/session responses reuse the committed work.
A lost apply response safely replays. Changed annotations require a new preview;
replacing an imported revision also requires --accept-updates. Missing saved
databases and corrupt PDF snapshots fail without recreating/substituting them.
Old import artifacts and briefs remain on disk. Workspace moves are explicitly
unsupported in this first version; restore to the original absolute location.

The daemon owns and closes its log and all HTTP requests before its shutdown
acknowledgement. It runs from the interpreter directory so Windows does not retain
a current-directory handle on the review folder. A minimal instance identity
probe and authenticated stop operation remain usable even if a brief is missing.
No stored/recycled PID is used to terminate a process.

Local verification completed: eight real workflow/recovery integration tests on
Windows and from installed Linux wheels; the final Windows wheel installed its
exact public dependencies into a fresh environment and passed all eight tests.
Existing adapter tests passed 44 cases. APW passed 119 backend tests (five optional
or Unix-specific skips locally), 50 frontend unit tests, type/lint/format checks,
and all 37 standalone browser cases. The real guided browser journey created a
PDF highlight, selected/previewed/imported it, downloaded the brief, followed its
actual passage link and followed it again after stop/resume. Desktop and mobile
evidence controls were checked; screenshots inspected. Site tests passed six
cases (one opposite-platform skip); desktop/mobile discovery, copy, anchors,
print and manual links passed. Registry and skill validation passed.

Current hosted runs: APW `40532247227` completed successfully, including its
browser job. SI `40532915383` has
Windows/Linux installed-wheel tests (including Python 3.10), all legacy adapter
jobs, registry and the new browser journey green; native macOS is queued.
Do not report the whole SI run as passed until checking final status. The macOS
job ID is `122290298795`; it has not been assigned a runner yet. The website's
native macOS manual walkthrough job passed; that is distinct from this package test.
Live desktop/mobile checks of the published quick start passed homepage discovery,
command copying, agent-section navigation, print styles and manual-guide links.
All three changed repositories are clean and synchronized with origin/main.

Ignored verification artifacts: SI `.workflow-test/browser-final/` contains the
real browser receipt/screenshots/downloaded brief; `.workflow-test/installed/`
is a clean Windows wheel/public-dependency installation; `.workflow-test/linux-env/`
is the WSL installed-wheel test environment. Site `.preview/verify_guided_site.mjs`
and `.preview/check_guided_site.py` own preview-browser checks; their preview
receipt/screenshots are retained. All temporary readers were stopped by owners.

Independent scientific review and researcher usability pilots remain separate
acceptance work. This implementation validates workflow mechanics, not scientific
answer accuracy. Do not start another phase automatically.

## Earlier checkpoint: Linux/macOS walkthrough and native platform validation

The user requested a Linux/macOS version alongside the published Windows guide.
The source pages are now committed, pushed and live:

- `https://scientifictooling.org/guides/rks-apw/`: operating-system chooser.
- `https://scientifictooling.org/guides/rks-apw-linux-macos/`: Bash/zsh walkthrough.
- The existing Windows URL is retained, with links between platform versions.

Both guides are Markdown sources in `Scientific-Tooling.github.io/guides/`;
`scripts/render_guide.py` generates both pages and the chooser from a shared
template. The homepage Walkthroughs navigation/main action now targets the
chooser, and RKS/APW project cards link directly to each platform. The Unix guide
uses Python for JSON, quoted paths, actual paper/annotation IDs, isolated venv
installation, explicit preview/apply, a source-linked brief, replay and backup.
It includes matching venv prerequisites and optional SSH loopback forwarding.

Current published source commits:

- RKS `b204e74`: Linux/macOS README link; required 120-case maintenance test passed.
- SI `fca7b8c`: Unix workflow entry point and README/default-workflow links.
- APW `2888ed4`: fix Unix SIGTERM deadlock; shutdown runs off the serving thread.
- APW `a435c2f`: local viewer binding no longer performs reverse DNS.
- Website `898ede2`: guide/chooser/shared rendering/native Unix CI.
- Website diagnostics `cfc3993` and `65e7232` exposed native startup logs/stacks.
- Website `b83c659`: fixed APW prerequisites, explicit loopback host/port and normal
  uninstrumented native startup verification.
- Website `2569ca1`: run both required Mac shell workflows on one native runner
  to avoid a second runner allocation while retaining Bash and zsh coverage.

The full documented Unix command sequence passed in Bash from fresh public HTTPS
clones on Linux with Python 3.12.16. Installation and PDF paths included spaces
and Unicode. The test supplies a single explicitly unreviewed annotation through
APW's HTTP API, then executes the actual preview/import/brief/replay commands and
resolves the actual generated citation. One item was added; replay added zero and
reported one unchanged item. A separate Chromium check opened the Linux-generated
brief URL against the native Linux viewer and selected the correct PDF passage.
The test leaves its data/logs/receipts under ignored `.preview/unix-*/` folders.

Native validation exposed two real APW issues, both reproduced before fixes:

1. SIGTERM called `server.shutdown()` on the thread running `serve_forever()`,
   causing a deadlock. A bounded Unix subprocess regression failed before the
   fix and passed with shutdown scheduled in a separate thread.
2. On native macOS, HTTPServer.server_bind blocked in socket.getfqdn(127.0.0.1)
   before listening. Captured Python/native process traces identified the call;
   proxy diagnostics ruled out a proxy issue. `_ViewerHTTPServer` now uses
   TCPServer binding and records the bound address/port without reverse DNS.
   The regression deliberately makes getfqdn unavailable; the real main startup
   still succeeds. Viewer integration tests use the same server implementation.

APW's final 118-case backend suites passed on Windows (one Unix-only skip) and
Linux (four optional MCP skips locally); full Ruff passed. Six site tests passed
on Windows/Linux with the opposite platform's native syntax check skipped.
Desktop/mobile preview checks passed chooser navigation, both platform switches,
both sets of copy buttons, anchors, print styles and page overflow checks.

Final Pages run 40524589809 at `2569ca1` succeeded: all four static matrix jobs,
the Ubuntu Bash workflow, both Bash and zsh workflows on a native macOS runner,
and deployment passed. The website gate requires all six validation jobs. Live
desktop/mobile Chromium checks passed homepage-to-chooser navigation, the Unix
page, switching back to Windows, both copy controls, fragment links, print styles
and no horizontal page overflow. RKS run 40519308187, APW run 40522430361 and SI
run 40519299216 also completed successfully at their current published heads.
The native smoke harness now uses ordinary documented startup; temporary
sitecustomize/faulthandler injection used for diagnosis has been removed.

All prerequisite changes were pushed before the website verification so source
clones can obtain them. No system Python packages, tags, PyPI releases, PRs or
external messages were created. A workspace-local uv/Python test runtime exists
under `.preview/`; uv is not a walkthrough dependency. The original hung owned
Linux test viewer was identified by its command line and stopped with SIGINT.

## Earlier checkpoint: published Windows walkthrough

The user requested a concise RKS/APW walkthrough and a dedicated page discoverable
on the Scientific Tooling website. It is now live:

https://scientifictooling.org/guides/rks-apw-windows/

The homepage has a Walkthrough navigation link, a primary PDF-to-brief action,
and links from the RKS/APW project cards; the sitemap includes the guide. Its
canonical Markdown source is
`Scientific-Tooling.github.io/guides/rks-apw-windows.md`; generate its HTML using
`python scripts/render_guide.py`. `--check` rejects stale output. The Markdown
and generated page retain exactly the same eight PowerShell blocks. CI gates
Pages deployment on source/page/link/syntax checks across Windows/Ubuntu and
Python 3.10/3.12. The build renderer is pinned to Markdown 3.10.3 to support 3.10.

Published commits, including the earlier workflow feature commits they require:

- RKS `06f8c1e`: README walkthrough entry point (feature minimum `6fc5c61`).
- APW `c40098d`: README walkthrough entry point (feature minimum `7715497`).
- Structured Intelligence `b986cb3`: concise workflow entry point and corrected
  README/default workflow links (feature minimum `2993fc6`).
- Website `707cfa6`: Markdown/HTML walkthrough, responsive design, copy/print,
  homepage discovery, sitemap and validation-gated Pages workflow.
- Structured Intelligence `58c724b`: CI failure tracebacks exposed in public
  annotations, preserving the exact research suite and its failing exit code.
- Structured Intelligence `db26735`: bound traceback annotations to GitHub's
  display limit so the failure tail remains inspectable.
- Structured Intelligence `a673678`: compare canonical absolute PDF paths when
  reusing sessions; normalize the pagination test's mock path; regression cases
  for equivalent absolute spellings and rejection of relative session paths.

All four repositories were pushed to public main, source repositories first so
the guide's HTTPS clone URLs expose the required features. No tags, PyPI releases,
PRs or external messages were created. The earlier handoff's statements about
unpushed commits are historical; do not repeat those pushes as unfinished work.

The walkthrough was executed in fresh local source clones and Python 3.12
environments in both Windows PowerShell 5.1 and PowerShell 7. Installation and PDF
paths contained spaces and Unicode. The real browser created a highlight; the
selected preview/import generated a brief whose actual link reopened the intended
passage. First import added one item; replay added zero and returned one unchanged
item. This validates editable source installation, not a wheel release. Original
PDF content was a generated engineering fixture, not scientific validation.

Local page checks: five passed on Windows, four on Ubuntu 3.10 with the Windows-
only syntax check skipped. Full RKS unittest maintenance check passed 120 cases;
44 research/native CLI integration tests and registry validation also passed;
the final path-identity fix expanded this to 46 passing cases on Windows/Ubuntu.
Live desktop/mobile Chromium checks passed homepage discovery, navigation, copy
fidelity (with normal Windows clipboard newline normalization), fragment links,
print styles and no horizontal page overflow. A clipped mobile navigation was
corrected before publication. Transient test servers were stopped by their owning
helpers. Artifacts, screenshots, logs and two fresh environments remain ignored
under `Scientific-Tooling.github.io/.preview/`; `.site-venv/` is its docs build env.

Hosted Pages run 40511029211 succeeded, including all four validation matrix jobs
and deployment. RKS run 40510937744 passed all six OS/Python test jobs and its
package check; APW run 40510950062 passed frontend, all six backend/MCP jobs and
Playwright E2E. Initial SI run 40510966394 failed a Windows adapter-test job while
Linux jobs passed. Local normal/default-encoding and clean-checkout reproductions
passed. Diagnostic annotations identified the pagination reuse fixture: its raw
temporary path did not match the adapter's canonical path on hosted Windows.
The fixture now mirrors the canonical source contract, and the adapter also
recognizes equivalent absolute snapshot spellings. A portable regression failed
before the adapter change and passed afterwards; different PDFs and relative paths
remain separate. Final run 40513201720 at `a673678` passed the registry job and
all four Windows/Ubuntu, Python 3.10/3.12 adapter jobs. The public
log-download endpoint requires authentication, so annotations were added for
inspectable tracebacks instead of guessing at an encoding or cleanup workaround.

Independent domain review, newly held-out scientific cases, one numerical analysis
workflow, installed APW wheel checks and hosted cross-repository CLI integration
remain acceptance work. No human scientific review was created by this slice.

## Earlier checkpoint: ranked term retrieval and frozen-question comparison

After the user asked how to resolve the testing problems, the shared RKS search
implementation was corrected and committed. Current local commits:

- RKS `6fc5c61`: shared BM25 term ranking across papers, claims, concepts, methods
  and datasets; explicit literal `--mode phrase`; identical CLI/HTTP behavior;
  versioned method/parameter metadata; linked concept names/aliases; meaningful
  regression tests and `docs/search.md`.
- Structured Intelligence `2993fc6`: native harness rejects changed/missing search
  identities and changed BM25 parameters; ranked-term/phrase/hash methods recorded
  separately; new `ranked-term-results.json` and updated findings/docs.

RKS ranked-term retrieval now finds a draft relevant passage first and within the
top five for 17/18 answerable questions, compared with 0/18 in the original whole-
query lexical baseline. The fixed standalone BM25 and local-hash per-question
rankings are unchanged; hash remains 9/18 top-five. Explicit phrase mode remains
0/18 for these whole-question inputs by design. The q02 target appears ninth;
do not fix it with a corpus-specific rewrite or alter relevance labels after
seeing results. No method parameters were tuned after the rerun.

The source/question revisions, original `baseline-results.json`, candidate labels
and pending review packet are unchanged. Independent review remains necessary,
scientific/abstention accuracy remains null, and the public reserved set is not
blind validation. Fresh raw responses and a disposable native workspace are
retained under `structured-intelligence/.research-eval/ranked-terms-v1/`.

Verification: 155 RKS pytest tests and 26 subtests passed on Windows; the full
repository-required RKS unittest suite passed 120 tests on Windows and Ubuntu;
all 44 research/adapter/native CLI integration tests passed on both systems.
Sources were reverified before the benchmark. Corpus/registry validation, CLI
help, recorded runner/scorer fingerprints and Git whitespace checks passed.
No APW code changed or browser journeys repeated in this slice. No packages were
installed, no expert reviews fabricated, and no pushes/PRs/deployments performed.

The portable ranker scans live records per query; it requires no derived-index
rebuild or schema migration, but large-corpus latency has not been qualified.
Read `research-knowledge-substrate/docs/search.md` before changing its contract.
Next work: obtain independent domain review and independently authored/newly
held-out questions; then measure any semantic improvement under a new method
identity. Hosted CI, installed-wheel smoke tests and researcher pilots remain.

## Earlier checkpoint: scientific corpus and retrieval evaluation

The user selected **single-cell RNA-seq methods** when asked about scientific
focus. Structured Intelligence commit `f0ae3d2` adds the corpus, evaluation tools,
results, review template, workflow documentation, and offline corpus CI validation.
RKS and APW code were unchanged during this slice.

Read these before continuing:

- `structured-intelligence/evaluations/scrna-methods-v1/README.md`
- `structured-intelligence/evaluations/scrna-methods-v1/RESULTS.md`
- `structured-intelligence/workflows/research/scientific-evaluation.md`

The corpus contains ten distinct DOI/PMCID papers, 23 text/table excerpts, one
derived whitespace duplicate, and 20 draft questions. All article-specific CC BY
4.0 notices, source fingerprints, title/author attribution, and excerpt transforms
were checked against retrieved original JATS and publisher PDFs. Full PDFs are
cached locally rather than committed; source text/table excerpts retain their
license and attribution. Corpus revision:
`1914a020d82932ebb8b38deb4fec326ea44aa825237d55a4ccfdc35d4a394112`.

Questions were frozen before the first baseline: 14 development and six public
reserved questions, grouped by paper. Eighteen have draft relevance targets;
two are insufficient-context probes. The split is public and agent-authored,
not blind/sealed or independently validated. No thresholds or rankers were tuned
after observing scores. All 20 questions remain pending independent domain review.
Do not label the agent-drafted answers or relevance lists an expert gold standard.

| Retrieval method | Relevant passage first | Relevant passage in top five |
| --- | --- | --- |
| Fixed BM25 passage baseline | 17/18 | 17/18 |
| Native RKS lexical interface | 0/18 | 0/18 |
| Native RKS local-hash-v1 | 5/18 | 9/18 |

These are draft passage-relevance scores, not scientific answer accuracy. Native
RKS receives verbatim questions and keeps its global top-ten cap across papers,
claims, and concepts; BM25 ranks passages directly. This interface difference is
disclosed in the results. Duplicates are collapsed before scoring; unanswerable
probes are not scored as retrieval failures. Scientific/abstention accuracy stays
`null`. See `baseline-results.json` for raw per-question rankings and provenance.

The concrete lexical limitation is in
`research-knowledge-substrate/src/rks/storage/claim_repository.py:search_claims`:
it matches `LIKE '%<entire query>%'`. Full natural-language questions consequently
miss passages containing their individual terms. The next engineering task is
explicit ranked term retrieval in the shared search layer, preserving a clear
phrase-search mode and versioned behavior. Do not add a silent adapter fallback,
tune around these questions, or claim the BM25 score establishes scientific
superiority. Compare any new implementation to the retained baseline and obtain
independently reviewed/newly held-out questions for generalization claims.

Three original-PDF journeys (Vieth, Zimmerman, Squair) passed reading, explicit
unreviewed annotation, selected export, dry-run/native import, replay, brief
generation, and actual Chromium page/quote navigation. The complete journey was
repeated: all three first imports and same-bundle replays were unchanged, with
annotation timestamps preserved. Screenshots were visually inspected; Lause's
runtime table was checked on original PDF page 10. These are engineering/source
checks, not qualified scientific review. Portable receipts are in
`journey-validation.json`.

Validation:

- 43 research tests passed on Windows (14.00 seconds) and Ubuntu (13.93 seconds),
  including the existing real cross-repository CLI tests.
- All ten PDF/JATS fingerprints, 23 source excerpts, attributions and license
  records verified. Corpus JSON and frozen-reference validation passed.
- Python Ruff, JavaScript syntax, registry validation, CI YAML parse, local
  documentation links, and Git whitespace checks passed.
- All three original-PDF browser cases passed in both complete-journey runs.

Useful retained local artifacts (ignored by Git):

- `structured-intelligence/.research-eval/sources/`: all original PDFs/JATS plus
  one-time source inspection metadata.
- `.research-eval/baseline-v1/native-rankings.json` and `native-responses.json`:
  full native benchmark and source-ID maps.
- `.research-eval/baseline-v1/rks/`: disposable RKS evaluation workspace with
  prepared excerpts explicitly stored as extracted, evaluation-only records.
- `.research-eval/viewer-v1/events.db` and `pdfs/`: APW annotations and retained
  original-PDF snapshots.
- `.research-eval/scientific-journey-v1/` and `scientific-journey-replay-v1/`:
  original handoffs, bundles/plans, briefs, receipts, browser results/screenshots.

No viewer was left running. No pushes, PRs, or deployments occurred. No reviewer
was contacted or assigned; no actual human review or researcher pilot occurred.
The pending review template requires actual human method/name/time/notes and
rejects stale source/question revisions. Representative-corpus expansion, an
independent question set, scientific review/pilot, full Linux backend suites,
installed-wheel checks, and hosted cross-repository CI remain acceptance work.

## Earlier checkpoint: passage navigation and source-linked briefs

The user explicitly requested committing the evidence-import changes and starting
the next slice. Both checkpoints are now committed on local `main`:

| Repository | Commit | Checkpoint |
| --- | --- | --- |
| RKS | `b5aac77` | Native transactional selected-evidence import |
| APW | `f69a042` | Selected evidence export and review provenance |
| Structured Intelligence | `10ad1fe` | Export/dry-run preparation adapter |
| APW | `7715497` | Exact source-passage navigation and selection ownership |
| Structured Intelligence | `b74e12d` | Source-linked reading brief generator |

APW now supports read-only `resolve-passage` and `GET /api/passage`. Citation URLs
bind session ID, document SHA-256, annotation ID, page, and the SHA-256 of the
recorded passage (`annotation_id`, `page`, `quote`, `anchor`, `rects`). The viewer
checks the live passage revision and consumes the exact PDF bytes verified by
the PDF endpoint. It rejects changed/deleted anchors, missing/ambiguous quotes,
and pages outside the PDF. Saved reading progress cannot override a citation page.
A closed session's citation starts another reading session for the same paper,
source revision, and annotation. A reader can reload a citation URL.

`structured-intelligence/scripts/research_brief.py` reads imported evidence through
the RKS CLI, checks APW passages and retained PDF bytes, and writes a new Markdown
brief. It preserves reviewed/unreviewed status and original interpretations;
it does not synthesize or promote scientific claims. Unavailable passages retain
their imported quote and an actionable error in place of an active link.

Read:

- `agent-pdf-workbench/docs/passage-navigation.md`
- `structured-intelligence/workflows/research/source-linked-brief.md`

Root causes found and fixed during real browser validation:

- Windows MIME associations labelled the `.mjs` PDF worker as plain text; module
  assets now have explicit JavaScript response types.
- Windows checkout line endings conflicted with Prettier and generated HTML;
  APW now has an LF `.gitattributes` rule. Canonically unchanged files were not
  included as unrelated content changes.
- PDF structure tags contributed phantom spaces to cached text and shifted
  annotation offsets; only text items now contribute to that text.
- Anchor resolution accepted stale ranges and ambiguous repeated quotes; it now
  requires matching ranges or an unambiguous contextual quote.
- An annotation save cleared newer selections after awaiting telemetry. A delayed
  browser response reproduced the failure. Cleanup now owns only its captured
  selection, occurs after persistence, and does not touch another active session.
- Expected browser disconnects now include Windows `ConnectionAbortedError`;
  unrelated I/O failures still propagate.

Validation for this committed checkpoint:

| Check | Result |
| --- | --- |
| Full Chromium browser suite | 37 passed, including five citation scenarios and the delayed-telemetry regression |
| Frontend unit tests | 50 passed |
| Frontend TypeScript, ESLint, complete Prettier check, Vite production build | Passed; built viewer assets committed |
| Full Windows APW backend suite before final disconnect unit case | 115 passed, 63.42 seconds |
| Final focused passage/API/disconnect regressions | Ten passed on Windows |
| Passage/API regressions on Ubuntu | Nine passed |
| Complete adapter/CLI integration suite | 23 passed on Windows and Ubuntu, including import-to-brief-to-resolved-citation and retained evidence after deletion |
| Python Ruff, registry validator, Git whitespace checks | Passed |

The complete final browser log is retained locally at
`agent-pdf-workbench/.apw/phase2-browser-tests.log` (ignored by Git). Locked frontend
dependencies and the matching Chromium runtime were installed for these checks.
No server was intentionally left running. No pushes, PRs, or deployments were
performed. RKS has no changes after its evidence-import commit; the other two
repositories remain untouched.

The generated one-/two-page PDF fixtures establish engineering behavior, not a
representative scientific corpus. Remaining work includes a rights-cleared
scientific corpus and bounded research questions, actual scientific review and
researcher pilot, full Linux backend suites, installed-wheel smoke checks, and
hosted cross-repository CI using published compatible commits.

## Earlier checkpoint: selected evidence import

The October 26 continuation added:

- APW `export-evidence`: selected annotations/notes, one read-only database
  snapshot, verified PDF hash, linked passages, content revisions, and explicit
  review manifests. Exported material defaults to unreviewed; no reviewer is
  inferred from a session. Missing selected/linked objects and inconsistent
  quote/anchor data fail explicitly.
- RKS `note import-evidence`: read-only dry-run by default, exact saved-plan
  requirement for apply, one `BEGIN IMMEDIATE` transaction, database uniqueness,
  replay protection, immutable revision history, and explicit `--accept-updates`.
  Concurrent changes invalidate a plan. One unresolved conflict blocks the batch.
- RKS migration `0014_external_evidence.sql` in both source and package trees;
  evidence tables included in graph/workspace backups; paper merge redirects;
  `note evidence <paper-id>` for current records and history.
- Structured Intelligence `scripts/research_evidence.py`: prepares an export and
  dry-run plan using public CLIs. It never applies evidence. Adapter CI now covers
  both research adapters.

Read these before editing the new boundary:

- `research-knowledge-substrate/docs/evidence-import.md` (contract and transactions)
- `agent-pdf-workbench/docs/evidence-export.md` (selection and review manifest)
- `structured-intelligence/workflows/research/evidence-import.md` (complete usage)

External identity includes caller-managed RKS/APW workspace names, original paper
ID, document SHA-256, item kind, and item ID. The first successful import binds
the RKS database to its workspace name. Names are not a global identity registry.
Human review metadata is an explicit caller assertion, not an authenticated
signature. The synthetic test review is not an actual scientific review.

Edits require acceptance of a fresh plan; deleted/omitted APW objects never delete
RKS evidence. New or edited imports must match the current paper PDF. Exact
historical replay works against its verified retained snapshot. Paper merges
after migration 0014 preserve redirects; older merges without recorded mappings
fail explicitly when their original paper ID is missing. No passage-level viewer
navigation has been implemented yet.

Validation from this continuation:

| Check | Result |
| --- | --- |
| Full Windows RKS suite before two final added cases | 143 tests and 17 subtests passed, 63.83 seconds |
| Final Windows RKS import module, including the two added cases | 14 tests and 2 subtests passed, 3.39 seconds |
| Full Windows APW backend suite before final export validation tightening | 105 tests passed with MCP installed, 71.83 seconds |
| Final APW export module | Seven tests passed on Windows and Ubuntu |
| All Structured Intelligence adapter and real CLI integration tests | 17 passed on Windows (14.67 seconds) and Ubuntu (13.81 seconds) |
| Final RKS import module on Ubuntu | 14 passed, 2.55 seconds |
| RKS migration resilience on Ubuntu | Passed alongside the earlier 12 import tests |
| Registry validator, focused Ruff checks, Git whitespace checks | Passed |

The import tests include actual subprocess termination after partial writes,
exception rollback, identical/competing concurrent imports, stale plans, local
RKS edits, changed/corrupt PDF snapshots, document revision isolation, merge
redirects, backup restoration, migration parity, and read-only missing-workspace
behavior. Integration checks preserve evidence after APW deletion and distinguish
unreviewed material from an explicit synthetic review assertion.

This checkpoint originally left the evidence-import changes uncommitted; the
commits are recorded above. Browser navigation and a generated engineering journey
are now validated by the latest checkpoint. Full Linux backend suites, installed
wheel smoke checks, hosted CI, the scientific corpus demonstration, and actual
scientific review/pilot remain pending. Windows tests required escalation for
temporary-directory access; no application workaround was added.

## Earlier commits

All commits below are on local `main`. No push, PR, deployment, or new chat was
created. Verify status before further edits.

| Repository | Phase | Commit | Change |
| --- | --- | --- | --- |
| `research-knowledge-substrate` | 1 | `089eba5` | Correct claim evaluation, configuration diagnostics, test collection, and migration fixture lifecycle |
| `agent-pdf-workbench` | 1 | `e720a8e` | Close SQLite connections consistently, including failure and backup paths |
| `research-knowledge-substrate` | 2, first slice | `fc9aaab` | Read-only paper source fingerprints |
| `structured-intelligence` | 2, first slice | `12808f8` | Verified RKS-to-APW reading adapter, workflow, regression/integration tests, and CI dependency setup |

`cell-wonderland` and `Scientific-Tooling.github.io` were not changed. Their
priorities remain in the umbrella plan.

## Historical initial Phase 2 behavior

RKS now provides `rks papers source <paper_id>`. It opens the configured database
read-only, does not initialize or migrate it, and returns
`rks.paper-source.v1`: paper metadata plus absolute local PDF path, SHA-256, and
byte count. Missing sources, relative stored paths, and absent workspaces fail
explicitly. Source identification lives in
`research-knowledge-substrate/src/rks/operations/paper_source.py`; CLI wiring is
in `src/rks/cli/commands/papers.py`.

`structured-intelligence/scripts/research_reading.py` invokes the RKS and APW
CLIs with argument arrays, using separate Python environments if requested. It
verifies a persistent cached PDF copy before calling APW. APW receives a local
filesystem path, not a `file://` URI; its current PDF endpoint expects a path.

The reference is `rks:<workspace-id>:<paper-id>:sha256:<document-sha256>`.
`--workspace-id` is caller-managed and must uniquely name the RKS workspace
within the shared APW database. The current implementation does not provide a
global identity registry. A changed PDF gets a distinct paper reference and
retains the prior snapshot. Sequential repeated opens reuse an active session
with the same reference and snapshot path. Simultaneous first opens can create
more than one session under the same reference.

The result is `scientific-tooling.reading-handoff.v1`, containing source metadata,
snapshot identity, APW database/session/reference, and a viewer URL. It does not
launch the viewer. The viewer must use the same database and set `--pdf-root` to
the cache directory. The current URL opens the session, not an individual passage.
Keep the cache with APW backups and verify its hash again at evidence import.

Read the tracked usage and contract documentation:
[source-reading.md](../workflows/research/source-reading.md).

## Historical initial Phase 2 implementation sequence

Steps 1–4 below are implemented and committed. The generated engineering journey
is tested. Continue step 5 with a representative scientific corpus and real review;
do not describe fixture assertions as scientific validation.

1. Define a versioned, selected-evidence export/import contract with workspace
   identity, RKS paper ID, document SHA-256, APW annotation/note ID, page, quote
   and anchor, content revision, timestamps, and actual review provenance. Keep
   machine interpretation distinct from reviewed evidence. Include an explicit
   dry-run report showing proposed additions, unchanged items, and conflicts.
2. Add a native RKS transactional import operation with a unique external-source
   identity and recorded revision. Its present `note add paper` API creates an
   independent record and commits immediately. Checking note text in the adapter
   before adding is not race-safe or crash-safe and is not the right fix. Inspect
   `storage/note_repository.py`, `operations/_paper.py`, and `cli/commands/notes.py`.
   Keep CLI handlers thin. Synchronize source/package migrations and migration
   tests according to the repository's existing conventions.
3. Define edits, deleted annotations, changed PDFs, and merged paper IDs. Do not
   interpret absence from an export as permission to delete durable RKS evidence.
   Test replay, interrupted import, competing imports, and conflicting revisions
   against the database transaction boundaries.
4. Add source-passage navigation in APW and use it in a generated research brief.
   Relevant frontend entry point: `frontend/src/app/usePaperSession.ts`, which
   currently accepts session or document parameters. Validate page/annotation
   anchors against the exact source revision and make missing anchors actionable.
5. Demonstrate the full journey on a small redistributable corpus, then broaden
   evaluation. A qualified scientific reviewer and actual researcher pilot are
   later requirements, not results already established by these engineering tests.

Read `research-knowledge-substrate/docs/system-constraints.md` before changing
RKS. A known architectural issue outside this slice is that many existing read
commands use `_open_session`, which initializes/migrates the database. The new
source command deliberately uses the existing read-only connection helper.

## Earlier source-reading checks and limitations

| Check | Result |
| --- | --- |
| Full RKS suite, Windows Python 3.12.14, after Phase 2 source changes | 131 tests and 15 subtests passed, 49.93 seconds |
| Full APW suite, Windows, Phase 1 checkpoint (APW unchanged since) | 99 tests passed with MCP installed and no skips |
| Adapter unit tests plus real cross-repository CLI test, Windows | 11 tests passed, 5.93 seconds |
| Adapter unit tests, Ubuntu WSL Python 3.10 | 10 tests passed |
| Cross-repository CLI test, Ubuntu using local source trees | One test passed |
| New RKS source tests, Ubuntu using local source tree | Six tests passed |
| Structured Intelligence registry validator | Passed with PyYAML 6.0.3 installed in the local RKS test environment |
| New adapter code/tests Ruff check, CI YAML parse, staged whitespace checks | Passed |

The integration test generates a valid one-page PDF and exercises actual RKS
ingestion/source and APW open/list/export commands. It verifies sequential reuse,
revision isolation, retained source bytes, and namespace isolation. It does not
render the viewer or validate scientific claims. Hosted CI, browser rendering,
full Linux backend suites, and Linux installed-package checks remain pending.

The older Phase 1 logs are `phase-1-rks-tests.txt` and `phase-1-apw-tests.txt` in
the umbrella directory. Earlier `*-review-test-results.txt` files show the
pre-fix failures; they are historical evidence, not the current result.

Phase 1's heuristic extraction thresholds are fixture baselines only. Prepared
claim imports and real extraction are now tested separately; neither establishes
scientific release quality.

## Historical initial reproduction commands

Existing isolated Windows environments:

- RKS: `C:\Users\yangm11\github\research-knowledge-substrate\.venv\Scripts\python.exe`
- APW: `C:\Users\yangm11\github\agent-pdf-workbench\.venv\Scripts\python.exe`

From the RKS repository:

```powershell
& '.\.venv\Scripts\python.exe' -m pytest -q
```

From Structured Intelligence:

```powershell
$env:RKS_TEST_PYTHON = 'C:\Users\yangm11\github\research-knowledge-substrate\.venv\Scripts\python.exe'
$env:APW_TEST_PYTHON = 'C:\Users\yangm11\github\agent-pdf-workbench\.venv\Scripts\python.exe'
& $env:RKS_TEST_PYTHON -m unittest discover -s tests -v
& $env:RKS_TEST_PYTHON scripts\validate_registry_schema.py
```

The integration test explicitly skips if those two variables are absent. CI
currently runs adapter unit tests; arrange a cross-repository CI job using
compatible committed revisions after the relevant changes are published.

Ubuntu's standard-library-only integration runs without installing packages:

```powershell
wsl.exe -d Ubuntu-20.04 --cd /mnt/c/Users/yangm11/github/structured-intelligence env PYTHONPATH=/mnt/c/Users/yangm11/github/research-knowledge-substrate/src:/mnt/c/Users/yangm11/github/agent-pdf-workbench/src RKS_TEST_PYTHON=python3 APW_TEST_PYTHON=python3 python3 -m unittest discover -s tests -p test_reading_integration.py -v
```

Windows sandbox test attempts could not access their newly created temporary
directories. Rerunning with the normal escalation mechanism passed; do not add
cleanup retries or suppress file errors in application code for this environment
restriction. WSL also required escalation to access its service. Its warning
about translating `\\snowman\win-coremake\scripts\bin` did not prevent tests.

The installed Ubuntu lacks venv/ensurepip support. Avoid nested PowerShell-to-shell
variable expansion when preparing Linux environments; direct argument arrays or
a saved script are safer. No system packages were installed during this work.

## Suggested next-session prompt

> Continue Scientific Tooling development from the current checkpoint in
> `C:\Users\yangm11\github\phase-2-handoff.md`. Verify repository status and
> preserve existing uncommitted changes. Candidate `2026-10-29-c1` and its 23-row
> acceptance/failure matrix are frozen. Read the candidate baseline and
> `structured-intelligence/evaluations/imported-evidence-2026-10-29/results.md`.
> The imported-evidence fixture and source-linked review packet are implemented;
> use `run-installed-original/`, `run-installed-corrected/` and `review-final/`.
> The original-source result is 17/18 draft top-five hits. A separate correction
> completes the truncated q02 excerpt and reaches 18/18 without ranking or label
> changes. The 61-test adapter suite passes on Python 3.12 and 3.14. Preserve
> both source revisions, all receipts and the immutable candidate; do not restart
> this completed slice or use earlier checkout-import runs as installed evidence.
> Next implement the missing browser recovery cases and rerun all ten real pilot
> citation targets, following M03/P01 and the remaining reader gates. Application
> changes require a child candidate and affected checks. S02/Q02 remain pending
> actual independent review and at least ten newly authored held-out questions;
> the packet has 26 pending decisions and zero approvals. Keep Structured
> Intelligence orchestration, RKS durable evidence and APW source reading distinct.
> Fix root causes, retain source/revision identities and explicit failure outcomes,
> and keep public dependency/browser pins coordinated before release.
