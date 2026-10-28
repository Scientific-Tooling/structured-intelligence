"""Project orchestration through RKS/APW contracts; scientific review stays explicit."""
from __future__ import annotations

import argparse
import os
import re
import sys
import uuid
from pathlib import Path

from . import brief, comparison, evidence, reading, search
from .reading import WorkflowError, hash_stream, run_json
from .state import lock, read_json, write_json

SCHEMA = "scientific-tooling.workspace.v2"
LEGACY_SCHEMA = "scientific-tooling.workspace.v1"
PAPER_FIELDS = ("original_pdf", "sha256", "size_bytes", "paper_id", "batch_id", "phase")


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.file = self.root / "workspace.json"

    def load(self) -> dict:
        if not self.file.is_file():
            raise WorkflowError("Workspace not found. Use start with PDFs and a question first.")
        data = read_json(self.file)
        if data.get("schema") not in {SCHEMA, LEGACY_SCHEMA}:
            raise WorkflowError("Unsupported workspace format. Preserve this directory and use a compatible version.")
        if data.get("root") != str(self.root):
            raise WorkflowError("Workspace was moved. Keep its original path; its retained source links use that path.")
        if data["schema"] == LEGACY_SCHEMA:
            # Read-only commands do not migrate on disk. The next locked save retains
            # the original manifest and all legacy artifact paths and identities.
            paper = {key: data.pop(key) for key in PAPER_FIELDS}
            paper.update(key="p1", title=Path(paper["original_pdf"]).stem, handoff="handoff.json")
            data.update(schema=SCHEMA, papers=[paper])
        return data

    def save(self, data: dict) -> None:
        if self.file.exists():
            original = read_json(self.file)
            if original.get("schema") == LEGACY_SCHEMA:
                backup = self.root / "workspace.v1.json"
                if backup.exists() and read_json(backup) != original:
                    raise WorkflowError("A different legacy backup exists. Preserve and inspect it before migration.")
                if not backup.exists():
                    write_json(backup, original)
        write_json(self.file, data)

    def rks(self, *args: str, codes=(0,)) -> dict:
        return run_json([sys.executable, "-m", "rks", *args], env={
            "RKS_DATA_DIR": str(self.root / "rks"), "RKS_AUTO_EXTRACT_MODE": "none",
        }, accepted_returncodes=codes)

    def apw(self, *args: str) -> dict:
        return run_json([sys.executable, "-m", "agent_pdf_workbench.dev_cli",
                         "--db-path", str(self.root / "events.db"), *args])

    @staticmethod
    def inspect_pdfs(pdfs: Path | list[Path]) -> list[dict]:
        records = []
        for pdf in [pdfs] if isinstance(pdfs, Path) else pdfs:
            pdf = pdf.expanduser().resolve()
            with pdf.open("rb") as stream:
                if b"%PDF" not in stream.read(1024):
                    raise WorkflowError(f"The selected file does not have a PDF header: {pdf}")
                stream.seek(0)
                sha, size = hash_stream(stream)
            if not any(record["sha256"] == sha for record in records):
                records.append({"original_pdf": str(pdf), "title": pdf.stem, "sha256": sha,
                                "size_bytes": size, "paper_id": None, "batch_id": None, "phase": "initializing"})
        if not records:
            raise WorkflowError("Select at least one PDF.")
        return records

    @staticmethod
    def append_papers(data: dict, records: list[dict]) -> list[str]:
        added = []
        for record in records:
            if any(paper["sha256"] == record["sha256"] for paper in data["papers"]):
                continue
            key = f"p{len(data['papers']) + 1}"
            record.update(key=key, handoff=f"papers/{key}/handoff.json")
            data["papers"].append(record)
            added.append(key)
        if added:
            data.pop("brief", None)  # Preserve old files, invalidate current coverage.
        return added

    def create(self, pdfs: Path | list[Path], question: str, port: int = 0) -> None:
        if not question.strip() or not 0 <= port <= 65535:
            raise WorkflowError("Provide a nonempty research question and a port from 0 to 65535.")
        records = self.inspect_pdfs(pdfs)  # Validate the entire input before changing state.
        self.root.mkdir(parents=True, exist_ok=True)
        with lock(self.root / "workspace.lock"):
            if self.file.exists():
                current = self.load()
                if current["question"] != question.strip() or not all(
                    any(p["sha256"] == r["sha256"] for p in current["papers"]) for r in records
                ):
                    raise WorkflowError("This workspace has a different PDF or question. Use sci add for more papers, or choose a new workspace.")
                return
            if any(p.name != "workspace.lock" for p in self.root.iterdir()):
                raise WorkflowError("Choose an empty directory; existing files will not be adopted or overwritten.")
            data = {"schema": SCHEMA, "root": str(self.root), "workspace_id": "review-" + uuid.uuid4().hex,
                    "source_id": "reader-" + uuid.uuid4().hex, "question": question.strip(), "port": port, "papers": []}
            self.append_papers(data, records)
            self.save(data)

    def add(self, pdfs: list[Path]) -> list[str]:
        records = self.inspect_pdfs(pdfs)
        with lock(self.root / "workspace.lock"):
            data = self.load()
            added = self.append_papers(data, records)
            self.save(data)
        self.prepare()
        return added

    def select(self, data: dict, paper: str | None = None, *, default: bool = False) -> dict:
        if paper is None:
            if len(data["papers"]) == 1 or default:
                return data["papers"][0]
            raise WorkflowError("Choose a paper with --paper (for example p1). Use sci papers to list this project.")
        matches = [item for item in data["papers"] if paper in (item["key"], item["paper_id"])]
        if len(matches) > 1:
            raise WorkflowError("Ambiguous paper identity. Choose a unique project paper key from sci papers.")
        if matches:
            return matches[0]
        raise WorkflowError(f"Paper {paper!r} is not in this project. Use sci papers to list it.")

    def for_session(self, session_id: str) -> str:
        for paper in self.load()["papers"]:
            path = self.root / paper["handoff"]
            if path.is_file() and read_json(path)["apw"]["session_id"] == session_id:
                return paper["key"]
        raise WorkflowError("This operation belongs to a different reading session.")

    def prepare(self) -> dict:
        """Resume each committed ingestion/session, including a lost response."""
        with lock(self.root / "workspace.lock"):
            data = self.load()
            if any(p["paper_id"] for p in data["papers"]) and not (self.root / "rks" / "rks.sqlite3").is_file():
                raise WorkflowError("The saved RKS database is missing. Restore the workspace before resuming.")
            if any(p["phase"] != "initializing" for p in data["papers"]) and not (self.root / "events.db").is_file():
                raise WorkflowError("The saved APW database is missing. Restore the workspace before resuming.")
            self.rks("init-db")
            # RKS records the immutable snapshot path as its native source_ref.
            # Paginate that public contract to recover a committed ingestion, then
            # verify its bytes. Never match paper titles or infer a new identity.
            known, offset = [], 0
            while True:
                page = self.rks("papers", "list", "--limit", "100", "--offset", str(offset), "--order", "asc")
                known.extend(page["papers"])
                offset += len(page["papers"])
                if offset >= page["total_count"]:
                    break
                if not page["papers"]:
                    raise WorkflowError("RKS paper pagination did not advance.")
            for paper in data["papers"]:
                snapshot = reading.snapshot_pdf({"path": paper["original_pdf"], "sha256": paper["sha256"],
                                                 "size_bytes": paper["size_bytes"]}, self.root / "pdfs")
                if paper["paper_id"] is None:
                    matches = [p for p in known if p["source_ref"] == str(snapshot)]
                    if len(matches) > 1:
                        raise WorkflowError("Several RKS papers reference this snapshot. Resolve the ambiguous identities before resuming.")
                    record = matches[0] if matches else self.rks("ingest", "pdf", str(snapshot), "--title", paper["title"])
                    paper["paper_id"] = record["id"]
                    self.save(data)
                source = self.rks("papers", "source", paper["paper_id"])
                descriptor = reading.validate_source(source, paper["paper_id"])
                if (descriptor["sha256"], descriptor["size_bytes"]) != (paper["sha256"], paper["size_bytes"]):
                    raise WorkflowError("The RKS paper no longer matches this project's PDF revision.")
                args = argparse.Namespace(paper_id=paper["paper_id"], workspace_id=data["workspace_id"],
                    rks_data_dir=self.root / "rks", apw_db=self.root / "events.db", cache_dir=self.root / "pdfs",
                    viewer_url=f"http://127.0.0.1:{data['port'] or 8790}", rks_python=Path(sys.executable),
                    apw_python=Path(sys.executable))
                handoff = reading.open_reading(args)
                path = self.root / paper["handoff"]
                path.parent.mkdir(parents=True, exist_ok=True)
                write_json(path, handoff)
                if paper["phase"] == "initializing":
                    paper["phase"] = "reading"
                self.save(data)
            return data

    def set_port(self, port: int) -> None:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            data["port"] = port
            self.save(data)
            for paper in data["papers"]:
                path = self.root / paper["handoff"]
                if path.is_file():
                    handoff = read_json(path)
                    handoff["apw"]["viewer_url"] = reading.session_url(f"http://127.0.0.1:{port}", handoff["apw"]["session_id"])
                    write_json(path, handoff)

    def search(self, query: str, *, paper: str | None = None, review: str = "all",
               mode: str = "lexical", limit: int = 20, offset: int = 0) -> dict:
        return search.search_project(self, query, paper=paper, review=review, mode=mode, limit=limit, offset=offset)

    def compare(self, action: str, **kwargs) -> dict:
        return comparison.operate(self, action, **kwargs)

    def batch_dir(self, batch_id: str) -> Path:
        if not isinstance(batch_id, str) or not re.fullmatch(r"[0-9a-f]{32}", batch_id):
            raise WorkflowError("Use the preview ID returned by this workspace.")
        return self.root / "imports" / batch_id

    def preview(self, annotation_ids: list[str], note_ids: list[str], paper: str | None = None) -> dict:
        if not annotation_ids and not note_ids:
            raise WorkflowError("Select at least one annotation or note before previewing an import.")
        for values in (annotation_ids, note_ids):
            if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values):
                raise WorkflowError("Selections must be lists of nonempty IDs.")
            if len(set(values)) != len(values):
                raise WorkflowError("Each selected ID must appear once.")
        with lock(self.root / "workspace.lock"):
            data = self.load()
            selected = self.select(data, paper)
            batch_id = uuid.uuid4().hex
            directory = self.batch_dir(batch_id)
            directory.mkdir(parents=True)
            args = argparse.Namespace(handoff=self.root / selected["handoff"], source_id=data["source_id"],
                annotation_id=annotation_ids, note_id=note_ids, reviews=None,
                bundle=directory / "evidence.json", plan=directory / "plan.json",
                rks_python=Path(sys.executable), apw_python=Path(sys.executable))
            evidence.prepare_evidence(args)
            selected.update(batch_id=batch_id, phase="preview")
            self.save(data)
            return self.preview_data(batch_id)

    def preview_data(self, batch_id: str) -> dict:
        directory = self.batch_dir(batch_id)
        bundle, plan = read_json(directory / "evidence.json"), read_json(directory / "plan.json")
        receipt = read_json(directory / "receipt.json") if (directory / "receipt.json").is_file() else None
        return {"id": batch_id, "paper_id": bundle["paper_id"], "counts": plan["counts"], "items": bundle["items"], "plan": plan,
                "applied": receipt is not None, "receipt": receipt}

    def apply(self, batch_id: str, *, accept_updates: bool = False, paper: str | None = None) -> dict:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            matches = [p for p in data["papers"] if p["batch_id"] == batch_id]
            if len(matches) != 1 or (paper is not None and self.select(data, paper) != matches[0]):
                raise WorkflowError("This is not the current preview for this paper. Inspect its current selection before applying.")
            selected = matches[0]
            directory = self.batch_dir(batch_id)
            bundle = read_json(directory / "evidence.json")
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
            # Invalidate across an uncertain response; the old artifact is retained.
            previous_brief = data.pop("brief", None)
            self.save(data)
            result = self.rks(*args, codes=(0, 2))
            if result.get("applied") is not True:
                return {"applied": False, "result": result, "next_action": "Inspect conflicts and prepare a fresh preview."}
            write_json(directory / "receipt.json", result)
            selected["phase"] = "imported"
            if previous_brief and not result["counts"]["added"] and not result["counts"]["updated"]:
                data["brief"] = previous_brief
            self.save(data)
            return {"applied": True, "result": result}

    def make_brief(self) -> dict:
        with lock(self.root / "workspace.lock"):
            data = self.load()
            if not data["port"]:
                raise WorkflowError("Resume the reader before generating passage links.")
            if any(not p["paper_id"] or p["phase"] == "initializing" for p in data["papers"]):
                raise WorkflowError("Resume this project to finish preparing all papers before generating a brief.")
            out = self.root / "briefs"
            out.mkdir(exist_ok=True)
            identity = uuid.uuid4().hex
            pending, target = out / (".pending-" + identity), out / (identity + ".md")
            sections, coverage = [], []
            counts = dict.fromkeys(("evidence", "reviewed", "unreviewed", "linked_passages", "unavailable_passages"), 0)
            for paper in data["papers"]:
                args = argparse.Namespace(paper_id=paper["paper_id"], question=data["question"],
                    workspace_id=data["workspace_id"], rks_data_dir=self.root / "rks", source_id=data["source_id"],
                    apw_db=self.root / "events.db", rks_note_id=[], viewer_url=f"http://127.0.0.1:{data['port']}",
                    output=pending, rks_python=Path(sys.executable), apw_python=Path(sys.executable))
                text, result = brief.render_brief(args, allow_empty=True)
                for key in counts:
                    counts[key] += result["counts"][key]
                coverage.append({"key": paper["key"], "paper_id": paper["paper_id"], "title": paper["title"], "counts": result["counts"]})
                # Preserve the verified per-paper renderer and attribution, nested
                # beneath a project heading rather than inventing scientific claims.
                body = text.split("\n", 1)[1]
                body = re.sub(r"^(#+) ", r"#\1 ", body, flags=re.MULTILINE)
                sections.append(f"## {brief.escape(paper['key'] + ': ' + paper['title'])}\n" + body)
            if not counts["evidence"]:
                raise WorkflowError("No matching imported evidence. Preview and import selected material from at least one paper first.")
            lines = ["# Source-linked project brief", "", f"Question: {brief.escape(data['question'])}", "",
                     "Evidence is grouped by paper for comparison. No agreement, contradiction, or scientific conclusion is inferred.", "",
                     "## Coverage", "", "| Paper | Evidence | Reviewed | Unreviewed | Linked passages | Unavailable |",
                     "| --- | ---: | ---: | ---: | ---: | ---: |"]
            for paper in coverage:
                c = paper["counts"]
                lines.append(f"| {brief.escape(paper['key'] + ': ' + paper['title']).replace(chr(10), ' ')} | {c['evidence']} | {c['reviewed']} | {c['unreviewed']} | {c['linked_passages']} | {c['unavailable_passages']} |")
            lines += ["", "Papers without imported evidence remain visible as coverage gaps, not negative findings.", "", *sections]
            try:
                with pending.open("x", encoding="utf-8") as stream:
                    stream.write("\n".join(lines))
                os.replace(pending, target)
            finally:
                pending.unlink(missing_ok=True)
            result = {"schema": "scientific-tooling.project-brief.v1", "path": str(target),
                      "counts": counts, "papers": coverage, "paper_count": len(coverage)}
            data["brief"] = result
            self.save(data)
            return result

    def paper_summary(self, data: dict, paper: dict) -> dict:
        path = self.root / paper["handoff"]
        handoff = read_json(path) if path.is_file() else None
        session = handoff["apw"]["session_id"] if handoff else None
        return {"key": paper["key"], "title": paper["title"], "paper_id": paper["paper_id"], "phase": paper["phase"],
                "source_pdf": str(self.root / "pdfs" / (paper["sha256"] + ".pdf")), "session_id": session,
                "viewer_url": reading.session_url(f"http://127.0.0.1:{data['port']}", session) if session and data["port"] else None}

    def summary(self, paper: str | None = None) -> dict:
        data = self.load()
        selected = self.select(data, paper, default=True)
        result = {"schema": SCHEMA, "workspace": str(self.root), "workspace_id": data["workspace_id"],
                  "question": data["question"], **self.paper_summary(data, selected),
                  "paper_count": len(data["papers"]), "papers": [self.paper_summary(data, p) for p in data["papers"]],
                  "preview": self.preview_data(selected["batch_id"]) if selected["batch_id"] else None,
                  "brief": data.get("brief")}
        if result["brief"]:
            text = Path(result["brief"]["path"]).read_text(encoding="utf-8")
            result["brief"] = {**result["brief"], "text": text,
                               "passage_urls": re.findall(r"\[Open the supporting passage\]\(([^)]+)\)", text)}
        return result
