"""Phase 6: determine which TCE department(s) an activity involves.

Decision rules:
  - Exact/fuzzy match against department names + aliases.
  - 0 matches  -> 'unknown'
  - 1 match    -> 'single'
  - 2+ matches -> 'multiple'
  - Clear campus-wide markers -> 'institution_wide'
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.nlp.extractors import extract_department_mentions
from backend.nlp.dictionaries import is_institution_wide, load_department_dict
from backend.database.init_db import get_connection


def detect_department_status(text):
    """Return (status_code, matches). matches is a list of dept dicts."""
    if not text:
        return "unknown", []
    if is_institution_wide(text):
        return "institution_wide", []
    matches = extract_department_mentions(text)
    if not matches:
        return "unknown", []
    if len(matches) == 1:
        return "single", matches
    return "multiple", matches


def _dept_status_id(conn, code):
    row = conn.execute(
        "SELECT id FROM department_statuses WHERE code=?", (code,)
    ).fetchone()
    return row["id"] if row else None


def populate_departments(conn=None, activity_id=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        if activity_id:
            rows = conn.execute(
                "SELECT id, title, description FROM institutional_activities WHERE id=?", (activity_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, description FROM institutional_activities"
            ).fetchall()

        counts = {"unknown": 0, "single": 0, "multiple": 0, "institution_wide": 0}
        for row in rows:
            text = " ".join(filter(None, [row["title"], row["description"]]))
            status_code, matches = detect_department_status(text)
            status_id = _dept_status_id(conn, status_code)
            conn.execute(
                "UPDATE institutional_activities SET department_status_id=? WHERE id=?",
                (status_id, row["id"]),
            )
            counts[status_code] += 1
            for index, dept in enumerate(matches):
                conn.execute(
                    """INSERT OR IGNORE INTO activity_departments
                       (activity_id, department_id, confidence, is_primary)
                       VALUES (?, ?, ?, ?)""",
                    (row["id"], dept["department_id"], dept["score"] / 100.0,
                     1 if index == 0 else 0),
                )
        conn.commit()
        return counts
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    counts = populate_departments()
    print("Department status counts:", counts)