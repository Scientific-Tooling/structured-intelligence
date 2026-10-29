"""Run installed candidate checks with immutable per-command receipts and logs."""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
CANDIDATE = ROOT.parent / ".development-candidate/2026-10-29-c1"
SOURCES = CANDIDATE / "source"
SCI = SOURCES / "structured-intelligence"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    logs = CANDIDATE / "checks"
    logs.mkdir(exist_ok=False)
    modules = {}
    for package, module in (("scientific-tooling", "scientific_tooling"),
                            ("agent-pdf-workbench", "agent_pdf_workbench"),
                            ("research-knowledge-substrate", "rks")):
        imported = importlib.import_module(module)
        path = Path(imported.__file__).resolve()
        assert path.is_relative_to(CANDIDATE / "installed"), path
        modules[package] = {"version": metadata.version(package), "path": str(path),
                            "direct_url": metadata.distribution(package).read_text("direct_url.json")}
    installed_skill = files("scientific_tooling.analysis_skill").joinpath("SKILL.md").read_bytes()
    source_skill = (SCI / "skills/scrnaseq-differential-expression/SKILL.md").read_bytes()
    assert installed_skill == source_skill
    installed_web = files("agent_pdf_workbench").joinpath("web/app.js").read_bytes()
    assert installed_web == (SOURCES / "agent-pdf-workbench/src/agent_pdf_workbench/web/app.js").read_bytes()
    identity = {"candidate": "2026-10-29-c1", "time": datetime.now(timezone.utc).isoformat(),
                "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                "processor": platform.processor(), "cpu_count": os.cpu_count(), "modules": modules,
                "manifest_sha256": digest(CANDIDATE / "manifest.json"),
                "protocol_sha256": digest(REPORT / "protocol.json"),
                "analysis_skill_sha256": hashlib.sha256(installed_skill).hexdigest(),
                "reader_app_sha256": hashlib.sha256(installed_web).hexdigest(),
                "wheels": {p.name: digest(p) for p in (CANDIDATE / "wheels").glob("*.whl")},
                "public_dependency_install": False}
    write(logs / "installation.json", identity)
    commands = [(name, [sys.executable, "scripts/run_research_tests.py", "discover", "-s", "tests", "-p", pattern, "-v"], SCI)
                for name, pattern in (("workflow", "test_workflow.py"), ("discovery", "test_discovery.py"),
                                      ("state", "test_state.py"), ("maintenance", "test_maintenance.py"),
                                      ("analysis", "test_analysis.py"), ("adapters", "test_research_*.py"),
                                      ("boundary", "test_*integration.py"))]
    environment = {**os.environ, "RKS_TEST_PYTHON": sys.executable, "APW_TEST_PYTHON": sys.executable}
    environment.pop("PYTHONPATH", None)
    results = []
    for name, command, cwd in commands:
        started = time.monotonic()
        with (logs / f"{name}.log").open("xb") as output:
            try:
                result = subprocess.run(command, cwd=cwd, env=environment, stdout=output,
                                        stderr=subprocess.STDOUT, timeout=900)
                code = result.returncode
            except subprocess.TimeoutExpired:
                code = "timeout"
        receipt = {"name": name, "command": command, "cwd": str(cwd), "exit_code": code,
                   "seconds": time.monotonic() - started, "log_sha256": digest(logs / f"{name}.log"),
                   "candidate_manifest_sha256": identity["manifest_sha256"]}
        write(logs / f"{name}.json", receipt)
        results.append(receipt)
        print(json.dumps({"name": name, "exit_code": code, "seconds": round(receipt["seconds"], 2)}), flush=True)
    write(logs / "results.json", results)
    return int(any(result["exit_code"] != 0 for result in results))


if __name__ == "__main__":
    raise SystemExit(main())
