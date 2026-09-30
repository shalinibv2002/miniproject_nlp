"""Tests for the LinkedIn manual-review / validation module.

These tests exercise ``backend.database.linkedin_review`` (review layer only):
the candidate-generation database and the production database are never
touched by anything here.
"""

import pytest

from backend.database import linkedin_candidates as cand
from backend.database import linkedin_review as rev
from backend.database.linkedin_staging import get_staging_connection, init_staging_schema


def _post(post_id, text):
    return {
        "id": post_id,
        "post_url": "https://www.linkedin.com/posts/tcemadurai_x",
        "post_text": text,
        "source_sheet": "June 2025-June 2026",
        "source_row": post_id,
    }


def _classified(text):
    """Run a text through the classifier and return the candidate record."""
    return cand.classify_post(_post(1, text))


def _rec(status=cand.STATUS_ACTIVITY_CANDIDATE, cats=(), depts=(), staks=(),
         text="", date_status="undated", dates=None, earliest=None, ay=None,
         flags=None, comm=None, multi=0, cat_ev=None, dept_ev=None,
         stak_ev=None, reason=""):
    return {
        "linkedin_post_id": 1,
        "post_url": "https://www.linkedin.com/posts/tcemadurai_x",
        "post_text": text,
        "source_sheet": "June 2025-June 2026",
        "source_row": 1,
        "candidate_status": status,
        "is_activity": 1 if status == cand.STATUS_ACTIVITY_CANDIDATE else 0,
        "kind": cand.KIND_EVENT,
        "category_candidates": list(cats),
        "department_candidates": list(depts),
        "stakeholder_candidates": list(staks),
        "date_status": date_status,
        "date_evidence": {"source": "explicit_text",
                          "dates": list(dates or []),
                          "earliest": earliest},
        "academic_year": ay,
        "category_evidence": dict(cat_ev or {}),
        "department_evidence": dict(dept_ev or {}),
        "stakeholder_evidence": dict(stak_ev or {}),
        "communication_type": comm,
        "communication_evidence": {} if comm is None
        else {comm: ["sample mention"]},
        "evidence_score": 5,
        "multi_label": multi,
        "flags": list(flags or []),
        "reason": reason,
    }


@pytest.fixture()
def staging_conn(tmp_path):
    path = str(tmp_path / "staging.db")
    conn = get_staging_connection(path)
    init_staging_schema(conn)
    yield conn
    conn.close()


def _insert_post(conn, post_id, text):
    conn.execute(
        "INSERT INTO linkedin_posts (id, post_text, normalized_text, source_sheet, source_row, post_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (post_id, text, text, "June 2025-June 2026", post_id,
         "https://www.linkedin.com/posts/tcemadurai_%d" % post_id),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Over-tag attention (group B)
# ---------------------------------------------------------------------------

def test_achievement_mention_only_is_dropped_not_flagged():
    # STEP-11 strict classification: mention-style ACHIEVEMENT is dropped from
    # the decision (the gate flag keeps the audit trail), so the review layer
    # no longer sees an over-tagged ACHIEVEMENT here.
    rec = _classified(
        "Congratulations to the placement cell! Certified students get a "
        "certificate of participation in the career fair at TCE Madurai.")
    assert rec["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "ACHIEVEMENT" not in rec["category_candidates"]
    assert "PLACEMENT" in rec["category_candidates"]
    assert "category_gate:ACHIEVEMENT" in rec["flags"]
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "cat_over_tag:ACHIEVEMENT" for p in props)


def test_achievement_with_strong_word_not_flagged():
    rec = _classified(
        "Our team won the National Robotics Championship and received a "
        "gold medal at Thiagarajar College of Engineering, Madurai.")
    assert "ACHIEVEMENT" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "cat_over_tag:ACHIEVEMENT" for p in props)


def test_alumni_feature_post_not_flagged():
    rec = _classified(
        "#AlumniSpotlight Proud to celebrate an outstanding alumnus who is a "
        "product lead at TCS. Great journey from TCE Madurai to industry.")
    assert "ALUMNI" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert not any(p["rule"].startswith("cat_over_tag:ALUMNI") for p in props)


def test_internship_with_year_not_flagged():
    rec = _classified(
        "Internship 2026 at TCE Madurai - a 6 month internship programme for "
        "final year students with industry mentors.")
    assert "INTERNSHIP" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert not any(p["rule"].startswith("cat_over_tag:INTERNSHIP") for p in props)


