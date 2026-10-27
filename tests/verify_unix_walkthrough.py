"""Execute the documented Bash/zsh blocks in fresh public source checkouts.

Only the demo folder and the manual reading action are supplied by this test.
The annotation is an explicitly unreviewed engineering fixture written through
APW's public HTTP API. This checks CLI/HTTP workflow behavior, not browser UI.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pdf_bytes() -> bytes:
    text = b"BT /F1 12 Tf 72 720 Td (Reading handoff test source.) Tj ET"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               b"<< /Length " + str(len(text)).encode() + b" >>\nstream\n" + text + b"\nendstream"]
    result, offsets = bytearray(b"%PDF-1.4\n"), [0]
    for number, value in enumerate(objects, 1):
        offsets.append(len(result))
        result.extend(f"{number} 0 obj\n".encode() + value + b"\nendobj\n")
    xref = len(result)
    result.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        result.extend(f"{offset:010} 00000 n \n".encode())
    result.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(result)


def objects_in(text: str) -> list[dict]:
    decoder, output, position = json.JSONDecoder(), [], 0
    while (position := text.find("{", position)) != -1:
        try:
            value, length = decoder.raw_decode(text[position:])
            output.append(value)
            position += length
        except ValueError:
            position += 1
    return output


def request_json(url: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def stop(process: subprocess.Popen | None) -> None:
    if process is not None and process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=15)


def verify(shell: str) -> Path:
    if os.name != "posix":
        raise RuntimeError("Run this full workflow test on Linux or macOS")
    with socket.socket() as check:
        if check.connect_ex(("127.0.0.1", 8790)) == 0:
            raise RuntimeError("Port 8790 is occupied; preserve the existing viewer")
    artifact_root = ROOT / ".workflow-test" / "manual"
    artifact_root.mkdir(parents=True, exist_ok=True)
    artifacts = Path(tempfile.mkdtemp(prefix=f"unix-{shell}-", dir=artifact_root))
    work = artifacts / "Linux macOS α demo"
    fixture = artifacts / "input paper α.pdf"
    fixture.write_bytes(pdf_bytes())
    source = ROOT / "workflows/research/manual-operations/unix.md"
    blocks = re.findall(r"```bash\n(.*?)\n```", source.read_text(encoding="utf-8"), re.DOTALL)
    if len(blocks) != 7:
        raise RuntimeError("Review the documented stage boundaries before updating this test")
    work_line = 'work="$HOME/scientific-tooling-demo"'

    def test_location(block: str) -> str:
        if block.count(work_line) != 1:
            raise RuntimeError("Expected one documented working-folder assignment")
        return block.replace(work_line, "work=" + shlex.quote(str(work)))

    ready = artifacts / "reader-ready"
    barrier = f"while [ ! -f {shlex.quote(str(ready))} ]; do sleep 0.1; done"
    script = artifacts / "terminal-a.sh"
    script.write_text("\n".join([test_location(blocks[0]), blocks[1], barrier, *blocks[3:]]),
                      encoding="utf-8", newline="\n")
    inputs = artifacts / "inputs.txt"
    inputs.write_text(f"{fixture}\nWhat is recorded in the engineering fixture?\nann_unix_walkthrough\n", encoding="utf-8")
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "PYTHONIOENCODING": "utf-8"}
    main = server = None
    print(f"Verifying {shell}; artifacts: {artifacts}", flush=True)
    with inputs.open("rb") as stdin, (artifacts / "terminal-a.log").open("wb") as log, (artifacts / "terminal-b.log").open("wb") as server_log:
        try:
            main = subprocess.Popen([shell, str(script)], stdin=stdin, stdout=log, stderr=log,
                                    env=environment, start_new_session=True)
            handoff_file = work / "review/reading-handoff.json"
            deadline = time.monotonic() + 300
            while True:
                if main.poll() is not None:
                    raise RuntimeError("Terminal A exited before the handoff; inspect terminal-a.log")
                try:
                    handoff = json.loads(handoff_file.read_text(encoding="utf-8"))
                    break
                except (OSError, ValueError):
                    if time.monotonic() > deadline:
                        raise RuntimeError("Timed out waiting for installation/handoff")
                    time.sleep(0.2)
            # Own the viewer directly rather than an extra shell process during signal checks.
            server_command = test_location(blocks[2]).replace('"$work/.venv/bin/apw-viewer-server"', 'exec "$work/.venv/bin/apw-viewer-server"', 1)
            server = subprocess.Popen([shell, "-c", server_command], stdout=server_log,
                                      stderr=server_log, env=environment, start_new_session=True)
            api = "http://127.0.0.1:8790"
            deadline = time.monotonic() + 30
            while True:
                try:
                    with urllib.request.urlopen(api, timeout=1):
                        break
                except OSError:
                    if server.poll() is not None or time.monotonic() > deadline:
                        with socket.socket() as direct:
                            direct.settimeout(1)
                            connection_error = direct.connect_ex(("127.0.0.1", 8790))
                        details = {
                            "viewer_exit": server.poll(), "direct_loopback_result": connection_error,
                            "proxy_types": sorted(urllib.request.getproxies()),
                            "loopback_proxy_bypass": urllib.request.proxy_bypass("127.0.0.1"),
                            "viewer_log": (artifacts / "terminal-b.log").read_text(encoding="utf-8", errors="replace")[-1500:],
                        }
                        if sys.platform == "darwin":
                            details["process"] = subprocess.run(
                                ["ps", "-p", str(server.pid), "-o", "pid=,ppid=,state=,etime=,command="],
                                capture_output=True, text=True, timeout=5, check=False).stdout[-1000:]
                            subprocess.run(["sample", str(server.pid), "1", "1", "-file", str(artifacts / "server-sample.txt")],
                                           capture_output=True, timeout=10, check=False)
                        raise RuntimeError("Viewer startup diagnostics: " + json.dumps(details))
                    time.sleep(0.2)
            quote = "Reading handoff test source."
            stamp = datetime.now(timezone.utc).isoformat()
            request_json(api + "/api/annotations", {"session_id": handoff["apw"]["session_id"], "annotation": {
                "id": "ann_unix_walkthrough", "page": 1, "type": "highlight", "quote": quote,
                "anchor": {"quote": quote, "start": 0, "end": len(quote), "prefix": "", "suffix": ""},
                "rects": [], "tags": [], "comment": "Unreviewed engineering fixture.",
                "createdAt": stamp, "updatedAt": stamp,
            }})
            ready.touch()
            if main.wait(timeout=120) != 0:
                raise RuntimeError("A documented command failed; inspect terminal-a.log")
            output = (artifacts / "terminal-a.log").read_text(encoding="utf-8", errors="replace")
            applied = [value for value in objects_in(output) if value.get("applied") is True]
            if len(applied) != 2 or applied[0]["counts"]["added"] != 1 or applied[1]["counts"]["added"] != 0 or applied[1]["counts"]["unchanged"] != 1:
                raise RuntimeError("First import/replay counters did not match the guide")
            brief = (work / "review/reading-brief.md").read_text(encoding="utf-8")
            citation = re.search(r"\[Open the supporting passage\]\(([^)]+)\)", brief)
            if citation is None:
                raise RuntimeError("The generated brief has no passage link")
            parsed = urllib.parse.urlsplit(citation.group(1))
            if parsed.netloc != "127.0.0.1:8790":
                raise RuntimeError("The citation points outside the test viewer")
            resolved = request_json(api + "/api/passage?" + parsed.query)
            if resolved["annotation"]["id"] != "ann_unix_walkthrough" or resolved["annotation"]["quote"] != quote:
                raise RuntimeError("Citation did not resolve to the selected passage")
            version = subprocess.check_output([str(work / ".venv/bin/python"), "-c", "import platform; print(platform.python_version())"],
                                              text=True, encoding="utf-8").strip()
            if not (3, 10) <= tuple(map(int, version.split(".")[:2])) <= (3, 12):
                raise RuntimeError("The walkthrough requires a Python 3.10-3.12 interpreter")
            receipt = {"passed": True, "platform": sys.platform, "shell": shell,
                       "python_version": version,
                       "source_commits": {repo: subprocess.check_output(["git", "-C", str(work / repo), "rev-parse", "HEAD"],
                                                                         text=True, encoding="utf-8").strip()
                                          for repo in ("research-knowledge-substrate", "agent-pdf-workbench", "structured-intelligence")},
                       "annotation_setup": "unreviewed fixture through APW HTTP API; browser UI not exercised by this test",
                       "source_install": "fresh public HTTPS clones and python3 -m venv",
                       "path_cases": "spaces and Unicode", "first_import": applied[0]["counts"],
                       "replay": applied[1]["counts"], "citation_resolved": True}
        finally:
            stop(main)
            stop(server)
            if main is not None and main.returncode not in (0, None):
                tail = (artifacts / "terminal-a.log").read_bytes()[-3500:].decode("utf-8", errors="replace")
                print(tail, file=sys.stderr)
                if os.environ.get("GITHUB_ACTIONS") == "true":
                    escaped = tail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
                    print(f"::error title=Unix walkthrough traceback::{escaped}")
    (artifacts / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2), flush=True)
    return artifacts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell", choices=("bash", "zsh"), default="bash")
    arguments = parser.parse_args()
    try:
        verify(arguments.shell)
    except Exception:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            detail = traceback.format_exc().encode("utf-8")[-3500:].decode("utf-8", errors="replace")
            escaped = detail.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            print(f"::error title=Unix walkthrough failure::{escaped}")
        raise
