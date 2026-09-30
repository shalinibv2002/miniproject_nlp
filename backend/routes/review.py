"""Review workflow endpoints (Phase 7)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.database.init_db import get_connection
from backend.review import service
from backend.routes.helpers import error_response, ok

bp = Blueprint("review", __name__, url_prefix="/api/review")


@bp.get("")
def review_queue():
    status = request.args.get("status", "open")
    if status not in service.REVIEW_STATUS:
        return error_response(f"valid statuses: {sorted(service.REVIEW_STATUS)}", 400)
    return ok({"items": service.queue_items(status=status)})


@bp.post("/queue")
def trigger_queue():
    n = service.queue_low_confidence()
    return ok({"queued": n})


@bp.post("/<int:activity_id>/edit")
def edit_field(activity_id):
    body = request.get_json(silent=True) or {}
    field = body.get("field")
    value = body.get("value")
    reviewer = (body.get("reviewer") or "anonymous").strip()
    if not field or value is None:
        return error_response("field and value are required", 400)
    if field not in service.EDITABLE_FIELDS:
        return error_response(f"field not editable; allowed: {sorted(service.EDITABLE_FIELDS)}", 400)
    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM institutional_activities WHERE id=?",
                        (activity_id,)).fetchone() is None:
            return error_response("activity not found", 404)
        service.edit_field(conn, activity_id, field, value, reviewer, body.get("reason", ""))
        return ok({"activity_id": activity_id, "field": field, "status": "updated"})
    finally:
        conn.close()


@bp.post("/<int:activity_id>/approve")
def approve_activity(activity_id):
    body = request.get_json(silent=True) or {}
    reviewer = (body.get("reviewer") or "anonymous").strip()
    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM institutional_activities WHERE id=?",
                        (activity_id,)).fetchone() is None:
            return error_response("activity not found", 404)
        service.approve(conn, activity_id, reviewer, body.get("reason", ""))
        return ok({"activity_id": activity_id, "status": "approved"})
    finally:
        conn.close()


@bp.post("/<int:activity_id>/reject")
def reject_activity(activity_id):
    body = request.get_json(silent=True) or {}
    reviewer = (body.get("reviewer") or "anonymous").strip()
    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM institutional_activities WHERE id=?",
                        (activity_id,)).fetchone() is None:
            return error_response("activity not found", 404)
        service.reject(conn, activity_id, reviewer, body.get("reason") or "rejected")
        return ok({"activity_id": activity_id, "status": "rejected"})
    finally:
        conn.close()


@bp.post("/<int:activity_id>/linkedin")
def record_linkedin(activity_id):
    body = request.get_json(silent=True) or {}
    reviewer = (body.get("reviewer") or "anonymous").strip()
    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM institutional_activities WHERE id=?",
                        (activity_id,)).fetchone() is None:
            return error_response("activity not found", 404)
        service.verify_linkedin(
            conn, activity_id,
            body.get("post_url", ""),
            reviewer,
            body.get("note", ""),
        )
        return ok({"activity_id": activity_id, "status": "linkedin-match-recorded"})
    finally:
        conn.close()