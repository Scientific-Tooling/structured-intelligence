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
from threading import Event, Thread
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import ProxyHandler, Request, build_opener

from .reading import WorkflowError
from .state import lock, read_json, write_json
from .workspace import Workspace
from .comparison import evidence_options
from . import discovery, maintenance

# Library callers retain handles for readers they started and reap them on stop.
# CLI callers may exit while their deliberately detached reader continues running.
_owned_children: dict[tuple[str, str], subprocess.Popen] = {}


def _reap_children(workspace, instance_id=None):
    for key, child in list(_owned_children.items()):
        if key[0] != str(workspace.root):
            continue
        if key[1] == instance_id or child.poll() is not None:
            child.wait(timeout=5)
            del _owned_children[key]


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
            with exc:
                message = json.load(exc).get("error", str(exc))
        except (ValueError, AttributeError):
            message = str(exc)
        raise WorkflowError(message) from exc


def running(workspace: Workspace, *, detailed: bool = True, paper: str | None = None) -> dict | None:
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
            selected = workspace.summary(paper)
            if selected["session_id"] is None:
                return {**selected, "running": True, "next_action": "Resume to finish preparing this paper."}
            return request(record["port"], "/api/workflow?" + urlencode({"session_id": selected["session_id"]}))
        return response
    return None


def ensure_running(workspace: Workspace, *, detailed: bool = True, paper: str | None = None) -> dict:
    if not workspace.load()["papers"]:
        raise WorkflowError("No PDF is selected yet. Use sci discover to find and select a paper before opening the reader.")
    existing = running(workspace, detailed=False)
    if existing:
        if any(p["phase"] == "initializing" for p in workspace.load()["papers"]):
            workspace.prepare()
        return running(workspace, detailed=detailed, paper=paper)
    with lock(workspace.root / "server.lock"):
        workspace.prepare()
    command = [sys.executable, "-m", "scientific_tooling", "serve", "--workspace", str(workspace.root)]
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    (workspace.root / "server.log").touch(exist_ok=True)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               cwd=os.path.dirname(sys.executable), env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **options)
    # A filename can become visible during publication before Windows allows it
    # to be opened. The child explicitly acknowledges completed publication;
    # startup must not infer readiness by polling that file.
    ready = Event()
    response = []
    def read_ready():
        try:
            response.append(process.stdout.readline())
        finally:
            ready.set()
    listener = Thread(target=read_ready, daemon=True)
    listener.start()
    try:
        if not ready.wait(timeout=20):
            raise WorkflowError(f"Reader startup timed out. Inspect {workspace.root / 'server.log'} and resume.")
        if not response or not response[0]:
            tail = (workspace.root / "server.log").read_text(encoding="utf-8", errors="replace")[-1800:]
            raise WorkflowError(f"Reader could not start. See {workspace.root / 'server.log'}\n{tail}")
        receipt = json.loads(response[0])
        if receipt.get("schema") != "scientific-tooling.reader-ready.v1" or receipt.get("workspace_id") != workspace.load()["workspace_id"]:
            raise WorkflowError("Reader returned an invalid startup acknowledgement. Inspect server.log.")
        current = running(workspace, detailed=detailed, paper=paper)
        if not current or current.get("instance_id") != receipt.get("instance_id"):
            raise WorkflowError("Reader did not confirm its published instance. Inspect server.log.")
        _owned_children[(str(workspace.root), receipt["instance_id"])] = process
        return current
    except BaseException:
        # This handle belongs to the child just launched, never a stored/recycled PID.
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        raise
    finally:
        listener.join(timeout=5)
        process.stdout.close()