def test_internship_mention_no_date_flagged():
    rec = _classified(
        "Our campus offers internship training, research labs and placement "
        "support for every student joining TCE Madurai.")
    assert rec["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "INTERNSHIP" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert any(p["rule"].startswith("cat_over_tag:INTERNSHIP") for p in props)


def test_research_mention_only_flagged():
    rec = _classified(
        "A proud moment for TCE Madurai: our sustainability drive is now "
        "recognised nationally with research being a key focus area.")
    assert "RESEARCH" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert any(p["rule"] == "cat_over_tag:RESEARCH" for p in props)


# ---------------------------------------------------------------------------
# Department generic-technical-term over-inference (group C)
# ---------------------------------------------------------------------------

def test_department_generic_term_only_flagged():
    rec = _classified(
        "Machine Learning Workshop for students and faculty organised at "
        "Thiagarajar College of Engineering, Madurai.")
    assert "Artificial Intelligence" in rec["department_candidates"]
    group, props = rev.validate_record(rec)
    assert group == "C"
    ai = [p for p in props if p["rule"] == "dept_generic_term"
          and p["current"] == "Artificial Intelligence"]
    assert ai and ai[0]["confidence"] == "low"


def test_department_explicit_not_flagged():
    rec = _classified(
        "Workshop on Machine Learning organised by the Department of "
        "Artificial Intelligence at Thiagarajar College of Engineering, Madurai.")
    assert "Artificial Intelligence" in rec["department_candidates"]
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "dept_generic_term" for p in props)


def test_department_generic_with_explicit_other_is_medium():
    rec = _classified(
        "Seminar on machine learning for students organised by the Department "
        "of Computer Science and Engineering at TCE Madurai.")
    assert "Artificial Intelligence" in rec["department_candidates"]
    assert "Computer Science and Engineering" in rec["department_candidates"]
    group, props = rev.validate_record(rec)
    ai = [p for p in props if p["rule"] == "dept_generic_term"
          and p["current"] == "Artificial Intelligence"]
    assert ai and ai[0]["confidence"] == "medium"


# ---------------------------------------------------------------------------
# Stakeholder isolated-word over-inference (group D)
# ---------------------------------------------------------------------------

def test_stakeholder_isolated_year_range_flagged():
    rec = _rec(cats=["CAMPUS"], staks=["Alumni"],
               text="B.E. ECE (2002-2006) proud alumnus honouree at an "
                    "annual event at TCE Madurai.",
               stak_ev={"Alumni": {"19\\d\\d[- ]20\\d\\d": ["2002-2006"]}})
    group, props = rev.validate_record(rec)
    assert group == "D"
    assert any(p["rule"] == "stakeholder_isolated" for p in props)


# ---------------------------------------------------------------------------
# Embedded event inside a communication post (group F)
# ---------------------------------------------------------------------------

def test_embedded_event_in_promo_is_promoted():
    rec = _classified(
        "Admissions open 2026! Also a 3-Day Workshop on Robotics on "
        "2026-02-10 and internship opportunities for students at TCE Madurai.")
    assert rec["candidate_status"] == cand.STATUS_NON_ACTIVITY
    assert rec["communication_type"] == "admission_promo"
    assert "WORKSHOP" in rec["category_evidence"]
    group, props = rev.validate_record(rec)
    assert group == "F"
    event = [p for p in props if p["rule"] == "embedded_event_possible"]
    assert event and event[0]["field"] == "status"
    assert event[0]["is_correction"]


def test_facility_word_not_an_embedded_event():
    rec = _classified(
        "Admissions open 2026 at TCE Madurai. We offer internship training, "
        "placement support, seminar halls and workshop laboratories for students.")
    assert rec["candidate_status"] == cand.STATUS_NON_ACTIVITY
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "embedded_event_possible" for p in props)


# ---------------------------------------------------------------------------
# Multi-label overlap (group B)
# ---------------------------------------------------------------------------

def test_multi_label_same_event_flagged():
    rec = _classified(
        "National Symposium cum Conference on Artificial Intelligence organised "
        "by the Departments at Thiagarajar College of Engineering, Madurai, for "
        "students and faculty of the institution.")
    assert rec["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert rec["multi_label"] == 1
    assert "SYMPOSIUM" in rec["category_candidates"]
    assert "CONFERENCE" in rec["category_candidates"]
    group, props = rev.validate_record(rec)
    assert any(p["rule"] == "multi_label_overlap" for p in props)


# ---------------------------------------------------------------------------
# Date / academic-year (group H + AY consistency)
# ---------------------------------------------------------------------------

def test_ay_mismatch_corrected():
    rec = _rec(date_status="dated", dates=["2026-08-01"], earliest="2026-08-01",
               ay="2025-26")
    group, props = rev.validate_record(rec)
    ay = [p for p in props if p["rule"] == "ay_mismatch"]
    assert ay and ay[0]["is_correction"]
    assert ay[0]["proposed"].startswith("set academic_year=2026-27")


def test_ay_consistent_no_correction():
    rec = _rec(date_status="dated", dates=["2025-08-01"], earliest="2025-08-01",
               ay="2025-26")
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "ay_mismatch" for p in props)


