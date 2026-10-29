"""Analysis handoffs retain exact support; fixtures never assert scientific approval."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_pdf_workbench.service import AgentPdfWorkbenchService
from scientific_tooling import analysis, maintenance
from scientific_tooling.reading import WorkflowError
from scientific_tooling.state import read_json, write_json
from scientific_tooling.workspace import Workspace
from test_workflow import pdf_bytes


class AnalysisTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        source = self.root / "paper.pdf"
        source.write_bytes(pdf_bytes())
        self.workspace = Workspace(self.root / "project")
        self.workspace.create(source, "Synthetic handoff contract check")
        self.workspace.prepare()
        self.session = self.workspace.summary()["session_id"]
        self.service = AgentPdfWorkbenchService(db_path=self.workspace.root / "events.db")
        self.annotation = {"id": "ann_test", "page": 1, "type": "highlight", "quote": "Reading workflow test source.",
                           "anchor": None, "rects": [], "comment": "Synthetic interpretation", "tags": [],
                           "createdAt": "2026-10-29T10:00:00+00:00", "updatedAt": "2026-10-29T10:00:00+00:00"}
        self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
        self.workspace.apply(self.workspace.preview(["ann_test"], [])["id"])
        entry = self.workspace.search("source")["results"][0]
        comparison = self.workspace.compare("create", payload={"title": "Fixture comparison", "criteria": ["Method", "Other"]})["comparison"]
        self.comparison = self.workspace.compare("set", comparison_id=comparison["id"], expected_revision=comparison["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "text": "Fixture interpretation", "conditions": "Engineering only",
                     "origin": "agent", "evidence": [{"note_id": entry["note_id"], "revision": entry["revision"]}]})["comparison"]
        self.dataset = self.root / "input.h5ad"
        self.dataset.write_bytes(b"Synthetic identity fixture, deliberately not a valid H5AD file.")
        self.environment = self.root / "environment.yml"
        self.environment.write_bytes(b"name: fixture\r\ndependencies: []\r\n")
        self.spec = {"schema": analysis.REQUEST, "title": "Fixture proposal", "purpose": "demonstration", "origin": "agent",
            "comparison": {"id": self.comparison["id"], "revision": self.comparison["revision"],
                           "cells": [self.comparison["cells"][0]["key"]]}, "rationale": "Engineering fixture only",
            "dataset": {"path": "input.h5ad", "label": "Synthetic identity fixture", "format": "h5ad", "provenance": "Test only"},
            "environment": {"path": "environment.yml", "description": "Unexecuted fixture"},
            "analysis": {"method": "pseudobulk-deseq2", "parameters": {
                "cell_type": "DemoCell", "cell_type_column": "cell_type", "condition_column": "condition",
                "reference": "control", "test": "treated", "sample_column": "sample", "counts_source": "layers/counts",
                "design": "~ condition", "min_cells_per_sample": 10, "adjusted_p_threshold": 0.05, "log2fc_threshold": 0.5},
                "assumptions": ["Synthetic counts; no scientific conclusions"], "expected_outputs": ["de.tsv"],
                "resources": {"cpus": 1, "memory_gb": 1, "notes": "Unmeasured test allocation"}}}
        self.spec_path = self.root / "spec.json"
        write_json(self.spec_path, self.spec)

    def create(self, identity="a" * 32):
        return analysis.create(self.workspace, self.spec_path, identity)

    def test_retains_support_and_explicit_draft_and_replays_without_reading_changed_inputs(self):
        result = self.create()
        record = result["handoff"]
        self.assertEqual(record["execution_status"], "not_run")
        self.assertEqual(record["plan_review"], "not_recorded")
        self.assertTrue(record["attention"])
        self.assertEqual(record["basis"]["cells"][0]["review"]["status"], "unreviewed")
        folder = Path(result["path"]).parent
        self.assertEqual((folder / "environment.txt").read_bytes(), self.environment.read_bytes())
        self.assertIn("# Skill: scRNA-seq Differential Expression", (folder / "SKILL.md").read_text())
        before = {p.name: p.read_bytes() for p in folder.iterdir()}
        self.assertEqual(analysis.check(self.workspace, record["id"])["freshness"], "current")
        self.assertEqual(before, {p.name: p.read_bytes() for p in folder.iterdir()})
        self.dataset.write_bytes(b"changed")
        replay = self.create()
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["handoff"], record)
        self.assertEqual(analysis.check(self.workspace, record["id"])["issues"][0]["kind"], "dataset")
        self.assertEqual(len(analysis.inventory(self.workspace)["handoffs"]), 1)

    def test_reading_edits_and_missing_inputs_make_handoff_outdated_without_rewriting_it(self):
        record = self.create()["handoff"]
        saved = analysis.show(self.workspace, record["id"])
        self.annotation.update(comment="Changed interpretation", updatedAt="2026-10-29T11:00:00+00:00")
        self.service.upsert_annotation(session_id=self.session, annotation=self.annotation)
        self.environment.unlink()
        checked = analysis.check(self.workspace, record["id"])
        self.assertEqual({i["kind"] for i in checked["issues"]}, {"support", "environment"})
        self.assertEqual(analysis.show(self.workspace, record["id"]), saved)

    def test_unselected_cell_edits_do_not_invalidate_selected_support_but_review_changes_do(self):
        record = self.create()["handoff"]
        updated = self.workspace.compare("set", comparison_id=self.comparison["id"], expected_revision=self.comparison["revision"],
            payload={"paper": "p1", "criterion_id": "c2", "text": "Unselected fixture", "conditions": "Test",
                     "origin": "agent", "evidence": []})["comparison"]
        self.assertEqual(analysis.check(self.workspace, record["id"])["freshness"], "current")
        self.workspace.compare("review", comparison_id=updated["id"], expected_revision=updated["revision"],
            payload={"paper": "p1", "criterion_id": "c1", "reviewer": "Synthetic fixture reviewer", "scope": "Test only",
                     "decision": "needs_changes", "statement": "Engineering fixture, not scientific review"})
        self.assertEqual(analysis.check(self.workspace, record["id"])["freshness"], "outdated")

    def test_lost_publication_replays_committed_record_and_recovers_missing_artifacts(self):
        with patch.object(analysis, "replace", side_effect=OSError("lost publication response")):
            with self.assertRaises(OSError):
                self.create()
        self.assertEqual(len(analysis.inventory(self.workspace)["handoffs"]), 1)
        result = self.create()
        self.assertTrue(result["replayed"])
        self.assertTrue(Path(result["path"]).is_file())
        self.assertEqual(analysis.inventory(self.workspace)["pending_requests"], [])

    def test_stale_selection_fails_with_a_pending_request_and_request_conflicts_fail(self):
        self.spec["comparison"]["revision"] = "stale"
        write_json(self.spec_path, self.spec)
        with self.assertRaisesRegex(WorkflowError, "Comparison changed"):
            self.create()
        self.assertEqual(analysis.inventory(self.workspace)["pending_requests"], ["a" * 32])
        self.spec["comparison"]["revision"] = self.comparison["revision"]
        write_json(self.spec_path, self.spec)
        with self.assertRaisesRegex(WorkflowError, "different analysis proposal"):
            self.create()
        self.assertFalse(self.create("b" * 32)["replayed"])

    def test_input_change_during_creation_never_commits_a_record(self):
        original = maintenance.stable_snapshot
        def change_after_snapshot(workspace):
            snapshot = original(workspace)
            self.dataset.write_bytes(b"changed during capture")
            return snapshot
        with patch.object(maintenance, "stable_snapshot", side_effect=change_after_snapshot):
            with self.assertRaisesRegex(WorkflowError, "input changed"):
                self.create()
        self.assertEqual(analysis.inventory(self.workspace)["handoffs"], [])
        self.assertEqual(analysis.inventory(self.workspace)["pending_requests"], ["a" * 32])

    def test_modified_artifacts_and_records_are_not_overwritten_and_foreign_workspace_fails(self):
        result = self.create()
        Path(result["path"]).write_text("user edit", encoding="utf-8")
        with self.assertRaisesRegex(WorkflowError, "artifact changed"):
            self.create()
        self.assertEqual(analysis.check(self.workspace, "a" * 32)["issues"][0]["kind"], "artifact")
        data = self.workspace.load()
        data["workspace_id"] = "foreign"
        with patch.object(self.workspace, "load", return_value=data):
            with self.assertRaisesRegex(WorkflowError, "another project"):
                analysis.show(self.workspace, "a" * 32)
        path = Path(result["path"]).parent / "record.json"
        record = read_json(path)
        record["spec"]["rationale"] = "tampered"
        write_json(path, record)
        with self.assertRaisesRegex(WorkflowError, "history changed"):
            analysis.show(self.workspace, "a" * 32)

    def test_malformed_parameters_and_unreviewed_claim_fields_are_rejected(self):
        for mutation in (lambda s: s.update(review="approved"),
                         lambda s: s["comparison"].update(cells=[{}]),
                         lambda s: s["analysis"]["parameters"].update(test="control"),
                         lambda s: s["analysis"]["parameters"].update(adjusted_p_threshold=2)):
            spec = copy.deepcopy(self.spec)
            mutation(spec)
            write_json(self.spec_path, spec)
            with self.assertRaises(WorkflowError):
                self.create()

    def test_installed_cli_emits_the_same_handoff_and_check_contract(self):
        command = [sys.executable, "-m", "scientific_tooling.cli", "analysis"]
        common = ["--workspace", str(self.workspace.root), "--json"]
        created = subprocess.run(command + ["create", str(self.spec_path), "--request-id", "a" * 32] + common,
                                 capture_output=True, text=True, check=True)
        record = json.loads(created.stdout)["handoff"]
        self.assertEqual(record["execution_status"], "not_run")
        self.assertIn("Criterion: Method", record["artifacts"]["handoff.md"])
        self.assertIn(record["spec"]["comparison"]["revision"], record["artifacts"]["handoff.md"])
        checked = subprocess.run(command + ["check", "a" * 32] + common, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(checked.stdout)["freshness"], "current")
        self.dataset.write_bytes(b"changed after handoff")
        outdated = subprocess.run(command + ["check", "a" * 32] + common, capture_output=True, text=True)
        self.assertEqual(outdated.returncode, 2)
        self.assertEqual(json.loads(outdated.stdout)["freshness"], "outdated")


if __name__ == "__main__":
    unittest.main()
