from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_reading as workflow


class ResearchReadingTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.pdf_path = self.root / "a paper α.pdf"
        self.pdf_path.write_bytes(b"%PDF-1.4\nsource\n%%EOF\n")
        self.cache = self.root / "cache"
        self.db = self.root / "events.db"
        self.source = {
            "schema": "rks.paper-source.v1",
            "paper_id": "p_000001",
            "title": "Paper",
            "pdf": {
                "path": str(self.pdf_path),
                "size_bytes": self.pdf_path.stat().st_size,
                "sha256": hashlib.sha256(self.pdf_path.read_bytes()).hexdigest(),
            },
        }

    def args(self, *extra):
        return workflow.build_parser().parse_args(
            [
                "p_000001",
                "--workspace-id",
                "review-a",
                "--rks-data-dir",
                str(self.root / "rks"),
                "--apw-db",
                str(self.db),
                "--cache-dir",
                str(self.cache),
                *extra,
            ]
        )

    def test_snapshot_survives_source_change(self) -> None:
        snapshot = workflow.snapshot_pdf(self.source["pdf"], self.cache)
        original = snapshot.read_bytes()
        self.pdf_path.write_bytes(b"a different revision")
        self.assertEqual(snapshot.read_bytes(), original)
        # A verified cached revision remains usable even if the mutable source moves.
        self.pdf_path.unlink()
        self.assertEqual(workflow.snapshot_pdf(self.source["pdf"], self.cache), snapshot)

    def test_changed_source_fails_before_creating_session_and_removes_partial_copy(self) -> None:
        self.pdf_path.write_bytes(b"changed during handoff")
        with patch.object(workflow, "run_json", return_value=self.source) as run:
            with self.assertRaisesRegex(workflow.WorkflowError, "changed during handoff"):
                workflow.open_reading(self.args())
        self.assertEqual(run.call_count, 1)
        self.assertEqual(list(self.cache.iterdir()), [])
        self.assertFalse(self.db.exists())

    def test_corrupt_cache_is_reported_without_overwriting_it(self) -> None:
        snapshot = workflow.snapshot_pdf(self.source["pdf"], self.cache)
        snapshot.write_bytes(b"external edit")
        with self.assertRaisesRegex(workflow.WorkflowError, "Cached PDF has changed"):
            workflow.snapshot_pdf(self.source["pdf"], self.cache)
        self.assertEqual(snapshot.read_bytes(), b"external edit")

    def test_reuses_matching_session_after_pagination(self) -> None:
        self.db.touch()
        ref = f"rks:review-a:p_000001:sha256:{self.source['pdf']['sha256']}"
        snapshot = (self.cache / f"{self.source['pdf']['sha256']}.pdf").resolve()
        session = {"id": "ps_existing", "paper_ref": ref, "pdf_uri": str(snapshot), "closed_at": None}
        with patch.object(
            workflow,
            "run_json",
            side_effect=[
                self.source,
                {"sessions": [], "has_more": True, "next_offset": 100},
                {"sessions": [session], "has_more": False, "next_offset": None},
            ],
        ) as run:
            result = workflow.open_reading(self.args())
        self.assertTrue(result["apw"]["reused_session"])
        self.assertEqual(result["apw"]["session_id"], "ps_existing")
        self.assertEqual(run.call_args_list[-1].args[0][-2:], ["--offset", "100"])

    def test_equivalent_snapshot_path_spelling_reuses_the_existing_session(self) -> None:
        self.db.touch()
        alias_directory = self.cache / "path-spelling"
        alias_directory.mkdir(parents=True)
        snapshot_alias = alias_directory / ".." / f"{self.source['pdf']['sha256']}.pdf"
        session = {"id": "ps_alias", "paper_ref": f"rks:review-a:p_000001:sha256:{self.source['pdf']['sha256']}",
                   "pdf_uri": str(snapshot_alias), "closed_at": None}
        with patch.object(workflow, "run_json", side_effect=[self.source, {
            "sessions": [session], "has_more": False,
        }]) as run:
            result = workflow.open_reading(self.args())
        self.assertTrue(result["apw"]["reused_session"])
        self.assertEqual(result["apw"]["session_id"], "ps_alias")
        self.assertEqual(run.call_count, 2)  # No open-paper write after the source/list reads.

    def test_namespaces_separate_papers_with_identical_local_ids_and_bytes(self) -> None:
        references = []
        for workspace_id in ("review-a", "review-b"):
            with patch.object(workflow, "run_json", side_effect=[self.source, {"id": "ps_new"}]):
                result = workflow.open_reading(self.args("--workspace-id", workspace_id))
            references.append(result["apw"]["paper_ref"])
            self.assertFalse(result["apw"]["reused_session"])
        self.assertNotEqual(*references)

    def test_relative_session_path_is_not_reinterpreted_from_the_adapter_directory(self) -> None:
        self.db.touch()
        self.cache.mkdir()
        candidate = {"id": "ps_relative", "paper_ref": f"rks:review-a:p_000001:sha256:{self.source['pdf']['sha256']}",
                     "pdf_uri": f"{self.source['pdf']['sha256']}.pdf", "closed_at": None}
        previous = Path.cwd()
        try:
            os.chdir(self.cache)
            with patch.object(workflow, "run_json", side_effect=[self.source, {
                "sessions": [candidate], "has_more": False,
            }, {"id": "ps_new"}]):
                result = workflow.open_reading(self.args())
        finally:
            os.chdir(previous)
        self.assertFalse(result["apw"]["reused_session"])
        self.assertEqual(result["apw"]["session_id"], "ps_new")

    def test_session_with_different_pdf_path_is_not_reused(self) -> None:
        self.db.touch()
        with patch.object(
            workflow,
            "run_json",
            side_effect=[
                self.source,
                {
                    "sessions": [
                        {
                            "id": "ps_wrong",
                            "paper_ref": f"rks:review-a:p_000001:sha256:{self.source['pdf']['sha256']}",
                            "pdf_uri": str(self.pdf_path),
                            "closed_at": None,
                        }
                    ],
                    "has_more": False,
                },
                {"id": "ps_new"},
            ],
        ):
            result = workflow.open_reading(self.args())
        self.assertFalse(result["apw"]["reused_session"])
        self.assertEqual(result["apw"]["session_id"], "ps_new")

    def test_source_contract_rejects_unknown_schema_identity_and_invalid_hash(self) -> None:
        for update in (
            {"schema": "v0"},
            {"paper_id": "p_other"},
            {"pdf": {**self.source["pdf"], "sha256": "../escape"}},
        ):
            with self.subTest(update=update):
                with self.assertRaises(workflow.WorkflowError):
                    workflow.validate_source({**self.source, **update}, "p_000001")

    def test_invalid_configuration_fails_before_any_command_or_file_write(self) -> None:
        for extra in (("--workspace-id", "bad:namespace"), ("--viewer-url", "file:///tmp/viewer")):
            with self.subTest(extra=extra), patch.object(workflow, "run_json") as run:
                with self.assertRaises(workflow.WorkflowError):
                    workflow.open_reading(self.args(*extra))
                run.assert_not_called()
        self.assertFalse(self.cache.exists())

    def test_command_boundary_handles_unicode_and_arguments_literally(self) -> None:
        value = "space α & $(not a command)"
        result = workflow.run_json(
            [sys.executable, "-c", "import json, sys; print(json.dumps({'value': sys.argv[1]}))", value]
        )
        self.assertEqual(result["value"], value)

    def test_command_failures_and_non_json_are_actionable(self) -> None:
        for code, error in (("raise SystemExit(7)", "Command failed"), ("print('text')", "did not return JSON")):
            with self.subTest(code=code), self.assertRaisesRegex(workflow.WorkflowError, error):
                workflow.run_json([sys.executable, "-c", code])


if __name__ == "__main__":
    unittest.main()
