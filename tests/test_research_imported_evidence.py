from __future__ import annotations

import argparse
import copy
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_imported_evidence as evaluation
from research_corpus import evaluate_rankings, load_corpus


class ImportedEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.corpus, self.questions = load_corpus()
        self.fixture = evaluation.make_fixture(self.corpus, self.questions)

    def packet(self):
        return evaluation.seal({"schema": evaluation.PACKET, "questions": self.questions["questions"],
                                "comparison": {"cells": [{"key": "cell-1", "cell_revision": "fixture",
                                                           "text": "Synthetic unreviewed interpretation"}]}})

    def test_exact_jats_notes_never_invent_pdf_anchors_or_change_reference_set(self):
        evaluation.validate_fixture(self.fixture, self.corpus, self.questions)
        self.assertEqual(len(self.fixture["entries"]), 24)
        self.assertEqual(len({e["canonical_id"] for e in self.fixture["entries"]}), 23)
        self.assertEqual(len({e["paper_id"] for e in self.fixture["entries"]}), 10)
        for entry in self.fixture["entries"]:
            note = evaluation.note(entry, "2026-10-29T12:00:00Z")
            self.assertEqual(note["markdown"], entry["text"])
            self.assertEqual(note["title"], "")
            self.assertEqual(note["linkedAnnotationIds"], [])
            self.assertEqual(entry["match_role"], "commentary")
            self.assertIsNone(entry["pdf_anchor"])

    def test_changed_or_resealed_fixture_cannot_silently_remap_a_passage(self):
        self.fixture["entries"][0]["paper_id"] = "foreign"
        for reseal in (False, True):
            if reseal:
                self.fixture = evaluation.seal({k: v for k, v in self.fixture.items() if k != "revision"})
            with self.assertRaises(evaluation.WorkflowError):
                evaluation.validate_fixture(self.fixture, self.corpus, self.questions)

    def test_source_correction_extends_the_same_paragraph_without_relabeling_questions(self):
        folder = evaluation.DEFAULT_CORPUS.parent / "imported-evidence-2026-10-29" / "corpus-source-complete"
        corpus, questions = load_corpus(folder)
        self.assertEqual(questions["questions"], self.questions["questions"])
        self.assertEqual(corpus["papers"], self.corpus["papers"])
        self.assertEqual(corpus["variants"], self.corpus["variants"])
        self.assertEqual(corpus["lineage"]["parent_corpus_revision"], evaluation.digest(self.corpus))
        changed = []
        for before, after in zip(self.corpus["passages"], corpus["passages"], strict=True):
            if before == after:
                continue
            changed.append(before["id"])
            for key in ("id", "paper_id", "selector", "transform", "source_text_sha256", "start"):
                self.assertEqual(before[key], after[key])
            self.assertTrue(after["text"].startswith(before["text"]))
            self.assertEqual(after["end"] - after["start"], len(after["text"]))
            self.assertIn("with increasing asymmetry", after["text"])
            self.assertIn("scran25 and SCnorm26", after["text"])
            self.assertTrue(after["text"].endswith("Linnorm29."))
        self.assertEqual(changed, ["vieth2019.normalization"])

    def test_importing_evaluator_does_not_redirect_application_imports(self):
        root = Path(__file__).resolve().parents[1]
        code = ("import sys; sys.path.insert(0, 'scripts'); before = sys.path.copy(); "
                "import research_imported_evidence; assert sys.path == before, sys.path")
        subprocess.run([sys.executable, "-c", code], cwd=root, check=True,
                       env={**os.environ, "PYTHONPATH": str(root / "src")}, capture_output=True)

    def test_candidate_rejects_checkout_metadata_even_if_source_bytes_would_match(self):
        class CheckoutDistribution:
            def read_text(self, name):
                return "{}"

            def locate_file(self, name):
                return Path(__file__).resolve().parents[1] / "src" / name

        with patch.object(evaluation, "read_json", return_value={"schema": "scientific-tooling.development-candidate.v1"}), \
                patch.object(evaluation.importlib.metadata, "distribution", return_value=CheckoutDistribution()), \
                self.assertRaisesRegex(evaluation.WorkflowError, "outside the installed environment"):
            evaluation.candidate_identity(Path("synthetic-manifest.json"))

    def test_duplicate_does_not_add_credit_or_backfill_the_native_cutoff(self):
        duplicate = self.corpus["variants"][0]
        doc = duplicate["canonical_id"]
        rankings = {q["id"]: [duplicate["id"], doc] for q in self.questions["questions"]}
        result = evaluate_rankings(self.corpus, self.questions, {evaluation.METHOD: rankings})
        self.assertTrue(all(row["ranking"] == [doc] for row in result["methods"][evaluation.METHOD]["questions"]))
        self.assertEqual(result["methods"][evaluation.METHOD]["aggregate"]["all"]["answerable_questions"], 18)
        self.assertEqual(result["unanswerable_probes"], 2)
        self.assertFalse(result["domain_review_complete"])

    def test_relevant_sixth_native_result_stays_outside_top_five_after_duplicate_collapse(self):
        duplicate = self.corpus["variants"][0]
        target = next(q for q in self.questions["questions"] if q["expected_passages"]
                      and duplicate["canonical_id"] not in q["expected_passages"])
        distractors = [p["id"] for p in self.corpus["passages"]
                       if p["id"] not in target["expected_passages"] and p["id"] != duplicate["canonical_id"]][:3]
        ranks = {q["id"]: [] for q in self.questions["questions"]}
        ranks[target["id"]] = [duplicate["id"], duplicate["canonical_id"], *distractors, target["expected_passages"][0]]
        result = evaluation.score_rankings(self.corpus, self.questions, ranks)
        row = next(r for r in result["methods"][evaluation.METHOD]["questions"] if r["id"] == target["id"])
        self.assertEqual(row["metrics"]["hit_at_5"], 0)
        self.assertEqual(row["metrics"]["recall_at_5"], 0)
        self.assertEqual(row["metrics"]["mrr_at_10"], 1 / 6)

    def sample_search(self):
        item = {"kind": "note", "content": {"markdown": "exact source text"}, "review": {"status": "unreviewed"}}
        entry = {"note_id": "n1", "source_key": "key", "revision": "rev", "paper_id": "p1", "record": {"item": item},
                 "passages": [], "matches": [{"role": "commentary"}]}
        payload = {"schema": "scientific-tooling.evidence-search.v1", "workspace_id": "w", "source_id": "s",
                   "unavailable_evidence": [], "results": [entry]}
        mapping = {"n1": {"document_id": "d1", "source_key": "key", "revision": "rev", "paper_id": "p1", "text": "exact source text"}}
        return payload, mapping, {"workspace_id": "w", "source_id": "s"}

    def test_foreign_unknown_duplicate_or_changed_results_fail(self):
        for mutate in (lambda p: p.update(workspace_id="foreign"), lambda p: p["results"][0].update(note_id="foreign"),
                       lambda p: p["results"].append(copy.deepcopy(p["results"][0])),
                       lambda p: p["results"][0].update(revision="changed"),
                       lambda p: p["results"][0]["record"]["item"]["content"].update(markdown="changed"),
                       lambda p: p["results"][0].update(passages=[{"page": 1}]),
                       lambda p: p["results"][0]["matches"][0].update(role="source")):
            payload, mapping, scope = self.sample_search()
            self.assertEqual(evaluation.map_results(payload, mapping, scope), ["d1"])
            mutate(payload)
            with self.assertRaises(evaluation.WorkflowError):
                evaluation.map_results(payload, mapping, scope)

    def test_template_contains_only_pending_reviews_and_no_invented_held_out_questions(self):
        packet = self.packet()
        response = evaluation.response_template(packet)
        result = evaluation.review_status(packet, response)
        self.assertEqual(result["counts"], {"pending": 21, "approved": 0, "revise": 0, "exclude": 0})
        self.assertEqual(response["held_out_questions"], [])
        self.assertFalse(result["release_gate_passed"])

    def test_missing_duplicate_or_stale_reviews_are_rejected(self):
        packet = self.packet()
        for mutate in (lambda r: r["records"].pop(), lambda r: r["records"].append(copy.deepcopy(r["records"][0])),
                       lambda r: r.update(packet_revision="stale"), lambda r: r["records"][0].update(target_revision="stale")):
            response = evaluation.response_template(packet)
            mutate(response)
            with self.assertRaises(evaluation.WorkflowError):
                evaluation.review_status(packet, response)

    def test_human_provenance_and_timezone_required_and_never_qualify_release(self):
        packet = self.packet()
        response = evaluation.response_template(packet)
        record = response["records"][0]
        record.update(decision="approved")
        with self.assertRaises(evaluation.WorkflowError):
            evaluation.review_status(packet, response)
        record.update(method="human", reviewer="Synthetic fixture only", reviewed_at="2026-10-29T12:00:00Z",
                      independent_of_implementation=True, notes="Synthetic validator test, not a scientific review")
        self.assertEqual(evaluation.review_status(packet, response)["counts"]["approved"], 1)
        self.assertFalse(evaluation.review_status(packet, response)["release_gate_passed"])
        record["reviewed_at"] = "2026-10-29T12:00:00"
        with self.assertRaises(evaluation.WorkflowError):
            evaluation.review_status(packet, response)

    def test_corrupted_packet_cannot_reuse_valid_review_responses(self):
        packet = self.packet()
        response = evaluation.response_template(packet)
        packet["questions"][0]["question"] = "Changed target"
        with self.assertRaises(evaluation.WorkflowError):
            evaluation.review_status(packet, response)

    def test_source_failure_precedes_any_evaluation_workspace_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture.json"
            evaluation.write_json(fixture, self.fixture)
            args = argparse.Namespace(corpus=evaluation.DEFAULT_CORPUS, fixture=fixture, cache=root / "missing",
                                      candidate_manifest=root / "candidate.json", run_dir=root / "run")
            # Only importing the application types needs installed packages.
            with patch.dict(sys.modules, {"agent_pdf_workbench.service": type("M", (), {"AgentPdfWorkbenchService": object}),
                                         "scientific_tooling.server": type("M", (), {"HostedWorkflow": object}),
                                         "scientific_tooling.workspace": type("M", (), {"Workspace": object})}), self.assertRaises(evaluation.WorkflowError):
                evaluation.run(args)
            self.assertFalse(args.run_dir.exists())

    def test_comparison_support_must_keep_source_scope_revision_and_available_passage(self):
        source = self.corpus["papers"][0]
        item = evaluation.seal({"kind": "annotation", "review": {"status": "unreviewed"},
                                "passages": [{"page": 1, "quote": "Fixture text"}]})
        entry = {"note_id": "n1", "source_key": "source1", "revision": item["revision"],
                 "record": {"workspace_id": "w", "source": {"source_id": "s"}, "paper_id": "p_1", "item": item,
                            "document": {"path": "synthetic.pdf", "sha256": source["pdf"]["sha256"]}},
                 "passages": [{"page": 1, "quote": "Fixture text", "available": True}]}
        cell = {"text": "Synthetic interpretation", "origin": "agent",
                "paper_source": "p_1:" + source["pdf"]["sha256"], "evidence": [entry]}
        comparison = {"workspace_id": "w", "source_id": "s", "cells": [cell, copy.deepcopy(cell)]}
        with patch.object(evaluation, "verify_bytes"):
            self.assertEqual(len(evaluation.comparison_sources(comparison, self.corpus)), 1)
            for mutate in (lambda c: c["cells"][0]["evidence"][0]["record"].update(workspace_id="foreign"),
                           lambda c: c["cells"][0]["evidence"][0].update(revision="changed"),
                           lambda c: c["cells"][0]["evidence"][0]["passages"][0].update(available=False),
                           lambda c: c["cells"][0].update(paper_source="wrong-paper")):
                changed = copy.deepcopy(comparison)
                mutate(changed)
                with self.assertRaises(evaluation.WorkflowError):
                    evaluation.comparison_sources(changed, self.corpus)
        with patch.object(evaluation, "verify_bytes", side_effect=evaluation.WorkflowError("Changed PDF")), self.assertRaisesRegex(evaluation.WorkflowError, "Changed PDF"):
            evaluation.comparison_sources(comparison, self.corpus)

    def test_harness_retention_is_exact_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = evaluation.retain_harness(root)
            for name, content in evaluation.HARNESS.items():
                self.assertEqual((root / "harness" / name).read_bytes(), content)
                self.assertEqual(evaluation.sha_file(root / "harness" / name), identity[name])
            with self.assertRaises(FileExistsError):
                evaluation.retain_harness(root)

    def test_live_packet_check_distinguishes_current_changed_and_unavailable_support(self):
        comparison = {"id": "synthetic", "revision": "old"}
        packet = evaluation.seal({"schema": evaluation.PACKET, "candidate": {"candidate": "test"},
                                  "workspace": "synthetic", "comparison": comparison, "sources": []})
        current = copy.deepcopy(comparison)

        class Workspace:
            def __init__(self, root):
                pass

            def compare(self, action, **kwargs):
                return {"comparison": current}

        args = argparse.Namespace(packet=Path("synthetic.json"), candidate_manifest=Path("candidate.json"))
        with patch.dict(sys.modules, {"scientific_tooling.workspace": type("M", (), {"Workspace": Workspace})}), \
                patch.object(evaluation, "read_json", return_value=packet), \
                patch.object(evaluation, "candidate_identity", return_value=packet["candidate"]), \
                patch.object(evaluation, "comparison_sources") as sources:
            self.assertEqual(evaluation.check_packet(args)["freshness"], "current")
            current["revision"] = "new"
            self.assertEqual(evaluation.check_packet(args)["freshness"], "outdated")
            sources.side_effect = evaluation.WorkflowError("Unavailable support")
            with self.assertRaisesRegex(evaluation.WorkflowError, "Unavailable support"):
                evaluation.check_packet(args)

    def test_readable_packet_contains_every_canonical_excerpt_and_table_boundaries(self):
        packet = {"revision": "fixture", "candidate": {"candidate": "fixture"}, "questions": self.questions["questions"],
                  "sources": self.corpus["papers"], "entries": self.fixture["entries"], "evidence": [],
                  "comparison": {"title": "Synthetic", "revision": "fixture", "criteria": [], "cells": []}}
        rendered = evaluation.render_packet(packet)
        for passage in self.corpus["passages"]:
            self.assertIn("### Passage " + passage["id"], rendered)
        table = next(e for e in self.fixture["entries"] if e["source"]["kind"] == "table")
        self.assertIn("```text\n" + table["text"] + "\n```", rendered)
        self.assertIn("CC BY 4.0", rendered)


if __name__ == "__main__":
    unittest.main()
