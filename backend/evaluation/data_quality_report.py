"""Phase 13: data-quality report — pipeline provenance numbers.

Distinct from institutional activity statistics: reports how many raw
records entered the system, how many survived validation/dedup, and how
complete the final records are. All counted live from DB + saved raw files.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from backend.config import EVALUATION_DIR, RAW_DATA_DIR
from backend.database.pipeline import load_raw_records
from backend.database.init_db import get_connection


def data_quality_report(conn):
    raw_dirs = [os.path.join(RAW_DATA_DIR, d) for d in os.listdir(RAW_DATA_DIR)
                if os.path.isdir(os.path.join(RAW_DATA_DIR, d))]
    raw_records = 0
    raw_titles = set()
    raw_files = 0
    for d in raw_dirs:
        try:
            for rec in load_raw_records(d):
                raw_records += 1
                title = (rec.get("title") or "").strip()
                if title:
                    raw_titles.add(title.lower())
        except Exception:
            pass
    for d in raw_dirs:
        raw_files += len([f for f in os.listdir(d) if f.endswith(".json")])

    total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]

    def filled(column):
        return conn.execute(
            f"SELECT COUNT(*) AS c FROM institutional_activities WHERE {column} IS NOT NULL"
        ).fetchone()["c"]

    duplicates_auto = conn.execute(
        "SELECT COUNT(*) AS c FROM duplicate_candidates WHERE status='Auto-Merged'"
    ).fetchone()["c"]
    dup_pending = conn.execute(
        "SELECT COUNT(*) AS c FROM duplicate_candidates WHERE status='Pending'"
    ).fetchone()["c"]
    review_backlog = conn.execute(
        "SELECT COUNT(*) AS c FROM review_queue WHERE status IN ('open','in_progress')"
    ).fetchone()["c"]
    msg_counts = {}
    for r in conn.execute("SELECT match_status, COUNT(*) AS c FROM linkedin_matches GROUP BY match_status"):
        msg_counts[r["match_status"]] = r["c"]

    report = {
        "pipeline": {
            "raw_archive_files": raw_files,
            "raw_records_collected": raw_records,
            "unique_raw_events": len(raw_titles),
            "final_unique_activities": total,
            "duplicates_auto_merged": duplicates_auto,
            "duplicates_pending_review": dup_pending,
            "collection_errors_open": conn.execute(
                "SELECT COUNT(*) AS c FROM collection_errors WHERE status='open'"
            ).fetchone()["c"],
        },
        "completeness": {
            "total_records": total,
            "date_present": filled("activity_date"),
            "venue_present": filled("venue"),
            "organizer_present": filled("organizer"),
            "description_present": filled("description"),
            "source_present": filled("source_url"),
            "confidence_present": filled("overall_confidence"),
            "no_mapped_academic_year": conn.execute(
                "SELECT COUNT(*) AS c FROM institutional_activities WHERE activity_year_id IS NULL"
            ).fetchone()["c"],
        },
        "classification": {
            "unknown_category": total - conn.execute(
                "SELECT COUNT(DISTINCT activity_id) AS c FROM activity_categories"
            ).fetchone()["c"],
            "unknown_department": conn.execute(
                """SELECT COUNT(*) AS c FROM institutional_activities a
                   JOIN department_statuses ds ON ds.id = a.department_status_id
                   WHERE ds.code = 'unknown'"""
            ).fetchone()["c"],
            "low_confidence_below_0.6": conn.execute(
                "SELECT COUNT(*) AS c FROM institutional_activities WHERE overall_confidence < 0.6"
            ).fetchone()["c"],
        },
        "review_verification": {
            "review_backlog": review_backlog,
            "verified": conn.execute(
                "SELECT COUNT(*) AS c FROM institutional_activities WHERE is_verified=1"
            ).fetchone()["c"],
            "needs_review": conn.execute(
                """SELECT COUNT(*) AS c FROM institutional_activities a
                   JOIN verification_statuses v ON v.id=a.verification_status_id
                   WHERE v.code='needs_review'"""
            ).fetchone()["c"],
            "linkedin_by_status": msg_counts,
        },
    }

    os.makedirs(EVALUATION_DIR, exist_ok=True)
    with open(os.path.join(EVALUATION_DIR, "data_quality_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    rows = []
    for group, metrics in report.items():
        if isinstance(metrics, dict):
            for metric, value in metrics.items():
                if isinstance(value, (int, float, str)):
                    rows.append({"group": group, "metric": metric, "value": value})
    pd.DataFrame(rows).to_csv(
        os.path.join(EVALUATION_DIR, "data_quality_report.csv"), index=False
    )
    return report