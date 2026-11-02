"""Reproducible installed-package acceptance; never replaces earlier run directories."""
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata as metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from contextlib import closing

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = Path(os.environ.get("ACCEPTANCE_CANDIDATE", ROOT / ".development-candidate/2026-11-02-c2")).resolve()
PROTOCOL = HERE / ("protocol-c3.json" if CANDIDATE.name == "2026-11-02-c3" else "protocol.json")
TIME = "2026-11-02T12:00:00+00:00"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def provenance():
    manifest = json.loads((CANDIDATE / "manifest.json").read_text())
    packages = {}
    for repo, module, distribution in [
        ("structured-intelligence", "scientific_tooling", "scientific-tooling"),
        ("agent-pdf-workbench", "agent_pdf_workbench", "agent-pdf-workbench"),
        ("research-knowledge-substrate", "rks", "research-knowledge-substrate"),
    ]:
        installed = Path(importlib.import_module(module).__file__).parent
        assert installed.is_relative_to(Path(sys.prefix)), installed
        prefix = f"src/{module}/"
        matched = {}
        for relative, record in manifest["repositories"][repo]["files"].items():
            if relative.startswith(prefix):
                path = installed / relative.removeprefix(prefix)
                assert path.is_file() and sha(path) == record["sha256"], path
                matched[relative.removeprefix(prefix)] = record["sha256"]
        assert matched
        packages[distribution] = {"version": metadata.version(distribution), "module": str(installed),
            "direct_url": json.loads(metadata.distribution(distribution).read_text("direct_url.json") or "null"),
            "verified_files": matched}
    return {"candidate": manifest["candidate"], "manifest_sha256": sha(CANDIDATE / "manifest.json"),
        "protocol_sha256": sha(PROTOCOL), "harness_sha256": sha(__file__),
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "processor": platform.processor(), "logical_cpus": os.cpu_count(), "packages": packages,
        "qualification_scope": "Installed application files match this frozen source. See direct_url provenance for each distribution; local coordinated-wheel checks do not qualify an ordinary public-dependency install.",
        "candidate_wheels": {p.name: sha(p) for p in (CANDIDATE / "wheels").glob("*.whl")}}


def cli(workspace, *args):
    command = [sys.executable, "-m", "scientific_tooling", *map(str, args), "--workspace", str(workspace), "--json"]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return json.loads(result.stdout)


def citations(output):
    """Recreate original quotations via public commands; the pilot is read-only input."""
    original = ROOT / ".living-project-pilot/receipts"
    baseline = json.loads((original / "resume.json").read_text(encoding="utf-8"))
    workspace = output / "project"
    sources = baseline["papers"]
    opened = cli(workspace, "start", sources[0]["source_pdf"], "--question", baseline["question"], "--no-open")
    rows = []
    try:
        for paper in sources:
            assert sha(paper["source_pdf"]) == paper["document_sha256"]
            if paper["key"] != "p1":
                cli(workspace, "add", paper["source_pdf"])
            cli(workspace, "resume", "--paper", paper["key"], "--no-open")
            selected = []
            for receipt in sorted(original.glob("annotate-*.json")):
                record = json.loads(receipt.read_text(encoding="utf-8"))
                if record["session_id"] != paper["session_id"]:
                    continue
                annotation = record["annotation"]
                created = cli(workspace, "annotate", "--paper", paper["key"], "--page", annotation["page"],
                    "--quote", annotation["quote"], "--comment", annotation["comment"])
                selected += ["--annotation", created["annotation"]["id"]]
                rows.append({"case_id": receipt.stem, "original_receipt_sha256": sha(receipt),
                    "original_annotation_id": annotation["id"], "annotation_id": created["annotation"]["id"],
                    "paper": paper["key"], "page": annotation["page"], "quote": annotation["quote"],
                    "document_sha256": paper["document_sha256"]})
            preview = cli(workspace, "preview", "--paper", paper["key"], *selected)
            applied = cli(workspace, "apply", preview["preview"]["id"])
            save(output / f"import-{paper['key']}.json", applied)
        assert len(rows) == 10
        cli(workspace, "brief")
        search = cli(workspace, "search", "Agent-prepared interpretation", "--mode", "phrase", "--limit", "100")
        assert search["total"] == 10
        for row in rows:
            entry = next(e for e in search["results"] if e["record"]["item"]["id"] == row["annotation_id"])
            passage = entry["passages"][0]
            assert passage["available"], passage
            row["passage"] = passage
        status = cli(workspace, "status")
        save(output / "citations.json", {"workspace": str(workspace), "viewer_url": opened["viewer_url"],
            "cases": rows, "papers": status["papers"]})
    finally:
        cli(workspace, "stop")


