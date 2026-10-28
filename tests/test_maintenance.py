"""Living-project provenance, freshness and crash recovery with installed RKS/APW."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_pdf_workbench.service import AgentPdfWorkbenchService
from scientific_tooling import discovery, maintenance, server
from scientific_tooling.reading import WorkflowError
from scientific_tooling.state import read_json, write_json
from scientific_tooling.workspace import Workspace
from test_discovery import FakeClient, crossref
from test_workflow import pdf_bytes


class MaintenanceTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        pdf = self.root / "original.pdf"
        pdf.write_bytes(pdf_bytes())
        self.workspace = Workspace(self.root / "project")
        self.workspace.create(pdf, "What changed in these findings?")
        self.workspace.prepare()
        self.workspace.set_port(8790)
        self.session = self.workspace.summary()["session_id"]
        self.service = AgentPdfWorkbenchService(db_path=self.workspace.root / "events.db")
        self.annotation = {"id": "ann_first", "page": 1, "type": "highlight", "quote": "Reading workflow test source.",
            "anchor": None, "rects": [], "comment": "Original interpretation", "tags": [],
            "createdAt": "2026-10-28T12:00:00+00:00", "updatedAt": "2026-10-28T12:00:00+00:00"}
        self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
        self.import_annotation()

    def import_annotation(self, accept_updates=False):
        preview = self.workspace.preview([self.annotation["id"]], [])
        return self.workspace.apply(preview["id"], accept_updates=accept_updates)

    def test_read_only_changes_preserve_editions_and_detect_unimported_edit(self):
        first = self.workspace.make_brief("a" * 32)
        files = [self.workspace.file, self.workspace.root / "events.db", self.workspace.root / "rks/rks.sqlite3"]
        before = [p.read_bytes() for p in files]
        initial = maintenance.inspect(self.workspace)
        self.assertEqual(initial["freshness"], "current")
        self.assertEqual(initial["changes"], [])
        self.assertEqual(before, [p.read_bytes() for p in files])
        original = Path(first["path"]).read_bytes()
        self.annotation.update(comment="Revised interpretation", updatedAt="2026-10-28T13:00:00+00:00")
        self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
        changed = maintenance.inspect(self.workspace, save=True)
        self.assertEqual(changed["freshness"], "outdated")
        self.assertIn("reading_changed_since_import", changed["attention"][0]["message"])
        self.assertTrue(Path(changed["path"]).is_file())
        self.assertEqual(changed["changes"][0]["before"]["record"]["item"]["content"]["comment"], "Original interpretation")
        self.import_annotation(accept_updates=True)
        second = self.workspace.make_brief("b" * 32)
        self.assertEqual(maintenance.inspect(self.workspace)["freshness"], "current")
        self.assertEqual(Path(first["path"]).read_bytes(), original)
        self.assertIn("Revised interpretation", Path(second["path"]).read_text(encoding="utf-8"))
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 2)
        replay = self.workspace.make_brief("a" * 32)
        self.assertTrue(replay["replayed"])
        self.assertEqual(self.workspace.summary()["brief"]["id"], "b" * 32)
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 2)

    def test_review_and_source_changes_identify_affected_interpretations(self):
        entry = self.workspace.search("source")["results"][0]
        created = self.workspace.compare("create", payload={"title": "Fixture comparison", "criteria": ["Result"]})["comparison"]
        current = self.workspace.compare("set", comparison_id=created["id"], expected_revision=created["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "text": "Literal fixture finding", "conditions": "Synthetic test",
                     "origin": "agent", "evidence": [{"note_id": entry["note_id"], "revision": entry["revision"]}]})["comparison"]
        first = self.workspace.make_brief()
        self.workspace.compare("review", comparison_id=current["id"], expected_revision=current["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "reviewer": "Synthetic test reviewer", "scope": "Engineering only",
                     "decision": "accepted", "statement": "Fixture, not scientific validation"})
        updated = maintenance.inspect(self.workspace)
        self.assertEqual(updated["freshness"], "outdated")
        self.assertEqual(updated["changes"][0]["category"], "comparisons")
        second = self.workspace.make_brief()
        Path(self.workspace.summary()["source_pdf"]).write_bytes(b"changed source")
        stale = maintenance.inspect(self.workspace)
        self.assertEqual(stale["freshness"], "outdated")
        affected = [a for a in stale["attention"] if a["kind"] == "interpretation"]
        self.assertEqual(affected[0]["id"], current["id"])
        self.assertIn("review: stale", affected[0]["message"])
        saved = maintenance.history(self.workspace, second["id"])
        self.assertEqual(saved["snapshot"]["comparisons"][0]["cells"][0]["review"]["status"], "accepted")
        self.assertNotIn("Synthetic test reviewer", maintenance.history(self.workspace, first["id"])["text"])

    def test_interrupted_publication_replays_committed_edition_and_tampering_fails(self):
        with patch.object(self.workspace, "save", side_effect=OSError("lost publication response")):
            with self.assertRaises(OSError):
                self.workspace.make_brief("c" * 32)
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 1)
        result = self.workspace.make_brief("c" * 32)
        self.assertTrue(result["replayed"])
        self.assertEqual(maintenance.inspect(self.workspace)["freshness"], "current")
        path = self.workspace.root / "briefs" / ("c" * 32) / "record.json"
        saved = read_json(path)
        saved["text"] = "altered"
        write_json(path, saved)
        with self.assertRaisesRegex(WorkflowError, "history changed"):
            maintenance.inspect(self.workspace)

    def test_interrupted_render_is_not_published_and_resume_uses_one_edition(self):
        first = self.workspace.make_brief()
        self.annotation.update(comment="Changed", updatedAt="2026-10-28T14:00:00+00:00")
        self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
        original = maintenance.capture
        calls = 0
        def changed_during_render(workspace):
            nonlocal calls
            result = original(workspace)
            calls += 1
            if calls == 2:
                result["revision"] = "different"
            return result
        with patch.object(maintenance, "capture", side_effect=changed_during_render):
            with self.assertRaisesRegex(WorkflowError, "No edition was published"):
                self.workspace.make_brief("d" * 32)
        self.assertEqual(maintenance.history(self.workspace)["pending_briefs"], ["d" * 32])
        self.assertEqual(maintenance.inspect(self.workspace)["freshness"], "outdated")
        self.assertEqual(self.workspace.summary()["brief"]["id"], first["id"])
        self.workspace.make_brief("d" * 32)
        self.assertEqual(maintenance.history(self.workspace)["pending_briefs"], [])
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 2)

    def test_paper_additions_and_legacy_briefs_are_preserved(self):
        first = self.workspace.make_brief()
        pdf = self.root / "revision.pdf"
        pdf.write_bytes(pdf_bytes("A second source revision."))
        self.workspace.add([pdf])
        report = maintenance.inspect(self.workspace)
        self.assertEqual(report["freshness"], "outdated")
        self.assertEqual(report["changes"][0]["after"]["key"], "p2")
        self.workspace.add([pdf])
        self.assertEqual(len(self.workspace.load()["papers"]), 2)
        self.assertTrue(Path(first["path"]).is_file())
        legacy = self.workspace.root / "briefs" / "legacy.md"
        legacy.write_text("Earlier output without a snapshot", encoding="utf-8")
        self.assertEqual(maintenance.history(self.workspace)["legacy_briefs"][0]["freshness"], "unverified")

    def test_repeat_discovery_is_bounded_attributed_and_never_selects_candidates(self):
        before = self.workspace.file.read_bytes()
        old = discovery.discover(self.workspace, "search", "conditions", provider="crossref", limit=2,
                                 client=FakeClient(records=[crossref(), crossref("10.1234/previous")]))
        repeat = discovery.repeat(self.workspace, old["id"], client=FakeClient(records=[
            crossref(title="Changed metadata"), crossref("10.1234/new")]))
        self.assertEqual(repeat["repeated_from"]["revision"], old["revision"])
        self.assertEqual(repeat["limit"], 2)
        self.assertEqual(len(repeat["candidate_changes"]["added"]), 1)
        self.assertEqual(len(repeat["candidate_changes"]["not_returned"]), 1)
        self.assertEqual(len(repeat["candidate_changes"]["changed"]), 1)
        self.assertEqual(before, self.workspace.file.read_bytes())
        self.assertEqual(discovery.show(self.workspace, old["id"]), old)

    def test_http_scope_and_brief_retry_use_the_same_project_contract(self):
        self.workspace.set_port(0)
        self.addCleanup(lambda: server.stop(self.workspace))
        state = server.ensure_running(self.workspace)
        port = self.workspace.load()["port"]
        payload = {"action": "brief", "session_id": state["session_id"], "request_id": "e" * 32}
        created = server.request(port, "/api/workflow", payload)["brief"]
        replay = server.request(port, "/api/workflow", payload)["brief"]
        self.assertEqual(created["id"], replay["id"])
        self.assertTrue(replay["replayed"])
        checked = server.request(port, f"/api/workflow/maintenance?session_id={state['session_id']}")
        self.assertEqual(checked["freshness"], "current")
        archived = server.request(port, f"/api/workflow/maintenance?session_id={state['session_id']}&edition_id={created['id']}")
        self.assertIn("Original interpretation", archived["text"])
        with self.assertRaises(WorkflowError):
            server.request(port, "/api/workflow/maintenance?session_id=foreign")
        with self.assertRaises(WorkflowError):
            server.request(port, "/api/workflow", {"action": "project_update", "session_id": "foreign"})
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 1)


if __name__ == "__main__":
    unittest.main()
