"""Saved discovery and explicit, recoverable selection into an existing reading project."""
from __future__ import annotations

import hashlib
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path

from . import discovery_sources as sources, reading
from .brief import digest
from .reading import WorkflowError
from .state import hex_id, lock, read_json, read_sealed, write_json

RUN_SCHEMA = "scientific-tooling.discovery.v1"
SELECTION_SCHEMA = "scientific-tooling.paper-selection.v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def identity(value):
    return hex_id(value, "Use a saved discovery or selection request ID from this project.")


def directory(workspace, run_id):
    return workspace.root / "discoveries" / identity(run_id)


def show(workspace, run_id):
    data = workspace.load()
    path = directory(workspace, run_id)
    changed = "Discovery identity or saved revision changed. Preserve and inspect its original files."
    result = read_sealed(path / "discovery.json", RUN_SCHEMA, data["workspace_id"], changed)
    if result.get("id") != run_id:
        raise WorkflowError(changed)
    for response in result["responses"]:
        name = response["path"]
        if not re.fullmatch(r"responses/\d{2}\.(json|xml)", name):
            raise WorkflowError("Invalid saved discovery response path.")
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != response["sha256"]:
            raise WorkflowError("Saved provider response changed. Restore the original discovery artifacts.")
    return result


def inventory(workspace):
    data = workspace.load()
    runs = []
    candidates = {}
    for path in sorted((workspace.root / "discoveries").glob("*/discovery.json")):
        run = show(workspace, path.parent.name)
        runs.append({k: run[k] for k in ("id", "action", "query", "provider", "retrieved_at", "status", "error")})
        candidates.update({(run["id"], run["revision"], c["id"]): c["title"] for c in run["candidates"]})
    selections = []
    for path in sorted((workspace.root / "selections").glob("*/selection.json")):
        state = read_json(path)
        request = state.get("request", {})
        if (state.get("schema") != SELECTION_SCHEMA or request.get("workspace_id") != data["workspace_id"]
                or request.get("id") != identity(path.parent.name) or state.get("request_revision") != digest(request)):
            raise WorkflowError("A saved selection has changed or belongs to another project.")
        candidate = (request.get("discovery_id"), request.get("discovery_revision"), request.get("candidate_id"))
        if candidate not in candidates:
            raise WorkflowError("A saved selection no longer matches its original discovery candidate.")
        selections.append({**state, "candidate_title": candidates[candidate]})
    return {"schema": "scientific-tooling.discovery-list.v1", "discoveries": runs,
            "works": data.get("works", []), "selections": selections}


