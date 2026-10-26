from __future__ import annotations

import copy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_corpus_journey as journey


class CorpusJourneyTest(unittest.TestCase):
    def setUp(self):
        self.case = {"id": "case-1", "page": 1, "quote": "A source quote.", "note": "Unreviewed fixture note."}

    def test_repeated_seeding_preserves_existing_annotation_and_timestamps(self):
        stored = []
        writes = []

        def api(_base, route, payload=None):
            if payload is not None:
                stored.append(payload["annotation"])
                writes.append(payload)
                return {"annotation": stored[-1]}
            return {"annotations": [{"annotation": item} for item in stored], "has_more": False}

        with patch.object(journey, "api", side_effect=api):
            first = journey.ensure_annotation("http://127.0.0.1:8794", "ps_1", self.case)
            second = journey.ensure_annotation("http://127.0.0.1:8794", "ps_1", self.case)
        self.assertEqual(first, second)
        self.assertEqual(len(writes), 1)
        self.assertIn("unreviewed", first["tags"])
        self.assertNotIn("reviewer", first)

    def test_existing_reading_edits_are_not_overwritten(self):
        with patch.object(journey, "api") as api:
            api.return_value = {"annotations": [{"annotation": {"id": "corpus-case-1", "page": 2}}], "has_more": False}
            with self.assertRaises(journey.WorkflowError):
                journey.ensure_annotation("http://127.0.0.1:8794", "ps_1", self.case)
        self.assertEqual(api.call_count, 1)

    def test_source_validation_precedes_http_or_workspace_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            args = type("Args", (), {"corpus": journey.DEFAULT_CORPUS, "cache": Path(temporary),
                                     "output_dir": Path(temporary) / "new"})()
            with patch.object(journey, "verify_sources", side_effect=journey.WorkflowError("corrupt source")), patch.object(
                journey, "api"
            ) as api, patch.object(journey, "run_json") as run, self.assertRaises(journey.WorkflowError):
                journey.run_journey(args)
            api.assert_not_called()
            run.assert_not_called()
            self.assertFalse(args.output_dir.exists())

    def test_invalid_case_path_is_rejected_before_any_viewer_operation(self):
        corpus, _ = journey.load_corpus()
        plan = journey.read_json(journey.DEFAULT_CORPUS / "journey.json")
        plan = copy.deepcopy(plan)
        plan["cases"][0]["id"] = "../../escape"
        with tempfile.TemporaryDirectory() as temporary:
            args = type("Args", (), {"corpus": journey.DEFAULT_CORPUS, "cache": Path(temporary),
                                     "output_dir": Path(temporary) / "new", "viewer_url": "http://127.0.0.1:8794",
                                     "benchmark_run": Path(temporary)})()
            with patch.object(journey, "verify_sources"), patch.object(journey, "read_json", side_effect=[
                plan, {"corpus_revision": journey.digest(corpus)}, {"paper_ids": {p["id"]: p["id"] for p in corpus["papers"]}},
            ]), patch.object(journey, "api") as api, self.assertRaisesRegex(journey.WorkflowError, "case ID"):
                journey.run_journey(args)
            api.assert_not_called()
