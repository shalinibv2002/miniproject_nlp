"""Phase 8 enrichment: enrich ``ACHIEVEMENT`` records with official TCE evidence.

Scope (user-approved): named-student records only.  Everything below was
verified against the live official Thiagarajar College of Engineering pages
(College Day Awards - 2026/2025/2024/2023, Campus Life > Best Outgoing
Students) fetched during Phase 8 research:

  * Correct the academic period of every ``college-day-awards-YYYY`` record
    (official page year ``N`` -> academic year ``(N-1)/N``; the 2021 page
    belongs to the 2020-21 batch -> stored as ``NULL``/"Before 2021").
  * Rebuild title / description / achievement_outcome for the 18 named BOS
    records, matching each student by name + department to the award row on
    the official page (the scraped titles are garbled: scraped row indexes
    shifted the award labels by one row, so titles were NOT trusted - the
    official page mapping is authoritative).
  * Enrich two named NSS records (IDs 107, 108) from TCE NSS evidence.

Features:
  * ``--apply`` performs the changes inside one transaction.
  * Default is a dry-run that only previews every change.

Conventions honoured:
  * ``achievement_outcome`` follows the admin ``_build_achievement`` shape:
    ``Student Name: <name> - <outcome>`` (TCE pages publish no register
    numbers, so none are fabricated).
  * ``department_display`` is intentionally NOT changed (scope decision:
    keep the General/Departmental analytics split untouched; the student's
    department is captured in the outcome text instead).
  * Every field change is written to ``review_history`` with the official
    source URL as the reason.
  * Evidence text and source URLs are never altered.
"""

import argparse
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.database.normalizer import to_normalized_title  # noqa: E402
DB_PATH = ROOT / "data" / "tce_activity_intelligence.db"
BACKUP_DIR = ROOT / "data" / "backups"
REVIEWER = "phase8-bos-enrichment"

# Official page calendar year -> stored public academic-year key.
# 2021 page = 2020-21 batch -> "Before 2021" -> stored NULL.
PERIOD_BY_PAGE_YEAR = {
    2026: "2025-26", 2025: "2024-25", 2024: "2023-24",
    2023: "2022-23", 2022: "2021-22", 2021: None,
}

# Public short-code -> full public department name (matches department_catalog).
DEPT_CODES = {
    "ARCH": "T'SEDA (Architecture, Design, Planning)",
    "CSBS": "Computer Science and Business Systems",
    "CSE": "Computer Science and Engineering",
    "CIVIL": "Civil Engineering",
    "IT": "Information Technology",
    "ECE": "Electronics and Communication Engineering",
    "EEE": "Electrical and Electronics Engineering",
    "MECT": "Mechatronics",
    "MECH": "Mechanical Engineering",
    "CA": "Computer Applications",
    "MCA": "Computer Applications",
}

# Named BOS enrichment: activity_id -> (name, dept_short, award_title, page_year).
# Award text is taken verbatim from the official College Day Awards page.
BOS_NAMED = {
    833: ("POOMIJA C A", "ARCH",
          "M.Plan. Urban Planning - Best Outgoing Student of the Department", 2026),
    834: ("VISHNU SANKAR V", "CSBS", "Best Outgoing NCC Cadet (Boy)", 2026),
    835: ("SUBHASHINI M", "CSE", "Best Outgoing NCC Cadet (Girl)", 2026),
    836: ("AKASH B S", "IT", "Best Outgoing NSS Volunteer (Boy)", 2026),
    837: ("RASMI S", "ECE", "Best Outgoing YRC Volunteer (Girl)", 2026),
    838: ("TANISH MILIND SALUNKHE", "CIVIL", "Best Outgoing Sports Person (Boy)", 2026),
    841: ("AKSHARA A", "CA",
          "Master of Computer Applications - Best Outgoing Student of the Department", 2024),
    842: ("APRAKKETH P D M", "MECT", "Best Outgoing NCC Cadet (Boy)", 2024),
    843: ("BALA SOUNDARYA V", "IT", "Best Outgoing NCC Cadet (Girl)", 2024),
    844: ("AMRITH S", "MECT", "Best Outgoing NSS Volunteer (Boy)", 2024),
    845: ("GOPI M", "MECT", "Best Outgoing YRC Volunteer (Boy)", 2024),
    846: ("MUKESH C", "MECH", "Best Outgoing Sports Person (Boy)", 2024),
    848: ("MADHUMITHAA N", "CA",
          "Master of Computer Applications - Best Outgoing Student of the Department", 2023),
    849: ("MITHUL KANNAN KR", "IT", "Best Outgoing NCC Cadet (Boy)", 2023),
    850: ("GOPIKA GS", "EEE", "Best Outgoing NCC Cadet (Girl)", 2023),
    851: ("APARAJITHAN MVV", "IT", "Best Outgoing NSS Volunteer (Boy)", 2023),
    852: ("GNANA DHEEPIKA GG", "IT", "Best Outgoing NSS Volunteer (Girl)", 2023),
    853: ("SHYAM K", "IT", "Best Outgoing Sports Person (Boy)", 2023),
}

# Named non-BOS enrichment (activity_id -> change dict).
NON_BOS = {
    107: {
        "academic_year": "2022-23",
        "stakeholder_display": "Faculty",
        "achievement_outcome":
            "Student Name: Siva Ilango - Best NSS Programme Officer "
            "(2022-2023), University Level (Anna University)",
        "source": "https://www.tce.edu/campuslife/nss",
    },
    108: {
        "achievement_outcome":
            "Student Name: Gowthaman - Best NSS Volunteer - State Level award",
        "source": "https://www.tce.edu/campuslife/nss",
    },
}

