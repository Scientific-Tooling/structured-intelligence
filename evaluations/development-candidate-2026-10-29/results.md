# Candidate baseline results

**2026-10-29-c1 is frozen and locally testable; release remains blocked.** The
combined local wheels passed 111 Python tests, 103 reader tests, both existing
installed browser journeys, a 30-page scrolling smoke check, and a same-path
0.3.1 upgrade/restore exercise on Windows. No product defect was demonstrated by
these completed checks. Missing independent evaluation and release checks remain
failures to qualify, not successful tests.

## Verified candidate

The [installation receipt](receipts/installation.json) records Windows 11 build
26200, Python 3.14.10, module locations inside the new environment, wheel hashes,
reader asset identity and the packaged analysis skill hash. All three wheels were
built from the frozen source copies. The archive/file verification passed again
after the tests. Manifest SHA-256:
`20877448f6c844489adb9a9bf51fb6b48604933e5162a147bc7bf6aa3fde9ecc`.

| Component | Version | Wheel SHA-256 |
| --- | --- | --- |
| sci | 0.4.0.dev20261029 | `03567b270e91be9ef0b57daa2b413deed1580b993522fc648fdfe9cee931945d` |
| APW | 0.3.2.dev20261029 | `b3107c3834b002c6ceaec27b79540d4ee77dd867fb08b1afb3d9f273baf61f18` |
| RKS | 0.2.0 | `4da2e23a4654c81880ca87d3ba6cb546e36e25cb2a15582d7f7a598c7570a992` |

This installation used the coordinated local wheels with `--no-deps`. It does
not validate the current old public APW pin. Frontend checks used the frozen
source with the existing checkout's dependency directory; a clean frontend
dependency install and rebuilt-asset parity remain release checks.

## Executed checks

| Check | Result | Evidence |
| --- | --- | --- |
| Installed workflow and recovery | 19 passed | [log](receipts/workflow.log) |
| Discovery and selection | 12 passed | [log](receipts/discovery.log) |
| Atomic state publication | 4 passed | [log](receipts/state.log) |
| Freshness and retained editions | 21 passed | [log](receipts/maintenance.log) |
| Draft analysis handoffs | 9 passed | [log](receipts/analysis.log) |
| Research source/corpus/evidence adapters | 44 passed | [log](receipts/adapters.log) |
| Installed native boundaries | 2 passed | [log](receipts/boundary.log) |
| Reader unit tests | 103 passed in 18 files | [log](receipts/frontend-unit-verified.log) |
| TypeScript, ESLint and Prettier | Passed | [receipt](receipts/frontend-checks.json) |
| Installed two-paper workflow | Passed, zero page errors; desktop/mobile, source navigation after restart, scoped synthetic review, stale review after edit, export | [receipt](receipts/browser-workflow.json) |
| Installed discovery browser | Passed; explicit selection, lost-response replay, unavailable full text, source navigation and desktop/mobile | [receipt](receipts/browser-discovery.json) |
| 30-page continuous reader | Passed for fit-width scrolling and paper switch; 8 recorded page visits, maximum 3 active rasters / 10,956,960 canvas pixel bytes | [receipt](receipts/long-reader.json) |
| Legacy workspace upgrade | Passed; old brief text retained, explicit comparison migration, exact import replay still one evidence record | [receipt](receipts/upgrade-candidate.json) |
| Same-path backup restoration | Passed; complete original file inventory restored and old installation reopened its brief without changing those files | [receipt](receipts/upgrade-restore.json) |

The browser test includes retained history behavior, but its existing receipt
does not enumerate every history assertion. Do not infer failed-check or
lost-brief-response browser coverage from its broad pass. Synthetic review records
are solely test assertions. The long-reader result is a raster measurement at
fit width, not total browser memory, 100% zoom coverage or a scientific PDF pilot.

Desktop comparison and long-reader screenshots were visually inspected. Raw
screenshots, disposable projects, wheels, archives, logs and the stopped legacy
backup remain under `.development-candidate/2026-10-29-c1/` in the umbrella workspace.
The restored legacy project and the separately retained upgraded project both
have their owned reader stopped.

## Acceptance disposition

