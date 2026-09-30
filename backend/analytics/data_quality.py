"""Phase 9: data-quality analytics (overall completeness)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def _completeness(conn, column):
    total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]
    filled = conn.execute(
        f"SELECT COUNT(*) AS c FROM institutional_activities WHERE {column} IS NOT NULL"
    ).fetchone()["c"]
    return (round(filled / total, 4), filled) if total else (0.0, 0)


def data_quality(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]
        fields = {}
        for col in ("title", "description", "activity_date", "venue",
                    "organizer", "resource_person", "source_url", "overall_confidence"):
            ratio, filled = _completeness(conn, col)
            fields[col] = {"filled": filled, "ratio": ratio}
        link_missing = conn.execute(
            """SELECT COUNT(*) AS c FROM institutional_activities a
               WHERE a.id NOT IN (SELECT activity_id FROM linkedin_matches)"""
        ).fetchone()["c"]
        review_backlog = conn.execute(
            """SELECT COUNT(*) AS c FROM review_queue
               WHERE status IN ('open', 'in_progress')"""
        ).fetchone()["c"]
        return {
            "total_activities": total,
            "field_completeness": fields,
            "linkedin_unchecked": link_missing,
            "review_backlog": review_backlog,
        }
    finally:
        if own:
            conn.close()