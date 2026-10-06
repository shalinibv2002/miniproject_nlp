"""Apify sync state management.

Persists checkpoint / resume state and sync run metadata in a dedicated
table within the LinkedIn staging database.  This keeps all LinkedIn
provenance data in one place and avoids any risk of touching the main
institutional activities database.

HARD GUARANTEES:
  * Only linkedin_staging.db is opened for writing here.
  * The main database (tce_activity_intelligence.db) is never touched.
  * The reportable database is never modified directly here.
  * Admin manual overrides and existing canonical records are never changed.
"""

import json
import os
import sqlite3
from datetime import datetime

from backend.database.linkedin_staging import STAGING_DB_PATH, get_staging_connection

# DDL for Apify-specific tables (additive migrations only)
APIFY_SCHEMA = """
CREATE TABLE IF NOT EXISTS apify_sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'partial')),
    -- Real counts from the sync pipeline (never hard-coded)
    fetched INTEGER NOT NULL DEFAULT 0,
    new_posts INTEGER NOT NULL DEFAULT 0,
    duplicates INTEGER NOT NULL DEFAULT 0,
    classified INTEGER NOT NULL DEFAULT 0,
    review_required INTEGER NOT NULL DEFAULT 0,
    non_activity INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    -- Checkpoint / resume support
    last_checkpoint TEXT,           -- opaque cursor returned by Apify actor
    apify_run_id TEXT,              -- Apify run ID for this sync
    notes TEXT
);

CREATE TABLE IF NOT EXISTS apify_sync_checkpoint (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_sync_run_id INTEGER REFERENCES apify_sync_runs(id),
    -- The continuation token / cursor from the last successfully processed post.
    -- This is the ACTUAL Apify cursor, not a simple post number.
    last_cursor TEXT,
    last_processed_post_id TEXT,    -- Apify post ID of the last processed post
    last_processed_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS apify_ingested_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Strongest available identifier: LinkedIn activity URN ID
    apify_post_id TEXT NOT NULL UNIQUE,     -- from Apify response (activity ID / URN)
    post_url TEXT,                          -- LinkedIn post URL
    normalized_text TEXT,                   -- for text-based dedup fallback
    -- Link to staging layer (set after staging insert)
    staging_post_id INTEGER,                -- linkedin_posts.id (if inserted)
    -- Classification result
    reportable_status TEXT
        CHECK (reportable_status IN ('REPORTABLE', 'NON_ACTIVITY', 'REVIEW_REQUIRED', NULL)),
    -- Provenance
    sync_run_id INTEGER NOT NULL REFERENCES apify_sync_runs(id),
    ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (sync_run_id) REFERENCES apify_sync_runs(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_apify_post_id
    ON apify_ingested_posts(apify_post_id);
CREATE INDEX IF NOT EXISTS idx_apify_sync_run
    ON apify_ingested_posts(sync_run_id);
CREATE INDEX IF NOT EXISTS idx_apify_post_url
    ON apify_ingested_posts(post_url) WHERE post_url IS NOT NULL;
"""


def ensure_apify_schema(conn):
    """Create Apify tables if they do not already exist.  Idempotent."""
    conn.executescript(APIFY_SCHEMA)
    conn.commit()


def get_apify_connection(db_path=None):
    """Open connection to the staging DB (which hosts Apify sync tables)."""
    conn = get_staging_connection(db_path or STAGING_DB_PATH)
    ensure_apify_schema(conn)
    return conn


# ---------------------------------------------------------------------------
# Sync run lifecycle
# ---------------------------------------------------------------------------

def start_sync_run(conn):
    """Create a new sync run record and return its ID."""
    cur = conn.execute(
        """INSERT INTO apify_sync_runs (started_at, status)
           VALUES (datetime('now'), 'running')"""
    )
    conn.commit()
    return cur.lastrowid


