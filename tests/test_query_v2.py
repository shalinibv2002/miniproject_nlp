"""Query System V2 tests: the interpreter + executor pair gives grounded,
deterministic public answers for counts, periods, departments, categories,
stakeholders, rankings, superlatives, trends, breakdowns, compares and named
event details — always through the public response contract.

The fixture mirrors the live schema (institutional_activities +
final_activity_metadata + mapping tables) so tests exercise the production
code path exactly.
"""

import pytest

from backend.database.init_db import get_connection
from backend.database import init_db
from backend.database.seed_reference_data import seed
from backend.nlp.query_engine import answer_question

CSC = "Computer Science and Engineering"
ECE = "Electronics and Communication Engineering"
MECH = "Mechanical Engineering"
IT = "Information Technology"

ZERO_MESSAGE = "No matching activities were found for the selected criteria."


@pytest.fixture
def conn(tmp_path):
    """In-memory DB with 31 activities spanning periods, departments,
    categories, stakeholders and one named event."""
    p = tmp_path / "v2_test.db"
    init_db.init_db(str(p))
    conn = get_connection(db_path=str(p))
    seed(conn=conn)

    cat_ids = {}
    for code in ("WORKSHOP", "ACHIEVEMENT", "RESEARCH", "CONFERENCE",
                 "SEMINAR", "INDUSTRY", "OUTREACH"):
        row = conn.execute("SELECT id FROM categories WHERE code=?", (code,)).fetchone()
        cat_ids[code] = row["id"] if row else None

    def year_id(name):
        row = conn.execute("SELECT id FROM academic_years WHERE name=?", (name,)).fetchone()
        return row["id"] if row else None

    year_2324 = year_id("2023-2024")
    year_2425 = year_id("2024-2025")
    year_2526 = year_id("2025-2026")

    def add(title, date, yid, codes, dept_display, stakeholder, year_short):
        conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, activity_date, activity_year_id,
                overall_confidence, source_url)
               VALUES (?, ?, ?, ?, 0.9, ?)""",
            (title, title.lower(), date, yid, "https://www.tce.edu/test"),
        )
        aid = conn.execute("SELECT last_insert_rowid() AS i").fetchone()["i"]
        for code in codes:
            conn.execute(
                "INSERT INTO activity_categories (activity_id, category_id, is_primary) "
                "VALUES (?, ?, 1)", (aid, cat_ids[code]),
            )
        conn.execute(
            """INSERT INTO final_activity_metadata
               (activity_id, activity_date_text, academic_year, department_display,
                stakeholder_display, achievement_outcome)
               VALUES (?, ?, ?, ?, ?, NULL)""",
            (aid, date, year_short, dept_display, stakeholder),
        )
        return aid

    # Workshops: 3 in 2023-24, 2 in 2024-25, 1 in 2025-26, 1 before 2021.
    add("Python Bootcamp", "2023-09-01", year_2324, ["WORKSHOP"], CSC, "Students", "2023-24")
    add("Robotics Workshop", "2023-10-10", year_2324, ["WORKSHOP"], CSC, "Students", "2023-24")
    add("PCB Design Workshop", "2023-11-20", year_2324, ["WORKSHOP"], ECE, "Students", "2023-24")
    add("Cloud Computing Workshop", "2024-08-15", year_2425, ["WORKSHOP"], CSC, "Faculty", "2024-25")
    add("UX Workshop", "2024-09-05", year_2425, ["WORKSHOP"], ECE, "Students", "2024-25")
    add("IoT Workshop", "2025-02-02", year_2526, ["WORKSHOP"], CSC, "Students", "2025-26")
    add("Legacy Hardware Workshop", "2018-05-01", None, ["WORKSHOP"], MECH, "Students", None)

    # Achievements: IT 5 (3 in 2024-25), ECE 1, CSC 1, MECH 1.
    add("Best Project Award", "2023-10-05", year_2324, ["ACHIEVEMENT"], IT, "Students", "2023-24")
    add("Paper of the Year", "2023-12-10", year_2324, ["ACHIEVEMENT"], IT, "Faculty", "2023-24")
    add("IETE Best Chapter", "2024-09-15", year_2425, ["ACHIEVEMENT"], IT, "Students", "2024-25")
    add("Best Innovation Award", "2024-10-01", year_2425, ["ACHIEVEMENT"], IT, "Students", "2024-25")
    add("TCE Excellence Award", "2024-11-11", year_2425, ["ACHIEVEMENT"], IT, "Students", "2024-25")
    add("ECE Hackathon Winner", "2024-12-20", year_2425, ["ACHIEVEMENT"], ECE, "Students", "2024-25")
    add("CSE Rank Holder Award", "2025-01-30", year_2425, ["ACHIEVEMENT"], CSC, "Students", "2024-25")
    add("MECH Design Award", "2023-09-18", year_2324, ["ACHIEVEMENT"], MECH, "Faculty", "2023-24")

    # Research: CSC 3, MECH 2, ECE 1.
    add("Funded Research Project Alpha", "2024-06-10", year_2425, ["RESEARCH"], CSC, "Faculty", "2024-25")
    add("Patent Filed Orion", "2024-07-21", year_2425, ["RESEARCH"], CSC, "Faculty", "2024-25")
    add("Consultancy Engagement North", "2024-08-01", year_2425, ["RESEARCH"], ECE, "Faculty", "2024-25")
    add("Sponsored Project Beta", "2023-05-05", year_2324, ["RESEARCH"], CSC, "Faculty", "2023-24")
    add("Patent Filed Vega", "2024-09-30", year_2425, ["RESEARCH"], MECH, "Faculty", "2024-25")
    add("Consultancy Engagement South", "2024-10-22", year_2425, ["RESEARCH"], MECH, "Faculty", "2024-25")
    add("Research Project Epsilon", "2025-03-15", year_2526, ["RESEARCH"], CSC, "Faculty", "2025-26")

    # Conferences (3) and seminars (2).
    add("International Conference on AI", "2024-01-15", year_2425, ["CONFERENCE"], CSC, "Students", "2024-25")
    add("National Conference on Materials", "2023-08-20", year_2324, ["CONFERENCE"], MECH, "Students", "2023-24")
    add("IEEE Conference Talk", "2024-11-05", year_2425, ["CONFERENCE"], ECE, "Students", "2024-25")
    add("First Year Orientation Seminar", "2024-08-12", year_2425, ["SEMINAR"], IT, "Students", "2024-25")
    add("Placement Seminar", "2025-04-01", year_2526, ["SEMINAR"], CSC, "Students", "2025-26")

    # Industry Collaboration (2): stakeholder Industry reads are disambiguated.
    add("MoU Signing with TechCorp", "2024-05-20", year_2425, ["INDUSTRY"], CSC, "Industry", "2024-25")
    add("Industry Visit to FabCorp", "2024-11-18", year_2425, ["INDUSTRY"], ECE, "Students", "2024-25")

    # Institution-wide activity (dimension = general).
    add("National Service Scheme Camp", "2023-06-10", year_2324, ["OUTREACH"], "", "Students", "2023-24")

    # Named event for detail queries.
    add("Future Ready Seminar on Industry 5.0", "2024-11-10", year_2425, ["SEMINAR"], IT,
        "Students", "2024-25")

    conn.commit()
    return conn


def test_count_all(conn):
    r = answer_question("How many activities are there?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 31
    assert "31" in r["answer"]


def test_count_period(conn):
    r = answer_question("How many workshops happened in 2023-2024?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 3
    assert "2023-2024" in r["criteria"]


def test_count_category_stakeholder(conn):
    r = answer_question("How many student workshops were conducted?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 6
    assert "Workshops" in r["criteria"]
    assert "Students" in r["criteria"]


def test_count_stakeholder_faculty(conn):
    r = answer_question("How many faculty activities are there?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 10


def test_industry_category_not_stakeholder(conn):
    """'Industry' is the category, not the Industry stakeholder."""
    r = answer_question("How many industry activities are there?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 2
    assert "Industry Collaboration" in r["criteria"]
    assert "Industry" not in r["criteria"]


def test_count_before_2021(conn):
    r = answer_question("How many activities before 2021?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 1
    assert "Before 2021" in r["criteria"]


def test_count_general_dimension(conn):
    r = answer_question("How many general activities are there?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 1
    assert "General / institution-wide" in r["criteria"]


def test_highest_year_workshops(conn):
    r = answer_question("Which year had the most workshops?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 3
    assert "2023-2024" in r["answer"]
    assert len(r["activities"]) == 3
    assert len(r["comparison"]) == 5
    assert {"academic_year": "2023-24", "activity_count": 3} in r["comparison"]


def test_lowest_department_workshops(conn):
    r = answer_question("Which department had the fewest workshops?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 1
    assert "Mechanical Engineering" in r["answer"]
    assert r["rows"][0] == {"label": "Mechanical Engineering", "value": 1}
    assert r["chart"]["data"][0] == {"label": "Mechanical Engineering", "value": 1}


def test_highest_department_period(conn):
    r = answer_question("Which department had the highest achievements in 2024-2025?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 3
    assert "Information Technology" in r["answer"]
    assert "Achievement and Awards" in r["criteria"]
    assert "2024-2025" in r["criteria"]
    assert r["rows"][0] == {"label": "Information Technology", "value": 3}


def test_ranking_departments(conn):
    r = answer_question("Rank departments by number of achievements.", conn=conn)
    assert r["status"] == "answer"
    assert r["rows"][0] == {"label": "Information Technology", "value": 5}
    assert len(r["rows"]) == 14
    assert len(r["comparison"]) == 14
    assert r["comparison"][0]["department"] == "Information Technology"
    assert r["chart"]["data"][0] == {"label": "Information Technology", "value": 5}


def test_top_n(conn):
    r = answer_question("Top 3 departments by research activities.", conn=conn)
    assert r["status"] == "answer"
    assert r["rows"] == [
        {"label": "Computer Science and Engineering", "value": 4},
        {"label": "Mechanical Engineering", "value": 2},
        {"label": "Electronics and Communication Engineering", "value": 1},
    ]
    assert len(r["comparison"]) == 14


def test_trend(conn):
    r = answer_question("Show the year-wise trend of workshops.", conn=conn)
    assert r["status"] == "answer"
    assert len(r["rows"]) == 6
    labels = [row["label"] for row in r["rows"]]
    assert labels[0] == "2021-2022"
    assert labels[-1] == "Before 2021"
    assert {"label": "2023-2024", "value": 3} in r["rows"]
    assert {"label": "Before 2021", "value": 1} in r["rows"]
    assert len(r["comparison"]) == 5


def test_breakdown(conn):
    r = answer_question("Give me a department-wise breakdown of workshops.", conn=conn)
    assert r["status"] == "answer"
    active = [row for row in r["rows"] if row["value"] > 0]
    assert active == [
        {"label": "Computer Science and Engineering", "value": 4},
        {"label": "Electronics and Communication Engineering", "value": 2},
        {"label": "Mechanical Engineering", "value": 1},
    ]


def test_compare(conn):
    r = answer_question("Compare workshops vs conferences activities.", conn=conn)
    assert r["status"] == "answer"
    assert r["answer"] == "Workshops has more activities than Conference (7 vs 3)."
    assert r["count"] == 7
    assert r["comparison"] == [
        {"entity": "Workshops", "activity_count": 7},
        {"entity": "Conference", "activity_count": 3},
    ]


def test_detail(conn):
    r = answer_question("When was the Future Ready seminar conducted?", conn=conn)
    assert r["status"] == "answer"
    assert r["count"] == 1
    assert r["detail"]["title"] == "Future Ready Seminar on Industry 5.0"
    assert r["detail"]["academic_year"] == "2024-25"


def test_zero_result(conn):
    r = answer_question("How many conferences in 2021-2022?", conn=conn)
    assert r["status"] == "zero"
    assert r["count"] == 0
    assert r["answer"] == ZERO_MESSAGE
    assert r["criteria"] == ["Conference", "2021-2022"]


def test_unsupported(conn):
    r = answer_question("What is the weather in Madurai?", conn=conn)
    assert r["status"] == "unsupported"
    assert r["count"] == 0
    assert r["activities"] == []


def test_clarification(conn):
    r = answer_question("How many activities in 2026-2027?", conn=conn)
    assert r["status"] == "clarification"
    assert "2025-2026" in r["answer"]


def test_department_name_not_eaten_by_event_phrase(conn):
    """An event/department overlap must not strip the department filter."""
    r = answer_question("What faculty activities are in Information Technology?", conn=conn)
    assert r["status"] == "answer"
    assert "Information Technology" in r["criteria"]
    assert "Faculty" in r["criteria"]


def test_deterministic(conn):
    q = "Which department had the highest achievements in 2024-2025?"
    r1 = answer_question(q, conn=conn)
    r2 = answer_question(q, conn=conn)
    assert r1["answer"] == r2["answer"]
    assert r1["rows"] == r2["rows"]
    assert r1["comparison"] == r2["comparison"]


def test_queries_do_not_mutate(conn):
    before = conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0]
    for q in (
            "How many activities are there?",
            "Rank departments by number of achievements.",
            "Compare workshops vs conferences activities.",
            "When was the Future Ready seminar conducted?"):
        answer_question(q, conn=conn)
    after = conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0]
    assert after == before == 31


def test_no_internal_keys_leak(conn, monkeypatch):
    """The HTTP whitelist only exposes public fields, even for V2 answers."""
    from backend.app import create_app
    from backend.database import init_db
    db_path = conn.execute("PRAGMA database_list").fetchone()[2]
    monkeypatch.setattr(init_db, "DATABASE_PATH", db_path)
    app = create_app()
    with app.test_client() as client:
        resp = client.post("/api/query", json={
            "question": "Rank departments by number of achievements."})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["status"] == "answer"
        assert data["rows"][0]["label"] == "Information Technology"
        assert data["chart"]["data"][0]["value"] == 5
        forbidden = {"intent", "filters", "entities", "compare", "_note",
                     "classifier", "confidence", "sql", "model"}
        assert not forbidden.intersection(data.keys())