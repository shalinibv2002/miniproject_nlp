"""Give every reportable LinkedIn activity exactly one primary category.

Run:  python scripts/migrate_single_category_20261002.py [--apply]

Without ``--apply`` this is a dry run and prints what would change.

Rules
-----
* A human decision (``manual_overrides.categories``) is ground truth and wins.
* A post with one confidently resolved category becomes ``categories=[code]``.
* A genuinely ambiguous post becomes ``REVIEW_REQUIRED`` with no category.
* A clear non-activity (a bare holiday wish) becomes ``NON_ACTIVITY``.
* Nothing is ever forced: an undecided row keeps no category at all.

Only rows that are currently ``REPORTABLE`` are touched.  Provenance is
appended to ``validation_history``; ``manual_overrides``,
``is_manually_validated``, departments, dates and academic years are preserved.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import primary_category  # noqa: E402
from backend.database.linkedin_reportable import (  # noqa: E402
    REPORTABLE,
    REPORTABLE_STATUSES,
    REVIEW_NEEDS_REVIEW,
    refresh_normalized,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "backend", "database", "linkedin_reportable.db")
AUDIT_PATH = os.path.join(ROOT, "data", "audit",
                          "single_category_reconciliation_20261002.md")
ACTOR = "migration:single_category_20261002"


def _load(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default


def _status_counts(conn):
    return {row["reportable_status"]: row["c"] for row in conn.execute(
        "SELECT reportable_status, COUNT(*) AS c "
        "FROM linkedin_reportable_activities GROUP BY reportable_status")}


def _category_counts(conn):
    return {row["category_code"]: row["c"] for row in conn.execute(
        "SELECT category_code, COUNT(*) AS c FROM linkedin_activity_categories "
        "GROUP BY category_code ORDER BY c DESC")}


def _multi_label_rows(conn):
    """Reportable rows whose stored categories are not exactly one."""
    bad = []
    for row in conn.execute(
            "SELECT activity_id, categories FROM linkedin_reportable_activities "
            "WHERE reportable_status=?", (REPORTABLE,)):
        codes = _load(row["categories"], [])
        if len(codes) != 1:
            bad.append((row["activity_id"], codes))
    return bad


def plan(conn):
    """Build the full set of decisions without writing anything."""
    rows = conn.execute(
        "SELECT * FROM linkedin_reportable_activities "
        "WHERE reportable_status=? ORDER BY activity_id", (REPORTABLE,)).fetchall()

    moves, unchanged, unresolved = [], [], []
    for row in rows:
        decision = primary_category.decide_for_row(row)
        old_codes = _load(row["categories"], [])
        status = decision["status"]

        if status == REPORTABLE:
            new_codes = [decision["category"]]
            if old_codes == new_codes:
                unchanged.append(row["activity_id"])
                continue
            moves.append({
                "activity_id": row["activity_id"], "title": row["title"],
                "old_categories": old_codes, "new_categories": new_codes,
                "old_status": row["reportable_status"],
                "new_status": REPORTABLE, "rule": decision["rule"],
                "reason": decision["reason"],
            })
        else:
            unresolved.append({
                "activity_id": row["activity_id"], "title": row["title"],
                "old_categories": old_codes, "new_categories": [],
                "old_status": row["reportable_status"], "new_status": status,
                "rule": decision["rule"], "reason": decision["reason"],
            })

    return {"moves": moves, "unchanged": unchanged, "unresolved": unresolved,
            "scanned": len(rows)}


def apply(conn, result):
    """Write the decisions in one transaction, recording provenance."""
    now = datetime.now().isoformat(timespec="seconds")
    written = 0

    for item in result["unresolved"]:
        row = conn.execute(
            "SELECT manual_overrides, validation_history, is_manually_validated "
            "FROM linkedin_reportable_activities WHERE activity_id=?",
            (item["activity_id"],)).fetchone()
        overrides = _load(row["manual_overrides"], {})
        history = _load(row["validation_history"], [])
        history.append({
            "field": "categories", "old": item["old_categories"], "new": [],
            "by": ACTOR, "at": now,
            "note": "%s: %s" % (item["new_status"], item["reason"]),
        })
        history.append({
            "field": "reportable_status", "old": item["old_status"],
            "new": item["new_status"], "by": ACTOR, "at": now,
            "note": item["rule"],
        })
        conn.execute(
            "UPDATE linkedin_reportable_activities SET categories=?, "
            "reportable_status=?, review_status=?, manual_overrides=?, "
            "validation_history=?, updated_at=datetime('now') WHERE activity_id=?",
            (json.dumps([]), item["new_status"], REVIEW_NEEDS_REVIEW,
             json.dumps(overrides), json.dumps(history), item["activity_id"]))
        written += 1

    for item in result["moves"]:
        row = conn.execute(
            "SELECT manual_overrides, validation_history "
            "FROM linkedin_reportable_activities WHERE activity_id=?",
            (item["activity_id"],)).fetchone()
        overrides = _load(row["manual_overrides"], {})
        history = _load(row["validation_history"], [])
        # Keep the human override document aligned with the stored decision.
        if isinstance(overrides, dict) and isinstance(overrides.get("categories"), list) \
                and len(overrides["categories"]) == 1:
            overrides["categories"] = item["new_categories"]
        history.append({
            "field": "categories", "old": item["old_categories"],
            "new": item["new_categories"], "by": ACTOR, "at": now,
            "note": "%s: %s" % (item["rule"], item["reason"]),
        })
        conn.execute(
            "UPDATE linkedin_reportable_activities SET categories=?, "
            "manual_overrides=?, validation_history=?, "
            "updated_at=datetime('now') WHERE activity_id=?",
            (json.dumps(item["new_categories"]), json.dumps(overrides),
             json.dumps(history), item["activity_id"]))
        written += 1

    # Rebuild the normalized tables so the join matches the stored columns.
    refresh_normalized(conn)
    return written


def reconciliation(conn):
    """unique reportable activities == sum of primary categories, per scope.

    Scope uses the same rule as the public filters: a General activity has no
    department row other than "General"; a Departmental one has at least one.
    """
    scope_sql = {
        "General": ("NOT EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                    "WHERE ad.activity_id = r.activity_id AND ad.department != ?)",),
        "Departmental": ("EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                         "WHERE ad.activity_id = r.activity_id AND ad.department != ?)",),
    }
    out = []
    for scope, (predicate,) in scope_sql.items():
        for row in conn.execute(
                "SELECT r.academic_year AS ay, COUNT(DISTINCT r.activity_id) AS unique_n, "
                "COUNT(ac.activity_id) AS cat_n "
                "FROM linkedin_reportable_activities r "
                "LEFT JOIN linkedin_activity_categories ac "
                "  ON ac.activity_id = r.activity_id "
                "WHERE r.reportable_status=? AND " + predicate +
                " GROUP BY r.academic_year ORDER BY r.academic_year",
                (REPORTABLE, "General")):
            out.append({
                "scope": scope, "academic_year": row["ay"],
                "unique": row["unique_n"], "category_sum": row["cat_n"],
                "difference": row["unique_n"] - row["cat_n"],
            })
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="write changes (default: dry run)")
    parser.add_argument("--audit", action="store_true",
                        help="also write the markdown audit report")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        sys.exit("database not found: %s" % DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    before = {
        "statuses": _status_counts(conn),
        "categories": _category_counts(conn),
        "multi_label": _multi_label_rows(conn),
    }
    result = plan(conn)
    print("=" * 78)
    print("reportable rows scanned : %d" % result["scanned"])
    print("category changed        : %d" % len(result["moves"]))
    print("already single category : %d" % len(result["unchanged"]))
    print("moved to review/non-act : %d" % len(result["unresolved"]))
    print("multi-label rows before : %d" % len(before["multi_label"]))
    print("=" * 78)

    if not args.apply:
        print("\nDRY RUN - nothing written. Re-run with --apply to migrate.")
        for item in result["unresolved"][:10]:
            print("  %s -> %-14s %s" % (item["activity_id"], item["new_status"],
                                       item["rule"]))
        conn.close()
        return 0

    conn.execute("BEGIN")
    try:
        written = apply(conn, result)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    print("\napplied %d row updates in one transaction" % written)

    after = {
        "statuses": _status_counts(conn),
        "categories": _category_counts(conn),
        "multi_label": _multi_label_rows(conn),
    }
    print("multi-label rows after  : %d" % len(after["multi_label"]))
    print("statuses before         : %s" % before["statuses"])
    print("statuses after          : %s" % after["statuses"])

    recon = reconciliation(conn)
    bad = [r for r in recon if r["difference"] != 0]
    print("\nreconciliation: %d scopes checked, %d mismatches"
          % (len(recon), len(bad)))
    for row in recon:
        if row["difference"] != 0 or row["academic_year"] in ("2025-26", "2026-27"):
            print("  %-12s %-6s unique=%-5d sum=%-5d diff=%d"
                  % (row["academic_year"], row["scope"], row["unique"],
                     row["category_sum"], row["difference"]))

    if args.audit:
        write_audit(conn, before, after, result, recon)
        print("\naudit written: %s" % AUDIT_PATH)

    conn.close()
    return 1 if bad else 0


def write_audit(conn, before, after, result, recon):
    lines = [
        "# Single-category reconciliation audit (2026-10-02)", "",
        "Every `REPORTABLE` activity carries exactly one primary category.",
        "", "## Status counts", "",
        "| status | before | after |", "| --- | ---: | ---: |",
    ]
    for status in sorted(set(before["statuses"]) | set(after["statuses"])):
        lines.append("| %s | %d | %d |" % (status,
                     before["statuses"].get(status, 0),
                     after["statuses"].get(status, 0)))

    lines += ["", "## Category counts", "",
              "| category | before | after |", "| --- | ---: | ---: |"]
    for code in sorted(set(before["categories"]) | set(after["categories"]),
                       key=lambda c: -after["categories"].get(c, 0)):
        lines.append("| %s | %d | %d |" % (code,
                     before["categories"].get(code, 0),
                     after["categories"].get(code, 0)))

    lines += ["", "## Reconciliation (unique activities vs category sum)", "",
              "| academic year | scope | unique | category sum | difference |",
              "| --- | --- | ---: | ---: | ---: |"]
    for row in recon:
        lines.append("| %s | %s | %d | %d | %d |"
                     % (row["academic_year"], row["scope"], row["unique"],
                        row["category_sum"], row["difference"]))

    lines += ["", "## Rows moved to REVIEW_REQUIRED or NON_ACTIVITY", "",
              "| activity_id | title | previous categories | final status | reason |",
              "| --- | --- | --- | --- | --- |"]
    for item in result["unresolved"]:
        lines.append("| %s | %s | %s | %s | %s |"
                     % (item["activity_id"], (item["title"] or "")[:80].replace("|", "/"),
                        ", ".join(item["old_categories"]) or "(none)",
                        item["new_status"], item["reason"]))

    lines += ["", "## Rows re-categorised", "",
              "| activity_id | title | previous categories | final category | rule |",
              "| --- | --- | --- | --- | --- |"]
    for item in result["moves"]:
        lines.append("| %s | %s | %s | %s | %s |"
                     % (item["activity_id"], (item["title"] or "")[:80].replace("|", "/"),
                        ", ".join(item["old_categories"]) or "(none)",
                        item["new_categories"][0], item["rule"]))

    os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
    with open(AUDIT_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())