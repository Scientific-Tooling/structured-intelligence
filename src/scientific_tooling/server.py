"""An owned background reader, addressed by an instance token rather than a PID."""
from __future__ import annotations

import hmac
import json
import os
import secrets
import signal
import subprocess
import sys
import time
import traceback
from contextlib import redirect_stderr
from threading import Thread
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from .reading import WorkflowError
from .state import lock, read_json, write_json
from .workspace import Workspace


def request(port: int, path: str, payload: dict | None = None, *, timeout: float = 60) -> dict:
    # Local requests should never pass through an institutional HTTP proxy.
    opener = build_opener(ProxyHandler({}))
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(f"http://127.0.0.1:{port}{path}", data=body,
                  headers={"Content-Type": "application/json"} if body else {})
    try:
        with opener.open(req, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            message = json.load(exc).get("error", str(exc))
        except (ValueError, AttributeError):
            message = str(exc)
        raise WorkflowError(message) from exc


def running(workspace: Workspace, *, detailed: bool = True) -> dict | None:
    path = workspace.root / "server.json"
    if not path.is_file():
        return None
    record = read_json(path)
    try:
        response = request(record["port"], "/api/workflow", timeout=1)
    except (OSError, URLError, WorkflowError, ValueError):
        return None
    if response.get("instance_id") == record["instance_id"] and response.get("workspace_id") == record["workspace_id"]:
        if detailed:
            return request(record["port"], "/api/workflow?" + urlencode({"session_id": response["session_id"]}))
        return response
    return None


def ensure_running(workspace: Workspace, *, detailed: bool = True) -> dict:
    existing = running(workspace, detailed=detailed)
    if existing:
        return existing
    with lock(workspace.root / "server.lock"):
        workspace.prepare()
    command = [sys.executable, "-m", "scientific_tooling", "serve", "--workspace", str(workspace.root)]
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    (workspace.root / "server.log").touch(exist_ok=True)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               cwd=os.path.dirname(sys.executable), env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **options)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        current = running(workspace, detailed=detailed)
        if current:
            return current
        if process.poll() is not None:
            tail = (workspace.root / "server.log").read_text(encoding="utf-8", errors="replace")[-1800:]
            raise WorkflowError(f"Reader could not start. See {workspace.root / 'server.log'}\n{tail}")
        time.sleep(0.1)
    # This handle belongs to the child just launched, never a stored/recycled PID.
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    raise WorkflowError(f"Reader startup timed out. Inspect {workspace.root / 'server.log'} and resume.")


def stop(workspace: Workspace) -> dict:
    current = running(workspace, detailed=False)
    if not current:
        with lock(workspace.root / "server.lock"):
            return {"stopped": True, "already_stopped": True, "workspace": str(workspace.root)}
    record = read_json(workspace.root / "server.json")
    request(record["port"], "/api/workflow", {"action": "stop", "token": record["token"]})
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if not (workspace.root / "server.json").exists():
            try:
                with lock(workspace.root / "server.lock"):
                    return {"stopped": True, "workspace": str(workspace.root)}
            except WorkflowError:
                pass
        time.sleep(0.1)
    raise WorkflowError("The owned reader is still stopping. Inspect server.log; no other process was terminated.")


