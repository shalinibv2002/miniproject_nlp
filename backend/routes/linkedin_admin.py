"""Protected Admin API for the FINAL LinkedIn REPORTABLE dataset.

All endpoints read/write ONLY ``backend/database/linkedin_reportable.db``.
Every route is guarded by ``admin_required`` (bearer token).  Only the fields
listed in ``ADMIN_EDITABLE_FIELDS`` may be changed; immutable provenance and
internal evidence are never editable.  Every edit is recorded in
``validation_history``.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.auth import admin_required, current_admin
from backend.database.linkedin_reportable import (
    admin_options,
    admin_record,
    admin_review_queue,
    admin_summary,
    admin_update,
    count_reportable,
    filters_fragment,
    get_reportable_connection,
    publish_record,
)
from backend.routes.helpers import error_response, ok, paginate_args, page_response

bp = Blueprint("linkedin_admin", __name__, url_prefix="/api/admin/linkedin")

# Server-side sortable columns for the admin list (single-table plus the
# normalized join columns; expressions are whitelisted, never interpolated
# from client input).
ADMIN_SORT_COLUMNS = {
    "activity_id": "r.activity_id",
    "title": "r.title COLLATE NOCASE",
    "activity_date": "r.activity_date",
    "academic_year": "r.academic_year",
    "evidence_score": "r.evidence_score",
    "reportable_status": "r.reportable_status",
    "review_status": "r.review_status",
    "category": "(SELECT ac.category_code FROM linkedin_activity_categories ac "
                "WHERE ac.activity_id = r.activity_id LIMIT 1)",
    "department": "(SELECT ad.department FROM linkedin_activity_departments ad "
                  "WHERE ad.activity_id = r.activity_id LIMIT 1)",
    "stakeholder": "(SELECT ast.stakeholder FROM linkedin_activity_stakeholders ast "
                   "WHERE ast.activity_id = r.activity_id LIMIT 1)",
}


def _reviewer():
    return current_admin() or "admin"


def _admin_order_by():
    sort = (request.args.get("sort") or "activity_id").lower()
    if sort not in ADMIN_SORT_COLUMNS:
        raise ValueError("sort must be one of: %s"
                         % ", ".join(sorted(ADMIN_SORT_COLUMNS)))
    direction = (request.args.get("order") or "asc").lower()
    if direction not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    return "%s %s, r.activity_id ASC" % (ADMIN_SORT_COLUMNS[sort],
                                         direction.upper())


@bp.get("/activities")
@admin_required
def list_activities():
    conn = get_reportable_connection()
    try:
        args = request.args.to_dict()
        where, params = filters_fragment(args)
        total = count_reportable(conn, args)
        offset, page_size = paginate_args()
        rows = conn.execute(
            "SELECT * FROM linkedin_reportable_activities r" + where +
            " ORDER BY " + _admin_order_by() + " LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        items = [admin_record(r) for r in rows]
        return ok(page_response(items, total, offset // page_size + 1, page_size))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/activities/<activity_id>")
@admin_required
def get_activity(activity_id):
    conn = get_reportable_connection()
    try:
        row = conn.execute(
            "SELECT * FROM linkedin_reportable_activities WHERE activity_id = ?",
            (activity_id,),
        ).fetchone()
        if row is None:
            return error_response("activity not found", 404)
        return ok(admin_record(row))
    finally:
        conn.close()


@bp.patch("/activities/<activity_id>")
@admin_required
def update_activity(activity_id):
    body = request.get_json(silent=True) or {}
    if not body:
        return error_response("empty PATCH body", 400)
    conn = get_reportable_connection()
    try:
        updated = admin_update(
            conn, activity_id, body,
            reviewer=_reviewer(),
            note=body.get("_note") or request.args.get("note"),
        )
        if updated is None:
            return error_response("activity not found", 404)
        return ok(updated)
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.post("/activities/<activity_id>/publish")
@admin_required
def publish_activity(activity_id):
    """Explicit "Save & Publish".  Never done behind the admin's back: this is
    the single sanctioned promotion to public REPORTABLE (see publish_record in
    linkedin_reportable).  Any editable fields carried in the body are persisted
    with the same rule-set as PATCH before the record is promoted."""
    body = request.get_json(silent=True) or {}
    conn = get_reportable_connection()
    try:
        note = body.get("_note") or request.args.get("note")
        editable = {key: value for key, value in body.items() if key in (
            "title", "description", "categories", "departments",
            "stakeholders", "activity_date", "academic_year")}
        if editable:
            admin_update(conn, activity_id, editable, reviewer=_reviewer(), note=note)
        updated = publish_record(
            conn, activity_id, reviewer=_reviewer(), note=note)
        if updated is None:
            return error_response("activity not found", 404)
        return ok(updated)
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/summary")
@admin_required
def summary():
    conn = get_reportable_connection()
    try:
        return ok(admin_summary(conn))
    finally:
        conn.close()


@bp.get("/options")
@admin_required
def options():
    conn = get_reportable_connection()
    try:
        return ok(admin_options(conn))
    finally:
        conn.close()


@bp.get("/review-queue")
@admin_required
def review_queue():
    conn = get_reportable_connection()
    try:
        items = admin_review_queue(conn, request.args.to_dict())
        return ok({"data": items, "total": len(items)})
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()