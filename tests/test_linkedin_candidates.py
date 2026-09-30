"""Tests for the LinkedIn candidate-generation/classification pilot module.

These tests exercise ``backend.database.linkedin_candidates`` against a
temporary staging database only.  The production database is never touched.
"""

import json

import pytest

from backend.database import linkedin_candidates as cand
from backend.database.linkedin_staging import (
    get_staging_connection,
    init_staging_schema,
)


def _post(post_id=1, text="", url="https://www.linkedin.com/posts/tcemadurai_x"):
    return {
        "id": post_id,
        "post_url": url,
        "post_text": text,
        "source_sheet": "June 2025-June 2026",
        "source_row": post_id,
    }


@pytest.fixture()
def staging_conn(tmp_path):
    path = str(tmp_path / "staging.db")
    conn = get_staging_connection(path)
    init_staging_schema(conn)
    yield conn
    conn.close()


def _insert_post(conn, post_id, text, url=None):
    conn.execute(
        "INSERT INTO linkedin_posts (id, post_text, normalized_text, source_sheet, source_row, post_url) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (post_id, text, text, "June 2025-June 2026", post_id, url),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# classify_post: status / kind decisions
# ---------------------------------------------------------------------------

def test_workshop_post_is_activity_candidate():
    row = cand.classify_post(_post(1, "One Day Workshop on Machine Learning organized by the Department of Computer Science at Thiagarajar College of Engineering, Madurai, open to all students."))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert row["is_activity"] == 1
    assert row["kind"] == cand.KIND_DEVELOPMENT
    assert "WORKSHOP" in row["category_candidates"]
    assert "communication_only" not in row["flags"]


def test_mca_department_of_is_explicit_organizer_not_general():
    row = cand.classify_post(_post(
        99, "The Department of MCA, Thiagarajar College of Engineering invites alumni "
            "to the MCA Alumni Meet 2025 held on 3 January 2026."))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "Computer Applications" in row["department_candidates"]
    # "Department of MCA" is an explicit MCA organizer, so the post is credited
    # to Computer Applications and not bucketed into the institution-wide
    # General fallback (RULE-09 regression for the Step 10 normalisation).
    assert row["department_display"] == ["Computer Applications"]
    assert "FLAG_DEPT_TO_GENERAL" not in row["flags"]


def test_bare_mca_mention_does_not_force_department():
    # A passing mention of MCA as a qualification is not an organiser clue and
    # must not be promoted to Computer Applications.
    row = cand.classify_post(_post(
        100, "We congratulate our staff for completing the Executive MCA programme "
             "offered by a partner university."))
    assert row["department_display"] == ["General"]


def test_fdp_post_kind_and_category():
    row = cand.classify_post(_post(2, "Five-Day AICTE Approved Faculty Development Programme on Universal Human Values II organized by the Department of Electrical and Electronics Engineering at Thiagarajar College of Engineering, Madurai."))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "FDP" in row["category_candidates"]
    assert row["kind"] == cand.KIND_DEVELOPMENT


def test_research_post_maps_to_kind_research():
    row = cand.classify_post(_post(3, "Research Journal publication by our faculty members is a proud moment for the Department of Applied Mathematics at Thiagarajar College of Engineering, Madurai."))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert row["kind"] == cand.KIND_RESEARCH
    assert "RESEARCH" in row["category_candidates"]


def test_greeting_post_is_non_activity():
    row = cand.classify_post(_post(4, "The management and staff of Thiagarajar College of Engineering wish you and your family a very happy and prosperous Deepavali festival celebration this year."))
    assert row["candidate_status"] == cand.STATUS_NON_ACTIVITY
    assert row["is_activity"] == 0
    assert row["kind"] == cand.KIND_GREETING
    assert "communication_only" in row["flags"]


def test_job_ad_post_is_non_activity_kind_f():
    row = cand.classify_post(_post(5, "We are hiring a Fire Safety Officer position at Thiagarajar Mills and the Thiagarajar Institute from qualified candidates with relevant experience."))
    assert row["candidate_status"] == cand.STATUS_NON_ACTIVITY
    assert row["kind"] == cand.KIND_JOB


def test_admission_promo_with_feature_words_is_non_activity():
    # 'internship' / 'research' here are program-feature mentions, not events.
    text = "PG Admissions 2026-27 Open at Thiagarajar College. Paid Internships and Research opportunities, strong Placement record, industry partners, alumni network."
    row = cand.classify_post(_post(6, text))
    assert row["candidate_status"] == cand.STATUS_NON_ACTIVITY
    assert row["kind"] == cand.KIND_ADMISSION
    assert "communication_only" in row["flags"]
    assert row["reason"].startswith("communication_override:admission_promo")
    # evidence is retained for reviewers even though the decision is non-activity
    assert "INTERNSHIP" in row["category_candidates"]


def test_event_announced_inside_admission_text_stays_activity():
    # a real event (workshop) wins over the promo framing
    text = "Admissions open, and we also invite you to a Hands-on Workshop on VLSI Design next week at the college campus for all interested participants."
    row = cand.classify_post(_post(7, text))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "WORKSHOP" in row["category_candidates"]


def test_url_only_post_is_review_required():
    row = cand.classify_post(_post(8, " ", url="https://www.linkedin.com/posts/tcemadurai_x"))
    assert row["candidate_status"] == cand.STATUS_REVIEW_REQUIRED
    assert row["kind"] == cand.KIND_UNKNOWN
    assert "url_only" in row["flags"]
    assert "weak_text" in row["flags"]


def test_weak_text_but_activity_is_review_required():
    row = cand.classify_post(_post(9, "TEDx TCE 2026"))
    assert row["candidate_status"] == cand.STATUS_REVIEW_REQUIRED
    assert row["is_activity"] == 1
    assert "weak_text" in row["flags"]


def test_insufficient_evidence_is_review_required():
    row = cand.classify_post(_post(10, "Interesting things are happening at the college this semester."))
    assert row["candidate_status"] == cand.STATUS_REVIEW_REQUIRED
    assert row["is_activity"] is None
    assert row["kind"] == cand.KIND_OTHER


# ---------------------------------------------------------------------------
# classify_post: dates, academic year, flags, multi-label
# ---------------------------------------------------------------------------

def test_date_status_and_academic_year_june():
    row = cand.classify_post(_post(11, "Seminar on 15 July 2026."))
    assert row["date_status"] == "dated"
    assert row["academic_year"] == "2026-27"


def test_date_status_and_academic_year_january():
    row = cand.classify_post(_post(12, "Seminar on 15 January 2026."))
    assert row["date_status"] == "dated"
    assert row["academic_year"] == "2025-26"


def test_undated_post():
    row = cand.classify_post(_post(13, "Graduation ceremony held recently."))
    assert row["date_status"] == "undated"
    assert row["academic_year"] is None


def test_multi_year_ambiguity():
    row = cand.classify_post(_post(14, "Events are scheduled for 15 March 2025 and again on 20 April 2026 at the college campus of Thiagarajar College of Engineering, Madurai."))
    assert row["date_status"] == "ambiguous_multi_year"
    assert "multi_year" in row["flags"]


def test_pre_2024_flag():
    row = cand.classify_post(_post(15, "Symposium held on 10 June 2023."))
    assert "pre_2024_ambiguous" in row["flags"]


def test_link_less_flag():
    row = cand.classify_post(_post(16, "Hands-on Training session announced.", url=None))
    assert "link_less" in row["flags"]


def test_text_is_url_flag():
    row = cand.classify_post(_post(17, "https://lnkd.in/gQrqtdhZ"))
    assert "text_is_url" in row["flags"]


def test_multi_label_flag():
    row = cand.classify_post(_post(18, "Inter-College Cultural Quiz and Hackathon competition."))
    assert row["multi_label"] == 1
    assert len(row["category_candidates"]) >= 2


# ---------------------------------------------------------------------------
# generate_candidates: staging-only persistence, idempotence, retention
# ---------------------------------------------------------------------------

def test_generate_candidates_persists_all_posts(staging_conn):
    _insert_post(staging_conn, 1, "TEDx TCE 2026 conference.", "https://lnkd.in/a")
    _insert_post(staging_conn, 2, "Happy Pongal to everyone.", None)
    _insert_post(staging_conn, 3, "", "https://lnkd.in/b")

    rows = cand.generate_candidates(staging_conn)
    assert len(rows) == 3
    total = staging_conn.execute("SELECT COUNT(*) FROM linkedin_activity_candidates").fetchone()[0]
    assert total == 3
    # every canonical post is KEPT (nothing deleted)
    assert staging_conn.execute("SELECT COUNT(*) FROM linkedin_posts").fetchone()[0] == 3
    # no production table exists in the staging db on our watch
    prod = [r[0] for r in staging_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert "institutional_activities" not in prod


def test_generate_candidates_is_idempotent(staging_conn):
    _insert_post(staging_conn, 1, "One Day Workshop on Machine Learning organized by the Department of Computer Science at Thiagarajar College of Engineering, Madurai, open to all students.", "https://lnkd.in/a")
    cand.generate_candidates(staging_conn)
    cand.generate_candidates(staging_conn)
    total = staging_conn.execute("SELECT COUNT(*) FROM linkedin_activity_candidates").fetchone()[0]
    assert total == 1
    rows = staging_conn.execute(
        "SELECT candidate_status, kind FROM linkedin_activity_candidates WHERE linkedin_post_id=1").fetchone()
    assert rows["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE


def test_mark_review_sample(staging_conn):
    _insert_post(staging_conn, 1, "Hackathon 2026 competition.", "https://lnkd.in/a")
    _insert_post(staging_conn, 2, "Wishes you all a Happy New Year.", None)
    cand.generate_candidates(staging_conn)
    cand.mark_review_sample(staging_conn, [1])
    marked = staging_conn.execute(
        "SELECT review_status FROM linkedin_activity_candidates WHERE linkedin_post_id=1").fetchone()[0]
    assert marked == cand.REVIEW_PENDING
    other = staging_conn.execute(
        "SELECT review_status FROM linkedin_activity_candidates WHERE linkedin_post_id=2").fetchone()[0]
    assert other == cand.REVIEW_AUTO


def test_build_review_sample_bounds_and_deterministic():
    rows = [cand.classify_post(_post(
        i, "Workshop on topic %d and student Hackathon competition." % i))
        for i in range(1, 250)]
    sample = cand.build_review_sample(rows, seed=42)
    again = cand.build_review_sample(rows, seed=42)
    assert cand.REVIEW_SAMPLE_MIN <= len(sample) <= cand.REVIEW_SAMPLE_MAX
    assert [r["linkedin_post_id"] for r in sample] == [r["linkedin_post_id"] for r in again]
    assert all(r["review_status"] == cand.REVIEW_PENDING for r in sample)


def test_distribution_helper():
    rows = [cand.classify_post(_post(1, "One Day Workshop on Machine Learning.")),
            cand.classify_post(_post(2, "Research Journal publication."))]
    d = cand.distribution(rows, "kind")
    assert d[cand.KIND_DEVELOPMENT] == 1
    assert d[cand.KIND_RESEARCH] == 1
    total = sum(d.values())
    assert total == 2


def test_module_never_touches_production():
    schema = cand.CANDIDATES_SCHEMA
    # the staging candidates schema must not create any production tables
    for table in ("institutional_activities", "final_activity_metadata",
                  "activity_candidates", "linkedin_matches", "activity_sources"):
        assert ("CREATE TABLE IF NOT EXISTS %s" % table) not in schema
        assert ("CREATE TABLE %s" % table) not in schema
    assert "linkedin_activity_candidates" in schema


# ---------------------------------------------------------------------------
# RULE-01..12 review-supported gates (flag-first, additive)
# ---------------------------------------------------------------------------

def test_pure_greeting_locked_non_activity():
    # RULE-01: a greeting with no activity category is a locked NON_ACTIVITY.
    row = cand.classify_post(_post(30, "The management and staff of Thiagarajar "
        "College of Engineering wish you and your family a happy festival."))
    assert row["candidate_status"] == cand.STATUS_NON_ACTIVITY
    assert "communication_only" in row["flags"]


def test_thanks_inside_activity_keeps_categories():
    # review finding E.4: congratulatory wording inside a real activity post
    # keeps its categories; only admission/job benefit from the comm override.
    row = cand.classify_post(_post(31, "Thank you to everyone who supported us. "
        "Our team secured a gold medal and a trophy at the national round "
        "of the robotics championship at TCE Madurai."))
    assert row["candidate_status"] == cand.STATUS_ACTIVITY_CANDIDATE
    assert "ACHIEVEMENT" in row["category_candidates"]
    assert "communication_only" not in row["flags"]


def test_curated_multilabel_collapse_same_event():
    # RULE-08: SYMPOSIUM + TECH_FEST in the same region collapse to SYMPOSIUM.
    row = cand.classify_post(_post(31, "National Symposium cum Technical "
        "Festival 2026 organised at Thiagarajar College of Engineering, Madurai."))
    assert "SYMPOSIUM" in row["category_candidates"]
    assert "TECH_FEST" not in row["category_candidates"]
    assert row["multi_label"] == 0
    assert any(f.startswith("multi_label_collapsed:") for f in row["flags"])


def test_curated_multilabel_kept_when_regions_far():
    # distinct events in separate regions stay multi-label
    row = cand.classify_post(_post(32, "A Conference on Advanced Artificial "
        "Intelligence and Machine Learning in March, followed by a separate "
        "Webinar on career guidance for women in July at TCE Madurai."))
    assert row["multi_label"] == 1
    assert "CONFERENCE" in row["category_candidates"]
    assert "WEBINAR" in row["category_candidates"]


def test_non_curated_multilabel_untouched():
    # SYMPOSIUM + CONFERENCE is NOT a curated pair -> stays multi-label
    row = cand.classify_post(_post(33, "National Symposium cum Conference on "
        "Artificial Intelligence organised by the Departments at Thiagarajar "
        "College of Engineering, Madurai, for students and faculty."))
    assert row["multi_label"] == 1
    assert "SYMPOSIUM" in row["category_candidates"]
    assert "CONFERENCE" in row["category_candidates"]


def test_department_generic_topic_display_is_general():
    # RULE-09: topic-technical terminology is not department evidence.
    row = cand.classify_post(_post(34, "Machine Learning Workshop for students "
        "and faculty at Thiagarajar College of Engineering, Madurai."))
    assert "Artificial Intelligence" in row["department_candidates"]
    assert row["department_display"] == ["General"]
    assert "dept_to_general" in row["flags"]


def test_department_explicit_organizer_display_kept():
    row = cand.classify_post(_post(35, "Workshop on Machine Learning organised "
        "by the Department of Artificial Intelligence at Thiagarajar College "
        "of Engineering, Madurai."))
    assert row["department_display"] == ["Artificial Intelligence"]
    assert "dept_to_general" not in row["flags"]


def test_department_of_chemistry_phrase_is_explicit():
    # alias matcher: "Department of Chemistry" is organizer evidence
    row = cand.classify_post(_post(36, "Seminar organised by the Department "
        "of Chemistry at Thiagarajar College of Engineering, Madurai."))
    assert "Chemistry" in row["department_candidates"]
    assert row["department_display"] == ["Chemistry"]


def test_mention_only_achievement_is_dropped():
    # STEP-11 strict ACHIEVEMENT classification (RULE-03 hard gate): a mention
    # like "congratulations / certificate / milestone / recognised" is a nod,
    # not an achievement — it is DROPPED from the decision while the
    # category_gate flag preserves the audit trail.
    row = cand.classify_post(_post(37, "Congratulations to our certified "
        "students and their recognised certificate milestones at TCE Madurai."))
    assert "ACHIEVEMENT" not in row["category_candidates"]
    assert "category_gate:ACHIEVEMENT" in row["flags"]


def test_strong_achievement_no_gate_flag():
    row = cand.classify_post(_post(38, "Our team won the National Robotics "
        "Championship and received a gold medal at Thiagarajar College of "
        "Engineering, Madurai."))
    assert "ACHIEVEMENT" in row["category_candidates"]
    assert "category_gate:ACHIEVEMENT" not in row["flags"]


def test_strict_achievement_never_overrides_real_activity():
    # "participated in a hackathon" / "attended a workshop" stay their real
    # category; congratulatory wording alone never upgrades to ACHIEVEMENT.
    hack = cand.classify_post(_post(51, "Students participated in a hackathon "
        "conducted at Thiagarajar College of Engineering, Madurai."))
    assert "HACKATHON" in hack["category_candidates"]
    assert "ACHIEVEMENT" not in hack["category_candidates"]

    workshop = cand.classify_post(_post(52, "MCA attended a workshop on "
        "Generative AI for students on 15 January 2026 at TCE Madurai."))
    assert "WORKSHOP" in workshop["category_candidates"]
    assert "ACHIEVEMENT" not in workshop["category_candidates"]

    nod = cand.classify_post(_post(53, "Congratulations everyone on your "
        "participation at the college day celebrations held at TCE Madurai."))
    assert "category_gate:ACHIEVEMENT" in nod["flags"] or "ACHIEVEMENT" not in nod["category_candidates"]


def test_direct_achievement_kept_secured_and_won():
    # "secured second place", "won first prize", "received ... Award" are
    # DIRECT achievement evidence (not mention-only) and MUST survive the gate.
    secured = cand.classify_post(_post(54, "Our team secured second place in "
        "the state-level robotics championship at TCE Madurai."))
    assert "ACHIEVEMENT" in secured["category_candidates"]
    assert "category_gate:ACHIEVEMENT" not in secured["flags"]

    won = cand.classify_post(_post(55, "Students won first prize in the "
        "inter-college hackathon conducted at TCE Madurai."))
    assert "ACHIEVEMENT" in won["category_candidates"]
    assert "category_gate:ACHIEVEMENT" not in won["flags"]

    award = cand.classify_post(_post(56, "Faculty member received Best Faculty "
        "Award for outstanding teaching at TCE Madurai this year."))
    assert "ACHIEVEMENT" in award["category_candidates"]


def test_plural_departments_list_with_mca_is_explicit_organizer():
    # LI-00214: "Departments of ... MCA ..." is an explicit Computer
    # Applications organizer list (not the generic bare-MCA mention).
    row = cand.classify_post(_post(57, "All the departments of our college, "
        "including MCA, organised the national technical symposium at "
        "Thiagarajar College of Engineering, Madurai."))
    assert "Computer Applications" in row["department_candidates"]
    assert row["department_display"] == ["Computer Applications"]
    assert "dept_to_general" not in row["flags"]


def test_unclear_reason_taxonomy():
    # RULE-12: machine-readable reason codes on REVIEW_REQUIRED rows
    row = cand.classify_post(_post(39, " ", url="https://www.linkedin.com/posts/tcemadurai_x"))
    assert "unclear:url_only" in row["flags"]
    assert row["unclear_reason"] == "url_only"

    row2 = cand.classify_post(_post(40, "TEDx TCE 2026"))
    assert row2["unclear_reason"] == "low_evidence_event_like"

    row3 = cand.classify_post(_post(41, "Annual Report"))
    assert row3["unclear_reason"] == "title_only"
    assert "unclear:title_only" in row3["flags"]


def test_generate_candidates_persists_new_columns(staging_conn):
    _insert_post(staging_conn, 1, "Machine Learning Workshop for students and "
                 "faculty at Thiagarajar College of Engineering, Madurai.",
                 url="https://www.linkedin.com/posts/tcemadurai_1")
    cand.generate_candidates(staging_conn)
    row = staging_conn.execute(
        "SELECT department_display, unclear_reason FROM "
        "linkedin_activity_candidates WHERE linkedin_post_id=1").fetchone()
    assert row["department_display"] == '["General"]'
    assert row["unclear_reason"] == "low_evidence_event_like"