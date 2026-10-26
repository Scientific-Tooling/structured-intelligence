"""Prepare selected APW evidence and an RKS dry-run plan through public CLIs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_reading import (
    WorkflowError,
    command_prefix,
    hash_stream,
    run_json,
    validate_source,
)


def prepare_evidence(args: argparse.Namespace) -> dict:
    handoff = json.loads(args.handoff.read_text(encoding="utf-8-sig"))
    if handoff.get("schema") != "scientific-tooling.reading-handoff.v1":
        raise WorkflowError("Expected a saved reading-handoff.v1 file")
    paper_id = handoff["source"]["paper_id"]
    original = validate_source(handoff["source"], paper_id)
    snapshot = handoff["snapshot"]
    snapshot_path = Path(snapshot["path"])
    if not snapshot_path.is_absolute():
        raise WorkflowError("Reading snapshot path must be absolute")
    expected = (original["sha256"], original["size_bytes"])
    with snapshot_path.open("rb") as source:
        if hash_stream(source) != expected or (snapshot["sha256"], snapshot["size_bytes"]) != expected:
            raise WorkflowError("Reading snapshot changed; restore its exact bytes before exporting evidence")
    bundle_path, plan_path = args.bundle.resolve(), args.plan.resolve()
    if bundle_path == plan_path or bundle_path.exists() or plan_path.exists():
        raise WorkflowError("Choose distinct new paths for the evidence bundle and dry-run plan")
    apw = command_prefix(args.apw_python, "agent_pdf_workbench.dev_cli", "apw-dev")
    command = apw + ["--db-path", handoff["apw"]["db_path"], "export-evidence",
                     "--session-id", handoff["apw"]["session_id"], "--source-id", args.source_id]
    for kind, values in (("annotation", args.annotation_id), ("note", args.note_id)):
        for value in values:
            command += [f"--{kind}-id", value]
    if args.reviews:
        command += ["--reviews", str(args.reviews)]
    bundle = run_json(command)
    expected_ref = f"rks:{handoff['workspace_id']}:{paper_id}:sha256:{original['sha256']}"
    if (bundle.get("schema") != "scientific-tooling.selected-evidence.v1"
            or bundle.get("workspace_id") != handoff["workspace_id"] or bundle.get("paper_id") != paper_id
            or bundle["source"]["paper_ref"] != expected_ref or handoff["apw"]["paper_ref"] != expected_ref
            or bundle["source"]["source_id"] != args.source_id
            or bundle["source"]["session_id"] != handoff["apw"]["session_id"]
            or bundle["document"]["sha256"] != original["sha256"]
            or bundle["document"]["size_bytes"] != original["size_bytes"]
            or Path(bundle["document"]["path"]).resolve() != snapshot_path.resolve()):
        raise WorkflowError("APW export does not match the saved reading handoff")
    with bundle_path.open("x", encoding="utf-8") as output:
        json.dump(bundle, output, indent=2, ensure_ascii=True)
        output.write("\n")
    rks = command_prefix(args.rks_python, "rks", "rks")
    plan = run_json(
        rks + ["note", "import-evidence", str(bundle_path), "--workspace-id", handoff["workspace_id"]],
        env={"RKS_DATA_DIR": handoff["rks_data_dir"]}, accepted_returncodes=(0, 2),
    )
    if plan.get("schema") != "rks.evidence-import-plan.v1" or plan.get("applied") is not False:
        raise WorkflowError("Unexpected RKS dry-run response; inspect the saved bundle")
    with plan_path.open("x", encoding="utf-8") as output:
        json.dump(plan, output, indent=2, ensure_ascii=True)
        output.write("\n")
    return {"schema": "scientific-tooling.evidence-preparation.v1", "bundle": str(bundle_path),
            "plan": str(plan_path), "workspace_id": handoff["workspace_id"], "counts": plan["counts"],
            "applied": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--source-id", required=True, help="Stable unique name for this APW database.")
    parser.add_argument("--annotation-id", action="append", default=[])
    parser.add_argument("--note-id", action="append", default=[])
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--bundle", type=Path, required=True, help="New JSON output file.")
    parser.add_argument("--plan", type=Path, required=True, help="New dry-run JSON output file.")
    parser.add_argument("--rks-python", type=Path)
    parser.add_argument("--apw-python", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare_evidence(args)
    except (WorkflowError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": "evidence_preparation_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 2 if result["counts"]["conflict"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
