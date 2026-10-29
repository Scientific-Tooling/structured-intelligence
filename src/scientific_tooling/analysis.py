"""Immutable proposals connecting selected research evidence to an existing analysis skill."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import uuid
from importlib.resources import files
from pathlib import Path

from . import brief, maintenance
from .reading import WorkflowError, hash_stream
from .state import lock, read_json, replace, write_json

REQUEST = "scientific-tooling.analysis-request.v1"
HANDOFF = "scientific-tooling.analysis-handoff.v1"
CHECK = "scientific-tooling.analysis-check.v1"
SKILL = "scrnaseq-differential-expression"


def fields(value, required):
    if not isinstance(value, dict) or set(value) != set(required.split()):
        raise WorkflowError(f"Expected exactly these fields: {required}")


def text(value):
    if not isinstance(value, str) or not value.strip():
        raise WorkflowError("Provide nonempty text for every declared analysis input.")


def strings(value):
    if not isinstance(value, list) or not value:
        raise WorkflowError("Provide a nonempty list of unique text values.")
    for item in value:
        text(item)
    if len(set(value)) != len(value):
        raise WorkflowError("List each selected value once.")


def read_spec(path):
    spec = read_json(path)
    fields(spec, "schema title purpose origin comparison rationale dataset environment analysis")
    if spec["schema"] != REQUEST or spec["purpose"] not in ("demonstration", "research"):
        raise WorkflowError("Use a versioned analysis request with demonstration or research purpose.")
    if spec["origin"] not in ("agent", "human"):
        raise WorkflowError("Record who proposed the analysis: agent or human.")
    for name in ("title", "rationale"):
        text(spec[name])
    fields(spec["comparison"], "id revision cells")
    for name in ("id", "revision"):
        text(spec["comparison"][name])
    strings(spec["comparison"]["cells"])
    fields(spec["dataset"], "path label format provenance")
    fields(spec["environment"], "path description")
    for group in ("dataset", "environment"):
        for value in spec[group].values():
            text(value)
        source = Path(spec[group]["path"]).expanduser()
        spec[group]["path"] = str((source if source.is_absolute() else path.parent / source).resolve())
    if spec["dataset"]["format"] not in ("h5ad", "rds"):
        raise WorkflowError("This skill handoff accepts an annotated h5ad or Seurat rds input.")
    fields(spec["analysis"], "method parameters assumptions expected_outputs resources")
    if spec["analysis"]["method"] not in ("pseudobulk-deseq2", "pseudobulk-edger"):
        raise WorkflowError("This first handoff supports the skill's two replicated pseudobulk methods.")
    parameters = spec["analysis"]["parameters"]
    fields(parameters, "cell_type cell_type_column condition_column reference test sample_column counts_source design "
                       "min_cells_per_sample adjusted_p_threshold log2fc_threshold")
    for key in ("cell_type", "cell_type_column", "condition_column", "reference", "test", "sample_column", "counts_source", "design"):
        text(parameters[key])
    if parameters["reference"] == parameters["test"]:
        raise WorkflowError("The reference and test conditions must differ.")
    if type(parameters["min_cells_per_sample"]) is not int or parameters["min_cells_per_sample"] < 1:
        raise WorkflowError("Minimum cells per sample must be a positive integer.")
    for name in ("adjusted_p_threshold", "log2fc_threshold"):
        if type(parameters[name]) not in (int, float) or parameters[name] < 0:
            raise WorkflowError("Analysis thresholds must be nonnegative numbers.")
    if not 0 < parameters["adjusted_p_threshold"] <= 1:
        raise WorkflowError("Adjusted-p threshold must be between zero (exclusive) and one.")
    for name in ("assumptions", "expected_outputs"):
        strings(spec["analysis"][name])
    fields(spec["analysis"]["resources"], "cpus memory_gb notes")
    resources = spec["analysis"]["resources"]
    if type(resources["cpus"]) is not int or resources["cpus"] < 1:
        raise WorkflowError("Requested CPUs must be a positive integer.")
    if type(resources["memory_gb"]) not in (int, float) or resources["memory_gb"] <= 0:
        raise WorkflowError("Requested memory must be positive.")
    text(resources["notes"])
    brief.digest(spec)  # Reject non-finite JSON numbers before saving a request.
    return spec


def fingerprint(path):
    with Path(path).open("rb") as source:
        sha256, size = hash_stream(source)
    if not size:
        raise WorkflowError(f"Analysis input is empty: {path}")
    return {"path": str(path), "sha256": sha256, "size_bytes": size}


def selected_basis(snapshot, selection, *, require_revision=False):
    comparison = next((c for c in snapshot["comparisons"] if c["id"] == selection["id"]), None)
    if comparison is None:
        raise WorkflowError("Selected comparison is missing from this project's exact source scope.")
    if require_revision and comparison["revision"] != selection["revision"]:
        raise WorkflowError("Comparison changed. Inspect it and use its current revision in a new request.")
    cells = {c["key"]: c for c in comparison["cells"]}
    if not set(selection["cells"]) <= cells.keys():
        raise WorkflowError("A selected comparison cell is missing.")
    selected = [cells[key] for key in sorted(selection["cells"])]
    if any(not c["text"].strip() or not c["evidence"] for c in selected):
        raise WorkflowError("Choose populated comparison cells with explicitly linked evidence.")
    keys = {e["source_key"] for c in selected for e in c["evidence"]}
    evidence = [e for e in snapshot["evidence"] if e["source_key"] in keys]
    return {"comparison_id": comparison["id"], "title": comparison["title"], "criteria": comparison["criteria"],
            "cells": selected, "current_evidence": evidence}


def basis_revision(basis):
    # Reader address and display labels are not scientific revisions. Retain
    # them in the handoff, but don't invalidate it solely because a port changes.
    return brief.digest({
        "cells": [{"key": c["key"], "revision": c["cell_revision"], "review": c["review"],
                   "support": c["support_status"], "evidence": [
                       {"source_key": e["source_key"], "revision": e["revision"], "status": e["status"],
                        "source_status": e["source_status"],
                        "passages": [{k: p[k] for k in ("annotation_id", "available")} for p in e["passages"]]}
                       for e in c["evidence"]]} for c in basis["cells"]],
        "reading": [{k: e[k] for k in ("source_key", "revision", "reading_status", "reading_item")}
                    for e in basis["current_evidence"]],
    })


def attention(basis):
    items = []
    for cell in basis["cells"]:
        if cell["review"]["status"] != "accepted" or cell["support_status"] != "linked":
            items.append({"kind": "comparison", "id": cell["key"],
                          "message": f"Support: {cell['support_status']}; review: {cell['review']['status']}."})
        for evidence in cell["evidence"]:
            if evidence["record"]["item"]["review"]["status"] != "reviewed":
                item = {"kind": "evidence", "id": evidence["note_id"], "message": "Imported evidence is unreviewed."}
                if item not in items:
                    items.append(item)
    for evidence in basis["current_evidence"]:
        if evidence["reading_status"] != "unchanged":
            items.append({"kind": "reading", "id": evidence["note_id"], "message": evidence["reading_status"]})
    return items


def directory(workspace, handoff_id):
    return workspace.root / "analyses" / maintenance.identity(handoff_id)


def render(record):
    spec, basis = record["spec"], record["basis"]
    lines = [f"# {brief.escape(spec['title'])}", "", f"Purpose: **{spec['purpose']}**. Proposal origin: {spec['origin']}.",
             "", "**Draft analysis handoff. No analysis has run and no scientific review of this plan is recorded.**",
             "", f"Handoff: `{record['id']}`. Created: {record['created_at']}.",
             "", f"Question: {brief.escape(record['question'])}", "", "## Rationale", "", brief.escape(spec["rationale"]),
             "", "## Selected support", "", brief.escape(basis["title"]), "",
             f"Comparison: `{basis['comparison_id']}` at revision `{spec['comparison']['revision']}`.", ""]
    criteria = {c["id"]: c["label"] for c in basis["criteria"]}
    for cell in basis["cells"]:
        lines += [f"### {brief.escape(cell['paper']['key'] + ': ' + cell['paper']['title'])}", "",
                  f"Criterion: {brief.escape(criteria[cell['criterion_id']])}", "",
                  brief.escape(cell["text"]), "", f"Conditions: {brief.escape(cell['conditions'])}",
                  f"Support: {cell['support_status']}; recorded comparison review: {cell['review']['status']}.", ""]
        for evidence in cell["evidence"]:
            lines += [f"Evidence {evidence['note_id']} at revision `{evidence['revision']}`; "
                      f"review: {evidence['record']['item']['review']['status']}.", ""]
            for passage in evidence["passages"]:
                lines += [f"> Page {passage['page']}: " + brief.escape(passage["quote"]).replace("\n", "\n> "), "",
                          f"[Open supporting passage]({passage['url']})" if passage["url"] else "Passage unavailable.", ""]
    lines += ["## Inputs and proposed execution", "", f"Dataset: {brief.escape(spec['dataset']['label'])}",
              f"Path: {brief.escape(spec['dataset']['path'])}",
              f"Provenance: {brief.escape(spec['dataset']['provenance'])}",
              f"Retained dataset identity: `{record['inputs']['dataset']['sha256']}`.", "",
              f"Target skill: `{SKILL}`. Method: `{spec['analysis']['method']}`.",
              f"Retained skill identity: `{record['target']['sha256']}`.", "",
              f"Environment: {brief.escape(spec['environment']['description'])}",
              f"Specification path: {brief.escape(spec['environment']['path'])}",
              f"Retained specification identity: `{record['inputs']['environment']['sha256']}`.", "",
              "The exact skill instructions and environment specification are retained beside this file.",
              "The environment is a specification, not a resolved lock or a verified runtime.", "",
              "Parameters (caller supplied; validate against the actual dataset):", "",
              "```json", json.dumps(spec["analysis"]["parameters"], indent=2, ensure_ascii=True), "```", "",
              "Assumptions:", "", *["- " + brief.escape(v) for v in spec["analysis"]["assumptions"]], "",
              "Expected outputs (none generated yet):", "",
              *["- " + brief.escape(v) for v in spec["analysis"]["expected_outputs"]], "",
              f"Requested resources: {spec['analysis']['resources']['cpus']} CPU(s), "
              f"{spec['analysis']['resources']['memory_gb']} GiB. {brief.escape(spec['analysis']['resources']['notes'])}", "",
              "## Before analysis", "",
              "Run `sci analysis check` with this handoff ID and original project path. Inspect every reported change and review gap.",
              "Review the rationale, biological replication, raw counts, contrast, covariates and applicability with the researcher.",
              "The check verifies identities and retained support; it does not validate the dataset's contents, statistical design, "
              "environment installation, or scientific conclusions. Invoke the retained analysis skill only within the user's scope.", ""]
    return "\n".join(lines)


def materialize(path, record):
    fields(record["artifacts"], "SKILL.md environment.txt handoff.md")
    for name, content in record["artifacts"].items():
        target = path / name
        raw = content.encode("utf-8")
        if target.exists() and target.read_bytes() != raw:
            raise WorkflowError(f"Retained handoff artifact changed: {target}")
        if not target.exists():
            # Derived artifacts can be recovered from the committed record.
            fd, pending = tempfile.mkstemp(prefix=".pending-", dir=path)
            try:
                with os.fdopen(fd, "wb") as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
                replace(pending, target)
            finally:
                Path(pending).unlink(missing_ok=True)


def show(workspace, handoff_id):
    path = directory(workspace, handoff_id)
    record = maintenance.verified(path / "record.json", HANDOFF, workspace.load()["workspace_id"])
    if record["id"] != handoff_id:
        raise WorkflowError("Analysis handoff identity disagrees with its directory.")
    fields(record["artifacts"], "SKILL.md environment.txt handoff.md")
    return record


def create(workspace, spec_path, request_id=None):
    spec = read_spec(spec_path.resolve())
    request_id = maintenance.identity(request_id or uuid.uuid4().hex)
    with lock(workspace.root / "workspace.lock"):
        data = workspace.load()
        path = directory(workspace, request_id)
        path.mkdir(parents=True, exist_ok=True)
        request = maintenance.seal({"schema": REQUEST, "id": request_id,
                                    "workspace_id": data["workspace_id"], "spec": spec})
        if (path / "request.json").exists():
            if read_json(path / "request.json") != request:
                raise WorkflowError("This request ID already belongs to a different analysis proposal.")
        else:
            write_json(path / "request.json", request)
        replayed = (path / "record.json").exists()
        if replayed:
            record = show(workspace, request_id)
        else:
            try:
                inputs = {name: fingerprint(spec[name]["path"]) for name in ("dataset", "environment")}
                environment = Path(spec["environment"]["path"]).read_bytes().decode("utf-8")
                if hashlib.sha256(environment.encode("utf-8")).hexdigest() != inputs["environment"]["sha256"]:
                    raise WorkflowError("Environment specification changed while it was being retained.")
                skill = files("scientific_tooling.analysis_skill").joinpath("SKILL.md").read_bytes().decode("utf-8")
                snapshot = maintenance.stable_snapshot(workspace)
                basis = selected_basis(snapshot, spec["comparison"], require_revision=True)
                if inputs != {name: fingerprint(spec[name]["path"]) for name in inputs}:
                    raise WorkflowError("Analysis input changed during handoff creation.")
                current = selected_basis(maintenance.capture(workspace), spec["comparison"])
                if basis_revision(current) != basis_revision(basis):
                    raise WorkflowError("Selected support changed during handoff creation.")
                record = {"schema": HANDOFF, "id": request_id, "workspace_id": data["workspace_id"],
                          "created_at": maintenance.now(), "question": snapshot["question"], "spec": spec,
                          "inputs": inputs, "basis": basis, "basis_revision": basis_revision(basis),
                          "target": {"skill": SKILL, "sha256": hashlib.sha256(skill.encode()).hexdigest()},
                          "execution_status": "not_run", "plan_review": "not_recorded",
                          "attention": attention(basis), "artifacts": {"SKILL.md": skill, "environment.txt": environment}}
                record["artifacts"]["handoff.md"] = render(record)
                record = maintenance.seal(record)
                write_json(path / "record.json", record)  # Commit before publishing recoverable derived files.
            except (WorkflowError, OSError, ValueError) as exc:
                raise WorkflowError(f"{exc}\nRequest retained: {request_id}. Retry with the same spec and request ID.") from exc
        materialize(path, record)
    return {"handoff": record, "path": str(path / "handoff.md"), "replayed": replayed, "freshness": "unchecked"}


def check(workspace, handoff_id):
    record = show(workspace, handoff_id)
    issues = []
    for name, expected in record["inputs"].items():
        try:
            if fingerprint(expected["path"]) != expected:
                issues.append({"kind": name, "message": "Input bytes changed since this handoff."})
        except (OSError, WorkflowError) as exc:
            issues.append({"kind": name, "message": str(exc)})
    for name, content in record["artifacts"].items():
        path = directory(workspace, handoff_id) / name
        if not path.is_file() or path.read_bytes() != content.encode("utf-8"):
            issues.append({"kind": "artifact", "message": f"{name} is missing or changed; inspect before retrying creation."})
    try:
        basis = selected_basis(maintenance.stable_snapshot(workspace), record["spec"]["comparison"])
        if basis_revision(basis) != record["basis_revision"]:
            issues.append({"kind": "support", "message": "Selected evidence, reading material, comparison or review changed."})
        needs_attention = attention(basis)
    except (WorkflowError, OSError, ValueError) as exc:
        issues.append({"kind": "support", "message": str(exc)})
        needs_attention = record["attention"]
    return {"schema": CHECK, "id": handoff_id, "checked_at": maintenance.now(),
            "freshness": "outdated" if issues else "current", "issues": issues, "attention": needs_attention,
            "execution_status": "not_run", "plan_review": "not_recorded",
            "scope": "File identities and selected support only; no dataset, runtime or statistical validation."}


def inventory(workspace):
    workspace.load()
    items, pending = [], []
    for path in sorted((workspace.root / "analyses").glob("*/request.json")):
        if (path.parent / "record.json").exists():
            record = show(workspace, path.parent.name)
            items.append({"id": record["id"], "title": record["spec"]["title"], "created_at": record["created_at"],
                          "purpose": record["spec"]["purpose"], "freshness": "unchecked", "execution_status": "not_run"})
        else:
            request = maintenance.verified(path, REQUEST, workspace.load()["workspace_id"])
            if request["id"] != path.parent.name:
                raise WorkflowError("Analysis request identity disagrees with its directory.")
            pending.append(maintenance.identity(path.parent.name))
    return {"handoffs": items, "pending_requests": pending}


def register(commands):
    parser = commands.add_parser("analysis", help="Retain an evidence-linked draft handoff to an analysis skill.")
    actions = parser.add_subparsers(dest="analysis_action", required=True)
    for name in ("create", "list", "show", "check"):
        sub = actions.add_parser(name)
        sub.add_argument("--workspace", type=Path, default=Path("review"))
        sub.add_argument("--json", action="store_true")
        if name == "create":
            sub.add_argument("spec", type=Path)
            sub.add_argument("--request-id")
        if name in {"show", "check"}:
            sub.add_argument("handoff_id")


def dispatch(workspace, args):
    if args.analysis_action == "create":
        return create(workspace, args.spec, args.request_id)
    if args.analysis_action == "list":
        return inventory(workspace)
    return (show if args.analysis_action == "show" else check)(workspace, args.handoff_id)
