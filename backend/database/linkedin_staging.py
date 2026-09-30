"""LinkedIn staging: load raw TCE LinkedIn posts from ``merged-workbook.xlsx``
into a separate SQLite staging database.  This is a dedicated staging source
ONLY — nothing here reads, writes, or modifies the institutional activity
database (``tce_activity_intelligence.db``).

Canonical, deduplicated posts live in ``linkedin_posts``; every raw occurrence
(row in the workbook) is preserved for audit in ``linkedin_post_occurrences``.
The Excel workbook itself is never modified.

Dedup rules applied (only inside this staging dataset):
  1. Same LinkedIn activity URL  -> keep one canonical post.
  2. URL-less posts -> normalize text; exact-equality groups then near-exact
     (rapidfuzz WRatio >= 95) groups collapse to a single post.
  3. A URL-less post whose normalized text exactly matches a URL-based post
     is associated with that existing record (new row is NOT created).
  4. ``source_sheet`` / ``source_row`` of every occurrence are preserved.
"""

import os
import re
import sqlite3
from datetime import datetime

import pandas as pd
from rapidfuzz import fuzz

from backend.database import cleaner, normalizer

WORKBOOK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "merged-workbook.xlsx")
STAGING_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "linkedin_staging.db")

ACTIVITY_PATTERN = re.compile(r"activity[:\-/?=_]*(\d+)")

# Near-exact text threshold, aligned with the project's fuzzy-dedup sensitivity.
NEAR_DUP_WRATIO = 95.0
NEAR_DUP_LENGTH_RATIO = 0.80

STAGING_SCHEMA = """
CREATE TABLE IF NOT EXISTS linkedin_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_url TEXT,                              -- LinkedIn activity URL (NULL for unmatched URL-less posts)
    activity_id TEXT,                           -- numeric id from urn:li:activity:<id>
    post_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    resolved_via TEXT,                          -- 'url' | 'text_exact' | 'text_near' | NULL
    source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    collected_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_linkedin_posts_url
    ON linkedin_posts(post_url) WHERE post_url IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_linkedin_posts_activity
    ON linkedin_posts(activity_id) WHERE activity_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS linkedin_post_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linkedin_post_id INTEGER REFERENCES linkedin_posts(id),
    source_sheet TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    post_url TEXT,
    post_text TEXT,
    normalized_text TEXT,
    duplicate_flag INTEGER NOT NULL DEFAULT 0 CHECK (duplicate_flag IN (0, 1)),
    duplicate_reason TEXT,  -- 'unique' | 'duplicate_url' | 'duplicate_text_exact'
                            -- | 'duplicate_text_near' | 'url_match_resolved'
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_linkedin_occurrences_post
    ON linkedin_post_occurrences(linkedin_post_id);
"""


def get_staging_connection(db_path=None):
    """Open a connection to the dedicated LinkedIn staging database only."""
    path = db_path or STAGING_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def extract_activity_id(post_url):
    if not post_url:
        return None
    m = ACTIVITY_PATTERN.search(post_url)
    return m.group(1) if m else None


def normalize_post_text(text):
    """Normalized text used for exact/near-exact URL-less dedup."""
    return normalizer.to_normalized_title(text or "")


def read_sheet_rows(workbook, sheet_name):
    """Return workbook rows for a sheet as (row_index, text, url) dicts.

    Handles the workbook quirks found during inspection:
      - sheets whose first row is a real post (no 'Post title' header)
      - sheets with a stray title row before the real 'Post title'/'Post link'
        header
    """
    raw = pd.read_excel(workbook, sheet_name=sheet_name, header=None,
                        dtype=str, keep_default_na=False)
    header_row = None
    for i in range(min(3, len(raw))):
        v = raw.iloc[i, 0]
        if isinstance(v, str) and v.strip() == "Post title":
            header_row = i
            break
    data_start = 0 if header_row is None else header_row + 1

    result = []
    for i in range(data_start, len(raw)):
        row = raw.iloc[i].tolist()
        if all(str(v).strip() == "" for v in row):
            continue
        text = str(row[0]).strip()
        url = ""
        for v in row[1:]:
            if isinstance(v, str) and v.strip().lower().startswith("http"):
                url = v.strip()
                break
        if not text and not url:
            continue
        result.append({"sheet": sheet_name, "row": i, "text": text, "url": url})
    return result


