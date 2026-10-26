from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import research_corpus as corpus_tools


class ResearchCorpusTest(unittest.TestCase):
    def setUp(self):
        self.corpus, self.questions = corpus_tools.load_corpus()

    def refreeze_for_validation_test(self):
        self.questions["corpus_revision"] = corpus_tools.digest(self.corpus)

    def test_real_starter_corpus_is_attributed_and_split_before_scoring(self):
        self.assertEqual(len(self.corpus["papers"]), 10)
        self.assertEqual(len(self.corpus["passages"]), 23)
        self.assertEqual(sum(q["split"] == "development" for q in self.questions["questions"]), 14)
        self.assertEqual(sum(q["split"] == "reserved" for q in self.questions["questions"]), 6)
        self.assertEqual(sum(not q["answerable_from_excerpts"] for q in self.questions["questions"]), 2)

    def test_missing_attribution_and_license_evidence_are_not_accepted(self):
        for field, value in (("authors", []), ("license", {"spdx": "unknown", "url": "", "evidence_text": "", "evidence_sha256": ""})):
            with self.subTest(field=field):
                corpus = copy.deepcopy(self.corpus)
                questions = copy.deepcopy(self.questions)
                corpus["papers"][0][field] = value
                questions["corpus_revision"] = corpus_tools.digest(corpus)
                with self.assertRaises(corpus_tools.WorkflowError):
                    corpus_tools.validate_corpus(corpus, questions)

    def test_duplicate_papers_cannot_inflate_corpus_size(self):
        self.corpus["papers"][1]["doi"] = self.corpus["papers"][0]["doi"]
        self.refreeze_for_validation_test()
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "Duplicate DOIs"):
            corpus_tools.validate_corpus(self.corpus, self.questions)

    def test_attribution_urls_cannot_be_swapped_between_papers(self):
        self.corpus["papers"][0]["source_url"] = self.corpus["papers"][1]["source_url"]
        self.refreeze_for_validation_test()
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "attribution links"):
            corpus_tools.validate_corpus(self.corpus, self.questions)

    def test_changed_question_source_and_cross_split_paper_leak_are_rejected(self):
        self.corpus["passages"][0]["text"] += " changed"
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "different corpus revision"):
            corpus_tools.validate_corpus(self.corpus, self.questions)
        self.corpus, self.questions = corpus_tools.load_corpus()
        self.questions["questions"][0]["split"] = "reserved"
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "leaks"):
            corpus_tools.validate_corpus(self.corpus, self.questions)

    def test_table_column_boundaries_and_source_slice_hashes_are_checked(self):
        table = next(p for p in self.corpus["passages"] if p["kind"] == "table")
        table["table"]["headers"].pop()
        self.refreeze_for_validation_test()
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "column boundaries"):
            corpus_tools.validate_corpus(self.corpus, self.questions)
        root = ET.fromstring("<article><body><p>First <italic>source</italic> sentence.</p></body></article>")
        passage = {"selector": "body.p.1", "kind": "text", "transform": "jats-itertext-whitespace-v1",
                   "source_text_sha256": corpus_tools.text_hash("First source sentence."), "start": 6, "end": 12}
        self.assertEqual(corpus_tools.extract_passage(root, passage), "source")
        passage["source_text_sha256"] = "0" * 64
        with self.assertRaises(corpus_tools.WorkflowError):
            corpus_tools.extract_passage(root, passage)

    def test_duplicate_representations_are_collapsed_without_extra_credit(self):
        variant = self.corpus["variants"][0]
        ranked = corpus_tools.canonical_ranking(self.corpus, [variant["id"], variant["canonical_id"]])
        self.assertEqual(ranked, [variant["canonical_id"]])
        metrics = corpus_tools.ranking_metrics([variant["canonical_id"], "other-relevant-source"], ranked)
        self.assertEqual(metrics["recall_at_5"], 0.5)
        self.assertEqual(metrics["hit_at_1"], 1)
        with self.assertRaises(corpus_tools.WorkflowError):
            corpus_tools.ranking_metrics([variant["canonical_id"]], [variant["canonical_id"]] * 2)

    def test_source_cache_corruption_fails_without_fetch_or_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "paper.xml"
            path.write_bytes(b"corrupt")
            descriptor = {"url": "https://example.invalid/paper.xml", "sha256": hashlib.sha256(b"expected").hexdigest(), "size_bytes": 8}
            before = path.read_bytes()
            with patch.object(corpus_tools.urllib.request, "urlopen") as fetch, self.assertRaises(corpus_tools.WorkflowError):
                corpus_tools.fetch_sources({"papers": [{"id": "paper", "xml": descriptor}]}, Path(temporary))
            fetch.assert_not_called()
            self.assertEqual(path.read_bytes(), before)

    def test_changed_remote_source_is_not_published_as_expected_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            descriptor = {"url": "https://example.invalid/paper.xml", "sha256": hashlib.sha256(b"expected").hexdigest(), "size_bytes": 8}
            with patch.object(corpus_tools.urllib.request, "urlopen") as fetch:
                fetch.return_value.__enter__.return_value.read.return_value = b"new revision"
                with self.assertRaisesRegex(corpus_tools.WorkflowError, "source changed"):
                    corpus_tools.fetch_sources({"papers": [{"id": "paper", "xml": descriptor}]}, Path(temporary))
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_bm25_is_a_deterministic_baseline_not_entailment(self):
        docs = [{"id": "a", "text": "Cells from one donor are not independent."},
                {"id": "b", "text": "Cellular sequencing depth is a covariate."}]
        self.assertEqual(corpus_tools.rank_bm25(docs, "sequencing depth covariate")[0], "b")
        # A lexical ranker can retrieve a negated statement for either polarity.
        self.assertEqual(corpus_tools.rank_bm25(docs, "donor cells independent")[0], "a")

    def test_unanswerable_probes_do_not_change_retrieval_denominators(self):
        rankings = {q["id"]: list(q["expected_passages"]) for q in self.questions["questions"]}
        result = corpus_tools.evaluate_rankings(self.corpus, self.questions, {"fixture-oracle": rankings})
        self.assertEqual(result["methods"]["fixture-oracle"]["aggregate"]["all"]["answerable_questions"], 18)
        self.assertEqual(result["unanswerable_probes"], 2)
        self.assertIsNone(result["scientific_accuracy"])
        self.assertIsNone(result["abstention_accuracy"])
        self.assertFalse(result["domain_review_complete"])

    def test_missing_unknown_or_partial_rankings_fail(self):
        with self.assertRaises(corpus_tools.WorkflowError):
            corpus_tools.evaluate_rankings(self.corpus, self.questions, {"incomplete": {}})
        with self.assertRaises(corpus_tools.WorkflowError):
            corpus_tools.canonical_ranking(self.corpus, ["invented-passage"])

    def test_review_template_is_pending_not_a_scientific_approval(self):
        packet = corpus_tools.review_packet(self.corpus, self.questions)
        status = corpus_tools.review_status(self.corpus, self.questions, packet)
        self.assertEqual((status["approved"], status["pending"]), (0, 20))
        self.assertFalse(status["reference_review_complete"])
        record = packet["records"][0]
        record["decision"] = "approved"
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "Actual review"):
            corpus_tools.review_status(self.corpus, self.questions, packet)

    def test_explicit_review_requires_exact_revisions_and_timezone(self):
        packet = corpus_tools.review_packet(self.corpus, self.questions)
        record = packet["records"][0]
        record.update(decision="approved", method="human", reviewer="synthetic test fixture", reviewed_at="2026-10-26T12:00:00+00:00",
                      notes="Unit-test assertion only; not an actual corpus review.")
        self.assertEqual(corpus_tools.review_status(self.corpus, self.questions, packet)["approved"], 1)
        record["reviewed_at"] = "2026-10-26T12:00:00"
        with self.assertRaises(corpus_tools.WorkflowError):
            corpus_tools.review_status(self.corpus, self.questions, packet)
        packet["corpus_revision"] = "bad"
        with self.assertRaisesRegex(corpus_tools.WorkflowError, "stale"):
            corpus_tools.review_status(self.corpus, self.questions, packet)
