"""Phase 7 tests: human review workflow."""

import pytest

from backend.database.init_db import get_connection
from backend.review import service
from backend.config import REVIEW_CONFIDENCE_THRESHOLD


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "review_test.db"
    from backend.database import init_db
    init_db.init_db(str(db_path))
    conn = get_connection(db_path=str(db_path))
    from backend.database.seed_reference_data import seed
    seed(conn=conn)
    yield conn
    conn.close()


@pytest.fixture
def activity(conn):
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, overall_confidence)
           VALUES ('Test Workshop', 'test workshop', 'A workshop for students', 0.40)"""
    )
    conn.commit()
    return conn.execute(
        "SELECT id FROM institutional_activities ORDER BY id DESC LIMIT 1"
    ).fetchone()["id"]


def test_queue_low_confidence(conn, activity):
    queued = service.queue_low_confidence(conn)
    assert queued >= 1
    rows = service.queue_items(conn, status="open")
    assert any(r["activity_id"] == activity for r in rows)
    assert any(r["reason"] == "low-confidence" for r in rows)


def test_edit_rejects_non_editable_field(conn, activity):
    with pytest.raises(ValueError):
        service.edit_field(conn, activity, "normalized_title", "New", "reviewer", "test")


def test_edit_records_history(conn, activity):
    service.queue_low_confidence(conn)
    service.edit_field(conn, activity, "title", "New Title", "reviewer-1", "fix typo")
    rec = conn.execute(
        """SELECT old_value, new_value, action, reviewer, reason
           FROM review_history WHERE activity_id=?""",
        (activity,),
    ).fetchone()
    assert rec["old_value"] == "Test Workshop"
    assert rec["new_value"] == "New Title"
    assert rec["action"] == "edit"
    assert rec["reviewer"] == "reviewer-1"
    assert rec["reason"] == "fix typo"


def test_merge_records_history(conn, activity):
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, overall_confidence)
           VALUES ('Dupe Workshop', 'dupe workshop', 0.30)"""
    )
    conn.commit()
    dupe = conn.execute(
        "SELECT id FROM institutional_activities ORDER BY id DESC LIMIT 1"
    ).fetchone()["id"]
    # give them a shared category to test re-parenting
    cat = conn.execute("SELECT id FROM categories LIMIT 1").fetchone()["id"]
    for aid in (activity, dupe):
        conn.execute(
            "INSERT OR IGNORE INTO activity_categories (activity_id, category_id, is_primary) "
            "VALUES (?, ?, 1)",
            (aid, cat),
        )
    conn.commit()
    service.merge_into(conn, dupe, activity, "reviewer-2", "duplicate content")
    assert conn.execute("SELECT id FROM institutional_activities WHERE id=?", (dupe,)).fetchone() is None
    assert conn.execute("SELECT COUNT(*) FROM activity_categories WHERE activity_id=? AND category_id=?",
                        (activity, cat)).fetchone()[0] == 1
    h = conn.execute(
        """SELECT old_value, new_value, action, reviewer, reason
           FROM review_history WHERE activity_id=? AND action='merge'""",
        (activity,),
    ).fetchone()
    assert h is not None and h["reviewer"] == "reviewer-2"


def test_approve_sets_verified(conn, activity):
    service.queue_low_confidence(conn)
    before = conn.execute(
        "SELECT verification_status_id FROM institutional_activities WHERE id=?",
        (activity,),
    ).fetchone()[0]
    verified = conn.execute(
        "SELECT id FROM verification_statuses WHERE code='verified'"
    ).fetchone()["id"]
    assert before != verified
    service.approve(conn, activity, "reviewer-3", "ok")
    row = conn.execute(
        "SELECT verification_status_id, is_verified FROM institutional_activities WHERE id=?",
        (activity,),
    ).fetchone()
    assert row["is_verified"] == 1
    assert row["verification_status_id"] == verified
    states = [r["status"] for r in service.queue_items(conn, status="approved")]
    assert activity in [r["activity_id"] for r in service.queue_items(conn, status="approved")]


def test_reject_sets_needs_review(conn, activity):
    service.queue_low_confidence(conn)
    service.reject(conn, activity, "reviewer-4", "missing source")
    assert any(
        r["activity_id"] == activity and r["status"] == "rejected"
        for r in service.queue_items(conn, status="rejected")
    )


def test_verify_linkedin_ins(conn, activity):
    service.verify_linkedin(conn, activity, "https://linkedin.com/posts/x", "reviewer-5")
    row = conn.execute(
        "SELECT match_status, linkedin_post_url FROM linkedin_matches WHERE activity_id=?",
        (activity,),
    ).fetchone()
    assert row["match_status"] == "Matched"
    assert row["linkedin_post_url"] == "https://linkedin.com/posts/x"