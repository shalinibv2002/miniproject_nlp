"""Phase 21/24 tests: Before-2021 period presentation, resolution and NLQ.

These pin the public read-time period behaviour:
  * ``resolve_period`` never lets a real stored/evidence date slip before the
    five public periods (RULE 3) and never invents a period.
  * list/detail items never expose "Not available" as a public period.
  * the ``Before 2021`` filter and the NLQ "before 2021" phrasing count the
    resolved historical bucket, and never the 2021-22 period.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import backend.database.init_db as init_db_mod
from backend.database import init_db
from backend.database.seed_reference_data import seed
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, normalize_period, period_label,
    resolve_period, single_evidence_year, year_to_period,
)

_ORIGINAL_DB = init_db_mod.DATABASE_PATH

_YEARS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]


@pytest.fixture(scope="session")
def client(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("periods") / "periods_test.db")
    init_db_mod.DATABASE_PATH = db
    init_db.init_db(db)
    conn = init_db_mod.get_connection(db_path=db)
    try:
        seed(conn=conn)
        # A controlled universe: stored five-period rows, in-window evidence
        # rows, genuinely pre-2021 rows, and undated/ambiguous rows.
        staged = [
            ("Stored 2021-22", "2021-09-15", "2021-22", "15 September 2021",
             "Official evidence", 1),
            ("Stored 2024-25", "2024-06-15", "2024-25", "15 June 2024",
             "Official evidence", 1),
            ("Evidence 2022", None, None, "September 2022", "Seed money during 2022", 1),
            ("Evidence 2019", None, None, "10 March 2019", "NAAC 2019 cycle", 1),
            ("Old 2018", "2018-04-10", None, "10 April 2018", "Official", 1),
            ("Undated ambiguous", None, None, "September 2020 - 2021", "Multi period", 1),
            ("No date", None, None, None, None, 1),
            ("Patent number only", None, None, None, "Application 202441009072", 1),
        ]
        year_ids = {}
        for code in _YEARS:
            row = conn.execute("SELECT id FROM academic_years WHERE name=?", (code,)).fetchone()
            year_ids[code] = row["id"] if row else None
        for title, date, academic_year, date_text, evidence, count in staged:
            for i in range(count):
                cur = conn.execute(
                    """INSERT INTO institutional_activities
                       (title, normalized_title, description, activity_date, source_url)
                       VALUES (?, ?, ?, ?, ?)""",
                    (title, title.lower(), "period test", date,
                     "https://www.tce.edu/period"),
                )
                activity_id = cur.lastrowid
                conn.execute(
                    """INSERT INTO final_activity_metadata
                       (activity_id, activity_date_text, academic_year, department_display,
                        stakeholder_display, achievement_outcome, evidence_text)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (activity_id, date_text, academic_year, "General", "Students",
                     "Outcome", evidence),
                )
                cat = conn.execute("SELECT id FROM categories WHERE code='WORKSHOP'").fetchone()
                if cat:
                    conn.execute("INSERT INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                                 (activity_id, cat["id"]))
        conn.commit()
    finally:
        conn.close()

    from backend.app import create_app
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c
    init_db_mod.DATABASE_PATH = _ORIGINAL_DB


# ----------------------------------------------------------------------------
# Pure resolution rules
# ----------------------------------------------------------------------------

def test_period_label_maps_and_falls_back():
    assert period_label("2024-25") == "2024-2025"
    assert period_label("2023-24") == "2023-2024"
    assert period_label(BEFORE_2021) == BEFORE_2021
    assert period_label("garbage") == BEFORE_2021
    assert period_label(None) == BEFORE_2021


def test_normalize_period_accepts_public_spellings():
    assert normalize_period("2024-25") == "2024-25"
    assert normalize_period("2024-2025") == "2024-25"
    assert normalize_period("Before 2021") == BEFORE_2021
    assert normalize_period("before 2021") == BEFORE_2021
    assert normalize_period("prior to 2021") == BEFORE_2021
    assert normalize_period("garbage", default=None) is None


def test_year_to_period_clamps():
    assert year_to_period(2019) == BEFORE_2021
    assert year_to_period(2020) == BEFORE_2021
    assert year_to_period(2021) == "2021-22"
    assert year_to_period(2022) == "2022-23"
    assert year_to_period(2023) == "2023-24"
    assert year_to_period(2024) == "2024-25"
    assert year_to_period(2025) == "2025-26"
    assert year_to_period(2026) == "2025-26"


def test_single_evidence_year_skips_spans_and_ids():
    assert single_evidence_year("September 2022", "Seed money during 2022") == 2022
    assert single_evidence_year("2020 - 2021", "Multi") is None
    assert single_evidence_year("Application 202441009072") is None
    assert single_evidence_year("2023 to 2025", "range") is None
    assert single_evidence_year("January 2024", "") == 2024


def test_resolve_period_authority_order():
    # Stored five-period year is authoritative over a conflicting date.
    assert resolve_period(academic_year="2024-25", activity_date="2024-06-15") == "2024-25"
    # Stored date wins over ambiguous evidence.
    assert resolve_period(academic_year=None, activity_date="2018-04-10",
                          activity_date_text=None, evidence_text=None) == BEFORE_2021
    # Real structured date wins for in-window years.
    assert resolve_period(academic_year=None, activity_date="2024-06-15") == "2024-25"
    # Evidence single year wins when no date.
    assert resolve_period(academic_year=None, activity_date=None,
                          activity_date_text="10 March 2019", evidence_text=None) == BEFORE_2021
    assert resolve_period(academic_year=None, activity_date=None,
                          activity_date_text="September 2022", evidence_text=None) == "2022-23"
    # Ambiguous/empty stays in Before 2021.
    assert resolve_period(academic_year=None, activity_date=None,
                          activity_date_text="September 2020 - 2021", evidence_text=None) == BEFORE_2021
    assert resolve_period(academic_year=None, activity_date=None,
                          activity_date_text=None, evidence_text="Application 202441009072") == BEFORE_2021


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------

def test_activity_items_never_expose_not_available_period(client):
    body = client.get("/api/activities?page_size=100").get_json()
    assert body["pagination"]["total"] == 8
    for item in body["data"]:
        assert item["academic_year"] in (*_YEARS, BEFORE_2021)
        assert item["academic_year"] != "Not available"


def test_before_2021_filter_returns_only_historical_rows(client):
    rows = client.get("/api/activities?academic_year=Before%202021&page_size=100").get_json()
    assert rows["total"] == 5
    titles = sorted(item["title"] for item in rows["data"])
    assert titles == ["Evidence 2019", "No date", "Old 2018", "Patent number only",
                      "Undated ambiguous"]


def test_before_2021_filter_accepts_label_spelling(client):
    rows = client.get("/api/activities?academic_year=prior%20to%202021&page_size=100").get_json()
    assert rows["total"] == 5


def test_legacy_not_available_filter_still_maps_to_null(client):
    rows = client.get("/api/activities?academic_year=Not%20available&page_size=100").get_json()
    assert rows["total"] == 6  # every row without a stored public year, regardless of resolution


def test_short_period_filter_uses_resolved_ids(client):
    rows = client.get("/api/activities?academic_year=2021-22&page_size=100").get_json()
    assert rows["total"] == 1
    assert rows["data"][0]["title"] == "Stored 2021-22"


def test_detail_period_is_resolved(client):
    detail = client.get("/api/activities/1").get_json()
    assert detail["academic_year"] == "2021-22"
    rows = client.get("/api/activities?page_size=100").get_json()
    evidence_2022 = next(item for item in rows["data"] if item["title"] == "Evidence 2022")
    assert evidence_2022["academic_year"] == "2022-23"


def test_overview_period_breakdown_counts_every_activity_once(client):
    overview = client.get("/api/analytics/overview").get_json()
    breakdown = {row["academic_year"]: row["activity_count"] for row in overview["period_breakdown"]}
    assert set(breakdown) == {*_YEARS, BEFORE_2021}
    assert sum(breakdown.values()) == overview["total_activities"] == 8
    assert breakdown["2021-22"] == 1
    assert breakdown["2022-23"] == 1
    assert breakdown["2023-24"] == 0
    assert breakdown["2024-25"] == 1
    assert breakdown["2025-26"] == 0
    assert breakdown[BEFORE_2021] == 5


# ----------------------------------------------------------------------------
# NLQ
# ----------------------------------------------------------------------------

def test_public_query_before_2021_never_answers_2021_22(client):
    r = client.post("/api/query", json={"question": "How many activities were there before 2021?"}).get_json()
    assert r["count"] == 5
    assert "5" in r["answer"]


def test_public_query_prior_to_2021(client):
    r = client.post("/api/query", json={"question": "List the activities prior to 2021."}).get_json()
    assert r["count"] == 5
    assert "intent" not in r


def test_public_query_2021_2022_still_answers_that_period(client):
    r = client.post("/api/query", json={"question": "How many activities were there in 2021-22?"}).get_json()
    assert r["count"] == 1
    assert "1" in r["answer"]