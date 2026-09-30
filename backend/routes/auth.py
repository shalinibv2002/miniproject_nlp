"""Public auth endpoints: login, session, logout (supports admin and user roles)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.auth import (
    create_token, current_user, current_role, revoke_token,
    verify_admin_credentials,
)
from backend.routes.helpers import error_response, ok

bp = Blueprint("auth", __name__, url_prefix="/api")


@bp.post("/login")
def login():
    """Validate credentials and issue a bearer token.

    Accepts {username, password}.  The exact admin credentials are the only
    way to sign in as ``admin``; every other username/password combination
    signs in as a standard ``user``.  Returns {token, username, role} on
    success.
    """
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = body.get("password") or ""
    if not username or not password:
        return error_response("username and password are required", 400)

    if verify_admin_credentials(username, password):
        token = create_token(username, role="admin")
        return ok({"token": token, "username": username, "role": "admin"}, 200)

    # Any other valid combination enters as a standard user.
    token = create_token(username, role="user")
    return ok({"token": token, "username": username, "role": "user"}, 200)


@bp.get("/session")
def session():
    """Confirm whether the current bearer token is still valid."""
    username = current_user()
    if username is None:
        return ok({"authenticated": False})
    return ok({"authenticated": True, "username": username, "role": current_role()})


@bp.post("/logout")
def logout():
    """Revoke the current bearer token."""
    revoke_token(request.headers.get("Authorization", "").removeprefix("Bearer ").strip())
    return ok({"status": "logged out"})
