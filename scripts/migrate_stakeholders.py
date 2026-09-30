"""Remap activities whose stakeholder display is unknown to ``Students``.

Stage 6 data refinement: institution-wide and departmental activities without
a resolved stakeholder were reported publicly as "Not available".  Every such
activity at TCE involves students, so the remaining NULL ``stakeholder_display``
rows are remapped to ``Students`` and linked in ``activity_stakeholders`` when a
link is not already present.  No literal "Not available" strings exist.

Usage:
    python scripts/migrate_stakeholders.py            # migrate
    python scripts/migrate_stakeholders.py --dry-run  # preview only

Exits non-zero if the checks fail.
"""

import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "tce_activity_intelligence.db"
STUDENTS = "Students"


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def migrate(dry_run=False):
    conn = connect()
    try:
        cur = conn.cursor()

        null_rows = cur.execute(
            "SELECT COUNT(*) AS c FROM final_activity_metadata "
            "WHERE stakeholder_display IS NULL").fetchone()["c"]
        literal = cur.execute(
            "SELECT COUNT(*) AS c FROM final_activity_metadata "
            "WHERE stakeholder_display = 'Not available'").fetchone()["c"]

        print(f"stakeholder_display IS NULL      : {null_rows}")
        print(f"stakeholder_display = 'Not available': {literal}")

        if literal:
            raise SystemExit("Unexpected literal 'Not available' records; aborting.")

        metadatas = cur.execute(
            "SELECT activity_id FROM final_activity_metadata "
            "WHERE stakeholder_display IS NULL ORDER BY activity_id").fetchall()
        already_linked = cur.execute(
            """SELECT COUNT(*) AS c FROM final_activity_metadata m
               WHERE m.stakeholder_display IS NULL
                 AND EXISTS (SELECT 1 FROM activity_stakeholders s
                             WHERE s.activity_id = m.activity_id)""").fetchone()["c"]
        print(f"NULL rows already carrying a link: {already_linked}")

        if dry_run:
            print(f"[dry-run] Would remap {len(metadatas)} NULL rows to '{STUDENTS}' "
                  f"and link them to the Students stakeholder.")
            return

        ids = [row["activity_id"] for row in metadatas]
        for activity_id in ids:
            cur.execute(
                "UPDATE final_activity_metadata SET stakeholder_display = ? "
                "WHERE activity_id = ?", (STUDENTS, activity_id))
            cur.execute(
                "INSERT OR IGNORE INTO activity_stakeholders (activity_id, stakeholder_id) "
                "VALUES (?, (SELECT id FROM stakeholders WHERE name = ?))",
                (activity_id, STUDENTS))
        conn.commit()

        remaining = cur.execute(
            "SELECT COUNT(*) AS c FROM final_activity_metadata "
            "WHERE stakeholder_display IS NULL").fetchone()["c"]
        linked = cur.execute(
            "SELECT COUNT(*) AS c FROM activity_stakeholders s "
            "JOIN stakeholders st ON st.id = s.stakeholder_id "
            "WHERE st.name = ?", (STUDENTS,)).fetchone()["c"]
        orphans = cur.execute(
            "SELECT COUNT(*) AS c FROM activity_stakeholders s "
            "LEFT JOIN institutional_activities a ON a.id = s.activity_id "
            "WHERE a.id IS NULL").fetchone()["c"]
        duplicates = cur.execute(
            "SELECT COUNT(*) AS c FROM (SELECT activity_id, stakeholder_id "
            "FROM activity_stakeholders GROUP BY activity_id, stakeholder_id "
            "HAVING COUNT(*) > 1)").fetchone()["c"]

        print(f"[done]      Remapped {len(ids)} rows to '{STUDENTS}'.")
        print(f"[verified]  remaining NULL stakeholder_display : {remaining}")
        print(f"[verified]  students links                      : {linked}")
        print(f"[verified]  orphan links                        : {orphans}")
        print(f"[verified]  duplicate pairs                     : {duplicates}")

        if remaining or orphans or duplicates:
            raise SystemExit("Post-migration checks failed.")
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="report what would change without modifying the database")
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)