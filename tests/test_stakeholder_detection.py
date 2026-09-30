"""Stakeholder detection tests (kept separate from department tests)."""

from backend.nlp.stakeholder_detector import detect_stakeholders, populate_stakeholders


def test_detect_alumni():
    codes = [c for c, _ in detect_stakeholders("The silver jubilee alumni meet was held in the campus.")]
    assert "ALUMNI" in codes


def test_detect_government():
    codes = [c for c, _ in detect_stakeholders("Sponsored research project funded by DST under the ministry.")]
    assert "GOVERNMENT" in codes


def test_detect_multiple():
    codes = [c for c, _ in detect_stakeholders(
        "Students, faculty and parents attended the orientation programme."
    )]
    assert {"STUDENTS", "FACULTY", "PARENTS"} <= set(codes)