def finish_sync_run(conn, run_id, status, counts, apify_run_id=None, notes=None):
    """Finalize a sync run with counts and status."""
    conn.execute(
        """UPDATE apify_sync_runs
           SET finished_at = datetime('now'),
               status = ?,
               fetched = ?,
               new_posts = ?,
               duplicates = ?,
               classified = ?,
               review_required = ?,
               non_activity = ?,
               errors = ?,
               apify_run_id = ?,
               notes = ?
           WHERE id = ?""",
        (
            status,
            counts.get("fetched", 0),
            counts.get("new_posts", 0),
            counts.get("duplicates", 0),
            counts.get("classified", 0),
            counts.get("review_required", 0),
            counts.get("non_activity", 0),
            counts.get("errors", 0),
            apify_run_id,
            notes,
            run_id,
        ),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Checkpoint management
# ---------------------------------------------------------------------------

def get_checkpoint(conn):
    """Return the current checkpoint row, or None if none exists."""
    return conn.execute(
        "SELECT * FROM apify_sync_checkpoint WHERE id = 1"
    ).fetchone()


def save_checkpoint(conn, run_id, cursor, post_id):
    """Save checkpoint after successfully processing one post.

    Only call this AFTER the post is safely committed to the database.
    The checkpoint is updated atomically with the commit, so a crash
    after commit but before checkpoint update is safe (the next run will
    see the post as a duplicate and skip it via the dedup layer).
    """
    conn.execute(
        """INSERT INTO apify_sync_checkpoint (id, last_sync_run_id, last_cursor,
               last_processed_post_id, last_processed_at, updated_at)
           VALUES (1, ?, ?, ?, datetime('now'), datetime('now'))
           ON CONFLICT(id) DO UPDATE SET
               last_sync_run_id = excluded.last_sync_run_id,
               last_cursor = excluded.last_cursor,
               last_processed_post_id = excluded.last_processed_post_id,
               last_processed_at = excluded.last_processed_at,
               updated_at = excluded.updated_at""",
        (run_id, cursor, post_id),
    )
    # NOTE: caller must commit to make this durable.


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------

def is_duplicate(conn, apify_post_id, post_url=None, normalized_text=None):
    """Return True if this post has already been processed by Apify ingestion.

    Checks by:
      1. apify_post_id (strongest — exact Apify internal ID)
      2. post_url (LinkedIn URL)
      3. normalized_text (fallback text match)

    This is a SECOND SAFETY LAYER; the primary dedup is the staging layer's
    existing deduplication logic (URL + text-exact + near-exact).
    """
    # Check 1: Apify post ID (strongest)
    if apify_post_id:
        row = conn.execute(
            "SELECT id FROM apify_ingested_posts WHERE apify_post_id = ?",
            (apify_post_id,),
        ).fetchone()
        if row:
            return True

    # Check 2: LinkedIn URL
    if post_url:
        row = conn.execute(
            "SELECT id FROM apify_ingested_posts WHERE post_url = ?",
            (post_url,),
        ).fetchone()
        if row:
            return True

    # Check 3: check existing staging posts (the pre-Apify dataset)
    if post_url:
        # Extract activity ID from URL for strongest match
        import re
        m = re.search(r"activity[:\-/?=_]*(\d+)", post_url, re.I)
        if m:
            aid = m.group(1)
            row = conn.execute(
                "SELECT id FROM linkedin_posts WHERE activity_id = ?", (aid,)
            ).fetchone()
            if row:
                return True
        # Exact URL match in staging
        row = conn.execute(
            "SELECT id FROM linkedin_posts WHERE post_url = ?", (post_url,)
        ).fetchone()
        if row:
            return True

    # Check 4: normalized text match in staging
    if normalized_text:
        row = conn.execute(
            "SELECT id FROM linkedin_posts WHERE normalized_text = ?",
            (normalized_text,),
        ).fetchone()
        if row:
            return True

    return False


def record_ingested_post(conn, run_id, apify_post_id, post_url,
                         normalized_text, staging_post_id, reportable_status):
    """Record that a post has been ingested in this sync run."""
    conn.execute(
        """INSERT OR IGNORE INTO apify_ingested_posts
           (apify_post_id, post_url, normalized_text, staging_post_id,
            reportable_status, sync_run_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (apify_post_id, post_url, normalized_text, staging_post_id,
         reportable_status, run_id),
    )


# ---------------------------------------------------------------------------
# Admin sync status query
# ---------------------------------------------------------------------------

def get_sync_status(conn):
    """Return sync status dict for the Admin Sync Status section."""
    last_run = conn.execute(
        """SELECT * FROM apify_sync_runs
           WHERE status IN ('completed', 'failed', 'partial')
           ORDER BY id DESC LIMIT 1"""
    ).fetchone()

    running = conn.execute(
        "SELECT * FROM apify_sync_runs WHERE status = 'running' ORDER BY id DESC LIMIT 1"
    ).fetchone()

    checkpoint = conn.execute(
        "SELECT * FROM apify_sync_checkpoint WHERE id = 1"
    ).fetchone()

    result = {
        "is_running": running is not None,
        "last_sync": None,
        "last_checkpoint": None,
        "fetched": 0,
        "new_posts": 0,
        "duplicates": 0,
        "classified": 0,
        "review_required": 0,
        "non_activity": 0,
        "errors": 0,
    }

    if last_run:
        result.update({
            "last_sync": last_run["finished_at"],
            "fetched": last_run["fetched"],
            "new_posts": last_run["new_posts"],
            "duplicates": last_run["duplicates"],
            "classified": last_run["classified"],
            "review_required": last_run["review_required"],
            "non_activity": last_run["non_activity"],
            "errors": last_run["errors"],
            "last_run_status": last_run["status"],
        })

    if checkpoint:
        result["last_checkpoint"] = checkpoint["last_processed_at"]

    return result
