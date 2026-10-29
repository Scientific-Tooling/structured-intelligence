"""Evaluate actual imported notes and prepare revision-bound human review packets.

All source acquisition is separate. JATS excerpts are unlinked notes, never
invented PDF anchors. Mutations are confined to a new evaluation project.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from research_corpus import (
    DEFAULT_CORPUS,
    candidates,
    canonical_ranking,
    digest,
    evaluate_rankings,
    load_corpus,
    read_json,
    require,
    source_path,
    verify_bytes,
    verify_sources,
    write_json,
)
from research_reading import WorkflowError

FIXTURE = "scientific-tooling.imported-evidence-fixture.v1"
PACKET = "scientific-tooling.imported-evidence-review-packet.v1"
METHOD = "rks-imported-note-bm25-v1"
# Retain the evaluator bytes when the process loads, before any long-running work.
HARNESS = {name: (Path(__file__).parent / name).read_bytes() for name in
           ("research_imported_evidence.py", "research_corpus.py", "research_reading.py")}


def retain_harness(directory):
    folder = directory / "harness"
    folder.mkdir()
    for name, content in HARNESS.items():
        (folder / name).write_bytes(content)
    return {name: hashlib.sha256(content).hexdigest() for name, content in HARNESS.items()}


def now():
    return datetime.now(UTC).isoformat()


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def seal(value):
    return {**value, "revision": digest(value)}


def check_seal(value, schema):
    require(value.get("schema") == schema and value.get("revision") ==
            digest({k: v for k, v in value.items() if k != "revision"}), "Changed or unsupported evaluation artifact")


def make_fixture(corpus, questions):
    papers = {p["id"]: p for p in corpus["passages"]}
    entries = [{**entry, "paper_id": papers[entry["canonical_id"]]["paper_id"],
                "kind": "note", "match_role": "commentary", "pdf_anchor": None,
                "source": {k: v for k, v in papers[entry["canonical_id"]].items() if k != "text"}}
               for entry in candidates(corpus)]
    return seal({"schema": FIXTURE, "corpus_revision": digest(corpus), "questions_revision": digest(questions),
                 "entries": entries, "reference_status": "agent_drafted_pending_independent_review",
                 "mapping_policy": "Exact JATS excerpt text in APW note markdown; empty title; no linked PDF annotation. Attribution and selector are retained in this fixture, not added to the searchable text.",
                 "ranking_policy": "Top ten native evidence records, in returned order. Apply each cutoff to native result slots BEFORE collapsing canonical duplicates; never backfill. No precision or scientific-accuracy claim."})


def validate_fixture(fixture, corpus, questions):
    check_seal(fixture, FIXTURE)
    require(fixture == make_fixture(corpus, questions), "Fixture differs from the frozen source/question mapping")


def candidate_identity(manifest_path):
    manifest = read_json(manifest_path)
    require(manifest.get("schema") == "scientific-tooling.development-candidate.v1", "Use a frozen candidate manifest")
    modules = {}
    for package, module, repository in (("scientific-tooling", "scientific_tooling", "structured-intelligence"),
                                      ("agent-pdf-workbench", "agent_pdf_workbench", "agent-pdf-workbench"),
                                      ("research-knowledge-substrate", "rks", "research-knowledge-substrate")):
        distribution = importlib.metadata.distribution(package)
        require(not json.loads(distribution.read_text("direct_url.json") or "{}").get("dir_info", {}).get("editable"),
                "Use an installed candidate wheel, not an editable package")
        checked = 0
        for relative, record in manifest["repositories"][repository]["files"].items():
            if relative.startswith(f"src/{module}/"):
                installed = Path(distribution.locate_file(relative.removeprefix("src/")))
                require(installed.is_file() and sha_file(installed) == record["sha256"],
                        f"Installed candidate source mismatch: {package}/{relative}")
                checked += 1
        require(checked > 0, "Candidate manifest has no installed module files")
        modules[package] = {"version": distribution.version, "checked_files": checked,
                            "direct_url": json.loads(distribution.read_text("direct_url.json") or "{}")}
    return {"candidate": manifest["candidate"], "manifest_sha256": sha_file(manifest_path), "packages": modules}


def note(entry, timestamp):
    return {"id": "corpus-" + entry["id"], "title": "", "markdown": entry["text"],
            "linkedAnnotationIds": [],
            "createdAt": timestamp, "updatedAt": timestamp}


def map_results(payload, mapping, data):
    require(payload.get("schema") == "scientific-tooling.evidence-search.v1"
            and payload.get("workspace_id") == data["workspace_id"]
            and payload.get("source_id") == data["source_id"], "Search returned a foreign project or unsupported contract")
    require(not payload["unavailable_evidence"], "Evaluation evidence became unavailable")
    ranking, seen = [], set()
    for entry in payload["results"]:
        key = entry["note_id"]
        require(key in mapping and key not in seen, "Unknown or duplicate native evidence identity")
        expected = mapping[key]
        item = entry["record"]["item"]
        require(entry["source_key"] == expected["source_key"] and entry["revision"] == expected["revision"]
                and entry["paper_id"] == expected["paper_id"] and item["kind"] == "note"
                and item["content"]["markdown"] == expected["text"]
                and item["review"]["status"] == "unreviewed" and not entry["passages"]
                and all(m["role"] == "commentary" for m in entry["matches"]),
                "Changed evidence identity, content, review state or fabricated source anchor")
        seen.add(key)
        ranking.append(expected["document_id"])
    return ranking


def score_rankings(corpus, questions, rankings):
    result = evaluate_rankings(corpus, questions, {METHOD: rankings})
    report = result["methods"][METHOD]
    for row in report["questions"]:
        raw = rankings[row["id"]]
        require(len(raw) <= 10 and len(raw) == len(set(raw)), "Native rankings require at most ten distinct evidence records")
        row["native_ranking"] = raw
        if row["metrics"] is None:
            continue
        targets = set(row["expected_passages"])
        top1, top5 = canonical_ranking(corpus, raw[:1]), canonical_ranking(corpus, raw[:5])
        first = next((rank for rank, key in enumerate(raw[:10], 1)
                      if set(canonical_ranking(corpus, [key])) & targets), None)
        row["metrics"] = {"hit_at_1": float(bool(targets & set(top1))), "hit_at_5": float(bool(targets & set(top5))),
                          "recall_at_5": len(targets & set(top5)) / len(targets), "mrr_at_10": 1 / first if first else 0.0}
    for split in ("development", "reserved", "all"):
        rows = [r for r in report["questions"] if r["metrics"] is not None and (split == "all" or r["split"] == split)]
        report["aggregate"][split] = {"answerable_questions": len(rows),
            **{key: sum(r["metrics"][key] for r in rows) / len(rows) if rows else None
               for key in ("hit_at_1", "hit_at_5", "recall_at_5", "mrr_at_10")},
            "hit_at_5_numerator": sum(int(r["metrics"]["hit_at_5"]) for r in rows), "hit_at_5_denominator": len(rows)}
    return result


def run(args):
    from agent_pdf_workbench.service import AgentPdfWorkbenchService
    from scientific_tooling.server import HostedWorkflow
    from scientific_tooling.workspace import Workspace

    corpus, questions = load_corpus(args.corpus)
    fixture = read_json(args.fixture)
    validate_fixture(fixture, corpus, questions)
    verify_sources(corpus, args.cache, include_pdf=True)
    identity = candidate_identity(args.candidate_manifest)
    require(not args.run_dir.exists(), "Choose a new evaluation directory; preserve prior runs")
    args.run_dir.mkdir(parents=True)
    harness = retain_harness(args.run_dir)
    write_json(args.run_dir / "fixture.json", fixture)
    write_json(args.run_dir / "corpus.json", corpus)
    write_json(args.run_dir / "questions.json", questions)
    w = Workspace(args.run_dir / "project")
    w.create([source_path(args.cache, p, "pdf") for p in corpus["papers"]], "Frozen imported-evidence retrieval evaluation")
    w.prepare()
    service = AgentPdfWorkbenchService(w.root / "events.db")
    by_sha = {p["sha256"]: p for p in w.load()["papers"]}
    mapping, imports = {}, []
    timestamp = now()
    for paper in corpus["papers"]:
        selected = by_sha[paper["pdf"]["sha256"]]
        session = read_json(w.root / selected["handoff"])["apw"]["session_id"]
        entries = [e for e in fixture["entries"] if e["paper_id"] == paper["id"]]
        for entry in entries:
            service.upsert_note(session_id=session, note=note(entry, timestamp))
        preview = w.preview([], ["corpus-" + e["id"] for e in entries], selected["key"])
        applied = w.apply(preview["id"], paper=selected["key"])["result"]
        replay = w.apply(preview["id"], paper=selected["key"])["result"]
        require(applied["counts"]["added"] == len(entries) and replay["counts"]["unchanged"] == len(entries),
                "Native import or exact replay did not preserve the selected evidence set")
        by_object = {"corpus-" + e["id"]: e for e in entries}
        for imported in applied["items"]:
            entry = by_object[imported["id"]]
            require(imported["note_id"] not in mapping, "Native note ID collision")
            mapping[imported["note_id"]] = {"document_id": entry["id"], "canonical_id": entry["canonical_id"],
                "text": entry["text"], "source_key": imported["source_key"], "revision": imported["revision"],
                "paper_id": selected["paper_id"], "paper_key": selected["key"]}
        imports.append({"paper": paper["id"], "preview_id": preview["id"], "first": applied, "replay": replay})
    write_json(args.run_dir / "imports.json", {"note_to_document": mapping, "receipts": imports})
    data = w.load()
    # These files must remain byte-identical across read-only retrieval.
    observed = [w.file, w.root / "events.db", w.root / "rks/rks.sqlite3"]
    before = {str(p): sha_file(p) for p in observed}
    rankings, responses, timings = {}, [], []
    host = HostedWorkflow(w, service, "evaluation", "evaluation-only")
    for question in questions["questions"]:
        started = time.perf_counter()
        payload = w.search(question["question"], limit=10)
        seconds = time.perf_counter() - started
        require(payload["retrieval"]["method"] == "bm25-terms-v1", "Native ranking method changed")
        rankings[question["id"]] = map_results(payload, mapping, data)
        hosted = host.search({"session_id": host.session_id, "q": question["question"], "limit": "10"})
        require(map_results(hosted, mapping, data) == rankings[question["id"]], "CLI and hosted search differ")
        responses.append({"question_id": question["id"], "cli": payload, "hosted": hosted})
        timings.append({"question_id": question["id"], "seconds_including_cli_startup": seconds})
    empty = w.search("   ")
    reviewed = w.search("single cell", review="reviewed")
    require(empty["outcome"] == "empty_query" and not empty["results"] and not reviewed["results"],
            "Empty query or review filter returned unexpected records")
    filtered = w.search(questions["questions"][0]["question"], paper="p1", limit=100)
    map_results(filtered, mapping, data)
    require(all(e["paper"]["key"] == "p1" for e in filtered["results"]), "Paper filter leaked evidence")
    try:
        host.search({"session_id": "foreign-session", "q": "single cell"})
    except ValueError:
        foreign_rejected = True
    else:
        raise WorkflowError("Hosted search accepted a foreign session")
    require(before == {str(p): sha_file(p) for p in observed}, "Search modified source databases or project state")
    result = score_rankings(corpus, questions, rankings)
    result.update(schema="scientific-tooling.imported-evidence-evaluation.v1", fixture_revision=fixture["revision"],
                  candidate=identity, acceptance_gate="pending_independent_labels_and_new_held_out_questions",
                  endpoint="rks note search-evidence via sci Workspace.search and HostedWorkflow.search",
                  scope="Imported JATS excerpt notes, commentary role; no PDF passage anchors. Draft reference metrics only.",
                  precision=None, source_navigation_acceptance=False,
                  provenance={"python": sys.version, "platform": platform.platform(), "harness_sha256": harness,
                              "native_result_policy": fixture["ranking_policy"], "timings": timings,
                              "hosted_scope": "Real hosted handler calls; HTTP transport/browser not measured here"},
                  checks={"read_only_bytes_unchanged": True, "exact_replay": True, "cli_hosted_same_rankings": True,
                          "empty_query": True, "review_filter": True, "paper_filter": True, "foreign_session_rejected": foreign_rejected})
    write_json(args.run_dir / "native-responses.json", {"queries": responses, "empty": empty, "reviewed": reviewed, "paper": filtered})
    write_json(args.run_dir / "rankings.json", {"fixture_revision": fixture["revision"], "methods": {METHOD: rankings}})
    write_json(args.run_dir / "results.json", result)
    return {"path": str(args.run_dir.resolve()), "records": len(mapping), "questions": len(rankings),
            "draft_metrics": result["methods"][METHOD]["aggregate"]["all"], "acceptance_gate": result["acceptance_gate"]}


def comparison_sources(comparison, corpus):
    papers = {p["pdf"]["sha256"]: p for p in corpus["papers"]}
    evidence = {}
    for cell in comparison["cells"]:
        require(cell["text"] and cell["origin"] in {"agent", "human"}, "Comparison has an empty or unknown-origin interpretation")
        for entry in cell["evidence"]:
            record, item = entry["record"], entry["record"]["item"]
            source = record["document"]
            require(source["sha256"] in papers, "Comparison source is outside the frozen corpus")
            require(record["workspace_id"] == comparison["workspace_id"]
                    and record["source"]["source_id"] == comparison["source_id"]
                    and cell["paper_source"] == f"{record['paper_id']}:{source['sha256']}", "Comparison support crosses project/source scope")
            require(entry["revision"] == item["revision"] == digest({k: v for k, v in item.items() if k != "revision"}),
                    "Comparison evidence revision mismatch")
            verify_bytes(Path(source["path"]), papers[source["sha256"]]["pdf"])
            for passage in entry["passages"]:
                require(passage["available"] and passage["page"] > 0 and passage["quote"].strip(), "Unavailable comparison passage")
            require(entry["passages"], "Comparison evidence has no source passage")
            key = entry["source_key"]
            retained = {"note_id": entry["note_id"], "revision": entry["revision"], "source_key": key,
                        "record": record, "passages": entry["passages"], "attribution": papers[source["sha256"]]}
            require(key not in evidence or evidence[key] == retained, "Same source identity has inconsistent revisions")
            evidence[key] = retained
    return list(evidence.values())


def packet_data(fixture, corpus, questions, comparison, identity, workspace):
    validate_fixture(fixture, corpus, questions)
    evidence = comparison_sources(comparison, corpus)
    return seal({"schema": PACKET, "fixture_revision": fixture["revision"], "corpus_revision": digest(corpus),
                 "questions_revision": digest(questions), "candidate": identity, "created_at": now(),
                 "workspace": str(workspace), "comparison": comparison, "evidence": evidence,
                 "questions": questions["questions"], "sources": corpus["papers"], "entries": fixture["entries"],
                 "review_state": "pending", "reader_link_status": "Saved URLs require the original reader at its recorded port; this packet does not launch it or verify browser matching.",
                 "review_scope": ["answerability and all relevant passages", "numeric values and units", "negation", "experimental unit", "conditions and applicability", "contradictions and limitations"]})


def response_template(packet):
    return {"schema": "scientific-tooling.imported-evidence-review-response.v1", "packet_revision": packet["revision"],
            "records": [{"kind": kind, "id": item[key], "target_revision": digest(item), "decision": "pending",
                         "method": None, "reviewer": None, "reviewed_at": None, "independent_of_implementation": None,
                         "notes": ""}
                        for kind, items, key in (("question", packet["questions"], "id"),
                                                 ("comparison_cell", packet["comparison"]["cells"], "key")) for item in items],
            "held_out_questions": [],
            "held_out_instructions": "At least ten NEW questions must be authored by a human who did not tune retrieval, then frozen before running them. Leave this empty until such questions exist. Public reserved questions do not count. This validator reports submitted questions but does not certify or evaluate them."}


def review_status(packet, response):
    check_seal(packet, PACKET)
    require(response.get("schema") == "scientific-tooling.imported-evidence-review-response.v1"
            and response.get("packet_revision") == packet["revision"], "Stale or foreign review response")
    targets = {(r["kind"], r["id"]): r["target_revision"] for r in response_template(packet)["records"]}
    seen, counts = set(), {"pending": 0, "approved": 0, "revise": 0, "exclude": 0}
    for record in response["records"]:
        key = (record["kind"], record["id"])
        require(key in targets and key not in seen and record["target_revision"] == targets[key], "Unknown, duplicate or changed review target")
        decision = record["decision"]
        require(decision in counts, "Unknown review decision")
        if decision != "pending":
            require(record["method"] == "human" and record["independent_of_implementation"] is True
                    and all(isinstance(record.get(k), str) and record[k].strip() for k in ("reviewer", "reviewed_at", "notes")),
                    "Completed reviews require actual independent human provenance and substantive notes")
            require(datetime.fromisoformat(record["reviewed_at"]).utcoffset() is not None,
                    "Review timestamp requires timezone")
        else:
            require(all(record.get(k) is None for k in ("method", "reviewer", "reviewed_at", "independent_of_implementation")),
                    "Pending reviews cannot assert completed reviewer provenance")
        counts[decision] += 1
        seen.add(key)
    require(seen == set(targets), "Review response must retain every question and comparison cell")
    require(isinstance(response.get("held_out_questions"), list), "Held-out questions must be a separate list")
    return {"counts": counts, "all_targets_approved": counts["approved"] == len(targets),
            "held_out_submissions": len(response["held_out_questions"]), "held_out_evaluation": "not_performed",
            "release_gate_passed": False, "scientific_accuracy": None,
            "provenance": "Caller assertions, not authenticated identities. This command never writes scientific review into RKS."}


def render_packet(packet):
    from html import escape
    esc = lambda s: escape(str(s), quote=False).replace("\n", "\n> ")
    lines = ["# Imported evidence and comparison review", "", "Independent review pending. No approvals have been recorded by this packet.", "",
             "Review question relevance and comparison claims against the attributed sources. Check answerability, all relevant passages, values and units, negation, experimental unit, conditions, applicability, contradictions and limitations. Record decisions in a copy of responses.json; retain pending fields until an actual review occurs.", "",
             f"Packet revision: `{packet['revision']}`. Candidate: `{packet['candidate']['candidate']}`.", "",
             "JATS excerpt notes below have no verified PDF page anchor. Their selector, original XML fingerprint and exact source slice are retained in packet.json. PDF comparison passages have separately retained page/annotation identities.", "",
             "## Review questions", ""]
    entries = {e["id"]: e for e in packet["entries"]}
    papers = {p["id"]: p for p in packet["sources"]}
    for q in packet["questions"]:
        lines += [f"### {q['id']} {esc(q['question'])}", "", f"Public split: {q['split']}; draft answerable: {q['answerable_from_excerpts']}.", "",
                  f"Agent draft answer: {esc(q['draft_answer'])}", "", f"Required qualifications: {esc('; '.join(q['required_qualifications']))}", ""]
        for key in q["expected_passages"]:
            e, p = entries[key], papers[entries[key]["paper_id"]]
            anchor = "passage-" + "".join(c for c in key.lower() if c.isalnum() or c == "-")
            lines += [f"Draft relevance target [{key}](#{anchor}). [{esc(p['title'])}]({p['source_url']}); selector `{e['source']['selector']}`.", ""]
        if not q["expected_passages"]:
            lines += ["Draft reference says insufficient evidence. Review this explicitly; an empty target list is not an abstention score.", ""]
    lines += ["## Complete excerpt set", "", "Inspect every candidate when checking relevance, including passages absent from the draft target lists. The extra whitespace representation is retained in packet.json and earns no additional evidence credit.", ""]
    for e in packet["entries"]:
        if e["id"] != e["canonical_id"]:
            continue
        p = papers[e["paper_id"]]
        lines += [f"### Passage {e['id']}", "", f"[{esc(p['title'])}]({p['source_url']}); JATS selector `{e['source']['selector']}`; transform `{e['source']['transform']}`.", ""]
        if e["source"]["kind"] == "table":
            lines += ["Exact tab-separated table excerpt; headers, row boundaries, units and footnotes are retained:", "", "```text", e["text"], "```", ""]
        else:
            lines += [f"Source slice [{e['source']['start']}, {e['source']['end']}); excerpt SHA-256 `{e['source']['sha256']}`.", "", "> " + esc(e["text"]), ""]
    lines += ["## Comparison review", "", f"{esc(packet['comparison']['title'])}. Comparison revision `{packet['comparison']['revision']}`.", ""]
    criteria = {c["id"]: c["label"] for c in packet["comparison"]["criteria"]}
    supports = {e["source_key"]: e for e in packet["evidence"]}
    for cell in packet["comparison"]["cells"]:
        lines += [f"### {esc(cell['paper']['title'])} — {esc(criteria[cell['criterion_id']])}", "",
                  f"Origin: {cell['origin']}; current review: {cell['review']['status']}; cell revision `{cell['cell_revision']}`.", "",
                  "Interpretation: " + esc(cell["text"]), "", "Conditions: " + esc(cell["conditions"]), ""]
        for e in cell["evidence"]:
            entry = supports[e["source_key"]]
            p = entry["attribution"]
            lines += [f"Evidence `{entry['note_id']}` revision `{entry['revision']}`; imported review `{entry['record']['item']['review']['status']}`.", ""]
            for passage in entry["passages"]:
                lines += [f"> PDF page {passage['page']}: {esc(passage['quote'])}", "",
                          f"[Publisher PDF page]({p['pdf']['url']}#page={passage['page']}) · [Article]({p['publisher_url']})", ""]
                if passage.get("url"):
                    lines += [f"[Exact retained reader passage]({passage['url']}) (requires original local reader).", ""]
    lines += ["## Source attribution", "", "Selected author text and tables retain their authors' CC BY 4.0 licenses. No PDFs or third-party images are bundled. JATS transforms/slices and the deliberate whitespace duplicate remain recorded in packet.json.", ""]
    for p in packet["sources"]:
        lines += [f"- {esc('; '.join(p['authors']))}. {esc(p['title'])}. [DOI]({p['publisher_url']}); [license]({p['license']['url']}). PDF SHA-256 `{p['pdf']['sha256']}`; XML SHA-256 `{p['xml']['sha256']}`."]
    lines += ["", "## New held-out questions", "", "A reviewer who did not tune retrieval must author at least ten new questions and source targets. Keep them separate and freeze them before scoring. The six public reserved questions are regressions, not blind tests.", ""]
    return "\n".join(lines)


def make_packet(args):
    from scientific_tooling.workspace import Workspace
    corpus, questions = load_corpus(args.corpus)
    fixture = read_json(args.fixture)
    validate_fixture(fixture, corpus, questions)
    verify_sources(corpus, args.cache, include_pdf=True)
    identity = candidate_identity(args.candidate_manifest)
    require(not args.output.exists(), "Choose a new review packet directory")
    workspace = Workspace(args.workspace)
    before = workspace.compare("show", comparison_id=args.comparison_id)["comparison"]
    packet = packet_data(fixture, corpus, questions, before, identity, workspace.root)
    after = workspace.compare("show", comparison_id=args.comparison_id)["comparison"]
    require(before == after, "Comparison/support changed during capture; no packet was published")
    args.output.mkdir(parents=True)
    write_json(args.output / "harness.json", retain_harness(args.output))
    write_json(args.output / "packet.json", packet)
    response = response_template(packet)
    write_json(args.output / "responses.json", response)
    write_json(args.output / "status.json", review_status(packet, response))
    (args.output / "review.md").write_text(render_packet(packet), encoding="utf-8")
    return {"path": str(args.output.resolve()), "questions": len(packet["questions"]),
            "cells": len(before["cells"]), "unique_evidence": len(packet["evidence"]), "review_state": "pending"}


def check_packet(args):
    from scientific_tooling.workspace import Workspace
    packet = read_json(args.packet)
    check_seal(packet, PACKET)
    identity = candidate_identity(args.candidate_manifest)
    require(identity == packet["candidate"], "Use the same installed candidate to check this packet")
    workspace = Workspace(Path(packet["workspace"]))
    current = workspace.compare("show", comparison_id=packet["comparison"]["id"])["comparison"]
    # Explicitly check retained bytes as well as current RKS/APW revisions.
    comparison_sources(current, {"papers": packet["sources"]})
    changed = current != packet["comparison"]
    return {"packet_revision": packet["revision"], "checked_at": now(),
            "freshness": "outdated" if changed else "current",
            "comparison_or_support_changed": changed, "review_approval": "not_inferred",
            "scope": "Comparison, source bytes and APW passage identities; does not verify browser text matching or scientific validity."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    commands = parser.add_subparsers(dest="command", required=True)
    freeze = commands.add_parser("freeze")
    freeze.add_argument("--output", type=Path, required=True)
    for name in ("run", "review-packet"):
        command = commands.add_parser(name)
        command.add_argument("--fixture", type=Path, required=True)
        command.add_argument("--cache", type=Path, required=True)
        command.add_argument("--candidate-manifest", type=Path, required=True)
        if name == "run":
            command.add_argument("--run-dir", type=Path, required=True)
        else:
            command.add_argument("--workspace", type=Path, required=True)
            command.add_argument("--comparison-id", required=True)
            command.add_argument("--output", type=Path, required=True)
    status = commands.add_parser("review-status")
    status.add_argument("packet", type=Path)
    status.add_argument("responses", type=Path)
    check = commands.add_parser("check-packet")
    check.add_argument("packet", type=Path)
    check.add_argument("--candidate-manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze":
            result = make_fixture(*load_corpus(args.corpus))
            write_json(args.output, result)
            result = {"path": str(args.output), "revision": result["revision"], "records": len(result["entries"])}
        elif args.command == "run":
            result = run(args)
        elif args.command == "review-packet":
            result = make_packet(args)
        elif args.command == "check-packet":
            result = check_packet(args)
        else:
            result = review_status(read_json(args.packet), read_json(args.responses))
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": "imported_evidence_evaluation_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 2 if result.get("freshness") == "outdated" else 0


if __name__ == "__main__":
    raise SystemExit(main())
