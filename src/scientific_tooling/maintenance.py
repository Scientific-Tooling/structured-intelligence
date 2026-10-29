"""Project change reports and immutable brief editions through public evidence contracts."""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import sys
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from . import brief, comparison
from .reading import WorkflowError, hash_stream
from .state import lock, read_json, write_json

SNAPSHOT = "scientific-tooling.project-snapshot.v1"
EDITION = "scientific-tooling.brief-edition.v1"
REPORT = "scientific-tooling.project-update.v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{32}", value):
        raise WorkflowError("Use an edition or request ID from this project's history.")
    return value


def seal(value):
    return {**value, "revision": brief.digest(value)}


def verified(path, schema, workspace_id):
    value = read_json(path)
    if (value.get("schema") != schema or value.get("workspace_id") != workspace_id
            or value.get("revision") != brief.digest({k: v for k, v in value.items() if k != "revision"})):
        raise WorkflowError(f"Saved project history changed or belongs to another project: {path}")
    return value


def read_rks_state(workspace, data):
    """Use the same native operations as RKS's CLI, in one read-only observation.

    Pass the project path/scope explicitly; never change process-wide RKS config
    or initialize a database. The next capture opens a new transaction.
    """
    sources, evidence, comparisons = {}, [], []
    if not any(p["paper_id"] for p in data["papers"]):
        return sources, evidence, comparisons
    from rks.operations.comparison import list_comparisons, list_evidence, show_comparison
    from rks.operations.paper_source import describe_paper_source
    from rks.storage.db import connect_db_readonly
    from rks.storage.paper_repository import PaperRepository
    try:
        with closing(connect_db_readonly(workspace.root / "rks" / "rks.sqlite3")) as conn:
            conn.execute("BEGIN")
            for paper in data["papers"]:
                if paper["paper_id"]:
                    try:
                        sources[paper["paper_id"]] = describe_paper_source(PaperRepository(conn).get_paper(paper["paper_id"]))
                    except (OSError, ValueError, KeyError):
                        sources[paper["paper_id"]] = None
            if all(p["paper_id"] for p in data["papers"]):
                scope = {"workspace_id": data["workspace_id"], "source_id": data["source_id"],
                         "paper_sources": [f"{p['paper_id']}:{p['sha256']}" for p in data["papers"]]}
                evidence = list_evidence(conn, **scope)["evidence"]
                comparisons = [show_comparison(conn, item["id"], **scope)
                               for item in list_comparisons(conn, **scope)["comparisons"]]
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        raise WorkflowError(f"Cannot inspect this project's RKS state: {exc}") from exc
    return sources, evidence, comparisons


