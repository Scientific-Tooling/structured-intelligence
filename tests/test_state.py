"""Exercise atomic state behavior with real filesystem handles and failures."""
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from scientific_tooling.state import open_record, read_json, write_json


class AtomicRecordTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.path = self.root / "record-\u00e9-\U0001f9ec.json"

    def test_open_reader_keeps_previous_complete_revision(self):
        write_json(self.path, {"revision": 1})
        with open_record(self.path) as earlier:
            for revision in range(2, 102):
                write_json(self.path, {"revision": revision})
                self.assertEqual(read_json(self.path), {"revision": revision})
            self.assertEqual(json.load(earlier), {"revision": 1})
        self.assertEqual(list(self.root.glob(".pending-*")), [])

    def test_invalid_serialization_preserves_previous_record(self):
        write_json(self.path, {"revision": 1})
        with self.assertRaises(ValueError):
            write_json(self.path, {"invalid": float("nan")})
        self.assertEqual(read_json(self.path), {"revision": 1})
        self.assertEqual(list(self.root.glob(".pending-*")), [])

    def test_replacement_failure_preserves_existing_directory(self):
        self.path.mkdir()
        with self.assertRaises(OSError):
            write_json(self.path, {"revision": 1})
        self.assertTrue(self.path.is_dir())
        self.assertEqual(list(self.root.glob(".pending-*")), [])

    @unittest.skipUnless(os.name == "nt", "Windows read-only attribute")
    def test_windows_read_only_attribute_is_not_bypassed(self):
        write_json(self.path, {"revision": 1})
        self.path.chmod(stat.S_IREAD)
        try:
            with self.assertRaises(PermissionError):
                write_json(self.path, {"revision": 2})
            self.assertEqual(read_json(self.path), {"revision": 1})
            self.assertEqual(list(self.root.glob(".pending-*")), [])
        finally:
            self.path.chmod(stat.S_IWRITE)


if __name__ == "__main__":
    unittest.main()