These statuses update the [frozen matrix](README.md#concrete-acceptance-and-failure-matrix).
`PARTIAL` and `NOT RUN` continue to block release. A pass covers the named
engineering case and does not supply an independent scientific judgment.

| Gate | Current disposition | Remaining evidence or next action | Owner |
| --- | --- | --- | --- |
| C01 | PASS local candidate identity | Repeat identity checks for each later distribution/platform | Release engineering |
| C02 | BLOCKED publication mismatch | Validate/publish immutable APW successor, coordinate metadata and browser pin, freeze successor and test ordinary install | Release engineering |
| S01 | PARTIAL | CLI/HTTP fixture scopes passed; run full native search acceptance and corpus import audit | RKS and sci |
| S02 | BLOCKED independent input | Prepare imported-evidence fixture; obtain actual reviewed 20-question labels and >=10 new reviewer-authored questions | RKS and domain reviewer |
| S03 | NOT RUN | Fixed 10,000-record / 100-query benchmark and raw cold/warm receipts | RKS and sci |
| P01 | NOT RUN | Recheck all 10 real pilot citations on this candidate, including deliberate failures | APW and sci |
| R01 | PARTIAL | Fit-width scrolling and paper switch passed; long-document annotation, search and zoom acceptance still needed | APW |
| R02 | PARTIAL | Fit-width raster bound passed; 100% zoom and repeatability measurement remain | APW |
| Q01 | PARTIAL | Installed review/retry/conflict/browser fixtures passed; full native history/concurrency audit remains | RKS and sci |
| Q02 | BLOCKED independent input | Actual domain review of 6 cells and 10 supporting passages | Domain reviewer |
| D01 | PARTIAL | Installed selection/recovery/browser fixtures passed; audit and add explicit timeout/rate-limit/acquisition interruption cases | sci and APW |
| D02 | NOT RUN | Broaden recorded live query/identifier/source cases and observe independent selection | sci and domain reviewer |
| M01 | PASS engineering fixtures | Keep independent real-project check open under H01 | sci |
| M02 | PASS engineering fixtures | Keep full browser fault cases open under M03 | sci |
| M03 | PARTIAL | Add failed freshness check and lost brief-publication response to installed browser journey | sci and APW |
| A01 | PARTIAL | 9 installed identity/recovery cases passed; rerun the valid H5AD demonstration with candidate identity | sci |
| A02 | PARTIAL | Selected/unselected scope and draft labels passed; guide-only independent inspection pending | sci and domain reviewer |
| U01 | PASS tested legacy fixture | Extend later to representative multi-paper/multi-edition upgrade set | Release engineering |
| U02 | PASS tested same-path restore | Retain original-path limitation; no portability claim | Release engineering |
| X01 | PARTIAL | Windows local checks passed; full RKS/APW suites, clean build assets, Linux/macOS/supported Python matrix and coordinated CI pending | Release engineering |
| H01 | BLOCKED independent input | Three actual researcher sessions, including one domain reviewer | Research coordinator |
| G01 | PARTIAL | Candidate record and handoff updated; final guide/release/upgrade sweep follows qualified release | Documentation owner |
| N01 | DEFERRED nonblocking | Recurrence, portability and analysis execution stay outside this delivery | Product owner |

## Observed failures and corrections

- **Publication mismatch is unresolved:** APW's local continuous renderer is not
  in sci's pinned public commit. Both current pins agree with one another, but
  they do not identify this candidate. No release or publication was performed.
- **Protocol correction retained:** revision 1 counted mounted page canvases.
  Source inspection showed zero-sized placeholders are intentionally retained for
  geometry. [Revision 2](protocol-v2.json), written before reader measurement,
  counts allocated rasters, reports placeholders separately and fixes viewport/
  zoom conditions. No failing product result was hidden by this change.
- **Upgrade fixture v1 was incomplete:** direct legacy `Workspace.apply()` does
  not create a brief. The first harness assumed a brief existed and failed with
  `TypeError` on `None`. It did not demonstrate data loss. The original project,
  backup and failure log remain. The corrected fixture explicitly creates a legacy
  brief before backup in a new `upgrade-v2` directory, then passes upgrade/restore.
- **Environment setup restrictions:** initial Python temporary-directory access
  and the frontend runner's child-process launch were denied. The same builds and
  checks passed with normal process/temp access. No application retry or fallback
  was added. Initial diagnostics remain in the local artifact directory.

No candidate application code changed after freezing. Version fields, the freeze
utility, evaluation harnesses and records are the new work in this session; all
pre-existing implementation changes and the user's staged settings removal were
preserved. Branch history and dependency pins remain unchanged.

## Continue from this checkpoint

The **imported-evidence acceptance fixture and source-linked review packet** are
now [implemented and measured](../imported-evidence-2026-10-29/results.md).
That follow-up retains its original-source and corrected-source runs separately,
and leaves scientific gates S02/Q02 pending actual independent input. The table
above is the original baseline disposition; the linked follow-up records the
additional evidence without rewriting these receipts.

Next are missing browser failure cases and the remaining citation/reader checks.
Preserve this candidate and all receipts. A
measured application correction must create a child candidate and rerun affected
gates. Human-dependent rows stay pending until actual reviews/sessions exist.

Reproduction entry points: [baseline runner](run_baseline.py),
[same-path upgrade check](check_upgrade.py), and [long-reader check](check_long_reader.mjs).
The baseline runner refuses to replace an existing check directory. To repeat a
run, retain its current outputs and use a fresh candidate/run directory. Individual
commands, working directories and log hashes are in [command receipts](receipts/results.json).
The [receipt index](receipts/index.json) hashes the retained report inputs.
