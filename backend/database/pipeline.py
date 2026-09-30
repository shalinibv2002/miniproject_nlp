"""Pipeline: raw records -> clean -> validate -> dedupe -> load into DB."""

import json
import sys
import os
import glob
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.cleaner import clean_record, normalize_date
from backend.database.normalizer import to_normalized_title
from backend.database.validator import validate_record
from backend.database.deduplicator import deduplicate
from backend.database.init_db import get_connection

logger = logging.getLogger("tce.pipeline")


def load_raw_records(raw_dir):
    """Load all raw record JSON files from data/raw/<subdir>/."""
    records = []
    for path in sorted(glob.glob(os.path.join(raw_dir, "*.json"))):
        if path.endswith("metadata.json"):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            for record in payload.get("records", []):
                record.setdefault("_source_url", payload.get("source_url", ""))
                record.setdefault("_collected_at", payload.get("collected_at", ""))
                records.append(record)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping raw file %s: %s", path, exc)
    return records


def _academic_year_id(conn, date_str):
    if not date_str:
        return None
    year = int(date_str[:4])
    row = conn.execute(
        "SELECT id FROM academic_years WHERE start_year=? AND end_year=?",
        (year, year + 1),
    ).fetchone()
    return row["id"] if row else None


def _source_registry_id(conn, source_name):
    if not source_name:
        return None
    row = conn.execute(
        "SELECT id FROM source_registry WHERE name=? OR source_type=?",
        (source_name, source_name.lower()),
    ).fetchone()
    return row["id"] if row else None


def _pending_status_id(conn):
    return conn.execute(
        "SELECT id FROM verification_statuses WHERE code='pending'"
    ).fetchone()["id"]


