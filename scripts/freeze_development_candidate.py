"""Retain exact working-tree bytes without changing Git indexes or branch history.

The destination must be new. Tracked and nonignored files are copied, excluding
per-user agent settings and the candidate's own evolving evaluation reports.
Verification compares the retained inventory with both copied files and archives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPOSITORIES = ("structured-intelligence", "agent-pdf-workbench", "research-knowledge-substrate")
EXCLUDED = (".claude/", ".codex/", ".agents/", "evaluations/development-candidate-2026-10-29/")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def inventory(root):
    paths = git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard").decode().split("\0")
    return {p: (root / p).read_bytes() for p in sorted(set(paths))
            if p and not p.startswith(EXCLUDED) and (root / p).is_file()}


def freeze(workspace, destination, candidate):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": "scientific-tooling.development-candidate.v1", "candidate": candidate,
                "frozen_at": datetime.now(timezone.utc).isoformat(), "excluded_prefixes": EXCLUDED,
                "status": "frozen-local-unreleased", "repositories": {}}
    for name in REPOSITORIES:
        root = workspace / name
        before_head = git(root, "rev-parse", "HEAD").decode().strip()
        before_status = git(root, "status", "--porcelain=v1", "-uall").decode()
        content = inventory(root)
        records = {p: {"sha256": sha(data), "size_bytes": len(data)} for p, data in content.items()}
        archive = destination / f"{name}.zip"
        with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as zipped:
            for path, data in content.items():
                copied = destination / "source" / name / path
                copied.parent.mkdir(parents=True, exist_ok=True)
                copied.write_bytes(data)
                info = zipfile.ZipInfo(path, date_time=(2026, 10, 29, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                zipped.writestr(info, data)
        if content != inventory(root) or before_head != git(root, "rev-parse", "HEAD").decode().strip():
            raise RuntimeError(f"{name} changed while freezing; incomplete destination retained for inspection")
        manifest["repositories"][name] = {
            "head": before_head, "status_porcelain": before_status,
            "archive": archive.name, "archive_sha256": sha(archive.read_bytes()),
            "tree_sha256": sha(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()),
            "files": records,
        }
    target = destination / "manifest.json"
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    verify(destination)
    return target


def verify(destination):
    manifest = json.loads((destination / "manifest.json").read_text(encoding="utf-8"))
    for name, repository in manifest["repositories"].items():
        archive = destination / repository["archive"]
        assert sha(archive.read_bytes()) == repository["archive_sha256"], archive
        with zipfile.ZipFile(archive) as zipped:
            assert set(zipped.namelist()) == set(repository["files"]), name
            for path, record in repository["files"].items():
                data = (destination / "source" / name / path).read_bytes()
                assert len(data) == record["size_bytes"] and sha(data) == record["sha256"], path
                assert zipped.read(path) == data, path
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--candidate", default="2026-10-29-c1")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.verify:
        result = verify(args.destination)
        print(json.dumps({"candidate": result["candidate"], "verified": True}))
    else:
        if not args.workspace:
            parser.error("--workspace is required when freezing")
        print(freeze(args.workspace, args.destination, args.candidate))