def discover(workspace, action, query, *, provider="pubmed", limit=10, client=None, previous=None):
    data = workspace.load()
    if action not in {"search", "lookup"} or not isinstance(query, str) or not query.strip() or len(query) > 1500:
        raise WorkflowError("Provide a nonempty query or identifier of at most 1500 characters.")
    if type(limit) is not int or not 1 <= limit <= 25 or provider not in {"pubmed", "crossref"}:
        raise WorkflowError("Choose pubmed/crossref and a result limit from 1 to 25.")
    if action == "lookup":
        kind, _ = sources.identifier(query)
        provider, limit = ("crossref" if kind == "doi" else "pubmed"), 1
    run_id = uuid.uuid4().hex
    path = directory(workspace, run_id)
    (path / "responses").mkdir(parents=True)
    run = {"schema": RUN_SCHEMA, "id": run_id, "workspace_id": data["workspace_id"], "question": data["question"],
           "action": action, "query": query.strip(), "provider": provider, "limit": limit, "retrieved_at": now(),
           "status": "pending", "error": None, "responses": [], "candidates": [], "requests": []}
    if previous:
        run["repeated_from"] = {"id": previous["id"], "revision": previous["revision"]}
    client = client or sources.Client()
    def save():
        run["revision"] = digest({k: v for k, v in run.items() if k != "revision"})
        write_json(path / "discovery.json", run)
    def fetch(url, format):
        run["requests"].append({"url": url, "requested_at": now()})
        save()
        raw, headers = client.fetch(url)
        if len(raw) > sources.METADATA_LIMIT:
            raise WorkflowError("Metadata response exceeds the size limit.")
        name = f"responses/{len(run['responses']) + 1:02d}.{format}"
        (path / name).write_bytes(raw)
        run["responses"].append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "retrieved_at": now(), **headers})
        save()
        return raw
    save()
    try:
        records, details = sources.retrieve(action, run["query"], provider, limit, fetch)
        if len(records) > limit or len({r["provider_id"] for r in records}) != len(records):
            raise WorkflowError("Provider returned too many or duplicate records.")
        run["candidates"] = [{"id": f"c{i + 1}", **r, "review_status": "unreviewed"} for i, r in enumerate(records)]
        if previous:
            old = {c["provider_id"]: {k: v for k, v in c.items() if k != "id"} for c in previous["candidates"]}
            new = {c["provider_id"]: {k: v for k, v in c.items() if k != "id"} for c in run["candidates"]}
            run["candidate_changes"] = {"added": sorted(new.keys() - old.keys()), "not_returned": sorted(old.keys() - new.keys()),
                                        "changed": sorted(k for k in old.keys() & new.keys() if old[k] != new[k]),
                                        "unchanged": sorted(k for k in old.keys() & new.keys() if old[k] == new[k])}
        run.update(status="complete", details=details)
        save()
    except (OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError, IndexError, WorkflowError) as exc:
        run.update(status="failed", error=str(exc))
        save()
        raise WorkflowError(f"Discovery {run_id} failed: {exc}. Its query and responses are retained; use discover show.") from exc
    return run


def repeat(workspace, run_id, *, client=None):
    previous = show(workspace, run_id)
    if previous["status"] != "complete":
        raise WorkflowError("Repeat a completed saved discovery; rerun failed queries explicitly.")
    return discover(workspace, previous["action"], previous["query"], provider=previous["provider"],
                    limit=previous["limit"], client=client, previous=previous)


def bind_work(data, candidate, run, request_id):
    """Exact identifiers establish identity; titles and abstract similarity never do."""
    works = data.setdefault("works", [])
    ids = candidate["identifiers"]
    matches = [w for w in works if any(w["identifiers"].get(k) == v for k, v in ids.items())]
    if len(matches) > 1:
        raise WorkflowError("Provider identifiers bridge multiple selected works. Resolve this identity conflict before adding a PDF.")
    if matches:
        work = matches[0]
        if any(k in work["identifiers"] and work["identifiers"][k] != v for k, v in ids.items()):
            raise WorkflowError("Provider identifiers conflict with the selected work's recorded identity.")
        work["identifiers"].update(ids)
    else:
        work = {"id": "w_" + uuid.uuid4().hex, "identifiers": dict(ids), "title": candidate["title"],
                "authors": candidate["authors"], "year": candidate["year"], "venue": candidate["venue"],
                "provenance": [], "selection_ids": [], "paper_keys": []}
        works.append(work)
    reference = {"discovery_id": run["id"], "discovery_revision": run["revision"], "candidate_id": candidate["id"],
                 "provider": candidate["provider"], "provider_id": candidate["provider_id"], "retrieved_at": run["retrieved_at"]}
    if reference not in work["provenance"]:
        work["provenance"].append(reference)
    if request_id not in work["selection_ids"]:
        work["selection_ids"].append(request_id)
    return work


