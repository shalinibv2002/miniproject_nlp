"""Deterministic Step 2 tests; no test contacts the live TCE website."""

from pathlib import Path

import pytest
import requests

from backend.collectors.base_collector import BaseCollector
from backend.collectors.tce_discovery_collector import (
    TCEDiscoveryCollector, discover_links, is_internal_url, normalize_url,
    pagination_links,
)
from backend.database.init_db import get_connection, init_db


class Response:
    def __init__(self, url, text="", content=None, content_type="text/html", status=200):
        self.url = url
        self.text = text
        self.content = content if content is not None else text.encode("utf-8")
        self.status_code = status
        self.headers = {"Content-Type": content_type}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class Session:
    headers = {"User-Agent": "test-crawler"}

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def get(self, url, timeout):
        self.calls.append(url)
        value = self.pages[url]
        if isinstance(value, Exception):
            raise value
        value.raise_for_status()
        return value


@pytest.fixture
def crawl_db(tmp_path, monkeypatch):
    path = str(tmp_path / "crawl.db")
    init_db(path)
    import backend.collectors.tce_discovery_collector as module
    monkeypatch.setattr(module, "init_db", lambda: None)
    monkeypatch.setattr(module, "get_connection", lambda: get_connection(path))
    return path


def test_normalize_url_and_reject_external_domains():
    assert normalize_url("/events/?utm_source=x#top", "https://www.tce.edu/") == "https://www.tce.edu/events"
    assert normalize_url("https://www.tce.edu/a?b=2&a=1") == "https://www.tce.edu/a?a=1&b=2"
    assert is_internal_url("https://www.tce.edu/events")
    assert not is_internal_url("https://example.org/events")
    assert not is_internal_url("mailto:test@tce.edu")


def test_link_and_pagination_discovery():
    html = '''<a href="/events/one">Workshop</a><a href="https://example.org/x">outside</a>
              <a rel="next" href="/events?page=1">Next</a>'''
    links = discover_links(html, "https://www.tce.edu/events")
    assert ("https://www.tce.edu/events/one", "Workshop") in links
    assert all("example.org" not in url for url, _ in links)
    assert "https://www.tce.edu/events?page=1" in pagination_links(html, "https://www.tce.edu/events")


def test_raw_collection_discovers_detail_pdf_and_preserves_provenance(crawl_db, monkeypatch):
    root = "https://www.tce.edu/"
    detail = "https://www.tce.edu/events/workshop"
    pdf = "https://www.tce.edu/sites/default/files/newsletter.pdf"
    pages = {
        root: Response(root, '<title>TCE</title><a href="/events">Events</a><a href="/sites/default/files/newsletter.pdf">Newsletter</a>'),
        "https://www.tce.edu/events": Response("https://www.tce.edu/events", '<title>Events</title><a href="/events/workshop">Workshop</a><a href="?page=1">Next</a>'),
        detail: Response(detail, '<title>Workshop</title><p>Faculty workshop activity</p>'),
        "https://www.tce.edu/events?page=1": Response("https://www.tce.edu/events?page=1", '<title>Archive</title><p>Achievement archive</p>'),
        pdf: Response(pdf, content=b"%PDF fake", content_type="application/pdf"),
    }
    collector = TCEDiscoveryCollector(max_pages=10, max_depth=2, session=Session(pages))
    monkeypatch.setattr(collector, "_robots_allowed", lambda url: True)
    monkeypatch.setattr(collector, "_extract_pdf_text", lambda data: ("Newsletter workshop report", None))
    result = collector.collect([root])
    assert result["pages_successfully_processed"] == 4
    assert result["pdfs_processed"] == 1
    assert result["raw_source_records"] == 5
    conn = get_connection(crawl_db)
    try:
        rows = conn.execute("SELECT normalized_url, referring_url, source_type, archive_path, text_archive_path FROM raw_source_occurrences").fetchall()
        assert len(rows) == 5
        pdf_row = next(r for r in rows if r["source_type"] == "pdf")
        assert pdf_row["referring_url"] == root
        assert pdf_row["archive_path"] and pdf_row["text_archive_path"]
    finally:
        conn.close()


def test_duplicate_urls_and_safety_limit_are_logged(crawl_db, monkeypatch):
    root = "https://www.tce.edu/"
    pages = {root: Response(root, '<a href="/events">Events</a><a href="/events/">Events duplicate</a>'),
             "https://www.tce.edu/events": Response("https://www.tce.edu/events", '<p>events</p>')}
    collector = TCEDiscoveryCollector(max_pages=1, max_depth=2, session=Session(pages))
    monkeypatch.setattr(collector, "_robots_allowed", lambda url: True)
    result = collector.collect([root])
    assert result["safety_limit_reached"] == 1
    # discover_links normalizes/deduplicates before queueing, so the duplicate
    # never becomes a second fetch candidate.
    assert result["pages_discovered"] == 2
    assert result["pages_fetched"] == 1
    assert result["urls_queued"] == 2
    assert result["unique_canonical_urls_discovered"] == 2


def test_http_failure_and_pdf_failure_are_persisted(crawl_db, monkeypatch):
    root = "https://www.tce.edu/"
    broken = "https://www.tce.edu/broken"
    pdf = "https://www.tce.edu/a.pdf"
    pages = {root: Response(root, '<a href="/broken">Workshop</a><a href="/a.pdf">Report</a>'),
             broken: requests.Timeout("slow"), pdf: Response(pdf, content=b"not a PDF", content_type="application/pdf")}
    collector = TCEDiscoveryCollector(max_pages=5, session=Session(pages))
    monkeypatch.setattr(collector, "_robots_allowed", lambda url: True)
    monkeypatch.setattr(collector, "_extract_pdf_text", lambda data: (None, ValueError("bad PDF")))
    result = collector.collect([root])
    assert result["pages_failed"] == 1 and result["pdfs_failed"] == 1
    conn = get_connection(crawl_db)
    try:
        assert conn.execute("SELECT COUNT(*) FROM collection_errors").fetchone()[0] == 2
    finally:
        conn.close()


def test_base_fetch_retries_temporary_failure(monkeypatch):
    collector = BaseCollector()
    calls = {"n": 0}
    def get(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] < 3:
            raise requests.Timeout("temporary")
        return Response("https://www.tce.edu/")
    collector.session.get = get
    monkeypatch.setattr("backend.collectors.base_collector.time.sleep", lambda *_: None)
    response = collector.fetch("https://www.tce.edu/")
    assert response.status_code == 200 and calls["n"] == 3
