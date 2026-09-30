"""Tests for the LinkedIn REPORTABLE natural-language engine.

The fixture builds a tiny, fully-real staging database (posts -> candidates ->
reportable rows) exactly like ``test_linkedin_reportable`` and answers
questions through ``backend.nlp.linkedin_query.answer_question`` with that
throwaway connection.  The production reportable/staging/website DBs are
never touched.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from backend.database import linkedin_candidates as cand
from backend.database import linkedin_reportable as rep
from backend.database.linkedin_staging import get_staging_connection, init_staging_schema
from backend.nlp.linkedin_query import answer_question


@pytest.fixture()
def reportable_query_conn(tmp_path):
    staging = str(tmp_path / "staging.db")
    conn = get_staging_connection(staging)
    init_staging_schema(conn)
    posts = [
        (1, "One Day Workshop on Machine Learning by the Department of Computer Science "
            "and Engineering on 15 January 2026 at Thiagarajar College of Engineering, ",
         None),
        (2, "The management wish you a very happy Pongal festival celebration this year.",
         None),
        (3, "The Department of MCA, Thiagarajar College of Engineering invites alumni to "
            "the MCA Alumni Meet 2025 held on 3 January 2026.", None),
    ]
    for pid, text, url in posts:
        conn.execute(
            "INSERT INTO linkedin_posts (id, post_text, normalized_text, source_sheet, "
            "source_row, post_url) VALUES (?, ?, ?, ?, ?, ?)",
            (pid, text, text.lower(), "June 2025-June 2026", pid, url),
        )
    conn.commit()
    cand.generate_candidates(conn)
    conn.close()

    path = str(tmp_path / "reportable.db")
    rep.build_reportable_dataset(staging_db_path=staging, reportable_db_path=path)
    return rep.get_reportable_connection(path)


def _ask(conn, question):
    return answer_question(question, conn=conn)


def test_mca_alias_grounds_to_computer_applications(reportable_query_conn):
    # The MCA Alumni Meet post should ground to "Computer Applications".
    result = _ask(reportable_query_conn, "How many activities does the MCA department have?")
    assert result["status"] in ("answer", "zero")
    assert any("Computer Applications" in c for c in result.get("criteria", []))
    assert result["count"] == 1


def test_mca_department_of_pattern_is_explicit(reportable_query_conn):
    row = reportable_query_conn.execute(
        "SELECT departments, department_display FROM linkedin_reportable_activities "
        "WHERE title LIKE '%MCA Alumni Meet%'").fetchone()
    assert row is not None
    assert "Computer Applications" in row["departments"]
    # explicit MCA organizer, not the institution-wide General fallback
    assert "General" not in row["departments"]
    assert "General" not in row["department_display"]


def test_year_wise_grouping_returns_breakdown(reportable_query_conn):
    result = _ask(reportable_query_conn, "How many workshops year wise?")
    assert result["status"] == "answer"
    assert result["rows"], "year-wise breakdown should list academic years"


def test_blocked_year_answers_honestly(reportable_query_conn):
    result = _ask(reportable_query_conn, "How many activities took place in 2010-2011?")
    assert result["count"] == 0
    assert result["status"] == "answer"
    assert "no available records" in result["answer"]


def test_undated_question_uses_date_status_filter(reportable_query_conn):
    result = _ask(reportable_query_conn, "How many activities are undated?")
    assert result["count"] == 0
    assert any("Date status" in c for c in result.get("criteria", []))


def test_projections_never_leak_internal_fields(reportable_query_conn):
    result = _ask(reportable_query_conn, "Show workshop activities.")
    for rec in result.get("activities", []):
        for internal in ("classification_status", "review_status", "date_status",
                         "evidence_score", "staging_post_id"):
            assert internal not in rec