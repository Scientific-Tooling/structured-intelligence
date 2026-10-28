"""Project-scoped evidence retrieval through the public RKS and APW contracts."""
from __future__ import annotations

import sys

from .brief import checked_passages, digest
from .reading import WorkflowError


def search_project(workspace, query: str, *, paper: str | None = None, review: str = "all",
                   mode: str = "lexical", limit: int = 20, offset: int = 0) -> dict:
    data = workspace.load()
    papers = [workspace.select(data, paper)] if paper is not None else data["papers"]
    pending = [p["key"] for p in papers if not p["paper_id"]]
    selected = {(p["paper_id"], p["sha256"]): p for p in papers if p["paper_id"]}
    if not selected:
        raise WorkflowError("Project papers are still being prepared. Use sci resume before searching evidence.")
    args = ["note", "search-evidence", query, "--workspace-id", data["workspace_id"],
            "--source-id", data["source_id"], "--review", review, "--mode", mode,
            "--limit", str(limit), "--offset", str(offset)]
    for paper_id, sha in selected:
        args += ["--paper-source", f"{paper_id}:{sha}"]
    result = workspace.rks(*args)
    if result.get("schema") != "rks.evidence-search.v1" or result.get("workspace_id") != data["workspace_id"]:
        raise WorkflowError("Unexpected RKS evidence-search contract. Install compatible RKS and sci versions.")
    apw = [sys.executable, "-m", "agent_pdf_workbench.dev_cli", "--db-path", str(workspace.root / "events.db")]
    checked = {}
    for entry in result["results"]:
        record, item = entry["record"], entry["record"]["item"]
        identity = (record["paper_id"], record["document"]["sha256"])
        if (identity not in selected or record["workspace_id"] != data["workspace_id"]
                or record["source"]["source_id"] != data["source_id"]
                or entry["revision"] != item["revision"]
                or item["revision"] != digest({k: v for k, v in item.items() if k != "revision"})):
            raise WorkflowError("RKS returned evidence outside the selected project or an inconsistent revision.")
        entry["paper"] = {key: selected[identity][key] for key in ("key", "title")}
        entry["passages"] = checked_passages(apw, record, f"http://127.0.0.1:{data['port']}" if data["port"] else None, checked)
    return {**result, "schema": "scientific-tooling.evidence-search.v1", "question": data["question"],
            "pending_papers": pending, "reader_hint": "Use sci resume with this workspace if the reader is stopped."}
