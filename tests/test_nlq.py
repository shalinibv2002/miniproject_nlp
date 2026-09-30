"""Phase 12 tests: NLQ parses intents and answers safely with real rows.

Small in-memory DB mirrors the real schema: activities, categories,
departments, stakeholders, academic years, plus the mapping tables.
"""

import pytest

from backend.database.init_db import get_connection
from backend.database import init_db
from backend.database.seed_reference_data import seed
from backend.nlp.query_parser import parse_question, normalize_year, detect_intent
from backend.nlp.query_engine import answer_question


@pytest.fixture
def conn(tmp_path):
    p = tmp_path / "nlq_test.db"
    init_db.init_db(str(p))
    conn = get_connection(db_path=str(p))
    seed(conn=conn)
    _CATS = {
        "SPORTS": "Sports and Games",
        "NCC": "NCC Activity",
        "FDP": "Faculty Development Programme",
        "CONFERENCE": "Conference",
        "WORKSHOP": "Workshop",
    }
    cat_ids = {}
    for code, name in _CATS.items():
        row = conn.execute("SELECT id FROM categories WHERE code=?", (code,)).fetchone()
        cat_ids[code] = row["id"] if row else None

    dept_ids = {
        code: conn.execute("SELECT id FROM departments WHERE code=?", (code,)).fetchone()["id"]
        for code in ("CSE", "MECH", "EEE")
    }
    year_2324 = conn.execute("SELECT id FROM academic_years WHERE name='2023-2024'").fetchone()["id"]
    year_2425 = conn.execute("SELECT id FROM academic_years WHERE name='2024-2025'").fetchone()["id"]

    def add(title, date, year_id, cats, depts=None):
        conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, activity_date, activity_year_id, overall_confidence)
               VALUES (?, ?, ?, ?, 0.9)""",
            (title, title.lower(), date, year_id),
        )
        aid = conn.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
        for code in cats:
            conn.execute(
                "INSERT INTO activity_categories (activity_id, category_id, is_primary) VALUES (?, ?, 1)",
                (aid, cat_ids[code]),
            )
        for code in (depts or ()):
            conn.execute(
                "INSERT INTO activity_departments (activity_id, department_id, is_primary) VALUES (?, ?, 1)",
                (aid, dept_ids[code]),
            )
        return aid

    add("Inter-Department Sports Meet", "2024-02-10", year_2324, ["SPORTS"], ["CSE", "MECH"])
    add("NCC Annual Camp", "2024-03-05", year_2324, ["NCC"])
    add("NCC CATC Training", "2024-09-12", year_2425, ["NCC"])
    add("AI Faculty Development Programme", "2024-11-01", year_2425, ["FDP"])
    add("Deep Learning Workshop", "2025-01-20", year_2425, ["WORKSHOP"], ["CSE"])
    conn.commit()
    return conn


def test_normalize_year_formats():
    assert normalize_year("in 2024-2025") == (2024, 2025)
    assert normalize_year("academic year 2023-24") == (2023, 2024)
    assert normalize_year("during 2024") == (2024, 2025)
    assert normalize_year("no year here") is None


def test_detect_intent():
    assert detect_intent("How many NCC activities were there?") == "count"
    assert detect_intent("List the NCC activities.") == "list"
    assert detect_intent("Compare workshop vs conference counts.") == "compare"


def test_parse_sports_2023_24(conn):
    p = parse_question("How many sports activities were there in 2023-24?", conn=conn)
    assert p["intent"] == "count"
    assert p["filters"]["category"] == "SPORTS"
    assert p["filters"]["year"] == (2023, 2024)


def test_parse_ncc_count(conn):
    p = parse_question("How many NCC activities were held?", conn=conn)
    assert p["filters"]["category"] == "NCC"
    assert p["intent"] == "count"


def test_count_sports_2023_24(conn):
    r = answer_question("How many sports activities were there in 2023-24?", conn=conn)
    assert r["count"] == 1
    assert "1" in r["answer"]


def test_count_ncc(conn):
    r = answer_question("How many NCC activities were there?", conn=conn)
    assert r["count"] == 2
    assert r["activities"] and len(r["activities"]) == 2


def test_list_fdp_2024_25(conn):
    r = answer_question("List the FDPs in 2024-25.", conn=conn)
    assert r["intent"] == "list"
    assert r["count"] == 1
    assert any("AI Faculty Development" in a["title"] for a in r["activities"])


def test_department_comparison(conn):
    r = answer_question("Compare CSE vs MECH activities.", conn=conn)
    assert r["intent"] == "compare"
    assert "CSE" in r["answer"] or "MECH" in r["answer"]


def test_unmapped_year_is_honest(conn):
    r = answer_question("How many NCC activities in 2026-2027?", conn=conn)
    assert r["count"] == 0
    assert "_note" in r["filters"]


def test_year_filter_honest_when_bucket_missing(conn):
    r = answer_question("How many FDPs were there in 2020-2021?", conn=conn)
    assert r["count"] == 0


def test_no_freeform_sql_injection(conn):
    # Curly braces / quotes in the question must not break or alter SQL.
    r = answer_question("How many activities; DROP TABLE institutional_activities;?", conn=conn)
    assert r["count"] == 5  # still answers normally, nothing dropped
    assert conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0] == 5


# ------------------------------------------------------------------
# Public-path fixture: uses final_activity_metadata so _public_answer
# is exercised (production code path).
# ------------------------------------------------------------------

@pytest.fixture
def pub_conn(tmp_path):
    """In-memory DB with final_activity_metadata populated."""
    p = tmp_path / "pub_nlq_test.db"
    init_db.init_db(str(p))
    conn = get_connection(db_path=str(p))
    seed(conn=conn)

    cat_ids = {}
    for code in ("SPORTS", "WORKSHOP", "FDP", "NCC"):
        row = conn.execute("SELECT id FROM categories WHERE code=?", (code,)).fetchone()
        cat_ids[code] = row["id"] if row else None

    dept_ids = {}
    for code in ("CSE", "MBA", "MECH"):
        row = conn.execute("SELECT id FROM departments WHERE code=?", (code,)).fetchone()
        if row:
            dept_ids[code] = row["id"]

    year_2324 = conn.execute("SELECT id FROM academic_years WHERE name='2023-2024'").fetchone()["id"]
    year_2425 = conn.execute("SELECT id FROM academic_years WHERE name='2024-2025'").fetchone()["id"]

    def add(title, date, year_id, cats, depts=None, stakeholder=None, academic_year_short=None):
        conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, activity_date, activity_year_id, overall_confidence,
                source_url)
               VALUES (?, ?, ?, ?, 0.9, ?)""",
            (title, title.lower(), date, year_id, "https://www.tce.edu/test"),
        )
        aid = conn.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
        for code in cats:
            conn.execute(
                "INSERT INTO activity_categories (activity_id, category_id, is_primary) VALUES (?, ?, 1)",
                (aid, cat_ids[code]),
            )
        for code in (depts or ()):
            conn.execute(
                "INSERT INTO activity_departments (activity_id, department_id, is_primary) VALUES (?, ?, 1)",
                (aid, dept_ids[code]),
            )
        dept_display = depts[0] if depts else "General"
        conn.execute(
            """INSERT INTO final_activity_metadata
               (activity_id, activity_date_text, academic_year, department_display,
                stakeholder_display, achievement_outcome)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (aid, date, academic_year_short, dept_display, stakeholder, None),
        )
        return aid

    add("Inter-Department Sports Meet", "2024-02-10", year_2324, ["SPORTS"], ["CSE"],
        stakeholder="Students", academic_year_short="2023-24")
    add("NCC Annual Camp", "2024-03-05", year_2324, ["NCC"], [],
        stakeholder="Students", academic_year_short="2023-24")
    add("NCC CATC Training", "2024-09-12", year_2425, ["NCC"], [],
        stakeholder="Faculty", academic_year_short="2024-25")
    add("AI Faculty Development Programme", "2024-11-01", year_2425, ["FDP"], ["MBA"],
        stakeholder="Faculty", academic_year_short="2024-25")
    add("Deep Learning Workshop", "2025-01-20", year_2425, ["WORKSHOP"], ["CSE"],
        stakeholder="Students", academic_year_short="2024-25")
    conn.commit()
    return conn


def test_stakeholder_count(pub_conn):
    """Stakeholder filter returns grounded count from the database."""
    r = answer_question("How many student activities are there?", conn=pub_conn)
    assert r["count"] == 3
    assert "3" in r["answer"]


def test_department_category_combined(pub_conn):
    """Department + category filters combine correctly."""
    r = answer_question("How many sports activities are in CSE?", conn=pub_conn)
    assert r["count"] == 1


def test_department_stakeholder_combined(pub_conn):
    """Department + stakeholder filters combine correctly."""
    r = answer_question("What faculty activities are in MBA?", conn=pub_conn)
    assert r["count"] == 1
    assert any("Faculty Development" in a["title"] for a in r["activities"])


def test_zero_result_public_query(pub_conn):
    """Valid query with zero results returns an honest message."""
    r = answer_question("How many sports activities in 2025-2026?", conn=pub_conn)
    assert r["count"] == 0
    assert "No matching activities were found" in r["answer"]


def test_unsupported_question(pub_conn):
    """Unrelated question is rejected, not answered from general knowledge."""
    r = answer_question("What is the weather in Madurai?", conn=pub_conn)
    assert r["status"] == "unsupported"
    assert r["count"] == 0
    assert len(r.get("activities", [])) == 0


def test_ambiguous_entity(pub_conn):
    """Ambiguous/unmatched entity gets a safe response, not a guess."""
    r = answer_question("How many activities in XYZ department?", conn=pub_conn)
    # No department matched → either all activities or unsupported
    # The system must not crash or invent data.
    assert isinstance(r["count"], int)
    assert isinstance(r["answer"], str)


def test_no_internal_fields_in_public_response(pub_conn):
    """The route filters out internal fields; only public keys are returned."""
    from backend.app import create_app
    app = create_app()
    with app.test_client() as client:
        resp = client.post("/api/query", json={"question": "How many activities?"})
        data = resp.get_json()
        # Only allowed public keys
        forbidden = {"intent", "filters", "entities", "compare", "_note",
                      "classifier", "confidence", "sql", "model"}
        assert not forbidden.intersection(data.keys()), \
            f"Internal keys leaked: {forbidden.intersection(data.keys())}"


def test_deterministic_repeated_query(pub_conn):
    """Same question asked twice produces identical answers."""
    q = "How many sports activities were there in 2023-2024?"
    r1 = answer_question(q, conn=pub_conn)
    r2 = answer_question(q, conn=pub_conn)
    assert r1["count"] == r2["count"]
    assert r1["answer"] == r2["answer"]
    assert len(r1["activities"]) == len(r2["activities"])


def test_period_comparison_superlative(pub_conn):
    """'Which period has the most activities?' triggers comparison table."""
    r = answer_question("Which period has the most activities?", conn=pub_conn)
    assert "comparison" in r
    assert len(r["comparison"]) == 5
    # All periods present
    years = [c["academic_year"] for c in r["comparison"]]
    assert "2023-24" in years
    assert "2024-25" in years


def test_short_alias_it_resolves_to_department():
    """A short all-caps alias must resolve; lowercase prose must not."""
    from backend.nlp.query_interpreter import resolve_department

    assert resolve_department(
        "How many achievements did IT have in 2025-2026?", None) == "Information Technology"
    assert resolve_department("Give me the activities", None) is None