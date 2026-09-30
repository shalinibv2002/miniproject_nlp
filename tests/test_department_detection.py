"""Phase 6 tests: department + stakeholder detection."""

from backend.nlp.department_detector import detect_department_status
from backend.nlp.stakeholder_detector import detect_stakeholders


def test_single_department():
    status, matches = detect_department_status(
        "organized by the Department of Computer Science and Engineering."
    )
    assert status == "single"
    assert any(m["code"] == "CSE" for m in matches)


def test_multiple_departments():
    status, matches = detect_department_status(
        "Joint symposium organized by the Department of Mechanical Engineering and"
        " the Department of Electrical and Electronics Engineering."
    )
    assert status == "multiple"
    assert len(matches) >= 2


def test_unknown_department():
    status, matches = detect_department_status("A generic study circle meeting about hobbies.")
    assert status == "unknown"
    assert matches == []


def test_institution_wide():
    assert detect_department_status("Annual Convocation day celebrated across the campus.")[0] == "institution_wide"
    assert detect_department_status("NAAC visit preparation meeting for the whole institute.")[0] == "institution_wide"


def test_institution_wide_trumps_specific():
    # Even with a department mention, clear institution-wide markers win.
    status, _ = detect_department_status(
        "All departments participated in the NAAC visit preparation meetings."
    )
    assert status == "institution_wide"


def test_detect_students():
    detections = detect_stakeholders("Seminar attended by 120 students and 10 faculty members.")
    codes = [c for c, _ in detections]
    assert "STUDENTS" in codes
    assert "FACULTY" in codes


def test_detect_industry_mou():
    detections = detect_stakeholders("MoU signed with a software company for placements.")
    codes = [c for c, _ in detections]
    assert "INDUSTRY" in codes


def test_detect_community_school():
    detections = detect_stakeholders(
        "Outreach programme conducted for nearby school children and the local community."
    )
    codes = [c for c, _ in detections]
    assert "COMMUNITY" in codes


def test_detect_unknown_stakeholder():
    assert detect_stakeholders("") == []
    assert detect_stakeholders("A quiet weekend study session.") == []