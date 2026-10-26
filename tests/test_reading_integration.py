"""Opt-in, offline integration against installed RKS and APW environments."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_reading import run_json

RKS_PYTHON = os.environ.get("RKS_TEST_PYTHON")
APW_PYTHON = os.environ.get("APW_TEST_PYTHON")
ADAPTER = Path(__file__).resolve().parents[1] / "scripts" / "research_reading.py"


def sample_pdf() -> bytes:
    """A generated one-page document with no external data or copyright dependency."""
    stream = b"BT /F1 12 Tf 72 720 Td (Reading handoff test source.) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(pdf))
        pdf += str(index).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 6\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode()
    pdf += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(pdf)


@unittest.skipUnless(
    RKS_PYTHON and APW_PYTHON, "Set RKS_TEST_PYTHON and APW_TEST_PYTHON for cross-repository integration"
)
class ReadingIntegrationTest(unittest.TestCase):
    def test_open_repeat_revision_and_namespace_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_path = root / "paper α with spaces.pdf"
            source_bytes = sample_pdf()
            source_path.write_bytes(source_bytes)
            data_dir = root / "rks"
            apw_db = root / "apw" / "events.db"
            env = {"RKS_DATA_DIR": str(data_dir), "RKS_AUTO_EXTRACT_MODE": "none"}
            paper = run_json([RKS_PYTHON, "-m", "rks", "ingest", "pdf", str(source_path)], env=env)
            command = [
                sys.executable,
                str(ADAPTER),
                paper["id"],
                "--workspace-id",
                "integration",
                "--rks-data-dir",
                str(data_dir),
                "--apw-db",
                str(apw_db),
                "--cache-dir",
                str(root / "cache"),
                "--rks-python",
                RKS_PYTHON,
                "--apw-python",
                APW_PYTHON,
            ]
            first = run_json(command)
            second = run_json(command)
            self.assertFalse(first["apw"]["reused_session"])
            self.assertTrue(second["apw"]["reused_session"])
            self.assertEqual(first["apw"]["session_id"], second["apw"]["session_id"])
            self.assertEqual(Path(first["snapshot"]["path"]).read_bytes(), source_bytes)
            self.assertEqual(first["snapshot"]["sha256"], hashlib.sha256(source_bytes).hexdigest())

            # The same paper ID and bytes in an explicitly different workspace stay separate.
            other = run_json(command + ["--workspace-id", "another-workspace"])
            self.assertNotEqual(first["apw"]["paper_ref"], other["apw"]["paper_ref"])

            # Source replacement creates a new document identity and preserves the old snapshot.
            Path(paper["pdf_path"]).write_bytes(source_bytes + b"\n% revision two\n")
            revised = run_json(command)
            self.assertNotEqual(first["apw"]["paper_ref"], revised["apw"]["paper_ref"])
            self.assertEqual(Path(first["snapshot"]["path"]).read_bytes(), source_bytes)
            exported = run_json([APW_PYTHON, "-m", "agent_pdf_workbench.dev_cli", "--db-path", str(apw_db), "export"])
            self.assertEqual(exported["session_count"], 3)
            self.assertEqual(exported["paper_count"], 3)


if __name__ == "__main__":
    unittest.main()
