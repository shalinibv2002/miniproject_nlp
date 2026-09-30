"""Step 4 candidate-only classification tests."""

from backend.database.init_db import get_connection, init_db
from backend.nlp.candidate_classify import classify_candidates, classify_text


def test_existing_rule_categories_are_reused():
    assert classify_text("Workshop on Python") == ["WORKSHOP"]
    assert set(classify_text("NCC workshop on leadership")) == {"NCC", "WORKSHOP"}
    assert classify_text("Annual sports tournament") == ["SPORTS"]
    assert classify_text("Alumni reunion") == ["ALUMNI"]
    assert classify_text("Quiet reflective gathering") == []


def test_candidate_classification_preserves_candidate_and_hint(tmp_path, monkeypatch):
    path = str(tmp_path / "candidate-classify.db")
    init_db(path)
    import backend.nlp.candidate_classify as module
    monkeypatch.setattr(module, "init_db", lambda: None)
    conn = get_connection(path)
    try:
        conn.execute("INSERT INTO collection_runs (status) VALUES ('completed')")
        collection_run = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO extraction_runs (collection_run_id, status) VALUES (?, 'completed')", (collection_run,))
        extraction_run = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO raw_source_occurrences (collection_run_id,source_url,normalized_url,source_type)
                     VALUES (?,?,?,'html')""", (collection_run, "https://www.tce.edu/a", "https://www.tce.edu/a"))
        source = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""INSERT INTO activity_candidates (extraction_run_id,source_occurrence_id,title,description,
                     academic_year,category_hint,evidence_text,extraction_method,extraction_confidence)
                     VALUES (?,?,?,?,?,?,?,?,?)""", (extraction_run, source, "NCC Workshop", "Workshop for cadets",
                     "2024-25", "NCC", "NCC Workshop for cadets", "test", .8))
        candidate = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO institutional_activities (title,normalized_title) VALUES ('Existing','existing')")
        conn.commit()
        before = tuple(conn.execute("SELECT title, academic_year, category_hint FROM activity_candidates WHERE id=?", (candidate,)).fetchone())
        report = classify_candidates(conn, extraction_run)
        rows = conn.execute("SELECT final_category,category_hint,hint_match_status FROM candidate_classifications").fetchall()
        assert report["classified_candidates"] == 1 and report["multi_label_candidates"] == 1
        assert {r["final_category"] for r in rows} == {"NCC", "WORKSHOP"}
        assert next(r["hint_match_status"] for r in rows if r["final_category"] == "NCC") == "CONSISTENT"
        assert tuple(conn.execute("SELECT title, academic_year, category_hint FROM activity_candidates WHERE id=?", (candidate,)).fetchone()) == before
        assert conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0] == 1
    finally:
        conn.close()
