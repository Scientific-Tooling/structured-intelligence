"""Offline export/import journey using installed APW and RKS environments."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from test_reading_integration import ADAPTER, APW_PYTHON, RKS_PYTHON, sample_pdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_reading import run_json

EVIDENCE = ADAPTER.with_name("research_evidence.py")
STAMP = "2026-10-26T12:00:00+00:00"


@unittest.skipUnless(RKS_PYTHON and APW_PYTHON, "Set RKS_TEST_PYTHON and APW_TEST_PYTHON for integration")
class EvidenceIntegrationTest(unittest.TestCase):
    def test_selected_export_preview_import_edit_review_delete_and_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pdf = root / "source α.pdf"
            pdf.write_bytes(sample_pdf())
            data, db = root / "rks", root / "apw.db"
            env = {"RKS_DATA_DIR": str(data), "RKS_AUTO_EXTRACT_MODE": "none"}
            rks = [RKS_PYTHON, "-m", "rks"]
            apw = [APW_PYTHON, "-m", "agent_pdf_workbench.dev_cli", "--db-path", str(db)]
            paper = run_json(rks + ["ingest", "pdf", str(pdf)], env=env)
            handoff = run_json([
                sys.executable, str(ADAPTER), paper["id"], "--workspace-id", "integration",
                "--rks-data-dir", str(data), "--apw-db", str(db), "--cache-dir", str(root / "cache"),
                "--rks-python", RKS_PYTHON, "--apw-python", APW_PYTHON,
            ])
            handoff_path = root / "handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            session_id = handoff["apw"]["session_id"]
            annotation = {"id": "ann_selected", "page": 1, "type": "highlight",
                          "quote": "Reading handoff test source.", "anchor": None, "rects": [], "tags": [],
                          "comment": "Unreviewed machine interpretation α", "createdAt": STAMP, "updatedAt": STAMP}
            note = {"id": "note_selected", "title": "Synthetic note", "markdown": "A reading observation.",
                    "linkedAnnotationIds": [annotation["id"]], "createdAt": STAMP, "updatedAt": STAMP}
            # Fixture setup uses APW's public service API; adapters only use CLIs.
            fixture = root / "fixture.json"
            fixture.write_text(json.dumps({"annotation": annotation, "note": note}), encoding="utf-8")
            setup = """
import json, sys
from pathlib import Path
from agent_pdf_workbench.service import AgentPdfWorkbenchService
svc = AgentPdfWorkbenchService(Path(sys.argv[1]))
fixture = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
svc.upsert_annotation(session_id=sys.argv[2], annotation=fixture['annotation'])
svc.upsert_note(session_id=sys.argv[2], note=fixture['note'])
print('{}')
"""
            run_json([APW_PYTHON, "-c", setup, str(db), session_id, str(fixture)])
            bundle_path, plan_path = root / "bundle.json", root / "plan.json"
            result = run_json([
                sys.executable, str(EVIDENCE), str(handoff_path), "--source-id", "reader",
                "--annotation-id", annotation["id"], "--note-id", note["id"],
                "--bundle", str(bundle_path), "--plan", str(plan_path),
                "--rks-python", RKS_PYTHON, "--apw-python", APW_PYTHON,
            ])
            self.assertEqual(result["counts"]["addition"], 2)
            self.assertFalse(result["applied"])
            self.assertEqual(run_json(rks + ["note", "evidence", paper["id"]], env=env)["evidence"], [])
            apply = rks + ["note", "import-evidence", str(bundle_path), "--workspace-id", "integration",
                           "--apply", "--plan", str(plan_path)]
            self.assertEqual(run_json(apply, env=env)["counts"]["added"], 2)
            self.assertEqual(run_json(apply, env=env)["counts"]["unchanged"], 2)

            brief_command = [
                sys.executable, str(ADAPTER.with_name("research_brief.py")), paper["id"],
                "--question", "What is recorded in this synthetic reading fixture?",
                "--workspace-id", "integration", "--rks-data-dir", str(data),
                "--source-id", "reader", "--apw-db", str(db),
                "--rks-python", RKS_PYTHON, "--apw-python", APW_PYTHON,
            ]
            brief_file = root / "brief.md"
            brief = run_json(brief_command + ["--output", str(brief_file)])
            self.assertEqual(brief["counts"]["linked_passages"], 2)
            self.assertEqual(brief["counts"]["unreviewed"], 2)
            links = re.findall(r"\[Open the supporting passage\]\(([^)]+)\)", brief_file.read_text(encoding="utf-8"))
            self.assertEqual(len(links), 2)
            query = parse_qs(urlsplit(links[0]).query)
            resolve = apw + ["resolve-passage"]
            for key, value in query.items():
                resolve += ["--" + key.replace("_", "-"), value[0]]
            self.assertEqual(run_json(resolve)["annotation"]["id"], annotation["id"])

            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            item = next(i for i in bundle["items"] if i["kind"] == "annotation")
            reviews = {"schema": "scientific-tooling.evidence-reviews.v1", "source_id": "reader",
                       "paper_ref": handoff["apw"]["paper_ref"], "reviews": {"annotation:ann_selected": {
                           "status": "reviewed", "reviewer": "integration test fixture", "reviewed_at": STAMP,
                           "method": "human", "content_revision": item["content_revision"],
                           "statement": "Synthetic provenance test; not a scientific review.",
                       }}}
            reviews_path = root / "reviews.json"
            reviews_path.write_text(json.dumps(reviews), encoding="utf-8")
            reviewed = run_json(apw + ["export-evidence", "--session-id", session_id, "--source-id", "reader",
                                       "--annotation-id", annotation["id"], "--reviews", str(reviews_path)])
            bundle_path.write_text(json.dumps(reviewed), encoding="utf-8")
            preview = rks + ["note", "import-evidence", str(bundle_path), "--workspace-id", "integration"]
            plan = run_json(preview, env=env, accepted_returncodes=(2,))
            self.assertEqual(plan["items"][0]["reason"], "revision_changed")
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            self.assertFalse(run_json(apply, env=env, accepted_returncodes=(2,))["applied"])
            self.assertEqual(run_json(apply + ["--accept-updates"], env=env)["counts"]["updated"], 1)
            records = run_json(rks + ["note", "evidence", paper["id"]], env=env)["evidence"]
            self.assertEqual(len(records), 2)  # Omitted note was not deleted.
            self.assertEqual(sorted(len(r["history"]) for r in records), [1, 2])
            delete = """
import json, sys
from pathlib import Path
from agent_pdf_workbench.service import AgentPdfWorkbenchService
print(json.dumps(AgentPdfWorkbenchService(Path(sys.argv[1])).delete_annotation(
    session_id=sys.argv[2], annotation_id='ann_selected')))
"""
            self.assertTrue(run_json([APW_PYTHON, "-c", delete, str(db), session_id])["deleted"])
            self.assertEqual(run_json(apply, env=env)["counts"]["unchanged"], 1)
            self.assertEqual(len(run_json(rks + ["note", "evidence", paper["id"]], env=env)["evidence"]), 2)
            unavailable_file = root / "brief-after-deletion.md"
            unavailable = run_json(brief_command + ["--output", str(unavailable_file)])
            self.assertEqual(unavailable["counts"]["unavailable_passages"], 2)
            self.assertEqual(unavailable["counts"]["linked_passages"], 0)
            self.assertIn("Source quote", unavailable_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