def select(workspace, run_id=None, candidate_id=None, *, pdf=None, source=None, request_id=None, retry=False, client=None):
    workspace.load()
    request_id = identity(request_id or uuid.uuid4().hex)
    root = workspace.root / "selections" / request_id
    root.mkdir(parents=True, exist_ok=True)
    with lock(workspace.root / "discovery.lock"):
        state_path = root / "selection.json"
        if retry:
            state = read_json(state_path)
            request = state["request"]
            run_id, candidate_id = request["discovery_id"], request["candidate_id"]
        else:
            run = show(workspace, run_id)
            if pdf is not None and source is not None:
                raise WorkflowError("Choose either an explicit PDF source or a local PDF.")
            descriptor = workspace.inspect_pdfs(Path(pdf))[0] if pdf is not None else None
            request = {"id": request_id, "workspace_id": workspace.load()["workspace_id"], "discovery_id": run_id,
                       "discovery_revision": run["revision"], "candidate_id": candidate_id, "source": source,
                       "local_pdf": {k: descriptor[k] for k in ("original_pdf", "sha256", "size_bytes")} if descriptor else None}
            if state_path.exists():
                state = read_json(state_path)
                if state["request"] != request:
                    raise WorkflowError("Selection request ID belongs to a different operation.")
            else:
                state = {"schema": SELECTION_SCHEMA, "request": request, "request_revision": digest(request),
                         "status": "pending", "created_at": now(), "snapshot": None, "paper_key": None,
                         "work_id": None, "error": None}
        if (state.get("schema") != SELECTION_SCHEMA or request.get("id") != request_id
                or request.get("workspace_id") != workspace.load()["workspace_id"]
                or state.get("request_revision") != digest(request)):
            raise WorkflowError("Saved selection identity changed or belongs to another project.")
        run = show(workspace, run_id)
        if run["status"] != "complete" or request["discovery_revision"] != run["revision"]:
            raise WorkflowError("Select from the original completed discovery revision.")
        candidate = next((c for c in run["candidates"] if c["id"] == candidate_id), None)
        if candidate is None:
            raise WorkflowError("Choose a candidate ID from this saved discovery.")
        if state["status"] == "added":
            verify_snapshot(state["snapshot"])
            paper = workspace.select(workspace.load(), state["paper_key"])
            if paper["sha256"] != state["snapshot"]["sha256"] or paper.get("work_id") != state["work_id"]:
                raise WorkflowError("The completed selection no longer matches its project paper.")
            workspace.prepare()
            return {**state, "replayed": True}
        if request["source"] is not None and (type(request["source"]) is not int or not 1 <= request["source"] <= len(candidate["pdf_sources"])):
            raise WorkflowError("Choose a numbered PDF source shown for this candidate.")
        write_json(state_path, state)
        try:
            with lock(workspace.root / "workspace.lock"):
                data = workspace.load()
                work = bind_work(data, candidate, run, request_id)
                state["work_id"] = work["id"]
                workspace.save(data)
            if state["snapshot"] is None:
                if request["local_pdf"]:
                    local = request["local_pdf"]
                    snapshot = reading.snapshot_pdf({"path": local["original_pdf"], "sha256": local["sha256"],
                                                     "size_bytes": local["size_bytes"]}, workspace.root / "pdfs")
                    state["snapshot"] = {"path": str(snapshot), "sha256": local["sha256"], "size_bytes": local["size_bytes"],
                                         "acquired_at": now(), "source": "user_selected_local_pdf"}
                else:
                    options = candidate["pdf_sources"]
                    if not options or (len(options) > 1 and request["source"] is None):
                        state.update(status="full_text_unavailable", error=("No PDF source reported. Select a local PDF or look up this work with another provider."
                            if not options else "Multiple PDF sources reported. Inspect them and select a numbered source."))
                        write_json(state_path, state)
                        return {**state, "replayed": False}
                    url = options[(request["source"] or 1) - 1]["url"]
                    state.update(status="downloading", error=None)
                    write_json(state_path, state)
                    content, headers = (client or sources.Client()).fetch(url, pdf=True)
                    if len(content) > sources.PDF_LIMIT or not content.lstrip().startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
                        raise WorkflowError("Source did not return a complete PDF. Its abstract is not a substitute.")
                    sha = hashlib.sha256(content).hexdigest()
                    fd, pending = tempfile.mkstemp(prefix=".pending-", suffix=".pdf", dir=root)
                    try:
                        with os.fdopen(fd, "wb") as stream:
                            stream.write(content)
                            stream.flush()
                            os.fsync(stream.fileno())
                        snapshot = reading.snapshot_pdf({"path": pending, "sha256": sha, "size_bytes": len(content)}, workspace.root / "pdfs")
                    finally:
                        Path(pending).unlink(missing_ok=True)
                    state["snapshot"] = {"path": str(snapshot), "sha256": sha, "size_bytes": len(content), "acquired_at": now(),
                                         "source": "selected_provider_pdf", **headers}
                state["status"] = "retained"
                write_json(state_path, state)  # Persist byte identity before creating any native paper/session.
            verify_snapshot(state["snapshot"])
            with lock(workspace.root / "workspace.lock"):
                data = workspace.load()
                work = bind_work(data, candidate, run, request_id)
                snapshot = state["snapshot"]
                existing = next((p for p in data["papers"] if p["sha256"] == snapshot["sha256"]), None)
                if existing and existing.get("work_id") not in (None, work["id"]):
                    raise WorkflowError("This PDF is already attributed to a different work. Inspect the identity conflict.")
                if existing is None:
                    records = workspace.inspect_pdfs(Path(snapshot["path"]))
                    records[0]["title"] = candidate["title"]
                    workspace.append_papers(data, records)
                    existing = data["papers"][-1]
                existing["work_id"] = work["id"]
                if existing["key"] not in work["paper_keys"]:
                    work["paper_keys"].append(existing["key"])
                state["paper_key"] = existing["key"]
                workspace.save(data)
            workspace.prepare()  # Existing RKS PDF ingestion and APW source verification own the reading handoff.
            state.update(status="added", error=None, completed_at=now())
            write_json(state_path, state)
            return {**state, "replayed": False}
        except (OSError, HTTPException, ValueError, KeyError, TypeError, WorkflowError) as exc:
            state.update(status="failed", error=str(exc))
            write_json(state_path, state)
            raise WorkflowError(f"Selection {request_id} needs attention: {exc}. Use discover retry with this request ID.") from exc


