"""Validate, fetch, and evaluate a versioned scientific source-passage corpus."""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
import sys
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from scientific_tooling.reading import WorkflowError

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "evaluations" / "scrna-methods-v1"
MAX_SOURCE_BYTES = 25 * 1024 * 1024


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def text(node: ET.Element) -> str:
    return " ".join("".join(node.itertext()).split())


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, indent=2, ensure_ascii=True, allow_nan=False)
        output.write("\n")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowError(message)


def load_corpus(directory: Path = DEFAULT_CORPUS) -> tuple[dict, dict]:
    corpus, questions = read_json(directory / "corpus.json"), read_json(directory / "questions.json")
    validate_corpus(corpus, questions)
    return corpus, questions


def validate_corpus(corpus: dict, questions: dict) -> None:
    require(corpus["schema"] == "scientific-tooling.corpus.v1", "Unsupported corpus schema")
    require(questions["schema"] == "scientific-tooling.questions.v1", "Unsupported questions schema")
    require(questions["corpus_id"] == corpus["id"] and questions["corpus_revision"] == digest(corpus),
            "Questions refer to a different corpus revision; review and refreeze the references")
    require(corpus["curation"]["domain_review"] == "pending", "Domain review belongs in a separate revision-bound review artifact")
    papers = {paper["id"]: paper for paper in corpus["papers"]}
    require(10 <= len(papers) <= 15 and len(papers) == len(corpus["papers"]), "Expect 10-15 distinct paper IDs")
    require(len({paper["doi"] for paper in papers.values()}) == len(papers), "Duplicate DOIs cannot count as independent papers")
    for paper in papers.values():
        require(re.fullmatch(r"[a-z][a-z0-9-]*", paper["id"]) is not None, "Invalid paper ID")
        license_record = paper["license"]
        require(license_record["spdx"] == "CC-BY-4.0"
                and license_record["url"] == "https://creativecommons.org/licenses/by/4.0/"
                and "creativecommons.org/licenses/by/4.0/" in license_record["evidence_text"]
                and text_hash(license_record["evidence_text"]) == license_record["evidence_sha256"],
                f"Missing or inconsistent article-specific redistribution rights for {paper['id']}")
        require(bool(paper["authors"]) and all(isinstance(author, str) and author.strip() for author in paper["authors"])
                and bool(paper["title"]) and bool(paper["doi"]), "Missing attribution")
        require(paper["source_url"] == f"https://pmc.ncbi.nlm.nih.gov/articles/{paper['pmcid']}/"
                and paper["publisher_url"] == f"https://doi.org/{paper['doi']}", "Source attribution links disagree with their identifiers")
        for kind in ("xml", "pdf"):
            descriptor = paper[kind]
            require(isinstance(descriptor, dict) and re.fullmatch(r"[0-9a-f]{64}", descriptor["sha256"]) is not None,
                    f"Missing pinned {kind} fingerprint for {paper['id']}")
            require(descriptor["url"].startswith("https://")
                    and type(descriptor["size_bytes"]) is int and 0 < descriptor["size_bytes"] <= MAX_SOURCE_BYTES,
                    f"Invalid {kind} source descriptor")
    passages = {passage["id"]: passage for passage in corpus["passages"]}
    require(len(passages) == len(corpus["passages"]), "Duplicate passage ID")
    require({p["paper_id"] for p in passages.values()} == set(papers), "Every selected paper needs an attributed passage")
    for passage in passages.values():
        require(passage["kind"] in {"text", "table"} and text_hash(passage["text"]) == passage["sha256"],
                f"Corrupt passage {passage['id']}")
        require("\ufffd" not in passage["text"], f"Replacement characters in passage {passage['id']}")
        if passage["kind"] == "table":
            table = passage["table"]
            require(all(len(row) == len(table["headers"]) for row in table["rows"]), "Table lost column boundaries")
        else:
            require(type(passage["start"]) is int and type(passage["end"]) is int
                    and 0 <= passage["start"] < passage["end"]
                    and passage["end"] - passage["start"] == len(passage["text"]), "Invalid source text slice")
    seen = set(passages)
    for variant in corpus["variants"]:
        require(variant["id"] not in seen and variant["canonical_id"] in passages, "Invalid duplicate representation identity")
        require(" ".join(variant["text"].split()) == " ".join(passages[variant["canonical_id"]]["text"].split()),
                "Duplicate representation changes source content")
        seen.add(variant["id"])
    require(len(questions["questions"]) == 20 and questions["frozen_before_baseline"] is True, "Expect twenty frozen questions")
    question_ids, paper_splits = set(), {}
    for question in questions["questions"]:
        require(question["id"] not in question_ids and question["question"].strip(), "Duplicate or empty question")
        question_ids.add(question["id"])
        require(question["review_status"] == "unreviewed", "Do not turn agent drafts into human reviews")
        require(question["split"] in {"development", "reserved"}, "Unknown evaluation split")
        expected = question["expected_passages"]
        require(len(expected) == len(set(expected)) and set(expected) <= set(passages), "Invalid relevance references")
        require(type(question["answerable_from_excerpts"]) is bool
                and question["answerable_from_excerpts"] == bool(expected), "Unanswerable probes need empty relevance targets")
        require(question["draft_answer"].strip() and question["required_qualifications"], "Missing draft answer or limits")
        group = {question["primary_paper"]} | {passages[key]["paper_id"] for key in expected}
        require(group <= set(papers), "Unknown primary paper")
        for paper_id in group:
            require(paper_splits.setdefault(paper_id, question["split"]) == question["split"],
                    "A source paper leaks across development and reserved questions")
    require(set(paper_splits.values()) == {"development", "reserved"}, "Both splits are required")


