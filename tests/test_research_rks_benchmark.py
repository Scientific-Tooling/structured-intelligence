from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_rks_benchmark as benchmark


class NativeBenchmarkTest(unittest.TestCase):
    def test_source_validation_precedes_any_native_write_or_workspace_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            args = type("Args", (), {"corpus": benchmark.DEFAULT_CORPUS, "cache": root / "cache",
                                     "run_dir": root / "new-run", "rks_python": None})()
            with patch.object(benchmark, "verify_sources", side_effect=benchmark.WorkflowError("corrupt source")), patch.object(
                benchmark, "run_json"
            ) as run, self.assertRaisesRegex(benchmark.WorkflowError, "corrupt"):
                benchmark.run_benchmark(args)
            run.assert_not_called()
            self.assertFalse(args.run_dir.exists())

    def test_existing_workspaces_are_not_reused_or_deleted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "existing.txt"
            marker.write_text("keep", encoding="utf-8")
            args = type("Args", (), {"corpus": benchmark.DEFAULT_CORPUS, "cache": root / "cache",
                                     "run_dir": root, "rks_python": None})()
            with patch.object(benchmark, "verify_sources"), patch.object(benchmark, "run_json") as run:
                with self.assertRaisesRegex(benchmark.WorkflowError, "new run directory"):
                    benchmark.run_benchmark(args)
            run.assert_not_called()
            self.assertEqual(marker.read_text(), "keep")