class HostedWorkflow:
    def __init__(self, workspace: Workspace, service, instance_id: str, token: str):
        self.workspace, self.service = workspace, service
        self.instance_id, self.token = instance_id, token
        self.workspace_id = workspace.load()["workspace_id"]
        self.session_id = read_json(workspace.root / "handoff.json")["apw"]["session_id"]
        self.server = None

    def status(self, session_id: str | None) -> dict:
        if session_id is None:
            # Control-plane identity must survive missing/corrupt result artifacts.
            return {"enabled": True, "running": True, "instance_id": self.instance_id,
                    "workspace_id": self.workspace_id, "session_id": self.session_id}
        try:
            data = self.workspace.summary()
            if session_id and data["session_id"] != session_id:
                return {"enabled": False}
            data.update(enabled=True, instance_id=self.instance_id, running=True)
            # Read the whole selection space through APW's public service, including
            # pagination; do not query APW's SQLite tables from orchestration.
            for kind in ("annotations", "notes"):
                records, offset = [], 0
                while True:
                    page = getattr(self.service, "list_" + kind)(session_id=data["session_id"], limit=1000, offset=offset)
                    records.extend(page[kind])
                    if not page["has_more"]:
                        break
                    offset = page["next_offset"]
                data[kind] = records
            return data
        except (WorkflowError, OSError, KeyError) as exc:
            raise ValueError(str(exc)) from exc

    def execute(self, payload: dict) -> dict:
        try:
            action = payload.get("action")
            if action == "stop":
                supplied = payload.get("token")
                if not isinstance(supplied, str) or not hmac.compare_digest(supplied, self.token):
                    raise WorkflowError("Only the owning workflow can stop this reader.")
                Thread(target=self.server.shutdown, daemon=True).start()
                return {"stopping": True}
            session_id = read_json(self.workspace.root / "handoff.json")["apw"]["session_id"]
            if payload.get("session_id") != session_id:
                raise WorkflowError("This operation belongs to a different reading session.")
            if action == "preview":
                result = self.workspace.preview(payload.get("annotation_ids", []), payload.get("note_ids", []))
                return {"preview": result}
            if action == "apply":
                result = self.workspace.apply(payload.get("preview_id"))
                if result["applied"]:
                    # Keep the successful import receipt even if generating the brief
                    # fails. A retry can safely replay or request only the brief.
                    try:
                        result["brief"] = self.workspace.make_brief()
                    except (WorkflowError, OSError, ValueError) as exc:
                        result["brief_error"] = str(exc)
                return result
            if action == "brief":
                return {"brief": self.workspace.make_brief()}
            raise WorkflowError("Unknown workflow action.")
        except (WorkflowError, OSError, KeyError, TypeError) as exc:
            raise ValueError(str(exc)) from exc


def serve(workspace: Workspace) -> None:
    # The daemon owns its log explicitly. Its shutdown acknowledgement is written
    # only after the server, requests, log and process lock have all been closed.
    instance_id, token = secrets.token_hex(16), secrets.token_urlsafe(32)
    record_path = workspace.root / "server.json"
    with lock(workspace.root / "server.lock"):
        try:
            with (workspace.root / "server.log").open("a", encoding="utf-8", buffering=1) as log:
                with redirect_stderr(log):
                    try:
                        _serve_owned(workspace, instance_id, token)
                    except BaseException:
                        traceback.print_exc(file=log)
                        raise
        finally:
            if record_path.is_file() and read_json(record_path).get("instance_id") == instance_id:
                record_path.unlink()


def _serve_owned(workspace: Workspace, instance_id: str, token: str) -> None:
    from agent_pdf_workbench.service import AgentPdfWorkbenchService
    from agent_pdf_workbench.viewer_server import create_viewer_server

    data = workspace.load()
    service = AgentPdfWorkbenchService(db_path=workspace.root / "events.db")
    workflow = HostedWorkflow(workspace, service, instance_id, token)
    try:
        server = create_viewer_server(workspace.root / "events.db", workspace.root / "pdfs",
                                      port=data["port"], workflow=workflow)
    except OSError as exc:
        raise WorkflowError(f"Cannot bind the saved reader port {data['port']}. Free that port and resume; existing passage links retain their address.") from exc
    workflow.server = server
    record_path = workspace.root / "server.json"
    try:
        workspace.set_port(server.server_address[1])
        write_json(record_path, {"instance_id": instance_id, "token": token,
                                "workspace_id": data["workspace_id"], "port": server.server_address[1]})
        signal.signal(signal.SIGTERM, lambda *_: Thread(target=server.shutdown, daemon=True).start())
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def annotate(workspace: Workspace, page: int, quote: str, comment: str) -> dict:
    import uuid
    from datetime import datetime, timezone

    if page < 1 or not quote.strip():
        raise WorkflowError("An annotation needs a positive page number and an exact source quote.")
    state = ensure_running(workspace)
    now = datetime.now(timezone.utc).isoformat()
    annotation = {"id": "ann_" + uuid.uuid4().hex, "page": page, "type": "highlight", "quote": quote,
                  "anchor": None, "rects": [], "comment": comment, "tags": [], "createdAt": now, "updatedAt": now}
    result = request(workspace.load()["port"], "/api/annotations",
                     {"session_id": state["session_id"], "annotation": annotation})
    result["review_status"] = "unreviewed"
    result["viewer_url"] = state["viewer_url"] + "&" + urlencode({"page": page})
    return result
