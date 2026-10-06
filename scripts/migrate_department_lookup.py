"""Bring the legacy `departments` lookup table in line with the 17-department
public master.

The public UI reads `final_activity_metadata.department_display` (normalised
read-time by backend.database.department_catalog) and never touches this table.
This table only feeds the legacy dictionary path
(backend.nlp.dictionaries.load_department_dict ->
backend.extractors.extract_department_mentions ->
backend.department_detector.populate_departments) and the NLQ department
resolver.  It is brought in line so the legacy path cannot resolve a bare
"mathematics" mention to Applied Mathematics.

Two additive changes, both idempotent:
  * Mathematics and Fashion Technology are added (they were in the scraped
    source but had no lookup row).
  * The AMCS row loses its bare "mathematics" / "maths" aliases, which is what
    used to merge the two departments.

Run:  python -m scripts.migrate_department_lookup
      python -m scripts.migrate_department_lookup --dry-run
"""

import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.department_catalog import PUBLIC_DEPARTMENTS  # noqa: E402
from backend.database.seed_reference_data import DEPARTMENTS as SEED_DEPARTMENTS  # noqa: E402

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "tce_activity_intelligence.db",
)

# Rows the legacy table must gain / have corrected.
ADDITIONS = ("MATHS", "FASH")
# Codes whose alias list changed and therefore need rewriting in place.
ALIAS_FIXES = ("MATH", "MATHS", "FASH", "PHY")


def _seed_row(code):
    for row in SEED_DEPARTMENTS:
        if row["code"] == code:
            return row
    raise KeyError("seed_reference_data has no department code %r" % code)


def migrate(db_path=DB_PATH, dry_run=False):
    if not os.path.exists(db_path):
        raise SystemExit("database not found: %s" % db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        have = {r["code"]: r for r in conn.execute(
            "SELECT id, code, name, short_name, aliases FROM departments")}
        actions = []

        for code in ADDITIONS:
            if code in have:
                continue
            row = _seed_row(code)
            if row["name"] not in PUBLIC_DEPARTMENTS:
                raise SystemExit(
                    "refusing to add %r: %r is not in the public department master"
                    % (code, row["name"]))
            actions.append(("insert", code, row["name"], row["aliases"]))

        for code in ALIAS_FIXES:
            if code not in have:
                continue
            row = _seed_row(code)
            if have[code]["aliases"] == row["aliases"]:
                continue
            actions.append(("update", code, have[code]["name"], row["aliases"]))

        if not actions:
            print("departments lookup table already matches the seed; nothing to do.")
            return []

        for action, code, name, aliases in actions:
            if action == "insert":
                print("insert %-6s %-52s %s" % (code, name, aliases))
                if not dry_run:
                    row = _seed_row(code)
                    conn.execute(
                        "INSERT INTO departments (code, name, short_name, aliases) "
                        "VALUES (?, ?, ?, ?)",
                        (row["code"], row["name"], row["short_name"], row["aliases"]),
                    )
            else:
                print("update %-6s %-52s %s" % (code, name, aliases))
                if not dry_run:
                    row = _seed_row(code)
                    conn.execute(
                        "UPDATE departments SET short_name = ?, aliases = ? WHERE code = ?",
                        (row["short_name"], row["aliases"], code),
                    )

        if dry_run:
            conn.rollback()
            print("\ndry run: %d change(s) rolled back." % len(actions))
        else:
            conn.commit()
            print("\napplied %d change(s)." % len(actions))

        total = conn.execute("SELECT COUNT(*) AS n FROM departments").fetchone()["n"]
        print("departments lookup rows: %d" % total)
        return actions
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    migrate(args.db, dry_run=args.dry_run)


if __name__ == "__main__":
    main()