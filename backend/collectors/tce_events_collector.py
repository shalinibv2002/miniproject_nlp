"""TCE Events page collector.

Fetches the public Events listing at https://www.tce.edu/events, extracts
title, date range, and detail URL for each item, and saves raw output to
data/raw/events/.
"""

import re
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.collectors.base_collector import BaseCollector, run_collector

DEFAULT_URL = "https://www.tce.edu/events"


class TCEEventsCollector(BaseCollector):
    source_registry_id = 1  # 'TCE Events' row in source_registry
    output_dir_name = "events"

    def collect(self, urls, max_items=None, with_details=False):
        if not with_details:
            return run_collector(self, urls, max_items=max_items)

        import logging

        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
        from backend.database.init_db import get_connection

        all_records = []
        conn = get_connection()
        try:
            for url in urls:
                try:
                    resp = self.fetch(url)
                    soup = self._parse(resp.text)
                    records = self.extract_items(soup)
                    if max_items:
                        records = records[:max_items]
                    enriched = []
                    for record in records:
                        try:
                            self._enrich_with_detail(record)
                        except Exception as exc:  # noqa: BLE001
                            logger.error("Detail fetch failed for %s: %s",
                                         record.get("url"), exc)
                            self.log_collection_error(conn, None, record.get("url"),
                                                      type(exc).__name__, str(exc),
                                                      stage="collect")
                        enriched.append(record)
                    self.save_raw(url, resp.text, enriched)
                    self.log_collection_run(
                        conn, url, pages_processed=1, raw_records=len(enriched),
                        saved_records=len(enriched), error_count=0, status="completed",
                        notes="with detail enrichment",
                    )
                    all_records.extend(enriched)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to collect %s: %s", url, exc)
                    self.log_collection_error(conn, None, url, type(exc).__name__, str(exc))
        finally:
            conn.close()
        return all_records

    def _enrich_with_detail(self, record):
        """Fetch the event detail page and extract description + dates."""
        detail_url = record.get("url")
        if not detail_url:
            return record
        resp = self.fetch(detail_url)
        soup = self._parse(resp.text)
        node = soup.select_one("article.node")
        if not node:
            node = soup

        h1 = node.select_one("h1, .page-title")
        if h1 and not record.get("title"):
            record["title"] = h1.get_text(strip=True)

        body = node.select_one(".field--name-body")
        if body:
            text_parts = []
            for p in body.select("p"):
                t = p.get_text(" ", strip=True)
                if t:
                    text_parts.append(t)
            if text_parts:
                record["description"] = " ".join(text_parts)

        schedule = node.select_one(".field--name-field-schedule")
        if schedule and not record.get("activity_date"):
            raw = schedule.get_text(" ", strip=True)
            if raw:
                start, _ = self._parse_date_range(raw)
                if start:
                    record["activity_date"] = start

        end_schedule = node.select_one(".field--name-field-end-schedule")
        if end_schedule and not record.get("activity_date_end"):
            raw = end_schedule.get_text(" ", strip=True)
            if raw:
                _, end = self._parse_date_range(raw)
                if end:
                    record["activity_date_end"] = end

        venue_el = node.select_one(".field--name-field-venue")
        if venue_el:
            record["venue"] = venue_el.get_text(" ", strip=True)
        return record

    @staticmethod
    def _parse_date_range(text):
        """Parse '17 Dec, 2026 - 18 Dec, 2026' into ISO dates."""
        text = text.strip()
        if not text:
            return None, None
        parts = re.split(r"\s*-\s*", text)
        dates = []
        for part in parts:
            part = part.strip()
            for fmt in ("%d %b, %Y", "%d %B, %Y", "%b %d, %Y", "%d-%m-%Y", "%Y-%m-%d"):
                try:
                    dates.append(datetime.strptime(part, fmt).strftime("%Y-%m-%d"))
                    break
                except ValueError:
                    continue
            else:
                dates.append(None)
        if not dates:
            return None, None
        start = dates[0]
        end = dates[-1] if len(dates) > 1 else None
        return start, end

    def extract_items(self, soup):
        records = []
        for block in soup.select("div.item-columns"):
            title_el = block.select_one(".views-field-title a")
            date_el = block.select_one(".views-field-nothing .field-content")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            href = title_el.get("href", "")
            url = f"https://www.tce.edu{href}" if href.startswith("/") else href
            date_text = date_el.get_text(strip=True) if date_el else ""
            start_date, end_date = self._parse_date_range(date_text)
            records.append({
                "title": title,
                "url": url,
                "date_text": date_text,
                "activity_date": start_date,
                "activity_date_end": end_date,
                "source": "TCE Events",
            })
        return records


if __name__ == "__main__":
    collector = TCEEventsCollector()
    # Kept for backward compatibility only. The normal collection entry point
    # is now tce_discovery_collector; do not impose an activity-record limit.
    collector.collect([DEFAULT_URL])
