"""Human-friendly commands and JSON results for agent hosts."""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
import webbrowser
from importlib.resources import files
from pathlib import Path

from . import __version__, comparison, discovery, server
from .reading import WorkflowError
from .workspace import Workspace


def doctor() -> dict:
    checks = []
    for package in ("research-knowledge-substrate", "agent-pdf-workbench"):
        try:
            checks.append({"name": package, "ok": True, "version": importlib.metadata.version(package)})
        except importlib.metadata.PackageNotFoundError:
            checks.append({"name": package, "ok": False, "message": "Reinstall scientific-tooling with its pinned dependencies."})
    try:
        from agent_pdf_workbench.viewer_server import WEB_DIR, create_viewer_server
        checks.append({"name": "embedded_reader", "ok": callable(create_viewer_server) and (WEB_DIR / "app.js").is_file()})
    except ImportError:
        checks.append({"name": "embedded_reader", "ok": False, "message": "APW is older than this workflow package."})
    return {"ok": all(check["ok"] for check in checks), "python": sys.version.split()[0],
            "version": __version__, "checks": checks}


def install_skill(destination: Path) -> dict:
    destination = destination.expanduser().resolve() / "paper-to-brief"
    if destination.exists():
        raise WorkflowError(f"Skill already exists at {destination}. Inspect it before replacing it.")
    source = files("scientific_tooling.agent_skill")
    # Copy only the runnable skill's documented files, not Python cache/configuration.
    destination.mkdir(parents=True)
    for relative in ("SKILL.md", "agents/openai.yaml", "agents/claude.yaml"):
        target = destination / relative
        target.parent.mkdir(exist_ok=True)
        target.write_text(source.joinpath(relative).read_text(encoding="utf-8"), encoding="utf-8")
    return {"installed": str(destination), "next_action": "Reload skills in your agent host, then ask for paper-to-brief."}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sci", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("init", "Start a research question before selecting any papers."),
        ("start", "Start a project with one or more PDFs and a question."),
        ("add", "Add PDFs to an existing project; identical files are reused."),
        ("papers", "List project papers and their reading progress."),
        ("search", "Find imported quotations and commentary across this project."),
        ("open", "Open a paper from this project."),
        ("resume", "Resume the saved reading workspace and open its reader."),
        ("status", "Show saved progress and available annotations."),
        ("preview", "Preview explicitly selected evidence without importing."),
        ("apply", "Apply an inspected preview; never imply scientific review."),
        ("brief", "Generate a source-linked brief from imported evidence."),
        ("annotate", "Save an exact page/quote as an unreviewed reading annotation."),
        ("stop", "Stop only this workspace's owned reader."),
        ("doctor", "Check installation and reader capabilities."),
        ("skill", "Install the bundled agent skill into a chosen skills directory."),
        ("serve", argparse.SUPPRESS),
    ):
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("--json", action="store_true", help="Return structured results for agents.")
        if name not in {"doctor", "skill"}:
            sub.add_argument("--workspace", type=Path, default=Path("review"))
        if name in {"start", "add"}:
            sub.add_argument("pdf", type=Path, nargs="+")
        if name in {"start", "init"}:
            sub.add_argument("--question", required=True)
            sub.add_argument("--port", type=int, default=0, help="Optional fixed local port; default assigns and remembers a free port.")
        if name == "open":
            sub.add_argument("paper", help="Project paper key (p1, p2, …) or RKS paper ID.")
        if name in {"resume", "status", "annotate", "preview", "search"}:
            sub.add_argument("--paper", help="Project paper key (p1, p2, …) or RKS paper ID.")
        if name == "search":
            sub.add_argument("query")
            sub.add_argument("--review", choices=("all", "reviewed", "unreviewed"), default="all")
            sub.add_argument("--mode", choices=("lexical", "phrase"), default="lexical")
            sub.add_argument("--limit", type=int, default=20)
            sub.add_argument("--offset", type=int, default=0)
        if name in {"start", "resume", "open"}:
            sub.add_argument("--no-open", action="store_true", help="Return the URL without opening a browser.")
        if name == "preview":
            sub.add_argument("--annotation", action="append", default=[])
            sub.add_argument("--note", action="append", default=[])
        if name == "apply":
            sub.add_argument("preview_id", help="The exact preview ID you inspected.")
            sub.add_argument("--accept-updates", action="store_true", help="Explicitly accept reviewed revision changes; other conflicts still fail.")
        if name == "annotate":
            sub.add_argument("--page", type=int, required=True)
            sub.add_argument("--quote", required=True)
            sub.add_argument("--comment", default="")
        if name == "skill":
            sub.add_argument("--dest", type=Path, required=True, help="Agent's skills directory, e.g. ~/.codex/skills or ~/.claude/skills.")
    comparison.register(commands)
    discovery.register(commands)
    return parser


