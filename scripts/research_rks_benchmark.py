"""Measure native RKS retrieval over pinned, prepared scientific source excerpts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

from research_corpus import (
    DEFAULT_CORPUS,
    candidates,
    digest,
    load_corpus,
    require,
    source_path,
    verify_sources,
    write_json,
)
from research_reading import WorkflowError, command_prefix, run_json


NATIVE_METHODS = (("lexical", "rks-bm25-terms-v1"), ("phrase", "rks-literal-phrase-v1"),
                  ("semantic", "rks-local-hash-v1"))


def verify_search_identity(payload: dict, mode: str) -> dict:
    metadata = payload.get("lexical_retrieval", {})
    expected = "literal-phrase-v1" if mode == "phrase" else "bm25-terms-v1"
    require(payload.get("mode") == mode and metadata.get("method") == expected,
            "Native query interpretation changed; define a new evaluation method/version")
    if mode != "phrase":
        require(metadata.get("parameters") == {"k1": 1.2, "b": 0.75}, "Native BM25 parameters changed")
    return metadata


def run_benchmark(args: argparse.Namespace) -> dict:
    corpus, questions = load_corpus(args.corpus)
    # All integrity checks precede workspace creation. No fetch occurs here.
    verify_sources(corpus, args.cache, include_pdf=True)
    require(not args.run_dir.exists(), "Choose a new run directory; existing benchmark workspaces are preserved")
    args.run_dir.mkdir(parents=True)
    rks = command_prefix(args.rks_python, "rks", "rks")
    data_dir = (args.run_dir / "rks").resolve()
    env = {"RKS_DATA_DIR": str(data_dir), "RKS_AUTO_EXTRACT_MODE": "none"}
    documents, claim_to_document, paper_ids = candidates(corpus), {}, {}
    by_id = {doc["id"]: doc for doc in documents}
    document_papers = {p["id"]: p["paper_id"] for p in corpus["passages"]}
    document_papers.update({v["id"]: document_papers[v["canonical_id"]] for v in corpus["variants"]})
    for paper in corpus["papers"]:
        ingested = run_json(rks + ["ingest", "pdf", str(source_path(args.cache, paper, "pdf").resolve()),
                                   "--title", paper["title"]], env=env)
        paper_ids[paper["id"]] = ingested["id"]
        selected = [doc for doc in documents if document_papers[doc["id"]] == paper["id"]]
        prepared = {"claims": [{
            "text": doc["text"], "predicate": "documents", "context": {
                "subject_text": "", "evaluation_only": True, "corpus_id": corpus["id"], "passage_id": doc["id"],
            }, "evidence": {"paper_id": ingested["id"], "quote": doc["text"], "source_doi": paper["doi"],
                            "corpus_revision": digest(corpus), "reference_status": "unreviewed_prepared_source_excerpt"},
            "confidence": None,
        } for doc in selected]}
        source = args.run_dir / f"{paper['id']}-prepared.json"
        write_json(source, prepared)
        imported = run_json(rks + ["import", "claims", ingested["id"], str(source.resolve())], env=env)
        require(imported["embedding_index"]["model"] == "local-hash-v1", "Native embedding model changed; define a new evaluation method/version")
        require(len(imported["claim_ids"]) == len(selected), "Native import returned an unexpected number of source passages")
        for claim_id, document in zip(imported["claim_ids"], selected, strict=True):
            require(claim_id not in claim_to_document, "Native claim identity collision")
            claim_to_document[claim_id] = document["id"]
    methods: dict[str, dict] = {name: {} for _, name in NATIVE_METHODS}
    method_metadata = {}
    responses, timings = [], {name: [] for name in methods}
    for question in questions["questions"]:
        for mode, name in NATIVE_METHODS:
            started = time.perf_counter()
            payload = run_json(rks + ["search", question["question"], "--mode", mode], env=env)
            timings[name].append(time.perf_counter() - started)
            metadata = verify_search_identity(payload, mode)
            require(name not in method_metadata or method_metadata[name] == metadata, "Native search policy changed during this run")
            method_metadata[name] = metadata
            if mode in {"lexical", "phrase"}:
                matches = [(claim["id"], claim["text"]) for claim in payload["claims"]]
            else:
                # Preserve the native global top-ten cap. Do not backfill after
                # paper/concept hits or duplicate representations consume slots.
                matches = [(match["object_id"], match["label"]) for match in payload["semantic_matches"]
                           if match["object_type"] == "claim"]
            ranking = []
            for claim_id, label in matches:
                require(claim_id in claim_to_document, "Unexpected native candidate outside the benchmark workspace")
                document_id = claim_to_document[claim_id]
                require(label == by_id[document_id]["text"], "Native claim ID order/label mapping changed")
                ranking.append(document_id)
            methods[name][question["id"]] = ranking
            responses.append({"question_id": question["id"], "mode": mode, "response": payload})
    result = {
        "schema": "scientific-tooling.native-retrieval-rankings.v1", "corpus_revision": digest(corpus),
        "questions_revision": digest(questions), "methods": methods,
        "provenance": {
            "python": platform.python_version(), "rks_command": rks,
            "embedding_model": "local-hash-v1", "embedding_dimensions": 64,
            "lexical_retrieval_by_method": method_metadata,
            "input_mode": "Prepared excerpts explicitly imported as extracted claims in a fresh disposable RKS workspace; no live extraction or reviewed graph promotion.",
            "native_result_policy": "Verbatim questions; ranked-term and literal-phrase claim order as returned, under separate method identities; semantic claims within native global top ten, with no backfill.",
            "bm25_comparison_notice": "BM25 ranks passages directly; RKS semantic results share a top-ten cap with papers/concepts. This compares exposed retrieval behavior, not isolated identical rankers.",
            "source_documents": {p["id"]: p["pdf"]["sha256"] for p in corpus["papers"]},
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "query_timing_seconds_including_cli_startup": {name: {"total": sum(values), "mean": sum(values) / len(values)}
                                                          for name, values in timings.items()},
        },
    }
    write_json(args.run_dir / "native-rankings.json", result)
    write_json(args.run_dir / "native-responses.json", {"paper_ids": paper_ids, "claim_to_document": claim_to_document, "responses": responses})
    return {"path": str((args.run_dir / "native-rankings.json").resolve()), "papers": len(paper_ids),
            "prepared_passages_including_duplicate": len(documents), "queries_per_method": len(questions["questions"])}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--rks-python", type=Path)
    args = parser.parse_args(argv)
    try:
        result = run_benchmark(args)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": "native_benchmark_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
