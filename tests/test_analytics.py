"""Phase 9 tests: analytics reconciliation — numbers must trace to real rows."""

import pytest

from backend.database.init_db import get_connection
from backend.database import init_db
from backend.database.seed_reference_data import seed
from backend.analytics import (
    overview, department, category, stakeholder,
    linkedin_visibility, data_quality,
)


@pytest.fixture
def conn(tmp_path):
    p = tmp_path / "analytics_test.db"
    init_db.init_db(str(p))
    conn = get_connection(db_path=str(p))
    seed(conn=conn)
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, activity_date, overall_confidence, is_verified)
           VALUES ('Workshop A', 'workshop a', 'workshop for CSE dept', '2024-01-20', 0.8, 1)"""
    )
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, activity_date, overall_confidence, is_verified)
           VALUES ('FDP B', 'fdp b', 'fdp jointly by CSE and IT', '2024-05-01', 0.7, 0)"""
    )
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, activity_date, overall_confidence, is_verified)
           VALUES ('Future Event C', 'future event c', 'event dated 2026 with no year bucket', '2026-03-01', 0.5, 0)"""
    )
    conn.commit()
    aids = [r["id"] for r in conn.execute("SELECT id FROM institutional_activities ORDER BY id")]
    cse, it = [r["id"] for r in conn.execute("SELECT id, code FROM departments WHERE code IN ('CSE','IT')")]
    year_id = conn.execute("SELECT id FROM academic_years WHERE name='2023-2024'").fetchone()["id"]
    conn.execute("UPDATE institutional_activities SET activity_year_id=? WHERE id=?", (year_id, aids[0]))
    conn.execute("UPDATE institutional_activities SET activity_year_id=? WHERE id=?", (year_id, aids[1]))
    cat = conn.execute("SELECT id FROM categories WHERE code='WORKSHOP'").fetchone()
    if cat:
        conn.execute(
            "INSERT INTO activity_categories (activity_id, category_id, confidence, is_primary) VALUES (?, ?, 0.8, 1)",
            (aids[0], cat["id"]),
        )
    conn.execute("INSERT INTO activity_departments (activity_id, department_id, is_primary) VALUES (?, ?, 1)", (aids[0], cse))
    conn.execute("INSERT INTO activity_departments (activity_id, department_id, is_primary) VALUES (?, ?, 1)", (aids[1], cse))
    conn.execute("INSERT INTO activity_departments (activity_id, department_id, is_primary) VALUES (?, ?, 0)", (aids[1], it))
    st = conn.execute("SELECT id FROM stakeholders WHERE code='STUDENTS'").fetchone()
    if st:
        conn.execute(
            "INSERT INTO activity_stakeholders (activity_id, stakeholder_id, confidence, is_primary) VALUES (?, ?, 0.8, 1)",
            (aids[0], st["id"]),
        )
    for aid in aids:
        conn.execute(
            "INSERT INTO linkedin_matches (activity_id, match_status, checked_by, checked_at) "
            "VALUES (?, 'Not Checked', 'test', datetime('now'))", (aid,))
    conn.commit()
    return conn


def test_overview_totals_reconcile(conn):
    o = overview.overview(conn)
    assert o["total_activities"] == 3
    assert o["verified_activities"] == 1
    assert o["needs_review"] == 0
    # only year-mapped activities appear in yearly buckets; others stay unmapped
    assert sum(y["total_activities"] for y in o["yearly_breakdown"]) == 2


def test_department_counts_account_for_multi(conn):
    d = department.department_summary(conn)
    by_code = {r["department_code"]: r for r in d}
    # CSE involved in both; IT only in one (primary_count + involvement split)
    assert by_code["CSE"]["involvement_count"] == 2
    assert by_code["IT"]["involvement_count"] == 1


def test_category_summary_reconciles(conn):
    s = category.category_summary(conn)
    assert sum(r["classification_count"] for r in s) == 1


def test_stakeholder_summary_reconciles(conn):
    s = stakeholder.stakeholder_summary(conn)
    assert sum(r["involvement_count"] for r in s) == 1


def test_linkedin_visibility_honest(conn):
    lk = linkedin_visibility.linkedin_summary(conn)
    assert lk["total_activities"] == 3
    assert lk["not_checked"] == 3
    assert lk["matched"] == 0


def test_data_quality_counts(conn):
    dq = data_quality.data_quality(conn)
    assert dq["total_activities"] == 3
    assert dq["field_completeness"]["title"]["filled"] == 3
    assert dq["linkedin_unchecked"] == 0