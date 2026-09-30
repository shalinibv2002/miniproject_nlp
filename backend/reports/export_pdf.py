"""Phase 14: convert the generated final report Markdown into a PDF.

A small deterministic converter (no external MD engine): headings, tables,
lists and paragraphs are mapped to reportlab primitives.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER

from backend.config import EXPORT_DIR

REPORT_DIR = os.path.join(os.path.dirname(EXPORT_DIR), "reports")
MD_PATH = os.path.join(REPORT_DIR, "final_report.md")
PDF_PATH = os.path.join(EXPORT_DIR, "tce_activity_intelligence_report.pdf")


def build_pdf(md_path=MD_PATH, pdf_path=PDF_PATH, font_name="Helvetica",
              font_bold="Helvetica-Bold", font_size=9):
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    styles = {
        "title": ParagraphStyle("title", fontName=font_bold, fontSize=16,
                                alignment=TA_CENTER, spaceAfter=4),
        "subtitle": ParagraphStyle("subtitle", fontName=font_name, fontSize=11,
                                   alignment=TA_CENTER, textColor=colors.grey,
                                   spaceAfter=10),
        "h1": ParagraphStyle("h1", fontName=font_bold, fontSize=13,
                             spaceBefore=10, spaceAfter=5,
                             textColor=colors.HexColor("#1a4fa0")),
        "h2": ParagraphStyle("h2", fontName=font_bold, fontSize=11,
                             spaceBefore=8, spaceAfter=3),
        "body": ParagraphStyle("body", fontName=font_name, fontSize=font_size,
                               leading=font_size + 3.2, spaceAfter=5),
        "small": ParagraphStyle("small", fontName=font_name, fontSize=font_size - 1,
                                textColor=colors.HexColor("#555555"), spaceAfter=5),
    }

    doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title="TCE Activity Intelligence - Final Report")
    story = []
    i = 0
    tables = []
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(line[2:], styles["title"]))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], styles["h1"]))
        elif line.startswith("### "):
            story.append(Paragraph(line[4:], styles["h2"]))
        elif line.startswith("| "):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not any(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                th = rows[0]
                body = rows[1:]
                n = Table([th] + body, hAlign="LEFT")
                n.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, 0), font_bold),
                    ("FONTSIZE", (0, 0), (-1, -1), font_size - 1),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3fb")),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8d4ea")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(Spacer(1, 2))
                story.append(n)
                story.append(Spacer(1, 6))
            continue
        elif line.startswith("_"):
            story.append(Paragraph(line.strip("_"), styles["small"]))
        elif line.startswith(("- ", "* ")):
            story.append(Paragraph("&bull; " + line[2:], styles["body"]))
        else:
            story.append(Paragraph(line, styles["body"]))
        i += 1

    doc.build(story)
    return pdf_path


if __name__ == "__main__":
    print(build_pdf())