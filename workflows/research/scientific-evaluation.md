# Evaluate the literature workflow on scientific sources

Use the [single-cell RNA-seq candidate corpus](../../evaluations/scrna-methods-v1/README.md)
after the source-reading, selected-import, and source-linked-brief workflow works.
It provides ten attributed open-access methods papers, pinned original PDFs/JATS,
23 excerpt/table passages, 20 bounded draft questions, and a pending review packet.

First validate the corpus and explicitly fetch the pinned sources into a local
cache. Run the native RKS baseline in a fresh evaluation directory. Compare its
recorded retrieval with the fixed BM25 passage baseline, preserving question/source
revisions, raw responses, model/index identity, native result caps, and duplicate
handling. A new run must not overwrite an earlier run or use a researcher's active
workspace. Prepared-source import checks do not measure extraction quality.

The current runner requires RKS's `bm25-terms-v1` and `literal-phrase-v1` search
metadata and rejects missing or changed method/parameter identities. Ranked term,
literal phrase and local-hash results are recorded separately. Preserve the
original `baseline-results.json`; use a new result file to compare behavior after
the query-interpretation fix. Neither the questions nor the reference labels may
be edited to improve a ranker's score.

Then exercise the original-PDF reading journey. It creates unreviewed reading
annotations, prepares dry-run reports, transactionally imports selected evidence,
replays the import, and generates briefs. Browser verification checks that their
links open the actual PDF/page/quote. A browser success establishes source location,
not that an interpretation is scientifically correct.

Inspect the per-question results as well as aggregates. Retrieve a correct source
for a question before interpreting any generated answer. Do not replace source
fidelity, numerical/negation checks, or scientific judgment with lexical similarity.
The corpus includes differing findings/conditions, tables and units, unanswerable
probes, and a duplicated representation. Candidate labels may be incomplete or
incorrect until independently reviewed.

Give the review packet and source records to a qualified reviewer. Record their
actual review only after it occurs. Keep judgments tied to the exact source and
question revisions. Scientific answer accuracy remains unavailable until reviewed
references and separately evaluated answers exist. The public reserved split is
not a blind held-out study; obtain independently authored questions for that use.

The next engineering decision should address a measured bottleneck with frozen
comparisons and independently reviewed cases. Actual researcher pilots, package
installation checks, and hosted cross-repository CI remain separate acceptance work.
