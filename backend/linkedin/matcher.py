"""Phase 8: record LinkedIn cross-reference results for activities."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.linkedin.search_term_builder import build_search_terms, build_per_activity_terms
from backend.config import (
    LINKEDIN_AUTO_METHOD,  # 'apt' or 'manual'
    LINKEDIN_PAGE_HANDLE,  # public page used by the institution
)

ALLOWED_STATUSES = ("Matched", "Possible Match", "Not Found", "Not Checked")


def record_match(conn, activity_id, match_status, reviewer="auto",
                 linkedin_post_url=None, notes=None, confidence=None):
    """Upsert one LinkedIn match result for an activity.

    'Not Found' is only honest when a human actually searched and found
    nothing in a reasonable window — see spec section 20.
    """
    if match_status not in ALLOWED_STATUSES:
        raise ValueError(
            f"Invalid match_status {match_status!r}; allowed {ALLOWED_STATUSES}"
        )
    terms = build_per_activity_terms(conn, activity_id)
    conn.execute(
        """INSERT INTO linkedin_matches
           (activity_id, match_status, linkedin_post_url, search_terms,
            confidence, checked_by, checked_at, notes)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?)
           ON CONFLICT DO NOTHING""",
        (activity_id, match_status,
         linkedin_post_url or "https://www.linkedin.com/company/tcemadurai",
         " | ".join(terms) if terms else None,
         confidence, reviewer, notes or LINKEDIN_AUTO_METHOD),
    )
    conn.commit()


def queue_pending_checks(conn=None, reviewer="pending-batch"):
    """Mark every activity without a linkedin_matches row as 'Not Checked'.

    This is the honest default: we have NOT verified these yet. A human then
    upgrades a defensible subset to 'Matched'/'Not Found' via record_match.
    """
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT a.id FROM institutional_activities a
               WHERE a.id NOT IN (SELECT activity_id FROM linkedin_matches)"""
        ).fetchall()
        count = 0
        for row in rows:
            record_match(conn, row["id"], "Not Checked", reviewer=reviewer,
                         linkedin_post_url=None)
            count += 1
        conn.commit()
        return count
    finally:
        if own:
            conn.close()


def activities_missing_linkedin_check(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        return [r["id"] for r in conn.execute(
            "SELECT id FROM institutional_activities "
            "WHERE id NOT IN (SELECT activity_id FROM linkedin_matches)"
        ).fetchall()]
    finally:
        if own:
            conn.close()


def export_lookup_sheet(conn=None, out_path=None, format="csv"):
    """Write a CSV for a human to search the TCE LinkedIn page and fill results."""
    import csv

    own = conn is None
    conn = conn or get_connection()
    out_path = out_path or os.path.join("data", "linkedin_lookup_queue.csv")
    try:
        rows = conn.execute(
            """SELECT a.id AS activity_id, a.title, a.activity_date,
                      a.source_url
               FROM institutional_activities a
               LEFT JOIN linkedin_matches lm ON lm.activity_id = a.id
               WHERE lm.id IS NULL OR lm.match_status = 'Not Checked'
               ORDER BY a.id"""
        ).fetchall()
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["activity_id", "title", "activity_date",
                             "source_url", "linkedin_page", "search_terms",
                             "result"])
            for r in rows:
                terms = build_per_activity_terms(conn, r["activity_id"])
                writer.writerow([
                    r["activity_id"], r["title"], r["activity_date"],
                    r["source_url"], LINKEDIN_PAGE_HANDLE,
                    " | ".join(terms), "",
                ])
        return len(rows)
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    mode = getattr(__import__("backend.config", fromlist=["LINKEDIN_AUTO_METHOD"]),
                   "LINKEDIN_AUTO_METHOD")
    if mode == "manual":
        n = queue_pending_checks()
        exported = export_lookup_sheet()
        print(f"Marked {n} activities as 'Not Checked'; exported {exported} rows to data/linkedin_lookup_queue.csv")
    else:
        print("LINKEDIN_AUTO_METHOD must be 'manual' for the free workflow.")