def dispatch(args) -> dict:
    if args.command == "doctor":
        return doctor()
    if args.command == "skill":
        return install_skill(args.dest)
    workspace = Workspace(args.workspace)
    if args.command == "init":
        workspace.initialize(args.question, args.port)
        return workspace.summary()
    if args.command == "discover":
        return discovery.dispatch(workspace, args)
    if args.command == "compare":
        return comparison.dispatch(workspace, args)
    if args.command == "search":
        return workspace.search(args.query, paper=args.paper, review=args.review, mode=args.mode,
                                limit=args.limit, offset=args.offset)
    if args.command == "add":
        added = workspace.add(args.pdf)
        return {**workspace.summary(), "added": added, "running": server.running(workspace, detailed=False) is not None}
    if args.command == "papers":
        data = workspace.load()
        return {"question": data["question"], "papers": [workspace.paper_summary(data, p) for p in data["papers"]],
                "works": data.get("works", [])}
    if args.command in {"start", "resume", "open"}:
        diagnosis = doctor()
        if not diagnosis["ok"]:
            raise WorkflowError("Installation check failed: " + json.dumps(diagnosis))
        if args.command == "start":
            workspace.create(args.pdf, args.question, args.port)
        else:
            workspace.load()
        paper = getattr(args, "paper", None)
        workspace.select(workspace.load(), paper, default=True)
        result = server.ensure_running(workspace, paper=paper)
        if not args.no_open:
            result["browser_opened"] = webbrowser.open(result["viewer_url"])
        return result
    if args.command == "serve":
        server.serve(workspace)
        return {"stopped": True}
    if args.command == "status":
        workspace.load()
        return server.running(workspace, paper=args.paper) or {**workspace.summary(args.paper), "running": False}
    if args.command == "stop":
        return server.stop(workspace)
    if args.command == "preview":
        return {"preview": workspace.preview(args.annotation, args.note, args.paper)}
    if args.command == "apply":
        return workspace.apply(args.preview_id, accept_updates=args.accept_updates)
    if args.command == "brief":
        server.ensure_running(workspace, detailed=False)
        return {"brief": workspace.make_brief()}
    if args.command == "annotate":
        return server.annotate(workspace, args.page, args.quote, args.comment, args.paper)
    raise WorkflowError("Unsupported command")


