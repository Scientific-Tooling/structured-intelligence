"""Exercise a disposable legacy project at one absolute path, retaining both states."""
from __future__ import annotations

import hashlib
import importlib.metadata as metadata
import json
import sys
import zipfile
from pathlib import Path

from agent_pdf_workbench.service import AgentPdfWorkbenchService
from scientific_tooling import server
from scientific_tooling.workspace import Workspace

ROOT = Path(__file__).resolve().parents[3] / ".development-candidate/2026-10-29-c1/upgrade-v2"
PROJECT = ROOT / "project"


def inventory():
    return {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in PROJECT.rglob("*") if p.is_file()}


def save(name, value):
    with (ROOT / name).open("x", encoding="utf-8") as f:
        json.dump(value, f, indent=2)
        f.write("\n")


def create():
    ROOT.mkdir(exist_ok=False)
    # Reuse the installed browser fixture PDF, whose construction is in its frozen test.
    source = ROOT.parent / "browser-workflow/input paper.pdf"
    w = Workspace(PROJECT)
    w.create(source, "Candidate upgrade engineering fixture")
    w.prepare()
    try:
        state = server.ensure_running(w)
        service = AgentPdfWorkbenchService(db_path=PROJECT / "events.db")
        service.upsert_annotation(session_id=state["session_id"], annotation={
            "id": "ann_upgrade", "page": 1, "type": "highlight", "quote": "Reading workflow test source.",
            "comment": "Unreviewed upgrade fixture", "anchor": None, "rects": [], "tags": [],
            "createdAt": "2026-10-29T16:00:00+00:00", "updatedAt": "2026-10-29T16:00:00+00:00"})
        preview = w.preview(["ann_upgrade"], [])
        w.apply(preview["id"])
        w.make_brief()
        summary = w.summary()
    finally:
        stopped = server.stop(w)
    assert server.running(w, detailed=False) is None
    before = inventory()
    with zipfile.ZipFile(ROOT / "stopped-0.3.1.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in before:
            archive.write(PROJECT / relative, relative)
    assert inventory() == before
    save("legacy.json", {"version": metadata.version("scientific-tooling"),
         "packages": {p: metadata.distribution(p).read_text("direct_url.json") for p in
                      ("scientific-tooling", "agent-pdf-workbench", "research-knowledge-substrate")},
         "project": str(PROJECT), "stopped": stopped, "summary": summary, "files": before,
         "archive_sha256": hashlib.sha256((ROOT / "stopped-0.3.1.zip").read_bytes()).hexdigest()})


def upgrade():
    from scientific_tooling import maintenance
    before = json.loads((ROOT / "legacy.json").read_text(encoding="utf-8"))
    assert inventory() == before["files"]
    w = Workspace(PROJECT)
    try:
        w.prepare()
        state = server.ensure_running(w)
        summary = w.summary()
        assert summary["brief"]["text"] == before["summary"]["brief"]["text"]
        # Explicit creation is the supported RKS 0015 migration operation.
        comparison = w.compare("create", payload={"title": "Upgrade fixture", "criteria": ["Method"]})
        results = w.search("source")
        assert len(results["results"]) == 1
        batch = w.load()["papers"][0]["batch_id"]
        w.apply(batch)
        assert len(w.search("source")["results"]) == 1
        history = maintenance.history(w)
        assert Path(before["summary"]["brief"]["path"]).read_text(encoding="utf-8") == before["summary"]["brief"]["text"]
    finally:
        stopped = server.stop(w)
    assert server.running(w, detailed=False) is None
    save("candidate.json", {"candidate": "2026-10-29-c1", "version": metadata.version("scientific-tooling"),
         "stopped": stopped, "comparison": comparison, "search": results, "history": history,
         "legacy_brief_preserved": True, "exact_import_replay_count": 1, "files": inventory()})


def restore():
    assert metadata.version("scientific-tooling") == "0.3.1"
    w = Workspace(PROJECT)
    assert server.running(w, detailed=False) is None
    receipt = json.loads((ROOT / "legacy.json").read_text(encoding="utf-8"))
    archive = ROOT / "stopped-0.3.1.zip"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == receipt["archive_sha256"]
    # Retain the upgraded project; only this explicitly named disposable project moves.
    assert PROJECT.resolve().parent == ROOT.resolve()
    retained = ROOT / "candidate-project-retained"
    assert not retained.exists()
    PROJECT.rename(retained)
    with zipfile.ZipFile(archive) as zipped:
        assert all((PROJECT / p).resolve().is_relative_to(PROJECT.resolve()) for p in zipped.namelist())
        zipped.extractall(PROJECT)
    assert inventory() == receipt["files"]
    summary = Workspace(PROJECT).summary()
    assert summary["brief"]["text"] == receipt["summary"]["brief"]["text"]
    assert inventory() == receipt["files"]
    save("restore.json", {"same_path": str(PROJECT), "restored_hashes_match": True,
         "legacy_summary_reopened": True, "legacy_brief_bytes_match": True,
         "mutated_candidate_retained": str(retained)})


if __name__ == "__main__":
    {"create": create, "upgrade": upgrade, "restore": restore}[sys.argv[1]]()
    print(json.dumps({"step": sys.argv[1], "passed": True}), flush=True)
