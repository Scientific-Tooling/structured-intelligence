"""Open a verified RKS source in APW using their public CLIs (Python 3.10+)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit


class WorkflowError(Exception):
    """An actionable source, configuration, or command failure."""


def run_json(command: list[str], *, env: dict[str, str] | None = None,
             accepted_returncodes: tuple[int, ...] = (0,)) -> dict:
    child_env = {**os.environ, "PYTHONIOENCODING": "utf-8", **(env or {})}
    try:
        result = subprocess.run(
            command,
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError(f"Could not run {command[0]}: {exc}") from exc
    if result.returncode not in accepted_returncodes:
        raise WorkflowError(f"Command failed ({result.returncode}): {result.stderr.strip() or result.stdout.strip()}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise WorkflowError(f"{command[0]} did not return JSON; check the installed tool version.") from exc
    if not isinstance(payload, dict):
        raise WorkflowError(f"{command[0]} returned an unexpected JSON value.")
    return payload


def command_prefix(python: Path | None, module: str, executable: str) -> list[str]:
    return [str(python), "-m", module] if python else [executable]


def validate_source(source: dict, paper_id: str) -> dict:
    if source.get("schema") != "rks.paper-source.v1" or source.get("paper_id") != paper_id:
        raise WorkflowError("Unexpected RKS source contract or paper identity; update RKS and retry.")
    pdf = source.get("pdf")
    if not isinstance(pdf, dict):
        raise WorkflowError("RKS did not return a local PDF descriptor.")
    if not isinstance(pdf.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", pdf["sha256"]):
        raise WorkflowError("RKS returned an invalid PDF SHA-256.")
    if type(pdf.get("size_bytes")) is not int or pdf["size_bytes"] <= 0:
        raise WorkflowError("The source PDF is empty or its byte count is invalid.")
    if not isinstance(pdf.get("path"), str) or not Path(pdf["path"]).is_absolute():
        raise WorkflowError("RKS must return an absolute local PDF path.")
    return pdf


def hash_stream(source, destination=None) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(block)
        size += len(block)
        if destination is not None:
            destination.write(block)
    return digest.hexdigest(), size


def snapshot_pdf(pdf: dict, cache_dir: Path) -> Path:
    """Publish only complete copies whose bytes match the RKS descriptor."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{pdf['sha256']}.pdf"
    expected = (pdf["sha256"], pdf["size_bytes"])
    if target.exists():
        with target.open("rb") as cached:
            if hash_stream(cached) != expected:
                raise WorkflowError(
                    f"Cached PDF has changed: {target}. Preserve it for inspection and use a new cache directory."
                )
        return target
    pending = None
    try:
        with tempfile.NamedTemporaryFile(dir=cache_dir, prefix=".pending-", suffix=".pdf", delete=False) as output:
            pending = Path(output.name)
            with Path(pdf["path"]).open("rb") as source:
                actual = hash_stream(source, output)
        if actual != expected:
            raise WorkflowError("The RKS PDF changed during handoff; retry after the source file is stable.")
        pending.replace(target)
        return target
    finally:
        if pending is not None:
            pending.unlink(missing_ok=True)


def session_url(base: str, session_id: str) -> str:
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.query or parsed.fragment:
        raise WorkflowError("--viewer-url must be an HTTP(S) base URL without a query or fragment.")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", urlencode({"session_id": session_id}), ""))


def open_reading(args: argparse.Namespace) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", args.workspace_id):
        raise WorkflowError(
            "--workspace-id must be 1-64 letters, digits, dots, underscores, or hyphens, "
            "starting with a letter or digit."
        )
    session_url(args.viewer_url, "validate-before-writing")
    data_dir = args.rks_data_dir.expanduser().resolve()
    cache_dir = args.cache_dir.expanduser().resolve()
    db_path = args.apw_db.expanduser().resolve()
    rks = command_prefix(args.rks_python, "rks", "rks")
    apw = command_prefix(args.apw_python, "agent_pdf_workbench.dev_cli", "apw-dev")
    apw += ["--db-path", str(db_path)]
    source = run_json(rks + ["papers", "source", args.paper_id], env={"RKS_DATA_DIR": str(data_dir)})
    pdf = validate_source(source, args.paper_id)
    snapshot = snapshot_pdf(pdf, cache_dir)
    paper_ref = f"rks:{args.workspace_id}:{args.paper_id}:sha256:{pdf['sha256']}"
    session = None
    # Listing a missing APW database would initialize it. Only open-paper should
    # create the workspace when there is no prior reading session.
    offset = 0
    while db_path.is_file():
        page = run_json(apw + ["list-sessions", "--paper-ref", paper_ref, "--open-only", "--offset", str(offset)])
        for candidate in page["sessions"]:
            if (
                candidate["paper_ref"] == paper_ref
                and candidate["pdf_uri"] == str(snapshot)
                and candidate["closed_at"] is None
            ):
                session = candidate
                break
        if session or not page["has_more"]:
            break
        next_offset = page["next_offset"]
        if type(next_offset) is not int or next_offset <= offset:
            raise WorkflowError("APW returned invalid session pagination.")
        offset = next_offset
    reused = session is not None
    if session is None:
        session = run_json(
            apw
            + [
                "open-paper",
                "--paper-ref",
                paper_ref,
                "--pdf-uri",
                str(snapshot),
                "--agent-id",
                "agent:structured-intelligence",
            ]
        )
    return {
        "schema": "scientific-tooling.reading-handoff.v1",
        "workspace_id": args.workspace_id,
        "rks_data_dir": str(data_dir),
        "source": source,
        "snapshot": {"path": str(snapshot), "sha256": pdf["sha256"], "size_bytes": pdf["size_bytes"]},
        "apw": {
            "db_path": str(db_path),
            "paper_ref": paper_ref,
            "session_id": session["id"],
            "reused_session": reused,
            "viewer_url": session_url(args.viewer_url, session["id"]),
            "pdf_root": str(cache_dir),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_id")
    parser.add_argument("--workspace-id", required=True, help="Stable, unique name for this RKS workspace.")
    parser.add_argument("--rks-data-dir", type=Path, required=True)
    parser.add_argument("--apw-db", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True, help="Persistent directory for verified PDF copies.")
    parser.add_argument("--viewer-url", default="http://127.0.0.1:8790")
    parser.add_argument(
        "--rks-python", type=Path, help="Python environment with RKS installed (otherwise uses rks on PATH)."
    )
    parser.add_argument(
        "--apw-python", type=Path, help="Python environment with APW installed (otherwise uses apw-dev on PATH)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        payload = open_reading(args)
    except (WorkflowError, OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": "reading_handoff_failed", "message": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