def benchmark(output):
    from rks.operations.evidence_contract import digest
    from rks.operations.evidence_import import import_evidence
    from rks.operations.evidence_search import search_evidence
    from rks.storage.db import connect_db, connect_db_readonly, initialize_db
    from rks.storage.paper_repository import PaperRepository

    db = output / "rks.sqlite3"
    subjects = ["donor replication", "batch correction", "mixed model", "pseudobulk aggregation", "cell sampling",
        "variance estimation", "multiple testing", "effect size", "library normalization", "simulation design"]
    queries = [f"{subjects[i % 10]} cohort{i % 100:03d}" for i in range(100)]
    save(output / "queries.json", queries)
    scope = []
    with closing(connect_db(db)) as conn:
        initialize_db(conn)
        for p in range(10):
            pdf = output / f"paper-{p}.pdf"
            pdf.write_bytes(f"%PDF-1.4\nSynthetic benchmark identity {p}\n%%EOF".encode())
            paper = PaperRepository(conn).create_paper_from_pdf(pdf, pdf, title=f"Synthetic benchmark paper {p}")
            file_sha = sha(pdf)
            scope.append(f"{paper.id}:{file_sha}")
            bundle = {"schema": "scientific-tooling.selected-evidence.v1", "workspace_id": "benchmark", "paper_id": paper.id,
                "source": {"system": "apw", "source_id": "reader", "session_id": f"ps_{p}",
                    "paper_ref": f"rks:benchmark:{paper.id}:sha256:{file_sha}"},
                "document": {"path": str(pdf.resolve()), "sha256": file_sha, "size_bytes": pdf.stat().st_size},
                "exported_at": TIME, "items": []}
            for i in range(1000):
                number = p * 1000 + i
                ident = f"note_{number:05d}"
                item = {"kind": "note", "id": ident, "content": {"id": ident,
                    "title": f"Synthetic {subjects[number % 10]} record {number}",
                    "markdown": (f"Unreviewed synthetic latency fixture cohort{number % 100:03d}. "
                        f"This record discusses {subjects[number % 10]} under condition {number % 37}. "
                        "Biological samples, experimental units, uncertainty, assumptions, limitations and "
                        "within-sample dependence are recorded separately from method interpretations. "
                        "The synthetic effect is not a scientific result. No relevance judgment is asserted."),
                    "linkedAnnotationIds": [], "createdAt": TIME, "updatedAt": TIME}, "passages": [],
                    "review": {"status": "unreviewed"},
                    "provenance": {"session_id": f"ps_{p}", "created_at": TIME, "updated_at": TIME}}
                item["content_revision"] = digest({"source_id": "reader", "paper_ref": bundle["source"]["paper_ref"],
                    **{k: item[k] for k in ("kind", "id", "content", "passages")}})
                item["revision"] = digest(item)
                bundle["items"].append(item)
            plan = import_evidence(conn, bundle, workspace_id="benchmark")
            result = import_evidence(conn, bundle, workspace_id="benchmark", plan=plan, apply=True)
            assert result["applied"], {"counts": result["counts"], "first": result["items"][0]}
            save(output / f"bundle-{p}.json", bundle)
            print(f"Imported {(p + 1) * 1000} records", flush=True)
        assert conn.execute("SELECT COUNT(*) FROM external_evidence").fetchone()[0] == 10000
    # Setup is excluded. Fresh process makes first-query cost explicit, without a false disk-cold claim.
    save(output / "scope.json", scope)
    result = subprocess.run([sys.executable, str(HERE / "acceptance.py"), "measure", str(output)],
        capture_output=True, text=True, encoding="utf-8", timeout=1200)
    (output / "measure.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def measure(output):
    from rks.operations.evidence_search import search_evidence
    from rks.storage.db import connect_db_readonly
    db = output / "rks.sqlite3"
    before = sha(db)
    scope = json.loads((output / "scope.json").read_text())
    queries = json.loads((output / "queries.json").read_text())
    rows = []
    for stage, selected in [("first_query", queries[:1]), ("warmup", queries[:10]), ("warm", queries)]:
        for index, query in enumerate(selected):
            started = time.perf_counter()
            with closing(connect_db_readonly(db)) as conn:
                conn.execute("BEGIN")
                result = search_evidence(conn, query, workspace_id="benchmark", source_id="reader", paper_sources=scope)
            elapsed = time.perf_counter() - started
            assert result["total"] > 0 and not result["unavailable_evidence"]
            assert all(r["record"]["workspace_id"] == "benchmark" for r in result["results"])
            rows.append({"stage": stage, "index": index, "query": query, "seconds": elapsed,
                "total": result["total"], "ids": [r["note_id"] for r in result["results"]]})
            save(output / "timings.json", rows)
    times = sorted(r["seconds"] for r in rows if r["stage"] == "warm")
    p95 = times[math.ceil(.95 * len(times)) - 1]
    assert sha(db) == before, "Search modified the database"
    result = {"passed": p95 <= 2.0, "records": 10000, "queries": len(times), "p95_seconds": p95,
        "median_seconds": (times[49] + times[50]) / 2, "max_seconds": max(times),
        "first_query_seconds": rows[0]["seconds"], "db_sha256_before_and_after": before,
        "os_caches_purged": False, "measurement": "native search with connection and read transaction, excluding process startup"}
    save(output / "result.json", result)
    print(json.dumps(result), flush=True)
    assert result["passed"], "S03 p95 exceeds 2 seconds; retain failure for diagnosis"


def measure_cli(output, fixture):
    db = fixture / "rks.sqlite3"
    before = sha(db)
    scope = json.loads((fixture / "scope.json").read_text())
    queries = json.loads((fixture / "queries.json").read_text())[:5]
    rows = []
    for query in queries:
        command = [sys.executable, "-m", "rks", "note", "search-evidence", query,
            "--workspace-id", "benchmark", "--source-id", "reader"]
        for source in scope:
            command += ["--paper-source", source]
        started = time.perf_counter()
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60,
            env={**os.environ, "RKS_DATA_DIR": str(fixture)})
        elapsed = time.perf_counter() - started
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["total"] > 0 and not payload["unavailable_evidence"]
        rows.append({"query": query, "seconds_including_process_startup": elapsed, "total": payload["total"]})
    assert sha(db) == before
    save(output / "result.json", {"samples": rows, "db_sha256_before_and_after": before,
        "scope": "Five CLI timings, kept separate from the 100-query native p95 gate"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["provenance", "citations", "benchmark", "measure", "cli-measure"])
    parser.add_argument("output", type=Path)
    parser.add_argument("--fixture", type=Path)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if args.action == "measure":
        measure(args.output)
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output / "acceptance.py").write_bytes(Path(__file__).read_bytes())
        (args.output / "protocol.json").write_bytes(PROTOCOL.read_bytes())
        try:
            save(args.output / "provenance.json", provenance())
            if args.action == "citations":
                citations(args.output)
            elif args.action == "benchmark":
                benchmark(args.output)
            elif args.action == "cli-measure":
                if args.fixture is None:
                    parser.error("--fixture is required for cli-measure")
                measure_cli(args.output, args.fixture.resolve())
        except Exception:
            import traceback
            (args.output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
            raise
