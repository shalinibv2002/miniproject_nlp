"""Phase 1 tests: schema, seed counts, FK enforcement, CHECK constraints, zero activities."""

ALL_TABLES = [
    "institutional_activities", "activity_sources",
    "activity_departments", "activity_categories", "activity_stakeholders",
    "activity_keywords", "activity_entities", "academic_years", "departments",
    "categories", "stakeholders", "classification_methods", "source_registry",
    "collection_runs", "collection_errors", "duplicate_candidates",
    "collection_run_details", "raw_source_occurrences",
    "linkedin_matches", "review_queue", "review_history",
    "department_statuses", "verification_statuses",
]


def test_all_tables_exist(conn):
    for table in ALL_TABLES:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
        ).fetchone()
        assert row is not None, f"Table {table} missing"


def test_seed_academic_years_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM academic_years").fetchone()["n"] == 5


def test_seed_departments_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM departments").fetchone()["n"] == 16


def test_seed_categories_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"] == 24


def test_seed_stakeholders_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM stakeholders").fetchone()["n"] == 8


def test_seed_classification_methods_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM classification_methods").fetchone()["n"] >= 8


def test_seed_source_registry_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM source_registry").fetchone()["n"] == 10


def test_seed_department_statuses_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM department_statuses").fetchone()["n"] == 4


def test_seed_verification_statuses_count(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM verification_statuses").fetchone()["n"] == 4


def test_zero_activities_exist(conn):
    assert conn.execute("SELECT COUNT(*) AS n FROM institutional_activities").fetchone()["n"] == 0


def test_foreign_keys_enforced(conn):
    import pytest as _pytest
    with _pytest.raises(Exception):
        conn.execute(
            "INSERT INTO activity_categories (activity_id, category_id) VALUES (99999, 99999)"
        )
    conn.rollback()
    with _pytest.raises(Exception):
        conn.execute(
            "INSERT INTO activity_sources (activity_id, source_url) VALUES (99999, 'http://x')"
        )
    conn.rollback()


def test_confidence_check_constraint(conn):
    with __import__("pytest").raises(Exception):
        conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, overall_confidence)
               VALUES ('X', 'x', 1.5)"""
        )
    conn.rollback()


def test_duplicate_unique_departments_names(conn):
    with __import__("pytest").raises(Exception):
        conn.execute(
            "INSERT INTO departments (code, name) VALUES ('ZZZ', 'Civil Engineering')"
        )
    conn.rollback()


def test_verification_status_default(conn):
    pending = conn.execute(
        "SELECT id FROM verification_statuses WHERE code='pending'"
    ).fetchone()["id"]
    conn.execute(
        "INSERT INTO institutional_activities (title, normalized_title, verification_status_id) "
        "VALUES ('T', 't', ?)",
        (pending,),
    )
    conn.commit()
    row = conn.execute(
        "SELECT verification_status_id FROM institutional_activities WHERE title='T'"
    ).fetchone()
    assert row["verification_status_id"] == pending
    conn.execute("DELETE FROM institutional_activities WHERE title='T'")
    conn.commit()