def read_all_sheets(workbook):
    xl = pd.ExcelFile(workbook)
    records = []
    for sheet in xl.sheet_names:
        records.extend(read_sheet_rows(workbook, sheet))
    return records


def extract_dates(text):
    """All explicit YYYY-MM-DD dates found in a post text (2000..2030 guard)."""
    if not text:
        return []
    found = set()
    for fmt, pattern in cleaner.DATE_PATTERNS:
        for m in pattern.finditer(str(text)):
            parts = m.groups()
            try:
                if fmt == "%Y-%m-%d":
                    dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                elif fmt in ("%d %b %Y", "%d %B %Y"):
                    month = cleaner.month_to_num(parts[1])
                    if not month:
                        continue
                    dt = datetime(int(parts[2]), month, int(parts[0]))
                elif fmt == "%b %d, %Y":
                    month = cleaner.month_to_num(parts[0])
                    if not month:
                        continue
                    dt = datetime(int(parts[2]), month, int(parts[1]))
                else:
                    dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            except (ValueError, TypeError, IndexError):
                continue
            if 2000 <= dt.year <= 2030:
                found.add(dt.strftime("%Y-%m-%d"))
    return sorted(found)


def _longest(first, second):
    """Deterministic 'keep this one' choice: longer text wins, else earlier."""
    if len(first["text"]) != len(second["text"]):
        return first if len(first["text"]) > len(second["text"]) else second
    order = {"April 2024 - June 2025": 0, "June 2025-June 2026": 1,
             "Jan - Sep 2025": 2, "May - June 2026": 3, "Sep to Dec 2025": 4}
    o1 = (order.get(first["sheet"], 99), first["row"])
    o2 = (order.get(second["sheet"], 99), second["row"])
    return first if o1 <= o2 else second


