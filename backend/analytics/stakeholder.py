"""Phase 9: stakeholder-wise analytics."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection


def stakeholder_summary(conn=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT s.code, s.name,
                      COUNT(ast.id) AS involvement_count,
                      SUM(CASE WHEN ast.is_primary THEN 1 ELSE 0 END) AS primary_count,
                      ROUND(AVG(ast.confidence), 3) AS avg_confidence
               FROM stakeholders s
               LEFT JOIN activity_stakeholders ast ON ast.stakeholder_id = s.id
               GROUP BY s.id, s.code, s.name
               ORDER BY involvement_count DESC, s.code"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if own:
            conn.close()