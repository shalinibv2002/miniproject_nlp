"""Phase 10 tests: Flask API endpoints behave correctly against a real DB."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Point the DB connection at a throwaway SQLite file for the whole session.
import backend.database.init_db as init_db_mod
from backend.database import init_db
from backend.database.seed_reference_data import seed

_ORIGINAL_DB = init_db_mod.DATABASE_PATH


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("api") / "api_test.db")
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)
    conn = init_db_mod.get_connection(db_path=db)
    try:
        seed(conn=conn)
        # The preserved original records deliberately have no Step 6 metadata.
        for index in range(10):
            conn.execute(
                """INSERT INTO institutional_activities
                   (title, normalized_title, description, activity_date, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Original Activity {index + 1}", f"original activity {index + 1}",
                 "Preserved original institutional record.", "2026-09-01",
                 "https://www.tce.edu/original"),
            )

        # Reproduce the Step 6 final distribution without using the real DB.
        years = (["2021-22"] * 46 + ["2022-23"] * 56 + ["2023-24"] * 105 +
                 ["2024-25"] * 99 + ["2025-26"] * 6 + [None] * 557)
        category_id = conn.execute("SELECT id FROM categories WHERE code='WORKSHOP'").fetchone()["id"]
        for index, academic_year in enumerate(years, start=1):
            cur = conn.execute(
                """INSERT INTO institutional_activities
                   (title, normalized_title, description, activity_date, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Final Workshop {index}", f"final workshop {index}",
                 "Workshop activity for students.", "2024-06-15",
                 f"https://www.tce.edu/activity/{index}"),
            )
            activity_id = cur.lastrowid
            conn.execute(
                """INSERT INTO final_activity_metadata
                   (activity_id, activity_date_text, academic_year, department_display,
                    stakeholder_display, achievement_outcome, evidence_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (activity_id, "15 June 2024", academic_year, "General", "Students",
                 "Workshop outcome", "Official workshop evidence"),
            )
            conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                         (activity_id, category_id))
        # Departmental activities give the two category dimensions real data.
        departmental = (("Information Technology", "ACHIEVEMENT", 5),
                        ("Civil Engineering", "RESEARCH", 2),
                        ("Civil Engineering", "WORKSHOP", 1))
        for department, code, how_many in departmental:
            category_id = conn.execute("SELECT id FROM categories WHERE code=?", (code,)).fetchone()["id"]
            for index in range(how_many):
                cur = conn.execute(
                    """INSERT INTO institutional_activities
                       (title, normalized_title, description, activity_date, source_url)
                       VALUES (?, ?, ?, ?, ?)""",
                    (f"{department} {code} {index + 1}", f"{department.lower()} {code.lower()} {index + 1}",
                     f"{department} activity in {code}.", "2025-01-20",
                     f"https://www.tce.edu/dept/{index}"),
                )
                activity_id = cur.lastrowid
                conn.execute(
                    """INSERT INTO final_activity_metadata
                       (activity_id, activity_date_text, academic_year, department_display,
                        stakeholder_display, achievement_outcome, evidence_text)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (activity_id, "20 January 2025", "2024-25", department, "Students",
                     "Outcome", "Evidence"),
                )
                conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                             (activity_id, category_id))
        # One final record has two preserved official source URLs.
        conn.execute("INSERT INTO activity_sources (activity_id, source_url) VALUES (11, 'https://www.tce.edu/activity/1')")
        conn.execute("INSERT INTO activity_sources (activity_id, source_url) VALUES (11, 'https://www.tce.edu/activity/1/support')")
        conn.commit()
    finally:
        conn.close()

    from backend.app import create_app
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c
    init_db_mod.DATABASE_PATH = _ORIGINAL_DB


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_activities_list(client):
    r = client.get("/api/activities")
    assert r.status_code == 200
    body = r.get_json()
    assert body["pagination"]["total"] >= 1
    expected = {"id", "title", "description", "activity_date", "activity_date_text",
                "academic_year", "department", "general_category", "departmental_category",
                "stakeholder", "achievement_outcome", "categories", "source_url"}
    assert all(set(item) == expected for item in body["data"])
    forbidden = {"normalized_title", "confidence", "overall_confidence", "is_verified",
                 "verification_code", "department_status", "keywords", "raw_record_id", "scope"}
    assert all(not (set(item) & forbidden) for item in body["data"])


def test_activities_pagination(client):
    r = client.get("/api/activities?page=1&page_size=1")
    assert r.status_code == 200
    body = r.get_json()
    assert len(body["data"]) == 1
    assert body["pagination"]["pages"] >= 1


def test_activities_invalid_pagination(client):
    assert client.get("/api/activities?page=abc").status_code == 400
    assert client.get("/api/activities?page=0").status_code == 400


def test_activity_detail(client):
    r = client.get("/api/activities/1")
    assert r.status_code == 200
    body = r.get_json()
    assert body["title"] == "Original Activity 1"
    assert isinstance(body["categories"], list)
    assert "official_sources" in body
    assert "overall_confidence" not in body


def test_activity_not_found(client):
    assert client.get("/api/activities/9999").status_code == 404


def test_reference_endpoints(client):
    for path in ("/api/years", "/api/departments", "/api/categories",
                 "/api/general-categories", "/api/departmental-categories",
                 "/api/stakeholders"):
        r = client.get(path)
        assert r.status_code == 200, path
        assert isinstance(r.get_json(), list), path


def test_final_academic_year_counts(client):
    rows = client.get("/api/years").get_json()
    assert {row["academic_year"]: row["activity_count"] for row in rows} == {
        "2021-22": 46, "2022-23": 56, "2023-24": 105, "2024-25": 107, "2025-26": 6,
    }


def test_clean_activity_filters_search_and_sources(client):
    assert client.get("/api/activities?academic_year=2021-22").get_json()["total"] == 46
    assert client.get("/api/activities?academic_year=Not%20available").get_json()["total"] == 567
    assert client.get("/api/activities?department=General").get_json()["total"] == 879
    assert client.get("/api/activities?category=WORKSHOP").get_json()["total"] == 870
    assert client.get("/api/activities?date_from=2024-06-01&date_to=2024-06-30").get_json()["total"] == 869
    assert client.get("/api/search?q=students").get_json()["data"]
    sources = client.get("/api/activities/11").get_json()["official_sources"]
    assert sources == ["https://www.tce.edu/activity/1", "https://www.tce.edu/activity/1/support"]


def test_dimension_category_filters(client):
    general = client.get("/api/activities?general_category=WORKSHOP").get_json()
    assert general["total"] == 869
    assert {item["department"] for item in general["data"]} == {"General"}
    assert all(item["general_category"] and not item["departmental_category"] for item in general["data"])

    departmental = client.get("/api/activities?departmental_category=ACHIEVEMENT").get_json()
    assert departmental["total"] == 5
    assert all(item["departmental_category"] and not item["general_category"] for item in departmental["data"])
    assert all(item["department"] != "General" for item in departmental["data"])

    combined = client.get("/api/activities?department=Information%20Technology&departmental_category=ACHIEVEMENT").get_json()
    assert combined["total"] == 5
    assert {item["department"] for item in combined["data"]} == {"Information Technology"}

    zero = client.get("/api/activities?general_category=ACHIEVEMENT").get_json()
    assert zero["total"] == 0

    assert client.get("/api/activities?general_category=bogus").status_code == 400
    assert client.get("/api/activities?departmental_category=bogus").status_code == 400
    assert client.get("/api/activities?departmental_category=SPORTS").status_code == 400


def test_scope_is_fully_removed(client):
    body = client.get("/api/activities?scope=General").get_json()
    assert "scope" not in body["data"][0]
    assert "scope" not in client.get("/api/analytics/overview").get_json()
    assert "scope" not in client.get("/api/activities/11").get_json()


def test_general_category_master(client):
    rows = client.get("/api/general-categories").get_json()
    assert len(rows) == 20
    codes = {row["code"] for row in rows}
    assert codes == {
        "ACHIEVEMENT", "RESEARCH", "INDUSTRY", "CLUB", "OUTREACH", "WORKSHOP",
        "CONFERENCE", "SEMINAR", "GUEST_LECTURE", "FDP", "HACKATHON", "CULTURAL",
        "SPORTS", "NCC", "NSS", "PLACEMENT", "INTERNSHIP", "ORIENTATION", "CAMPUS",
        "WEBINAR",
    }
    assert "TECH_FEST" not in codes and "STTP" not in codes and "SYMPOSIUM" not in codes
    assert all(row["activity_count"] >= 0 for row in rows)
    assert all(row["name"] for row in rows)


def test_departmental_category_master(client):
    rows = client.get("/api/departmental-categories").get_json()
    assert len(rows) == 7
    assert {row["code"] for row in rows} == {
        "ACHIEVEMENT", "RESEARCH", "INDUSTRY", "CLUB", "OUTREACH", "WORKSHOP", "CONFERENCE",
    }
    it_rows = client.get("/api/departmental-categories?department=Information%20Technology").get_json()
    assert {row["code"] for row in it_rows} == {"ACHIEVEMENT"}
    assert it_rows[0]["activity_count"] == 5
    civil_rows = client.get("/api/departmental-categories?department=Civil%20Engineering").get_json()
    assert {row["code"] for row in civil_rows} == {"RESEARCH", "WORKSHOP"}
    assert client.get("/api/departmental-categories?department=General").get_json() == []


EXPECTED_PUBLIC_DEPARTMENTS = (
    "Civil Engineering", "Chemistry", "Computer Science and Engineering",
    "Computer Science and Business Systems", "Computer Applications",
    "Applied Mathematics and Computational Science", "Artificial Intelligence",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering", "English",
    "Information Technology", "Mechanical Engineering", "Mechatronics",
    "T'SEDA (Architecture, Design, Planning)",
)
EXPECTED_PUBLIC_CATEGORY_CODES = {
    "ACHIEVEMENT", "RESEARCH", "INDUSTRY", "CLUB", "OUTREACH", "WORKSHOP",
    "CONFERENCE", "SEMINAR", "GUEST_LECTURE", "FDP", "HACKATHON", "CULTURAL",
    "SPORTS", "NCC", "NSS", "PLACEMENT", "INTERNSHIP", "ORIENTATION", "CAMPUS",
    "WEBINAR",
}


def test_departments_master_exactly_14_never_general(client):
    rows = client.get("/api/departments").get_json()
    names = [row["department"] for row in rows]
    assert [name for name in names] == list(EXPECTED_PUBLIC_DEPARTMENTS)
    assert len(rows) == 14
    for forbidden in ("General", "Fashion Technology", "Mathematics", "Physics", "Unknown", "Other"):
        assert forbidden not in names
    by_name = {row["department"]: row["activity_count"] for row in rows}
    assert by_name["Information Technology"] == 5
    assert by_name["Civil Engineering"] == 3
    assert sum(by_name.values()) == 8


def test_categories_report_only_public_master_codes(client):
    rows = client.get("/api/categories").get_json()
    codes = {row["code"] for row in rows}
    assert codes == EXPECTED_PUBLIC_CATEGORY_CODES
    assert len(rows) == 20
    for legacy in ("TECH_FEST", "STTP", "SYMPOSIUM", "ALUMNI"):
        assert legacy not in codes
    assert "scope" not in rows[0]
    assert "general_count" not in rows[0]
    assert "departmental_count" not in rows[0]


def test_analytics_never_expose_legacy_categories(client):
    overview = client.get("/api/analytics/overview").get_json()
    all_codes = {row["code"] for row in overview["category_totals"]}
    assert all_codes == EXPECTED_PUBLIC_CATEGORY_CODES
    trend = client.get("/api/analytics/categories?include_trend=1").get_json()
    trend_codes = {row["category_code"] for row in trend["year_category_breakdown"]}
    assert not (trend_codes & {"TECH_FEST", "STTP", "SYMPOSIUM", "ALUMNI"})
    general = client.get("/api/general-categories").get_json()
    departmental = client.get("/api/departmental-categories").get_json()
    assert not ({row["code"] for row in general} & {"TECH_FEST", "STTP", "SYMPOSIUM", "ALUMNI"})
    assert not ({row["code"] for row in departmental} & {"TECH_FEST", "STTP", "SYMPOSIUM", "ALUMNI"})


def test_general_analytics_is_institution_wide_only(client):
    body = client.get("/api/analytics/general").get_json()
    assert body["total_activities"] == 879
    assert sum(row["activity_count"] for row in body["period_breakdown"]) == 879
    assert len({(row["name"], row["code"]) for row in body["general_categories"]}) == 1
    assert body["general_categories"][0]["code"] == "WORKSHOP"
    assert body["general_categories"][0]["activity_count"] == 869
    assert "departmental_categories" not in body
    assert "departments" not in body


def test_department_analytics_overview_excludes_general(client):
    body = client.get("/api/analytics/department").get_json()
    names = {row["department"] for row in body["departments"]}
    assert names == set(EXPECTED_PUBLIC_DEPARTMENTS)
    assert "General" not in names
    assert body["total_activities"] == 8
    assert sum(row["activity_count"] for row in body["period_breakdown"]) == 8
    codes = {row["code"] for row in body["departmental_categories"]}
    assert codes == {"ACHIEVEMENT", "RESEARCH", "WORKSHOP"}
    assert not (codes & {"TECH_FEST", "STTP", "SYMPOSIUM"})


def test_department_analytics_filters_to_one_department(client):
    body = client.get(
        "/api/analytics/department?department=Information%20Technology").get_json()
    assert body["department"] == "Information Technology"
    assert body["total_activities"] == 5
    assert sum(row["activity_count"] for row in body["period_breakdown"]) == 5
    assert body["departmental_categories"] == [{
        "code": "ACHIEVEMENT", "name": "Achievement and Awards", "activity_count": 5}]
    assert body["year_category_breakdown"][0] == {
        "academic_year": "2024-25", "category_code": "ACHIEVEMENT",
        "category": "Achievement and Awards", "activity_count": 5}


def test_general_is_not_a_valid_department_analytics_option(client):
    assert client.get("/api/analytics/department?department=General").status_code == 400
    assert client.get("/api/analytics/department?department=Physics").status_code == 400


def test_department_filter_never_mixes_general(client):
    it = client.get(
        "/api/activities?department=Information%20Technology").get_json()
    assert it["total"] == 5
    assert {item["department"] for item in it["data"]} == {"Information Technology"}
    civil = client.get("/api/activities?department=Civil%20Engineering").get_json()
    assert civil["total"] == 3
    assert {item["department"] for item in civil["data"]} == {"Civil Engineering"}


def test_before_2021_presentation_survives_the_refactor(client):
    overview = client.get("/api/analytics/overview").get_json()
    periods = overview["period_breakdown"]
    assert {row["academic_year"] for row in periods} == {
        "2021-22", "2022-23", "2023-24", "2024-25", "2025-26", "Before 2021"}
    assert sum(row["activity_count"] for row in periods) == overview["total_activities"]


def test_public_analytics_uses_final_metadata(client):
    overview = client.get("/api/analytics/overview").get_json()
    assert overview["total_activities"] == 887
    assert {row["academic_year"]: row["activity_count"] for row in overview["yearly_breakdown"]} == {
        "2021-22": 46, "2022-23": 56, "2023-24": 105, "2024-25": 107, "2025-26": 6,
    }
    assert "activity_scopes" not in overview
    assert [row["code"] for row in overview["general_category_totals"]] == ["WORKSHOP"]
    assert overview["general_category_totals"][0]["activity_count"] == 869
    by_dept = {row["department"]: row for row in overview["departmental_category_totals"]}
    assert {"code": "ACHIEVEMENT", "name": "Achievement and Awards", "activity_count": 5} in by_dept["Information Technology"]["categories"]
    assert {row["code"] for row in by_dept["Civil Engineering"]["categories"]} == {"RESEARCH", "WORKSHOP"}
    categories = client.get("/api/analytics/categories?include_trend=1").get_json()
    assert categories["year_category_breakdown"]


def test_search(client):
    r = client.get("/api/search?q=workshop")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ok"
    titles = [i["title"] for i in body["data"]]
    assert any("Workshop" in t for t in titles)


def test_search_requires_q(client):
    assert client.get("/api/search").status_code == 400


def test_analytics_overview(client):
    r = client.get("/api/analytics/overview")
    assert r.status_code == 200
    body = r.get_json()
    assert body["total_activities"] >= 1
    assert isinstance(body["yearly_breakdown"], list)


def test_analytics_endpoints(client):
    for path in ("yearly", "departments", "categories", "stakeholders", "linkedin", "data-quality"):
        r = client.get(f"/api/analytics/{path}")
        assert r.status_code == 200, path
        body = r.get_json()
        assert body is not None, path


def test_review_queue_endpoint(client):
    r = client.get("/api/review?status=open")
    assert r.status_code == 200
    assert "items" in r.get_json()


def test_review_invalid_status(client):
    assert client.get("/api/review?status=bogus").status_code == 400


def test_review_approve(client):
    r = client.post("/api/review/1/approve", json={"reviewer": "api-test"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "approved"


def test_review_approve_missing(client):
    r = client.post("/api/review/9999/approve", json={"reviewer": "api-test"})
    assert r.status_code == 404


def test_review_edit_roundtrip(client):
    r = client.post("/api/review/1/edit",
                    json={"field": "venue", "value": "Main Auditorium", "reviewer": "api-test"})
    assert r.status_code == 200
    # Review writes remain available, but public activity reads never leak venue.
    assert "venue" not in client.get("/api/activities/1").get_json()


def test_linkedin_record(client):
    r = client.post("/api/review/1/linkedin",
                    json={"post_url": "https://www.linkedin.com/company/tcemadurai",
                          "reviewer": "api-test"})
    assert r.status_code == 200
    lk = client.get("/api/analytics/linkedin").get_json()
    assert lk["matched"] >= 1


def test_collection_run(client, tmp_path):
    isolated_raw = tmp_path / "raw"
    isolated_raw.mkdir()
    r = client.post("/api/collection/run", json={"raw_dir": str(isolated_raw)})
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "completed"
    assert isinstance(body["result"]["loaded"], int)


def test_query_post(client):
    r = client.post("/api/query", json={"question": "How many activities are there?"})
    assert r.status_code == 200
    body = r.get_json()
    assert "answer" in body


def test_query_get(client):
    r = client.get("/api/query?q=How%20many%20activities%20are%20there?")
    assert r.status_code == 200
    body = r.get_json()
    assert "answer" in body


def test_public_query_uses_final_metadata_and_hides_parser_details(client):
    total = client.post("/api/query", json={"question": "How many activities are there?"}).get_json()
    period = client.post("/api/query", json={"question": "How many activities were there in 2021-2022?"}).get_json()
    category = client.post("/api/query", json={"question": "How many workshops were conducted?"}).get_json()
    combined = client.post("/api/query", json={"question": "How many student workshops were there in 2021-2022?"}).get_json()
    assert total["count"] == 887
    assert period["count"] == 46
    assert category["count"] == 870
    assert combined["count"] == 46
    assert "intent" not in total and "filters" not in total