def _insert_post(cursor, url, text, norm, resolved_via, rec):
    aid = extract_activity_id(url) if url else None
    cursor.execute(
        """INSERT INTO linkedin_posts
           (post_url, activity_id, post_text, normalized_text, resolved_via,
            source_sheet, source_row)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (url or None, aid, text, norm, resolved_via, rec["sheet"], rec["row"]),
    )
    return cursor.lastrowid


def _insert_occurrence(cursor, pid, rec, reason, dup_flag, url=None):
    cursor.execute(
        """INSERT INTO linkedin_post_occurrences
           (linkedin_post_id, source_sheet, source_row, post_url, post_text,
            normalized_text, duplicate_flag, duplicate_reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (pid, rec["sheet"], rec["row"], url or None, rec["text"],
         normalize_post_text(rec["text"]), dup_flag, reason),
    )


def _load(conn, workbook):
    cursor = conn.cursor()
    all_recs = read_all_sheets(workbook)
    url_recs = [r for r in all_recs if r["url"]]
    url_less = [r for r in all_recs if not r["url"]]

    # ---- Phase 1: URL-based posts -----------------------------------------
    url_by_key = {}          # activity_id or url -> chosen record
    url_dup_records = []     # chosen records that lost to a longer-text twin
    for rec in url_recs:
        aid = extract_activity_id(rec["url"])
        key = aid or rec["url"]
        if key in url_by_key:
            keep = _longest(url_by_key[key], rec)
            if keep is rec:
                url_dup_records.append(url_by_key[key])
                url_by_key[key] = rec
            else:
                url_dup_records.append(rec)
        else:
            url_by_key[key] = rec

    url_post_id = {}         # canonical linkedin_posts.id by url key
    url_norm_index = {}      # normalized_text -> first canonical id (URL posts)
    for key, rec in url_by_key.items():
        norm = normalize_post_text(rec["text"])
        pid = _insert_post(cursor, rec["url"], rec["text"], norm, "url", rec)
        url_post_id[key] = pid
        if norm and norm not in url_norm_index:
            url_norm_index[norm] = pid

    for rec in url_recs:
        aid = extract_activity_id(rec["url"])
        key = aid or rec["url"]
        canonical = url_by_key[key]
        if rec is canonical:
            reason, dup = "unique", 0
        else:
            reason, dup = "duplicate_url", 1
        _insert_occurrence(cursor, url_post_id[key], rec, reason, dup, url=rec["url"])

    # ---- Phase 2: URL-less posts ------------------------------------------
    form_stats = {"url_post_count": len(url_by_key), "url_dup_records": len(url_dup_records),
                  "url_less_total": len(url_less)}

    # 2a. exact match to an existing URL post -> associate, no new row
    for rec in url_less:
        norm = normalize_post_text(rec["text"])
        if norm and norm in url_norm_index:
            _insert_occurrence(cursor, url_norm_index[norm], rec, "url_match_resolved", 0)

    # 2b. exact text groups among the remaining URL-less posts
    url_less_remaining = [
        r for r in url_less
        if (n := normalize_post_text(r["text"])) and n not in url_norm_index
    ]
    text_groups = {}
    text_order = []
    for rec in url_less_remaining:
        norm = normalize_post_text(rec["text"])
        if norm not in text_groups:
            text_groups[norm] = []
            text_order.append(norm)
        text_groups[norm].append(rec)

    representatives = []
    for norm in text_order:
        group = text_groups[norm]
        chosen = group[0]
        for other in group[1:]:
            chosen = _longest(chosen, other)
        representatives.append({"norm": norm, "chosen": chosen, "group": group})

    # 2c. near-exact grouping across representatives (WRatio >= 95).
    # Each merged rep collapses into one specific lower-index (non-merged) rep.
    merged_into = {}       # rep index -> partner rep index (lower, non-merged)
    merged = set()         # rep indices that collapse
    for i in range(len(representatives)):
        if i in merged:
            continue
        for j in range(i + 1, len(representatives)):
            if j in merged:
                continue
            a, b = representatives[i]["norm"], representatives[j]["norm"]
            if not a or not b:
                continue
            len_ratio = min(len(a), len(b)) / max(len(a), len(b))
            if len_ratio >= NEAR_DUP_LENGTH_RATIO and fuzz.WRatio(a, b) >= NEAR_DUP_WRATIO:
                merged.add(j)
                merged_into[j] = i

    # canonical owner for every rep index
    owner_rep = {}         # rep index -> rep index that provides the kept post
    for i in range(len(representatives)):
        owner_rep[i] = merged_into.get(i, i)

    # owner posts that absorbed a near-exact merge (label them 'text_near')
    absorbed_near = set()
    for j, i in merged_into.items():
        absorbed_near.add(i)

    # insert each canonical owner post once; resolved_via reflects merging kind
    owner_pid = {}         # id(owner record) -> linkedin_posts.id
    for i, rep in enumerate(representatives):
        owner = representatives[owner_rep[i]]["chosen"]
        oid = id(owner)
        if oid in owner_pid:
            continue
        if owner_rep[i] == i and i not in absorbed_near:
            resolved = "text_exact" if len(rep["group"]) > 1 else None
        else:
            resolved = "text_near"
        owner_pid[oid] = _insert_post(
            cursor, None, owner["text"], normalize_post_text(owner["text"]),
            resolved, owner)

    # record every URL-less occurrence mapped to its canonical post
    for i, rep in enumerate(representatives):
        owner = representatives[owner_rep[i]]["chosen"]
        pid = owner_pid[id(owner)]
        for rec in rep["group"]:
            if rec is owner:
                _insert_occurrence(cursor, pid, rec, "unique", 0)
            elif owner_rep[i] != i:
                _insert_occurrence(cursor, pid, rec, "duplicate_text_near", 1)
            else:
                _insert_occurrence(cursor, pid, rec, "duplicate_text_exact", 1)

    conn.commit()
    return form_stats


def init_staging_schema(conn):
    conn.executescript(STAGING_SCHEMA)
    conn.commit()


def _count(conn, sql, params=()):
    return conn.execute(sql, params).fetchone()[0]


def build_report(conn):
    stats = {}
    stats["total_raw"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences")
    stats["with_url"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences WHERE post_url IS NOT NULL AND post_url != ''")
    stats["without_url"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences WHERE post_url IS NULL OR post_url = ''")
    stats["unique_urls"] = _count(conn, "SELECT COUNT(DISTINCT post_url) FROM linkedin_post_occurrences WHERE post_url IS NOT NULL AND post_url != ''")
    stats["unique_activity_ids"] = _count(conn, "SELECT COUNT(DISTINCT activity_id) FROM linkedin_posts WHERE activity_id IS NOT NULL")
    stats["dup_urls_removed"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences WHERE duplicate_reason='duplicate_url'")
    stats["dup_texts_removed"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences WHERE duplicate_reason IN ('duplicate_text_exact','duplicate_text_near')")
    stats["url_less_matched_to_url"] = _count(conn, "SELECT COUNT(*) FROM linkedin_post_occurrences WHERE duplicate_reason='url_match_resolved'")
    stats["final_unique_posts"] = _count(conn, "SELECT COUNT(*) FROM linkedin_posts")

    rows = conn.execute("SELECT post_text FROM linkedin_posts").fetchall()
    all_dates = []
    post_years = {}
    for i, r in enumerate(rows):
        dates = extract_dates(r["post_text"])
        all_dates.extend(dates)
        years = {d[:4] for d in dates}
        if years:
            post_years[i] = years
    stats["posts_with_dates"] = len(post_years)
    stats["posts_without_dates"] = len(rows) - len(post_years)
    stats["earliest_post"] = min(all_dates) if all_dates else None
    stats["latest_post"] = max(all_dates) if all_dates else None
    year_counter = {}
    for years in post_years.values():
        for y in years:
            year_counter[y] = year_counter.get(y, 0) + 1
    stats["posts_per_year"] = {y: year_counter[y] for y in sorted(year_counter)}

    stats["posts_per_sheet"] = {
        r["source_sheet"]: r["n"]
        for r in conn.execute(
            "SELECT source_sheet, COUNT(*) AS n FROM linkedin_posts GROUP BY source_sheet ORDER BY source_sheet"
        ).fetchall()
    }
    stats["occurrences_per_sheet"] = {
        r["source_sheet"]: r["n"]
        for r in conn.execute(
            "SELECT source_sheet, COUNT(*) AS n FROM linkedin_post_occurrences GROUP BY source_sheet ORDER BY source_sheet"
        ).fetchall()
    }
    return stats


def load_staging(workbook=WORKBOOK_PATH, db_path=STAGING_DB_PATH, recreate=False):
    conn = get_staging_connection(db_path)
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='linkedin_posts'"
        ).fetchone() is not None
        if exists:
            n = _count(conn, "SELECT COUNT(*) FROM linkedin_posts")
            if n and not recreate:
                raise RuntimeError(
                    f"staging database already contains {n} posts at {db_path}; "
                    "pass recreate=True to reload from the workbook.")
            if recreate:
                conn.execute("DROP TABLE IF EXISTS linkedin_post_occurrences")
                conn.execute("DROP TABLE IF EXISTS linkedin_posts")
                conn.commit()
        if not exists or recreate:
            init_staging_schema(conn)
        _load(conn, workbook)
        return build_report(conn)
    finally:
        conn.close()


def print_report(stats):
    print("LINKEDIN STAGING REPORT")
    print("-" * 46)
    print("total raw rows loaded:            %d" % stats["total_raw"])
    print("rows with URL:                    %d" % stats["with_url"])
    print("rows without URL:                 %d" % stats["without_url"])
    print("unique URLs (raw rows):           %d" % stats["unique_urls"])
    print("unique activity IDs:              %d" % stats["unique_activity_ids"])
    print("duplicate URLs removed:           %d" % stats["dup_urls_removed"])
    print("duplicate TEXT rows removed:      %d" % stats["dup_texts_removed"])
    print("URL-less posts matched to URL:    %d" % stats["url_less_matched_to_url"])
    print("FINAL unique LinkedIn posts:      %d" % stats["final_unique_posts"])
    print()
    print("posts with explicit date in text: %d" % stats["posts_with_dates"])
    print("posts without explicit date:      %d" % stats["posts_without_dates"])
    print("earliest post date (from text):   %s" % stats["earliest_post"])
    print("latest post date (from text):     %s" % stats["latest_post"])
    print("posts per year (from text):       %s" % stats["posts_per_year"])
    print()
    print("posts per source sheet (canonical):")
    for s, n in stats["posts_per_sheet"].items():
        print("   %-25s %d" % (s, n))
    print("occurrences per source sheet (all rows):")
    for s, n in stats["occurrences_per_sheet"].items():
        print("   %-25s %d" % (s, n))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load LinkedIn staging data (read-only wrt main DB).")
    parser.add_argument("--workbook", default=WORKBOOK_PATH)
    parser.add_argument("--db", default=STAGING_DB_PATH)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    report = load_staging(workbook=args.workbook, db_path=args.db, recreate=args.recreate)
    print_report(report)