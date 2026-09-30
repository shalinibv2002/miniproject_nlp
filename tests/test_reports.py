"""Phase 14 tests: report artifacts are generated and internally consistent."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.reports import report_generator
from backend.reports import export_pdf
from backend.reports import presentation
from backend.config import EXPORT_DIR

REPORT_DIR = os.path.join(os.path.dirname(EXPORT_DIR), "reports")
SECTION_COUNT = 31


@pytest.fixture(scope="module")
def artifacts():
    conn = report_generator.get_connection()
    try:
        evaluation = report_generator.run_evaluation()
        md = report_generator.build_markdown(conn, evaluation)
    finally:
        conn.close()
    return md


def test_report_has_all_31_sections(artifacts):
    for idx in range(1, SECTION_COUNT + 1):
        assert f"## {idx}." in artifacts, f"Missing section {idx}"


def test_report_numbers_come_from_live_db(artifacts):
    conn = report_generator.get_connection()
    try:
        o = report_generator.overview.overview(conn)
    finally:
        conn.close()
    assert f"{o['total_activities']}" in artifacts


def test_report_markdown_written(tmp_path):
    out = report_generator.build_report()
    assert os.path.exists(out["md"])
    assert out["markdown_lines"] > 100


def test_excel_export_has_expected_sheets(tmp_path):
    out = report_generator.build_report()
    import pandas as pd
    xl = pd.ExcelFile(out["xlsx"])
    sheets = set(xl.sheet_names)
    assert {"yearly", "departments", "categories", "stakeholders",
            "linkedin", "data_quality"} <= sheets


def test_pdf_export_valid(tmp_path):
    md_path = os.path.join(REPORT_DIR, "final_report.md")
    pdf_path = os.path.join(EXPORT_DIR, "tce_activity_intelligence_report.pdf")
    if os.path.exists(md_path):
        export_pdf.build_pdf(md_path=md_path, pdf_path=pdf_path)
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 1000


def test_presentation_has_section_headers():
    slides_path = presentation.build_presentation()
    with open(slides_path, encoding="utf-8") as f:
        content = f.read()
    assert content.startswith("---")
    assert "---\n\n# " in content