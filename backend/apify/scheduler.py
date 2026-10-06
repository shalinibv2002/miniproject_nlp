"""Weekly Apify scheduler.

Schedules the LinkedIn sync to run every Monday at 09:00 Asia/Kolkata.

Design:
  * The scheduler is SEPARATE from the ingestion service.  The same
    run_apify_sync() function is used by both the scheduler and the
    Admin "Run Update Now" button — no code duplication.
  * At most one sync may run at a time (lock enforced via sync_state).
  * The scheduler does NOT run on page load or when the frontend starts.
  * No infinite retries; a failed sync logs the error and waits for
    the next scheduled window.
"""

import logging
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger("tce.apify.scheduler")

# Scheduler state
_scheduler_thread = None
_scheduler_lock = threading.Lock()
_scheduler_running = False

# Sync lock: prevents concurrent syncs from the scheduler AND admin button
_sync_lock = threading.Lock()

# Asia/Kolkata = UTC+5:30
_IST_OFFSET_HOURS = 5
_IST_OFFSET_MINUTES = 30

# Monday = 0 in Python's weekday()
_MONDAY = 0
_SYNC_HOUR = 9    # 09:00
_SYNC_MINUTE = 0


def _is_sync_time():
    """Return True if the current IST time matches the scheduled slot."""
    utc_now = datetime.now(timezone.utc)
    # Convert to IST (UTC+5:30)
    ist_seconds = utc_now.timestamp() + (_IST_OFFSET_HOURS * 3600 + _IST_OFFSET_MINUTES * 60)
    ist_now = datetime.utcfromtimestamp(ist_seconds)
    return (
        ist_now.weekday() == _MONDAY
        and ist_now.hour == _SYNC_HOUR
        and ist_now.minute == _SYNC_MINUTE
    )


def _run_scheduled_sync():
    """Run the Apify sync in a background thread, respecting the sync lock."""
    if not _sync_lock.acquire(blocking=False):
        logger.info("Scheduler: sync already running, skipping this slot.")
        return

    try:
        logger.info("Scheduler: starting scheduled Apify sync.")
        from backend.apify.ingestion import run_apify_sync
        result = run_apify_sync()
        logger.info("Scheduler: sync completed. result=%s", result)
    except Exception as exc:
        logger.error("Scheduler: sync failed: %s", exc)
    finally:
        _sync_lock.release()


def _scheduler_loop(check_interval=60):
    """Main scheduler loop.  Checks every `check_interval` seconds."""
    global _scheduler_running
    last_run_date = None

    logger.info("Scheduler loop started (interval=%ds).", check_interval)
    while _scheduler_running:
        try:
            if _is_sync_time():
                today = datetime.utcnow().date()
                if last_run_date != today:
                    last_run_date = today
                    t = threading.Thread(
                        target=_run_scheduled_sync,
                        name="apify-scheduled-sync",
                        daemon=True,
                    )
                    t.start()
        except Exception as exc:
            logger.error("Scheduler loop error: %s", exc)
        time.sleep(check_interval)

    logger.info("Scheduler loop stopped.")


def start_scheduler():
    """Start the background scheduler thread (idempotent)."""
    global _scheduler_thread, _scheduler_running

    with _scheduler_lock:
        if _scheduler_thread and _scheduler_thread.is_alive():
            logger.debug("Scheduler already running.")
            return

        _scheduler_running = True
        _scheduler_thread = threading.Thread(
            target=_scheduler_loop,
            name="apify-scheduler",
            daemon=True,
        )
        _scheduler_thread.start()
        logger.info("Apify scheduler started (Monday 09:00 IST).")


def stop_scheduler():
    """Stop the background scheduler thread."""
    global _scheduler_running
    _scheduler_running = False
    logger.info("Apify scheduler stop requested.")


def is_sync_running():
    """Return True if a sync is currently in progress."""
    return not _sync_lock.acquire(blocking=False) or (
        _sync_lock.release() or False
    )


def run_manual_sync(use_mock=False):
    """Run a manual sync (Admin 'Run Update Now').

    Reuses the same ingestion function as the scheduler.
    Returns the sync result dict or raises RuntimeError if already running.
    """
    if not _sync_lock.acquire(blocking=False):
        raise RuntimeError("A sync is already running. Please wait for it to complete.")

    try:
        logger.info("Manual sync started (use_mock=%s).", use_mock)
        from backend.apify.ingestion import run_apify_sync
        result = run_apify_sync(use_mock=use_mock)
        logger.info("Manual sync completed: %s", result)
        return result
    finally:
        _sync_lock.release()
