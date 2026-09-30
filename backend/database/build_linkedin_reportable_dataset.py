"""Build the FINAL LinkedIn REPORTABLE dataset (dedicated isolated database).

Reads the LinkedIn staging database READ-ONLY and writes ONLY
``backend/database/linkedin_reportable.db``.  The workbook, staging DB and the
old website production DB are never modified.

Usage:
    python -m backend.database.build_linkedin_reportable_dataset
    python -m backend.database.build_linkedin_reportable_dataset --db <reportable.db> --audit-dir <dir>
"""

import argparse
import json
import os

from backend.database.linkedin_reportable import (
    DEFAULT_AUDIT_DIR,
    REPORTABLE_DB_PATH,
    build_reportable_dataset,
    get_reportable_connection,
)


def _print_summary(summary):
    cls = summary["classification"]
    dates = summary["dates"]
    integ = summary["integrity"]
    source = summary["source"]
    print("=" * 70)
    print("FINAL LINKEDIN REPORTABLE DATASET — BUILD SUMMARY")
    print("=" * 70)
    print("workbook        : %s" % source["workbook"])
    print("workbook sha256 : %s" % source["workbook_sha256"])
    print("sheets          : %s" % ", ".join(source["sheets"]))
    print("raw rows        : %s" % source["raw_rows"])
    print("-" * 70)
    stg = summary["staging"]
    print("canonical posts : %d" % stg["canonical_posts"])
    print("candidates      : %d" % stg["candidates"])
    print("PENDING_REVIEW  : %d" % stg["pending_review_sample"])
    print("-" * 70)
    print("FINAL STATUS:")
    for status in ("REPORTABLE", "NON_ACTIVITY", "REVIEW_REQUIRED"):
        print("  %-16s %d" % (status, cls["by_status"].get(status, 0)))
    print("-" * 70)
    print("DATE STATUS: dated=%d undated=%d ambiguous_multi_year=%d"
          % (dates["dated"], dates["undated"], dates["ambiguous_multi_year"]))
    print("academic_year distribution (reportable):")
    if dates["academic_year_distribution"]:
        for k, v in dates["academic_year_distribution"].items():
            print("  %s: %d" % (k, v))
    else:
        print("  (none)")
    print("-" * 70)
    print("INTEGRITY:")
    for key in ("no_duplicate_final_ids", "no_invalid_categories",
                "no_invalid_departments", "no_invalid_stakeholders",
                "no_invalid_academic_years", "all_traceable"):
        print("  %-28s %s" % (key, integ[key]))
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="Build the FINAL LinkedIn reportable dataset (dedicated isolated DB).")
    parser.add_argument("--staging-db", default=None,
                        help="path to the LinkedIn staging database (default: linkedin_staging.db)")
    parser.add_argument("--db", default=REPORTABLE_DB_PATH,
                        help="reportable DB path (default: backend/database/linkedin_reportable.db)")
    parser.add_argument("--audit-dir", default=None,
                        help="directory for MD+JSON audit report (default: data/audit)")
    parser.add_argument("--no-preserve-overrides", action="store_true",
                        help="drop existing admin overrides on rebuild")
    parser.add_argument("--verify", action="store_true",
                        help="print a quick audit summary of the current reportable DB")
    args = parser.parse_args()

    if args.verify:
        from backend.database.linkedin_reportable import _read_staging
        conn = get_reportable_connection(args.db)
        try:
            rows = conn.execute(
                "SELECT reportable_status, COUNT(*) AS c FROM linkedin_reportable_activities "
                "GROUP BY reportable_status ORDER BY reportable_status").fetchall()
            by_ay = conn.execute(
                "SELECT academic_year, COUNT(*) AS c FROM linkedin_reportable_activities "
                "WHERE reportable_status='REPORTABLE' AND academic_year IS NOT NULL "
                "GROUP BY academic_year ORDER BY academic_year").fetchall()
            print("status counts:",
                  {r["reportable_status"]: r["c"] for r in rows})
            print("academic_year (reportable):",
                  {r["academic_year"]: r["c"] for r in by_ay})
        finally:
            conn.close()
        return

    audit_dir = args.audit_dir or DEFAULT_AUDIT_DIR
    summary = build_reportable_dataset(
        staging_db_path=args.staging_db,
        reportable_db_path=args.db,
        audit_dir=audit_dir,
        preserve_overrides=not args.no_preserve_overrides,
    )
    _print_summary(summary)
    md, js = (os.path.join(audit_dir, "linkedin_final_reportable_dataset_20260923.md"),
              os.path.join(audit_dir, "linkedin_final_reportable_dataset_20260923.json"))
    print("audit report   : %s" % md)
    print("audit json     : %s" % js)


if __name__ == "__main__":
    main()