METADATA_FIELDS = {"achievement_outcome", "academic_year", "stakeholder_display"}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def backup():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = BACKUP_DIR / f"tce_activity_intelligence_pre-phase8-{stamp}.db"
    shutil.copy2(DB_PATH, target)
    print(f"[backup]     {target}")
    return target


def page_year_from_url(url):
    match = re.search(r"college-day-awards-(\d{4})", url or "")
    return int(match.group(1)) if match else None


def collect_plan(conn):
    """Return list of changes: (activity_id, field, new_value, source_url)."""
    changes = []

    rows = conn.execute(
        """SELECT a.id, a.source_url, m.academic_year
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
           WHERE a.source_url LIKE '%college-day-awards%'"""
    ).fetchall()
    for row in rows:
        year = page_year_from_url(row["source_url"])
        if year is None or year not in PERIOD_BY_PAGE_YEAR:
            continue
        target = PERIOD_BY_PAGE_YEAR[year]
        if row["academic_year"] != target:
            changes.append((row["id"], "academic_year", target, row["source_url"]))

    for activity_id, (name, dept_short, award, page_year) in BOS_NAMED.items():
        dept_full = DEPT_CODES[dept_short]
        period = PERIOD_BY_PAGE_YEAR[page_year]
        url = f"https://www.tce.edu/campuslife/bos/college-day-awards-{page_year}"
        changes.append((activity_id, "title", f"{award} - {name}", url))
        changes.append((activity_id, "description",
                        f"{name} of {dept_full} was honoured with the {award} "
                        f"award at the College Day Awards {page_year} of "
                        f"Thiagarajar College of Engineering, Madurai.", url))
        changes.append((activity_id, "achievement_outcome",
                        f"Student Name: {name} - {award}, College Day Awards "
                        f"{page_year} (academic year {period}), Thiagarajar "
                        f"College of Engineering, Madurai; Department: "
                        f"{dept_full}.", url))

    for activity_id, payload in NON_BOS.items():
        source = payload["source"]
        for field, value in payload.items():
            if field == "source":
                continue
            changes.append((activity_id, field, value, source))

    return changes


def apply_change(conn, activity_id, field, new_value, source_url, cur):
    if field == "title":
        cur.execute(
            "UPDATE institutional_activities SET title=?, normalized_title=? "
            "WHERE id=?",
            (new_value, to_normalized_title(new_value), activity_id))
    elif field == "description":
        cur.execute(
            "UPDATE institutional_activities SET description=? WHERE id=?",
            (new_value, activity_id))
    else:
        assert field in METADATA_FIELDS, field
        cur.execute(
            f"UPDATE final_activity_metadata SET {field}=?, "
            "updated_at=datetime('now') WHERE activity_id=?",
            (new_value, activity_id))
        if field == "stakeholder_display":
            cur.execute(
                "DELETE FROM activity_stakeholders WHERE activity_id=?",
                (activity_id,))
            cur.execute(
                "INSERT OR IGNORE INTO activity_stakeholders (activity_id, stakeholder_id) "
                "SELECT ?, id FROM stakeholders WHERE name=?",
                (activity_id, new_value))
    cur.execute(
        "INSERT INTO review_history (activity_id, field_name, old_value, "
        "new_value, action, reviewer, reason, created_at) "
        "VALUES (?, ?, NULL, ?, 'edit', ?, ?, datetime('now'))",
        (activity_id, field, new_value, REVIEWER,
         f"Verified against official TCE source: {source_url}"))


def verify(conn):
    print("\n[verify] post-state")
    print("  BOS period distribution (target):")
    rows = conn.execute(
        """SELECT substr(m.academic_year,1,7) AS period, COUNT(*) AS n
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
           WHERE a.source_url LIKE '%college-day-awards%'
           GROUP BY m.academic_year ORDER BY m.academic_year"""
    ).fetchall()
    for row in rows:
        print(f"    {row['period'] or 'Before 2021':10} {row['n']}")

    rows = conn.execute(
        """SELECT a.id, a.title FROM institutional_activities a
           WHERE a.id IN (833,834,835,836,837,838,841,842,843,844,845,846,
                          848,849,850,851,852,853,107,108)
           ORDER BY a.id"""
    ).fetchall()
    print("  named record titles:")
    for row in rows:
        print(f"    {row['id']}: {(row['title'] or '')[:90]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="write changes; default is dry-run")
    parser.add_argument("--no-backup", action="store_true",
                        help="skip the pre-apply database backup")
    args = parser.parse_args()

    conn = connect()
    try:
        plan = collect_plan(conn)
        print(f"[plan]       {len(plan)} field changes across "
              f"{len({c[0] for c in plan})} records")
        for activity_id, field, value, source in plan:
            print(f"  {activity_id:>4}  {field:20} -> "
                  f"{(str(value)[:70] if value else 'NULL')}")
            print(f"       source: {source}"[:120])

        if not args.apply:
            print("\n[dry-run] nothing written - pass --apply to persist.")
            return

        backup_path = None if args.no_backup else backup()
        cur = conn.cursor()
        try:
            for activity_id, field, value, source in plan:
                apply_change(conn, activity_id, field, value, source, cur)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        print(f"[applied]    {len(plan)} changes committed.")
        verify(conn)
        if backup_path:
            print(f"[done]       backup kept at {backup_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()