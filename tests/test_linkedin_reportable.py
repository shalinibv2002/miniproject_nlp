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

def _insert_post(conn, post_id, text, url=None):
    conn.execute(
        "INSERT INTO linkedin_posts (id, post_text, normalized_text, source_sheet, source_row, post_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (post_id, text, text.lower(), "June 2025-June 2026", post_id, url),
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
            "open to all students."),
        (2, "The management and staff of Thiagarajar College of Engineering wish you and your family "
            "a very happy and prosperous Pongal festival celebration this year."),
        (3, " ", "https://www.linkedin.com/posts/tcemadurai_x"),
        (4, "Students of the Department of Information Technology attended a Five-Day Faculty "
            "Development Programme on Cloud Computing from 3 March 2026 organized by the Department "
            "of Information Technology at TCE Madurai."),
    ]
    for pid, text, *rest in posts:
        url = rest[0] if rest else None
        _insert_post(conn, pid, text, url)

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
    assert plain == sum(x["activity_count"] for x in yearly)
    filtered = rep.count_reportable(reportable_conn, {"academic_year": "2025-26"})
    cats = rep.analytics_categories(reportable_conn, {"academic_year": "2025-26"})
    assert filtered == sum(x["activity_count"] for x in cats)


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
    assert years == [{"academic_year": "2025-26", "activity_count": 2}]

    cats = {x["category"]: x["activity_count"] for x in client.get("/api/linkedin/categories").get_json()}
    assert cats.get("WORKSHOP") == 1 and cats.get("FDP") == 1

    filters = client.get("/api/linkedin/filters").get_json()
    assert filters["years"] == ["2025-26"]
    assert {c["code"] for c in filters["categories"]} >= {"WORKSHOP", "FDP"}
    assert len(filters["departments"]) >= 1
    assert len(filters["stakeholders"]) >= 1

    overview = client.get("/api/linkedin/analytics/overview").get_json()
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
    assert overview["total_reportable_activities"] == 3

    assert client.post("/api/admin/linkedin/activities/LI-99999/publish",
                       json={}, headers=headers).status_code == 404