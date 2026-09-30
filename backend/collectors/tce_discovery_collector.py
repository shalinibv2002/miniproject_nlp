"""Bounded, robots-aware raw-source discovery for public TCE content.

This module intentionally stops before activity extraction: one page or PDF is
one *source occurrence*, not one institutional activity.
"""

import hashlib
import json
import logging
import os
import re
from collections import deque
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, quote, unquote, urlencode, urljoin, urlsplit, urlunsplit
from urllib import robotparser

from bs4 import BeautifulSoup

from backend.collectors.base_collector import BaseCollector
from backend.config import (
    CRAWL_ALLOWED_DOMAINS, CRAWL_ALLOW_SUBDOMAINS, CRAWL_ENABLE_PAGINATION,
    CRAWL_ENABLE_PDFS, CRAWL_MAX_DEPTH, CRAWL_MAX_PAGES, RAW_DATA_DIR,
)
from backend.database.init_db import get_connection, init_db

logger = logging.getLogger("tce.discovery")

# Verified official URLs retained from the prior archived discovery run.
DEFAULT_SEEDS = (
    "https://www.tce.edu/", "https://www.tce.edu/events",
    "https://www.tce.edu/index.php/student/physical-education/activities",
    "https://www.tce.edu/student/ncc", "https://www.tce.edu/campuslife/nss",
    "https://www.tce.edu/alumni/alumni-activities", "https://www.tce.edu/industry/iic",
    "https://www.tce.edu/wdc", "https://www.tce.edu/academics/departments",
    "https://www.tce.edu/research",
)
PDF_SUFFIXES = (".pdf",)
TRACKING_QUERY_KEYS = {"fbclid", "gclid", "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}
RELEVANCE_TERMS = (
    "event", "activit", "achievement", "award", "workshop", "seminar", "fdp", "training",
    "sport", "ncc", "nss", "club", "association", "cultural", "student", "faculty",
    "research", "placement", "competition", "outreach", "extension", "innovation", "mou",
    "collaboration", "newsletter", "report", "department",
)
STATIC_PATH_TERMS = ("contact", "privacy", "fee", "hostel", "rules", "login", "captcha")


def normalize_url(url, base_url=None):
    """Return stable HTTP(S) URL; strip fragments and known tracking params."""
    if not url:
        return None
    absolute = urljoin(base_url, url) if base_url else url
    parts = urlsplit(absolute)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        return None
    path = quote(unquote(parts.path or "/"), safe="/%:@")
    if path != "/":
        path = path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if k.lower() not in TRACKING_QUERY_KEYS]
    query.sort()
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query, doseq=True), ""))


def is_internal_url(url, allowed_domains=CRAWL_ALLOWED_DOMAINS, allow_subdomains=CRAWL_ALLOW_SUBDOMAINS):
    if not url:
        return False
    host = urlsplit(url).hostname or ""
    host = host.lower()
    for domain in allowed_domains:
        domain = domain.lower().lstrip(".")
        if host == domain or host == f"www.{domain}":
            return True
        if allow_subdomains and host.endswith("." + domain):
            return True
    return False


def is_pdf_url(url):
    return bool(urlsplit(url).path.lower().endswith(PDF_SUFFIXES))


def discover_links(html, base_url, allowed_domains=CRAWL_ALLOWED_DOMAINS, allow_subdomains=CRAWL_ALLOW_SUBDOMAINS):
    """Yield unique internal links as URL, anchor text pairs without fetching."""
    soup = BeautifulSoup(html, "lxml")
    found, seen = [], set()
    for anchor in soup.select("a[href]"):
        normalized = normalize_url(anchor.get("href"), base_url)
        if normalized and is_internal_url(normalized, allowed_domains, allow_subdomains) and normalized not in seen:
            seen.add(normalized)
            found.append((normalized, anchor.get_text(" ", strip=True)))
    return found


def page_is_relevant(url, title, text, anchor_text=""):
    haystack = " ".join((url, title or "", text or "", anchor_text or "")).lower()
    path = urlsplit(url).path.lower()
    if any(term in path for term in STATIC_PATH_TERMS) and not any(term in haystack for term in RELEVANCE_TERMS):
        return False
    return any(term in haystack for term in RELEVANCE_TERMS)


def pagination_links(html, base_url):
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a[href]"):
        label = a.get_text(" ", strip=True).lower()
        rel = " ".join(a.get("rel", [])).lower()
        href = normalize_url(a.get("href"), base_url)
        if href and ("next" in label or label.isdigit() or "next" in rel or "page=" in href):
            links.append(href)
    return links


