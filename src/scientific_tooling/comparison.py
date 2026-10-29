"""Project comparison orchestration. RKS owns revisions, history and human reviews."""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

from .brief import checked_passages, escape
from .reading import WorkflowError, hash_file
from .state import hex_id, lock, read_json, write_json


def register(commands):
    parser = commands.add_parser("compare", help="Build evidence-linked comparisons and record scoped human reviews.")
    actions = parser.add_subparsers(dest="compare_action", required=True)
    for name in ("create", "list", "show", "set", "review", "retry"):
        sub = actions.add_parser(name)
        sub.add_argument("--workspace", type=Path, default=Path("review"))
        sub.add_argument("--json", action="store_true")
        if name in {"show", "set", "review"}:
            sub.add_argument("comparison_id")
        if name == "show":
            sub.add_argument("--history", action="store_true")
        if name == "create":
            sub.add_argument("--title", required=True)
            sub.add_argument("--criterion", action="append", required=True)
        if name in {"set", "review"}:
            sub.add_argument("--paper", required=True)
            sub.add_argument("--criterion", required=True)
            sub.add_argument("--expected-revision", required=True, help="Comparison revision returned by show.")
        if name == "set":
            sub.add_argument("--text", required=True, help="Interpretation; an empty string records a gap.")
            sub.add_argument("--conditions", default="")
            sub.add_argument("--origin", choices=("human", "agent"), required=True)
            sub.add_argument("--evidence", action="append", default=[], help="RKS note_id@revision; repeat for selected evidence.")
        if name == "review":
            sub.add_argument("--reviewer", required=True)
            sub.add_argument("--scope", required=True)
            sub.add_argument("--decision", choices=("accepted", "needs_changes"), required=True)
            sub.add_argument("--statement", required=True)
        if name in {"create", "set", "review"}:
            sub.add_argument("--request-id", help="UUID hex for exact retry; generated and saved when omitted.")
        if name == "retry":
            sub.add_argument("request_id")


def dispatch(workspace, args):
    action = args.compare_action
    payload = None
    if action == "create":
        payload = {"title": args.title, "criteria": args.criterion}
    elif action == "set":
        selections = []
        for value in args.evidence:
            if "@" not in value:
                raise WorkflowError("Select evidence as note_id@revision from sci search --json")
            note_id, revision = value.rsplit("@", 1)
            selections.append({"note_id": note_id, "revision": revision})
        payload = {"paper": args.paper, "criterion_id": args.criterion, "text": args.text,
                   "conditions": args.conditions, "origin": args.origin, "evidence": selections}
    elif action == "review":
        payload = {"paper": args.paper, "criterion_id": args.criterion,
                   **{k: getattr(args, k) for k in ("reviewer", "scope", "decision", "statement")}}
    return operate(workspace, action, comparison_id=getattr(args, "comparison_id", None), payload=payload,
                   expected_revision=getattr(args, "expected_revision", None), request_id=getattr(args, "request_id", None),
                   history=getattr(args, "history", False))


def evidence_options(workspace):
    data, papers, args = scope(workspace)
    result = workspace.rks("comparison", "evidence", *args)
    for entry in result["evidence"]:
        record = entry["record"]
        paper = papers[f"{record['paper_id']}:{record['document']['sha256']}"]
        entry["paper"] = {k: paper[k] for k in ("key", "title")}
    return result


def scope(workspace):
    data = workspace.load()
    if not data["papers"]:
        raise WorkflowError("Select a PDF before comparing findings.")
    if any(not p["paper_id"] for p in data["papers"]):
        raise WorkflowError("Resume this project to finish preparing its papers before comparing findings.")
    sources = paper_sources(data["papers"])
    args = ["--workspace-id", data["workspace_id"], "--source-id", data["source_id"]]
    for identity in sources:
        args += ["--paper-source", identity]
    return data, sources, args


def paper_sources(papers):
    """Exact RKS paper sources (paper_id:sha256) of the papers that have an RKS identity."""
    return {f"{p['paper_id']}:{p['sha256']}": p for p in papers if p["paper_id"]}


def enrich(workspace, result, data, papers, *, checked=None, resolver=None, file_hash=hash_file):
    if result.get("schema") != "rks.comparison.v1" or result.get("workspace_id") != data["workspace_id"]:
        raise WorkflowError("Unexpected RKS comparison response. Check compatible tool versions.")
    if result["source_id"] != data["source_id"] or not set(result["paper_sources"]) <= set(papers):
        raise WorkflowError("Comparison returned sources outside this project")
    apw = [sys.executable, "-m", "agent_pdf_workbench.dev_cli", "--db-path", str(workspace.root / "events.db")]
    checked = {} if checked is None else checked
    for cell in result["cells"]:
        cell["paper"] = {k: papers[cell["paper_source"]][k] for k in ("key", "title")}
        for evidence in cell["evidence"]:
            evidence["passages"] = checked_passages(apw, evidence["record"],
                f"http://127.0.0.1:{data['port']}" if data["port"] else None, checked,
                resolver=resolver, file_hash=file_hash)
        if any(not p["available"] for e in cell["evidence"] for p in e["passages"]):
            cell["support_status"] = "stale"
            if cell["review"]["latest"]:
                cell["review"]["status"] = "stale"
            cell["source_warning"] = "A supporting passage is unavailable. Inspect its original evidence before reviewing."
    result["schema"] = "scientific-tooling.comparison.v1"
    result["papers"] = [{"paper_source": identity, **{k: papers[identity][k] for k in ("key", "title")}}
                        for identity in result["paper_sources"]]
    result["excluded_papers"] = [p["key"] for identity, p in papers.items() if identity not in result["paper_sources"]]
    result["markdown"] = render_markdown(result)
    return result