def stop(workspace: Workspace) -> dict:
    current = running(workspace, detailed=False)
    if not current:
        with lock(workspace.root / "server.lock"):
            _reap_children(workspace)
            return {"stopped": True, "already_stopped": True, "workspace": str(workspace.root)}
    record = read_json(workspace.root / "server.json")
    request(record["port"], "/api/workflow", {"action": "stop", "token": record["token"]})
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if not (workspace.root / "server.json").exists():
            try:
                with lock(workspace.root / "server.lock"):
                    _reap_children(workspace, record["instance_id"])
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
        data = workspace.load()
        self.session_id = read_json(workspace.root / data["papers"][0]["handoff"])["apw"]["session_id"]
        self.server = None

    def status(self, session_id: str | None) -> dict:
        if session_id is None:
            # Control-plane identity must survive missing/corrupt result artifacts.
            return {"enabled": True, "running": True, "instance_id": self.instance_id,
                    "workspace_id": self.workspace_id, "session_id": self.session_id}
        try:
            try:
                paper = self.workspace.for_session(session_id)
            except WorkflowError:
                return {"enabled": False}
            data = self.workspace.summary(paper)
            data.update(enabled=True, instance_id=self.instance_id, running=True,
                        capabilities={"evidence_search": True, "comparisons": True, "discovery": True, "maintenance": True})
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

    def search(self, params: dict) -> dict:
        try:
            self.workspace.for_session(params.get("session_id"))
            return self.workspace.search(params.get("q", ""), paper=params.get("paper") or None,
                                         review=params.get("review", "all"), mode=params.get("mode", "lexical"),
                                         limit=int(params.get("limit", "20")), offset=int(params.get("offset", "0")))
        except (WorkflowError, OSError, KeyError, TypeError) as exc:
            raise ValueError(str(exc)) from exc

    def comparisons(self, params: dict) -> dict:
        try:
            self.workspace.for_session(params.get("session_id"))
            result = self.workspace.compare("list")
            if params.get("comparison_id"):
                result.update(self.workspace.compare("show", comparison_id=params["comparison_id"]))
                result["evidence"] = evidence_options(self.workspace)["evidence"]
            return result
        except (WorkflowError, OSError, KeyError, TypeError) as exc:
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
            paper = self.workspace.for_session(payload.get("session_id"))
            if action == "project_update":
                return maintenance.inspect(self.workspace, save=True)
            if action == "discovery_repeat":
                return {"discovery": discovery.repeat(self.workspace, payload.get("discovery_id"))}
            if action in {"discovery_search", "discovery_lookup"}:
                return {"discovery": discovery.discover(self.workspace, action.removeprefix("discovery_"), payload.get("query"),
                    provider=payload.get("provider", "pubmed"), limit=payload.get("limit", 10))}
            if action == "discovery_select":
                # Local filesystem paths are deliberately CLI-only; browser selections use saved provider URLs.
                return {"selection": discovery.select(self.workspace, payload.get("discovery_id"), payload.get("candidate_id"),
                    source=payload.get("source"), request_id=payload.get("request_id"))}
            if action == "discovery_retry":
                return {"selection": discovery.select(self.workspace, request_id=payload.get("request_id"), retry=True)}
            if action in {"comparison_create", "comparison_set", "comparison_review"}:
                return self.workspace.compare(action.removeprefix("comparison_"),
                    comparison_id=payload.get("comparison_id"), payload=payload.get("payload"),
                    expected_revision=payload.get("expected_revision"), request_id=payload.get("request_id"))
            if action == "preview":
                result = self.workspace.preview(payload.get("annotation_ids", []), payload.get("note_ids", []), paper)
                return {"preview": result}
            if action == "apply":
                result = self.workspace.apply(payload.get("preview_id"), paper=paper)
                if result["applied"]:
                    # Keep the successful import receipt even if generating the brief
                    # fails. A retry can safely replay or request only the brief.
                    try:
                        result["brief"] = self.workspace.make_brief(payload.get("preview_id"))
                    except (WorkflowError, OSError, ValueError) as exc:
                        result["brief_error"] = str(exc)
                return result
            if action == "brief":
                return {"brief": self.workspace.make_brief(payload.get("request_id"))}
            raise WorkflowError("Unknown workflow action.")
        except (WorkflowError, OSError, KeyError, TypeError) as exc:
            raise ValueError(str(exc)) from exc

    def discovery(self, params: dict) -> dict:
        try:
            self.workspace.for_session(params.get("session_id"))
            result = discovery.inventory(self.workspace)
            if params.get("discovery_id"):
                result["discovery"] = discovery.show(self.workspace, params["discovery_id"])
            return result
        except (WorkflowError, OSError, KeyError, TypeError) as exc:
            raise ValueError(str(exc)) from exc

    def maintenance(self, params: dict) -> dict:
        try:
            self.workspace.for_session(params.get("session_id"))
            if params.get("edition_id"):
                return maintenance.history(self.workspace, params["edition_id"])
            return maintenance.inspect(self.workspace)
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
        print(json.dumps({"schema": "scientific-tooling.reader-ready.v1", "instance_id": instance_id,
                          "workspace_id": data["workspace_id"]}), flush=True)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def annotate(workspace: Workspace, page: int, quote: str, comment: str, paper: str | None = None) -> dict:
    import uuid
    from datetime import datetime, timezone

    if page < 1 or not quote.strip():
        raise WorkflowError("An annotation needs a positive page number and an exact source quote.")
    selected = workspace.select(workspace.load(), paper)
    state = ensure_running(workspace, paper=selected["key"])
    now = datetime.now(timezone.utc).isoformat()
    annotation = {"id": "ann_" + uuid.uuid4().hex, "page": page, "type": "highlight", "quote": quote,
                  "anchor": None, "rects": [], "comment": comment, "tags": [], "createdAt": now, "updatedAt": now}
    result = request(workspace.load()["port"], "/api/annotations",
                     {"session_id": state["session_id"], "annotation": annotation})
    result["review_status"] = "unreviewed"
    result["viewer_url"] = state["viewer_url"] + "&" + urlencode({"page": page})
    return result
