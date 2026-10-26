from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_evidence as workflow


class EvidencePreparationTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.pdf = self.root / "snapshot.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\nsource")
        sha = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.document = {"path": str(self.pdf), "sha256": sha, "size_bytes": self.pdf.stat().st_size}
        self.ref = f"rks:lab:p_000001:sha256:{sha}"
        self.handoff = {"schema": "scientific-tooling.reading-handoff.v1", "workspace_id": "lab",
                        "rks_data_dir": str(self.root / "rks"),
                        "source": {"schema": "rks.paper-source.v1", "paper_id": "p_000001", "pdf": self.document},
                        "snapshot": self.document,
                        "apw": {"db_path": str(self.root / "apw.db"), "paper_ref": self.ref, "session_id": "ps_1"}}
        self.handoff_path = self.root / "handoff.json"
        self.handoff_path.write_text(json.dumps(self.handoff), encoding="utf-8")
        self.bundle = {"schema": "scientific-tooling.selected-evidence.v1", "workspace_id": "lab",
                       "paper_id": "p_000001", "source": {"paper_ref": self.ref, "source_id": "reader",
                                                          "session_id": "ps_1"}, "document": self.document}
        self.plan = {"schema": "rks.evidence-import-plan.v1", "applied": False,
                     "counts": {"addition": 0, "unchanged": 0, "conflict": 1}}
        self.args = workflow.build_parser().parse_args([
            str(self.handoff_path), "--source-id", "reader", "--annotation-id", "ann α;literal",
            "--bundle", str(self.root / "bundle.json"), "--plan", str(self.root / "plan.json"),
        ])

    def test_writes_exact_bundle_and_conflict_report_without_apply(self):
        with patch.object(workflow, "run_json", side_effect=[self.bundle, self.plan]) as run:
            result = workflow.prepare_evidence(self.args)
        self.assertFalse(result["applied"])
        self.assertEqual(json.loads(self.args.bundle.read_text()), self.bundle)
        self.assertEqual(json.loads(self.args.plan.read_text()), self.plan)
        self.assertIn("ann α;literal", run.call_args_list[0].args[0])
        self.assertNotIn("--apply", run.call_args_list[1].args[0])
        self.assertEqual(run.call_args_list[1].kwargs["accepted_returncodes"], (0, 2))

    def test_corrupt_snapshot_fails_before_commands(self):
        self.pdf.write_bytes(b"changed")
        with patch.object(workflow, "run_json") as run, self.assertRaisesRegex(workflow.WorkflowError, "snapshot changed"):
            workflow.prepare_evidence(self.args)
        run.assert_not_called()

    def test_mismatched_export_is_not_published(self):
        self.bundle["source"]["source_id"] = "other"
        with patch.object(workflow, "run_json", return_value=self.bundle), self.assertRaisesRegex(
            workflow.WorkflowError, "does not match"
        ):
            workflow.prepare_evidence(self.args)
        self.assertFalse(self.args.bundle.exists())

    def test_existing_artifact_is_preserved(self):
        self.args.plan.write_text("reviewed plan", encoding="utf-8")
        with patch.object(workflow, "run_json") as run, self.assertRaisesRegex(workflow.WorkflowError, "new paths"):
            workflow.prepare_evidence(self.args)
        run.assert_not_called()
        self.assertEqual(self.args.plan.read_text(), "reviewed plan")

    def test_failed_preview_keeps_export_for_diagnosis(self):
        with (
            patch.object(workflow, "run_json", side_effect=[self.bundle, workflow.WorkflowError("rks migrate")]),
            self.assertRaisesRegex(workflow.WorkflowError, "migrate"),
        ):
            workflow.prepare_evidence(self.args)
        self.assertEqual(json.loads(self.args.bundle.read_text()), self.bundle)
        self.assertFalse(self.args.plan.exists())
