# November 2 engineering acceptance

**The requested M03, P01, R01/R02 and S03 cases pass locally.** Testing found and
fixed one APW defect: a citation to a nonexistent page cleared a valid PDF and
hid its saved quotations. Candidate **2026-11-02-c2** retains that failure;
**2026-11-02-c3** contains the correction and passed the affected checks.

This is Windows/Chromium engineering acceptance, not a public release or an
independent scientific review. At this checkpoint the APW fix was unpublished
and public sci pinned APW `4c3a379...`. The subsequent
[publication verification](../publication-2026-11-02/README.md) records publication
at `d800a777...` and coordinated sci pins. Frozen receipts below retain their
original pre-publication status and dependency metadata.

## Results

| Gate | Result | Evidence and limits |
| --- | --- | --- |
| M03 browser recovery | PASS | Failed checks remove an earlier current label; a lost response after a committed brief retries the identical request without another edition; interrupted generation resumes after restart; old retries preserve the latest edition; a delayed previous-paper response cannot overwrite newer state. Earlier edition hashes remain unchanged. |
| P01 real citation targets | PASS | All ten original pilot quotations open on the correct retained PDF/page with visible selected highlights, both initially and after restart: 20 successful visits. Changed/missing PDF bytes, edited/deleted anchors, inconsistent citation fields, unmatched/ambiguous quotes and out-of-range pages reject explicitly. Readable sources retain their quotations after quote/page rejection. |
| R01 long reader | PASS | A 30-page PDF is traversed forward and backward at fit width and 100%: 120 page visits. Search visits all 30 matches, wraps both ways and finds a unique page; direct page jumps, saved highlights on pages 2/15/29, zoom, paper switching and reopening preserve the correct state. |
| R02 raster retention | PASS | At 1440×1000, maximum 3 active rasters at fit width and 4 at 100%, below the frozen ceiling of 7. Peak canvas pixel allocation is 10,956,960 bytes. No prior-document text/raster pages remain after switching to the one-page paper. Browser heap readings are coarse and do not establish a total-memory bound. |
| S03 10,000-record search | PASS, inherited unchanged RKS | 100 warm native queries after 10 explicit warmups: p95 **1.4515 s**, median **1.3806 s**, maximum **1.5043 s**. Threshold: p95 ≤2 s. First query in a fresh process: **1.4293 s**; OS disk caches were not purged. Five separate CLI timings including process startup: **1.6823–1.7509 s**. Database SHA-256 is unchanged. |

The four final browser runs contain **41 passing checks and zero page errors**.
See [machine-readable results](results.json), [raw receipts](receipts/), and the
[receipt hash inventory](receipts.json). Original thresholds are in
[protocol.json](protocol.json); [the child protocol](protocol-c3.json) records
the correction and required reruns without relaxing a threshold.

## Defect and correction

APW validated a citation's page number inside `loadPdf`. That error propagated
through the session's failed-document-load rollback, clearing the reader before
saved annotations were loaded. A valid document with an invalid citation target
was therefore treated like an unreadable source.

Page-range validation now occurs in passage focusing, after verified PDF bytes
and annotations are loaded. The existing passage-error handling retains the
document, saved quotation and repair message, while refusing to select an invalid
target. PDF identity/hash verification still happens before rendering. The normal
reader position is bounded to the document; it is never reported as a resolved
citation to the invalid page.

Changes are in APW `frontend/src/app/App.tsx`, `usePdfReader.ts`, a focused reader
unit regression, the existing passage browser regression, and rebuilt `web/app.js`
and `web/sw.js`. No RKS or sci application code changed.

Validation: **104 frontend tests in 18 files**, TypeScript, ESLint, formatting and
the production build passed. All **five focused passage browser tests** passed.
The installed c3 browser runs then repeated recovery, all ten real targets,
long-reader behavior, source/anchor failures and delayed-response behavior.

## Candidate and installation identity

- c2 freezes the published development source baseline: sci `5118e7f...`,
  APW `4c3a379...`, RKS `44a8f33...`. Its application checks reuse retained c1
  wheels whose installed application files match c2 byte for byte. This is
  explicitly not a new c2 distribution/public-install qualification.
- c3 is a child with the APW correction. All three wheels were built from its
  frozen sources and installed in a new environment. Package metadata still names
  the published dependencies, so the combined local wheel install uses `--no-deps`;
  it does not claim an ordinary public sci install contains the correction.
- Every browser attempt verifies installed application files against its candidate
  manifest and retains module paths, distribution origins, interpreter identity,
  wheel hashes, protocol identity and harness identity. Original and child source
  archives verified again after testing. RKS's complete source tree is identical
  across c2 and c3, so the measured S03 result is inherited rather than remeasured.
