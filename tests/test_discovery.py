"""Frozen provider fixtures and real installed reading handoffs; no scientific review implied."""
from __future__ import annotations

import json
import io
import socket
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from http.client import IncompleteRead
from unittest.mock import patch

from scientific_tooling import cli, discovery, discovery_sources as sources, server
from scientific_tooling.reading import WorkflowError
from scientific_tooling.workspace import Workspace
from test_workflow import pdf_bytes


def crossref(doi="10.1234/example", title="Literal conditions: no effect at 5 mg", links=True):
    return {"DOI": doi, "title": [title], "author": [{"given": "A", "family": "Researcher"}],
            "issued": {"date-parts": [[2024]]}, "container-title": ["Fixture Journal"], "type": "journal-article",
            "link": [{"content-type": "application/pdf", "URL": "https://papers.example/source.pdf"}] if links else []}


def pubmed():
    return b'''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>12345</PMID><Article>
      <ArticleTitle>Literal <i>conditions</i>: no effect at 5 mg</ArticleTitle>
      <Abstract><AbstractText Label="RESULT">No effect at 5 mg.</AbstractText></Abstract>
      <Journal><Title>Fixture Journal</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
      <AuthorList><Author><ForeName>A</ForeName><LastName>Researcher</LastName></Author></AuthorList>
      </Article></MedlineCitation><PubmedData><ArticleIdList>
      <ArticleId IdType="pubmed">12345</ArticleId><ArticleId IdType="doi">10.1234/EXAMPLE</ArticleId>
      <ArticleId IdType="pmc">PMC12345</ArticleId></ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>'''


class FakeClient:
    def __init__(self, records=None, pdf=None):
        self.records = records if records is not None else [crossref()]
        self.pdf = pdf or pdf_bytes("Selected discovery source.")
        self.calls = []

    def fetch(self, url, *, pdf=False):
        self.calls.append((url, pdf))
        if pdf:
            raw = self.pdf
        elif "esearch.fcgi" in url:
            raw = json.dumps({"esearchresult": {"idlist": ["12345"], "count": "1", "querytranslation": "frozen translation"}}).encode()
        elif "efetch.fcgi" in url:
            raw = pubmed()
        elif "/works?" in url:
            raw = json.dumps({"status": "ok", "message": {"items": self.records, "total-results": len(self.records)}}).encode()
        else:
            raw = json.dumps({"status": "ok", "message": self.records[0]}).encode()
        return raw, {"requested_url": url, "resolved_url": url, "content_type": "application/pdf" if pdf else "application/json"}


