"""Admin-only Flask routes for the Apify LinkedIn sync.

Protected endpoints (require @admin_required):
  GET  /api/admin/apify/status        — sync status + last checkpoint
  POST /api/admin/apify/sync          — trigger manual sync (concurrent-safe)

Public endpoints (no auth — minimal data only, safe for Dashboard):
  GET  /api/admin/apify/notification      — pending notification (counts only)
  POST /api/admin/apify/notification/seen — mark notification seen

Security:
  * The APIFY_API_TOKEN is NEVER included in any response.
  * Status / sync endpoints are protected by @admin_required.
  * Notification endpoint returns ONLY: run_id, new_activities,
    review_required, finished_at — no internals, no tokens, no DB details.
"""

import logging

from flask import Blueprint, request

from backend.auth import admin_required
from backend.routes.helpers import error_response, ok

logger = logging.getLogger("tce.routes.apify")

bp = Blueprint("apify_admin", __name__, url_prefix="/api/admin/apify")


@bp.get("/status")
@admin_required
def sync_status():
    """Return current sync status, last checkpoint, and run counts."""
    try:
        from backend.apify.sync_state import get_apify_connection, get_sync_status
        from backend.apify.scheduler import is_sync_running

        conn = get_apify_connection()
        try:
            status = get_sync_status(conn)
        finally:
            conn.close()

        # Override is_running from the scheduler lock for accuracy
        status["is_running"] = is_sync_running()
        return ok(status)
    except Exception as exc:
        logger.error("sync_status failed: %s", exc)
        return error_response("Unable to fetch sync status.", 500)


@bp.post("/sync")
@admin_required
def trigger_sync():
    """Trigger a manual Apify sync.

    Uses the same safe ingestion pipeline as the weekly scheduler.
    Only one sync may run at a time; returns 409 if one is already running.
    Optional body param: ``mock=true`` uses mock posts (for testing).
    """
    body = request.get_json(silent=True) or {}
    use_mock = str(body.get("mock", "false")).lower() in ("1", "true", "yes")

    try:
        from backend.apify.scheduler import run_manual_sync
        result = run_manual_sync(use_mock=use_mock)
        # Strip any sensitive fields before returning (none expected, but guard)
        safe = {k: v for k, v in result.items()
                if k not in ("error_detail", "apify_token")}
        return ok(safe)
    except RuntimeError as exc:
        # Concurrent sync running
        return error_response(str(exc), 409)
    except Exception as exc:
        logger.error("Manual sync failed: %s", exc)
        return error_response("Sync failed. Check server logs.", 500)


@bp.get("/notification")
def get_notification():
    """Return pending sync notification for the user dashboard.

    This endpoint does NOT require admin auth — it is called by the
    user-facing Dashboard to display sync notifications.
    Uses REAL counts from the database; never hard-coded.
    """
    try:
        from backend.apify.sync_state import get_apify_connection
        from backend.apify.ingestion import get_pending_notification

        conn = get_apify_connection()
        try:
            notification = get_pending_notification(conn)
        finally:
            conn.close()

        if notification is None:
            return ok({"notification": None})

        # Explicit field allowlist — never leak internals, token, or DB details
        safe_notification = {
            "run_id":         notification.get("run_id"),
            "new_activities": notification.get("new_activities"),
            "review_required":notification.get("review_required"),
            "finished_at":    notification.get("finished_at"),
        }
        return ok({"notification": safe_notification})
    except Exception as exc:
        logger.error("get_notification failed: %s", exc)
        return ok({"notification": None})


@bp.post("/notification/seen")
def mark_notification_seen():
    """Mark a notification as seen (no duplicate notification for same sync)."""
    body = request.get_json(silent=True) or {}
    run_id = body.get("run_id")
    if run_id is not None:
        try:
            from backend.apify.ingestion import mark_notification_seen
            mark_notification_seen(int(run_id))
        except Exception:
            pass
    return ok({"ok": True})
