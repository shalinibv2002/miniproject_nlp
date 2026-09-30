"""Targeted expansion collection for TCE department sub-pages (run_7).

Fetches an explicit allow-list of official department sub-page URLs, archives
each HTML + text under data/raw/discovery/run_7/, and registers one
raw_source_occurrence per page.  No link following: correctness of provenance
and politeness are the priorities here.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlsplit

from backend.collectors.base_collector import BaseCollector
from backend.collectors.tce_discovery_collector import (
    TCEDiscoveryCollector,
    is_internal_url,
    normalize_url,
    page_is_relevant,
)
from backend.config import RAW_DATA_DIR
from backend.database.init_db import get_connection, init_db

logger = logging.getLogger("tce.expansion")


class TCEDepartmentExpansionCollector(TCEDiscoveryCollector):
    """A shallow, explicit-URL department sub-page collector (run_7)."""

    output_dir_name = "discovery"

    def collect_explicit(self, urls, run_id=None):
        init_db()
        conn = get_connection()
        if run_id is None:
            run_id = self._create_run(conn, [normalize_url(u) for u in urls])
        stats = {k: 0 for k in ("pages_fetched", "pages_failed", "raw_source_records",
                                "relevant_pages", "retry_count")}
        for url in urls:
            norm = normalize_url(url)
            if not norm or not is_internal_url(norm, self.allowed_domains, self.allow_subdomains):
                stats["pages_failed"] += 1
                self._log_error(conn, run_id, url, ValueError("not an allowed internal URL"))
                continue
            try:
                if not self._robots_allowed(norm):
                    stats["pages_failed"] += 1
                    self._log_error(conn, run_id, norm, PermissionError("disallowed by robots.txt"))
                    continue
                response = self.fetch(norm)
                stats["retry_count"] += max(0, self.last_fetch_attempts - 1)
                stats["pages_fetched"] += 1
                soup = self._parse(response.text)
                title = soup.title.get_text(" ", strip=True) if soup.title else ""
                text = self._html_text(soup)
                relevant = page_is_relevant(norm, title, text)
                archive = self._archive(run_id, norm, response.text, ".html")
                text_archive = self._archive(run_id, norm, text, ".txt")
                self._store_occurrence(
                    conn, run_id, url=norm, referring_url=None, source_type="html",
                    title=title, status=response.status_code,
                    content_type=response.headers.get("Content-Type", "").lower(),
                    archive_path=archive, text_archive_path=text_archive,
                    extraction_status="raw_text_extracted",
                )
                stats["raw_source_records"] += 1
                stats["relevant_pages"] += int(relevant)
            except Exception as exc:  # keep going; no failure disappears
                stats["pages_failed"] += 1
                self._log_error(conn, run_id, url, exc)
        conn.execute(
            """UPDATE collection_runs SET finished_at=datetime('now'), pages_processed=?,
               raw_records=?, saved_records=?, error_count=?, status=?, notes=? WHERE id=?""",
            (stats["pages_fetched"], stats["raw_source_records"], stats["raw_source_records"],
             stats["pages_failed"], "partial" if stats["pages_failed"] else "completed",
             json.dumps(stats, sort_keys=True), run_id),
        )
        conn.commit()
        return {"run_id": run_id, **stats}


def main(url_file):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    urls = [line.strip() for line in Path(url_file).read_text(encoding="utf-8").splitlines() if line.strip()]
    collector = TCEDepartmentExpansionCollector()
    result = collector.collect_explicit(urls)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\mlwav\AppData\Local\Temp\opencode\dept_subpage_urls.txt")