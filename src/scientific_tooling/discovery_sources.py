"""Bounded public metadata requests. Discovery is never evidence or full-text reading."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import threading
import time
from urllib.parse import quote, urlencode, urlsplit, unquote
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .reading import WorkflowError

PUBMED = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
CROSSREF = "https://api.crossref.org/works"
METADATA_LIMIT = 10 * 1024 * 1024
PDF_LIMIT = 64 * 1024 * 1024
_network_lock = threading.Lock()
_last_request = 0.0


def public_url(url):
    """Reject local destinations, credentials and unsupported schemes, including redirects."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise WorkflowError("Source URLs must use public HTTPS without credentials or custom ports.")
    addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise WorkflowError("Source URL resolves to a non-public address.")
    return url


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return super().redirect_request(req, fp, code, msg, headers, public_url(newurl))


class Client:
    def fetch(self, url, *, pdf=False):
        global _last_request
        public_url(url)
        # Stay below the unauthenticated NCBI rate within this process, including parallel requests.
        with _network_lock:
            time.sleep(max(0, 0.4 - (time.monotonic() - _last_request)))
            _last_request = time.monotonic()
        request = Request(url, headers={"User-Agent": "Scientific-Tooling/0.3 (bounded research discovery)",
                                      "Accept": "application/pdf" if pdf else "application/json, application/xml, text/xml"})
        limit, deadline = (PDF_LIMIT if pdf else METADATA_LIMIT), time.monotonic() + 60
        with build_opener(PublicRedirects()).open(request, timeout=20) as response:
            content = bytearray()
            while True:
                block = response.read(min(65536, limit + 1 - len(content)))
                content.extend(block)
                if len(content) > limit:
                    raise WorkflowError("Response exceeds the bounded download size.")
                if time.monotonic() > deadline:
                    raise WorkflowError("Source response exceeded the download time limit.")
                if not block:
                    break
            return bytes(content), {"requested_url": url, "resolved_url": response.geturl(),
                                    "content_type": response.headers.get("Content-Type", "")}


def identifier(value):
    value = value.strip()
    if value.startswith(("https://doi.org/", "http://doi.org/")):
        value = unquote(value.split("doi.org/", 1)[1])
    if value.casefold().startswith("doi:"):
        value = value[4:]
    if re.fullmatch(r"10\.\d{4,9}/[^\s?#]+", value, re.IGNORECASE) and len(value) <= 255:
        return "doi", value.casefold()
    match = re.fullmatch(r"(?:pmid:)?([1-9]\d{0,8})", value, re.IGNORECASE)
    if not match:
        match = re.fullmatch(r"https://pubmed\.ncbi\.nlm\.nih\.gov/([1-9]\d{0,8})/?", value)
    if match:
        return "pmid", match[1]
    raise WorkflowError("Use a DOI, PMID, doi:…/pmid:… identifier or its canonical DOI/PubMed URL.")


def normalize_doi(value):
    if not value:
        return None
    kind, normalized = identifier(str(value))
    if kind != "doi":
        raise WorkflowError("Provider returned a malformed DOI.")
    return normalized


def crossref_record(message):
    doi = normalize_doi(message["DOI"])
    links = []
    for entry in message.get("link", []):
        url = entry.get("URL")
        if entry.get("content-type") == "application/pdf" and isinstance(url, str) and url.startswith("https://"):
            if not any(link["url"] == url for link in links):
                links.append({"url": url, "source": "crossref_link", "availability": "unverified"})
    authors = [" ".join(filter(None, [a.get("given"), a.get("family")])) or a.get("name", "")
               for a in message.get("author", [])]
    return {"provider": "crossref", "provider_id": doi, "identifiers": {"doi": doi},
            "title": " ".join(message.get("title") or [doi]), "authors": [a for a in authors if a],
            "year": (message.get("issued", {}).get("date-parts") or [[None]])[0][0],
            "venue": "; ".join(message.get("container-title") or []),
            "abstract": re.sub(r"<[^>]*>", " ", message.get("abstract") or "").strip() or None,
            "landing_url": "https://doi.org/" + doi, "pdf_sources": links,
            "licenses": message.get("license", []), "publication_types": [message.get("type", "unknown")]}


