"""Verify the ordinary dependency install separately from frozen c3 evidence."""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPORT = Path(__file__).resolve().parent
REPO = REPORT.parents[1]
ROOT = REPO.parent
PUBLICATION = ROOT / ".publication/2026-11-02"
CANDIDATE = ROOT / ".development-candidate/2026-11-02-c3"
APW = "d800a7779f1893be1a4aa0a93804c7e630d6be1a"
RKS = "44a8f33f47d9e867a03a8cff9e07a7b021e04cea"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    checks = REPORT / "checks"
    checks.mkdir(exist_ok=False)
    manifest = json.loads((CANDIDATE / "manifest.json").read_text(encoding="utf-8"))
    packages = {}
    for repo, module, package, commit in [
        ("structured-intelligence", "scientific_tooling", "scientific-tooling", None),
        ("agent-pdf-workbench", "agent_pdf_workbench", "agent-pdf-workbench", APW),
        ("research-knowledge-substrate", "rks", "research-knowledge-substrate", RKS),
    ]:
        installed = Path(importlib.import_module(module).__file__).parent
        assert installed.is_relative_to(PUBLICATION / "installed"), installed
        dist = metadata.distribution(package)
        origin = json.loads(dist.read_text("direct_url.json"))
        if commit:
            assert origin["vcs_info"]["commit_id"] == commit, origin
        else:
            assert any(APW in requirement for requirement in dist.requires), dist.requires
        files = {}
        prefix = f"src/{module}/"
        for relative, expected in manifest["repositories"][repo]["files"].items():
            if not relative.startswith(prefix):
                continue
            target = installed / relative.removeprefix(prefix)
            actual = target.read_bytes()
            source = (CANDIDATE / "source" / repo / relative).read_bytes()
            assert sha(source) == expected["sha256"]
            exact = actual == source
            assert exact or actual.replace(b"\r\n", b"\n") == source.replace(b"\r\n", b"\n"), target
            files[relative.removeprefix(prefix)] = {"installed_sha256": sha(actual),
                "candidate_sha256": sha(source), "match": "exact" if exact else "line_endings_only"}
        packages[package] = {"version": dist.version, "module": str(installed), "direct_url": origin, "files": files}
    save(checks / "installation.json", {"python": sys.version, "executable": sys.executable,
        "candidate_manifest_sha256": sha((CANDIDATE / "manifest.json").read_bytes()),
        "ordinary_public_dependencies": True, "packages": packages})
    env = {**os.environ, "RKS_TEST_PYTHON": sys.executable, "APW_TEST_PYTHON": sys.executable}
    env.pop("PYTHONPATH", None)
    results = []
    for name, pattern in [("installed-workflow", "test_workflow.py"), ("native-boundaries", "test_*integration.py")]:
        command = [sys.executable, "scripts/run_research_tests.py", "discover", "-s", "tests", "-p", pattern, "-v"]
        started = time.perf_counter()
        result = subprocess.run(command, cwd=REPO, env=env, capture_output=True, timeout=600)
        output = result.stdout + result.stderr
        (checks / f"{name}.log").write_bytes(output)
        count = re.search(rb"Ran (\d+) tests?", output)
        row = {"name": name, "command": command, "exit_code": result.returncode,
            "seconds": time.perf_counter() - started, "tests": int(count[1]) if count else None,
            "log_sha256": sha(output)}
        results.append(row)
        print(json.dumps(row), flush=True)
    save(checks / "results.json", results)
    save(REPORT / "summary.json", {"apw_commit": APW, "rks_commit": RKS,
        "passed": all(r["exit_code"] == 0 for r in results), "tests": sum(r["tests"] or 0 for r in results),
        "candidate": "2026-11-02-c3", "ordinary_public_dependencies": True})
    for name in ("install.log", "venv.log"):
        (REPORT / name).write_bytes((PUBLICATION / name).read_bytes())
    assert all(r["exit_code"] == 0 for r in results), results


if __name__ == "__main__":
    main()
