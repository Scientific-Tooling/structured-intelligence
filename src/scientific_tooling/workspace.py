"""Orchestration through RKS/APW contracts; scientific review remains explicit."""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from pathlib import Path

from . import brief, evidence, reading
from .reading import WorkflowError, hash_stream, run_json
from .state import lock, read_json, write_json

SCHEMA = "scientific-tooling.workspace.v1"


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.file = self.root / "workspace.json"

    def load(self) -> dict:
        if not self.file.is_file():
            raise WorkflowError("Workspace not found. Use start with a PDF and question first.")
        data = read_json(self.file)
        if data.get("schema") != SCHEMA:
            raise WorkflowError("Unsupported workspace format. Preserve this directory and use a compatible version.")
        if data.get("root") != str(self.root):
            raise WorkflowError("Workspace was moved. Keep its original path; its retained source links use that path.")
        return data

    def save(self, data: dict) -> None:
        write_json(self.file, data)

    def rks(self, *args: str, codes=(0,)) -> dict:
        return run_json([sys.executable, "-m", "rks", *args], env={
            "RKS_DATA_DIR": str(self.root / "rks"), "RKS_AUTO_EXTRACT_MODE": "none",
        }, accepted_returncodes=codes)

    def apw(self, *args: str) -> dict:
        return run_json([sys.executable, "-m", "agent_pdf_workbench.dev_cli",
                         "--db-path", str(self.root / "events.db"), *args])

    def create(self, pdf: Path, question: str, port: int = 0) -> None:
        pdf = pdf.expanduser().resolve()
        if not question.strip() or not 0 <= port <= 65535:
            raise WorkflowError("Provide a nonempty research question and a port from 0 to 65535.")
        with pdf.open("rb") as stream:
            if b"%PDF" not in stream.read(1024):
                raise WorkflowError("The selected file does not have a PDF header.")
            stream.seek(0)
            sha, size = hash_stream(stream)
        self.root.mkdir(parents=True, exist_ok=True)
        with lock(self.root / "workspace.lock"):
            if self.file.exists():
                current = self.load()
                if current["sha256"] != sha or current["question"] != question.strip():
                    raise WorkflowError("This workspace has a different PDF or question. Choose a new workspace.")
                return
            if any(p.name != "workspace.lock" for p in self.root.iterdir()):
                raise WorkflowError("Choose an empty directory; existing files will not be adopted or overwritten.")
            self.save({"schema": SCHEMA, "root": str(self.root), "workspace_id": "review-" + uuid.uuid4().hex,
                       "source_id": "reader-" + uuid.uuid4().hex, "question": question.strip(),
                       "original_pdf": str(pdf), "sha256": sha, "size_bytes": size, "port": port,
                       "paper_id": None, "batch_id": None, "phase": "initializing"})

    def prepare(self) -> dict:
        """Resume committed ingestion/session creation even after a lost response."""
        with lock(self.root / "workspace.lock"):
            data = self.load()
            if data["paper_id"] is not None and not (self.root / "rks" / "rks.sqlite3").is_file():
                raise WorkflowError("The saved RKS database is missing. Restore the workspace before resuming.")
            if data["phase"] != "initializing" and not (self.root / "events.db").is_file():
                raise WorkflowError("The saved APW database is missing. Restore the workspace before resuming.")
            snapshot = reading.snapshot_pdf({"path": data["original_pdf"], "sha256": data["sha256"],
                                             "size_bytes": data["size_bytes"]}, self.root / "pdfs")
            self.rks("init-db")
            papers = self.rks("papers", "list", "--limit", "2")
            if papers["total_count"] > 1:
                raise WorkflowError("This single-paper workspace contains unexpected extra papers. Inspect RKS before resuming.")
            if not papers["papers"]:
                paper = self.rks("ingest", "pdf", str(snapshot), "--title", Path(data["original_pdf"]).stem)
            else:
                paper = papers["papers"][0]
            if data["paper_id"] is not None and data["paper_id"] != paper["id"]:
                raise WorkflowError("The saved RKS paper identity changed. Inspect the workspace before resuming.")
            source = self.rks("papers", "source", paper["id"])
            descriptor = reading.validate_source(source, paper["id"])
            if (descriptor["sha256"], descriptor["size_bytes"]) != (data["sha256"], data["size_bytes"]):
                raise WorkflowError("The RKS paper no longer matches this workspace's PDF revision.")
            data["paper_id"] = paper["id"]
            self.save(data)
            # The viewer URL is replaced with the actual bound port when the server starts.
            args = argparse.Namespace(paper_id=paper["id"], workspace_id=data["workspace_id"],
                rks_data_dir=self.root / "rks", apw_db=self.root / "events.db", cache_dir=self.root / "pdfs",
                viewer_url=f"http://127.0.0.1:{data['port'] or 8790}", rks_python=Path(sys.executable),
                apw_python=Path(sys.executable))
            handoff = reading.open_reading(args)
            write_json(self.root / "handoff.json", handoff)
            if data["phase"] == "initializing":
                data["phase"] = "reading"
            self.save(data)
            return data

    def set_port(self, port: int) -> None:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            data["port"] = port
            self.save(data)
            handoff = read_json(self.root / "handoff.json")
            handoff["apw"]["viewer_url"] = reading.session_url(f"http://127.0.0.1:{port}", handoff["apw"]["session_id"])
            write_json(self.root / "handoff.json", handoff)

    def batch_dir(self, batch_id: str) -> Path:
        if not isinstance(batch_id, str) or not re.fullmatch(r"[0-9a-f]{32}", batch_id):
            raise WorkflowError("Use the preview ID returned by this workspace.")
        return self.root / "imports" / batch_id

    def preview(self, annotation_ids: list[str], note_ids: list[str]) -> dict:
        if not annotation_ids and not note_ids:
            raise WorkflowError("Select at least one annotation or note before previewing an import.")
        for values in (annotation_ids, note_ids):
            if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
                raise WorkflowError("Selections must be lists of nonempty IDs.")
            if len(set(values)) != len(values):
                raise WorkflowError("Each selected ID must appear once.")
        with lock(self.root / "workspace.lock"):
            data = self.load()
            batch_id = uuid.uuid4().hex
            directory = self.batch_dir(batch_id)
            directory.mkdir(parents=True)
            args = argparse.Namespace(handoff=self.root / "handoff.json", source_id=data["source_id"],
                annotation_id=annotation_ids, note_id=note_ids, reviews=None,
                bundle=directory / "evidence.json", plan=directory / "plan.json",
                rks_python=Path(sys.executable), apw_python=Path(sys.executable))
            evidence.prepare_evidence(args)
            data.update(batch_id=batch_id, phase="preview")
            self.save(data)
            return self.preview_data(batch_id)

    def preview_data(self, batch_id: str) -> dict:
        directory = self.batch_dir(batch_id)
        bundle, plan = read_json(directory / "evidence.json"), read_json(directory / "plan.json")
        receipt = read_json(directory / "receipt.json") if (directory / "receipt.json").is_file() else None
        return {"id": batch_id, "counts": plan["counts"], "items": bundle["items"], "plan": plan,
                "applied": receipt is not None, "receipt": receipt}

    def apply(self, batch_id: str, *, accept_updates: bool = False) -> dict:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            if data["batch_id"] != batch_id:
                raise WorkflowError("This is not the current preview. Inspect the current selection before applying.")
            directory = self.batch_dir(batch_id)
            bundle = read_json(directory / "evidence.json")
            # RKS validates its own changes since preview. Also check APW's selected
            # objects so an edit/deletion in the reader cannot apply an old preview.
            command = ["export-evidence", "--session-id", bundle["source"]["session_id"],
                       "--source-id", data["source_id"]]
            for item in bundle["items"]:
                command += [f"--{item['kind']}-id", item["id"]]
            current = self.apw(*command)
            if current["items"] != bundle["items"]:
                raise WorkflowError("Selected evidence changed after preview. Preview it again before importing.")
            args = ["note", "import-evidence", str(directory / "evidence.json"), "--workspace-id",
                    data["workspace_id"], "--apply", "--plan", str(directory / "plan.json")]
            if accept_updates:
                args.append("--accept-updates")
            # A successful import may outlive a lost response. Do not keep showing
            # an older brief as current across that uncertainty; its file is retained.
            previous_brief = data.pop("brief", None)
            self.save(data)
            result = self.rks(*args, codes=(0, 2))
            if result.get("applied") is not True:
                return {"applied": False, "result": result, "next_action": "Inspect conflicts and prepare a fresh preview."}
            write_json(directory / "receipt.json", result)
            data["phase"] = "imported"
            if previous_brief and not result["counts"]["added"] and not result["counts"]["updated"]:
                data.update(brief=previous_brief, phase="brief")
            self.save(data)
            return {"applied": True, "result": result}

    def make_brief(self) -> dict:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            if not data["port"]:
                raise WorkflowError("Resume the reader before generating passage links.")
            out = self.root / "briefs"
            out.mkdir(exist_ok=True)
            identity = uuid.uuid4().hex
            pending, target = out / (".pending-" + identity), out / (identity + ".md")
            args = argparse.Namespace(paper_id=data["paper_id"], question=data["question"],
                workspace_id=data["workspace_id"], rks_data_dir=self.root / "rks", source_id=data["source_id"],
                apw_db=self.root / "events.db", rks_note_id=[], viewer_url=f"http://127.0.0.1:{data['port']}",
                output=pending, rks_python=Path(sys.executable), apw_python=Path(sys.executable))
            try:
                result = brief.generate_brief(args)
                os.replace(pending, target)
            finally:
                pending.unlink(missing_ok=True)
            result["path"] = str(target)
            data.update(phase="brief", brief=result)
            self.save(data)
            return result

    def summary(self) -> dict:
        data = self.load()
        handoff_path = self.root / "handoff.json"
        handoff = read_json(handoff_path) if handoff_path.is_file() else None
        result = {"schema": SCHEMA, "workspace": str(self.root), "workspace_id": data["workspace_id"],
                  "question": data["question"], "phase": data["phase"], "paper_id": data["paper_id"],
                  "source_pdf": str(self.root / "pdfs" / (data["sha256"] + ".pdf")),
                  "session_id": handoff["apw"]["session_id"] if handoff else None,
                  "viewer_url": handoff["apw"]["viewer_url"] if handoff and data["port"] else None,
                  "preview": self.preview_data(data["batch_id"]) if data["batch_id"] else None,
                  "brief": data.get("brief")}
        if result["brief"]:
            text = Path(result["brief"]["path"]).read_text(encoding="utf-8")
            result["brief"] = {**result["brief"], "text": text,
                               "passage_urls": re.findall(r"\[Open the supporting passage\]\(([^)]+)\)", text)}
        return result
