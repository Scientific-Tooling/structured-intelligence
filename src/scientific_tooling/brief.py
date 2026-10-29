"""Generate a source-linked reading brief from explicitly imported RKS evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from .reading import (
    WorkflowError,
    command_prefix,
    hash_stream,
    run_json,
    session_url,
)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def escape(value: str) -> str:
    """Escape imported Markdown and HTML before placing it in a quoted block."""
    return re.sub(r"([\\`*_{}\[\]<>#|])", r"\\\1", value)


def passage_url(base: str, record: dict, passage: dict) -> str:
    session_url(base, "validate")
    parsed = urlsplit(base)
    query = {"session_id": record["source"]["session_id"], "document_sha256": record["document"]["sha256"],
             "annotation_id": passage["annotation_id"], "page": passage["page"], "passage_sha256": digest(passage)}
    return urlunsplit((parsed.scheme, parsed.netloc, quote(parsed.path or "/", safe="/:@%"), urlencode(query), ""))


def check_passage(apw: list[str], record: dict, passage: dict, *, resolver=None) -> tuple[bool, str]:
    if not passage["quote"].strip():
        return False, "No text quote. Capture and review a source text anchor before citing it."
    try:
        citation = {"session_id": record["source"]["session_id"],
                    "document_sha256": record["document"]["sha256"],
                    "annotation_id": passage["annotation_id"], "page": passage["page"],
                    "passage_sha256": digest(passage)}
        resolved = resolver(**citation) if resolver else run_json(apw + [
            "resolve-passage", "--session-id", record["source"]["session_id"],
            "--document-sha256", record["document"]["sha256"],
            "--annotation-id", passage["annotation_id"], "--page", str(passage["page"]),
            "--passage-sha256", digest(passage),
        ])
        if (resolved.get("schema") != "apw.passage.v1"
                or resolved.get("document_sha256") != record["document"]["sha256"]
                or resolved.get("passage_sha256") != digest(passage)
                or resolved["session"]["paper_ref"] != record["source"]["paper_ref"]):
            raise WorkflowError("Unexpected APW passage response. Check compatible tool versions and the selected APW database.")
        path = Path(resolved["session"]["pdf_uri"])
        if not path.is_absolute():
            raise WorkflowError("Reading snapshot must have an absolute local PDF path.")
        with path.open("rb") as source:
            actual = hash_stream(source)
        if actual != (record["document"]["sha256"], record["document"]["size_bytes"]):
            raise WorkflowError("Source PDF changed. Restore the exact reading snapshot before using this citation.")
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        return False, str(exc)
    return True, "Source and annotation revision verified; the viewer checks page text when opened."


def checked_passages(apw: list[str], record: dict, viewer_url: str | None, checked: dict, *, resolver=None) -> list[dict]:
    """Shared citation checks for search and comparisons; never substitutes a source."""
    passages = []
    for passage in record["item"]["passages"]:
        key = (record["source"]["session_id"], record["document"]["sha256"], digest(passage))
        if key not in checked:
            checked[key] = check_passage(apw, record, passage, resolver=resolver)
        available, reason = checked[key]
        url = passage_url(viewer_url, record, passage) if available and viewer_url else None
        passages.append({**passage, "available": available, "message": reason, "url": url})
    return passages


def render_brief(args: argparse.Namespace, *, allow_empty: bool = False, evidence_payload=None) -> tuple[str, dict]:
    """Validate and render one paper for either a standalone or project brief."""
    session_url(args.viewer_url, "validate-before-reading")
    if not args.question.strip():
        raise WorkflowError("Provide a bounded research question.")
    if args.output.exists():
        raise WorkflowError("Choose a new output path to preserve the existing brief.")
    rks = command_prefix(args.rks_python, "rks", "rks")
    apw = command_prefix(args.apw_python, "agent_pdf_workbench.dev_cli", "apw-dev")
    apw += ["--db-path", str(args.apw_db.resolve())]
    payload = evidence_payload if evidence_payload is not None else run_json(rks + ["note", "evidence", args.paper_id],
                       env={"RKS_DATA_DIR": str(args.rks_data_dir.resolve())})
    paper_id = payload["paper_id"]  # May be the canonical target of an RKS merge.
    selected = []
    for entry in payload["evidence"]:
        record = entry["record"]
        if record["workspace_id"] != args.workspace_id:
            raise WorkflowError("Imported evidence belongs to a different RKS workspace. Check --workspace-id and --rks-data-dir.")
        if record["source"]["source_id"] != args.source_id:
            continue
        if args.rks_note_id and entry["note_id"] not in args.rks_note_id:
            continue
        item = record["item"]
        if (record["schema"] != "scientific-tooling.selected-evidence.v1"
                or entry["paper_id"] != paper_id or entry["revision"] != item["revision"]
                or item["revision"] != digest({key: value for key, value in item.items() if key != "revision"})):
            raise WorkflowError("Unexpected imported evidence contract or revision. Inspect RKS before generating a brief.")
        selected.append(entry)
    if (not selected and not allow_empty) or (args.rks_note_id and set(args.rks_note_id) != {entry["note_id"] for entry in selected}):
        raise WorkflowError("No matching imported evidence, or a selected RKS note is missing from this source workspace.")
    lines = ["# Source-linked reading brief", "", f"Question: {escape(args.question)}", "",
             f"RKS paper: {escape(paper_id)}. Workspace: {escape(args.workspace_id)}.", "",
             "This brief compiles imported reading material. Interpretations retain their recorded review status; "
             "inclusion does not establish scientific support for the question.", ""]
    counts = {"evidence": len(selected), "reviewed": 0, "unreviewed": 0, "linked_passages": 0, "unavailable_passages": 0}
    checked: dict[tuple, tuple[bool, str]] = {}
    for entry in selected:
        record, item = entry["record"], entry["record"]["item"]
        review = item["review"]
        reviewed = review["status"] == "reviewed"
        counts["reviewed" if reviewed else "unreviewed"] += 1
        lines += [f"## {escape(entry['note_id'])}: {'Recorded human review' if reviewed else 'Unreviewed reading material'}", ""]
        if entry.get("status", "current") != "current" or entry.get("reading_status", "unchanged") != "unchanged":
            lines += ["**Needs attention:** this retained import differs from, or cannot be checked against, its current source or reading material.", ""]
        if reviewed:
            lines += [f"Reviewer (caller asserted): {escape(review['reviewer'])}. Reviewed at {escape(review['reviewed_at'])}.",
                      "", f"Review scope: {escape(review['statement'])}", ""]
        content = item["content"]
        interpretation = content["comment"] if item["kind"] == "annotation" else content["title"] + "\n" + content["markdown"]
        if interpretation.strip():
            lines += ["Imported interpretation:", "", *["> " + escape(line) for line in interpretation.splitlines()], ""]
        if not item["passages"]:
            lines += ["No linked source passage was recorded for this note. Capture and review an anchor before citing it.", ""]
        for passage in item["passages"]:
            key = (record["source"]["session_id"], record["document"]["sha256"], digest(passage))
            if key not in checked:
                saved_check = next((p for p in entry.get("passages", []) if p["annotation_id"] == passage["annotation_id"]), None)
                checked[key] = ((saved_check["available"], saved_check["message"]) if saved_check is not None
                                else check_passage(apw, record, passage))
            ready, message = checked[key]
            lines += [f"Source quote, page {passage['page']}:", "",
                      *["> " + escape(line) for line in passage["quote"].splitlines()], ""]
            if ready:
                counts["linked_passages"] += 1
                lines += [f"[Open the supporting passage]({passage_url(args.viewer_url, record, passage)})", ""]
            else:
                counts["unavailable_passages"] += 1
                lines += [f"**Passage unavailable:** {escape(message)}", ""]
        lines += [f"APW {escape(item['kind'])}: {escape(item['id'])}. Imported revision: `{item['revision']}`.", "",
                  f"Source PDF SHA-256: `{record['document']['sha256']}`.", ""]
    lines += ["## Limits", "", "Links require the selected APW database and retained PDF cache. "
              "The viewer rejects changed documents, deleted or edited passage anchors, out-of-range pages, "
              "and quotes that cannot be located unambiguously. Source text layout is checked when the link opens.", ""]
    if not selected:
        lines += ["No evidence has been imported for this paper yet. This is a coverage gap, not a negative finding.", ""]
    return "\n".join(lines), {"schema": "scientific-tooling.research-brief.v1",
                              "path": str(args.output.resolve()), "paper_id": paper_id, "counts": counts}


def generate_brief(args: argparse.Namespace) -> dict:
    text, result = render_brief(args)
    with args.output.open("x", encoding="utf-8") as output:
        output.write(text)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_id")
    parser.add_argument("--question", required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--rks-data-dir", type=Path, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--apw-db", type=Path, required=True)
    parser.add_argument("--rks-note-id", action="append", default=[])
    parser.add_argument("--viewer-url", default="http://127.0.0.1:8790")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rks-python", type=Path)
    parser.add_argument("--apw-python", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = generate_brief(args)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": "research_brief_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
