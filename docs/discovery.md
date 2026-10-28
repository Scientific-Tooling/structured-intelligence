# Discover and add papers (development)

Milestone 3 starts with bounded PubMed and Crossref discovery. Save a question or
identifier search, inspect its candidates, then explicitly select a PDF to add to
the reading project. Metadata, selection, source reading, evidence import and
scientific review remain separate operations.

For the browser workflow, follow the [nine-step screenshot guide](discovery-screenshots.md).

This implementation is available on main and is not in the tagged sci 0.3.1
release. The package and browser CI pin APW to
`c9aa169ec4fdcb5dd79d65c67baedb426df6bd73`, which includes discovery and the
research desk reader. Paper changes preserve the reader layout, workspace tab
and zoom mode while restoring each paper's reading position.

## Start with a question

```text
sci init --workspace my-review --question "Which single-cell normalization methods fit this experiment?"
sci discover search "single-cell RNA-seq normalization" --provider pubmed --limit 10 --workspace my-review
sci discover list --workspace my-review
sci discover show DISCOVERY_ID --workspace my-review --json
```

An existing `sci start` project also supports these commands. `init` creates a
question-only project; it does not create a reading session or launch a browser.
The first selected PDF enables the reader. Queries are explicit, at most 1,500
characters, with 1–25 results (default 10). No agent expands the query or chooses
papers automatically. Results preserve provider order, query translation and
warnings where supplied. Relevance is the provider's ranking, not a reviewed
judgment of suitability for the research question.

## Look up and select a work

```text
sci discover lookup "10.1038/s41467-019-12266-7" --workspace my-review --json
sci discover lookup "pmid:29961579" --workspace my-review --json
sci discover select DISCOVERY_ID --candidate c1 --source 1 --workspace my-review --json
sci open p1 --workspace my-review
```

Use IDs returned by your own saved discovery. DOI lookup uses Crossref; PMID
lookup uses PubMed. Canonical DOI/PubMed URLs are accepted. Other DOI registries
and arXiv identifiers are outside this first slice; unavailable records produce
an explicit provider error. A search is not automatically inferred from a failed
identifier lookup.

Candidates include title, authors, publication year, venue, identifiers, provider,
retrieval time, landing URL, reported licenses and any declared PDF sources.
Abstracts are metadata and never become a read PDF or imported evidence. Crossref
links declared as PDFs are unverified until acquisition. A PMCID alone does not
establish an available PDF. The former [PMC OA web service](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/)
was retired in August 2026; this implementation does not depend on it or invent
PDF URLs from a PMCID.

With one reported PDF source, explicit candidate selection may use it without
`--source`. With several, choose a numbered source. No alternate URL is tried
silently. Publisher access errors, HTML responses, incomplete PDFs and download
limits are reported with the saved selection request ID. Downloads require public
HTTPS, check redirects, cap metadata at 10 MiB and PDFs at 64 MiB, and enforce
socket and elapsed-time bounds. Requests are spaced within each process; multiple
independent clients must still respect their shared provider/IP rate limits.

If no PDF is reported, selection keeps an attributed reference with
`full_text_unavailable` status. It creates no RKS paper or APW session. To read it,
explicitly select a lawful local copy or look up the same DOI through Crossref:

```text
sci discover select DISCOVERY_ID --candidate c1 --pdf /path/to/paper.pdf --workspace my-review
```

Local selection records the file path and byte identity. It is the user's
attribution of that PDF to the candidate; the software does not establish that
the document's scientific content matches the bibliographic metadata.

## Continue in the reader

After at least one PDF is ready, open **Discover and add papers** in the paper
navigation panel. Search or look up an identifier, reopen a saved discovery,
inspect candidates and select the displayed PDF source. Multiple PDF links
require an explicit choice. References with no PDF stay visible with that status.
The reader lists interrupted selections and offers retry. Local file selection
is currently a CLI operation. Adding a PDF updates Project papers; opening it
uses the same verified source and session as CLI selection.

## Identity, provenance and recovery

Each discovery saves the exact query or identifier, project/question identity,
request URLs/times, raw provider responses with hashes, normalized candidates,
and a revision digest under `discoveries/DISCOVERY_ID/`. `show` reopens and
verifies these saved artifacts without querying the provider. A later search is
a new run because live provider results can change. Failed and interrupted runs
retain what was received; rerun the query to create another bounded attempt.

Selected bibliographic works live in `workspace.json` under `works`. Exact shared
DOI/PMID/PMCID identities join provider provenance to one work. Titles alone never
merge works. Conflicting identifiers or aliases bridging two existing works need
inspection rather than an automatic merge. Discovery metadata is retained in
the project catalog; RKS owns the selected PDF and durable evidence, and APW owns
reading sessions and annotations.

A work can have multiple PDF versions. Identical bytes reuse the existing paper;
different bytes create another paper key and session under the same work, leaving
older source revisions intact. A PDF already attributed to another work causes
an explicit conflict. Existing local papers acquire a work attribution only when
an explicitly selected candidate has the identical PDF hash.

Selections save an immutable request and retained snapshot identity under
`selections/REQUEST_ID/`. The snapshot is persisted before native ingestion.
If a response is lost or preparation fails, retry that exact request:

```text
sci discover list --workspace my-review --json
sci discover retry REQUEST_ID --workspace my-review --json
sci resume --workspace my-review
```

Retry reuses retained bytes and native ingestion/session recovery. A completed
request verifies its saved PDF and paper attribution before returning a replay.
Changed requests cannot reuse an ID. Changing the selected source or supplying
a local PDF is a new explicit selection, not a mutation of the old request.
Keep the workspace at its original absolute path, as with other sci operations.

Saved records publish atomically. Windows uses shared record readers and the
native `FileRenameInfoEx` replacement operation; this requires a modern Windows
filesystem supporting that operation (validated on local NTFS). Existing readers
keep their prior complete record while new readers see the new revision. Genuine
permissions and exclusive file locks remain errors. No retry loop bypasses them.

## Verification and remaining acceptance

Engineering tests cover frozen PubMed/Crossref metadata, exact identifiers,
multiple providers, duplicate and changed PDFs, missing/invalid full text,
conflicting identities, changed artifacts, project scope and interrupted native
ingestion. The installed browser check exercises explicit selection, a lost HTTP
reply, source navigation, retained references and desktop/mobile layouts using
clearly synthetic provider fixtures. Tests do not assess scientific relevance.

Windows validation also isolated a record-publication defect: standard-library
replacement failed 62 times in 3,000 standalone writes on this machine. Native
replacement completed the same 3,000-write diagnostic without failures. Regression
tests cover open readers, Unicode paths, failed serialization and preservation of
read-only files. The implementation follows Microsoft's
[file replacement semantics](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information).

Live verification on October 28, 2026 used both providers and a Crossref DOI
lookup for Vieth et al., `10.1038/s41467-019-12266-7`. Its selected Nature PDF
entered RKS/APW and matched the existing evaluation corpus SHA-256
`112dcf8fe1db9ff5c33e05bda563e678cff5254ceffe8521dd37f439ae0c2940`.
That checks one accessible source, not publisher-wide availability.

Tagged release verification, independent relevance judgments, researcher
usability checks and broader full-text availability
measurements remain pending. This slice does not crawl reference graphs,
schedule recurring searches, infer review decisions or merge different works.

The PubMed adapter packages the parser already maintained by the
[NCBI E-utilities skill](../skills/ncbi-eutilities-assistant/SKILL.md).
Provider contracts: [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25497/)
and [Crossref REST API](https://github.com/CrossRef/rest-api-doc).
