"""Lightweight role-based authentication for the demo project.

A practical, token-based session over the existing Flask backend: users sign in
once, receive a random bearer token, and protected routes require that token.
Tokens live in-process (a restart signs users out), which is deliberately
simple and appropriate for a college project.

Two roles are supported: ``admin`` and ``user``.  Admin credentials are
configured in ``backend.config``; a separate user account is also configured
there.  No plaintext password is ever stored or returned.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from functools import wraps

from flask import request

from backend.config import (
    ADMIN_PASSWORD_HASH,
    ADMIN_SESSION_TTL_SECONDS,
    ADMIN_USERNAME,
    USER_PASSWORD_HASH,
    USER_SESSION_TTL_SECONDS,
    USER_USERNAME,
)
from backend.routes.helpers import error_response

# token -> {"username": str, "role": str, "expires_at": float}
_tokens: dict = {}
_lock = threading.Lock()


def _digest(password: str) -> str:
    return hashlib.sha256((password or "").encode("utf-8")).hexdigest()


def verify_admin_credentials(username: str, password: str) -> bool:
    """Return True only when both the username and password match admin creds."""
    user_ok = (username or "").strip() == ADMIN_USERNAME
    pass_ok = hmac.compare_digest(_digest(password), ADMIN_PASSWORD_HASH)
    return user_ok and pass_ok


def verify_user_credentials(username: str, password: str) -> bool:
    """Return True only when both the username and password match user creds."""
    user_ok = (username or "").strip() == USER_USERNAME
    pass_ok = hmac.compare_digest(_digest(password), USER_PASSWORD_HASH)
    return user_ok and pass_ok


def verify_credentials(username: str, password: str) -> bool:
    """Return True for admin credentials (backward compatibility)."""
    return verify_admin_credentials(username, password)


def create_token(username: str, role: str = "admin") -> str:
    """Issue a fresh bearer token for a successfully authenticated user."""
    token = secrets.token_urlsafe(32)
    ttl = ADMIN_SESSION_TTL_SECONDS if role == "admin" else USER_SESSION_TTL_SECONDS
    with _lock:
        _tokens[token] = {
            "username": (username or "").strip(),
            "role": role,
            "expires_at": time.time() + ttl,
        }
    return token


def validate_token(token) -> dict | None:
    """Return {"username": str, "role": str} or None for invalid/expired tokens."""
    if not token:
        return None
    with _lock:
        entry = _tokens.get(token)
        if entry is None:
            return None
        if time.time() > entry["expires_at"]:
            _tokens.pop(token, None)
            return None
        return {"username": entry["username"], "role": entry["role"]}


def revoke_token(token) -> bool:
    """Sign a token out; returns True when a session was actually revoked."""
    with _lock:
        return _tokens.pop(token, None) is not None


def bearer_token() -> str | None:
    """Read the bearer token from the Authorization header, if present."""
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:].strip()
    return None


def current_user() -> str | None:
    """The authenticated username for this request, or None (any role)."""
    info = validate_token(bearer_token())
    return info["username"] if info else None


def current_admin() -> str | None:
    """The authenticated admin username for this request, or None."""
    info = validate_token(bearer_token())
    if info and info["role"] == "admin":
        return info["username"]
    return None


def current_role() -> str | None:
    """The role of the current authenticated user, or None."""
    info = validate_token(bearer_token())
    return info["role"] if info else None


def admin_required(view):
    """Decorator: reject unauthenticated or non-admin access to a protected route."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_admin() is None:
            return error_response("authentication required", 401)
        return view(*args, **kwargs)

    return wrapped


def login_required(view):
    """Decorator: reject unauthenticated access (any role)."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            return error_response("authentication required", 401)
        return view(*args, **kwargs)

    return wrapped
