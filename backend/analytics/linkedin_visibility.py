"""Phase 9: LinkedIn visibility analytics (honest — 'Not Checked' != absent)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def linkedin_summary(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT match_status, COUNT(*) AS c
               FROM linkedin_matches
               GROUP BY match_status"""
        ).fetchall()
        by_status = {r["match_status"]: r["c"] for r in rows}
        total_activities = conn.execute(
            "SELECT COUNT(*) AS c FROM institutional_activities"
        ).fetchone()["c"]
        matched = by_status.get("Matched", 0)
        coverage = round(matched / total_activities, 4) if total_activities else 0.0
        return {
            "total_activities": total_activities,
            "by_status": by_status,
            "matched": matched,
            "possible": by_status.get("Possible Match", 0),
            "not_found_after_search": by_status.get("Not Found", 0),
            "not_checked": by_status.get("Not Checked", 0),
            "coverage_ratio": coverage,
            # Honest framing per spec section 20:
            "note": ("'Not Checked' means manual LinkedIn lookup still pending; "
                     "'Not Found' only records a performed search that returned nothing."),
        }
    finally:
        if own:
            conn.close()