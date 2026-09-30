"""Phase 8 tests: search term building + legitimate match recording."""

import pytest

from backend.database.init_db import get_connection
from backend.database import init_db
from backend.database.seed_reference_data import seed
from backend.linkedin.search_term_builder import build_search_terms
from backend.linkedin import matcher


@pytest.fixture
def conn(tmp_path):
    p = tmp_path / "linkedin_test.db"
    init_db.init_db(str(p))
    conn = get_connection(db_path=str(p))
    seed(conn=conn)
    yield conn
    conn.close()


@pytest.fixture
def activity(conn):
    conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, activity_date)
           VALUES ('National Level Technical Symposium', 'national level technical symposium',
                   'Technical paper and project presentations organized by the Department of CSE.',
                   '2026-03-15')"""
    )
    conn.commit()
    return conn.execute("SELECT id FROM institutional_activities ORDER BY id DESC LIMIT 1").fetchone()["id"]


def test_build_search_terms_specificity(activity):
    terms = build_search_terms(
        "National Level Technical Symposium", "Technical symposium for students.",
        "2026-03-15", "Computer Science and Engineering",
    )
    assert terms[0] == "National Level Technical Symposium"
    assert any("Computer Science" in t for t in terms)
    assert any("2026" in t for t in terms)


def test_build_search_terms_no_fabrication(conn, activity):
    terms = matcher.build_per_activity_terms(conn, activity)
    assert len(terms) >= 1
    assert all("linkedin.com" not in t.lower() for t in terms)


def test_record_match_and_activities_preserved(conn, activity):
    matcher.record_match(conn, activity, "Matched",
                         reviewer="case-study-demo",
                         linkedin_post_url="https://www.linkedin.com/company/tcemadurai")
    row = conn.execute(
        "SELECT match_status, linkedin_post_url FROM linkedin_matches WHERE activity_id=?",
        (activity,),
    ).fetchone()
    assert row["match_status"] == "Matched"
    # the website activity must remain regardless of match result
    assert conn.execute(
        "SELECT COUNT(*) FROM institutional_activities WHERE id=?", (activity,)
    ).fetchone()[0] == 1


def test_invalid_match_status_rejected(conn, activity):
    with pytest.raises(ValueError):
        matcher.record_match(conn, activity, "Confirmed via hack")


def test_not_checked_without_search(conn, activity):
    matcher.queue_pending_checks(conn)
    rows = conn.execute(
        "SELECT match_status, linkedin_post_url FROM linkedin_matches WHERE activity_id=?",
        (activity,),
    ).fetchall()
    assert all(r["match_status"] == "Not Checked" for r in rows)
    # never claim 'Not Found' when we did not search
    assert all(r["match_status"] != "Not Found" for r in rows)


def test_export_lookup_sheet(tmp_path, conn, activity):
    out = tmp_path / "queue.csv"
    n = matcher.export_lookup_sheet(conn, out_path=str(out))
    assert n >= 1
    text = out.read_text(encoding="utf-8")
    assert "National Level Technical Symposium" in text
    assert matcher.LINKEDIN_PAGE_HANDLE in text