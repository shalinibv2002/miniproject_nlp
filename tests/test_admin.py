"""Phase 10 tests: the protected Admin API (login, sessions, overview, CRUD)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import backend.database.init_db as init_db_mod
from backend.database import init_db
from backend.database.seed_reference_data import seed

_ORIGINAL_DB = init_db_mod.DATABASE_PATH


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("admin") / "admin_test.db")
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)
    conn = init_db_mod.get_connection(db_path=db)
    try:
        seed(conn=conn)
        workshop = conn.execute("SELECT id FROM categories WHERE code='WORKSHOP'").fetchone()["id"]
        achievement = conn.execute("SELECT id FROM categories WHERE code='ACHIEVEMENT'").fetchone()["id"]
        for index in range(3):
            cur = conn.execute(
                """INSERT INTO institutional_activities
                   (title, normalized_title, description, activity_date, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (f"Admin Seed Activity {index + 1}", f"admin seed activity {index + 1}",
                 "Seed record.", "2025-03-10", "https://www.tce.edu/seed"),
            )
            activity_id = cur.lastrowid
            conn.execute(
                """INSERT INTO final_activity_metadata
                   (activity_id, activity_date_text, academic_year, department_display,
                    stakeholder_display, achievement_outcome, evidence_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (activity_id, "10 March 2025", "2024-25", "General", "Students",
                 "Outcome", "Evidence"),
            )
            conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                         (activity_id, workshop))
        cur = conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, description, activity_date, source_url)
               VALUES (?, ?, ?, ?, ?)""",
            ("Seed Department Activity", "seed department activity",
             "A departmental record.", "2025-06-01", "https://www.tce.edu/dept"),
        )
        activity_id = cur.lastrowid
        conn.execute(
            """INSERT INTO final_activity_metadata
               (activity_id, activity_date_text, academic_year, department_display,
                stakeholder_display, achievement_outcome, evidence_text)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, "1 June 2025", "2025-26", "Information Technology", "Faculty",
             "Outcome", "Evidence"),
        )
        conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                     (activity_id, achievement))
        conn.execute("INSERT INTO activity_sources (activity_id, source_url) VALUES (?, ?)",
                     (activity_id, "https://www.tce.edu/dept"))
        conn.commit()
    finally:
        conn.close()

    from backend.app import create_app
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c
    init_db_mod.DATABASE_PATH = _ORIGINAL_DB


def _login(client, username="shalini", password="shalini02"):
    return client.post("/api/admin/login", json={"username": username, "password": password})


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_wrong_password(client):
    r = _login(client, password="wrong-password")
    assert r.status_code == 401
    assert r.get_json()["error"] == "Invalid username or password."


def test_login_missing_credentials(client):
    r = client.post("/api/admin/login", json={})
    assert r.status_code == 400


def test_login_and_session(client):
    body = _login(client).get_json()
    assert body["username"] == "shalini"
    token = body["token"]
    assert token

    no_auth = client.get("/api/admin/session").get_json()
    assert no_auth == {"authenticated": False}

    with_auth = client.get("/api/admin/session", headers=_headers(token)).get_json()
    assert with_auth == {"authenticated": True, "username": "shalini"}


def test_protected_endpoints_require_auth(client):
    for method, path, kwargs in (
        ("get", "/api/admin/overview", {}),
        ("get", "/api/admin/stakeholder-options", {}),
        ("get", "/api/admin/activities", {}),
        ("get", "/api/admin/activities/1", {}),
        ("post", "/api/admin/activities", {"json": {"title": "X"}}),
        ("delete", "/api/admin/activities/1", {}),
    ):
        r = getattr(client, method)(path, **kwargs)
        assert r.status_code == 401, path


def test_logout_revokes_token(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/logout", headers=_headers(token))
    assert r.status_code == 200
    after = client.get("/api/admin/overview", headers=_headers(token))
    assert after.status_code == 401


def test_overview(client):
    token = _login(client).get_json()["token"]
    body = client.get("/api/admin/overview", headers=_headers(token)).get_json()
    expected = {"total_activities", "general_activities", "departmental_activities",
                "period_breakdown", "category_totals", "department_totals",
                "records_requiring_attention", "recent_activities"}
    assert expected <= set(body)
    assert body["total_activities"] == 4
    assert body["general_activities"] == 3
    assert body["departmental_activities"] == 1
    assert body["records_requiring_attention"] >= 0


def test_stakeholder_options(client):
    token = _login(client).get_json()["token"]
    names = client.get("/api/admin/stakeholder-options",
                       headers=_headers(token)).get_json()["stakeholders"]
    assert "Students" in names
    assert "Faculty" in names


def test_list_activities(client):
    token = _login(client).get_json()["token"]
    body = client.get("/api/admin/activities", headers=_headers(token)).get_json()
    assert body["total"] == 4
    row = body["data"][0]
    assert set(row) >= {"id", "title", "department", "stakeholder", "academic_year",
                        "activity_date", "source_url", "categories"}
    assert "overall_confidence" not in row


def test_list_activities_filters(client):
    token = _login(client).get_json()["token"]
    headers = _headers(token)
    assert client.get("/api/admin/activities?department=General",
                      headers=headers).get_json()["total"] == 3
    assert client.get("/api/admin/activities?departmental_category=ACHIEVEMENT",
                      headers=headers).get_json()["total"] == 1
    assert client.get("/api/admin/activities?q=Department",
                      headers=headers).get_json()["total"] == 1


def test_activity_detail_prefill(client):
    token = _login(client).get_json()["token"]
    item = client.get("/api/admin/activities/4", headers=_headers(token)).get_json()
    assert item["scope"] == "departmental"
    assert item["department"] == "Information Technology"
    assert item["category"] == "ACHIEVEMENT"
    assert client.get("/api/admin/activities/9999", headers=_headers(token)).status_code == 404


def test_add_general_activity(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/activities", headers=_headers(token), json={
        "title": "New General Workshop", "scope": "general",
        "category": "WORKSHOP", "academic_year": "2024-25",
        "activity_date": "2025-02-02", "stakeholder": "Students",
        "description": "A fresh workshop.", "source_url": "https://www.tce.edu/new",
    })
    assert r.status_code == 201
    body = r.get_json()
    assert body["status"] == "created"
    assert body["links"] == 3  # category + source + stakeholder
    listed = client.get("/api/admin/activities?q=New General Workshop",
                        headers=_headers(token)).get_json()
    assert listed["total"] == 1
    assert listed["data"][0]["academic_year"] == "2024-25"
    assert listed["data"][0]["stakeholder"] == "Students"


def test_add_departmental_activity(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/activities", headers=_headers(token), json={
        "title": "New Dept Workshop", "scope": "departmental",
        "department": "Civil Engineering", "category": "WORKSHOP",
    })
    assert r.status_code == 201
    item = client.get(f"/api/admin/activities/{r.get_json()['activity_id']}",
                      headers=_headers(token)).get_json()
    assert item["department"] == "Civil Engineering"
    assert item["scope"] == "departmental"


def test_add_invalid_category(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/activities", headers=_headers(token), json={
        "title": "Bad Category", "scope": "general", "category": "SYMPOSIUM",
    })
    assert r.status_code == 400
    assert "general category" in r.get_json()["error"].lower()


def test_add_invalid_department(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/activities", headers=_headers(token), json={
        "title": "Bad Department", "scope": "departmental", "department": "General",
        "category": "WORKSHOP",
    })
    assert r.status_code == 400


def test_add_invalid_date(client):
    token = _login(client).get_json()["token"]
    r = client.post("/api/admin/activities", headers=_headers(token), json={
        "title": "Bad Date", "scope": "general", "category": "WORKSHOP",
        "activity_date": "02/03/2025",
    })
    assert r.status_code == 400
    assert "ISO date" in r.get_json()["error"]


def test_update_rewires_dimension(client):
    token = _login(client).get_json()["token"]
    headers = _headers(token)
    r = client.post("/api/admin/activities", headers=headers, json={
        "title": "Switchable Activity", "scope": "general", "category": "WORKSHOP",
    })
    activity_id = r.get_json()["activity_id"]

    updated = client.put(f"/api/admin/activities/{activity_id}", headers=headers, json={
        "title": "Now Departmental", "scope": "departmental",
        "department": "Mechanical Engineering", "category": "RESEARCH",
        "stakeholder": "Students", "academic_year": "2023-24",
        "activity_date": "2024-08-08",
    })
    assert updated.status_code == 200
    item = client.get(f"/api/admin/activities/{activity_id}", headers=headers).get_json()
    assert item["scope"] == "departmental"
    assert item["department"] == "Mechanical Engineering"
    assert item["category"] == "RESEARCH"
    assert item["academic_year"] == "2023-24"

    listed = client.get("/api/admin/activities?departmental_category=RESEARCH",
                        headers=headers).get_json()
    assert any(row["id"] == activity_id for row in listed["data"])
    general_workshops = client.get("/api/admin/activities?general_category=WORKSHOP",
                                   headers=headers).get_json()
    assert not any(row["id"] == activity_id for row in general_workshops["data"])


def test_update_not_found(client):
    token = _login(client).get_json()["token"]
    r = client.put("/api/admin/activities/9999", headers=_headers(token), json={
        "title": "Ghost", "scope": "general", "category": "WORKSHOP",
    })
    assert r.status_code == 404


def test_delete_removes_activity_and_links(client):
    token = _login(client).get_json()["token"]
    headers = _headers(token)
    r = client.post("/api/admin/activities", headers=headers, json={
        "title": "Doomed Activity", "scope": "departmental",
        "department": "Electronics and Communication Engineering",
        "category": "WORKSHOP", "source_url": "https://www.tce.edu/doomed",
    })
    activity_id = r.get_json()["activity_id"]

    deleted = client.delete(f"/api/admin/activities/{activity_id}", headers=headers)
    assert deleted.status_code == 200
    assert client.get(f"/api/admin/activities/{activity_id}", headers=headers).status_code == 404

    conn = init_db_mod.get_connection(db_path=init_db_mod.DATABASE_PATH)
    try:
        for table, column in (
            ("final_activity_metadata", "activity_id"),
            ("activity_categories", "activity_id"),
            ("activity_sources", "activity_id"),
            ("activity_stakeholders", "activity_id"),
            ("review_history", "activity_id"),
        ):
            count = conn.execute(
                f"SELECT COUNT(*) AS c FROM {table} WHERE {column} = ?",
                (activity_id,)).fetchone()["c"]
            assert count == 0, table
        dup = conn.execute(
            "SELECT COUNT(*) AS c FROM duplicate_candidates "
            "WHERE activity_id_a=? OR activity_id_b=?", (activity_id, activity_id)
        ).fetchone()["c"]
        assert dup == 0, "duplicate_candidates"
    finally:
        conn.close()


def test_delete_not_found(client):
    token = _login(client).get_json()["token"]
    r = client.delete("/api/admin/activities/9999", headers=_headers(token))
    assert r.status_code == 404