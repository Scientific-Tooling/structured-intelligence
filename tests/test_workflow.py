"""Real installed RKS/APW integration, recovery, and process ownership checks."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sysconfig
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit

from scientific_tooling import reading, server
from scientific_tooling.cli import install_skill
from scientific_tooling.reading import WorkflowError
from scientific_tooling.state import lock
from scientific_tooling.workspace import Workspace


def pdf_bytes() -> bytes:
    text = b"BT /F1 12 Tf 72 720 Td (Reading workflow test source.) Tj ET"
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


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.pdf = self.root / "paper α with spaces.pdf"
        self.pdf.write_bytes(pdf_bytes())
        self.workspace = Workspace(self.root / "review α with spaces")
        self.workspace.create(self.pdf, "What does this source record?")
        self.addCleanup(lambda: server.stop(self.workspace))

    def cli(self, *args, code=0):
        executable = Path(sysconfig.get_path("scripts")) / ("sci.exe" if os.name == "nt" else "sci")
        result = subprocess.run([str(executable), *args,
                                 "--workspace", str(self.workspace.root), "--json"],
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, code, result.stderr + result.stdout)
        return json.loads(result.stdout if code == 0 else result.stderr)

    def annotation(self):
        return self.cli("annotate", "--page", "1", "--quote", "Reading workflow test source.",
                        "--comment", "An unreviewed test interpretation.")["id"]

    def test_complete_installed_cli_journey_and_resume(self):
        first = self.cli("resume", "--no-open")
        annotation = self.annotation()
        preview = self.cli("preview", "--annotation", annotation)["preview"]
        result = self.cli("apply", preview["id"])
        self.assertTrue(result["applied"])
        self.assertEqual(result["result"]["counts"]["added"], 1)
        brief = self.cli("brief")["brief"]
        self.assertEqual(brief["counts"]["linked_passages"], 1)
        self.assertEqual(brief["counts"]["unreviewed"], 1)
        replay = self.cli("apply", preview["id"])
        self.assertEqual(replay["result"]["counts"]["unchanged"], 1)
        self.assertTrue(self.cli("stop")["stopped"])
        self.assertFalse(self.cli("status")["running"])
        second = self.cli("resume", "--no-open")
        self.assertEqual(first["session_id"], second["session_id"])
        self.assertEqual(first["viewer_url"], second["viewer_url"])
        citation = urlsplit(second["brief"]["passage_urls"][0])
        resolved = server.request(citation.port, "/api/passage?" + citation.query)
        self.assertEqual(resolved["annotation"]["quote"], "Reading workflow test source.")
        Path(second["brief"]["path"]).unlink()
        # Artifact errors must not make the owned server unmanageable.
        self.assertTrue(self.cli("stop")["stopped"])
        self.assertFalse((self.workspace.root / "server.json").exists())

    def test_lost_ingestion_and_session_responses_resume_without_duplicates(self):
        original = self.workspace.rks
        def lose_ingest(*args, **kwargs):
            result = original(*args, **kwargs)
            if args[:2] == ("ingest", "pdf"):
                raise WorkflowError("simulated lost ingestion response")
            return result
        with patch.object(self.workspace, "rks", side_effect=lose_ingest):
            with self.assertRaisesRegex(WorkflowError, "lost ingestion"):
                self.workspace.prepare()
        opening = reading.open_reading
        def lose_session(args):
            opening(args)
            raise WorkflowError("simulated lost session response")
        with patch.object(reading, "open_reading", side_effect=lose_session):
            with self.assertRaisesRegex(WorkflowError, "lost session"):
                self.workspace.prepare()
        self.workspace.prepare()
        self.assertEqual(self.workspace.rks("papers", "list")["total_count"], 1)
        self.assertEqual(len(self.workspace.apw("list-sessions")["sessions"]), 1)

    def test_lost_apply_response_replays_one_import(self):
        annotation = self.annotation()
        preview = self.workspace.preview([annotation], [])
        original = self.workspace.rks
        def lose_apply(*args, **kwargs):
            result = original(*args, **kwargs)
            if "--apply" in args:
                raise WorkflowError("simulated lost apply response")
            return result
        with patch.object(self.workspace, "rks", side_effect=lose_apply):
            with self.assertRaisesRegex(WorkflowError, "lost apply"):
                self.workspace.apply(preview["id"])
        result = self.workspace.apply(preview["id"])
        self.assertEqual(result["result"]["counts"]["unchanged"], 1)
        evidence = self.workspace.rks("note", "evidence", self.workspace.load()["paper_id"])
        self.assertEqual(len(evidence["evidence"]), 1)

    def test_changed_annotation_requires_new_preview_and_explicit_update(self):
        annotation = self.annotation()
        old = self.workspace.preview([annotation], [])
        self.workspace.apply(old["id"])
        state = server.running(self.workspace)
        saved = state["annotations"][0]["annotation"]
        saved["comment"] = "Edited interpretation."
        server.request(self.workspace.load()["port"], "/api/annotations",
                       {"session_id": state["session_id"], "annotation": saved})
        with self.assertRaisesRegex(WorkflowError, "changed after preview"):
            self.workspace.apply(old["id"])
        fresh = self.workspace.preview([annotation], [])
        self.assertEqual(fresh["counts"]["conflict"], 1)
        self.assertFalse(self.workspace.apply(fresh["id"])["applied"])
        result = self.workspace.apply(fresh["id"], accept_updates=True)
        self.assertEqual(result["result"]["counts"]["updated"], 1)

    def test_source_corruption_and_wrong_workspace_are_preserved(self):
        self.workspace.prepare()
        snapshot = Path(self.workspace.summary()["source_pdf"])
        snapshot.write_bytes(b"changed source")
        with self.assertRaisesRegex(WorkflowError, "Cached PDF has changed"):
            self.workspace.prepare()
        self.assertEqual(snapshot.read_bytes(), b"changed source")
        with self.assertRaisesRegex(WorkflowError, "different PDF or question"):
            self.workspace.create(self.pdf, "another question")

    def test_workspace_lock_is_process_owned(self):
        with lock(self.workspace.root / "workspace.lock"):
            result = self.cli("resume", "--no-open", code=1)
        self.assertIn("workspace is busy", result["message"])
        self.workspace.prepare()  # Lock is released, no stale lock-file cleanup.

    def test_occupied_saved_port_preserves_other_listener(self):
        self.workspace.prepare()
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            self.workspace.set_port(listener.getsockname()[1])
            with self.assertRaisesRegex(WorkflowError, "Cannot bind the saved reader port"):
                server.ensure_running(self.workspace)
            self.assertGreater(listener.fileno(), -1)
        self.assertFalse((self.workspace.root / "server.json").exists())

    def test_skill_is_packaged_and_does_not_overwrite_an_existing_skill(self):
        result = install_skill(self.root / "skills")
        skill = Path(result["installed"])
        self.assertIn("name: paper-to-brief", (skill / "SKILL.md").read_text())
        with self.assertRaisesRegex(WorkflowError, "already exists"):
            install_skill(self.root / "skills")


if __name__ == "__main__":
    unittest.main()