- Package versions remain sci `0.4.0.dev20261029`, APW `0.3.2.dev20261029`, RKS
  `0.2.0`; candidate and content hashes distinguish the unpublished correction.

Hardware: Intel Core i5-9600, six cores/logical processors, approximately 32 GiB
RAM; Windows 11, Python 3.14.10, Chromium 151.0.7922.34. The search fixture contains
10,000 deterministic synthetic imported commentary notes across ten paper
identities. It measures native retrieval latency, including connection/read
transaction work, without mixing process startup into the native p95. It does
not measure ranking quality or scientific validity. The benchmark ran before
concurrent browser checks.

The ten citation targets are recreated through public sci commands in disposable
projects using the original pilot's exact PDF bytes, pages, quotations and comments.
New session/annotation IDs are mapped back to hashed original annotation receipts.
The original pilot and its review decisions are unchanged. Faults affect only
disposable copies, with source bytes and annotation content restored afterwards.

## Retained failures

| Attempt | Finding | Disposition |
| --- | --- | --- |
| c2 citations-01 | Public-install RKS files differed from frozen source by CRLF/LF bytes | Provenance preflight rejected that environment; used byte-matching retained wheels. |
| c2 citations-02 | Harness passed unsupported `--paper` to `sci apply` | Removed that argument; preview identity already binds the paper. |
| c2 benchmark-01 | Harness registered relative synthetic PDF paths | Used absolute paths, as required by the source contract. |
| c2 reader-01 | Harness counted the empty-state list item as an annotation | Counted saved annotation controls; the 120 raster measurements remain valid. |
| c2 citation-browser-01/02 | Error-message matcher omitted “different”; annotation API returns successful HTTP 201 | Corrected harness expectations without changing application behavior. |
| c2 edges-01 | Invalid citation page erased the readable document/quotation from the UI | **Product failure.** Preserved, corrected in c3, regression and installed reruns passed. |
| c3 edges-01 | Harness assumed page 1 after deliberately visiting an invalid target | Asserted restored page 30, then explicitly jumped to page 1 before the separate delayed-response case. |

Earlier outputs and harness versions are retained. No failed result was replaced
by a passing one. Browser subprocess creation required normal process access;
that environment restriction was not treated as a product failure.

## Reproduce and verify

From the umbrella workspace in PowerShell, use the retained installed child:

```powershell
$env:ACCEPTANCE_CANDIDATE = 'C:\Users\yangm11\github\.development-candidate\2026-11-02-c3'
$env:ACCEPTANCE_PYTHON = "$env:ACCEPTANCE_CANDIDATE\installed\Scripts\python.exe"
$checks = 'C:\Users\yangm11\github\structured-intelligence\evaluations\engineering-acceptance-2026-11-02'

# Every output path must be new; select fresh names for subsequent attempts.
node "$checks\browser.mjs" recovery "$env:ACCEPTANCE_CANDIDATE\repeat-recovery-01"
node "$checks\browser.mjs" reader "$env:ACCEPTANCE_CANDIDATE\repeat-reader-01"
node "$checks\browser.mjs" edges "$env:ACCEPTANCE_CANDIDATE\repeat-edges-01"
& $env:ACCEPTANCE_PYTHON "$checks\acceptance.py" citations "$env:ACCEPTANCE_CANDIDATE\repeat-citations-01"
node "$checks\browser.mjs" citations "$env:ACCEPTANCE_CANDIDATE\repeat-citation-browser-01" "$env:ACCEPTANCE_CANDIDATE\repeat-citations-01"

# Run latency measurements separately from browser/build workloads.
& $env:ACCEPTANCE_PYTHON "$checks\acceptance.py" benchmark "$env:ACCEPTANCE_CANDIDATE\repeat-benchmark-01"
& $env:ACCEPTANCE_PYTHON "$checks\acceptance.py" cli-measure "$env:ACCEPTANCE_CANDIDATE\repeat-cli-01" --fixture "$env:ACCEPTANCE_CANDIDATE\repeat-benchmark-01"

# Verify the retained report; --include-local also checks PDFs, DBs and screenshots.
& $env:ACCEPTANCE_PYTHON "$checks\retain_results.py" --verify --include-local
```

Large artifacts remain under `.development-candidate/2026-11-02-c2/` and
`.development-candidate/2026-11-02-c3/`, indexed in
[local-artifacts.json](local-artifacts.json). The tracked report includes raw
timings, candidate manifests, install provenance, successes, failures and harness
versions. Reproduction requires the retained pilot source PDFs and annotation
receipts; nothing is fetched or scientifically relabeled by these harnesses.

## Still open

Independent retrieval labels and held-out questions, domain comparison review,
researcher pilots, other acceptance rows, coordinated publication of the APW fix,
an ordinary public-dependency installation and supported-platform release checks
remain separate gates. This report does not mark the combined release complete.
