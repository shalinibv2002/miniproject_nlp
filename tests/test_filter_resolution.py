"""Regression tests for public filter resolution.

Covers the drill-down defects fixed in the stabilization pass:

  * ``category`` accepts the public display name the UI sends (``Workshops``),
    not only the stored code (``WORKSHOP``) / stored name (``Workshop``).
  * ``/api/categories`` honours ``period``/``department`` and returns public
    names, reconciling with ``/api/activities``.
  * ``/api/stakeholders`` honours the ``category`` filter.
  * ``department`` filtering normalises aliases inside multi-department rows
    ("IT; Architecture" must match Information Technology and T'SEDA).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import backend.database.init_db as init_db_mod
from backend.database import init_db
from backend.database.seed_reference_data import seed


@pytest.fixture
def client(tmp_path):
    db = str(tmp_path / "filter_resolution.db")
    previous = init_db_mod.DATABASE_PATH
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)
    conn = init_db_mod.get_connection(db_path=db)
    try:
        seed(conn=conn)

        def add(title, academic_year, department, stakeholder, category_code):
            cur = conn.execute(
                """INSERT INTO institutional_activities
                   (title, normalized_title, description, activity_date, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (title, title.lower(), "test", "2024-06-15", "https://www.tce.edu/x"),
            )
            activity_id = cur.lastrowid
            conn.execute(
                """INSERT INTO final_activity_metadata
                   (activity_id, activity_date_text, academic_year, department_display,
                    stakeholder_display, achievement_outcome, evidence_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (activity_id, "15 June 2024", academic_year, department, stakeholder,
                 "Outcome", "Evidence"),
            )
            category_id = conn.execute(
                "SELECT id FROM categories WHERE code=?", (category_code,)).fetchone()["id"]
            conn.execute(
                "INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                (activity_id, category_id))
            return activity_id

        add("General Workshop", "2024-25", "General", "Students", "WORKSHOP")
        add("IT Achievement", "2024-25", "Information Technology", "Students", "ACHIEVEMENT")
        add("IT Achievement 2025", "2025-26", "Information Technology", "Faculty", "ACHIEVEMENT")
        add("Multi Alias Workshop", "2024-25", "IT; Architecture", "Students", "WORKSHOP")
        add("General Achievement", "2024-25", "General", "Students", "ACHIEVEMENT")
        conn.commit()
    finally:
        conn.close()

    from backend.app import create_app
    app = create_app({"TESTING": True})
    try:
        with app.test_client() as c:
            yield c
    finally:
        init_db_mod.DATABASE_PATH = previous


def total(client, path):
    return client.get(path).get_json()["total"]


def test_category_public_name_matches_stored_code(client):
    assert total(client, "/api/activities?category=Workshops") == \
        total(client, "/api/activities?category=WORKSHOP")
    assert total(client, "/api/activities?category=Workshops") == 2
    assert total(client, "/api/activities?category=Achievement and Awards") == \
        total(client, "/api/activities?category=ACHIEVEMENT")


def test_activities_accepts_period_alias_consistent_with_analytics(client):
    by_year = total(client, "/api/activities?academic_year=2024-25&category=WORKSHOP")
    by_period = total(client, "/api/activities?period=2024-25&category=WORKSHOP")
    assert by_period == by_year == 2


def test_category_public_name_reconciles_with_categories_endpoint(client):
    rows = client.get("/api/categories?period=2024-25").get_json()
    by_code = {row["code"]: row for row in rows}
    assert by_code["WORKSHOP"]["name"] == "Workshops"
    assert by_code["ACHIEVEMENT"]["name"] == "Achievement and Awards"
    assert by_code["WORKSHOP"]["activity_count"] == \
        total(client, "/api/activities?academic_year=2024-25&category=WORKSHOP")
    assert len(rows) == 20


def test_categories_ignores_no_filter_but_honours_department(client):
    global_row = next(row for row in client.get("/api/categories?period=2024-25").get_json()
                      if row["code"] == "ACHIEVEMENT")
    it_row = next(row for row in client.get(
        "/api/categories?period=2024-25&department=Information%20Technology").get_json()
        if row["code"] == "ACHIEVEMENT")
    # Two 2024-25 achievements (one General, one IT); the 2025-26 IT
    # achievement and the multi-department workshop are out of this period.
    assert global_row["activity_count"] == 2
    assert it_row["activity_count"] == 1


def test_stakeholders_honours_category_filter(client):
    workshops = total(client, "/api/activities?category=Workshops")
    rows = client.get("/api/stakeholders?category=Workshops").get_json()
    assert sum(row["activity_count"] for row in rows) <= workshops
    # Only workshop stakeholders are counted, so the unfiltered list is larger.
    unfiltered = client.get("/api/stakeholders").get_json()
    assert sum(row["activity_count"] for row in rows) < \
        sum(row["activity_count"] for row in unfiltered)


def test_department_alias_equivalence_and_multi_department(client):
    assert total(client, "/api/activities?department=IT") == \
        total(client, "/api/activities?department=Information%20Technology")
    assert total(client, "/api/activities?department=IT") == 3  # 2 IT + 1 "IT; Architecture"
    tseda = client.get(
        "/api/activities?department=T%27SEDA%20(Architecture%2C%20Design%2C%20Planning)").get_json()
    assert tseda["total"] == 1
    assert tseda["data"][0]["title"] == "Multi Alias Workshop"


def test_department_resolver_consistent_with_departments_endpoint(client):
    it = next(row for row in client.get("/api/departments?period=2024-25").get_json()
              if row["department"] == "Information Technology")
    tseda = next(row for row in client.get("/api/departments?period=2024-25").get_json()
                 if row["department"] == "T'SEDA (Architecture, Design, Planning)")
    assert it["activity_count"] == 2  # 2024-25 IT + 2024-25 "IT; Architecture"
    assert tseda["activity_count"] == 1
