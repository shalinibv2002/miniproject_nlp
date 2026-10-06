"""Tests for the single-primary-category semantic resolver.

The resolver must pick exactly ONE category from the existing 24-code
taxonomy by reading what the post actually *did*, not by trusting isolated
keyword hits.  These tests pin the behavioural rules that were used to fix the
category-sum / unique-count inflation, including the false friends that
inflated RESEARCH, INTERNSHIP and SEMINAR in the live data.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from backend.database.primary_category import (
    ALLOWED_CATEGORY_CODES,
    NON_ACTIVITY,
    REPORTABLE,
    REVIEW_REQUIRED,
    decide_for_row,
    resolve_primary_category,
    resolve_for_row,
)


def classify(text, title=None, candidates=None):
    return resolve_primary_category(text=text, title=title, candidates=candidates)


# ---------------------------------------------------------------------------
# taxonomy
# ---------------------------------------------------------------------------
def test_taxonomy_is_exactly_24_codes():
    assert len(ALLOWED_CATEGORY_CODES) == 24
    assert "CULTURAL" in ALLOWED_CATEGORY_CODES
    assert "ACHIEVEMENT" in ALLOWED_CATEGORY_CODES


def test_result_is_always_in_taxonomy_or_none():
    text = "Thiagarajar College of Engineering organised a workshop on AI tools."
    result = classify(text)
    assert result["category"] in ALLOWED_CATEGORY_CODES


def test_candidate_list_alone_cannot_produce_multiple_categories():
    text = "A seminar and a workshop and a hackathon all happened."
    result = classify(text, candidates=["SEMINAR", "WORKSHOP", "HACKATHON"])
    assert isinstance(result["category"], (str, type(None)))
    assert result["category"] in ALLOWED_CATEGORY_CODES


# ---------------------------------------------------------------------------
# organised events declare themselves; the head noun is the activity
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text,expected", [
    ("TCE invites you to a 3-day Faculty Development Programme on AI.",
     "FDP"),
    ("The Department of ECE is organising a five-day STTP on VLSI design.",
     "STTP"),
    ("Registration is open for the National Level Technical Symposium 2026.",
     "SYMPOSIUM"),
    ("Join the Hackathon 2026 at Thiagarajar College of Engineering.",
     "HACKATHON"),
    ("TCE is hosting an international conference on sustainable engineering.",
     "CONFERENCE"),
    ("The college invites you to a Guest Lecture on machine learning.",
     "GUEST_LECTURE"),
    ("A hands-on workshop on PCB fabrication will be conducted for students.",
     "WORKSHOP"),
    ("TCE is organising a state-level chess tournament for school students.",
     "SPORTS"),
    ("Webinar on Design Thinking for AI and Data Innovation, register now.",
     "WEBINAR"),
])
def test_organized_event_head_noun_wins(text, expected):
    assert classify(text)["category"] == expected


def test_american_spelling_of_programme_is_recognised():
    # "program" (not "programme") must still be found.
    assert classify(
        "The AI Consortium presents a Professional Training Program for scholars."
    )["category"] == "WORKSHOP"


def test_inauguration_spelling_is_recognised():
    # "inaug..." was previously misspelled in the pattern and never matched.
    result = classify("Inaugural Ceremony of the English Language Lab at TCE.")
    assert result["category"] == "CAMPUS"


def test_curly_apostrophe_does_not_break_day_patterns():
    # Live text uses U+2019; patterns must fold it to a straight quote.
    assert classify(
        "\U0001f338 International Women\u2019s Day 2026 Celebration, TCE invites you."
    )["category"] == "CAMPUS"
    assert classify(
        "Founder\u2019s Day 2026 at Thiagarajar College of Engineering."
    )["category"] == "CAMPUS"


# ---------------------------------------------------------------------------
# venue words are not event names
# ---------------------------------------------------------------------------
def test_seminar_hall_is_a_venue_not_a_seminar():
    text = ("Monthly faculty meeting held in the Seminar Hall; the new "
            "attendance policy was circulated.")
    assert classify(text)["category"] != "SEMINAR"


# ---------------------------------------------------------------------------
# strict results -> ACHIEVEMENT
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "Team Eureka secured AIR 1 overall at the national E-Bike challenge.",
    "Congratulations to our students who won the first prize in the quiz.",
    "Dr. Kumar was awarded the Outstanding Engineer Award 2024 by IEI.",
    "Heartiest congratulations, our faculty have been honoured with the "
    "Tamil Nadu Young Scientist Fellowship.",
])
def test_real_results_are_achievements(text):
    assert classify(text)["category"] == "ACHIEVEMENT"


def test_participation_alone_is_not_an_achievement():
    text = ("Thanks to all who participated in the certificate of "
            "participation programme.")
    result = classify(text)
    assert result["category"] != "ACHIEVEMENT"


def test_person_spotlight_beats_topical_research_words():
    # A profile of one person: the research words are the person's credentials.
    text = ("Alumni Spotlight: proud to feature Mr. Kumar (B.Tech 2015-2019), "
            "a Machine Learning Researcher who secured AIR 1 in NPTEL and "
            "earned a US Patent while pursuing his PhD.")
    assert classify(text)["category"] == "ACHIEVEMENT"


def test_plain_research_grant_is_still_research_not_achievement():
    # A single person's grant is a research act, not a spotlight profile.
    text = "Dr. A. Karuppasamy secures a UGC-DAE CSR research grant of Rs 1.35 lakh."
    assert classify(text)["category"] == "RESEARCH"


# ---------------------------------------------------------------------------
# research
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "The college proudly celebrates the grant of a patent for a new process.",
    "Our inventors have been granted a utility patent by the Indian Patent Office.",
    "A research grant of Rs 10.11 lakh has been sanctioned by UGC-IUAC.",
    "The team published a paper in a peer-reviewed international journal.",
])
def test_research_outputs_are_research(text):
    assert classify(text)["category"] == "RESEARCH"


def test_bare_word_research_is_not_enough():
    # "Research" as a topic/audience word must not create a research activity.
    text = ("The college organised a cultural evening for research scholars "
            "and students of the research department.")
    assert classify(text)["category"] != "RESEARCH"


# ---------------------------------------------------------------------------
# industry / career
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text", [
    "TCE Madurai and NIT Calicut signed an MoU yesterday.",
    "An NDA was signed with Lakshmi Machine Works Limited, Coimbatore.",
    "TCE signed an MoU with Conserve Consultants Pvt. Ltd.",
])
def test_genuine_industry_arrangements_are_industry(text):
    assert classify(text)["category"] == "INDUSTRY"


def test_event_head_noun_beats_a_weak_industry_mention():
    # Declares a Hackathon; "Industry Innovation" is only part of the title.
    text = ("Industry Innovation Hackathon 2026, in association with the "
            "Institution's Innovation Council, presents itself.")
    assert classify(text)["category"] == "HACKATHON"


def test_international_is_not_an_internship():
    # 106 live rows were classified INTERNSHIP purely from "international".
    text = ("International Women's Day 2026 Celebration is organised by the "
            "Women Empowerment Cell.")
    result = classify(text, candidates=["INTERNSHIP"])
    assert result["category"] != "INTERNSHIP"


def test_real_internship_programme_is_an_internship():
    text = ("The department launched a six-week internship programme with "
            "industry partners for final year students.")
    assert classify(text)["category"] == "INTERNSHIP"


def test_placement_activity_is_placement():
    text = ("Campus recruitment drive conducted by TCS; three students "
            "received offer letters.")
    assert classify(text)["category"] == "PLACEMENT"


# ---------------------------------------------------------------------------
# alumni
# ---------------------------------------------------------------------------
def test_alumni_meet_is_alumni():
    text = ("TCE USA Alumni Meetup: reconnect and relive cherished memories "
            "with fellow alumni in Edison, New Jersey.")
    assert classify(text)["category"] == "ALUMNI"


def test_alumnus_speaking_is_not_alumni_engagement():
    text = ("An alumnus shared his career journey during the guest lecture "
            "organised by the placement cell.")
    result = classify(text, candidates=["ALUMNI"])
    assert result["category"] != "ALUMNI"


# ---------------------------------------------------------------------------
# honesty: never invent a category
# ---------------------------------------------------------------------------
def test_ambiguous_post_returns_none_not_a_guess():
    # No act is identifiable; the resolver must decline rather than guess.
    text = "Creativity fuels progress, and innovation drives change!"
    result = classify(text, candidates=["INTERNSHIP"])
    assert result["category"] is None
    assert result["rule"] in ("all_candidates_suppressed", "multi_family_tie",
                              "no_candidate")


def test_every_return_carries_an_audit_trail():
    text = "TCE organised a national level workshop on AI tools for students."
    result = classify(text)
    for key in ("category", "confidence", "rule", "reason", "dropped"):
        assert key in result
    assert result["rule"]
    assert result["reason"]


# ---------------------------------------------------------------------------
# human decisions are authoritative
# ---------------------------------------------------------------------------
def _row(**over):
    row = {
        "title": "Dr. A. Karuppasamy Secures Rs 1.35 Lakh Research Grant",
        "description": "A research grant was sanctioned.",
        "categories": json.dumps(["RESEARCH", "ACHIEVEMENT"]),
        "category_candidates": json.dumps(["RESEARCH", "ACHIEVEMENT"]),
        "category_evidence": None,
        "manual_overrides": None,
    }
    row.update(over)
    return row


def test_manual_override_in_categories_column_is_authoritative():
    # Live overrides live inside the manual_overrides JSON document.
    row = _row(manual_overrides=json.dumps(
        {"categories": ["ACHIEVEMENT"], "review_status": "APPROVED"}))
    result = resolve_for_row(row)
    assert result["category"] == "ACHIEVEMENT"
    assert result["rule"] == "manual_override"


def test_manual_override_wins_even_against_strong_text_evidence():
    row = _row(
        description="MoU signed with a leading company for research collaboration.",
        manual_overrides=json.dumps({"categories": ["INDUSTRY"]}),
    )
    assert resolve_for_row(row)["category"] == "INDUSTRY"


def test_multi_element_override_is_not_treated_as_a_primary_category():
    # An override that still holds several codes carries no single decision.
    row = _row(manual_overrides=json.dumps({"categories": ["RESEARCH", "ACHIEVEMENT"]}))
    assert resolve_for_row(row)["rule"] != "manual_override"


def test_non_category_override_is_ignored():
    row = _row(manual_overrides=json.dumps({"academic_year": "2025-26",
                                            "review_status": "APPROVED"}))
    assert resolve_for_row(row)["rule"] != "manual_override"


def test_missing_override_falls_back_to_semantic_resolution():
    result = resolve_for_row(_row())
    assert result["category"] == "RESEARCH"


# ---------------------------------------------------------------------------
# strict honesty: greetings are not activities, uncertainty is never a guess
# ---------------------------------------------------------------------------
def decide(text, title=None, **over):
    row = _row(title=title, description=text, **over)
    return decide_for_row(row)


def test_christmas_greeting_is_non_activity_not_a_campus_event():
    text = ("Merry Christmas from Thiagarajar College of Engineering. May the "
            "joy, peace and warmth of Christmas fill your hearts and homes. "
            "Warm wishes to our students, faculty, alumni and well-wishers.")
    result = decide(text)
    assert result["status"] == NON_ACTIVITY
    assert result["category"] is None


def test_generic_new_year_greeting_is_non_activity():
    result = decide("Happy New Year 2025 from TCE! Wishing you all a joyful year ahead.")
    assert result["status"] == NON_ACTIVITY


def test_a_wish_post_that_also_reports_an_activity_stays_reportable():
    # The greeting must not demote a post that actually reports an event.
    text = ("Wishes on Republic Day! Our NSS unit organised a cleanliness drive "
            "and a campus awareness programme today.")
    result = decide(text)
    assert result["status"] == REPORTABLE
    assert result["category"] in ALLOWED_CATEGORY_CODES


def test_annual_round_up_is_not_given_one_of_the_activities_it_lists():
    text = ("Happy New Year 2026. 2025 at a Glance: 686 institutional activities, "
            "70+ MoUs and collaborations, 65+ outreach initiatives.")
    result = decide(text)
    assert result["status"] == REVIEW_REQUIRED
    assert result["category"] is None
    assert result["rule"] == "aggregate_recap"


def test_real_event_invitation_is_not_mistaken_for_a_round_up():
    # "annual report" and "<n> events" appear in ordinary invitations.
    text = ("The Management, Principal, Staff and Students cordially invite you "
            "to the Annual Day at KS Auditorium on 24 Jan 2026, 10:00 AM.")
    result = decide(text)
    assert result["status"] == REPORTABLE


def test_ambiguous_post_is_review_required_rather_than_guessed():
    text = ("TCE alumni light up San Ramon! https://youtu.be/example "
            "#TCEReunion #AlumniMeet2024 #TCEUSA")
    result = decide(text, title="TCE alumni light up San Ramon!")
    assert result["status"] == REVIEW_REQUIRED
    assert result["category"] is None


def test_decide_never_returns_more_than_one_category():
    text = "MoU signed with a company, plus a research grant was sanctioned."
    for _ in range(3):
        result = decide(text)
        assert isinstance(result["category"], (str, type(None)))
        assert result["category"] in ALLOWED_CATEGORY_CODES


def test_manual_override_is_never_reclassified_as_non_activity():
    # A reviewer decided this greeting-shaped post IS reportable; respect that.
    row = _row(
        description="Merry Christmas from TCE. Warm wishes to everyone.",
        manual_overrides=json.dumps({"categories": ["CAMPUS"]}),
    )
    assert decide_for_row(row)["status"] == REPORTABLE
    assert decide_for_row(row)["category"] == "CAMPUS"


# ---------------------------------------------------------------------------
# general head nouns added for real corpus rows
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("text, expected", [
    ("CIVIL RAILWAY ENGINEERING SKILLS TRAINING [CREST '26] Batch-II, a week "
     "of hands-on exposure at Civil Seminar Hall.", "WORKSHOP"),
    ("An interactive session with Prof. Rajkumar Buyya, Director CLOUDS Lab, "
     "University of Melbourne, on Cloud and Quantum Computing.", "GUEST_LECTURE"),
])
def test_new_general_head_nouns(text, expected):
    assert classify(text)["category"] == expected


def test_constitution_day_observance_is_campus():
    text = ("TCE is Celebrating our Constitution Day on 26.11.2024, 10.00 AM "
            "to 1.15 PM, Venue: TCE EIACP Seminar Hall.")
    assert classify(text)["category"] == "CAMPUS"


# ---------------------------------------------------------------------------
# live corpus regression: no forced categories
# ---------------------------------------------------------------------------
REPORTABLE_DB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "backend", "database", "linkedin_reportable.db")


@pytest.mark.skipif(not os.path.exists(REPORTABLE_DB), reason="live db absent")
def test_live_corpus_never_yields_multi_label_or_guesses():
    import sqlite3
    conn = sqlite3.connect(REPORTABLE_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM linkedin_reportable_activities "
            "WHERE reportable_status='REPORTABLE'").fetchall()
        assert rows
        for row in rows:
            result = decide_for_row(row)
            if result["status"] == REPORTABLE:
                assert result["category"] in ALLOWED_CATEGORY_CODES
            else:
                assert result["category"] is None
    finally:
        conn.close()