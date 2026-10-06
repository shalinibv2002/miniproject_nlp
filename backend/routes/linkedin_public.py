"""Public read-only API for the FINAL LinkedIn REPORTABLE dataset.

Every endpoint reads ONLY ``backend/database/linkedin_reportable.db`` (the
dedicated, isolated reportable dataset).  Nothing here touches the staging
database, the workbook, or the website production database.

Two invariants are enforced by construction:
  * The public projection (``_row_to_record``) never exposes internal evidence,
    scoring, heuristics or provenance pins.
  * All list/analytics endpoints share one query builder (``filters_fragment``)
    so the unique total never diverges across year/category/department/
    stakeholder filters.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request, send_file
from io import BytesIO

from backend.database.linkedin_reportable import (
    REPORTABLE,
    _row_to_record,
    analytics_categories,
    analytics_departments,
    analytics_overview,
    analytics_stakeholders,
    analytics_yearly,
    availability,
    count_reportable,
    filters_fragment,
    get_reportable_connection,
)
from backend.routes.helpers import error_response, ok, paginate_args, page_response

bp = Blueprint("linkedin", __name__, url_prefix="/api/linkedin")

SORT_COLUMNS = {
    "activity_id": "r.activity_id",
    "title": "r.title COLLATE NOCASE",
    "activity_date": "r.activity_date",
    "academic_year": "r.academic_year",
}


def _order_by():
    sort = (request.args.get("sort") or "activity_date").lower()
    if sort not in SORT_COLUMNS:
        raise ValueError("sort must be one of: activity_id, title, activity_date, academic_year")
    direction = (request.args.get("order") or "desc").lower()
    if direction not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    return f"{SORT_COLUMNS[sort]} {direction.upper()} NULLS LAST, r.activity_id ASC"


def _list_rows(conn, args):
    where, params = filters_fragment(args)
    offset, page_size = paginate_args()
    rows = conn.execute(
        "SELECT * FROM linkedin_reportable_activities r" + where +
        " ORDER BY " + _order_by() + " LIMIT ? OFFSET ?",
        params + [page_size, offset],
    ).fetchall()
    return [_row_to_record(r) for r in rows], offset, page_size


@bp.get("/activities")
def list_activities():
    conn = get_reportable_connection()
    try:
        args = request.args.to_dict()
        args["status"] = REPORTABLE
        total = count_reportable(conn, args)
        items, offset, page_size = _list_rows(conn, args)
        return ok(page_response(items, total, offset // page_size + 1, page_size))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/activities/<activity_id>")
def get_activity(activity_id):
    conn = get_reportable_connection()
    try:
        row = conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id = ? "
            "AND reportable_status = ?",
            (activity_id, REPORTABLE),
        ).fetchone()
        if row is None:
            return error_response("activity not found", 404)
        return ok(_row_to_record(row))
    finally:
        conn.close()


@bp.get("/years")
def list_years():
    conn = get_reportable_connection()
    try:
        return ok(analytics_yearly(conn, request.args.to_dict()))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/categories")
def list_categories():
    conn = get_reportable_connection()
    try:
        return ok(analytics_categories(conn, request.args.to_dict()))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/departments")
def list_departments():
    conn = get_reportable_connection()
    try:
        return ok(analytics_departments(conn, request.args.to_dict()))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/stakeholders")
def list_stakeholders():
    conn = get_reportable_connection()
    try:
        return ok(analytics_stakeholders(conn, request.args.to_dict()))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/analytics/overview")
def analytics():
    conn = get_reportable_connection()
    try:
        return ok(analytics_overview(conn, request.args.to_dict()))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/analytics/yearly")
def analytics_yearly_view():
    return list_years()


@bp.get("/analytics/categories")
def analytics_categories_view():
    return list_categories()


@bp.get("/analytics/departments")
def analytics_departments_view():
    return list_departments()


@bp.get("/analytics/stakeholders")
def analytics_stakeholders_view():
    return list_stakeholders()


@bp.get("/filters")
def filters():
    conn = get_reportable_connection()
    try:
        return ok(availability(conn))
    finally:
        conn.close()


@bp.get("/report-schema")
def report_schema():
    """The category-specific report column definitions (read-only).

    The preview, the exports and the on-screen tables all choose their columns
    from this one definition; exposing it keeps the contract explicit for any
    client.
    """
    from backend.database.category_report_schema import report_schema_payload
    return ok(report_schema_payload())


@bp.get("/reports/preview")
def report_preview():
    """JSON preview for the Report Generator (same dataset as downloads).

    ``columns`` is the category-specific column definition produced by the very
    same helper the XLSX/PDF exports use, so the preview table and the
    downloaded file always show identical columns.
    """
    from backend.reports.linkedin_exports import (
        REPORT_TYPES,
        _report_sheet_bytes,
        export_column_payload,
    )
    conn = get_reportable_connection()
    try:
        args = request.args.to_dict()
        scope = (args.get("scope") or "").lower()
        if scope and scope not in ("general", "departmental"):
            return error_response("scope must be 'general' or 'departmental'", 400)
        report_type = args.get("report_type") or "all"
        if report_type not in REPORT_TYPES:
            return error_response(
                "invalid report_type: use one of %s"
                % ", ".join(sorted(REPORT_TYPES)), 400)
        records, count, context, filter_args = _report_sheet_bytes(args, conn)
        from backend.database import linkedin_reportable as rep
        if filter_args.get("scope") == "general":
            cats = rep.analytics_categories(conn, filter_args)
            depts = []
            staks = rep.analytics_stakeholders(conn, filter_args)
        else:
            cats = rep.analytics_categories(conn, filter_args)
            depts = rep.analytics_departments(conn, filter_args)
            staks = rep.analytics_stakeholders(conn, filter_args)
        return ok({
            "report_type": report_type,
            "report_label": REPORT_TYPES[report_type][1],
            "context": context,
            "filters": filter_args,
            "columns": export_column_payload(filter_args, records),
            "total": count,
            "records": records,
            "breakdown": {
                "categories": cats,
                "departments": depts,
                "stakeholders": staks,
            },
        })
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/reports/export")
def report_export():
    """Download a report as .xlsx (format=xlsx) or .pdf (format=pdf)."""
    from backend.reports.linkedin_exports import build_excel, build_pdf
    fmt = (request.args.get("format") or "xlsx").lower()
    if fmt not in ("xlsx", "pdf"):
        return error_response("format must be 'xlsx' or 'pdf'", 400)
    conn = get_reportable_connection()
    try:
        args = request.args.to_dict()
        scope = (args.get("scope") or "").lower()
        if scope and scope not in ("general", "departmental"):
            return error_response("scope must be 'general' or 'departmental'", 400)
        if fmt == "xlsx":
            data, count, context = build_excel(args, conn)
            blob = BytesIO(data)
            blob.seek(0)
            return send_file(
                blob, as_attachment=True, download_name="tce_linkedin_report.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        data, count, context = build_pdf(args, conn)
        blob = BytesIO(data)
        blob.seek(0)
        return send_file(
            blob, as_attachment=True, download_name="tce_linkedin_report.pdf",
            mimetype="application/pdf")
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.route("/query", methods=["GET", "POST"])
def question():
    from backend.nlp.linkedin_query import answer_question
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
        question = (
            body.get("question")
            or request.args.get("q")
            or request.args.get("question")
            or ""
        ).strip()
    else:
        question = (
            request.args.get("q")
            or request.args.get("question")
            or ""
        ).strip()

    if not question:
        return error_response("missing 'question' (provide JSON body or 'q' query param)", 400)
    if len(question) > 500:
        return error_response("question too long (max 500 chars)", 400)
    result = answer_question(question)
    # Keep implementation details out of the public HTTP contract.
    return ok({key: result[key] for key in (
        "question", "status", "answer", "count", "activities",
        "comparison", "rows", "chart", "criteria", "detail",
        # The grounded selection, so the client reports the result with the
        # same category-specific columns as the Report Generator.
        "category_code", "scope", "department",
    ) if key in result})


@bp.get("/query/export")
def question_export():
    """Download the result set of a natural-language query (same result set)."""
    from backend.nlp.linkedin_query import answer_question
    from backend.reports.linkedin_exports import build_query_excel, build_query_pdf
    question = (request.args.get("q") or request.args.get("question") or "").strip()
    if not question:
        return error_response("missing 'q' query param", 400)
    if len(question) > 500:
        return error_response("question too long (max 500 chars)", 400)
    fmt = (request.args.get("format") or "xlsx").lower()
    if fmt not in ("xlsx", "pdf"):
        return error_response("format must be 'xlsx' or 'pdf'", 400)
    result = answer_question(question)
    if fmt == "xlsx":
        data = build_query_excel(result)
        blob = BytesIO(data)
        blob.seek(0)
        return send_file(
            blob, as_attachment=True, download_name="tce_linkedin_query_report.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    data = build_query_pdf(result)
    blob = BytesIO(data)
    blob.seek(0)
    return send_file(
        blob, as_attachment=True, download_name="tce_linkedin_query_report.pdf",
        mimetype="application/pdf")


@bp.get("/filters/availability")
def filter_availability():
    return filters()