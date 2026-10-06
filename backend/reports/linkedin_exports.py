"""Excel/PDF report generation for the PUBLIC LinkedIn reportable dataset.

Every report here is generated live from ``linkedin_reportable.db`` using the
exact same query helpers as the list/analytics endpoints
(``filters_fragment`` / ``count_reportable`` / ``analytics_*``), so a
downloaded report always reconciles with the count shown in the UI.  Only the
public projection is ever exported — internal validation fields never leak.
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from backend.database.linkedin_reportable import (
    REPORTABLE,
    _row_to_record,
    analytics_categories,
    analytics_departments,
    analytics_stakeholders,
    analytics_yearly,
    count_reportable,
    filters_fragment,
    get_reportable_connection,
)
from backend.database.category_catalog import public_category_name
from backend.database.category_report_schema import (
    ALL_REPORT_FIELDS,
    column_widths,
    normalize_scope,
    report_columns,
    report_columns_for_records,
)

# The column set of every report is category-specific and comes from ONE
# definition (``backend.database.category_report_schema``): the on-screen table,
# the preview, Excel, PDF and the Ask-the-Data exports all render the very same
# projection, so a downloaded report can never disagree with the screen.
# ``export_columns()`` is the single entry point used by all of them.

# Human-buildable report presets for the Report Generator.  Each maps a
# report_type slug to a public category; None means "all categories".
REPORT_TYPES = {
    "all": (None, "All Activities"),
    "achievements": ("ACHIEVEMENT", "Achievement and Awards"),
    "research": ("RESEARCH", "Research and Consultancy"),
    "industry": ("INDUSTRY", "Industry Collaboration"),
    "clubs": ("CLUB", "Clubs and Chapters"),
    "outreach": ("OUTREACH", "Outreach and Extension"),
    "workshops": ("WORKSHOP", "Workshops"),
    "conferences": ("CONFERENCE", "Conference"),
    "seminars": ("SEMINAR", "Seminar"),
    "guest_lectures": ("GUEST_LECTURE", "Guest Lecture"),
    "fdp": ("FDP", "FDP"),
    "hackathons": ("HACKATHON", "Hackathon"),
    "cultural": ("CULTURAL", "Cultural"),
    "sports": ("SPORTS", "Sports"),
    "ncc": ("NCC", "NCC"),
    "nss": ("NSS", "NSS"),
    "placements": ("PLACEMENT", "Placement"),
    "internships": ("INTERNSHIP", "Internship"),
    "webinars": ("WEBINAR", "Webinar"),
    "campus": ("CAMPUS", "Campus"),
}

# ``ALL_REPORT_FIELDS`` comes from the category schemas themselves, so a column
# added to a schema is exported the moment it exists (and nothing else is).
PUBLIC_RECORD_FIELDS = (
    "activity_id", "title", "summary", "post_url", "activity_date",
    "academic_year", "category", "categories", "department", "departments",
    "stakeholder", "stakeholders", "source",
) + ALL_REPORT_FIELDS


def export_columns(args=None, records=None):
    """Report columns for a request, chosen by scope and category.

    ``records`` (the rows actually being reported) is used when the request is
    not pinned to a single category, so a result set that happens to be
    category-specific still gets that category's columns.
    """
    args = args or {}
    scope = normalize_scope(args.get("scope"), args.get("department"))
    category = args.get("category")
    if category:
        return report_columns(category, scope)
    if records is not None:
        return report_columns_for_records(records, scope)
    return report_columns(None, scope)


def export_column_payload(args=None, records=None):
    """Column descriptors for the JSON preview (label + projection key)."""
    return [{"label": label, "field": field}
            for label, field in export_columns(args, records)]


def public_record(rec):
    """Public projection of a reportable row: never leaks internal fields."""
    return {key: rec.get(key) for key in PUBLIC_RECORD_FIELDS}


def _fetch_records(conn, args, limit=5000):
    where, params = filters_fragment(args)
    rows = conn.execute(
        "SELECT * FROM linkedin_reportable_activities r" + where +
        " ORDER BY r.activity_date DESC NULLS LAST, r.activity_id ASC LIMIT ?",
        params + [limit],
    ).fetchall()
    return [_row_to_record(r) for r in rows]


def _build_context(args):
    """Human-readable filter summary for a report (public vocabulary only)."""
    parts = []
    scope = (args or {}).get("scope")
    if scope == "general":
        parts.append("General (institution-wide) activities")
    elif scope == "departmental":
        parts.append("Departmental activities")
    if args.get("department") and str(args.get("department")).lower() != "general":
        parts.append("Department: %s" % args["department"])
    if args.get("academic_year"):
        parts.append("Academic year: %s" % args["academic_year"])
    if args.get("category"):
        cat = args["category"]
        parts.append("Category: %s" % public_category_name(cat))
    if args.get("stakeholder"):
        parts.append("Stakeholder: %s" % args["stakeholder"])
    return " · ".join(parts) if parts else "All reportable LinkedIn activities"


def _report_sheet_bytes(args, conn=None):
    """Return (records, count, context, filter_args) for a requested report.

    ``args`` may carry ``report_type`` (a REPORT_TYPES slug plus optional
    ``scope``/``department``/``category``/``stakeholder``/``from_year``/
    ``to_year`` overrides).  Records are returned in their public projection.
    """
    own = conn is None
    conn = conn or get_reportable_connection()
    try:
        report_type = (args or {}).get("report_type") or "all"
        if report_type not in REPORT_TYPES:
            raise ValueError("report_type must be one of: %s"
                             % ", ".join(sorted(REPORT_TYPES)))
        cat_code, cat_label = REPORT_TYPES[report_type]
        filter_args = {"status": REPORTABLE}
        for key in ("scope", "department", "academic_year", "stakeholder",
                    "from_year", "to_year"):
            if args.get(key):
                filter_args[key] = args[key]
        # An explicitly selected category is more specific than the report-type
        # preset, so it wins; the preset stays the default category.
        explicit_category = (args or {}).get("category")
        if explicit_category:
            cat_code = str(explicit_category).strip().upper()
            cat_label = public_category_name(cat_code)
        if cat_code:
            filter_args["category"] = cat_code
        records = _fetch_records(conn, filter_args)
        count = count_reportable(conn, filter_args)
        context = _build_context(filter_args)
        if cat_label and cat_label != "All Activities":
            context = "%s" % cat_label + \
                ((" · " + context) if context else "")
        return [public_record(r) for r in records], count, context, filter_args
    finally:
        if own:
            conn.close()


def _clean(value):
    if value is None:
        return ""
    return str(value)


def build_excel(args, conn=None):
    """Build an in-memory .xlsx workbook and return raw bytes."""
    records, count, context, filter_args = _report_sheet_bytes(args, conn)
    columns = export_columns(filter_args, records)
    wb = Workbook()
    ws = wb.active
    ws.title = "Activity Report"

    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="A03252")

    ws.append(["TCE Institutional Activity Intelligence"])
    ws.append(["Report: %s" % context])
    ws.append(["Total activities: %d" % count])
    ws.append([])

    headers = [label for label, _field in columns]
    ws.append(headers)
    for cell in ws[ws.max_row]:
        cell.font = head_font
        cell.fill = head_fill

    for index, rec in enumerate(records, start=1):
        ws.append([index if field is None else _clean(rec.get(field))
                   for _label, field in columns])

    for i, width in enumerate(column_widths(columns), start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read(), count, context


def build_pdf(args, conn=None):
    """Build an in-memory .pdf report and return raw bytes."""
    records, count, context, filter_args = _report_sheet_bytes(args, conn)
    columns = export_columns(filter_args, records)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="TCE LinkedIn Activity Report",
    )
    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=15,
        textColor=colors.HexColor("#17202b"), spaceAfter=4)
    context_style = ParagraphStyle(
        "context", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#5b6775"), spaceAfter=10)
    tbl_header = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.white, leading=10)
    tbl_cell = ParagraphStyle(
        "td", fontName="Helvetica", fontSize=7.5,
        leading=9.5, wordWrap="CJK")

    story = []

    def p(text, style):
        story.append(Paragraph(text, style))

    p("TCE Institutional Activity Intelligence", title_style)
    p("Report: %s" % context, context_style)
    p("Total activities: %d" % count, context_style)

    headers = [label for label, _field in columns]
    header_cells = [Paragraph(h, tbl_header) for h in headers]
    data = [header_cells]
    for index, rec in enumerate(records, start=1):
        data.append([Paragraph(str(index) if field is None
                               else _clean(rec.get(field, "")), tbl_cell)
                     for _label, field in columns])

    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A03252")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d8dee9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f7f3f5")]),
    ]))
    story.append(table)

    doc.build(story)
    buf.seek(0)
    return buf.read(), count, context


def _query_columns(result, records):
    """Ask-the-Data reports use the same schema as the report generator.

    The grounded scope/category of the question decides the columns, so an
    achievement question reports achievements and a workshop question reports
    workshops.
    """
    return export_columns({
        "scope": result.get("scope"),
        "department": result.get("department"),
        "category": result.get("category_code"),
    }, records)


def build_query_excel(result):
    """Build an .xlsx from an NLQ result (activities + rows + count)."""
    records = result.get("activities") or []
    rows = result.get("rows") or []
    count = result.get("count")
    if count is None:
        count = len(records)
    wb = Workbook()
    ws = wb.active
    ws.title = "Activity Report"
    head_font = Font(bold=True, color="FFFFFF")
    head_fill = PatternFill("solid", fgColor="A03252")
    ws.append(["TCE Institutional Activity Intelligence"])
    ws.append(["Question: %s" % (result.get("question") or "")])
    ws.append(["Answer: %s" % (result.get("answer") or "")])
    ws.append(["Total activities: %d" % count])
    ws.append([])
    columns = _query_columns(result, records)
    ws.append([label for label, _field in columns])
    for cell in ws[ws.max_row]:
        cell.font = head_font
        cell.fill = head_fill
    for index, rec in enumerate(records, start=1):
        ws.append([index if field is None else _clean(rec.get(field, ""))
                   for _label, field in columns])
    if rows:
        ws.append([])
        ws.append(["Breakdown"])
        ws.append(["Label", "Count"])
        for rc in ws[ws.max_row]:
            rc.font = head_font
            rc.fill = head_fill
        for row in rows:
            ws.append([_clean(row.get("label")), _clean(row.get("value"))])
    for i, width in enumerate(column_widths(columns), start=1):
        ws.column_dimensions[get_column_letter(i)].width = width
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def build_query_pdf(result):
    """Build a .pdf from an NLQ result (activities + rows + count)."""
    records = result.get("activities") or []
    rows = result.get("rows") or []
    count = result.get("count")
    if count is None:
        count = len(records)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        leftMargin=14 * mm, rightMargin=14 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title="TCE LinkedIn Activity Report",
    )
    title_style = ParagraphStyle(
        "title", fontName="Helvetica-Bold", fontSize=15,
        textColor=colors.HexColor("#17202b"), spaceAfter=4)
    context_style = ParagraphStyle(
        "context", fontName="Helvetica", fontSize=10,
        textColor=colors.HexColor("#5b6775"), spaceAfter=10)
    tbl_header = ParagraphStyle(
        "th", fontName="Helvetica-Bold", fontSize=8,
        textColor=colors.white, leading=10)
    tbl_cell = ParagraphStyle(
        "td", fontName="Helvetica", fontSize=7.5,
        leading=9.5, wordWrap="CJK")

    story = []

    def para(text, style):
        story.append(Paragraph(text, style))

    para("TCE Institutional Activity Intelligence", title_style)
    para("Question: %s" % (result.get("question") or ""), context_style)
    para("Answer: %s" % (result.get("answer") or ""), context_style)
    para("Total activities: %d" % count, context_style)

    columns = _query_columns(result, records)
    headers = [label for label, _field in columns]
    data = [[Paragraph(h, tbl_header) for h in headers]]
    for index, rec in enumerate(records, start=1):
        data.append([Paragraph(str(index) if field is None
                               else _clean(rec.get(field, "")), tbl_cell)
                     for _label, field in columns])
    if rows:
        data.append([Paragraph("", tbl_cell)] * len(headers))
        data.append([Paragraph("Breakdown", tbl_header)] + [Paragraph("", tbl_cell)] * (len(headers) - 1))
        row_cells = [Paragraph("%s: %s" % (r.get("label", ""), r.get("value", "")), tbl_cell)
                     for r in rows]
        data.append(row_cells + [Paragraph("", tbl_cell)] * (len(headers) - len(row_cells)))

    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#A03252")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d8dee9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f7f3f5")]),
    ]))
    story.append(table)

    doc.build(story)
    buf.seek(0)
    return buf.read()