class TCEDiscoveryCollector(BaseCollector):
    """Crawl bounded official TCE pages and archive raw source occurrences."""

    output_dir_name = "discovery"

    def __init__(self, *, allowed_domains=CRAWL_ALLOWED_DOMAINS,
                 allow_subdomains=CRAWL_ALLOW_SUBDOMAINS, max_pages=CRAWL_MAX_PAGES,
                 max_depth=CRAWL_MAX_DEPTH, enable_pdfs=CRAWL_ENABLE_PDFS,
                 enable_pagination=CRAWL_ENABLE_PAGINATION, session=None):
        super().__init__()
        self.allowed_domains = tuple(allowed_domains)
        self.allow_subdomains = allow_subdomains
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.enable_pdfs = enable_pdfs
        self.enable_pagination = enable_pagination
        if session is not None:
            self.session = session
        self._robots = {}

    def _robots_allowed(self, url):
        root = f"{urlsplit(url).scheme}://{urlsplit(url).netloc}"
        if root not in self._robots:
            rp = robotparser.RobotFileParser()
            rp.set_url(root + "/robots.txt")
            try:
                rp.read()
            except Exception as exc:  # fail closed for an unknown policy
                logger.warning("Could not read robots.txt for %s: %s", root, exc)
                self._robots[root] = None
            else:
                self._robots[root] = rp
        rp = self._robots[root]
        return bool(rp and rp.can_fetch(self.session.headers.get("User-Agent", "*"), url))

    @staticmethod
    def _html_text(soup):
        for node in soup(["script", "style", "noscript"]):
            node.decompose()
        return soup.get_text(" ", strip=True)

    @staticmethod
    def _section(url):
        parts = [p for p in urlsplit(url).path.split("/") if p]
        return parts[0] if parts else "home"

    def _archive(self, run_id, url, data, suffix):
        folder = Path(RAW_DATA_DIR) / self.output_dir_name / f"run_{run_id}"
        folder.mkdir(parents=True, exist_ok=True)
        token = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        path = folder / f"{token}{suffix}"
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_text(data, encoding="utf-8")
        return str(path.relative_to(Path(RAW_DATA_DIR)))

    def _create_run(self, conn, seeds):
        cur = conn.execute(
            "INSERT INTO collection_runs (started_at, status, notes) VALUES (datetime('now'), 'running', ?)",
            ("TCE-wide raw discovery",),
        )
        run_id = cur.lastrowid
        conn.execute("INSERT INTO collection_run_details (collection_run_id, seed_urls_json) VALUES (?, ?)",
                     (run_id, json.dumps(seeds)))
        conn.commit()
        return run_id

    def _finish_run(self, conn, run_id, stats, status="completed"):
        conn.execute(
            """UPDATE collection_runs SET finished_at=datetime('now'), pages_processed=?, raw_records=?,
               saved_records=?, error_count=?, status=?, notes=? WHERE id=?""",
            (stats["pages_successfully_processed"], stats["raw_source_records"], stats["raw_source_records"],
             stats["pages_failed"] + stats["pdfs_failed"], status, json.dumps(stats, sort_keys=True), run_id),
        )
        keys = ("pages_discovered", "pages_fetched", "pages_successfully_processed", "pages_failed",
                "relevant_pages", "pdfs_discovered", "pdfs_processed", "pdfs_failed",
                "duplicate_urls_skipped", "retry_count", "parser_errors", "safety_limit_reached")
        conn.execute("UPDATE collection_run_details SET " + ", ".join(f"{k}=?" for k in keys) +
                     " WHERE collection_run_id=?", [stats[k] for k in keys] + [run_id])
        conn.commit()

    def _log_error(self, conn, run_id, url, exc, stage="collect"):
        self.log_collection_error(conn, run_id, url, type(exc).__name__, str(exc), stage=stage)

    def _store_occurrence(self, conn, run_id, *, url, referring_url, source_type, title=None,
                          status=None, content_type=None, archive_path=None, text_archive_path=None,
                          extraction_status="not_attempted", extraction_error=None):
        conn.execute(
            """INSERT OR IGNORE INTO raw_source_occurrences
               (collection_run_id, source_url, normalized_url, referring_url, source_type, page_title,
                source_section, http_status, content_type, archive_path, text_archive_path, extraction_status, extraction_error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, url, normalize_url(url), referring_url, source_type, title, self._section(url),
             status, content_type, archive_path, text_archive_path, extraction_status, extraction_error),
        )
        conn.commit()

    def _extract_pdf_text(self, data):
        try:
            from pypdf import PdfReader
            from io import BytesIO
            reader = PdfReader(BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages), None
        except Exception as exc:  # preserves raw PDF and records the exact failure
            return None, exc

    def collect(self, seeds=None):
        """Run a raw-only crawl and return telemetry, not activity records."""
        seeds = seeds or DEFAULT_SEEDS
        normalized_seeds = [normalize_url(s) for s in seeds]
        normalized_seeds = [s for s in normalized_seeds if s and is_internal_url(s, self.allowed_domains, self.allow_subdomains)]
        if not normalized_seeds:
            raise ValueError("no allowed seed URLs")

        init_db()  # applies additive CREATE IF NOT EXISTS tables for existing DBs
        conn = get_connection()
        stats = {k: 0 for k in ("pages_discovered", "unique_canonical_urls_discovered", "links_discovered",
                                 "urls_queued", "urls_skipped_or_excluded", "pages_fetched",
                                 "pages_successfully_processed", "pages_failed", "relevant_pages", "pdfs_discovered",
                                 "pdfs_processed", "pdfs_failed", "raw_source_records", "duplicate_urls_skipped",
                                 "retry_count", "parser_errors", "safety_limit_reached")}
        run_id = self._create_run(conn, normalized_seeds)
        # `discovered` is separate from `visited`: URLs are deduplicated before
        # entering the queue, so telemetry means unique URLs rather than links.
        discovered = set(normalized_seeds)
        queue, visited = deque((s, None, 0, "") for s in normalized_seeds), set()
        stats["pages_discovered"] = len(discovered)
        stats["unique_canonical_urls_discovered"] = len(discovered)
        stats["urls_queued"] = len(discovered)
        try:
            while queue and stats["pages_fetched"] < self.max_pages:
                url, referrer, depth, anchor = queue.popleft()
                if url in visited:
                    stats["duplicate_urls_skipped"] += 1
                    continue
                visited.add(url)
                if not self._robots_allowed(url):
                    stats["urls_skipped_or_excluded"] += 1
                    self._log_error(conn, run_id, url, PermissionError("disallowed by robots.txt"))
                    continue
                try:
                    response = self.fetch(url)
                    stats["retry_count"] += max(0, self.last_fetch_attempts - 1)
                    stats["pages_fetched"] += 1
                    content_type = response.headers.get("Content-Type", "").lower()
                    is_pdf = is_pdf_url(url) or "application/pdf" in content_type
                    if is_pdf:
                        stats["pdfs_discovered"] += 1
                        if not self.enable_pdfs:
                            continue
                        archive = self._archive(run_id, url, response.content, ".pdf")
                        text, error = self._extract_pdf_text(response.content)
                        text_archive = self._archive(run_id, url, text, ".txt") if text is not None else None
                        self._store_occurrence(conn, run_id, url=url, referring_url=referrer, source_type="pdf",
                                               title=Path(urlsplit(url).path).name, status=response.status_code,
                                               content_type=content_type, archive_path=archive, text_archive_path=text_archive,
                                               extraction_status="extracted" if error is None else "failed",
                                               extraction_error=str(error)[:2000] if error else None)
                        stats["raw_source_records"] += 1
                        if error:
                            stats["pdfs_failed"] += 1
                            self._log_error(conn, run_id, url, error, stage="extract")
                        else:
                            stats["pdfs_processed"] += 1
                        continue

                    soup = BeautifulSoup(response.text, "lxml")
                    title = soup.title.get_text(" ", strip=True) if soup.title else ""
                    text = self._html_text(soup)
                    relevant = page_is_relevant(url, title, text, anchor)
                    archive = self._archive(run_id, url, response.text, ".html")
                    text_archive = self._archive(run_id, url, text, ".txt")
                    self._store_occurrence(conn, run_id, url=url, referring_url=referrer, source_type="html",
                                           title=title, status=response.status_code, content_type=content_type,
                                           archive_path=archive, text_archive_path=text_archive,
                                           extraction_status="raw_text_extracted")
                    stats["raw_source_records"] += 1
                    stats["pages_successfully_processed"] += 1
                    stats["relevant_pages"] += int(relevant)
                    if depth >= self.max_depth:
                        continue
                    raw_link_count = len(BeautifulSoup(response.text, "lxml").select("a[href]"))
                    links = discover_links(response.text, url, self.allowed_domains, self.allow_subdomains)
                    stats["links_discovered"] += raw_link_count
                    stats["urls_skipped_or_excluded"] += raw_link_count - len(links)
                    pagination = set(pagination_links(response.text, url)) if self.enable_pagination else set()
                    for child, label in links:
                        if is_pdf_url(child) and not self.enable_pdfs:
                            continue
                        child_relevant = page_is_relevant(child, "", "", label)
                        # Navigate section menus at shallow depth, then retain activity/pagination branches.
                        if child in discovered:
                            stats["duplicate_urls_skipped"] += 1
                            continue
                        if child not in visited and (depth < 1 or child_relevant or child in pagination or is_pdf_url(child)):
                            discovered.add(child)
                            queue.append((child, url, depth + 1, label))
                            stats["pages_discovered"] = len(discovered)
                            stats["unique_canonical_urls_discovered"] = len(discovered)
                            stats["urls_queued"] += 1
                        else:
                            stats["urls_skipped_or_excluded"] += 1
                except Exception as exc:  # no failure disappears from telemetry
                    stats["pages_failed"] += 1
                    self._log_error(conn, run_id, url, exc)
            if queue:
                stats["safety_limit_reached"] = 1
            self._finish_run(conn, run_id, stats, "partial" if stats["safety_limit_reached"] else "completed")
            return {"run_id": run_id, "seed_urls": normalized_seeds, **stats}
        except Exception:
            self._finish_run(conn, run_id, stats, "failed")
            raise
        finally:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    print(json.dumps(TCEDiscoveryCollector().collect(), indent=2))
