"""Shared base class for all web collectors.

Handles request headers/User-Agent, delay between requests, retries on
failure, structured logging, and writing raw HTML/text to data/raw/.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests

from backend.config import (
    RAW_DATA_DIR,
    REQUEST_DELAY_SECONDS,
    REQUEST_RETRIES,
    REQUEST_TIMEOUT,
    REQUEST_USER_AGENT,
)
from backend.database.init_db import get_connection

logger = logging.getLogger("tce.collector")


class BaseCollector:
    """Base class for collectors. Subclass and implement extract_items()."""

    source_registry_id = None
    output_dir_name = "generic"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": REQUEST_USER_AGENT})
        self.last_request_time = 0.0
        self.output_dir = Path(RAW_DATA_DIR) / self.output_dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.last_fetch_attempts = 0

    def _respect_delay(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)
        self.last_request_time = time.time()

    def fetch(self, url):
        """Fetch a URL with retries and politeness delay."""
        last_error = None
        for attempt in range(1, REQUEST_RETRIES + 1):
            self._respect_delay()
            try:
                logger.info("Fetching %s (attempt %d)", url, attempt)
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                self.last_fetch_attempts = attempt
                return resp
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("Attempt %d failed for %s: %s", attempt, url, exc)
                time.sleep(1.0 * attempt)
        self.last_fetch_attempts = REQUEST_RETRIES
        raise last_error

    def save_raw(self, url, html, records, run_id=None, conn=None):
        """Save raw HTML and extracted records as timestamped JSON files."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_host = url.replace("https://", "").replace("http://", "").replace("/", "_")[:40]
        base_name = f"{ts}_{safe_host}"
        html_path = self.output_dir / f"{base_name}.html"
        records_path = self.output_dir / f"{base_name}.json"

        html_path.write_text(html, encoding="utf-8")
        payload = {
            "source_url": url,
            "collected_at": datetime.now().isoformat(),
            "raw_file": html_path.name,
            "records": records,
        }
        records_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved %d records -> %s", len(records), records_path)
        return records_path

    def log_collection_run(
        self,
        conn,
        url,
        pages_processed=1,
        raw_records=0,
        saved_records=0,
        error_count=0,
        status="completed",
        notes=None,
    ):
        cur = conn.execute(
            """INSERT INTO collection_runs
               (source_registry_id, started_at, finished_at, pages_processed,
                raw_records, saved_records, error_count, status, notes)
               VALUES (?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?)""",
            (self.source_registry_id, pages_processed, raw_records,
             saved_records, error_count, status, notes),
        )
        conn.commit()
        return cur.lastrowid

    def log_collection_error(
        self,
        conn,
        run_id,
        url,
        error_type,
        error_message,
        stage="collect",
        raw_record_id=None,
    ):
        conn.execute(
            """INSERT INTO collection_errors
               (collection_run_id, source_registry_id, url, stage,
                error_type, error_message, raw_record_id, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'open')""",
            (run_id, self.source_registry_id, url, stage,
             error_type, str(error_message)[:2000], raw_record_id),
        )
        conn.commit()

    def collect(self, urls, max_items=None):
        """Collect from a list/tuple of (url,) or strings. Returns records."""
        raise NotImplementedError("Subclasses must implement collect()")

    def _parse(self, html):
        from bs4 import BeautifulSoup

        return BeautifulSoup(html, "lxml")

    def extract_items(self, soup):
        """Extract a list of record dicts from a parsed page."""
        raise NotImplementedError("Subclasses must implement extract_items()")


def run_collector(collector, urls, conn=None, max_items=None):
    """Shared CLI runner for a collector instance."""
    import logging

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    own_conn = conn is None
    conn = conn or get_connection()
    all_records = []
    total_errors = 0
    try:
        for url in urls:
            run_id = None
            try:
                resp = collector.fetch(url)
                soup = collector._parse(resp.text)
                records = collector.extract_items(soup)
                if max_items:
                    records = records[:max_items]
                path = collector.save_raw(url, resp.text, records)
                collector.log_collection_run(
                    conn, url, pages_processed=1, raw_records=len(records),
                    saved_records=len(records), error_count=0, status="completed",
                    notes=f"raw file: {path.name}",
                )
                all_records.extend(records)
                for record in records:
                    record["_source_url"] = url
            except Exception as exc:  # noqa: BLE001
                total_errors += 1
                logger.error("Failed to collect %s: %s", url, exc)
                collector.log_collection_error(conn, None, url, type(exc).__name__, str(exc))
    finally:
        if own_conn:
            conn.close()
    return all_records
