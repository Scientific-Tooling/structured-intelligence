from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_brief as workflow


class ResearchBriefTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.pdf = self.root / "retained.pdf"
        self.pdf.write_bytes(b"%PDF-1.4\nretained")
        self.sha = hashlib.sha256(self.pdf.read_bytes()).hexdigest()
        self.passage = {"annotation_id": "ann α", "page": 2, "quote": "source quote", "anchor": None, "rects": []}
        self.item = {"kind": "annotation", "id": "ann α", "content": {
            "comment": "An interpretation [unsafe](javascript:alert(1)) <script>"},
            "passages": [self.passage], "review": {"status": "unreviewed"}}
        self.item["revision"] = workflow.digest(self.item)
        self.record = {"schema": "scientific-tooling.selected-evidence.v1", "workspace_id": "lab",
                       "paper_id": "p_000001", "document": {"path": str(self.pdf), "sha256": self.sha,
                                                             "size_bytes": self.pdf.stat().st_size},
                       "source": {"source_id": "reader", "session_id": "ps_1",
                                  "paper_ref": f"rks:lab:p_000001:sha256:{self.sha}"}, "item": self.item}
        self.payload = {"paper_id": "p_000001", "evidence": [{"note_id": "n_000001", "paper_id": "p_000001",
                        "revision": self.item["revision"], "record": self.record}]}
        self.resolved = {"schema": "apw.passage.v1", "document_sha256": self.sha,
                         "passage_sha256": workflow.digest(self.passage),
                         "session": {"paper_ref": self.record["source"]["paper_ref"], "pdf_uri": str(self.pdf)}}
        self.args = workflow.build_parser().parse_args([
            "p_000001", "--question", "What does this source support?", "--workspace-id", "lab",
            "--rks-data-dir", str(self.root / "rks"), "--source-id", "reader", "--apw-db", str(self.root / "apw.db"),
            "--output", str(self.root / "brief.md"),
        ])

    def test_generates_literal_content_with_exact_passage_links(self):
        with patch.object(workflow, "run_json", side_effect=[self.payload, self.resolved]) as run:
            result = workflow.generate_brief(self.args)
        self.assertEqual(result["counts"]["unreviewed"], 1)
        self.assertEqual(result["counts"]["linked_passages"], 1)
        output = self.args.output.read_text(encoding="utf-8")
        self.assertIn("Unreviewed reading material", output)
        self.assertIn(r"\[unsafe\]", output)
        self.assertIn(r"\<script\>", output)
        self.assertNotIn("--apply", repr(run.call_args_list))
        query = parse_qs(urlsplit(workflow.passage_url("http://127.0.0.1:8790", self.record, self.passage)).query)
        self.assertEqual(query["annotation_id"], ["ann α"])
        self.assertEqual(query["document_sha256"], [self.sha])
        self.assertEqual(query["passage_sha256"], [workflow.digest(self.passage)])

    def test_unavailable_passage_retains_quote_without_an_active_citation(self):
        with patch.object(workflow, "run_json", return_value=self.payload), patch.object(
            workflow, "check_passage", return_value=(False, "Deleted annotation: restore the backup.")
        ):
            result = workflow.generate_brief(self.args)
        output = self.args.output.read_text(encoding="utf-8")
        self.assertIn("source quote", output)
        self.assertIn("Passage unavailable", output)
        self.assertNotIn("[Open the supporting passage]", output)
        self.assertEqual(result["counts"]["unavailable_passages"], 1)

    def test_reviewed_item_preserves_actual_asserted_scope(self):
        self.item["review"] = {"status": "reviewed", "reviewer": "synthetic fixture", "reviewed_at": "2026-10-26",
                               "statement": "Fixture only; no scientific review was performed."}
        self.item["revision"] = workflow.digest({key: value for key, value in self.item.items() if key != "revision"})
        self.payload["evidence"][0]["revision"] = self.item["revision"]
        with patch.object(workflow, "run_json", side_effect=[self.payload, self.resolved]):
            result = workflow.generate_brief(self.args)
        self.assertEqual(result["counts"]["reviewed"], 1)
        self.assertIn("no scientific review was performed", self.args.output.read_text())

    def test_wrong_workspace_and_missing_selected_note_fail(self):
        for option, value in (("workspace_id", "other"), ("rks_note_id", ["missing"])):
            previous = getattr(self.args, option)
            setattr(self.args, option, value)
            with patch.object(workflow, "run_json", return_value=self.payload), self.assertRaises(workflow.WorkflowError):
                workflow.generate_brief(self.args)
            self.assertFalse(self.args.output.exists())
            setattr(self.args, option, previous)

    def test_existing_brief_is_preserved(self):
        self.args.output.write_text("existing brief", encoding="utf-8")
        with patch.object(workflow, "run_json") as run, self.assertRaises(workflow.WorkflowError):
            workflow.generate_brief(self.args)
        run.assert_not_called()
        self.assertEqual(self.args.output.read_text(), "existing brief")

    def test_corrupt_document_and_stale_passage_response_are_unavailable(self):
        self.pdf.write_bytes(b"changed")
        with patch.object(workflow, "run_json", return_value=self.resolved):
            ready, message = workflow.check_passage(["apw-dev"], self.record, self.passage)
        self.assertFalse(ready)
        self.assertIn("PDF changed", message)
        self.resolved["passage_sha256"] = "a" * 64
        with patch.object(workflow, "run_json", return_value=self.resolved):
            ready, message = workflow.check_passage(["apw-dev"], self.record, self.passage)
        self.assertFalse(ready)
        self.assertIn("Unexpected APW", message)
