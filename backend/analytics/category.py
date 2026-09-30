"""Phase 9: category-wise analytics."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def category_summary(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT c.code, c.name, c.description,
                      COUNT(ac.id) AS classification_count,
                      SUM(CASE WHEN ac.is_primary THEN 1 ELSE 0 END) AS primary_count,
                      ROUND(AVG(ac.confidence), 3) AS avg_confidence
               FROM categories c
               LEFT JOIN activity_categories ac ON ac.category_id = c.id
               GROUP BY c.id, c.code, c.name, c.description
               ORDER BY classification_count DESC, c.code"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()


def category_trend(conn=None, category_code=None):
    """Category counts sliced by academic year."""
    own = conn is None
    conn = conn or get_connection()
    try:
        q = """SELECT ya.name AS year_name,
                      c.code AS category_code,
                      COUNT(a.id) AS activity_count
               FROM academic_years ya
               JOIN institutional_activities a ON a.activity_year_id = ya.id
               JOIN activity_categories ac ON ac.activity_id = a.id
               JOIN categories c ON c.id = ac.category_id
            """
        params = []
        if category_code:
            q += "WHERE c.code = ?\n"
            params.append(category_code)
        q += "GROUP BY ya.id, c.id ORDER BY ya.start_year, c.code"
        rows = conn.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()