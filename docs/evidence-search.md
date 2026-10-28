# Find imported evidence across a project

Milestone 1 implementation, October 27, 2026; dependency pins updated October 28.
Available from repository `main`, with matching RKS and APW commits pinned in
`pyproject.toml`. This development feature is not included in the tagged sci 0.3.1
release. Independent evaluation and release validation remain pending.

```bash
sci search "donor variance" --workspace review
sci search "normalization" --workspace review --paper p2 --review unreviewed --json
sci search "negative binomial" --workspace review --mode phrase --limit 20 --offset 0
```

The Evidence tab's **Find project evidence** form uses the same operation. Search
across all project papers or select one paper and a review status. Open a result's
supporting passage to return to its exact retained PDF and annotation. To use CLI
links when the reader is stopped, run `sci resume --workspace review`.

Search reads current **imported** annotations and notes. It searches their recorded
quotations, annotation comments, note titles and note bodies. Unsaved selections,
unimported highlights, other project databases, full paper text and extracted RKS
claims are outside this search. A no-match result does not show that a paper lacks
relevant information. Quotes are labeled source text; notes and interpretations
are labeled commentary. Review status is the recorded assertion for the imported
revision, not an endorsement created by the search.

## Matching and identity

RKS owns retrieval. The existing `bm25-terms-v1` ranker matches any complete query
term; phrase mode uses a literal normalized substring within one field. Both use
Unicode NFKC and casefold. There is no semantic fallback, stemming, query expansion
or model call. Relevance rank does not measure scientific support or confidence.
Statistics are calculated after project/source/review filtering. Unrelated papers
cannot affect rank or occupy result slots. IDs, review statements, timestamps and
serialized metadata are excluded from searchable text.

The project sends its RKS workspace identity, APW source identity and exact
`paper_id:document_sha256` pairs to `rks note search-evidence`. Scope is applied
inside one read-only RKS transaction before ranking. Reads neither initialize nor
migrate missing databases, and they do not start the reader or write project state.
Original evidence identity survives a paper merge; the canonical paper ID is also
returned. Repeated imports return one current revision per identity. Identical text
under different evidence identities stays separate and is ordered deterministically.

The JSON schema is `scientific-tooling.evidence-search.v1`. It includes the query,
retrieval method, exact paper scope, review filter, total, offset, limit, `has_more`,
and ordered `results`. Each result preserves its RKS note ID, external source key,
evidence revision, original record, project paper key/title, matched fields with
source/commentary roles, and checked passage links. Pages are one-based. Default
page size is 20; allowed sizes are 1–100. Repeat with a new offset for more results.
Each request reads current state; pagination is not a snapshot spanning writes.

## Explicit outcomes

- Blank queries and punctuation-only term queries return `empty_query`; no full
  evidence dump or broader search is substituted. The reader requires nonblank text.
- Unknown paper keys and ambiguous RKS paper IDs fail with instructions to select
  a unique project key. Papers still awaiting ingestion are listed in `pending_papers`;
  if none are ready, resume is required.
- Changed, deleted or retargeted RKS notes are excluded with
  `unavailable_evidence` reasons. Corrupt evidence/review revisions fail explicitly.
- Missing, changed or deleted APW anchors and missing/corrupt PDF snapshots retain
  the imported result text, with an actionable message and no active passage link.
  Unlinked notes explicitly have no supporting passage.
- Available links verify source bytes and the saved annotation revision. The
  existing viewer additionally checks page text, including ambiguous repeated
  quotations, when opened. It never silently chooses another passage.
- Changing reader filters, queries or sessions invalidates any outstanding search
  response. Changing the import preview clears prior displayed search results.

## Development validation and remaining acceptance

The frozen engineering cases in RKS `tests/test_evidence_search.py` check matching,
roles, namespace/source/review isolation, current-revision replay, duplicate text,
pagination, merges, corruption and read-only behavior. The installed sci suite
exercises two real papers through CLI and HTTP, source navigation, stopped-reader
search and corrupt retained PDFs. APW tests cover response ownership and HTTP guards.
The browser journey in `scripts/verify_workflow_browser.mjs` checks two-paper search,
filters, commentary, mobile layout and reopening search citations after restart.

Installed validation also exposed a reader startup publication race on Windows.
Startup now waits for a child-process acknowledgement after the server ownership
record is completely published, then verifies that same server instance over HTTP.
It no longer polls the record while it is being published. Invalid or missing
acknowledgements preserve diagnostics and clean up only the child just launched;
permission failures are not suppressed. Regression tests enforce publication order
and owned-process cleanup.

These tests use synthetic sources. They do not supply independently reviewed
scientific relevance judgments. Independent reference review, newly held-out
scientific questions, researcher usability pilots, large-project latency and
Windows/Linux/macOS release validation remain acceptance work. Keep milestone 1
in progress until those acceptance gates are complete.

For local development, build wheels from all three matching checkouts, then install
the three wheels together with `pip install --no-deps` in an isolated environment.
This tests the local implementations. The repository now also pins the published
RKS/APW commits and uses the same APW revision for browser CI. Before release,
run the ordinary pinned installation matrix. Do not replace pins with floating
branches or local paths.
