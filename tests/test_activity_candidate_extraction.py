"""Step 3 offline extraction tests using deterministic archived-text fixtures."""

import json

import pytest

from backend.database.init_db import get_connection, init_db
from backend.extraction.activity_candidate_extractor import (
    ActivityCandidateExtractor, academic_year, extract_date, extract_departments,
    extract_stakeholders, extract_academic_year_context, split_activity_blocks,
)


@pytest.fixture
def extraction_env(tmp_path, monkeypatch):
    db_path = str(tmp_path / "extract.db")
    init_db(db_path)
    archive = tmp_path / "raw"; archive.mkdir()
    import backend.extraction.activity_candidate_extractor as module
    monkeypatch.setattr(module, "init_db", lambda: None)
    conn = get_connection(db_path)
    conn.execute("INSERT INTO collection_runs (status) VALUES ('completed')")
    run_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def add_source(name, text, source_type="html", title="Activities"):
        (archive / name).write_text(text, encoding="utf-8")
        conn.execute("""INSERT INTO raw_source_occurrences
          (collection_run_id,source_url,normalized_url,source_type,page_title,text_archive_path,extraction_status)
          VALUES (?,?,?,?,?,?,?)""", (run_id, f"https://www.tce.edu/{name}", f"https://www.tce.edu/{name}",
                                        source_type, title, name, "extracted"))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    yield conn, run_id, archive, add_source
    conn.close()


def test_academic_year_boundary():
    assert academic_year("2024-07-31") == "2023-24"
    assert academic_year("2024-08-01") == "2024-25"
    assert academic_year("2025-01-15") == "2024-25"
    assert academic_year("2025-08-01") == "2025-26"
    assert academic_year("2021-07-31") is None
    assert academic_year("2026-08-01") is None


@pytest.mark.parametrize("text, expected", [
    ("held on 15 March 2024", "2024-03-15"), ("held on 15/03/2024", "2024-03-15"),
    ("held on 15-03-2024", "2024-03-15"), ("March 15, 2024", "2024-03-15"),
    ("15 Mar 2024", "2024-03-15"), ("2024-03-15", "2024-03-15"),
])
def test_date_formats(text, expected):
    assert extract_date(text)[0] == expected


def test_year_only_is_preserved_without_an_invented_date():
    assert extract_date("2024. Alumni interaction was held.") == (None, "2024")


def test_explicit_academic_year_context_is_unambiguous_and_in_scope():
    assert extract_academic_year_context("Activities conducted during Academic Year 2023-24") == "2023-24"
    assert extract_academic_year_context("Annual Report 2024-2025") == "2024-25"
    assert extract_academic_year_context("Academic Year 2020-21") is None
    assert extract_academic_year_context("2024 Alumni Reunion") is None


def test_context_assigns_undated_record_but_not_plain_year(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("annual.txt", "Annual Report 2024-25. NSS workshop was conducted for students.")
    add("plain-year.txt", "2024 Alumni NSS workshop was conducted for students.")
    conn.commit()
    ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    years = [r[0] for r in conn.execute("SELECT academic_year FROM activity_candidates ORDER BY id")]
    assert "2024-25" in years and None in years


def test_year_at_start_is_not_a_numbered_list_marker():
    blocks = split_activity_blocks("2024. Alumni interaction was held for students.")
    assert blocks == ["2024. Alumni interaction was held for students."]


def test_split_three_activities_and_preserve_provenance(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("sports.txt", """Activities. Workshop on AI was conducted for students on 15 March 2024.
    Alumni interaction was held on 16 March 2024. Industry seminar was organized on 17 March 2024.""")
    conn.commit()
    result = ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert result["activity_candidates"] == 3
    rows = conn.execute("SELECT * FROM activity_candidates ORDER BY id").fetchall()
    assert len(rows) == 3
    assert all(r["source_occurrence_id"] and r["evidence_text"] and r["status"] == "PENDING" for r in rows)
    assert all(r["academic_year"] == "2023-24" for r in rows)


def test_department_and_stakeholder_evidence_only():
    departments, phrase = extract_departments("Department of Computer Applications conducted a session")
    assert departments == ["Computer Applications"] and phrase
    assert extract_departments("A workshop was conducted for students.")[0] == ["GENERAL"]
    stakeholders, _ = extract_stakeholders("Industry interaction with students and faculty")
    assert set(stakeholders) == {"INDUSTRY", "STUDENTS", "FACULTY"}


def test_non_activity_and_missing_values_do_not_create_candidates(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("contact.txt", "Contact the administrative office for fee payment and hostel information.", title="Contact")
    conn.commit()
    result = ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert result["activity_candidates"] == 0
    telemetry = conn.execute("SELECT extraction_status, contains_activity_evidence FROM source_extraction_telemetry").fetchone()
    assert tuple(telemetry) == ("SKIPPED", 0)


def test_page_title_alone_does_not_create_a_candidate(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("empty-ncc.txt", "Office contacts and fee information.", title="NCC Activities")
    conn.commit()
    result = ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert result["activity_candidates"] == 0


def test_policy_or_fee_source_is_not_treated_as_activity_evidence(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("research-policy.pdf.txt", "A workshop was conducted for students.", "pdf", "TCE Research Policy")
    conn.commit()
    result = ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert result["activity_candidates"] == 0


def test_hyphenated_policy_filename_is_non_activity_source():
    from backend.extraction.activity_candidate_extractor import source_is_non_activity
    assert source_is_non_activity("https://www.tce.edu/TCE-Research-Policy.pdf", "TCE-Research-Policy.pdf")


def test_pdf_text_source_is_processed(extraction_env):
    conn, run_id, archive, add = extraction_env
    add("newsletter.txt", "NSS Blood Donation Camp was organized on 20 August 2023 for students.", "pdf")
    conn.commit()
    result = ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert result["pdf_sources_processed"] == 1 and result["pdf_candidates"] == 1


def test_existing_activities_are_not_modified(extraction_env):
    conn, run_id, archive, add = extraction_env
    conn.execute("INSERT INTO institutional_activities (title, normalized_title) VALUES ('Existing', 'existing')")
    add("activity.txt", "NCC Camp was held on 10 August 2024 for cadets.")
    conn.commit()
    before = conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0]
    ActivityCandidateExtractor(conn=conn, archive_root=archive).run(collection_run_id=run_id)
    assert conn.execute("SELECT COUNT(*) FROM institutional_activities").fetchone()[0] == before
