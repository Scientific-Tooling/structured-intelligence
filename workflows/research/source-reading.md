# Read an RKS paper in PDF Workbench

This is the first implemented slice of the integrated literature workflow. It
opens a source already ingested into Research Knowledge Substrate (RKS) in Agent
PDF Workbench (APW), preserving the PDF revision used for reading.

The adapter uses the public CLIs. RKS owns paper metadata and evidence; APW owns
reading sessions, annotations, and notes. The adapter does not query either
database directly. It reads RKS without initializing or migrating its database.
Opening a reading session writes a verified PDF copy and may create an APW
database/session. It prints a JSON handoff and a viewer link; it does not start a
server or open a browser.

## Prerequisites

- Python 3.12 or newer (3.14 recommended).
- RKS installed from a checkout containing `rks papers source`.
- APW installed, including its built viewer assets when using the viewer.
- An RKS workspace containing a paper with an accessible local PDF.
- RKS, APW, and the adapter running on the same host, with a persistent directory
  for source copies. A remote APW server will not resolve local paths correctly.

Use an explicit, stable `--workspace-id`, unique among the RKS workspaces sharing
an APW database. Keep that ID when moving the same RKS workspace. Use a new ID for
an independent workspace, even when its paper IDs start again at `p_000001`.
This ID is caller-managed; this first slice does not persist or enforce a global
workspace registry. Save the returned handoff with the research project.

## Run

From the Structured Intelligence checkout, with `rks` and `apw-dev` on PATH:

```bash
python scripts/research_reading.py p_000001 --workspace-id review-a --rks-data-dir /path/to/rks-data --apw-db /path/to/review/events.db --cache-dir /path/to/review/pdfs
```

For separate virtual environments, pass `--rks-python /path/to/rks-venv/bin/python`
and `--apw-python /path/to/apw-venv/bin/python`. On Windows these paths end in
`Scripts/python.exe`; quote paths containing spaces. The adapter never activates
environments or builds shell commands from these values.

The JSON response includes `apw.viewer_url`. Start APW with the exact database
and PDF directory used above, then open that link:

```bash
apw-viewer-server --db-path /path/to/review/events.db --pdf-root /path/to/review/pdfs
```

The default viewer URL is `http://127.0.0.1:8790`. Use `--viewer-url` if the local
viewer is listening at a different base URL. The adapter does not check server
availability. The viewer must use the returned `apw.db_path` and allow the
returned `apw.pdf_root`; otherwise the session or document will be unavailable.

## Contract and revision behavior

`rks papers source <paper_id>` returns `rks.paper-source.v1`:

- Paper ID, title, DOI, arXiv ID, source type, and original source reference.
- Absolute local PDF path, SHA-256 digest, and the number of bytes read.

The adapter returns `scientific-tooling.reading-handoff.v1`:

- Caller-supplied workspace ID and current RKS data directory.
- The complete RKS source descriptor.
- Verified snapshot path, SHA-256, and byte count.
- APW database path, paper reference, session ID, reuse flag, PDF root, and viewer URL.

The APW paper reference is
`rks:<workspace-id>:<paper-id>:sha256:<document-sha256>`. PDFs are copied into
`<cache-dir>/<document-sha256>.pdf` and verified before APW is called. An incomplete
copy is never published as the source. Existing copies are checked before reuse;
corrupt copies produce an error rather than being silently overwritten.

Sequential repeated opens reuse an active session for the same paper reference
and canonical absolute snapshot path. Equivalent absolute path spellings (including
Windows short paths) resolve to that same location. Relative session paths are
not reinterpreted from the adapter's working directory. A new PDF revision receives a new paper reference and session;
the prior PDF copy remains available to its annotations. Simultaneous first opens
can create separate sessions under the same paper reference. Session reuse is
not a transaction or a guarantee of exactly-once creation.

Keep the cache alongside the APW database in backups and do not edit its PDFs.
The cache is verified at handoff time, not protected against subsequent external
modification. The [evidence import workflow](evidence-import.md) rechecks document hashes. Changing the
cache path can require a new session; automatically relocating existing sessions
is outside this slice.

## Failure and recovery

Missing papers/PDFs, an uninitialized RKS database, incompatible source schemas,
empty PDFs, and changed or corrupt source bytes fail with a nonzero exit code.
Errors appear as JSON on stderr. Relative PDF paths in RKS are rejected because
resolving them against an arbitrary working directory could select the wrong file.
Repair source metadata or configuration before retrying.

If a copy succeeded but APW failed, retrying reuses the verified copy. If APW
opened a session before the command output was lost, a sequential retry discovers
it through the supported session-list API. No fallback to a different PDF occurs.
This establishes file identity, not scientific validity or correct PDF parsing.

## Validation

Unit tests need only the Python standard library:

```bash
python -m unittest discover -s tests -p test_research_reading.py -v
```

The offline integration test uses a generated one-page PDF, the real RKS ingest
and source commands, and the real APW session/export commands. Set
`RKS_TEST_PYTHON` and `APW_TEST_PYTHON` to the Python executables in the installed
environments, then run:

```bash
python -m unittest discover -s tests -v
```

Without those variables, the integration test is explicitly skipped. It checks
revision preservation, sequential session reuse, and workspace namespace
isolation. Browser rendering and navigation to an individual evidence passage
need separate validation. CI currently runs adapter unit tests on Windows and
Linux; cross-repository integration is opt-in until compatible revisions are
available together.

## Next steps

Selected export, native transactional RKS import, explicit revision acceptance,
and merge/deletion behavior are implemented in the
[evidence import workflow](evidence-import.md).

The [source-linked brief workflow](source-linked-brief.md) adds exact passage
navigation after import. The reading-handoff URL still opens the session; generated
brief citations include the PDF and passage identities.

Exercise the journey on a representative rights-cleared scientific corpus before
declaring Phase 2 complete. Scientific review and a researcher pilot require real
participants and are not implied by generated fixtures or browser tests.
