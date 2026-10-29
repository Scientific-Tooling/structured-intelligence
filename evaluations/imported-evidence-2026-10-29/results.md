# Imported evidence fixture and review packet results

Implemented and exercised on October 29, 2026 against frozen candidate
**2026-10-29-c1**. The final [source-linked review packet](review-final/review.md)
contains 20 reference questions, 23 canonical source excerpts, six comparison
cells and ten unique PDF supporting passages. Its [response template](review-final/responses.json)
contains 26 pending decisions, zero approvals and zero new held-out questions.

## Measured retrieval

Both final runs imported 24 notes from ten verified papers through APW selection
and native RKS evidence import. Every note remains unreviewed commentary. The
20 verbatim questions were run through `Workspace.search` and the actual hosted
search handler, with full responses and import/replay receipts retained.

| Measure | Original source fixture | Corrected source fixture |
| --- | --- | --- |
| Answerable questions | 18 | 18 |
| Hit at 1 | 17/18 (94.44%) | 18/18 (100%) |
| Hit at 5 | 17/18 (94.44%) | 18/18 (100%) |
| Mean recall at 5 | 90.74% | 96.30% |
| Mean reciprocal rank at 10 | 0.95 | 1.00 |
| q02 expected passage native rank | 10 | 1 |
| Independent reviews / new held-out questions | 0 / 0 | 0 / 0 |

Full evidence: [original results](run-installed-original/results.json),
[corrected results](run-installed-corrected/results.json),
[original native responses](run-installed-original/native-responses.json),
[corrected native responses](run-installed-corrected/native-responses.json), and
[corrected import/replay receipts](run-installed-corrected/imports.json).

These are engineering measurements against agent-drafted targets. They do not
establish precision or scientific accuracy. Hit at 5 exceeds the frozen 90%
numerical threshold on both runs, but **S02 remains blocked** on independent
labels and at least ten new reviewer-authored questions. Public reserved
questions are not blind holdouts. The two insufficient-evidence probes remain
visible and outside answerable-query denominators; abstention was not scored.
Query times include CLI startup and do not qualify the 10,000-record latency gate.

## Root causes and retained corrections

**Truncated reference passage.** The original q02 source slice ended at character
767, before the sentences about increasing asymmetry and the named normalization
methods that its draft answer expected. The new [corpus revision](corpus-source-complete/corpus.json)
extends that slice to character 1,052, through complete comparison sentences in
the same pinned paragraph. [The correction record](corpus-source-complete/change.json)
retains both excerpts, selectors, offsets and hashes. Source XML/PDF bytes,
question wording, relevance target IDs, all other excerpts and ranking code are
unchanged. The original corpus and run remain intact. This is a disclosed source
correction after observing a miss, not an independent test; domain review remains
pending. No spelling, synonym or ranking fallback was introduced.

**Native result cutoff.** Duplicate collapse must happen inside the first five
native result slots, not before taking five. The evaluator now retains raw
rankings and prevents a duplicate from promoting the sixth native result into
the top five. A regression fixes this boundary and checks reciprocal rank against
native positions. The original exploratory artifacts remain retained.

**Installed-package provenance.** A legacy compatibility helper inserted the
checkout's `src` directory into the import path. Earlier source hashes matched
the frozen candidate, but metadata came from stale checkout egg-info; those
records do not qualify as installed-package measurements. The corpus helper now
imports the packaged API directly. Source-only CI explicitly selects `src`.
The evaluator rejects editable packages, distributions outside the environment
and imported modules outside the selected distribution, then verifies every
candidate module file against the frozen manifest. Both final runs were repeated
in new projects, and the final packet was recaptured. Earlier artifacts were not
overwritten. Their misleading installed-version metadata remains visible.

The verified final environment contains sci `0.4.0.dev20261029`, APW
`0.3.2.dev20261029` and RKS `0.2.0`, with 16, 19 and 122 package files checked,
respectively. Each result records module locations, wheel origins and evaluator
source hashes; its `harness/` directory retains the exact evaluator/helper bytes.
Candidate manifest SHA-256 is
`20877448f6c844489adb9a9bf51fb6b48604933e5162a147bc7bf6aa3fde9ecc`.
Frozen application archives and sources [still verify](candidate-verification.json).

## Slice acceptance and failure matrix

| Check | Acceptance / explicit failure | Observed disposition |
| --- | --- | --- |
| Source fixture | 10 papers, 23 canonical excerpts plus 1 duplicate; exact source bytes and mapping; changed bytes/mapping fail before writes | PASS; source verification and tamper regressions |
| Native import | 24 selected notes; exact replay unchanged; no invented PDF anchors or review status | PASS on both final runs |
| Retrieval identity | No foreign workspace, source, note, revision or content; duplicate native identity and fabricated passage fail | PASS; native run plus negative regressions |
| Search scope | CLI/hosted handler same ranking; empty query, paper/review filters and foreign session have explicit outcomes | PASS; HTTP/browser transport is outside this slice |
| Read-only retrieval | Project manifest and both databases byte-identical across search | PASS on both final runs |
| Metric accounting | Native top-five slots before duplicate collapse; separate hit numerator/denominator and recall | PASS; cutoff and reciprocal-rank regressions |
| Installed identity | Loaded package location and all module bytes match the installed frozen candidate | PASS on final runs; earlier artifacts superseded |
| Source-linked packet | 20 questions, all canonical excerpts, 6 cells / 10 unique supports; exact revisions, PDF bytes, attribution and links | PASS; final packet captured from original pilot |
| Packet freshness | Changed live comparison/support produces outdated status; unavailable or inconsistent source fails | Current at [recorded check](review-final/check.json); backend freshness only |
| Review response | Every exact target retained; stale, missing, foreign or duplicate targets fail; completed decisions require human provenance | PASS validator regressions; actual 26 decisions pending |
| Independent scientific qualification | Actual domain decisions and >=10 new independently authored frozen questions | BLOCKED; no reviews or questions invented |

All **61 research adapter tests** pass on Python 3.14 and Python 3.12, including
17 new imported-evidence tests. The 3.12 run disables site packages and explicitly
selects checkout sources to verify the dependency-free CI mode. See
[3.14 test log](adapter-tests-final-installed.log),
[3.12 test log](adapter-tests-python312-stdlib.log) and [lint log](lint.log).
The existing CI test pattern includes the new suite. Hosted CI was not run here.

## Review and next development

Use [review-final/review.md](review-final/review.md) with a copy of
[responses.json](review-final/responses.json). Run `check-packet` before and after
review, and `review-status` against the unchanged sealed packet. Reviewer names
and independence are caller assertions, not authenticated identities; this tool
does not write scientific review into RKS or approve a release. Saved local reader
links require the original project and its reader; publisher/article links and
source fingerprints are also retained. Browser quote matching remains untested.

S01 has additional native-import/search evidence but broader fault/filter and
HTTP coverage remains open. S02 and Q02 now have concrete review inputs; their
human-dependent gates remain blocked. The next engineering work is the missing
browser failure cases and ten real pilot citation checks, followed by remaining
reader/performance/platform gates in the frozen acceptance matrix. No candidate
application code, dependency pin, release tag or original pilot state was changed.

The [artifact index](receipts.json) hashes retained evaluation files. Full local
disposable projects and command logs remain under the umbrella directory:
`.imported-evidence/c1-installed-original`, `c1-installed-corrected`, and
`installed-baseline.log`, `installed-corrected.log`, `installed-packet.log`.