def verify_snapshot(snapshot):
    if reading.hash_file(snapshot["path"]) != (snapshot["sha256"], snapshot["size_bytes"]):
        raise WorkflowError("Retained selection PDF changed. Restore its exact bytes before retrying.")


def register(commands):
    parser = commands.add_parser("discover", help="Find candidate papers, inspect saved searches and add selected PDFs.")
    actions = parser.add_subparsers(dest="discovery_action", required=True)
    for name in ("search", "lookup", "list", "show", "select", "retry", "repeat"):
        sub = actions.add_parser(name)
        sub.add_argument("--workspace", type=Path, default=Path("review"))
        sub.add_argument("--json", action="store_true")
        if name in {"search", "lookup"}:
            sub.add_argument("query")
        if name == "search":
            sub.add_argument("--provider", choices=("pubmed", "crossref"), default="pubmed")
            sub.add_argument("--limit", type=int, default=10)
        if name in {"show", "select", "repeat"}:
            sub.add_argument("discovery_id")
        if name == "select":
            sub.add_argument("--candidate", required=True)
            inputs = sub.add_mutually_exclusive_group()
            inputs.add_argument("--pdf", type=Path)
            inputs.add_argument("--source", type=int)
            sub.add_argument("--request-id")
        if name == "retry":
            sub.add_argument("request_id")


def dispatch(workspace, args):
    action = args.discovery_action
    if action in {"search", "lookup"}:
        return discover(workspace, action, args.query, provider=getattr(args, "provider", "pubmed"), limit=getattr(args, "limit", 10))
    if action == "list":
        return inventory(workspace)
    if action == "show":
        return show(workspace, args.discovery_id)
    if action == "repeat":
        return repeat(workspace, args.discovery_id)
    if action == "select":
        return select(workspace, args.discovery_id, args.candidate, pdf=args.pdf, source=args.source, request_id=args.request_id)
    return select(workspace, request_id=args.request_id, retry=True)