def source_path(cache: Path, paper: dict, kind: str) -> Path:
    return cache / f"{paper['id']}.{kind}"


def verify_bytes(path: Path, descriptor: dict) -> None:
    require(path.is_file(), f"Missing source {path}; run the explicit fetch command")
    with path.open("rb") as source:
        actual = source.read(MAX_SOURCE_BYTES + 1)
    require((hashlib.sha256(actual).hexdigest(), len(actual)) == (descriptor["sha256"], descriptor["size_bytes"]),
            f"Source fingerprint mismatch: {path}. Preserve it for inspection; do not substitute new bytes.")


def extract_passage(root: ET.Element, passage: dict) -> str:
    part, _, number = passage["selector"].rpartition(".")
    require(number.isdigit() and int(number) > 0, "Invalid JATS selector")
    index = int(number) - 1
    if passage["kind"] == "table":
        require(part == "table-wrap" and passage["transform"] == "jats-simple-table-tsv-v1", "Unsupported table transform")
        node = list(root.iter("table-wrap"))[index]
        require(all(cell.get("rowspan", "1") == "1" and cell.get("colspan", "1") == "1"
                    for cell in node.findall(".//th") + node.findall(".//td")), "Complex table requires explicit curation")
        headers = [text(cell) for cell in node.findall("./table/thead/tr/*")]
        rows = [[text(cell) for cell in row] for row in node.findall("./table/tbody/tr")]
        caption, footnotes = text(node.find("caption")), [text(p) for p in node.findall("./table-wrap-foot/p")]
        require(passage["table"] == {"headers": headers, "rows": rows, "caption": caption, "footnotes": footnotes},
                "Table structure differs from the pinned source")
        return text(node.find("label")) + ": " + caption + "\n" + "\t".join(headers) + "\n" + (
            "\n".join("\t".join(row) for row in rows)) + "\n" + "\n".join(footnotes)
    require(passage["transform"] == "jats-itertext-whitespace-v1", "Unsupported text transform")
    section = root.find("./front/article-meta/abstract") if part == "abstract.p" else root.find("body")
    require(part in {"abstract.p", "body.p"}, "Unsupported source section")
    full = text(list(section.iter("p"))[index])
    require(text_hash(full) == passage["source_text_sha256"], "Source paragraph differs from the frozen reference")
    return full[passage["start"]:passage["end"]]


