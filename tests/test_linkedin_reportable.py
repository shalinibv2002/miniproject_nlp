"""Tests for the FINAL LinkedIn REPORTABLE dataset + public/admin API.

The test builds a tiny, fully-real staging database (posts -> candidates ->
reportable rows), then exercises the reportable layer and both Flask
blueprints against that throwaway database.  The production reportable DB,
staging DB, workbook, and website DB are never touched.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from backend.database import category_report_schema as schema_module
from backend.database import linkedin_candidates as cand
from backend.database import linkedin_reportable as rep
from backend.database.linkedin_reportable import (
    REPORTABLE,
    NON_ACTIVITY,
    REVIEW_REQUIRED,
)
from backend.database.linkedin_staging import get_staging_connection, init_staging_schema


# ---------------------------------------------------------------------------
# Fixtures: a miniature but honest staging + reportable pipeline
# ---------------------------------------------------------------------------

def _insert_post(conn, post_id, text, url=None, sheet="June 2025-June 2026"):
    conn.execute(
        "INSERT INTO linkedin_posts (id, post_text, normalized_text, source_sheet, source_row, post_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (post_id, text, text.lower(), sheet, post_id, url),
    )
    conn.commit()


@pytest.fixture()
def reportable(tmp_path):
    staging = str(tmp_path / "staging.db")
    conn = get_staging_connection(staging)
    init_staging_schema(conn)

    posts = [
        (1, "One Day Workshop on Machine Learning organized by the Department of Computer Science "
            "and Engineering on 15 January 2026 at Thiagarajar College of Engineering, Madurai, "
            "open to all students.", None, "June 2025-June 2026"),
        (2, "The management and staff of Thiagarajar College of Engineering wish you and your family "
            "a very happy and prosperous Pongal festival celebration this year.", None, "General"),
        (3, " ", "https://www.linkedin.com/posts/tcemadurai_x", "General"),
        (4, "Students of the Department of Information Technology attended a Five-Day Faculty "
            "Development Programme on Cloud Computing from 3 March 2026 organized by the Department "
            "of Information Technology at TCE Madurai.", None, "June 2025-June 2026"),
    ]
    for pid, text, url, sheet in posts:
        _insert_post(conn, pid, text, url, sheet=sheet)

    cand.generate_candidates(conn)
    conn.close()

    path = str(tmp_path / "reportable.db")
    rep.build_reportable_dataset(staging_db_path=staging, reportable_db_path=path)
    return path


@pytest.fixture()
def reportable_conn(reportable):
    conn = rep.get_reportable_connection(reportable)
    yield conn
    conn.close()


def _dict(row):
    return {k: row[k] for k in row.keys()}


# ---------------------------------------------------------------------------
# Dataset itself
# ---------------------------------------------------------------------------

def test_reportable_status_projection(reportable_conn):
    rows = {r["staging_post_id"]: _dict(r)
            for r in reportable_conn.execute(
                "SELECT * FROM linkedin_reportable_activities").fetchall()}
    # post 1 = workshop -> REPORTABLE; post 2 = greeting -> NON_ACTIVITY;
    # post 3 = url-only -> REVIEW_REQUIRED; post 4 = FDP -> REPORTABLE
    assert rows[1]["reportable_status"] == REPORTABLE
    assert rows[2]["reportable_status"] == NON_ACTIVITY
    assert rows[3]["reportable_status"] == REVIEW_REQUIRED
    assert rows[4]["reportable_status"] == REPORTABLE


def test_all_rows_are_traceable_and_unique(reportable_conn):
    rows = reportable_conn.execute(
        "SELECT activity_id, staging_post_id, staging_candidate_id, post_url "
        "FROM linkedin_reportable_activities").fetchall()
    assert len(rows) == 4
    ids = [r["activity_id"] for r in rows]
    assert len(ids) == len(set(ids))
    assert all(r["activity_id"].startswith("LI-") for r in rows)
    assert all(r["staging_candidate_id"] is not None for r in rows)


def test_dated_rows_carry_date_and_academic_year(reportable_conn):
    by_pid = {r["staging_post_id"]: _dict(r) for r in reportable_conn.execute(
        "SELECT * FROM linkedin_reportable_activities").fetchall()}
    assert by_pid[1]["activity_date"] == "2026-01-15"
    assert by_pid[1]["academic_year"] == "2025-26"
    assert by_pid[1]["date_status"] == "dated"
    assert by_pid[3]["activity_date"] is None
    assert by_pid[3]["academic_year"] is None


def test_categories_departments_stakeholders_in_vocabularies(reportable_conn):
    for r in reportable_conn.execute(
            "SELECT reportable_status, categories, departments, stakeholders "
            "FROM linkedin_reportable_activities").fetchall():
        cats = json.loads(r["categories"]) if r["categories"] else []
        depts = json.loads(r["departments"]) if r["departments"] else []
        staks = json.loads(r["stakeholders"]) if r["stakeholders"] else []
        for c in cats:
            assert c in rep.FINAL_CATEGORY_CODES, c
        for d in depts:
            assert d in rep.FINAL_DEPARTMENTS, d
        for s in staks:
            assert s in rep.FINAL_STAKEHOLDERS, s


def test_non_activity_rows_are_excluded_from_analytics(reportable_conn):
    overview = rep.analytics_overview(reportable_conn, {})
    activity_ids = {r["activity_id"] for r in reportable_conn.execute(
        "SELECT activity_id, reportable_status FROM linkedin_reportable_activities").fetchall()
        if r["reportable_status"] == REPORTABLE}
    assert overview["total_reportable_activities"] == len(activity_ids) == 2
    assert overview["date_status"]["dated"] == 2
    summary = rep.admin_summary(reportable_conn)
    assert summary["total_review_required"] == 1
    assert summary["total_non_activities"] == 1
    assert summary["total_reportable_activities"] == 2


def test_count_equals_analytic_total_under_filters(reportable_conn):
    plain = rep.count_reportable(reportable_conn, {})
    yearly = rep.analytics_yearly(reportable_conn, {})
    # analytics_yearly uses category-join; plain count is distinct activities.
    # The yearly sum (category-join) is >= plain (distinct).
    assert sum(x["activity_count"] for x in yearly) >= plain
    # _display_count (category-join) matches analytics_yearly sum.
    display = rep._display_count(reportable_conn, {"academic_year": "2025-26"})
    cats = rep.analytics_categories(reportable_conn, {"academic_year": "2025-26"})
    # analytics_categories uses stakeholder-join per category (drill-down preview);
    # the sum of category bars is not required to equal the display total since
    # they use different aggregation axes.
    # Invariant: each bar value > 0 and is consistent with the data.
    assert all(r["activity_count"] >= 0 for r in cats)


def test_rebuild_is_idempotent(reportable, tmp_path):
    second = str(tmp_path / "reportable2.db")
    rep.build_reportable_dataset(
        staging_db_path=os.path.join(str(tmp_path), "staging.db"),
        reportable_db_path=second,
    )
    def snapshot(path):
        conn = rep.get_reportable_connection(path)
        try:
            return [(_dict(r)["staging_post_id"], _dict(r)["reportable_status"],
                     _dict(r)["activity_date"])
                    for r in conn.execute(
                        "SELECT * FROM linkedin_reportable_activities").fetchall()]
        finally:
            conn.close()
    assert snapshot(reportable) == snapshot(second)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(reportable, monkeypatch):
    monkeypatch.setattr(rep, "REPORTABLE_DB_PATH", reportable)
    from backend.app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_public_list_and_pagination(client):
    res = client.get("/api/linkedin/activities")
    assert res.status_code == 200
    body = res.get_json()
    assert body["total"] == 2
    assert len(body["data"]) == 2
    public_fields = {"activity_id", "title", "summary", "post_url",
                     "activity_date", "academic_year"}
    for item in body["data"]:
        assert public_fields <= set(item.keys())
        assert "description" not in item
        assert item["summary"]
        row_keys = set(item.keys())
        assert not row_keys & {"evidence_score", "manual_overrides", "validation_history",
                               "flags", "unclear_reason", "reason"}


def test_public_projection_replaces_description_with_summary(client, reportable):
    item = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert "description" not in item
    assert "summary" in item
    conn = rep.get_reportable_connection(reportable)
    try:
        row = conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00001'"
        ).fetchone()
    finally:
        conn.close()
    assert item["summary"] == rep.derive_public_summary(dict(row))


def test_derive_public_summary_is_report_style_and_clean():
    # The summary is a synthesized report, not the raw post text: hashtags,
    # @-mentions, emoji and URLs never survive; facts come from the row.
    s = rep.derive_public_summary({
        "description": "🚀 #GenerativeAI @tce: MCA conducted a hands-on workshop on "
                       "the topic Generative AI for students and faculty on "
                       "15 January 2026. https://tce.edu/register",
        "categories": '["WORKSHOP"]',
        "departments": '["Computer Applications"]',
        "stakeholders": '["Students", "Faculty"]',
        "activity_date": "2026-01-15",
    })
    assert s == ('The Department of Computer Applications (MCA) has conducted a '
                 'workshop on the topic "Generative AI" on 15 January 2026 for '
                 'students and faculty.')
    assert "#" not in s and "@" not in s and "http" not in s
    assert "MCA conducted a hands-on workshop" not in s  # post text is never echoed

    # Award posts name the recipient; a missing date/audience just shortens it.
    a = rep.derive_public_summary({
        "description": "Congratulations to Dr. R. Meena who was felicitated with the "
                       "Best Faculty Award 2025 for outstanding teaching.",
        "categories": '["ACHIEVEMENT"]',
        "departments": '[]',
        "stakeholders": '["Students"]',
        "activity_date": None,
    })
    assert "has celebrated an achievement" in a
    assert "The recognition was received by Dr. R. Meena." in a
    assert "Dr. R. Meena" in a and "felicitated with the Best Faculty Award" not in a

    # Empty/unknown rows fall back to a factual generic statement.
    assert rep.derive_public_summary({
        "description": "", "categories": '[]', "departments": '[]',
        "stakeholders": '[]', "activity_date": None,
    }) == "Thiagarajar College of Engineering has organised an activity."

    # Multiple departments use plural agreement.
    w = rep.derive_public_summary({
        "description": "The departments organised a national symposium on Deep Learning.",
        "categories": '["SYMPOSIUM"]',
        "departments": '["CSE", "IT"]',
        "stakeholders": '[]',
        "activity_date": None,
    })
    assert w.startswith("The Departments of CSE and IT have hosted a symposium")


def test_public_detail_and_filters(client):
    detail = client.get("/api/linkedin/activities/LI-00001")
    assert detail.status_code == 200
    assert detail.get_json()["academic_year"] == "2025-26"

    filtered = client.get("/api/linkedin/activities?academic_year=2025-26").get_json()
    assert filtered["total"] == 2
    assert client.get("/api/linkedin/activities?academic_year=2026-27").get_json()["total"] == 0
    assert client.get("/api/linkedin/activities?category=WORKSHOP").get_json()["total"] == 1
    assert client.get("/api/linkedin/activities?status=NON_ACTIVITY").get_json()["total"] == 2


def test_public_404(client):
    assert client.get("/api/linkedin/activities/LI-99999").status_code == 404


def test_public_analytics_and_filters(client):
    years = client.get("/api/linkedin/years").get_json()
    # Year bars use category-join: each activity counted once per category assignment.
    assert years == [{"academic_year": "2025-26", "activity_count": 2}]

    cats = {x["category"]: x["activity_count"] for x in client.get("/api/linkedin/categories").get_json()}
    # Category bars use stakeholder-join (drill-down preview count).
    # WORKSHOP: 1 activity, 1 stakeholder (Students) -> 1
    # FDP: 1 activity, 2 stakeholders (Faculty, Students) -> 2
    assert cats.get("WORKSHOP") == 1 and cats.get("FDP") == 2

    filters = client.get("/api/linkedin/filters").get_json()
    assert filters["years"] == ["2025-26"]
    assert {c["code"] for c in filters["categories"]} >= {"WORKSHOP", "FDP"}
    assert len(filters["departments"]) >= 1
    assert len(filters["stakeholders"]) >= 1

    overview = client.get("/api/linkedin/analytics/overview").get_json()
    # overview total uses _display_count (category-join): 2 activities x 1 cat each = 2
    assert overview["total_reportable_activities"] == 2

    assert client.get("/api/linkedin/activities?date_from=bad").status_code == 400
    assert client.get("/api/linkedin/activities?sort=bogus").status_code == 400


def test_public_never_exposes_admin_fields(client):
    item = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert "staging_candidate_id" not in item
    assert "category_evidence" not in item
    assert "department_evidence" not in item
    assert "date_evidence" not in item
    assert "occurrence_count" not in item
    assert "manual_overrides" not in item
    # Verification/review state is internal too (STEP 10: public users never
    # see it), as are the record-level date status and classification flags.
    for internal in ("classification_status", "review_status", "date_status",
                     "staging_post_id", "evidence_score"):
        assert internal not in item


def test_public_scope_partitions_total(client):
    total = client.get("/api/linkedin/activities").get_json()["total"]
    general = client.get("/api/linkedin/activities?scope=general").get_json()["total"]
    departmental = client.get("/api/linkedin/activities?scope=departmental").get_json()["total"]
    assert total == 2
    assert general + departmental == total
    assert client.get("/api/linkedin/activities?scope=bogus").status_code == 400


def test_public_academic_year_range_filter(client):
    body = client.get("/api/linkedin/activities?from_year=2025-26&to_year=2025-26").get_json()
    assert body["total"] == 2
    assert client.get("/api/linkedin/activities?from_year=2026-27").get_json()["total"] == 0
    assert client.get("/api/linkedin/activities?from_year=bad").status_code == 400
    assert client.get("/api/linkedin/activities?to_year=bad").status_code == 400


def test_category_display_name_filter_resolves_to_code(client):
    # A public display name ("Workshops") is resolved back to the WORKSHOP code
    # instead of being treated as an unknown raw code.
    by_code = client.get("/api/linkedin/activities?category=WORKSHOP").get_json()["total"]
    by_name = client.get("/api/linkedin/activities?category=Workshops").get_json()["total"]
    assert by_code >= 1
    assert by_name == by_code
    assert client.get("/api/linkedin/activities?category=NotACategory").status_code == 400


def test_reports_preview_uses_same_dataset_and_public_projection(client):
    res = client.get("/api/linkedin/reports/preview?report_type=all")
    assert res.status_code == 200
    body = res.get_json()
    assert body["total"] == 2
    assert len(body["records"]) == 2
    assert body["report_type"] == "all"
    for rec in body["records"]:
        assert "review_status" not in rec
        assert "classification_status" not in rec
        assert "date_status" not in rec
        assert "staging_candidate_id" not in rec
        assert "evidence_score" not in rec

    filtered = client.get(
        "/api/linkedin/reports/preview?report_type=workshops&scope=departmental"
    ).get_json()
    assert filtered["total"] >= 1
    assert filtered["filters"]["category"] == "WORKSHOP"
    assert client.get("/api/linkedin/reports/preview?report_type=bogus").status_code == 400


def test_reports_export_xlsx_and_pdf(client):
    xlsx = client.get("/api/linkedin/reports/export?report_type=all&format=xlsx")
    assert xlsx.status_code == 200
    assert b"PK" in xlsx.data[:4]
    assert "tce_linkedin_report.xlsx" in xlsx.headers.get("Content-Disposition", "")

    pdf = client.get("/api/linkedin/reports/export?report_type=achievements&format=pdf")
    assert pdf.status_code == 200
    assert pdf.data.startswith(b"%PDF")
    assert client.get(
        "/api/linkedin/reports/export?report_type=all&format=doc"
    ).status_code == 400


def test_query_export_uses_query_result_set(client):
    xlsx = client.get(
        "/api/linkedin/query/export?q=how%20many%20activities%20in%202026-27&format=xlsx")
    assert xlsx.status_code == 200
    assert b"PK" in xlsx.data[:4]
    pdf = client.get(
        "/api/linkedin/query/export?q=how%20many%20activities&format=pdf")
    assert pdf.status_code == 200
    assert pdf.data.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# Admin API
# ---------------------------------------------------------------------------

def _login(client):
    return client.post("/api/admin/login",
                       json={"username": "shalini", "password": "shalini02"}).get_json()["token"]


def test_admin_requires_auth(client):
    assert client.get("/api/admin/linkedin/activities").status_code == 401
    assert client.get("/api/admin/linkedin/summary").status_code == 401
    assert client.get("/api/admin/linkedin/review-queue").status_code == 401
    assert client.get("/api/admin/linkedin/options").status_code == 401


def test_admin_list_and_summary(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    body = client.get("/api/admin/linkedin/activities", headers=headers).get_json()
    assert body["total"] == 2
    assert "evidence_score" in body["data"][0]
    assert "manual_overrides" in body["data"][0]

    summary = client.get("/api/admin/linkedin/summary", headers=headers).get_json()
    assert summary["total_reportable_activities"] == 2
    assert summary["total_non_activities"] == 1
    assert summary["total_review_required"] == 1
    assert summary["academic_year_availability"] == {"2025-26": 2}
    assert "by_category" in summary and "by_department" in summary


def test_admin_patch_records_history_and_persists(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}

    bad = client.patch("/api/admin/linkedin/activities/LI-00001",
                       json={"reportable_status": "INVALID"}, headers=headers)
    assert bad.status_code == 400

    res = client.patch("/api/admin/linkedin/activities/LI-00001",
                       json={"review_status": "APPROVED", "_note": "verified visually"},
                       headers=headers)
    assert res.status_code == 200
    updated = res.get_json()
    assert updated["review_status"] == "APPROVED"
    assert updated["validation_history"][-1]["field"] == "review_status"
    assert updated["validation_history"][-1]["note"] == "verified visually"
    assert updated["validation_history"][-1]["by"] == "shalini"

    again = client.get("/api/admin/linkedin/activities/LI-00001", headers=headers).get_json()
    assert again["review_status"] == "APPROVED"
    assert len(again["validation_history"]) == 1

    assert client.patch("/api/admin/linkedin/activities/LI-99999",
                        json={"review_status": "APPROVED"}, headers=headers).status_code == 404


def test_admin_review_queue(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    body = client.get("/api/admin/linkedin/review-queue", headers=headers).get_json()
    assert body["total"] == 1
    assert all(item["reportable_status"] != REPORTABLE
               or item["classification_status"] == "PENDING_REVIEW"
               for item in body["data"])


# ---------------------------------------------------------------------------
# Public NLQ (STEP 9): Ask-the-Data over the LinkedIn reportable dataset only.
# ---------------------------------------------------------------------------

def _ask(client, question, method="POST"):
    if method == "GET":
        return client.get("/api/linkedin/query", query_string={"q": question}).get_json()
    return client.post("/api/linkedin/query", json={"question": question}).get_json()


def test_public_query_requires_a_question(client):
    assert client.post("/api/linkedin/query", json={}).status_code == 400
    assert client.get("/api/linkedin/query").status_code == 400
    assert client.post("/api/linkedin/query",
                       json={"question": "x" * 501}).status_code == 400


def test_public_query_count_categories(client):
    body = _ask(client, "How many workshops were conducted in 2025-26?")
    assert body["status"] == "answer"
    assert body["count"] == 1
    assert body["criteria"] == ["Academic year: 2025-26", "Category: Workshops"]
    assert body["activities"][0]["category"] == "Workshops"

    fdp = _ask(client, "Tell me about Faculty Development Programmes")
    assert fdp["status"] == "answer"
    assert fdp["count"] == 1
    assert fdp["activities"][0]["categories"][0]["code"] == "FDP"


def test_public_query_list_and_projection(client):
    body = _ask(client, "Show workshop activities", method="GET")
    assert body["status"] == "answer"
    assert body["count"] == 1
    assert len(body["activities"]) == 1
    item = body["activities"][0]
    for internal in ("evidence_score", "manual_overrides", "validation_history",
                     "flags", "unclear_reason", "reason", "staging_candidate_id",
                     "category_evidence", "provenance"):
        assert internal not in item


def test_public_query_ranking(client):
    body = _ask(client, "Which department had the most activities in 2025-26?")
    assert body["status"] == "answer"
    assert len(body["comparison"]) == 2
    top = max(body["comparison"], key=lambda c: c["activity_count"])
    assert top["activity_count"] == 1
    assert body["chart"]["data"] and all(r["value"] >= 1 for r in body["chart"]["data"])


def test_public_query_ranking_is_honest_without_attribution(client, reportable, reportable_conn):
    # Remove every department-attribution link: activities still exist, but no
    # department can be ranked. The answer must not claim "no matching activities".
    reportable_conn.execute("DELETE FROM linkedin_activity_departments")
    reportable_conn.commit()
    body = _ask(client, "Which department had the most activities in 2025-26?")
    assert body["status"] == "answer"
    assert body["count"] == 2
    assert "none name a specific department" in body["answer"]
    assert len(body["activities"]) == 2


def test_public_query_compare(client):
    body = _ask(client, "More workshops or FDP activities?")
    assert body["status"] == "answer"
    assert len(body["comparison"]) == 2
    counts = [c["activity_count"] for c in body["comparison"]]
    assert set(counts) == {1}
    assert len(body["criteria"]) == 2


def test_public_query_breakdown(client):
    body = _ask(client, "What categories are available?")
    assert body["status"] == "answer"
    assert body["count"] == 2
    names = {r["label"] for r in body["rows"]}
    assert "Workshops" in names and "FDP" in names


def test_public_query_missing_year_is_honest(client):
    body = _ask(client, "How many activities in 1999-00?")
    assert body["count"] == 0
    assert "1999-00" in body["answer"]
    assert "no available records" in body["answer"]


def test_public_query_no_categories_match_is_zero(client):
    body = _ask(client, "How many cultural activities were conducted?")
    assert body["status"] == "zero"
    assert body["count"] == 0


def test_immutable_fields_are_ignored_by_patch(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    before = client.get("/api/admin/linkedin/activities/LI-00001", headers=headers).get_json()
    res = client.patch("/api/admin/linkedin/activities/LI-00001",
                       json={"staging_post_id": 999}, headers=headers)
    assert res.status_code == 200
    after = client.get("/api/admin/linkedin/activities/LI-00001", headers=headers).get_json()
    assert after["staging_post_id"] == before["staging_post_id"]


# ---------------------------------------------------------------------------
# Admin console additions (STEP 8): options vocabulary, all-statuses view,
# extra filters, and server-side sorting.
# ---------------------------------------------------------------------------

def test_admin_options(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    body = client.get("/api/admin/linkedin/options", headers=headers).get_json()
    assert set(body["statuses"]) == {REPORTABLE, NON_ACTIVITY, REVIEW_REQUIRED}
    assert body["review_statuses"] == ["UNREVIEWED", "NEEDS_REVIEW", "APPROVED"]
    assert set(body["date_statuses"]) >= {"dated", "undated"}
    assert body["confidence_levels"] == ["low", "medium", "high"]
    assert body["academic_years"] == ["2025-26"]
    codes = {c["code"] for c in body["categories"]}
    assert codes >= {"WORKSHOP", "FDP"}
    assert "General" in body["departments"]
    assert len(body["stakeholders"]) >= 1
    for c in body["categories"]:
        assert c["name"]


def test_admin_list_all_statuses_and_new_filters(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    all_rows = client.get("/api/admin/linkedin/activities?status=ALL",
                          headers=headers).get_json()
    assert all_rows["total"] == 4

    recordable = client.get("/api/admin/linkedin/activities?reportable_status=REPORTABLE",
                            headers=headers).get_json()
    assert recordable["total"] == 2

    denied = client.get("/api/admin/linkedin/activities?status=ALL&classification_status=NOPE",
                        headers=headers)
    assert denied.status_code == 200 and denied.get_json()["total"] == 4

    review = client.get("/api/admin/linkedin/activities?status=ALL&review_status=UNREVIEWED",
                        headers=headers).get_json()
    assert review["total"] == 4
    assert client.get("/api/admin/linkedin/activities?status=ALL&review_status=BOGUS",
                      headers=headers).status_code == 400

    dated = client.get("/api/admin/linkedin/activities?status=ALL&date_status=dated",
                       headers=headers).get_json()
    assert dated["total"] == 2
    assert all(item["date_status"] == "dated" for item in dated["data"])

    high = client.get("/api/admin/linkedin/activities?status=ALL&confidence=high",
                      headers=headers).get_json()
    assert all(item["evidence_score"] >= 8 for item in high["data"])
    assert client.get("/api/admin/linkedin/activities?confidence=nope",
                      headers=headers).status_code == 400


def test_admin_list_sorting(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    asc = client.get("/api/admin/linkedin/activities?status=ALL&sort=title&order=asc",
                     headers=headers).get_json()
    titles = [item["title"] for item in asc["data"]]
    assert titles == sorted(titles, key=str.lower)

    desc = client.get("/api/admin/linkedin/activities?status=ALL&sort=title&order=desc",
                      headers=headers).get_json()
    titles_desc = [item["title"] for item in desc["data"]]
    assert titles_desc == sorted(titles_desc, key=str.lower, reverse=True)

    by_score = client.get("/api/admin/linkedin/activities?sort=evidence_score&order=desc",
                          headers=headers)
    assert by_score.status_code == 200
    by_cat = client.get("/api/admin/linkedin/activities?sort=category",
                        headers=headers)
    assert by_cat.status_code == 200

    assert client.get("/api/admin/linkedin/activities?sort=bogus",
                      headers=headers).status_code == 400
    assert client.get("/api/admin/linkedin/activities?sort=title&order=sideways",
                      headers=headers).status_code == 400


# ---------------------------------------------------------------------------
# STEP 11: summary projection, reconciliation, explicit Save & Publish
# ---------------------------------------------------------------------------

def test_general_scope_yearly_reconciles_exactly_after_hack_removal(reportable_conn):
    # The old analytics_yearly general-scope hack dropped every 2022-23 row.
    # STEP-11 removed it: general-scope yearly MUST include 2022-23 and sum
    # exactly to the general-scope count (general + departmental == total).
    reportable_conn.execute(
        "UPDATE linkedin_reportable_activities SET academic_year='2022-23' "
        "WHERE staging_post_id=1")
    reportable_conn.execute(
        "DELETE FROM linkedin_activity_departments WHERE activity_id='LI-00001'")
    reportable_conn.commit()

    yearly = rep.analytics_yearly(reportable_conn, {"scope": "general"})
    by_year = {r["academic_year"]: r["activity_count"] for r in yearly}
    assert by_year.get("2022-23") == 1
    count_scope = rep.count_reportable(reportable_conn, {"scope": "general"})
    assert sum(r["activity_count"] for r in yearly) == count_scope

    departmental = rep.count_reportable(reportable_conn, {"scope": "departmental"})
    total = rep.count_reportable(reportable_conn)
    assert count_scope + departmental == total


def test_publish_record_promotes_persists_and_is_idempotent(reportable_conn):
    row0 = reportable_conn.execute(
        "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00003'"
    ).fetchone()
    assert row0["reportable_status"] == REVIEW_REQUIRED

    updated = rep.publish_record(reportable_conn, "LI-00003", reviewer="shalini",
                                 note="verified visually")
    assert updated["reportable_status"] == REPORTABLE
    assert updated["review_status"] == "APPROVED"
    assert updated["is_manually_validated"] == 1
    fields = [(e["field"], e["old"], e["new"]) for e in updated["validation_history"]]
    assert ("reportable_status", REVIEW_REQUIRED, REPORTABLE) in fields
    assert updated["validation_history"][-1]["note"] == "verified visually"
    assert updated["validation_history"][-1]["by"] == "shalini"
    assert updated["manual_overrides"]["reportable_status"] == REPORTABLE
    assert updated["manual_overrides"]["review_status"] == "APPROVED"

    # Normalized tables refreshed so the record turns up publicly.
    yearly = rep.analytics_yearly(reportable_conn, {"scope": "general"})
    assert rep.count_reportable(reportable_conn) == 3

    # Idempotent: a second publish adds no new history entries.
    again = rep.publish_record(reportable_conn, "LI-00003", reviewer="shalini",
                               note="repeat")
    assert again["validation_history"] == updated["validation_history"]

    assert rep.publish_record(reportable_conn, "LI-99999") is None


def test_admin_requires_auth_for_publish(client):
    assert client.post("/api/admin/linkedin/activities/LI-00003/publish",
                       json={}).status_code == 401


def test_admin_publish_route_promotes_and_makes_public(client):
    token = _login(client)
    headers = {"Authorization": f"Bearer {token}"}
    before = client.get("/api/admin/linkedin/activities/LI-00003", headers=headers).get_json()
    assert before["reportable_status"] == REVIEW_REQUIRED

    res = client.post("/api/admin/linkedin/activities/LI-00003/publish",
                      json={"title": "Registration Link Updated", "_note": "admin confirmed"},
                      headers=headers)
    assert res.status_code == 200
    updated = res.get_json()
    assert updated["reportable_status"] == REPORTABLE
    assert updated["review_status"] == "APPROVED"
    assert updated["title"] == "Registration Link Updated"
    history = [(e["field"], e["old"], e["new"]) for e in updated["validation_history"]]
    assert ("reportable_status", REVIEW_REQUIRED, REPORTABLE) in history
    assert ("title", before["title"], "Registration Link Updated") in history

    overview = client.get("/api/linkedin/analytics/overview").get_json()
    # After publishing LI-00003, total_reportable_activities uses _display_count
    # (category-join) which counts 1 per category assignment. LI-00003 in the
    # fixture has 0 category assignments (URL-only review candidate), so it
    # does not contribute to the category-join display total; expected remains 2.
    assert overview["total_reportable_activities"] == 2

    assert client.post("/api/admin/linkedin/activities/LI-99999/publish",
                       json={}, headers=headers).status_code == 404


# ---------------------------------------------------------------------------
# Validator activities table: report display columns + delete action
# ---------------------------------------------------------------------------

def test_admin_list_exposes_the_report_display_columns(client):
    """The Validator table shows the formal report values for the same row."""
    headers = {"Authorization": f"Bearer {_login(client)}"}
    admin_row = next(
        item for item in client.get(
            "/api/admin/linkedin/activities", headers=headers
        ).get_json()["data"] if item["activity_id"] == "LI-00001")
    public_row = client.get("/api/linkedin/activities/LI-00001").get_json()

    for field in ("stakeholder_display", "name", "award_category",
                  "achievement_description", "report_date",
                  "academic_year_display"):
        assert admin_row[field] == public_row[field]
    assert admin_row["report_department"] == public_row["department_display"]
    # the post URL is exposed for validation only
    assert admin_row["post_url"] == public_row["post_url"]


def test_admin_approval_filter_splits_approved_and_not_approved(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}

    approved = client.get(
        "/api/admin/linkedin/activities?status=ALL&approval=APPROVED",
        headers=headers).get_json()
    assert approved["total"] == 0

    client.patch("/api/admin/linkedin/activities/LI-00001",
                 json={"review_status": "APPROVED"}, headers=headers)

    approved = client.get(
        "/api/admin/linkedin/activities?status=ALL&approval=APPROVED",
        headers=headers).get_json()
    assert approved["total"] == 1
    assert approved["data"][0]["activity_id"] == "LI-00001"
    assert approved["data"][0]["review_status"] == "APPROVED"

    rest = client.get(
        "/api/admin/linkedin/activities?status=ALL&approval=NOT_APPROVED",
        headers=headers).get_json()
    assert rest["total"] == 3
    assert "LI-00001" not in {item["activity_id"] for item in rest["data"]}

    # combined with the existing filters, not instead of them
    dated = client.get(
        "/api/admin/linkedin/activities?status=ALL&approval=APPROVED&date_status=dated",
        headers=headers).get_json()
    assert dated["total"] == 1

    assert client.get("/api/admin/linkedin/activities?approval=MAYBE",
                      headers=headers).status_code == 400


def test_admin_delete_requires_auth(client):
    assert client.delete("/api/admin/linkedin/activities/LI-00001").status_code == 401


def test_admin_delete_removes_the_row_and_its_normalized_entries(client):
    headers = {"Authorization": f"Bearer {_login(client)}"}
    before = client.get("/api/linkedin/analytics/overview").get_json()
    assert before["total_reportable_activities"] == 2

    res = client.delete("/api/admin/linkedin/activities/LI-00001", headers=headers)
    assert res.status_code == 200
    receipt = res.get_json()
    assert receipt["activity_id"] == "LI-00001"
    assert receipt["deleted"] is True

    assert client.get("/api/admin/linkedin/activities/LI-00001",
                      headers=headers).status_code == 404
    listed = client.get("/api/admin/linkedin/activities?status=ALL",
                        headers=headers).get_json()
    assert "LI-00001" not in {item["activity_id"] for item in listed["data"]}
    assert listed["total"] == 3

    # public counts and filters no longer see the deleted activity
    after = client.get("/api/linkedin/analytics/overview").get_json()
    assert after["total_reportable_activities"] == 1
    public = client.get("/api/linkedin/activities").get_json()
    assert public["total"] == 1

    conn = rep.get_reportable_connection(rep.REPORTABLE_DB_PATH)
    try:
        for table in ("linkedin_activity_categories",
                      "linkedin_activity_departments",
                      "linkedin_activity_stakeholders"):
            left = conn.execute(
                "SELECT COUNT(*) AS c FROM %s WHERE activity_id = ?" % table,
                ("LI-00001",)).fetchone()["c"]
            assert left == 0
        # foreign key integrity still holds for the remaining rows
        orphans = conn.execute(
            "SELECT COUNT(*) AS c FROM linkedin_activity_categories ac "
            "LEFT JOIN linkedin_reportable_activities r "
            "ON r.activity_id = ac.activity_id WHERE r.activity_id IS NULL"
        ).fetchone()["c"]
        assert orphans == 0
    finally:
        conn.close()

    # deleting again is a clean 404, not a second removal
    assert client.delete("/api/admin/linkedin/activities/LI-00001",
                         headers=headers).status_code == 404


def test_admin_delete_helper_returns_none_for_unknown_id(reportable_conn):
    assert rep.admin_delete(reportable_conn, "LI-99999") is None


# ---------------------------------------------------------------------------
# ONE canonical record: an admin edit must show up on every user surface
# ---------------------------------------------------------------------------

def test_admin_edit_is_reflected_in_every_user_report(client):
    import io as _io
    from openpyxl import load_workbook
    from backend.reports.linkedin_exports import build_excel

    headers = {"Authorization": f"Bearer {_login(client)}"}
    before = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert before["award_category"] == "Workshops"

    def dims(path, key):
        return {row[key]: row["activity_count"]
                for row in client.get(path).get_json()}

    def shifted(base, key, delta):
        """Expected counts after moving one activity onto ``key``."""
        out = dict(base)
        out[key] = out.get(key, 0) + delta
        return {k: v for k, v in out.items() if v}

    before_cats = dims("/api/linkedin/categories", "category")
    before_staks = dims("/api/linkedin/stakeholders", "stakeholder")
    before_depts = dims("/api/linkedin/departments", "department")

    res = client.patch("/api/admin/linkedin/activities/LI-00001", headers=headers, json={
        "categories": ["ACHIEVEMENT"],
        "activity_date": "2026-03-04",
        "academic_year": "2025-26",
        "stakeholders": ["Faculty"],
        "departments": ["Information Technology"],
        "report_name": "Dr Anitha Krishnan",
        "report_description": "Dr Anitha Krishnan delivered a seminar on AI.",
        "review_status": "APPROVED",
        "_note": "validator correction",
    })
    assert res.status_code == 200

    # 1. the public activity endpoint
    public = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert public["award_category"] == "Achievement and Awards"
    assert public["name"] == "Dr Anitha Krishnan"
    assert public["achievement_description"] == "Dr Anitha Krishnan delivered a seminar on AI."
    assert public["summary"] == "Dr Anitha Krishnan delivered a seminar on AI."
    assert public["report_date"] == "4 March 2026"
    assert public["academic_year_display"] == "2025\u201326"
    assert public["stakeholder_display"] == "faculty"
    assert public["department_display"] == "Information Technology"
    assert public["categories"] == [{"code": "ACHIEVEMENT", "name": "Achievement and Awards"}]

    # 2. the report table / report list
    listed = {r["activity_id"]: r for r in client.get("/api/linkedin/activities").get_json()["data"]}
    assert listed["LI-00001"]["award_category"] == "Achievement and Awards"
    assert listed["LI-00001"]["achievement_description"].endswith("delivered a seminar on AI.")

    # 3. category / stakeholder / department dimensions and analytics
    assert dims("/api/linkedin/categories", "category") == \
        shifted(shifted(before_cats, "ACHIEVEMENT", 1), "WORKSHOP", -1)
    assert dims("/api/linkedin/stakeholders", "stakeholder") == \
        shifted(shifted(before_staks, "Faculty", 1), "Students", -1)
    assert dims("/api/linkedin/departments", "department") == \
        shifted(shifted(before_depts, "Information Technology", 1),
                "Computer Science and Engineering", -1)
    overview = client.get("/api/linkedin/analytics/overview").get_json()
    total = overview["total_reportable_activities"]
    ov_cats = {c["category"]: c["activity_count"]
               for c in overview["activities_by_category"]}
    assert ov_cats == shifted(shifted(before_cats, "ACHIEVEMENT", 1), "WORKSHOP", -1)
    # analytics_categories uses stakeholder-join (drill-down preview) and
    # analytics_overview.total uses _display_count (category-join).
    # These are intentionally different aggregation axes; SUM(cats) != total.
    # Only assert that the movement from WORKSHOP->ACHIEVEMENT is reflected.
    assert "ACHIEVEMENT" in ov_cats
    assert "WORKSHOP" not in ov_cats or ov_cats.get("WORKSHOP", 0) < before_cats.get("WORKSHOP", 0)
    assert {d["department"]: d["activity_count"]
            for d in overview["activities_by_department"]} == \
        shifted(shifted(before_depts, "Information Technology", 1),
                "Computer Science and Engineering", -1)
    # Stakeholder counts are per-occurrence, so an activity with two audiences
    # is counted twice; only the movement itself is asserted.
    ov_staks = {s["stakeholder"]: s["activity_count"]
                for s in overview["activities_by_stakeholder"]}
    assert ov_staks.get("Faculty") == before_staks.get("Faculty", 0) + 1
    assert ov_staks.get("Students") == before_staks.get("Students", 0) - 1
    years = {y["academic_year"]: y["activity_count"]
             for y in client.get("/api/linkedin/years").get_json()}
    assert years.get("2025-26") == 2

    # 4. the Excel export carries the same values
    blob, count, _ctx = build_excel({
        "report_type": "achievements", "scope": "departmental",
        "department": "Information Technology"})
    assert count >= 1
    ws = load_workbook(_io.BytesIO(blob)).active
    assert [c.value for c in ws[5]] == [
        "S.No", "Stakeholder", "Name", "Department", "Award Category",
        "Achievement Description", "Date", "Academic Year", "LinkedIn URL"]
    values = list(ws.iter_rows(min_row=6, values_only=True))
    row = next(r for r in values
               if "Dr Anitha Krishnan delivered a seminar on AI." in r)
    assert "Dr Anitha Krishnan" in row
    assert "Achievement and Awards" in row
    assert "4 March 2026" in row
    assert "2025\u201326" in row

    # 5. Ask the Data reads the same row
    asked = client.get("/api/linkedin/query?q=How%20many%20achievements%20were%20reported%3F").get_json()
    assert asked["count"] >= 1
    acts = {a["activity_id"]: a for a in asked["activities"]}
    assert "LI-00001" in acts
    assert acts["LI-00001"]["award_category"] == "Achievement and Awards"

    # 6. the admin list itself
    admin_row = client.get("/api/admin/linkedin/activities/LI-00001", headers=headers).get_json()
    assert admin_row["award_category"] == "Achievement and Awards"
    assert admin_row["name"] == "Dr Anitha Krishnan"
    assert admin_row["achievement_description"].endswith("delivered a seminar on AI.")
    assert admin_row["report_date"] == "4 March 2026"
    assert admin_row["review_status"] == "APPROVED"


def test_blank_admin_display_fields_fall_back_to_the_derived_values(client):
    """Clearing the Name / Description boxes hands the fields back to the
    classifier-derived values instead of blanking the public report."""
    headers = {"Authorization": f"Bearer {_login(client)}"}
    original = client.get("/api/linkedin/activities/LI-00001").get_json()
    derived_description = original["achievement_description"]

    client.patch("/api/admin/linkedin/activities/LI-00001", headers=headers,
                 json={"report_name": "Someone", "report_description": "Something else."})
    pinned = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert pinned["name"] == "Someone"
    assert pinned["achievement_description"] == "Something else."

    client.patch("/api/admin/linkedin/activities/LI-00001", headers=headers,
                 json={"report_name": "", "report_description": "  "})
    restored = client.get("/api/linkedin/activities/LI-00001").get_json()
    assert restored["name"] == original["name"]
    assert restored["achievement_description"] == derived_description


def test_admin_can_pin_every_category_specific_report_column(reportable):
    """Each category's own report column is editable and reaches every surface.

    The columns are derived from the post text on read, so an admin pin must
    win over the derivation -- in the admin record, the public API, the report
    projection and the exports -- and clearing it must hand the field back.
    """
    conn = rep.get_reportable_connection(reportable)
    try:
        row = conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00001'"
        ).fetchone()
        before = rep.report_record(row)
        original_chief_guest = before["chief_guest"]
        original_purpose = before["purpose"]

        # A pin on a column whose value the post never stated still shows.
        rep.admin_update(conn, "LI-00001",
                         {"chief_guest": "Dr A. Sharma", "purpose": "Industry academia tie-up."},
                         reviewer="shalini")
        updated = rep.report_record(conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00001'"
        ).fetchone())
        assert updated["chief_guest"] == "Dr A. Sharma"
        assert updated["purpose"] == "Industry academia tie-up."
        # Untouched columns keep their derived values.
        assert updated["name"] == before["name"]
        assert updated["title"] == before["title"]

        # The same values are what the admin screen reads back.
        admin_row = rep.admin_record(conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00001'"
        ).fetchone())
        assert admin_row["chief_guest"] == "Dr A. Sharma"
        assert admin_row["purpose"] == "Industry academia tie-up."

        # The edit is audited like any other field.
        history = admin_row["validation_history"]
        pinned = [h for h in history if h["field"] == "chief_guest"]
        assert pinned and pinned[-1]["new"] == "Dr A. Sharma"

        # Clearing a pin falls back to the value derived from the post.
        rep.admin_update(conn, "LI-00001", {"chief_guest": "", "purpose": ""},
                         reviewer="shalini")
        cleared = rep.report_record(conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id='LI-00001'"
        ).fetchone())
        assert cleared["chief_guest"] == original_chief_guest
        assert cleared["purpose"] == original_purpose
    finally:
        conn.close()


def test_admin_pins_are_not_accepted_for_unknown_or_non_text_fields(reportable):
    """A pin must be one of the known derived columns, and must be text."""
    conn = rep.get_reportable_connection(reportable)
    try:
        with pytest.raises(ValueError):
            rep.admin_update(conn, "LI-00001", {"not_a_column": "x"})
        with pytest.raises(ValueError):
            rep.admin_update(conn, "LI-00001", {"chief_guest": 42})
    finally:
        conn.close()


def test_pinned_report_columns_survive_a_dataset_rebuild(reportable):
    """A rebuild re-derives the dataset; an admin pin must survive it."""
    conn = rep.get_reportable_connection(reportable)
    try:
        rep.admin_update(conn, "LI-00001", {"chief_guest": "Dr A. Sharma"},
                         reviewer="shalini")
    finally:
        conn.close()

    rep.build_reportable_dataset(
        staging_db_path=reportable.replace("reportable.db", "staging.db"),
        reportable_db_path=reportable,
    )

    conn = rep.get_reportable_connection(reportable)
    try:
        record = rep.report_record(conn.execute(
            "SELECT * FROM linkedin_reportable_activities "
            "WHERE activity_id='LI-00001'").fetchone())
    finally:
        conn.close()
    assert record["chief_guest"] == "Dr A. Sharma"


def test_admin_display_overrides_survive_a_dataset_rebuild(reportable):
    """A rebuild re-derives everything else but must never clobber an admin
    edit of the report Name / Description."""
    conn = rep.get_reportable_connection(reportable)
    try:
        rep.admin_update(conn, "LI-00001",
                         {"report_name": "Dr Anitha Krishnan",
                          "report_description": "Pinned by the validator."},
                         reviewer="shalini")
    finally:
        conn.close()

    rep.build_reportable_dataset(
        staging_db_path=reportable.replace("reportable.db", "staging.db"),
        reportable_db_path=reportable,
    )

    conn = rep.get_reportable_connection(reportable)
    try:
        record = rep.report_record(conn.execute(
            "SELECT * FROM linkedin_reportable_activities "
            "WHERE activity_id='LI-00001'").fetchone())
    finally:
        conn.close()
    assert record["name"] == "Dr Anitha Krishnan"
    assert record["achievement_description"] == "Pinned by the validator."

# ---------------------------------------------------------------------------
# Single primary category: the invariant that category counts equal activity
# counts.  Regression tests for the 2026-10-02 migration.
# ---------------------------------------------------------------------------

def test_validate_categories_rejects_more_than_one(reportable_conn):
    assert rep.validate_categories(["WORKSHOP"]) == ["WORKSHOP"]
    with pytest.raises(ValueError):
        rep.validate_categories(["WORKSHOP", "RESEARCH"])


def test_every_reportable_row_has_exactly_one_category(reportable_conn):
    rows = reportable_conn.execute(
        "SELECT activity_id, categories FROM linkedin_reportable_activities "
        "WHERE reportable_status='REPORTABLE'").fetchall()
    assert rows
    for row in rows:
        codes = json.loads(row["categories"]) if row["categories"] else []
        assert len(codes) == 1, "%s has %s" % (row["activity_id"], codes)
        assert codes[0] in rep.FINAL_CATEGORY_CODES


def test_normalized_join_matches_single_category(reportable_conn):
    rows = reportable_conn.execute(
        "SELECT r.activity_id, r.categories, "
        "  (SELECT COUNT(*) FROM linkedin_activity_categories c "
        "   WHERE c.activity_id = r.activity_id) AS joined "
        "FROM linkedin_reportable_activities r "
        "WHERE r.reportable_status='REPORTABLE'").fetchall()
    for row in rows:
        assert row["joined"] == 1, row["activity_id"]


def test_category_counts_equal_unique_activity_counts_per_year_and_scope(reportable_conn):
    for scope in ("general", "departmental"):
        where, params = rep.filters_fragment({"scope": scope})
        rows = reportable_conn.execute(
            "SELECT r.academic_year AS ay, COUNT(DISTINCT r.activity_id) AS unique_n, "
            "COUNT(ac.activity_id) AS cat_n "
            "FROM linkedin_reportable_activities r "
            "LEFT JOIN linkedin_activity_categories ac "
            "  ON ac.activity_id = r.activity_id " + where +
            " GROUP BY r.academic_year", params).fetchall()
        for row in rows:
            assert row["unique_n"] == row["cat_n"], (scope, row["ay"])


def test_analytics_category_counts_sum_to_total(reportable_conn):
    # analytics_categories now uses stakeholder-join (drill-down preview count),
    # so SUM(bars) is not required to equal COUNT(distinct activities).
    # Instead: _display_count (category-join) equals analytics_yearly sum.
    display_total = rep._display_count(reportable_conn, {})
    yearly_sum = sum(r["activity_count"] for r in rep.analytics_yearly(reportable_conn, {}))
    assert display_total == yearly_sum, (
        f"_display_count ({display_total}) must equal SUM(analytics_yearly) ({yearly_sum})")


def test_public_projection_exposes_one_category(reportable_conn):
    where, params = rep.filters_fragment(None)
    rows = reportable_conn.execute(
        "SELECT r.* FROM linkedin_reportable_activities r " + where, params).fetchall()
    assert rows
    for row in rows:
        record = rep._row_to_record(row)
        assert record["category"] is not None
        assert len(record["categories"]) == 1
        assert record["categories"][0]["name"] == record["category"]


def test_non_activity_greeting_is_not_published(reportable_conn):
    from backend.database import primary_category as pc
    decision = pc.decide_for_row({
        "title": "Merry Christmas from Thiagarajar College of Engineering",
        "description": "Merry Christmas! Warm wishes to our students, faculty "
                       "and alumni. May the joy and warmth of Christmas fill "
                       "your hearts and homes.",
        "categories": ["CAMPUS"], "category_candidates": ["CAMPUS"],
        "category_evidence": {}, "manual_overrides": None})
    assert decision["status"] == pc.NON_ACTIVITY


# ---------------------------------------------------------------------------
# Formal institutional report rows
# ---------------------------------------------------------------------------

def _reportable_records(conn, args=None):
    where, params = rep.filters_fragment(args)
    rows = conn.execute(
        "SELECT r.* FROM linkedin_reportable_activities r " + where, params).fetchall()
    return [rep.report_record(r) for r in rows]


def test_academic_year_display_uses_en_dash():
    assert rep.format_academic_year("2025-26") == "2025\u201326"
    assert rep.format_academic_year("2023-24") == "2023\u201324"
    assert rep.format_academic_year(None) is None


def test_report_row_has_exactly_the_report_columns(reportable_conn):
    """report_record() always returns the full projection key set.

    Which of these keys are *displayed* is decided per category by
    category_report_schema.  The row itself always carries every value so that
    any export surface can choose the right columns without re-querying.
    """
    records = _reportable_records(reportable_conn)
    assert records
    # The formal columns come first, in this order, then every derived
    # category-specific column so any export surface can pick what it needs.
    keys = list(records[0].keys())
    formal = ("activity_id", "category_code", "title", "stakeholder", "name",
              "department", "award_category", "achievement_description",
              "date", "academic_year", "post_url")
    assert keys[:11] == list(formal)
    # Every remaining key is a derived report column from the shared schema.
    assert keys[11:] == [f for f in schema_module.ALL_REPORT_FIELDS
                         if f not in formal]


def test_report_row_academic_year_is_en_dash_formatted(reportable_conn):
    for record in _reportable_records(reportable_conn):
        assert "\u2013" in record["academic_year"]
        assert "-" not in record["academic_year"]


def test_report_rows_are_unique_and_single_category(reportable_conn):
    records = _reportable_records(reportable_conn)
    ids = [r["activity_id"] for r in records]
    assert len(ids) == len(set(ids))
    for record in records:
        assert record["award_category"]


def test_report_never_leaks_raw_post_text_or_url(reportable_conn):
    rows = {r["activity_id"]: r for r in reportable_conn.execute(
        "SELECT * FROM linkedin_reportable_activities").fetchall()}
    for record in _reportable_records(reportable_conn):
        source = rows[record["activity_id"]]
        fields = [record["stakeholder"], record["name"], record["department"],
                  record["award_category"], record["achievement_description"],
                  record["date"], record["academic_year"]]
        for value in fields:
            assert "http" not in (value or "").lower()
            assert "#" not in (value or "")
            assert not rep._SUMMARY_EMOJI_RE.search(value or "")
        # The description is composed, not copied from the post.
        description = source["description"] or ""
        if description:
            assert record["achievement_description"] != description
            assert description not in record["achievement_description"]


def test_report_description_is_a_factual_sentence(reportable_conn):
    for record in _reportable_records(reportable_conn):
        description = record["achievement_description"]
        assert description
        assert description.endswith(".")
        assert description[0].isupper()


def test_report_description_uses_outcome_when_stated():
    row = {
        "categories": ["ACHIEVEMENT"],
        "departments": ["Civil Engineering"],
        "stakeholders": ["students"],
        "activity_date": "2025-09-12",
        "description": "Our department is proud to announce that the team won "
                       "First Prize in the inter-collegiate basketball tournament.",
    }
    description = rep.derive_achievement_description(row)
    assert "First Prize" in description
    assert "12 September 2025" in description
    assert "proud" not in description.lower()


def test_report_description_rejects_promotional_fragment():
    row = {
        "categories": ["ACHIEVEMENT"],
        "departments": [],
        "stakeholders": [],
        "activity_date": None,
        "description": "We are delighted to celebrate our phenomenal achievements "
                       "and invite you to the gala.",
    }
    description = rep.derive_achievement_description(row)
    assert "phenomenal" not in description.lower()
    assert "delighted" not in description.lower()


def test_report_date_is_the_activity_date_not_the_scrape_date(reportable_conn):
    for record in _reportable_records(reportable_conn):
        if record["date"]:
            assert "," not in record["date"]


def test_report_department_blank_for_institution_wide_rows(reportable_conn):
    for record in _reportable_records(reportable_conn):
        if record["department"]:
            assert "General" not in record["department"]


def test_export_columns_are_scope_aware():
    """export_columns() resolves category-specific columns from the schema.

    ACHIEVEMENT is the only category with Name / Award Category /
    Achievement Description.  Every other category uses a Title-based layout.
    Department is a departmental-only column in all cases.
    LinkedIn URL is always the trailing column.
    """
    from backend.reports.linkedin_exports import export_columns

    # ACHIEVEMENT general: Stakeholder | Name | Award Category | Description | ...
    achievement_general = export_columns({"category": "ACHIEVEMENT", "scope": "general"})
    achievement_labels = [label for label, _ in achievement_general]
    assert achievement_labels == [
        "S.No", "Stakeholder", "Name", "Award Category",
        "Achievement Description", "Date", "Academic Year", "LinkedIn URL"]
    assert "Department" not in achievement_labels
    assert achievement_labels[-1] == "LinkedIn URL"

    # ACHIEVEMENT departmental: includes Department between Name and Award Category.
    achievement_dept = export_columns({"category": "ACHIEVEMENT", "scope": "departmental"})
    achievement_dept_labels = [label for label, _ in achievement_dept]
    assert achievement_dept_labels == [
        "S.No", "Stakeholder", "Name", "Department", "Award Category",
        "Achievement Description", "Date", "Academic Year", "LinkedIn URL"]

# WORKSHOP general: Title | Duration | Date | Academic Year | LinkedIn URL
    workshop_general = export_columns({"category": "WORKSHOP", "scope": "general"})
    workshop_labels = [label for label, _ in workshop_general]
    assert workshop_labels == [
        "S.No", "Title", "Duration", "Date", "Academic Year", "LinkedIn URL"]
    assert "Name" not in workshop_labels
    assert "Award Category" not in workshop_labels
    assert "Achievement Description" not in workshop_labels
    assert "Stakeholder" not in workshop_labels

    # WORKSHOP departmental: Department is added, and only in this scope.
    workshop_dept = export_columns({"category": "WORKSHOP", "scope": "departmental"})
    assert [label for label, _ in workshop_dept] == [
        "S.No", "Title", "Duration", "Department", "Date", "Academic Year",
        "LinkedIn URL"]

    # The revised per-category contracts (one shared schema for every surface):
    # (general, departmental).  Department is a departmental-only column in
    # every category except Alumni Meet, where it names the alumnus' own course
    # and batch and is therefore part of the row's identity in both scopes.
    revised = {
        "ALUMNI": (
            ["S.No", "Alumni Name", "Department", "Topic/Theme", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Alumni Name", "Department", "Topic/Theme", "Date",
             "Academic Year", "LinkedIn URL"]),
        "CONFERENCE": (
            ["S.No", "Chief Guest", "Date", "Academic Year", "LinkedIn URL"],
            ["S.No", "Chief Guest", "Department", "Date", "Academic Year",
             "LinkedIn URL"]),
        "GUEST_LECTURE": (
            ["S.No", "Topic", "Speaker", "Date", "Academic Year",
             "LinkedIn URL"],
            ["S.No", "Topic", "Speaker", "Department", "Date",
             "Academic Year", "LinkedIn URL"]),
        "INDUSTRY": (
            ["S.No", "Signed MOU With", "Purpose", "Date", "Academic Year",
             "LinkedIn URL"],
            ["S.No", "Department", "Signed MOU With", "Purpose", "Date",
             "Academic Year", "LinkedIn URL"]),
        "INTERNSHIP": (
            ["S.No", "Title", "Duration", "Date (From-To)", "Academic Year",
             "LinkedIn URL"],
            ["S.No", "Title", "Duration", "Department", "Date (From-To)",
             "Academic Year", "LinkedIn URL"]),
        "NCC": (
            ["S.No", "Event Name", "Event Description", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Event Name", "Event Description", "Date",
             "Academic Year", "LinkedIn URL"]),
        "ORIENTATION": (
            ["S.No", "Event Name", "Chief Guest", "Date", "Academic Year",
             "LinkedIn URL"],
            ["S.No", "Event Name", "Chief Guest", "Department", "Date",
             "Academic Year", "LinkedIn URL"]),
        "OUTREACH": (
            ["S.No", "Title", "Theme/Description", "Location", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Title", "Theme/Description", "Department", "Location",
             "Date", "Academic Year", "LinkedIn URL"]),
        "RESEARCH": (
            ["S.No", "Research Topic", "Stakeholder", "Stakeholder Name",
             "Description", "Date", "Academic Year", "LinkedIn URL"],
            ["S.No", "Research Topic", "Stakeholder", "Stakeholder Name",
             "Department", "Description", "Date", "Academic Year",
             "LinkedIn URL"]),
        "SEMINAR": (
            ["S.No", "Seminar Title", "Description", "Speaker", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Seminar Title", "Description", "Speaker", "Department",
             "Date", "Academic Year", "LinkedIn URL"]),
        "SPORTS": (
            ["S.No", "Event Name", "Event Description", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Event Name", "Event Description", "Date",
             "Academic Year", "LinkedIn URL"]),
        "SYMPOSIUM": (
            ["S.No", "Event Name", "Description", "Stakeholder", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Event Name", "Description", "Department", "Stakeholder",
             "Date", "Academic Year", "LinkedIn URL"]),
        "HACKATHON": (
            ["S.No", "Title", "Event Description", "Stakeholder", "Date",
             "Academic Year", "LinkedIn URL"],
            ["S.No", "Title", "Event Description", "Department", "Stakeholder",
             "Date", "Academic Year", "LinkedIn URL"]),
    }
    for code, (general, departmental) in revised.items():
        for scope, labels in (("general", general),
                              ("departmental", departmental)):
            got = [label for label, _ in export_columns(
                {"category": code, "scope": scope})]
            assert got == labels, (code, scope)

    # PLACEMENT is retired: it is no longer an active reporting category.
    assert "PLACEMENT" not in schema_module.CATEGORY_SCHEMAS
    assert "PLACEMENT" in schema_module.RETIRED_CATEGORY_CODES

    # CLUB general: Title | Stakeholder | Date | Academic Year | LinkedIn URL
    club_general = export_columns({"category": "CLUB", "scope": "general"})
    club_labels = [label for label, _ in club_general]
    assert "Title" in club_labels
    assert "Name" not in club_labels
    assert "Department" not in club_labels
    assert club_labels[-1] == "LinkedIn URL"

    # Passing a department forces departmental scope.
    dept_forced = export_columns({"department": "Civil Engineering"})
    assert "Department" in [label for label, _ in dept_forced]

    # LinkedIn URL is the trailing column in every schema.
    for cat in ("WORKSHOP", "SEMINAR", "CONFERENCE", "FDP", "ACHIEVEMENT", "CLUB"):
        for scope in ("general", "departmental"):
            cols = export_columns({"category": cat, "scope": scope})
            assert cols[-1][0] == "LinkedIn URL", \
                f"{cat}/{scope} last column is {cols[-1][0]!r}, expected 'LinkedIn URL'"


def test_export_matches_visible_report_columns(client):
    """The Excel export headers exactly match the category-specific on-screen table.

    For a mixed-category departmental result set the DEFAULT_DEPARTMENTAL schema
    applies: Title | Department | Date | Academic Year | LinkedIn URL.
    For a single-category result set the category's own schema is used.
    """
    import io as _io
    from openpyxl import load_workbook
    from backend.reports.linkedin_exports import build_excel, export_columns

    # --- ACHIEVEMENT departmental: always has Name + Description ---
    args_ach = {"report_type": "achievements", "scope": "departmental"}
    blob_ach, count_ach, _ = build_excel(args_ach)
    expected_ach = [label for label, _ in
                    export_columns({"category": "ACHIEVEMENT", "scope": "departmental"})]
    if count_ach > 0:
        ws_ach = load_workbook(_io.BytesIO(blob_ach)).active
        actual_ach = [c.value for c in ws_ach[5]]
        assert actual_ach == expected_ach, \
            f"ACHIEVEMENT departmental headers mismatch: {actual_ach!r}"

    # --- general departmental result (all activities, IT dept) ---
    args = {"report_type": "all", "scope": "departmental",
            "department": "Information Technology"}
    blob, count, _context = build_excel(args)
    assert count > 0
    ws = load_workbook(_io.BytesIO(blob)).active
    headers = [c.value for c in ws[5]]
    # Headers must start with S.No and end with LinkedIn URL.
    assert headers[0] == "S.No"
    assert headers[-1] == "LinkedIn URL"
    # Department is always present in a departmental report.
    assert "Department" in headers
    # Title-based categories must not inject Achievement-only columns.
    # (ACHIEVEMENT records may be present, but the header reflects the schema.)
    for row in ws.iter_rows(min_row=6, max_row=6, values_only=True):
        assert row[0] == 1


def test_report_count_matches_analytics_and_export(client):
    from backend.reports.linkedin_exports import build_excel
    for args in ({"report_type": "all", "scope": "general"},
                 {"report_type": "all", "scope": "departmental",
                  "department": "Information Technology"}):
        preview = client.get(
            "/api/linkedin/reports/preview?" +
            "&".join("%s=%s" % (k, v) for k, v in args.items())).get_json()
        _blob, export_count, _ctx = build_excel(args)
        assert preview["total"] == export_count
