"""Phase 9: department-wise analytics."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def department_summary(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT d.code, d.short_name, d.name,
                      COUNT(ad.id) AS involvement_count,
                      SUM(CASE WHEN ad.is_primary THEN 1 ELSE 0 END) AS primary_count
               FROM departments d
               LEFT JOIN activity_departments ad ON ad.department_id = d.id
               GROUP BY d.id, d.code, d.short_name, d.name
               ORDER BY involvement_count DESC, d.code"""
        ).fetchall()
        return [
            {
                "department_code": r["code"],
                "department_name": r["name"],
                "involvement_count": r["involvement_count"],
                "primary_count": r["primary_count"],
            }
            for r in rows
        ]
    finally:
        if own:
            conn.close()


def category_breakdown_by_department(conn=None):
    """Path: department -> categories -> activity counts."""
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT d.code AS department_code,
                      c.code AS category_code,
                      COUNT(DISTINCT a.id) AS activity_count
               FROM activity_departments ad
               JOIN departments d ON d.id = ad.department_id
               JOIN activity_categories ac ON ac.activity_id = ad.activity_id
               JOIN categories c ON c.id = ac.category_id
               JOIN institutional_activities a ON a.id = ad.activity_id
               GROUP BY d.id, c.id
               ORDER BY d.code, activity_count DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()