def capture(workspace):
    """Retain imported records, current availability and exact comparison/review states."""
    data = workspace.load()
    native_sources, native_evidence, native_comparisons = read_rks_state(workspace, data)
    papers = []
    for paper in data["papers"]:
        source = workspace.root / "pdfs" / (paper["sha256"] + ".pdf")
        status = "available"
        try:
            with source.open("rb") as stream:
                if hash_stream(stream) != (paper["sha256"], paper["size_bytes"]):
                    status = "changed"
        except FileNotFoundError:
            status = "missing"
        if paper["paper_id"]:
            try:
                native = native_sources[paper["paper_id"]]
                if native is None:
                    raise WorkflowError("RKS source unavailable")
                from .reading import validate_source
                descriptor = validate_source(native, paper["paper_id"])
                if (descriptor["sha256"], descriptor["size_bytes"]) != (paper["sha256"], paper["size_bytes"]):
                    status = "rks_source_changed"
            except WorkflowError:
                status = "rks_source_unavailable"
        papers.append({**{k: paper.get(k) for k in ("key", "title", "paper_id", "sha256", "size_bytes", "work_id")},
                       "source_status": status, "prepared": paper["phase"] != "initializing"})
    evidence, comparisons = [], []
    if papers and all(p["paper_id"] for p in papers):
        from agent_pdf_workbench.evidence import export_evidence
        from agent_pdf_workbench.passage import resolve_passage

        evidence = native_evidence
        paper_scope = {f"{p['paper_id']}:{p['sha256']}": p for p in data["papers"]}
        # APW owns these read-only APIs. Avoid starting a Python process per item
        # or constructing its service (which initializes/migrates the database).
        # This cache belongs to one observation; stable_snapshot reads again.
        checked = {}
        db_path = workspace.root / "events.db"
        def resolver(**citation):
            try:
                return resolve_passage(db_path, **citation)
            except sqlite3.Error as exc:
                raise WorkflowError(str(exc)) from exc
        apw = [sys.executable, "-m", "agent_pdf_workbench.dev_cli", "--db-path", str(workspace.root / "events.db")]
        for entry in evidence:
            record, item = entry["record"], entry["record"]["item"]
            paper = paper_scope[f"{record['paper_id']}:{record['document']['sha256']}"]
            entry["paper"] = {k: paper[k] for k in ("key", "title")}
            entry["paper_id"] = record["paper_id"]
            entry["passages"] = brief.checked_passages(apw, record,
                f"http://127.0.0.1:{data['port']}" if data["port"] else None, checked, resolver=resolver)
            entry["reading_item"] = None
            try:
                exported = export_evidence(db_path, session_id=record["source"]["session_id"],
                    source_id=data["source_id"], annotation_ids=[item["id"]] if item["kind"] == "annotation" else [],
                    note_ids=[item["id"]] if item["kind"] == "note" else [])
                if (exported.get("workspace_id") != data["workspace_id"]
                        or exported.get("paper_id") != record["paper_id"]
                        or exported["document"]["sha256"] != record["document"]["sha256"]):
                    raise WorkflowError("Reading export is outside this project's exact source scope.")
                entry["reading_status"] = ("unchanged" if exported["items"][0]["content_revision"] == item["content_revision"]
                                           else "changed_since_import")
                entry["reading_item"] = exported["items"][0]
            except (WorkflowError, OSError, ValueError, sqlite3.Error):
                entry["reading_status"] = "unavailable"
        for item in native_comparisons:
            comparisons.append(comparison.enrich(workspace, item, data, paper_scope,
                                                  checked=checked, resolver=resolver))
    elif any(p["paper_id"] for p in papers):
        raise WorkflowError("Resume the interrupted paper selection before checking project changes.")
    snapshot = {"schema": SNAPSHOT, "workspace_id": data["workspace_id"], "source_id": data["source_id"],
                "question": data["question"], "reader_port": data["port"], "papers": papers,
                "works": data.get("works", []), "evidence": sorted(evidence, key=lambda e: e["source_key"]),
                "comparisons": sorted(comparisons, key=lambda c: c["id"])}
    if workspace.load() != data:
        raise WorkflowError("The project changed during inspection. Check changes again after the active operation finishes.")
    return seal(snapshot)


def stable_snapshot(workspace):
    first = capture(workspace)
    if first != capture(workspace):
        raise WorkflowError("Sources or interpretations changed during inspection. Retry when editing has finished.")
    return first


def editions(workspace):
    data = workspace.load()
    records = []
    for path in (workspace.root / "briefs").glob("*/record.json"):
        record = verified(path, EDITION, data["workspace_id"])
        if record["id"] != identity(path.parent.name):
            raise WorkflowError("Brief edition identity does not match its saved directory.")
        records.append(record)
    return sorted(records, key=lambda r: (r["created_at"], r["id"]))


def history(workspace, edition_id=None):
    if edition_id:
        path = workspace.root / "briefs" / identity(edition_id) / "record.json"
        if not path.is_file():
            raise WorkflowError("Brief edition not found in this project.")
        result = verified(path, EDITION, workspace.load()["workspace_id"])
        if result["id"] != edition_id:
            raise WorkflowError("Brief edition identity does not match its saved directory.")
        return result
    records = editions(workspace)
    pending = []
    known = {r["id"] for r in records}
    for path in (workspace.root / "briefs").glob("*/request.json"):
        request = verified(path, "scientific-tooling.brief-request.v1", workspace.load()["workspace_id"])
        if request["id"] != identity(path.parent.name):
            raise WorkflowError("Brief request identity does not match its directory.")
        if request["id"] not in known:
            pending.append(request["id"])
    return {"schema": "scientific-tooling.project-history.v1",
            "editions": [{k: r[k] for k in ("id", "created_at", "revision", "result")} for r in reversed(records)],
            "pending_briefs": pending,
            "legacy_briefs": [{"path": str(p), "freshness": "unverified"} for p in sorted((workspace.root / "briefs").glob("*.md"))]}


def difference(before, after, key, category):
    old, new = {v[key]: v for v in before}, {v[key]: v for v in after}
    return [{"category": category, "id": k,
             "change": "added" if k not in old else "removed" if k not in new else "changed",
             "before": old.get(k), "after": new.get(k)}
            for k in sorted(old.keys() | new.keys()) if old.get(k) != new.get(k)]


