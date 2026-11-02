"""Seal acceptance receipts and verify both tracked evidence and local artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / ".development-candidate"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def retain():
    receipts = HERE / "receipts"
    receipts.mkdir(exist_ok=False)
    c2, c3 = BASE / "2026-11-02-c2", BASE / "2026-11-02-c3"
    original, corrected = read(c2 / "manifest.json"), read(c3 / "manifest.json")
    assert original["repositories"]["research-knowledge-substrate"]["tree_sha256"] == corrected["repositories"]["research-knowledge-substrate"]["tree_sha256"]
    for repo, package in [("structured-intelligence", "scientific_tooling"), ("research-knowledge-substrate", "rks")]:
        prefix = f"src/{package}/"
        before = {p: r for p, r in original["repositories"][repo]["files"].items() if p.startswith(prefix)}
        after = {p: r for p, r in corrected["repositories"][repo]["files"].items() if p.startswith(prefix)}
        assert before == after, f"Application changed: {repo}"
    checks = {}
    for run in ("recovery-01", "reader-01", "citation-browser-01", "edges-02"):
        result = read(c3 / run / "receipt.json")
        assert result["passed"] and not result["errors"], run
        checks[run] = result
    assert not read(c2 / "edges-01/receipt.json")["passed"]
    benchmark = read(c2 / "benchmark-02/result.json")
    assert benchmark["passed"] and benchmark["queries"] == 100 and benchmark["records"] == 10000
    timings = read(c2 / "benchmark-02/timings.json")
    assert len([r for r in timings if r["stage"] == "warm"]) == 100

    # Raw logs, candidate inventories, provenance, all timings and failed attempts
    # stay byte-identical. Large fixture databases, PDFs and images remain local.
    local = {}
    for candidate in (c2, c3):
        for item in candidate.iterdir():
            if item.name in {"source", "installed", "wheels", "provenance-c1-check"}:
                continue
            if item.is_file():
                paths = [item]
            else:
                paths = [p for p in item.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
            for file in paths:
                if file.name.endswith(("-shm", "-wal")):
                    continue
                relative = file.relative_to(BASE).as_posix()
                local[relative] = {"sha256": sha(file), "size_bytes": file.stat().st_size}
                # Copy bounded reports, not full paper content or 10,000-record bundles.
                if (len(file.relative_to(candidate).parts) <= 2 and file.suffix in {".json", ".log", ".txt"}
                        and not file.name.startswith(("bundle-", "import-")) and file.name != "citations.json"):
                    target = receipts / file.relative_to(BASE)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(file.read_bytes())
                if file.name in {"acceptance.py", "browser.mjs"}:
                    target = HERE / "harnesses" / (sha(file) + file.suffix)
                    if not target.exists():
                        target.write_bytes(file.read_bytes())
        for wheel in (candidate / "wheels").glob("*.whl"):
            local[wheel.relative_to(BASE).as_posix()] = {"sha256": sha(wheel), "size_bytes": wheel.stat().st_size}

    rasters = checks["reader-01"]["raster_samples"]
    summary = {"candidate": corrected["candidate"], "parent": original["candidate"],
        "candidate_manifest_sha256": sha(c3 / "manifest.json"),
        "browser_checks_passed": sum(len(r["checks"]) for r in checks.values()),
        "page_errors": [], "real_citation_targets": 10, "real_citation_visits_including_restart": 20,
        "reader": {"page_visits": len(rasters), "max_active_rasters": max(s["active"] for s in rasters),
            "max_canvas_pixel_bytes": max(s["pixel_bytes"] for s in rasters), "limit": 7,
            "heap": "Chromium performance.memory is coarse here and is not used as a total-memory acceptance claim"},
        "search": {**benchmark, "inherited_from": "2026-11-02-c2/benchmark-02", "rks_tree_unchanged": True},
        "gates": {gate: "PASS local engineering acceptance" for gate in ("M03", "P01", "R01", "R02", "S03")},
        "limits": ["Windows 11 / Python 3.14.10 / Chromium 151.0.7922.34",
            "Source and scientific interpretation review remain independent and pending",
            "c3 local wheels include an unpublished APW fix; public sci still pins the prior APW commit",
            "No new cross-platform release qualification or public dependency installation is implied"]}
    write(HERE / "results.json", summary)
    write(HERE / "local-artifacts.json", {"base": str(BASE), "files": local})
    files = [p for folder in (receipts, HERE / "harnesses") for p in folder.rglob("*") if p.is_file()]
    files += [HERE / name for name in ("results.json", "local-artifacts.json", "protocol.json", "protocol-c3.json",
        "acceptance.py", "browser.mjs", "retain_results.py")]
    write(HERE / "receipts.json", {"files": {p.relative_to(HERE).as_posix(): sha(p) for p in sorted(files)}})
    verify(False)
    print(json.dumps(summary, indent=2))


def verify(include_local):
    for relative, expected in read(HERE / "receipts.json")["files"].items():
        assert sha(HERE / relative) == expected, relative
    if include_local:
        inventory = read(HERE / "local-artifacts.json")
        for relative, record in inventory["files"].items():
            file = Path(inventory["base"]) / relative
            assert sha(file) == record["sha256"], relative
    print("Retained receipt hashes verified" + (" including local artifacts" if include_local else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--include-local", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify(args.include_local)
    else:
        retain()
