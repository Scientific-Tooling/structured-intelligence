"""Exercise original scientific PDFs through reading, selected import, and briefs."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from research_corpus import (
    DEFAULT_CORPUS,
    digest,
    load_corpus,
    read_json,
    require,
    verify_sources,
    write_json,
)
from research_reading import WorkflowError, command_prefix, run_json, session_url

SCRIPTS = Path(__file__).resolve().parent


def api(base: str, route: str, payload: dict | None = None) -> dict:
    request = urllib.request.Request(base.rstrip("/") + route,
                                     data=json.dumps(payload).encode("utf-8") if payload is not None else None,
                                     headers={"Content-Type": "application/json"} if payload is not None else {})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def ensure_annotation(base: str, session_id: str, case: dict) -> dict:
    expected = {"id": "corpus-" + case["id"], "page": case["page"], "type": "highlight", "quote": case["quote"],
                "anchor": {"quote": case["quote"], "start": None, "end": None, "prefix": "", "suffix": ""},
                "comment": case["note"], "tags": ["scientific-corpus", "unreviewed"], "rects": []}
    offset = 0
    while True:
        page = api(base, "/api/annotations?" + urlencode({"session_id": session_id, "limit": 1000, "offset": offset}))
        for row in page["annotations"]:
            annotation = row["annotation"]
            if annotation["id"] == expected["id"]:
                require(all(annotation[key] == value for key, value in expected.items()),
                        "An existing corpus annotation was edited. Preserve it and review a new case/version explicitly.")
                return annotation
        if not page["has_more"]:
            break
        require(type(page["next_offset"]) is int and page["next_offset"] > offset, "Invalid APW annotation pagination")
        offset = page["next_offset"]
    now = datetime.now(timezone.utc).isoformat()
    annotation = {**expected, "createdAt": now, "updatedAt": now}
    return api(base, "/api/annotations", {"session_id": session_id, "annotation": annotation})["annotation"]


def run_journey(args: argparse.Namespace) -> dict:
    corpus, _ = load_corpus(args.corpus)
    verify_sources(corpus, args.cache, include_pdf=True)
    plan = read_json(args.corpus / "journey.json")
    require(plan["schema"] == "scientific-tooling.scientific-journey.v1" and plan["corpus_revision"] == digest(corpus),
            "Journey cases belong to a different corpus revision")
    require(plan["status"] == "agent_prepared_unreviewed_reading_notes", "Journey seeding cannot assert human review")
    require(not args.output_dir.exists(), "Choose a new journey artifact directory")
    session_url(args.viewer_url, "validate")
    require(urlsplit(args.viewer_url).hostname in {"127.0.0.1", "localhost", "::1"}, "The evaluation viewer must run on loopback")
    native = read_json(args.benchmark_run / "native-rankings.json")
    require(native["corpus_revision"] == digest(corpus), "Benchmark workspace belongs to a different corpus revision")
    mapping = read_json(args.benchmark_run / "native-responses.json")["paper_ids"]
    passages = {p["id"]: p for p in corpus["passages"]}
    papers = {p["id"]: p for p in corpus["papers"]}
    case_ids = set()
    for case in plan["cases"]:
        require(isinstance(case["id"], str) and re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", case["id"]) is not None
                and case["id"] not in case_ids, "Invalid or duplicate journey case ID")
        require(type(case["page"]) is int and case["page"] > 0 and case["quote"].strip()
                and case["question"].strip() and case["note"].strip(), "Journey case needs a page, quote, question, and note")
        case_ids.add(case["id"])
        require(case["paper_id"] in mapping and case["passage_id"] in passages
                and passages[case["passage_id"]]["paper_id"] == case["paper_id"]
                and case["quote"] in passages[case["passage_id"]]["text"], "Journey quote does not match its attributed source excerpt")
    require(api(args.viewer_url, "/api/health")["service"] == "agent-pdf-workbench", "Select an APW viewer")
    args.output_dir.mkdir(parents=True)
    rks = command_prefix(args.rks_python, "rks", "rks")
    data_dir = (args.benchmark_run / "rks").resolve()
    env = {"RKS_DATA_DIR": str(data_dir), "RKS_AUTO_EXTRACT_MODE": "none"}
    interpreters = ["--rks-python", str(args.rks_python), "--apw-python", str(args.apw_python)]
    results = []
    for case in plan["cases"]:
        paper_id = mapping[case["paper_id"]]
        handoff = run_json([
            sys.executable, str(SCRIPTS / "research_reading.py"), paper_id,
            "--workspace-id", args.workspace_id, "--rks-data-dir", str(data_dir),
            "--apw-db", str(args.apw_db.resolve()), "--cache-dir", str(args.pdf_cache.resolve()),
            "--viewer-url", args.viewer_url, *interpreters,
        ])
        require(handoff["snapshot"]["sha256"] == papers[case["paper_id"]]["pdf"]["sha256"], "RKS paper no longer matches the pinned original PDF")
        session_id = handoff["apw"]["session_id"]
        attached = api(args.viewer_url, "/api/session?" + urlencode({"session_id": session_id}))
        require(attached["paper_ref"] == handoff["apw"]["paper_ref"] and attached["pdf_uri"] == handoff["snapshot"]["path"],
                "The viewer is not serving the selected APW database/snapshot")
        annotation = ensure_annotation(args.viewer_url, session_id, case)
        prefix = args.output_dir / case["id"]
        handoff_path, bundle_path, plan_path = prefix.with_suffix(".handoff.json"), prefix.with_suffix(".evidence.json"), prefix.with_suffix(".plan.json")
        write_json(handoff_path, handoff)
        prepared = run_json([
            sys.executable, str(SCRIPTS / "research_evidence.py"), str(handoff_path.resolve()),
            "--source-id", args.source_id, "--annotation-id", annotation["id"],
            "--bundle", str(bundle_path.resolve()), "--plan", str(plan_path.resolve()), *interpreters,
        ])
        require(not prepared["applied"], "Preparation unexpectedly applied evidence")
        command = rks + ["note", "import-evidence", str(bundle_path.resolve()), "--workspace-id", args.workspace_id,
                         "--apply", "--plan", str(plan_path.resolve())]
        first, replay = run_json(command, env=env), run_json(command, env=env)
        require(first["applied"] and replay["counts"]["unchanged"] == 1, "Import replay did not preserve evidence identity")
        brief_path = prefix.with_suffix(".brief.md")
        brief = run_json([
            sys.executable, str(SCRIPTS / "research_brief.py"), paper_id, "--question", case["question"],
            "--workspace-id", args.workspace_id, "--rks-data-dir", str(data_dir), "--source-id", args.source_id,
            "--apw-db", str(args.apw_db.resolve()), "--viewer-url", args.viewer_url, "--output", str(brief_path.resolve()), *interpreters,
        ])
        require(brief["counts"]["unreviewed"] == 1 and brief["counts"]["linked_passages"] == 1
                and brief["counts"]["reviewed"] == 0, "Unexpected brief evidence/review state")
        links = re.findall(r"\[Open the supporting passage\]\(([^)]+)\)", brief_path.read_text(encoding="utf-8"))
        require(len(links) == 1, "Brief needs exactly the selected source link")
        results.append({"case_id": case["id"], "source_paper": case["paper_id"], "paper_id": paper_id,
                        "document_sha256": handoff["snapshot"]["sha256"], "page": case["page"],
                        "quote": case["quote"], "brief": str(brief_path.resolve()), "url": links[0],
                        "first_import_counts": first["counts"],
                        "replay_unchanged": replay["counts"]["unchanged"], "review_status": "unreviewed"})
    result = {"schema": "scientific-tooling.scientific-journey-results.v1", "corpus_revision": digest(corpus),
              "workspace_id": args.workspace_id, "source_id": args.source_id,
              "scientific_accuracy": None, "browser_validation": "pending", "cases": results}
    write_json(args.output_dir / "journey-results.json", result)
    return {"path": str((args.output_dir / "journey-results.json").resolve()), "completed_original_pdf_cases": len(results),
            "scientific_review": "pending", "browser_validation": "pending"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--benchmark-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--apw-db", type=Path, required=True)
    parser.add_argument("--pdf-cache", type=Path, required=True)
    parser.add_argument("--viewer-url", default="http://127.0.0.1:8794")
    parser.add_argument("--workspace-id", default="scrna-eval-v1")
    parser.add_argument("--source-id", default="scrna-reader-v1")
    parser.add_argument("--rks-python", type=Path, required=True)
    parser.add_argument("--apw-python", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run_journey(args)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": "scientific_journey_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