def report(workspace, snapshot):
    records = editions(workspace)
    previous = records[-1] if records else None
    baseline = previous["snapshot"] if previous else {}
    changes = []
    for name, key in (("papers", "key"), ("works", "id"), ("evidence", "source_key"), ("comparisons", "id")):
        changes += difference(baseline.get(name, []), snapshot[name], key, name)
    if previous and any(baseline.get(k) != snapshot[k] for k in ("question", "reader_port")):
        changes.append({"category": "project", "id": snapshot["workspace_id"], "change": "changed",
                        "before": {k: baseline.get(k) for k in ("question", "reader_port")},
                        "after": {k: snapshot[k] for k in ("question", "reader_port")}})
    attention = []
    for paper in snapshot["papers"]:
        if paper["source_status"] != "available" or not paper["prepared"]:
            attention.append({"kind": "source", "paper": paper["key"], "id": paper["sha256"],
                              "message": f"Retained source is {paper['source_status']}; prepared: {paper['prepared']}."})
    for entry in snapshot["evidence"]:
        reasons = []
        if entry["status"] != "current":
            reasons.append(entry["status"])
        if entry["source_status"] != "available":
            reasons.append(entry["source_status"])
        if entry["reading_status"] != "unchanged":
            reasons.append("reading_" + entry["reading_status"])
        if any(not p["available"] for p in entry["passages"]):
            reasons.append("supporting_passage_unavailable")
        if reasons:
            attention.append({"kind": "evidence", "paper": entry["paper"]["key"], "id": entry["note_id"],
                              "message": "; ".join(reasons), "revision": entry["revision"]})
    changed_reading = {e["source_key"] for e in snapshot["evidence"] if e["reading_status"] != "unchanged"}
    for item in snapshot["comparisons"]:
        for cell in item["cells"]:
            reading_changed = any(e["source_key"] in changed_reading for e in cell["evidence"])
            if cell["text"].strip() and (cell["support_status"] != "linked" or cell["review"]["status"] != "accepted" or reading_changed):
                attention.append({"kind": "interpretation", "id": item["id"], "cell": cell["key"],
                                  "paper": cell["paper"]["key"], "text": cell["text"],
                                  "message": f"Support: {cell['support_status']}; review: {cell['review']['status']}."
                                  + (" Supporting reading material changed or is unavailable; inspect before reusing this interpretation." if reading_changed else "")})
        if item["excluded_papers"]:
            attention.append({"kind": "coverage", "id": item["id"],
                              "message": "Comparison excludes later papers: " + ", ".join(item["excluded_papers"])})
    return {"schema": REPORT, "workspace_id": snapshot["workspace_id"], "checked_at": now(),
            "baseline_id": previous["id"] if previous else None,
            "freshness": ("current" if baseline.get("revision") == snapshot["revision"] else "outdated") if previous else "unverified",
            "snapshot_revision": snapshot["revision"], "changes": changes, "attention": attention,
            "history": history(workspace)}


def inspect(workspace, *, save=False):
    snapshot = stable_snapshot(workspace)
    result = report(workspace, snapshot)
    if save:
        result["id"] = uuid.uuid4().hex
        path = workspace.root / "updates" / (result["id"] + ".json")
        path.parent.mkdir(exist_ok=True)
        write_json(path, seal({**result, "snapshot": snapshot}))
        result["path"] = str(path)
    return result


def make_brief(workspace, request_id=None):
    request_id = identity(request_id or uuid.uuid4().hex)
    with lock(workspace.root / "workspace.lock"):
        data = workspace.load()
        directory = workspace.root / "briefs" / request_id
        directory.mkdir(parents=True, exist_ok=True)
        request_path = directory / "request.json"
        if request_path.exists():
            request = verified(request_path, "scientific-tooling.brief-request.v1", data["workspace_id"])
            if request["id"] != request_id:
                raise WorkflowError("Brief request identity changed.")
        else:
            write_json(request_path, seal({"schema": "scientific-tooling.brief-request.v1", "workspace_id": data["workspace_id"],
                                          "id": request_id, "created_at": now()}))
        record_path = directory / "record.json"
        replayed = record_path.exists()
        if replayed:
            record = verified(record_path, EDITION, data["workspace_id"])
        else:
            try:
                record = render_edition(workspace, request_id, directory)
                write_json(record_path, record)  # Commit point: text and provenance publish together.
            except (WorkflowError, OSError, ValueError) as exc:
                raise WorkflowError(f"{exc}\nBrief request retained: {request_id}. Retry sci brief --request-id {request_id}.") from exc
        target = directory / "brief.md"
        if target.exists():
            if target.read_text(encoding="utf-8") != record["text"]:
                raise WorkflowError("Saved brief text changed. Preserve it and inspect its edition record.")
        else:
            # The canonical record already contains the whole output. An interrupted
            # convenience-file publication can be recovered from that exact edition.
            from .state import replace
            pending = directory / ".brief.md"
            pending.write_text(record["text"], encoding="utf-8")
            replace(pending, target)
        latest = editions(workspace)[-1]
        data["brief"] = latest["result"]
        workspace.save(data)
        return {**record["result"], "replayed": replayed}