def verify_sources(corpus: dict, cache: Path, *, include_pdf: bool = False) -> dict:
    for paper in corpus["papers"]:
        path = source_path(cache, paper, "xml")
        verify_bytes(path, paper["xml"])
        root = ET.fromstring(path.read_bytes())
        meta = root.find("./front/article-meta")
        authors = [" ".join(filter(None, [author.findtext("name/given-names"), author.findtext("name/surname")]))
                   for group in meta.findall("contrib-group") for author in group.findall("contrib")
                   if author.get("contrib-type") == "author" or group.get("content-type") == "author"]
        require(authors == paper["authors"] and text(meta.find("title-group/article-title")) == paper["title"],
                f"Source title/author attribution disagrees for {paper['id']}")
        require(any(node.get("pub-id-type") == "doi" and text(node) == paper["doi"] for node in meta.findall("article-id")),
                f"Source DOI disagrees for {paper['id']}")
        require(any(text(node) == paper["license"]["evidence_text"] for node in meta.findall("./permissions/license")),
                f"Source license evidence disagrees for {paper['id']}")
        for passage in corpus["passages"]:
            if passage["paper_id"] == paper["id"]:
                require(extract_passage(root, passage) == passage["text"], f"Excerpt differs from its source: {passage['id']}")
        if include_pdf:
            pdf = source_path(cache, paper, "pdf")
            verify_bytes(pdf, paper["pdf"])
            with pdf.open("rb") as source:
                require(source.read(5) == b"%PDF-", "Pinned PDF is not a PDF")
    return {"papers_verified": len(corpus["papers"]), "passages_verified": len(corpus["passages"]),
            "pdfs_verified": len(corpus["papers"]) if include_pdf else 0}


