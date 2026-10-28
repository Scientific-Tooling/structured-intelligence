"""Drive the installed reader against bounded recorded provider fixtures, without external network calls."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from pathlib import Path
from unittest.mock import patch

from agent_pdf_workbench.service import AgentPdfWorkbenchService
from agent_pdf_workbench.viewer_server import create_viewer_server
from scientific_tooling import discovery_sources
from scientific_tooling.server import HostedWorkflow
from scientific_tooling.workspace import Workspace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from test_discovery import FakeClient, crossref
from test_workflow import pdf_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apw", type=Path, required=True)
    parser.add_argument("--node", default="node")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    pdf = args.output / "seed.pdf"
    pdf.write_bytes(pdf_bytes("Existing reading project."))
    workspace = Workspace(args.output / "review")
    workspace.create(pdf, "Which experimental conditions differ?")
    workspace.prepare()
    service = AgentPdfWorkbenchService(workspace.root / "events.db")
    host = HostedWorkflow(workspace, service, "fixture", "fixture-token")
    http = create_viewer_server(workspace.root / "events.db", workspace.root / "pdfs", workflow=host)
    host.server = http
    workspace.set_port(http.server_port)
    client = FakeClient(records=[crossref(), crossref("10.1234/no-full-text", "Reference without full text", links=False)])
    thread = threading.Thread(target=http.serve_forever)
    with patch.object(discovery_sources, "Client", return_value=client):
        thread.start()
        try:
            subprocess.run([args.node, str(ROOT / "scripts/verify_discovery_browser.mjs"), workspace.summary()["viewer_url"],
                            str(args.apw.resolve()), str(args.output.resolve())], check=True)
            data = workspace.load()
            assert len(data["papers"]) == 2, data
            assert len(data["works"]) == 2, data
            assert workspace.rks("papers", "list")["total_count"] == 2
            assert len([c for c in client.calls if c[1]]) == 1, client.calls
            (args.output / "receipt.json").write_text(json.dumps({"passed": True, "provider_data": "frozen fixtures",
                "reader_http": "real", "explicit_selection": True, "lost_response_replay": True,
                "missing_full_text": True, "source_navigation": True, "desktop_mobile": True,
                "papers": len(data["papers"]), "works": len(data["works"])}, indent=2))
        finally:
            http.shutdown()
            thread.join(timeout=5)
            http.server_close()


if __name__ == "__main__":
    main()