def render_edition(workspace, edition_id, directory):
    data = workspace.load()
    if not data["port"] or not data["papers"] or any(p["phase"] == "initializing" for p in data["papers"]):
        raise WorkflowError("Resume the reader and finish preparing the selected papers before generating a brief.")
    snapshot = capture(workspace)
    sections, coverage = [], []
    counts = dict.fromkeys(("evidence", "reviewed", "unreviewed", "linked_passages", "unavailable_passages"), 0)
    for paper in data["papers"]:
        entries = [e for e in snapshot["evidence"] if e["paper"]["key"] == paper["key"]]
        args = argparse.Namespace(paper_id=paper["paper_id"], question=data["question"], workspace_id=data["workspace_id"],
            rks_data_dir=workspace.root / "rks", source_id=data["source_id"], apw_db=workspace.root / "events.db",
            rks_note_id=[], viewer_url=f"http://127.0.0.1:{data['port']}", output=directory / "brief.md",
            rks_python=Path(sys.executable), apw_python=Path(sys.executable))
        text, rendered = brief.render_brief(args, allow_empty=True,
            evidence_payload={"paper_id": paper["paper_id"], "evidence": entries})
        for key in counts:
            counts[key] += rendered["counts"][key]
        coverage.append({"key": paper["key"], "paper_id": paper["paper_id"], "title": paper["title"], "counts": rendered["counts"]})
        body = re.sub(r"^(#+) ", r"#\1 ", text.split("\n", 1)[1], flags=re.MULTILINE)
        sections.append(f"## {brief.escape(paper['key'] + ': ' + paper['title'])}\n" + body)
    if not counts["evidence"]:
        raise WorkflowError("No matching imported evidence. Preview and import selected material first.")
    checked_at = now()
    lines = ["# Source-linked project brief", "", f"Question: {brief.escape(data['question'])}", "",
             f"Edition: {edition_id}. Captured at {checked_at}.",
             f"Project snapshot: {snapshot['revision']}.", "",
             "This is a retained edition. Run sci changes to check freshness before using it for a new decision.", "",
             "No agreement, contradiction, or scientific conclusion is inferred.", "", "## Coverage", "",
             "| Paper | Evidence | Reviewed | Unreviewed | Linked passages | Unavailable |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for paper in coverage:
        c = paper["counts"]
        lines.append(f"| {brief.escape(paper['key'] + ': ' + paper['title']).replace(chr(10), ' ')} | {c['evidence']} | {c['reviewed']} | {c['unreviewed']} | {c['linked_passages']} | {c['unavailable_passages']} |")
    lines += ["", "Papers without imported evidence remain coverage gaps, not negative findings.", "", *sections]
    for item in snapshot["comparisons"]:
        lines += ["", "## Retained comparison", "", re.sub(r"^(#+) ", r"##\1 ", item["markdown"], flags=re.MULTILINE)]
    if snapshot != capture(workspace):
        raise WorkflowError("Project inputs changed while generating this brief. No edition was published; retry after editing finishes.")
    text = "\n".join(lines)
    result = {"schema": "scientific-tooling.project-brief.v1", "id": edition_id, "created_at": checked_at,
              "path": str(directory / "brief.md"), "counts": counts, "papers": coverage, "paper_count": len(coverage),
              "snapshot_revision": snapshot["revision"], "freshness": "unchecked"}
    return seal({"schema": EDITION, "workspace_id": data["workspace_id"], "id": edition_id, "created_at": checked_at,
                 "snapshot": snapshot, "result": result, "text": text,
                 "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()})


def register(commands):
    for name in ("changes", "update", "history"):
        parser = commands.add_parser(name, help={"changes": "Inspect changes since the last retained brief without writes.",
            "update": "Save a project change report without importing or reviewing evidence.",
            "history": "List retained brief editions or inspect an exact edition."}[name])
        parser.add_argument("--workspace", type=Path, default=Path("review"))
        parser.add_argument("--json", action="store_true")
        if name == "history":
            parser.add_argument("edition_id", nargs="?")
