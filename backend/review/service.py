"""Phase 7: Human review workflow with full audit history."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.config import REVIEW_CONFIDENCE_THRESHOLD

EDITABLE_FIELDS = {
    "title", "description", "activity_date", "activity_date_end", "venue",
    "organizer", "resource_person", "overall_confidence",
}

VALID_ACTIONS = {"edit", "merge", "duplicate-mark", "verify-source",
                 "verify-linkedin", "approve", "reject", "unflag"}

REVIEW_STATUS = {"open", "in_progress", "approved", "rejected"}


def _verified_status_id(conn):
    return conn.execute("SELECT id FROM verification_statuses WHERE code='verified'").fetchone()["id"]


def _needs_review_status_id(conn):
    return conn.execute("SELECT id FROM verification_statuses WHERE code='needs_review'").fetchone()["id"]


def _current_value(conn, activity_id, field):
    row = conn.execute(
        "SELECT {} FROM institutional_activities WHERE id=?".format(field),
        (activity_id,),
    ).fetchone()
    return row[0] if row else None


def queue_low_confidence(conn=None, threshold=None):
    """Queue any activity whose overall_confidence < threshold for review."""
    threshold = threshold if threshold is not None else REVIEW_CONFIDENCE_THRESHOLD
    own = conn is None
    conn = conn or get_connection()
    queued = 0
    try:
        rows = conn.execute(
            """SELECT a.id FROM institutional_activities a
               WHERE a.overall_confidence IS NOT NULL
                 AND a.overall_confidence < ?
                 AND a.id NOT IN (SELECT activity_id FROM review_queue)""",
            (threshold,),
        ).fetchall()
        for row in rows:
            conn.execute(
                """INSERT INTO review_queue (activity_id, reason, status)
                   VALUES (?, 'low-confidence', 'open')""",
                (row["id"],),
            )
            queued += 1
            conn.execute(
                "UPDATE institutional_activities SET verification_status_id=? WHERE id=?",
                (_needs_review_status_id(conn), row["id"]),
            )
        conn.commit()
        return queued
    finally:
        if own:
            conn.close()


def _record_history(conn, activity_id, field, old, new, action, reviewer, reason):
    conn.execute(
        """INSERT INTO review_history
           (activity_id, field_name, old_value, new_value, action, reviewer, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (activity_id, field, old if old is not None else "",
         new if new is not None else "", action, reviewer, reason),
    )


def edit_field(conn, activity_id, field, new_value, reviewer, reason=""):
    """Edit a field on an activity; record before/after in review_history."""
    if field not in EDITABLE_FIELDS:
        raise ValueError(f"Field '{field}' is not editable. Allowed: {sorted(EDITABLE_FIELDS)}")
    old_value = _current_value(conn, activity_id, field)
    conn.execute(
        "UPDATE institutional_activities SET {}=?, updated_at=datetime('now') WHERE id=?".format(field),
        (new_value, activity_id),
    )
    _record_history(conn, activity_id, field, old_value, new_value, "edit", reviewer, reason)
    _update_queue_state(conn, activity_id, "in_progress")
    conn.commit()


def mark_duplicate(conn, activity_id, note="", reviewer=""):
    _record_history(conn, activity_id, "activity_id", None, None,
                    "duplicate-mark", reviewer, note)
    _update_queue_state(conn, activity_id, "in_progress")
    conn.execute(
        "UPDATE institutional_activities SET verification_status_id=? WHERE id=?",
        (_needs_review_status_id(conn), activity_id),
    )
    conn.commit()


def merge_into(conn, source_id, target_id, reviewer, reason=""):
    """Merge source activity into target, preserving source provenance."""
    for table in ("activity_categories", "activity_departments",
                  "activity_stakeholders", "activity_entities",
                  "activity_keywords", "activity_sources", "linkedin_matches"):
        conn.execute(
            f"UPDATE OR IGNORE {table} SET activity_id=? WHERE activity_id=?",
            (target_id, source_id),
        )
    _record_history(conn, target_id, "merged_from_activity_id", source_id, target_id,
                    "merge", reviewer, reason)
    conn.execute("DELETE FROM institutional_activities WHERE id=?", (source_id,))
    _update_queue_state(conn, target_id, "in_progress")
    conn.commit()


def verify_source(conn, activity_id, source_url, reviewer, reason=""):
    old = _current_value(conn, activity_id, "source_url")
    conn.execute(
        "UPDATE institutional_activities SET source_url=?, updated_at=datetime('now') WHERE id=?",
        (source_url, activity_id),
    )
    _record_history(conn, activity_id, "source_url", old, source_url,
                    "verify-source", reviewer, reason)
    _update_queue_state(conn, activity_id, "in_progress")
    conn.commit()


def verify_linkedin(conn, activity_id, post_url, reviewer, note=""):
    conn.execute(
        """INSERT INTO linkedin_matches
           (activity_id, match_status, linkedin_post_url, checked_by, checked_at, notes)
           VALUES (?, 'Matched', ?, ?, datetime('now'), ?)""",
        (activity_id, post_url, reviewer, note),
    )
    _record_history(conn, activity_id, "linkedin_matches", None, post_url,
                    "verify-linkedin", reviewer, note)
    _update_queue_state(conn, activity_id, "in_progress")
    conn.commit()


def approve(conn, activity_id, reviewer, reason=""):
    conn.execute(
        "UPDATE institutional_activities SET verification_status_id=?, is_verified=1, "
        "updated_at=datetime('now') WHERE id=?",
        (_verified_status_id(conn), activity_id),
    )
    _record_history(conn, activity_id, "verification_status", None, "verified",
                    "approve", reviewer, reason)
    _update_queue_state(conn, activity_id, "approved")
    conn.commit()


def reject(conn, activity_id, reviewer, reason=""):
    conn.execute(
        "UPDATE institutional_activities SET verification_status_id=? WHERE id=?",
        (_needs_review_status_id(conn), activity_id),
    )
    _record_history(conn, activity_id, "verification_status", None, "rejected",
                    "reject", reviewer, reason)
    _update_queue_state(conn, activity_id, "rejected")
    conn.commit()


def _update_queue_state(conn, activity_id, state):
    if state == "approved":
        conn.execute(
            "UPDATE review_queue SET status='approved', updated_at=datetime('now') "
            "WHERE activity_id=? AND status != 'rejected'",
            (activity_id,),
        )
    elif state == "rejected":
        conn.execute(
            "UPDATE review_queue SET status='rejected', updated_at=datetime('now') "
            "WHERE activity_id=?",
            (activity_id,),
        )
    else:
        conn.execute(
            "UPDATE review_queue SET status='in_progress', updated_at=datetime('now') "
            "WHERE activity_id=? AND status='open'",
            (activity_id,),
        )


def queue_items(conn=None, status="open", limit=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        q = """SELECT rq.*, a.title, a.overall_confidence, a.verification_status_id
               FROM review_queue rq JOIN institutional_activities a ON a.id = rq.activity_id
               WHERE rq.status=? ORDER BY rq.created_at"""
        params = [status]
        if limit:
            q += " LIMIT ?"
            params.append(limit)
        return [dict(r) for r in conn.execute(q, params).fetchall()]
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    n = queue_low_confidence()
    print(f"Queued {n} low-confidence activities for review.")