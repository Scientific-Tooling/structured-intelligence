"""Living-project provenance, freshness and crash recovery with installed RKS/APW."""
from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from agent_pdf_workbench.service import AgentPdfWorkbenchService
from agent_pdf_workbench import evidence as apw_evidence, passage as apw_passage
from scientific_tooling import brief, cli, comparison, discovery, maintenance, server
from scientific_tooling.reading import WorkflowError
from scientific_tooling.state import read_json, write_json
from scientific_tooling.workspace import Workspace
from test_discovery import FakeClient, crossref
from test_workflow import pdf_bytes


class OfflineClient:
    def fetch(self, url, *, pdf=False):
        raise OSError("Provider unreachable in this test.")


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

    def add_comparison(self, text):
        entry = self.workspace.search("source")["results"][0]
        created = self.workspace.compare("create", payload={"title": "Fixture", "criteria": ["Result"]})["comparison"]
        return self.workspace.compare("set", comparison_id=created["id"], expected_revision=created["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "text": text, "conditions": "Synthetic",
                     "origin": "agent", "evidence": [{"note_id": entry["note_id"], "revision": entry["revision"]}]})["comparison"]

    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            code = cli.main([*args, "--workspace", str(self.workspace.root)])
        return code, output.getvalue()

    def test_brief_file_holds_exact_edition_bytes_including_carriage_returns(self):
        self.add_comparison("First line\r\nSecond line")
        result = self.workspace.make_brief("f" * 32)
        edition = maintenance.history(self.workspace, result["id"])
        self.assertIn("\r\n", edition["text"])
        path = Path(result["path"])
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), edition["text_sha256"])
        self.assertEqual(self.workspace.summary()["brief"]["text"], edition["text"])
        self.assertTrue(self.workspace.make_brief("f" * 32)["replayed"])
        # Earlier releases wrote brief.md in text mode; that exact translation is still recognised.
        path.write_bytes(edition["text"].replace("\n", "\r\n").encode("utf-8"))
        self.assertEqual(self.workspace.summary()["brief"]["text"], edition["text"])
        path.write_bytes(edition["text"].replace("Second line", "Altered line").encode("utf-8"))
        with self.assertRaisesRegex(WorkflowError, "text or location changed"):
            self.workspace.summary()
        with self.assertRaisesRegex(WorkflowError, "Saved brief text changed"):
            self.workspace.make_brief("f" * 32)

    def test_validation_failures_are_not_listed_as_interrupted_briefs(self):
        self.workspace.set_port(0)
        with self.assertRaisesRegex(WorkflowError, "Resume the reader") as raised:
            self.workspace.make_brief("1" * 32)
        self.assertNotIn("Brief request retained", str(raised.exception))
        self.workspace.set_port(8790)
        original = maintenance.capture
        with patch.object(maintenance, "capture", side_effect=lambda workspace: {**original(workspace), "evidence": []}):
            with self.assertRaisesRegex(WorkflowError, "No matching imported evidence") as raised:
                self.workspace.make_brief("2" * 32)
        self.assertNotIn("Brief request retained", str(raised.exception))
        self.assertEqual(maintenance.history(self.workspace)["pending_briefs"], [])
        self.assertFalse((self.workspace.root / "briefs" / ("1" * 32)).exists())
        self.assertFalse((self.workspace.root / "briefs" / ("2" * 32)).exists())

    def test_interrupted_paper_preparation_is_reported_not_fatal(self):
        first = self.workspace.make_brief()
        pdf = self.root / "interrupted.pdf"
        pdf.write_bytes(pdf_bytes("A paper whose preparation was interrupted."))
        data = self.workspace.load()
        self.workspace.append_papers(data, self.workspace.inspect_pdfs([pdf]))
        self.workspace.save(data)  # sci add stopped before prepare() gave the paper an RKS identity.
        report = maintenance.inspect(self.workspace)
        self.assertEqual(report["freshness"], "outdated")
        self.assertEqual([c["id"] for c in report["changes"]], ["p2"])
        self.assertEqual([(a["kind"], a["paper"]) for a in report["attention"]], [("source", "p2")])
        self.assertIn("interrupted", report["attention"][0]["message"])
        with self.assertRaisesRegex(WorkflowError, "finish preparing"):
            self.workspace.make_brief()
        self.assertEqual(maintenance.history(self.workspace)["pending_briefs"], [])
        self.assertEqual(self.workspace.summary()["brief"]["id"], first["id"])

    def test_presentation_changes_do_not_make_a_brief_outdated(self):
        self.add_comparison("Literal fixture finding")
        result = self.workspace.make_brief()
        check, markdown = brief.check_passage, comparison.render_markdown
        def reworded(*args, **kwargs):
            available, _ = check(*args, **kwargs)
            return available, "Reworded verification message."
        with patch.object(brief, "check_passage", side_effect=reworded), \
                patch.object(comparison, "render_markdown", side_effect=lambda item: "Reworded\n" + markdown(item)):
            report = maintenance.inspect(self.workspace)
        self.assertNotEqual(report["snapshot_revision"], result["snapshot_revision"])
        self.assertEqual(report["freshness"], "current")
        self.assertEqual(report["changes"], [])

    def test_a_damaged_older_edition_does_not_block_a_new_brief(self):
        self.workspace.make_brief("a" * 32)
        path = self.workspace.root / "briefs" / ("a" * 32) / "record.json"
        saved = read_json(path)
        saved["text"] = "altered"
        write_json(path, saved)
        second = self.workspace.make_brief("b" * 32)
        self.assertFalse(second["replayed"])
        self.assertEqual(self.workspace.summary()["brief"]["id"], "b" * 32)
        with self.assertRaisesRegex(WorkflowError, "history changed"):
            maintenance.inspect(self.workspace)

    def test_one_export_per_session_and_a_missing_item_hides_only_itself(self):
        second = {**self.annotation, "id": "ann_second", "comment": "Second interpretation"}
        self.service.upsert_annotation(session_id=self.session, annotation=second)
        self.workspace.apply(self.workspace.preview([second["id"]], [])["id"])
        with patch.object(apw_evidence, "export_evidence", wraps=apw_evidence.export_evidence) as export, \
                patch.object(maintenance, "hash_file", wraps=maintenance.hash_file) as hashed:
            snapshot = maintenance.capture(self.workspace)
        self.assertEqual(export.call_count, 1)
        self.assertEqual(hashed.call_count, 1)  # The source PDF is hashed once for papers and passages.
        self.assertEqual({e["reading_status"] for e in snapshot["evidence"]}, {"unchanged"})
        self.service.delete_annotation(session_id=self.session, annotation_id=second["id"])
        snapshot = maintenance.capture(self.workspace)
        states = {e["record"]["item"]["id"]: e["reading_status"] for e in snapshot["evidence"]}
        self.assertEqual(states, {"ann_first": "unchanged", "ann_second": "unavailable"})

    def test_cli_reports_changes_history_and_saved_brief_freshness(self):
        first = self.workspace.make_brief()
        code, text = self.run_cli("changes")
        self.assertEqual(code, 0)
        self.assertIn("Brief freshness: current", text)
        self.assertIn("0 changes since the last retained edition; 0 items need attention.", text)
        code, text = self.run_cli("update")
        self.assertEqual(code, 0)
        self.assertTrue(Path(text.split("Saved report: ", 1)[1].splitlines()[0]).is_file())
        with patch.object(maintenance, "render_edition", side_effect=WorkflowError("Simulated lost response")):
            with self.assertRaisesRegex(WorkflowError, "Brief request retained"):
                self.workspace.make_brief("c" * 32)
        code, text = self.run_cli("history")
        self.assertEqual(code, 0)
        self.assertIn(f"{first['id']}  {first['created_at']}  {first['path']}", text)
        self.assertIn(f"Interrupted brief: {'c' * 32}. Resume with sci brief --request-id {'c' * 32}.", text)
        code, text = self.run_cli("history", first["id"])
        self.assertTrue(text.startswith("# Source-linked project brief"))
        code, text = self.run_cli("status")
        self.assertIn(f"Brief: {first['path']}", text)
        self.assertIn("Run sci changes to check whether it still matches the project.", text)

    def test_cli_repeats_a_saved_discovery_with_its_original_bounds(self):
        old = discovery.discover(self.workspace, "search", "conditions", provider="crossref", limit=2,
                                 client=FakeClient(records=[crossref(), crossref("10.1234/previous")]))
        with patch.object(discovery.sources, "Client", return_value=FakeClient(records=[crossref("10.1234/new")])):
            code, text = self.run_cli("discover", "repeat", old["id"])
        self.assertEqual(code, 0)
        self.assertIn("Changes from saved discovery", text)
        self.assertIn("Not returned means absent from this bounded result list", text)
        repeated = [run for run in discovery.inventory(self.workspace)["discoveries"] if run["id"] != old["id"]]
        self.assertEqual(discovery.show(self.workspace, repeated[0]["id"])["limit"], 2)

    def test_passages_are_shared_with_comparisons_but_rechecked_between_observations(self):
        entry = self.workspace.search("source")["results"][0]
        created = self.workspace.compare("create", payload={"title": "Fixture", "criteria": ["Result"]})["comparison"]
        self.workspace.compare("set", comparison_id=created["id"], expected_revision=created["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "text": "Fixture", "conditions": "Synthetic",
                     "origin": "agent", "evidence": [{"note_id": entry["note_id"], "revision": entry["revision"]}]})
        self.workspace.make_brief()
        with patch.object(apw_passage, "resolve_passage", wraps=apw_passage.resolve_passage) as resolve, \
                patch.object(self.workspace, "rks", side_effect=AssertionError("Inspection must not spawn RKS")), \
                patch.object(self.workspace, "apw", side_effect=AssertionError("Inspection must not spawn APW")):
            result = maintenance.inspect(self.workspace)
        self.assertEqual(result["freshness"], "current")
        self.assertEqual(resolve.call_count, 2)  # Once per observation, including comparison support.

    def test_missing_rks_database_is_not_created(self):
        database = self.workspace.root / "rks" / "rks.sqlite3"
        database.rename(database.with_suffix(".backup"))
        with self.assertRaisesRegex(WorkflowError, "Cannot inspect this project's RKS state"):
            maintenance.inspect(self.workspace)
        self.assertFalse(database.exists())

    def test_native_reads_reject_a_foreign_workspace_identity(self):
        data = self.workspace.load()
        data["workspace_id"] = "foreign"
        with patch.object(self.workspace, "load", return_value=data):
            with self.assertRaisesRegex(WorkflowError, "another evidence workspace"):
                maintenance.inspect(self.workspace)

    def test_actual_reading_change_between_observations_is_rejected(self):
        original = maintenance.capture
        def edit_after_observation(workspace):
            result = original(workspace)
            self.annotation.update(comment="Changed between observations", updatedAt="2026-10-28T15:00:00+00:00")
            self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
            return result
        with patch.object(maintenance, "capture", side_effect=edit_after_observation):
            with self.assertRaisesRegex(WorkflowError, "changed during inspection"):
                maintenance.inspect(self.workspace)

    def test_missing_reading_database_is_not_created_and_retained_evidence_survives(self):
        self.workspace.make_brief()
        database = self.workspace.root / "events.db"
        database.rename(database.with_suffix(".backup"))
        result = maintenance.inspect(self.workspace)
        self.assertFalse(database.exists())
        self.assertEqual(result["freshness"], "outdated")
        evidence = next(c["after"] for c in result["changes"] if c["category"] == "evidence")
        self.assertEqual(evidence["reading_status"], "unavailable")
        self.assertFalse(evidence["passages"][0]["available"])
        self.assertEqual(evidence["record"]["item"]["content"]["comment"], "Original interpretation")

    def test_export_from_another_source_is_rejected(self):
        original = apw_evidence.export_evidence
        def foreign_export(*args, **kwargs):
            result = original(*args, **kwargs)
            result["paper_id"] = "foreign"
            return result
        with patch.object(apw_evidence, "export_evidence", side_effect=foreign_export):
            snapshot = maintenance.capture(self.workspace)
        self.assertEqual(snapshot["evidence"][0]["reading_status"], "unavailable")
        self.assertIsNone(snapshot["evidence"][0]["reading_item"])

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
        saved = server.request(port, "/api/workflow", {"action": "project_update", "session_id": state["session_id"]})
        self.assertEqual(saved["freshness"], "current")
        self.assertTrue(Path(saved["path"]).is_file())
        with self.assertRaises(WorkflowError):
            discovery.discover(self.workspace, "search", "conditions", provider="crossref", limit=2, client=OfflineClient())
        failed = discovery.inventory(self.workspace)["discoveries"][0]["id"]
        with self.assertRaisesRegex(WorkflowError, "Repeat a completed saved discovery"):
            server.request(port, "/api/workflow", {"action": "discovery_repeat", "session_id": state["session_id"],
                                                   "discovery_id": failed})
        self.assertEqual(len(maintenance.history(self.workspace)["editions"]), 1)


if __name__ == "__main__":
    unittest.main()