def insert_activity(conn, record, source_registry_id, pending_status_id, max_title_len=400):
    title = (record.get("title") or "").strip()[:max_title_len]
    description = (record.get("description") or "").strip()
    activity_date = normalize_date(record.get("activity_date")) if record.get("activity_date") else None
    activity_date_end = (
        normalize_date(record.get("activity_date_end"))
        if record.get("activity_date_end")
        else None
    )
    norm_title = to_normalized_title(title)
    source_url = record.get("_source_url") or record.get("source_url") or "unknown"

    # Idempotency guard: re-running the pipeline over the same raw records
    # must NOT create a second copy of an existing activity.
    if activity_date:
        existing = conn.execute(
            "SELECT id FROM institutional_activities WHERE normalized_title=? AND activity_date=?",
            (norm_title, activity_date),
        ).fetchone()
    else:
        existing = conn.execute(
            "SELECT id FROM institutional_activities WHERE normalized_title=? AND activity_date IS NULL",
            (norm_title,),
        ).fetchone()
    if existing:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO activity_sources
                   (activity_id, source_registry_id, source_url, raw_record_id, collected_at)
                   VALUES (?, ?, ?, NULL, ?)""",
                (existing["id"], source_registry_id, source_url,
                 record.get("_collected_at") or datetime.now().isoformat()),
            )
        except Exception:  # noqa: BLE001
            pass
        return existing["id"]

    cur = conn.execute(
        """INSERT INTO institutional_activities
           (title, normalized_title, description, activity_date, activity_date_end,
            venue, organizer, resource_person, activity_year_id, verification_status_id,
            overall_confidence, is_verified, source_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)""",
        (
            title,
            norm_title,
            description,
            activity_date,
            activity_date_end,
            (record.get("venue") or "").strip() or None,
            (record.get("organizer") or "").strip() or None,
            (record.get("resource_person") or "").strip() or None,
            _academic_year_id(conn, activity_date),
            pending_status_id,
            0.5,
            source_url,
        ),
    )
    activity_id = cur.lastrowid

    try:
        conn.execute(
            """INSERT INTO activity_sources
               (activity_id, source_registry_id, source_url, raw_record_id, collected_at)
               VALUES (?, ?, ?, NULL, ?)""",
            (activity_id, source_registry_id, source_url,
             record.get("_collected_at") or datetime.now().isoformat()),
        )
    except Exception:  # noqa: BLE001
        pass  # UNIQUE conflict means the source row already exists
    return activity_id


def run_pipeline(raw_dirs=None, conn=None, limit=None):
    """Run clean -> validate -> dedupe -> load for the given raw dirs."""
    from backend.config import RAW_DATA_DIR

    if raw_dirs is None:
        raw_dirs = [os.path.join(RAW_DATA_DIR, d) for d in os.listdir(RAW_DATA_DIR)
                    if os.path.isdir(os.path.join(RAW_DATA_DIR, d))]

    own_conn = conn is None
    conn = conn or get_connection()
    pending_status_id = _pending_status_id(conn)
    stats = {"raw": 0, "cleaned": 0, "invalid": 0, "duplicates_auto": 0,
             "duplicates_pending": 0, "loaded": 0, "records": []}

    # Fresh diagnostics per run so data-quality numbers describe THIS run
    # (re-running the pipeline must remain reproducible).
    conn.execute("DELETE FROM collection_errors")
    conn.execute("DELETE FROM duplicate_candidates")
    conn.execute("DELETE FROM review_queue WHERE reason LIKE 'validation-flag%'")
    conn.commit()

    try:
        all_records = []
        for raw_dir in raw_dirs:
            if not os.path.isdir(raw_dir):
                continue
            all_records.extend(load_raw_records(raw_dir))
        stats["raw"] = len(all_records)

        cleaned = [clean_record(r) for r in all_records]
        valid_records = []
        review_flags = {}
        for record in cleaned:
            vr = validate_record(record)
            if vr.problems:
                stats["invalid"] += 1
                conn.execute(
                    """INSERT INTO collection_errors
                       (source_registry_id, url, stage, error_type, error_message, status)
                       VALUES (?, ?, 'validate', 'validation-flag', ?, 'open')""",
                    (
                        _source_registry_id(conn, record.get("source")),
                        record.get("_source_url") or record.get("source_url") or "",
                        ";".join(vr.problems),
                    ),
                )
            if vr.valid:
                review_flags[id(record)] = vr
                valid_records.append(record)

        deduped, candidates = deduplicate(valid_records)
        stats["duplicates_auto"] = sum(
            1 for c in candidates if c["status"] == "Auto-Merged"
        )
        stats["duplicates_pending"] = sum(
            1 for c in candidates if c["status"] == "Pending"
        )

        if limit:
            deduped = deduped[:limit]

        for record in deduped:
            src_id = _source_registry_id(conn, record.get("source"))
            activity_id = insert_activity(conn, record, src_id, pending_status_id)
            stats["loaded"] += 1
            vr = review_flags.get(id(record))
            if vr and vr.problems:
                still_open = conn.execute(
                    """SELECT 1 FROM review_queue
                       WHERE activity_id=? AND status IN ('open','in_progress')""",
                    (activity_id,),
                ).fetchone()
                if not still_open:
                    conn.execute(
                        """INSERT INTO review_queue (activity_id, reason, status)
                           VALUES (?, 'validation-flag: ' || ?, 'open')""",
                        (activity_id, ";".join(vr.problems)),
                    )

        for c in candidates:
            conn.execute(
                """INSERT INTO duplicate_candidates
                   (similarity_score, match_reason, status)
                   VALUES (?, ?, ?)""",
                (c["similarity_score"], c["match_reason"], c["status"]),
            )

        conn.commit()
        stats["records"] = [
            {
                "title": r.get("title"),
                "activity_date": r.get("activity_date"),
                "source_url": r.get("_source_url") or r.get("source_url"),
            }
            for r in deduped
        ]
        return stats
    except Exception:
        conn.rollback()
        raise
    finally:
        if own_conn:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    stats = run_pipeline()
    print(json.dumps(stats, indent=2, ensure_ascii=False))