def pubmed_records(raw):
    # The same parser serves the standalone NCBI skill and the installed sci package.
    from .ncbi_eutils.eutils_cli import parse_pubmed_xml_records
    result = []
    for record in parse_pubmed_xml_records(raw):
        pmid = record["pmid"]
        if not pmid or identifier("pmid:" + pmid) != ("pmid", pmid):
            raise WorkflowError("PubMed returned an invalid record identity.")
        ids = {"pmid": pmid}
        doi = normalize_doi(record["article_ids"].get("doi"))
        if doi:
            ids["doi"] = doi
        pmc = record["article_ids"].get("pmc")
        if pmc and re.fullmatch(r"PMC\d+", pmc):
            ids["pmcid"] = pmc
        result.append({"provider": "pubmed", "provider_id": pmid, "identifiers": ids,
                       "title": record["title"] or "PMID " + pmid, "authors": [
                           a.get("collective_name") or " ".join(filter(None, [a.get("fore_name") or a.get("initials"), a.get("last_name")]))
                           for a in record["authors"]], "year": record["publication_year"], "venue": record["journal"],
                       "abstract": record["abstract"], "landing_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                       "pdf_sources": [], "licenses": [], "publication_types": record["publication_types"]})
    return result


def retrieve(action, query, provider, limit, fetch):
    """One bounded search page, or an exact lookup. fetch persists each response."""
    if action == "lookup":
        kind, value = identifier(query)
        provider = "crossref" if kind == "doi" else "pubmed"
    if provider == "crossref":
        url = CROSSREF + ("/" + quote(value, safe="") if action == "lookup" else
                          "?" + urlencode({"query.bibliographic": query, "rows": limit, "sort": "relevance"}))
        payload = json.loads(fetch(url, "json"))
        if payload.get("status") != "ok":
            raise WorkflowError("Crossref returned an unsuccessful response.")
        message = payload["message"]
        records = [crossref_record(m) for m in ([message] if action == "lookup" else message["items"])]
        if action == "lookup" and (len(records) != 1 or records[0]["identifiers"].get("doi") != value):
            raise WorkflowError("DOI lookup returned a different work.")
        return records, {"total": 1 if action == "lookup" else message["total-results"], "sort": "relevance"}
    if provider != "pubmed":
        raise WorkflowError("Choose pubmed or crossref.")
    if action == "lookup":
        ids, metadata = [value], {"total": 1, "sort": "identifier"}
    else:
        params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json", "sort": "relevance", "tool": "scientific-tooling"}
        payload = json.loads(fetch(PUBMED + "esearch.fcgi?" + urlencode(params), "json"))
        search = payload["esearchresult"]
        if search.get("errorlist") or payload.get("error"):
            raise WorkflowError("PubMed reported query errors: " + str(search.get("errorlist") or payload.get("error")))
        ids = search["idlist"]
        metadata = {"total": int(search["count"]), "sort": "relevance", "query_translation": search.get("querytranslation"),
                    "warnings": search.get("warninglist", {})}
    if len(ids) > limit or len(set(ids)) != len(ids) or any(not re.fullmatch(r"[1-9]\d{0,8}", i) for i in ids):
        raise WorkflowError("PubMed returned an invalid or unbounded selection.")
    if not ids:
        return [], metadata
    params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "tool": "scientific-tooling"}
    records = pubmed_records(fetch(PUBMED + "efetch.fcgi?" + urlencode(params), "xml"))
    if len(records) != len(ids) or {r["provider_id"] for r in records} != set(ids):
        raise WorkflowError("PubMed record response is incomplete or does not match the selected IDs.")
    by_id = {r["provider_id"]: r for r in records}
    return [by_id[i] for i in ids], metadata
