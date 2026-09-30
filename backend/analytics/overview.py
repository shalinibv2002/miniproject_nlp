"""Phase 9: overview + yearly analytics."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def yearly_counts(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT ya.name AS year_name,
                      COUNT(a.id) AS total_activities,
                      SUM(CASE WHEN a.is_verified THEN 1 ELSE 0 END) AS verified
               FROM academic_years ya
               LEFT JOIN institutional_activities a
                 ON a.activity_year_id = ya.id
               GROUP BY ya.id, ya.name
               ORDER BY ya.start_year"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()


def overview(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]
        verified = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities WHERE is_verified=1").fetchone()["c"]
        needs_review = conn.execute(
            """SELECT COUNT(*) AS c FROM institutional_activities a
               JOIN verification_statuses v ON v.id = a.verification_status_id
               WHERE v.code = 'needs_review'"""
        ).fetchone()["c"]
        open_review = conn.execute(
            "SELECT COUNT(*) AS c FROM review_queue WHERE status IN ('open','in_progress')"
        ).fetchone()["c"]
        dept_counts = conn.execute(
            """SELECT COUNT(DISTINCT department_id) AS c FROM activity_departments"""
        ).fetchone()["c"]
        cat_counts = conn.execute(
            """SELECT COUNT(DISTINCT category_id) AS c FROM activity_categories"""
        ).fetchone()["c"]
        stk_counts = conn.execute(
            """SELECT COUNT(DISTINCT stakeholder_id) AS c FROM activity_stakeholders"""
        ).fetchone()["c"]
        sources = conn.execute(
            """SELECT COUNT(DISTINCT source_registry_id) AS c FROM activity_sources"""
        ).fetchone()["c"]
        year_start = conn.execute(
            """SELECT MIN(activity_date) AS m FROM institutional_activities"""
        ).fetchone()["m"]
        year_end = conn.execute(
            """SELECT MAX(activity_date) AS m FROM institutional_activities"""
        ).fetchone()["m"]
        return {
            "total_activities": total,
            "verified_activities": verified,
            "needs_review": needs_review,
            "open_review_tasks": open_review,
            "distinct_departments": dept_counts,
            "distinct_categories": cat_counts,
            "distinct_stakeholders": stk_counts,
            "distinct_sources": sources,
            "date_range": {"min": year_start, "max": year_end},
            "yearly_breakdown": yearly_counts(conn),
        }
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    import json
    print(json.dumps(overview(), indent=2, default=str))