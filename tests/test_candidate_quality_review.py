"""Step 5 conservative candidate-year resolution and audit tests."""

from backend.database.init_db import get_connection, init_db
from backend.review.candidate_quality_review import _resolution_for, _quality_for


def _row(**overrides):
    data = {"activity_date": None, "evidence_text": "", "page_title": "", "source_url": "https://www.tce.edu/events",
            "title": "Activity", "final_categories": ""}
    data.update(overrides)
    return data


def test_date_boundary_resolution_uses_august_one():
    assert _resolution_for(_row(activity_date="2024-07-15"))[0] == "2023-24"
    assert _resolution_for(_row(activity_date="2024-08-15"))[0] == "2024-25"
    assert _resolution_for(_row(activity_date="2025-07-15"))[0] == "2024-25"
    assert _resolution_for(_row(activity_date="2025-08-15"))[0] == "2025-26"


def test_context_resolution_ignores_plain_url_and_copyright_years():
    assert _resolution_for(_row(evidence_text="Activities during Academic Year 2024-25")) == ("2024-25", "ACADEMIC_YEAR_CONTEXT")
    assert _resolution_for(_row(evidence_text="Copyright 2024", source_url="https://www.tce.edu/2024/events")) == (None, None)
    assert _resolution_for(_row(page_title="Annual Report 2024-25")) == ("2024-25", "ANNUAL_REPORT_CONTEXT")
    assert _resolution_for(_row(evidence_text="Submitted Institute Data for NIRF. Academic Year 2024-25")) == (None, None)


def test_quality_flags_do_not_depend_on_or_change_category_data():
    status, reason = _quality_for(_row(title="He", final_categories="CONFERENCE,CULTURAL,HACKATHON,SEMINAR,TECH_FEST,WORKSHOP"))
    assert status == "REVIEW" and "MANY_UNRELATED_FINAL_CATEGORIES" in reason
    assert _quality_for(_row(source_url="https://www.tce.edu/sites/default/files/TCE-Research-Policy.pdf", page_title="TCE Research Policy"))[0] == "NON_ACTIVITY"