def print_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return
    if result.get("schema") == discovery.RUN_SCHEMA:
        print(f"Discovery {result['id']} ({result['status']})\n{result['provider']}: {result['query']}\nRetrieved: {result['retrieved_at']}")
        if result["error"]:
            print(result["error"])
        for candidate in result["candidates"]:
            print(f"\n{candidate['id']}. {candidate['title']} ({candidate['year'] or 'year unknown'})")
            print(", ".join(candidate["authors"]) + " · " + (candidate["venue"] or ""))
            print("Identifiers: " + json.dumps(candidate["identifiers"]) + "\n" + candidate["landing_url"])
            for index, source in enumerate(candidate["pdf_sources"], 1):
                print(f"  PDF source {index} (unverified): {source['url']}")
            if not candidate["pdf_sources"]:
                print("  No PDF source reported. Keep this reference or select a local PDF.")
        print("Discovery does not add papers, import evidence or record review. Use discover select for explicit selections.")
        return
    if result.get("schema") == discovery.SELECTION_SCHEMA:
        print(f"Selection {result['request']['id']}: {result['status']}")
        if result["paper_key"]:
            print(f"Paper: {result['paper_key']}. Use sci resume to open the retained PDF.")
        if result["error"]:
            print(result["error"])
        return
    if result.get("schema") == "scientific-tooling.discovery-list.v1":
        for run in result["discoveries"]:
            print(f"{run['id']}  {run['provider']}  {run['status']}  {run['query']}")
        for work in result["works"]:
            print(f"{work['id']}  {work['title']}  PDFs: {', '.join(work['paper_keys']) or 'none'}")
        for selection in result["selections"]:
            print(f"Selection {selection['request']['id']}: {selection['status']} · {selection['candidate_title']}")
            if selection["error"]:
                print("  " + selection["error"])
        return
    if "comparison" in result:
        item = result["comparison"]
        print(item["markdown"])
        print(f"Comparison: {item['id']}\nRevision: {item['revision']}")
        if result.get("request_id"):
            print(f"Saved request: {result['request_id']}")
        return
    if "comparisons" in result:
        for item in result["comparisons"]:
            print(f"{item['id']}  {item['title']}")
        if not result["comparisons"]:
            print("No comparisons yet. Use sci compare create with a title and criteria.")
        return
    if result.get("schema") == "scientific-tooling.evidence-search.v1":
        print(f"{result['total']} imported evidence matches for {result['query']!r}.")
        for entry in result["results"]:
            item = entry["record"]["item"]
            print(f"\n{entry['rank']}. {entry['paper']['key']}: {entry['paper']['title']} ({item['review']['status']})")
            print(f"   Evidence: {entry['note_id']} / {item['id']} · revision {entry['revision']}")
            print(f"   Source SHA-256: {entry['record']['document']['sha256']}")
            for match in entry["matches"]:
                location = f" (page {match['page']})" if match.get("page") else ""
                print(f"   {match['role'].capitalize()}{location}: {match['text']}")
            for passage in entry["passages"]:
                print(f"   Page {passage['page']}: {passage['url'] or passage['message']}")
            if not entry["passages"]:
                print("   No supporting passage is linked to this note.")
        if result["unavailable_evidence"]:
            print(f"{len(result['unavailable_evidence'])} imports need attention; inspect --json for details.")
        if result["pending_papers"]:
            print("Papers still being prepared: " + ", ".join(result["pending_papers"]))
        if result["has_more"]:
            print(f"More matches: repeat with --offset {result['offset'] + result['limit']}.")
        print("Search covers imported evidence only. " + result["reader_hint"])
        return
    if "phase" in result:
        print(f"{result['question']}\nProgress: {result['phase']}\nWorkspace: {result['workspace']}")
        if result.get("running"):
            print(f"Reader: {result['viewer_url']}\nSelect highlights in the reader, then preview and import the evidence.")
        elif result["phase"] == "discovering":
            print(result["next_action"])
        else:
            print("Reader is stopped. Use sci resume with this workspace.")
    if "papers" in result:
        for paper in result["papers"]:
            print(f"  {paper['key']}  {paper['title']}  ({paper['phase']})")
        if result["papers"]:
            print("Open a paper with sci open p1 --workspace <project>.")
    if result.get("preview"):
        preview = result["preview"]
        print(f"Preview: {preview['id']}\nChanges: {json.dumps(preview['counts'])}")
        for item in preview["items"]:
            for passage in item["passages"]:
                print(f"  Page {passage['page']}: {passage['quote']}")
        if "phase" not in result:
            print("Full evidence and conflicts are available with --json. Apply using this preview ID after inspection.")
    if result.get("brief"):
        print(f"Brief: {result['brief']['path']}")
    if not any(key in result for key in ("phase", "preview", "brief", "papers")):
        print(json.dumps(result, indent=2))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = dispatch(args)
        if args.command == "serve":
            return 0  # Internal child emitted its single startup acknowledgement.
        print_result(result, args.json)
        if result.get("ok") is False or result.get("applied") is False or (result.get("preview") or {}).get("counts", {}).get("conflict", 0):
            return 2
        return 0
    except (WorkflowError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"error": "workflow_failed", "message": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