def test_multi_year_kept_and_group_h():
    text = ("TCE Interdepartmental Math Olympiad and Workshop 2025-26 - "
            "multiple rounds: 2025-11-19, 2026-01-22, 2026-02-11 at "
            "Thiagarajar College of Engineering, Madurai.")
    rec = _classified(text)
    assert rec["date_status"] == "ambiguous_multi_year"
    assert "multi_year" in rec["flags"]
    group, props = rev.validate_record(rec)
    assert any(p["rule"] == "multi_year_keep" and not p["is_correction"]
               for p in props)
    assert group == "H"


def test_undated_post_stays_undated():
    rec = _rec(cats=["SEMINAR"], text="Seminar on careers at TCE Madurai.")
    group, props = rev.validate_record(rec)
    assert not any(p["rule"] == "ay_mismatch" for p in props)


# ---------------------------------------------------------------------------
# Group assignment precedence
# ---------------------------------------------------------------------------

def test_review_required_is_group_g():
    rec = _rec(status=cand.STATUS_REVIEW_REQUIRED)
    group, props = rev.validate_record(rec)
    assert group == "G"


def test_non_activity_correct_is_group_e():
    rec = _rec(status=cand.STATUS_NON_ACTIVITY, comm="job_ad",
               cats=["PLACEMENT"],
               reason="communication_override:job_ad (category keywords are "
                      "program-feature mentions)")
    group, props = rev.validate_record(rec)
    assert group == "E"
    assert any(p["rule"] == "comm_separation_confirmed" and not p["is_correction"]
               for p in props)
    assert any(p["rule"] == "comm_mention_context" for p in props)


def test_activity_no_corrections_is_group_a():
    rec = _classified(
        "One Day Workshop on VLSI Design organised by the Department of "
        "Electronics and Communication Engineering for students at TCE Madurai.")
    assert rec["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    group, props = rev.validate_record(rec)
    assert group == "A"


# ---------------------------------------------------------------------------
# Integration: loading, validating and persisting in a temp staging DB
# ---------------------------------------------------------------------------

def test_load_review_sample_mismatch_raises(staging_conn):
    cand.init_candidates_schema(staging_conn)
    with pytest.raises(RuntimeError):
        rev.load_review_sample(staging_conn, expected=200)


def test_run_review_persists_proposals_and_reports(staging_conn, tmp_path):
    cand.init_candidates_schema(staging_conn)
    texts = [
        "Workshop on machine learning organised by the Department of Computer "
        "Science and Engineering at TCE Madurai.",
        "Admissions open 2026 at TCE Madurai for all programmes.",
        "Congratulations! TCE Madurai qualifies for the national round of a "
        "hackathon and secured a trophy.",
    ]
    for i, t in enumerate(texts, start=1):
        _insert_post(staging_conn, i, t)
    cand.generate_candidates(staging_conn)
    rows = [dict(r) for r in staging_conn.execute(
        "SELECT * FROM linkedin_activity_candidates").fetchall()]
    cand.mark_review_sample(staging_conn, [r["linkedin_post_id"] for r in rows])

    records = rev.load_review_sample(staging_conn, expected=len(rows))
    assert len(records) == len(rows)
    records, summary = rev.run_review(staging_conn, records)
    assert summary["review_sample_size"] == len(rows)
    assert sum(summary["group_counts"].values()) == len(rows)

    n_props = staging_conn.execute(
        "SELECT COUNT(*) FROM linkedin_manual_review_proposals").fetchone()[0]
    assert n_props == sum(len(r["proposals"]) for r in records)
    assert staging_conn.execute(
        "SELECT COUNT(*) FROM linkedin_activity_candidates").fetchone()[0] == len(rows)

    out = tmp_path / "out"
    paths = rev.write_reports(records, summary, out_dir=str(out))
    for ext in ("json", "md", "csv"):
        assert paths[ext].endswith("." + ext)
        assert (out / rev.REPORT_BASENAME).with_suffix("." + ext).exists()
    with open(paths["csv"], "rb") as fh:
        assert fh.read(3) == b"\xef\xbb\xbf"  # Excel-friendly BOM


def test_run_review_idempotent(staging_conn):
    cand.init_candidates_schema(staging_conn)
    _insert_post(staging_conn, 1, "Seminar on careers at TCE Madurai.")
    _insert_post(staging_conn, 2, "Thanks for a great year at TCE Madurai!")
    cand.generate_candidates(staging_conn)
    rows = [dict(r) for r in staging_conn.execute(
        "SELECT * FROM linkedin_activity_candidates").fetchall()]
    cand.mark_review_sample(staging_conn, [r["linkedin_post_id"] for r in rows])
    records = rev.load_review_sample(staging_conn, expected=len(rows))
    _, s1 = rev.run_review(staging_conn, records)
    _, s2 = rev.run_review(staging_conn, records)
    assert s1["total_proposed_corrections"] == s2["total_proposed_corrections"]
    assert staging_conn.execute(
        "SELECT COUNT(*) FROM linkedin_manual_review_proposals").fetchone()[0] == \
        s1["total_proposed_corrections"] + s1["total_review_notes"]