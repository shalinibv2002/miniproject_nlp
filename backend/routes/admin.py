"""Protected Admin API endpoints (login, session, overview, CRUD)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.auth import (
    admin_required, create_token, current_admin, revoke_token, verify_credentials,
)
from backend.database.init_db import get_connection
from backend.routes.helpers import error_response, ok
from backend.admin import service

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _admin_name():
    return current_admin() or "admin"


@bp.post("/login")
def login():
    """Validate credentials and issue a bearer token for the session."""
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        return error_response("username and password are required", 400)
    if not verify_credentials(username, password):
        return error_response("Invalid username or password.", 401)
    token = create_token(username)
    return ok({"token": token, "username": username}, 200)


@bp.post("/logout")
@admin_required
def logout():
    revoke_token(request.headers.get("Authorization", "").removeprefix("Bearer ").strip())
    return ok({"status": "logged out"})


@bp.get("/session")
def session():
    """Confirm whether the current bearer token is still valid."""
    username = current_admin()
    if username is None:
        return ok({"authenticated": False})
    return ok({"authenticated": True, "username": username})


@bp.get("/overview")
@admin_required
def overview():
    return ok(service.overview())


@bp.get("/stakeholder-options")
@admin_required
def stakeholder_options():
    return ok({"stakeholders": service.public_stakeholder_names()})


@bp.get("/activities")
@admin_required
def list_activities():
    try:
        rows = service.list_activities(
            period=request.args.get("period") or None,
            department=request.args.get("department") or None,
            general_category=request.args.get("general_category") or None,
            departmental_category=request.args.get("departmental_category") or None,
            stakeholder=request.args.get("stakeholder") or None,
            search=request.args.get("q") or None,
            limit=min(int(request.args.get("limit", 200)), 500),
        )
        return ok({"data": rows, "total": len(rows)})
    except ValueError as exc:
        return error_response(str(exc), 400)


@bp.get("/activities/<int:activity_id>")
@admin_required
def get_activity(activity_id):
    conn = get_connection()
    try:
        item = service.activity_detail(conn=conn, activity_id=activity_id)
        if item is None:
            return error_response("activity not found", 404)
        return ok(item)
    finally:
        conn.close()


@bp.post("/activities")
@admin_required
def add_activity():
    body = request.get_json(silent=True) or {}
    try:
        activity_id, links = service.add_activity(data=body)
        return ok({"activity_id": activity_id, "status": "created",
                   "links": links}, 201)
    except (service.AdminValidationError, ValueError) as exc:
        return error_response(str(exc), 400)


@bp.put("/activities/<int:activity_id>")
@admin_required
def update_activity(activity_id):
    body = request.get_json(silent=True) or {}
    try:
        updated = service.update_activity(activity_id=activity_id, data=body)
        return ok({"activity_id": updated, "status": "updated"})
    except service.AdminValidationError as exc:
        message = str(exc)
        return error_response(message, 404 if "not found" in message else 400)
    except ValueError as exc:
        return error_response(str(exc), 400)


@bp.delete("/activities/<int:activity_id>")
@admin_required
def delete_activity(activity_id):
    conn = get_connection()
    try:
        try:
            service.delete_activity(conn=conn, activity_id=activity_id)
        except (service.AdminValidationError, ValueError) as exc:
            return error_response(str(exc), 404 if "not found" in str(exc) else 400)
        return ok({"activity_id": activity_id, "status": "deleted"})
    finally:
        conn.close()