def fetch_sources(corpus: dict, cache: Path, *, include_pdf: bool = False) -> dict:
    cache.mkdir(parents=True, exist_ok=True)
    for paper in corpus["papers"]:
        for kind in (("xml", "pdf") if include_pdf else ("xml",)):
            destination, descriptor = source_path(cache, paper, kind), paper[kind]
            if destination.exists():
                verify_bytes(destination, descriptor)
                continue
            request = urllib.request.Request(descriptor["url"], headers={"User-Agent": "ScientificTooling-CorpusEvaluation/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                content = response.read(MAX_SOURCE_BYTES + 1)
            require((hashlib.sha256(content).hexdigest(), len(content)) == (descriptor["sha256"], descriptor["size_bytes"]),
                    f"Publisher source changed: {descriptor['url']}. Review a new corpus revision explicitly.")
            pending = None
            try:
                with tempfile.NamedTemporaryFile(dir=cache, prefix=".pending-", delete=False) as output:
                    pending = Path(output.name)
                    output.write(content)
                if destination.exists():
                    verify_bytes(destination, descriptor)
                else:
                    pending.replace(destination)
            finally:
                if pending is not None:
                    pending.unlink(missing_ok=True)
    return verify_sources(corpus, cache, include_pdf=include_pdf)


def candidates(corpus: dict) -> list[dict]:
    return [{"id": p["id"], "canonical_id": p["id"], "text": p["text"]} for p in corpus["passages"]] + [
        {"id": v["id"], "canonical_id": v["canonical_id"], "text": v["text"]} for v in corpus["variants"]]


def tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def rank_bm25(documents: list[dict], query: str, *, k1: float = 1.2, b: float = 0.75) -> list[str]:
    frequencies = [collections.Counter(tokens(doc["text"])) for doc in documents]
    average = sum(sum(freq.values()) for freq in frequencies) / len(frequencies)
    query_tokens, scores = set(tokens(query)), []
    for doc, freq in zip(documents, frequencies, strict=True):
        score = 0.0
        for token in query_tokens:
            count = freq.get(token, 0)
            if not count:
                continue
            document_frequency = sum(token in candidate for candidate in frequencies)
            inverse = math.log(1 + (len(documents) - document_frequency + 0.5) / (document_frequency + 0.5))
            score += inverse * count * (k1 + 1) / (count + k1 * (1 - b + b * sum(freq.values()) / average))
        if score > 0:
            scores.append((score, doc["id"]))
    return [key for _, key in sorted(scores, key=lambda pair: (-pair[0], pair[1]))]


def canonical_ranking(corpus: dict, ranking: list[str]) -> list[str]:
    canonical = {p["id"]: p["id"] for p in corpus["passages"]}
    canonical.update({v["id"]: v["canonical_id"] for v in corpus["variants"]})
    output = []
    for key in ranking:
        require(key in canonical, f"Unknown ranked passage: {key}")
        if canonical[key] not in output:
            output.append(canonical[key])
    return output


def ranking_metrics(expected: list[str], ranking: list[str]) -> dict:
    require(bool(expected) and len(expected) == len(set(expected)), "Ranking metrics require distinct answerable targets")
    targets = set(expected)
    require(len(ranking) == len(set(ranking)), "Collapse duplicate source representations before scoring")
    first = next((rank for rank, key in enumerate(ranking[:10], 1) if key in targets), None)
    return {"hit_at_1": float(bool(targets & set(ranking[:1]))), "hit_at_5": float(bool(targets & set(ranking[:5]))),
            "recall_at_5": len(targets & set(ranking[:5])) / len(targets), "mrr_at_10": 1 / first if first else 0.0}


def evaluate_rankings(corpus: dict, questions: dict, methods: dict[str, dict[str, list[str]]]) -> dict:
    require(bool(methods), "No retrieval methods supplied")
    expected_questions = {q["id"] for q in questions["questions"]}
    results = {}
    for method, rankings in methods.items():
        require(set(rankings) == expected_questions, "Every question, including abstention probes, needs a recorded ranking")
        per_question = []
        for question in questions["questions"]:
            ranked = canonical_ranking(corpus, rankings[question["id"]])
            metrics = ranking_metrics(question["expected_passages"], ranked) if question["answerable_from_excerpts"] else None
            per_question.append({"id": question["id"], "split": question["split"], "cases": question["cases"],
                                 "expected_passages": question["expected_passages"], "ranking": ranked[:10], "metrics": metrics})
        aggregates = {}
        for split in ("development", "reserved", "all"):
            rows = [row for row in per_question if row["metrics"] is not None and (split == "all" or row["split"] == split)]
            aggregates[split] = {"answerable_questions": len(rows), **{
                key: sum(row["metrics"][key] for row in rows) / len(rows) if rows else None
                for key in ("hit_at_1", "hit_at_5", "recall_at_5", "mrr_at_10")}}
        results[method] = {"aggregate": aggregates, "questions": per_question}
    return {"schema": "scientific-tooling.retrieval-evaluation.v1", "corpus_id": corpus["id"],
            "corpus_revision": digest(corpus), "questions_revision": digest(questions),
            "evaluated_at": datetime.now(timezone.utc).isoformat(), "reference_status": questions["reference_status"],
            "scientific_accuracy": None, "domain_review_complete": False,
            "scope": "Prepared source-passage retrieval against draft relevance labels; not extraction, answer generation, or scientific entailment.",
            "split_notice": questions["split_policy"],
            "unanswerable_probes": sum(not q["answerable_from_excerpts"] for q in questions["questions"]),
            "abstention_accuracy": None, "methods": results}


def review_packet(corpus: dict, questions: dict) -> dict:
    return {"schema": "scientific-tooling.corpus-review.v1", "corpus_revision": digest(corpus),
            "questions_revision": digest(questions), "instructions": "Fill only after an actual independent review. Drafts and empty records are not approvals.",
            "records": [{"question_id": q["id"], "question_revision": digest(q), "decision": "pending", "method": None, "reviewer": None,
                         "reviewed_at": None, "notes": "", "question": q["question"], "draft_answer": q["draft_answer"],
                         "expected_passages": q["expected_passages"], "required_qualifications": q["required_qualifications"]}
                        for q in questions["questions"]]}


def review_status(corpus: dict, questions: dict, packet: dict) -> dict:
    require(packet["schema"] == "scientific-tooling.corpus-review.v1"
            and packet["corpus_revision"] == digest(corpus) and packet["questions_revision"] == digest(questions),
            "Review packet is stale or belongs to a different reference set")
    by_id = {q["id"]: q for q in questions["questions"]}
    seen, counts = set(), collections.Counter()
    for record in packet["records"]:
        key = record["question_id"]
        require(key in by_id and key not in seen and record["question_revision"] == digest(by_id[key]), "Duplicate, unknown, or stale question review")
        require(record["decision"] in {"pending", "approved", "revise", "exclude"}, "Unknown review decision")
        if record["decision"] != "pending":
            require(record.get("method") == "human" and isinstance(record["reviewer"], str) and bool(record["reviewer"].strip())
                    and isinstance(record["reviewed_at"], str) and record["notes"].strip(), "Actual review requires reviewer, time, and notes")
            require(datetime.fromisoformat(record["reviewed_at"].replace("Z", "+00:00")).utcoffset() is not None,
                    "Review time needs a timezone")
        seen.add(key)
        counts[record["decision"]] += 1
    return {"approved": counts["approved"], "pending": len(by_id) - counts["approved"] - counts["revise"] - counts["exclude"],
            "revise": counts["revise"], "exclude": counts["exclude"], "reference_review_complete": counts["approved"] == len(by_id),
            "provenance": "Caller-asserted human review records; identity is not authenticated.", "scientific_accuracy": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "fetch", "verify-sources"):
        command = commands.add_parser(name)
        command.add_argument("--cache", type=Path)
        command.add_argument("--include-pdf", action="store_true")
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--rankings", type=Path, help="Optional external rankings, including native RKS baselines")
    evaluate.add_argument("--output", type=Path, required=True)
    packet = commands.add_parser("review-packet")
    packet.add_argument("--output", type=Path, required=True)
    status = commands.add_parser("review-status")
    status.add_argument("packet", type=Path)
    args = parser.parse_args(argv)
    try:
        corpus, questions = load_corpus(args.corpus)
        if args.command in {"fetch", "verify-sources"}:
            require(args.cache is not None, "Select an explicit source cache")
            operation = fetch_sources if args.command == "fetch" else verify_sources
            result = operation(corpus, args.cache, include_pdf=args.include_pdf)
        elif args.command == "validate":
            result = {"valid": True, "papers": len(corpus["papers"]), "passages": len(corpus["passages"]),
                      "questions": len(questions["questions"]), "corpus_revision": digest(corpus)}
        elif args.command == "evaluate":
            documents = candidates(corpus)
            methods = {"bm25-v1": {q["id"]: rank_bm25(documents, q["question"]) for q in questions["questions"]}}
            if args.rankings:
                external = read_json(args.rankings)
                require(external["corpus_revision"] == digest(corpus) and external["questions_revision"] == digest(questions),
                        "External rankings belong to different source/question revisions")
                require(not set(methods) & set(external["methods"]), "Duplicate retrieval method identity")
                methods.update(external["methods"])
            result = evaluate_rankings(corpus, questions, methods)
            if args.rankings:
                result["external_provenance"] = external["provenance"]
            result["implementation_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            write_json(args.output, result)
        elif args.command == "review-packet":
            result = review_packet(corpus, questions)
            write_json(args.output, result)
            result = {"path": str(args.output.resolve()), "pending_reviews": len(result["records"])}
        else:
            result = review_status(corpus, questions, read_json(args.packet))
    except (WorkflowError, OSError, ValueError, KeyError, TypeError, IndexError, ET.ParseError) as exc:
        print(json.dumps({"error": "corpus_evaluation_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