class DiscoveryTest(unittest.TestCase):
    def test_bibliography_is_bound_to_the_selected_work(self):
        data = self.workspace.load()
        data["works"] = [{"id": "w_first", "authors": ["A Researcher"], "year": 2024, "venue": "Fixture Journal"},
                         {"id": "w_other", "authors": ["Other Author"], "year": 2020, "venue": "Other Journal"}]
        paper = {"key": "p1", "title": "A paper", "paper_id": None, "phase": "reading", "sha256": "a" * 64,
                 "handoff": "absent.json", "work_id": "w_first"}
        before = self.workspace.file.read_bytes()
        self.assertEqual(self.workspace.paper_summary(data, paper)["bibliography"],
                         {"authors": ["A Researcher"], "year": 2024, "venue": "Fixture Journal"})
        paper.pop("work_id")
        self.assertIsNone(self.workspace.paper_summary(data, paper)["bibliography"])
        self.assertEqual(before, self.workspace.file.read_bytes())

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.workspace = Workspace(self.root / "review")
        self.workspace.initialize("Which conditions differ?")
        self.addCleanup(lambda: server.stop(self.workspace))
        self.client = FakeClient()

    def search(self, **kwargs):
        return discovery.discover(self.workspace, "search", "conditions", provider="crossref", client=self.client, **kwargs)

    def test_bounded_frozen_search_and_read_only_reopen(self):
        run = self.search(limit=2)
        self.assertEqual(run["candidates"][0]["title"], "Literal conditions: no effect at 5 mg")
        self.assertIn("rows=2", run["requests"][0]["url"])
        self.assertEqual(self.workspace.load()["papers"], [])
        self.assertFalse((self.workspace.root / "rks").exists())
        before = self.workspace.file.read_bytes()
        self.assertEqual(discovery.show(self.workspace, run["id"]), run)
        self.assertEqual(len(discovery.inventory(self.workspace)["discoveries"]), 1)
        self.assertEqual(before, self.workspace.file.read_bytes())
        raw = discovery.directory(self.workspace, run["id"]) / run["responses"][0]["path"]
        raw.write_text("changed")
        with self.assertRaisesRegex(WorkflowError, "response changed"):
            discovery.select(self.workspace, run["id"], "c1", client=self.client)
        self.assertEqual(self.workspace.load()["papers"], [])

    def test_pubmed_parser_identifier_normalization_and_provider_provenance(self):
        self.assertEqual(sources.identifier("https://doi.org/10.1234/EXAMPLE"), ("doi", "10.1234/example"))
        run = discovery.discover(self.workspace, "lookup", "pmid:12345", client=self.client)
        candidate = run["candidates"][0]
        self.assertEqual(candidate["identifiers"], {"doi": "10.1234/example", "pmid": "12345", "pmcid": "PMC12345"})
        self.assertEqual(candidate["abstract"], "RESULT: No effect at 5 mg.")
        selected = discovery.select(self.workspace, run["id"], "c1", client=self.client)
        self.assertEqual(discovery.inventory(self.workspace)["selections"][0]["candidate_title"], run["candidates"][0]["title"])
        self.assertEqual(selected["status"], "full_text_unavailable")
        self.assertIsNone(selected["paper_key"])
        self.assertFalse((self.workspace.root / "events.db").exists())
        other = self.search()
        with patch.object(self.workspace, "prepare"):
            added = discovery.select(self.workspace, other["id"], "c1", client=self.client)
        data = self.workspace.load()
        self.assertEqual(len(data["works"]), 1)
        self.assertEqual(len(data["works"][0]["provenance"]), 2)
        self.assertEqual(added["work_id"], selected["work_id"])

    def test_same_work_same_bytes_reused_changed_pdf_is_new_version(self):
        first = self.search()
        with patch.object(self.workspace, "prepare"):
            a = discovery.select(self.workspace, first["id"], "c1", client=self.client)
            b = discovery.select(self.workspace, first["id"], "c1", client=self.client)
            self.assertEqual(a["paper_key"], b["paper_key"])
            self.client.pdf = pdf_bytes("A changed revision.")
            c = discovery.select(self.workspace, first["id"], "c1", client=self.client)
        data = self.workspace.load()
        self.assertEqual(c["work_id"], a["work_id"])
        self.assertNotEqual(c["paper_key"], a["paper_key"])
        self.assertEqual(len(data["papers"]), 2)
        self.assertEqual(len(data["works"]), 1)
        self.assertNotEqual(c["snapshot"]["sha256"], a["snapshot"]["sha256"])
        self.assertTrue(Path(a["snapshot"]["path"]).is_file())

    def test_interrupted_handoff_reuses_retained_bytes_and_exact_request(self):
        run = self.search()
        request_id = "a" * 32
        with patch.object(self.workspace, "prepare", side_effect=WorkflowError("lost handoff response")):
            with self.assertRaisesRegex(WorkflowError, request_id):
                discovery.select(self.workspace, run["id"], "c1", request_id=request_id, client=self.client)
        before = list(self.client.calls)
        self.client.pdf = b"Must never be fetched on this retry"
        with patch.object(self.workspace, "prepare"):
            result = discovery.select(self.workspace, request_id=request_id, retry=True, client=self.client)
            self.assertEqual(result["status"], "added")
            self.assertTrue(discovery.select(self.workspace, request_id=request_id, retry=True, client=self.client)["replayed"])
        self.assertEqual(self.client.calls, before)
        self.assertEqual(len(self.workspace.load()["papers"]), 1)
        with self.assertRaisesRegex(WorkflowError, "different operation"):
            discovery.select(self.workspace, run["id"], "c1", source=1, request_id=request_id, client=self.client)

    def test_download_failures_never_promote_abstracts_or_unselected_sources(self):
        self.client.pdf = b"<html>Login required</html>"
        run = self.search()
        with self.assertRaisesRegex(WorkflowError, "complete PDF"):
            discovery.select(self.workspace, run["id"], "c1", client=self.client)
        self.assertEqual(self.workspace.load()["papers"], [])
        self.assertEqual(len(self.workspace.load()["works"]), 1)
        self.assertFalse((self.workspace.root / "rks").exists())
        self.assertEqual(discovery.inventory(self.workspace)["selections"][0]["status"], "failed")
        item = crossref()
        item["link"].append({"URL": "https://other.example/paper.pdf", "content-type": "application/pdf"})
        self.client.records = [item]
        run = self.search()
        before = list(self.client.calls)
        result = discovery.select(self.workspace, run["id"], "c1", client=self.client)
        self.assertEqual(result["status"], "full_text_unavailable")
        self.assertIn("Multiple", result["error"])
        self.assertEqual(self.client.calls, before)

    def test_local_pdf_requires_explicit_selection_and_preserves_identity_conflicts(self):
        run = self.search()
        local = self.root / "selected.pdf"
        local.write_bytes(pdf_bytes())
        with patch.object(self.workspace, "prepare"):
            selected = discovery.select(self.workspace, run["id"], "c1", pdf=local)
        self.assertEqual(selected["snapshot"]["source"], "user_selected_local_pdf")
        self.client.records = [crossref("10.1234/another")]
        other = self.search()
        with self.assertRaisesRegex(WorkflowError, "different work"):
            discovery.select(self.workspace, other["id"], "c1", pdf=local)
        self.assertEqual(len(self.workspace.load()["papers"]), 1)

    def test_invalid_queries_failed_providers_and_foreign_or_changed_requests(self):
        for query, limit in [("", 10), ("query", 26), ("query", True)]:
            with self.assertRaises(WorkflowError):
                discovery.discover(self.workspace, "search", query, limit=limit, client=self.client)
        with patch.object(self.client, "fetch", side_effect=OSError("Provider unavailable")):
            with self.assertRaisesRegex(WorkflowError, "Provider unavailable"):
                self.search()
        self.assertEqual(discovery.inventory(self.workspace)["discoveries"][0]["status"], "failed")
        run = self.search()
        with patch.object(self.workspace, "prepare"):
            result = discovery.select(self.workspace, run["id"], "c1", client=self.client)
        Path(result["snapshot"]["path"]).write_bytes(b"corrupted")
        with self.assertRaisesRegex(WorkflowError, "changed"):
            discovery.select(self.workspace, request_id=result["request"]["id"], retry=True)

    def test_question_only_project_and_foreign_selection_are_explicit(self):
        self.assertEqual(self.workspace.summary()["phase"], "discovering")
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(cli.main(["init", "--workspace", str(self.workspace.root), "--question", self.workspace.load()["question"]]), 0)
        self.assertIn("discover", output.getvalue())
        self.assertNotIn("Use sci resume", output.getvalue())
        self.assertFalse((self.workspace.root / "rks").exists())
        with self.assertRaisesRegex(WorkflowError, "No PDF"):
            server.ensure_running(self.workspace)
        run = discovery.discover(self.workspace, "lookup", "pmid:12345", client=self.client)
        selected = discovery.select(self.workspace, run["id"], "c1", client=self.client)
        path = self.workspace.root / "selections" / selected["request"]["id"] / "selection.json"
        state = json.loads(path.read_text())
        state["request"]["workspace_id"] = "foreign"
        state["request_revision"] = discovery.digest(state["request"])
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(WorkflowError, "another project"):
            discovery.inventory(self.workspace)

    def test_public_https_guard_rejects_private_sources_and_redirects(self):
        for url in ("http://example.org/p.pdf", "file:///paper.pdf", "https://user:secret@example.org/p.pdf", "https://example.org:8000/x"):
            with self.assertRaises(WorkflowError):
                sources.public_url(url)
        addresses = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch.object(socket, "getaddrinfo", return_value=addresses):
            with self.assertRaisesRegex(WorkflowError, "non-public"):
                sources.public_url("https://example.org/p.pdf")
            with self.assertRaisesRegex(WorkflowError, "non-public"):
                sources.PublicRedirects().redirect_request(None, None, 302, "redirect", {}, "https://example.org/private.pdf")

    def test_malformed_provider_responses_are_saved_failures(self):
        for raw, provider, query in [(b"[]", "crossref", "10.1234/example"), (b"<broken", "pubmed", "pmid:12345")]:
            with patch.object(self.client, "fetch", return_value=(raw, {"requested_url": "https://fixture.example/"})):
                with self.assertRaisesRegex(WorkflowError, "Its query and responses are retained"):
                    discovery.discover(self.workspace, "lookup", query, provider=provider, client=self.client)
        runs = discovery.inventory(self.workspace)["discoveries"]
        self.assertEqual(len(runs), 2)
        self.assertTrue(all(run["status"] == "failed" for run in runs))
        self.assertTrue(all(len(discovery.show(self.workspace, run["id"])["responses"]) == 1 for run in runs))
        run = self.search()
        with patch.object(self.client, "fetch", side_effect=IncompleteRead(b"partial", 20)):
            with self.assertRaisesRegex(WorkflowError, "Use discover retry"):
                discovery.select(self.workspace, run["id"], "c1", client=self.client)
        self.assertEqual(discovery.inventory(self.workspace)["selections"][0]["status"], "failed")
        self.assertEqual(self.workspace.load()["papers"], [])

    def test_actual_ingestion_lost_response_restart_and_saved_source_link(self):
        run = self.search()
        prepare = self.workspace.prepare
        def lose_response():
            prepare()
            raise WorkflowError("lost native response")
        with patch.object(self.workspace, "prepare", side_effect=lose_response):
            with self.assertRaisesRegex(WorkflowError, "lost native"):
                discovery.select(self.workspace, run["id"], "c1", request_id="b" * 32, client=self.client)
        result = discovery.select(self.workspace, request_id="b" * 32, retry=True, client=self.client)
        self.assertEqual(result["status"], "added")
        self.assertEqual(self.workspace.rks("papers", "list")["total_count"], 1)
        self.assertEqual(len(self.workspace.apw("list-sessions")["sessions"]), 1)
        opened = server.ensure_running(self.workspace)
        port = self.workspace.load()["port"]
        session = opened["session_id"]
        fetched = server.request(port, f"/api/workflow/discovery?session_id={session}&discovery_id={run['id']}")
        self.assertEqual(fetched["discovery"], run)
        with self.assertRaises(WorkflowError):
            server.request(port, "/api/workflow/discovery?session_id=foreign")
        server.stop(self.workspace)
        resumed = server.ensure_running(self.workspace)
        self.assertEqual(resumed["session_id"], session)
        self.assertEqual(resumed["viewer_url"], opened["viewer_url"])
        self.assertEqual(self.workspace.search("source")["total"], 0)


if __name__ == "__main__":
    unittest.main()
