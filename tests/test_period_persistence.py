"""Tests that an academic period filter restricts analytics to one period.

These cover the period-persistence fix (Period -> Department -> Stakeholder ->
Activity); they are independent of any profile feature.
"""

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
    db = str(tmp_path_factory.mktemp("period_persistence") / "period_persistence_test.db")
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)

    conn = init_db_mod.get_connection(db_path=db)
    try:
        seed(conn=conn)
        workshop = conn.execute("SELECT id FROM categories WHERE code='WORKSHOP'").fetchone()["id"]
        achievement = conn.execute("SELECT id FROM categories WHERE code='ACHIEVEMENT'").fetchone()["id"]
        # General activities across two periods + one Information Technology activity.
        general_rows = [
            ("General 2024-25 A", "2024-25", "General", workshop),
            ("General 2024-25 B", "2024-25", "General", workshop),
            ("General 2021-22 A", "2021-22", "General", workshop),
        ]
        for title, year, department, category_id in general_rows:
            cur = conn.execute(
                """INSERT INTO institutional_activities (title, normalized_title, description, activity_date, source_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (title, title.lower(), "Seed.", "2025-03-10", "https://www.tce.edu/seed"),
            )
            activity_id = cur.lastrowid
            conn.execute(
                """INSERT INTO final_activity_metadata
                   (activity_id, activity_date_text, academic_year, department_display,
                    stakeholder_display, achievement_outcome, evidence_text)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (activity_id, "10 March 2025", year, department, "Students", "Outcome", "Evidence"),
            )
            conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                         (activity_id, category_id))
        cur = conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, description, activity_date, source_url)
               VALUES (?, ?, ?, ?, ?)""",
            ("IT Activity 2025-26", "it activity 2025-26", "Seed.", "2026-03-01",
             "https://www.tce.edu/seed"),
        )
        activity_id = cur.lastrowid
        conn.execute(
            """INSERT INTO final_activity_metadata
               (activity_id, activity_date_text, academic_year, department_display,
                stakeholder_display, achievement_outcome, evidence_text)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, "1 March 2026", "2025-26", "Information Technology",
             "Faculty", "Outcome", "Evidence"),
        )
        conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                     (activity_id, achievement))
        conn.execute("INSERT INTO activity_sources (activity_id, source_url) VALUES (?, ?)",
                     (activity_id, "https://www.tce.edu/seed"))
        conn.commit()
    finally:
        conn.close()

    from backend.app import create_app
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c
    init_db_mod.DATABASE_PATH = _ORIGINAL_DB


class TestPeriodPersistenceOnAnalytics:
    def _period_count(self, body, period):
        return next(row["activity_count"] for row in body["period_breakdown"]
                    if row["academic_year"] == period)

    def test_general_analytics_restricts_every_series_to_one_period(self, client):
        body = client.get("/api/analytics/general?academic_year=2024-25").get_json()
        assert body["total_activities"] == 2
        assert body["periods_covered"] == ["2024-25"]
        assert self._period_count(body, "2024-25") == 2
        for period in ("2021-22", "2022-23", "2023-24", "2025-26", "Before 2021"):
            assert self._period_count(body, period) == 0

    def test_department_analytics_restricts_to_one_period(self, client):
        body = client.get(
            "/api/analytics/department?department=Information%20Technology&academic_year=2025-26"
        ).get_json()
        assert body["department"] == "Information Technology"
        assert body["total_activities"] == 1
        assert self._period_count(body, "2025-26") == 1
        for period in ("2021-22", "2022-23", "2023-24", "2024-25", "Before 2021"):
            assert self._period_count(body, period) == 0
        assert all(row["academic_year"] == "2025-26"
                   for row in body["year_category_breakdown"])

    def test_department_overview_without_period_reports_all_periods(self, client):
        body = client.get("/api/analytics/department").get_json()
        assert body["total_activities"] == 1
        assert self._period_count(body, "2025-26") == 1

    def test_invalid_academic_year_is_rejected(self, client):
        assert client.get("/api/analytics/general?academic_year=1899-00").status_code == 400
        assert client.get("/api/analytics/department?academic_year=1899-00").status_code == 400

    def test_period_can_be_sent_as_period_alias(self, client):
        body = client.get("/api/analytics/general?period=2021-22").get_json()
        assert body["periods_covered"] == ["2021-22"]
        assert body["total_activities"] == 1