def render_markdown(result):
    lines = [f"# {escape(result['title'])}", "", f"Question: {escape(result['question'])}", "",
             "Interpretations are proposals tied to selected imported evidence. Links and review decisions do not establish scientific validity.", ""]
    for criterion in result["criteria"]:
        lines += [f"## {escape(criterion['label'])}", ""]
        for cell in (c for c in result["cells"] if c["criterion_id"] == criterion["id"]):
            lines += [f"### {escape(cell['paper']['key'] + ': ' + cell['paper']['title'])}", "",
                      f"Support: {cell['support_status']}. Comparison review: {cell['review']['status']}.", "",
                      f"Interpretation ({cell['origin']}): {escape(cell['text']) if cell['text'] else 'Missing information.'}", "",
                      f"Conditions: {escape(cell['conditions']) if cell['conditions'] else 'Not recorded.'}", ""]
            for evidence in cell["evidence"]:
                lines += [f"Evidence {evidence['note_id']}, revision {evidence['revision']}; imported review: {evidence['record']['item']['review']['status']}.", ""]
                for passage in evidence["passages"]:
                    lines += [f"> Page {passage['page']}: " + escape(passage["quote"]).replace("\n", "\n> "), "",
                              f"[Open supporting passage]({passage['url']})" if passage["url"] else escape(passage["message"]), ""]
            latest = cell["review"]["latest"]
            if latest:
                lines += [f"Review by {escape(latest['reviewer'])} at {escape(latest['reviewed_at'])}: {latest['decision']}.",
                          f"Scope: {escape(latest['scope'])}. {escape(latest['statement'])}", ""]
    if result["excluded_papers"]:
        lines += ["Papers added after this comparison: " + ", ".join(result["excluded_papers"]), ""]
    return "\n".join(lines)


def operate(workspace, action, *, comparison_id=None, payload=None, expected_revision=None, request_id=None, history=False):
    data, papers, args = scope(workspace)
    if action == "list":
        return workspace.rks("comparison", "list", *args)
    if action == "show":
        result = workspace.rks("comparison", "show", comparison_id, *args, *(["--history"] if history else []))
        return {"comparison": enrich(workspace, result, data, papers)}
    if action not in {"create", "set", "review", "retry"}:
        raise WorkflowError("Unknown comparison operation")
    request_id = hex_id(request_id or uuid.uuid4().hex, "Use a UUID hex request ID from this project")
    path = workspace.root / "comparisons" / "requests" / f"{request_id}.json"
    with lock(workspace.root / "workspace.lock"):
        data, papers, args = scope(workspace)
        if action == "retry":
            request = read_json(path)
        else:
            payload = dict(payload or {})
            if action == "create":
                payload["question"] = data["question"]
            else:
                paper = workspace.select(data, payload.pop("paper"))
                payload["paper_source"] = f"{paper['paper_id']}:{paper['sha256']}"
            request = {"schema": "rks.comparison-request.v1", "request_id": request_id, "action": action,
                       "comparison_id": comparison_id, "expected_revision": expected_revision, "payload": payload}
            if path.exists() and read_json(path) != request:
                raise WorkflowError("Request ID already belongs to a different saved operation")
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                write_json(path, request)
        if request["action"] == "create":
            if not (workspace.root / "rks" / "rks.sqlite3").is_file():
                raise WorkflowError("The RKS database is missing. Restore it before creating comparisons.")
            workspace.rks("migrate")  # Explicit comparison creation is a write; reads never migrate.
        if request["action"] == "review" and request["payload"]["decision"] == "accepted":
            view = operate(workspace, "show", comparison_id=request["comparison_id"])["comparison"]
            cell = next((c for c in view["cells"] if c["paper_source"] == request["payload"]["paper_source"]
                         and c["criterion_id"] == request["payload"]["criterion_id"]), None)
            if cell is None or cell["support_status"] != "linked":
                raise WorkflowError("This entry lacks current supporting passages. Resolve its gaps before accepting it.")
        try:
            result = workspace.rks("comparison", "apply", str(path), *args)
        except WorkflowError as exc:
            raise WorkflowError(f"{exc}\nRequest retained at {path}. Reload a changed comparison; retry a lost response with this request ID.") from exc
    result["comparison"] = enrich(workspace, result["comparison"], data, papers)
    return {**result, "request_id": request_id, "request_path": str(path)}
