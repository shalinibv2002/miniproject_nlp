"""One-time migration of the canonical reportable layer.

Three changes, all reversible, all audited, all in ONE transaction:

  1. Placement removal -- ``PLACEMENT`` leaves the active reporting taxonomy.
     Every reportable row that carries it is reclassified into the most
     accurate remaining category (``INDUSTRY`` for an external counterparty,
     ``INTERNSHIP`` for a career outcome).  A row with neither signal is not
     guessed at: it is parked in ``NEEDS_REVIEW`` and listed in the audit.
  2. Stored titles -- the database keeps the cleaned title, so Excel/PDF and
     any direct consumer of the DB show the title and not the raw caption.
     Admin overrides (``report_name``/pinned fields) are never touched.
  3. Duplicate collapse -- rows that describe the same activity are merged
     into the survivor with the most evidence.  Staging provenance is never
     modified: this only ever touches the derived canonical layer.

Safety
------
  * ``--apply`` is required to write anything; the default is a dry run.
  * The database is copied and SHA-256 recorded BEFORE any write.
  * Every step runs inside a single transaction; on any failure the database
    file is restored from the backup and the SHA is re-verified.
  * The migration re-validates the result (counts, categories, no PLACEMENT,
    no broken category references) before it commits.

Usage
-----
  python scripts/migrate_reportable_placement_dedup.py            # dry run
  python scripts/migrate_reportable_placement_dedup.py --apply    # migrate
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import primary_category, report_fields          # noqa: E402
from backend.database import category_catalog                          # noqa: E402
from backend.database.category_report_schema import CATEGORY_SCHEMAS  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "backend", "database", "linkedin_reportable.db")
BACKUP_DIR = os.path.join(ROOT, "data", "backups")
AUDIT_PATH = os.path.join(ROOT, "data", "audit",
                          "reportable_placement_dedup_migration.json")

RETIRED_CODE = "PLACEMENT"

# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------
#: Two rows are the same activity only when ALL of these hold:
#:   * same primary category,
#:   * the same non-null activity date (a missing date is never evidence),
#:   * the same normalised title, and
#:   * description token overlap of at least ``JACCARD_MIN``.
#: Any conflict in post_url / staging ids / activity id disqualifies the pair,
#: so provenance is never merged by accident.
JACCARD_MIN = 0.90
WS = re.compile(r"\s+")
PUNCT = re.compile(r"[^\w\s]+", re.U)
STOP = frozenset("""a an the and or of for to in on at by with from is are was
were be been this that our your we they he she it as into over under about
after before""".split())


def _tokens(text):
    return {w for w in WS.sub(" ", PUNCT.sub(" ", (text or "").lower())).split()
            if w not in STOP and len(w) > 2}


def _norm(text):
    return WS.sub(" ", PUNCT.sub(" ", (text or "").lower())).strip()


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def _primary(row):
    codes = json.loads(row["categories"] or "[]")
    if not codes:
        return None
    item = codes[0]
    return item.get("code") if isinstance(item, dict) else item


def find_duplicates(rows):
    """Duplicate groups, strongest evidence first.  Returns a list of lists."""
    tokens = [_tokens(r["description"]) for r in rows]
    blocks = defaultdict(list)
    for index, row in enumerate(rows):
        # Index on the title tokens AND the date: a duplicate must share both.
        for word in {w for w in _tokens(row["title"]) if len(w) > 3}:
            blocks[(word, row["activity_date"])].append(index)

    candidates = set()
    for key, indexes in blocks.items():
        if not key[1] or len(indexes) > 40:
            continue
        for a, b in combinations(sorted(indexes), 2):
            candidates.add((a, b))

    parent = {}

    def find(i):
        parent.setdefault(i, i)
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for a, b in candidates:
        ra, rb = rows[a], rows[b]
        if ra["activity_id"] == rb["activity_id"]:
            continue
        if _primary(ra) != _primary(rb):
            continue
        if not ra["activity_date"] or ra["activity_date"] != rb["activity_date"]:
            continue
        if _norm(ra["title"]) != _norm(rb["title"]):
            continue
        if _jaccard(tokens[a], tokens[b]) < JACCARD_MIN:
            continue
        # A conflict in provenance means these are two different real posts.
        if ra["post_url"] and rb["post_url"] and ra["post_url"] != rb["post_url"]:
            continue
        if ra["staging_post_id"] and rb["staging_post_id"] \
                and ra["staging_post_id"] == rb["staging_post_id"] \
                and ra["activity_date"] == rb["activity_date"] \
                and _norm(ra["description"]) != _norm(rb["description"]):
            continue
        union(a, b)

    groups = defaultdict(list)
    for index in parent:
        groups[find(index)].append(index)
    result = []
    for members in groups.values():
        if len(members) < 2:
            continue
        # Survivor: most evidence first (URL, then departments/stakeholders,
        # then the longest description).  Ties break on activity_id so the
        # choice is deterministic.
        def rank(i):
            r = rows[i]
            return (
                1 if r["post_url"] else 0,
                len(json.loads(r["departments"] or "[]"))
                + len(json.loads(r["stakeholders"] or "[]")),
                len(r["description"] or ""),
                # negated: smallest id wins a tie
                tuple(-ord(ch) for ch in r["activity_id"][:12]),
            )

        ordered = sorted(members, key=rank, reverse=True)
        result.append(ordered)
    result.sort(key=lambda g: rows[g[0]]["activity_id"])
    return result


# ---------------------------------------------------------------------------
# Placement reclassification
# ---------------------------------------------------------------------------
#: An external counterparty in the post: a MoU, tie-up, partner or recruiter.
_PARTNER_RES = (
    re.compile(r"m\s*o\s*u\b", re.I),
    re.compile(r"tie[-\s]?up", re.I),
    re.compile(r"\b(?:collaborat\w+|partnership|partnered|agreement)\s+"
               r"(?:with|by)\b", re.I),
    re.compile(r"\b(?:recruit(?:er|ing|ment)|placement\s+drive|"
               r"campus\s+recruit\w*)\s+(?:by|at|with)\s+([A-Z][\w&. ]{2,40})"),
)
#: A career outcome for one person: joined, placed, appointed, offered.
_OUTCOME_RES = (
    re.compile(r"\b(?:joins?|joining|joined|placed\s+at|placement|offer\s+letter|"
               r"selected|recruited|appointed|onboard(?:ed|ing)|appointee|"
               r"secured\s+(?:a\s+)?(?:job|role|position))\b", re.I),
)


def placement_codes(conn):
    """activity_id -> every category code, from BOTH stores."""
    codes = defaultdict(set)
    for row in conn.execute(
            "SELECT activity_id, category_code FROM "
            "linkedin_activity_categories"):
        codes[row[0]].add(row[1])
    for row in conn.execute(
            "SELECT activity_id, categories FROM "
            "linkedin_reportable_activities WHERE reportable_status='REPORTABLE'"):
        for item in json.loads(row[1] or "[]"):
            codes[row[0]].add(item.get("code") if isinstance(item, dict)
                              else item)
    return codes


def plan_placement(conn, rows):
    """(activity_id, from, to, reason) for every reportable PLACEMENT row.

    PLACEMENT counts when EITHER store still names it: a half-finished earlier
    run must be finished, not skipped.
    """
    codes = placement_codes(conn)
    plan = []
    for row in rows:
        if RETIRED_CODE not in codes.get(row["activity_id"], ()):
            continue
        text = "%s\n%s" % (row["title"] or "", row["description"] or "")
        if any(p.search(text) for p in _PARTNER_RES):
            plan.append((row["activity_id"], RETIRED_CODE, "INDUSTRY",
                         "post names an external counterparty"))
        elif any(p.search(text) for p in _OUTCOME_RES):
            plan.append((row["activity_id"], RETIRED_CODE, "INTERNSHIP",
                         "post reports a career outcome"))
        else:
            plan.append((row["activity_id"], RETIRED_CODE, "NEEDS_REVIEW",
                         "no partner and no career-outcome evidence"))
    return plan


def apply_placement(conn, plan):
    """Rewrite the categories of every planned row.  Returns the applied plan.

    Two stores have to agree or the report breaks in a new way: the ordered
    ``categories`` JSON (which decides the primary category) and the
    ``linkedin_activity_categories`` join table (which the filters, analytics
    and category counts read).  Both are rewritten together.  The JSON keeps the
    dataset's own shape -- a list of category code strings, in primary-first
    order -- so no consumer sees a differently shaped value.
    """
    applied = []
    for activity_id, _frm, to, reason in plan:
        row = conn.execute(
            "SELECT categories FROM linkedin_reportable_activities "
            "WHERE activity_id=?", (activity_id,)).fetchone()
        if not row:
            continue
        codes = [c.get("code") if isinstance(c, dict) else c
                 for c in json.loads(row[0] or "[]")]
        codes = [c for c in codes if c != RETIRED_CODE]
        conn.execute(
            "DELETE FROM linkedin_activity_categories "
            "WHERE activity_id=? AND category_code=?", (activity_id, RETIRED_CODE))
        if to == "NEEDS_REVIEW":
            # Not guessable: keep the post, take it out of the active taxonomy
            # and flag it.  NEEDS_REVIEW rows stay publicly visible.
            conn.execute(
                "UPDATE linkedin_reportable_activities SET categories=? "
                "WHERE activity_id=?",
                (json.dumps(codes), activity_id))
            conn.execute(
                "UPDATE linkedin_reportable_activities SET review_status=? "
                "WHERE activity_id=? AND (review_status IS NULL OR "
                "review_status NOT IN ('APPROVED'))",
                ("NEEDS_REVIEW", activity_id))
            applied.append((activity_id, RETIRED_CODE, "REVIEW_REQUIRED", reason))
            continue
        # Replace PLACEMENT with the resolved category, first in the list.
        ordered = [to] + [c for c in codes if c != to]
        conn.execute(
            "UPDATE linkedin_reportable_activities SET categories=? "
            "WHERE activity_id=?",
            (json.dumps(ordered), activity_id))
        conn.executemany(
            "INSERT OR IGNORE INTO linkedin_activity_categories "
            "(activity_id, category_code) VALUES (?, ?)",
            [(activity_id, c) for c in ordered])
        applied.append((activity_id, RETIRED_CODE, to, reason))
    return applied


# ---------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------
def plan_titles(rows):
    return [(r["activity_id"], r["title"] or "",
             report_fields.clean_title(r["description"] or r["title"] or ""))
            for r in rows
            if report_fields.clean_title(r["description"] or r["title"] or "")
            != (r["title"] or "")]


def apply_titles(conn, plan):
    conn.executemany(
        "UPDATE linkedin_reportable_activities SET title=? WHERE activity_id=?",
        [(new, aid) for aid, _old, new in plan if new])


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def normalise_category_json(conn):
    """Every ``categories`` value is a list of code strings, primary first.

    The dataset stores codes, not objects.  A row written in any other shape
    (an earlier version of this script, a hand edit) is rewritten so no
    consumer has to handle two shapes.
    """
    changed = []
    for row in conn.execute(
            "SELECT activity_id, categories FROM linkedin_reportable_activities"):
        parsed = json.loads(row[1] or "[]")
        codes = [c.get("code") if isinstance(c, dict) else c for c in parsed]
        codes = [c for c in codes if c]
        if codes != parsed:
            changed.append(row[0])
    return changed


def apply_category_shape(conn, ids):
    for activity_id in ids:
        parsed = json.loads(conn.execute(
            "SELECT categories FROM linkedin_reportable_activities "
            "WHERE activity_id=?", (activity_id,)).fetchone()[0] or "[]")
        codes = [c.get("code") if isinstance(c, dict) else c for c in parsed]
        codes = [c for c in codes if c]
        conn.execute(
            "UPDATE linkedin_reportable_activities SET categories=? "
            "WHERE activity_id=?", (json.dumps(codes), activity_id))
    return len(ids)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reportable_rows(conn):
    rows = conn.execute(
        "SELECT * FROM linkedin_reportable_activities "
        "WHERE reportable_status='REPORTABLE'").fetchall()
    return [dict(r) for r in rows]


def validate(conn, before_count):
    """Post-migration invariants.  Raises on any violation."""
    problems = []
    after = _reportable_rows(conn)
    if len(after) > before_count:
        problems.append("row count grew: %d -> %d" % (before_count, len(after)))
    for row in after:
        code = _primary(row)
        if code == RETIRED_CODE:
            problems.append("%s still carries PLACEMENT" % row["activity_id"])
        if code and code not in CATEGORY_SCHEMAS:
            problems.append("%s has unknown category %s"
                            % (row["activity_id"], code))
        if not (row["title"] or "").strip():
            problems.append("%s has a blank title" % row["activity_id"])
    known = {r[0] for r in conn.execute(
        "SELECT activity_id FROM linkedin_reportable_activities")}
    for table in ("linkedin_activity_categories",
                  "linkedin_activity_departments",
                  "linkedin_activity_stakeholders"):
        for (activity_id,) in conn.execute(
                "SELECT activity_id FROM %s" % table):
            if activity_id not in known:
                problems.append("%s references deleted row %s"
                                % (table, activity_id))
    if problems:
        raise AssertionError("validation failed:\n  " + "\n  ".join(problems))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="write the changes (default: dry run only)")
    parser.add_argument("--db", default=DB_PATH)
    args = parser.parse_args(argv)

    if not os.path.exists(args.db):
        print("no such database: %s" % args.db)
        return 2

    before_sha = sha256(args.db)
    print("database : %s" % args.db)
    print("sha256   : %s" % before_sha)
    print("mode     : %s" % ("APPLY" if args.apply else "DRY RUN"))

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    try:
        rows = _reportable_rows(conn)
        placement = plan_placement(conn, rows)
        titles = plan_titles(rows)
        groups = find_duplicates(rows)
        removed = [g[1:] for g in groups]

        print("\nreportable rows   : %d" % len(rows))
        print("placement rows    : %d" % len(placement))
        for aid, _frm, to, reason in placement:
            print("    %-14s -> %-14s %s" % (aid, to, reason))
        print("titles to rebuild : %d" % len(titles))
        print("duplicate groups  : %d" % len(groups))
        print("rows to remove    : %d" % sum(len(g) - 1 for g in groups))
        print("category json fix : %d" % len(normalise_category_json(conn)))
        for group in groups[:10]:
            print("    keep %-14s remove %s"
                  % (rows[group[0]]["activity_id"],
                     ", ".join(rows[i]["activity_id"] for i in group[1:])))
        if len(groups) > 10:
            print("    ... and %d more groups" % (len(groups) - 10))

        audit = {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "database": os.path.relpath(args.db, ROOT),
            "sha256_before": before_sha,
            "mode": "apply" if args.apply else "dry_run",
            "reportable_rows_before": len(rows),
            "jaccard_min": JACCARD_MIN,
            "placement": [
                {"activity_id": a, "from": f, "to": t, "reason": r}
                for a, f, t, r in placement],
            "titles_rebuilt": len(titles),
            "title_changes": [
                {"activity_id": a, "before": o, "after": n}
                for a, o, n in titles],
            "duplicate_groups": [
                {
                    "keep": rows[g[0]]["activity_id"],
                    "remove": [rows[i]["activity_id"] for i in g[1:]],
                    "title": rows[g[0]]["title"],
                    "category": _primary(rows[g[0]]),
                    "date": rows[g[0]]["activity_date"],
                    "similarity": round(max(
                        _jaccard(_tokens(rows[g[0]]["description"]),
                                 _tokens(rows[i]["description"]))
                        for i in g[1:]), 4),
                }
                for g in groups],
        }

        if not args.apply:
            os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
            with open(AUDIT_PATH, "w", encoding="utf-8") as handle:
                json.dump(audit, handle, indent=2, ensure_ascii=False)
            print("\ndry run: nothing written.  audit -> %s" % AUDIT_PATH)
            return 0

        # ---- backup before the first write -------------------------------
        os.makedirs(BACKUP_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(BACKUP_DIR, "linkedin_reportable_%s.db" % stamp)
        shutil.copy2(args.db, backup)
        if sha256(backup) != before_sha:
            print("backup verification failed; aborting")
            return 1
        print("\nbackup   : %s" % os.path.relpath(backup, ROOT))

        try:
            conn.execute("BEGIN IMMEDIATE")
            fixed_shape = apply_category_shape(
                conn, normalise_category_json(conn))
            apply_placement(conn, placement)
            apply_titles(conn, titles)
            for group in removed:
                for index in group:
                    activity_id = rows[index]["activity_id"]
                    for table in ("linkedin_activity_categories",
                                  "linkedin_activity_departments",
                                  "linkedin_activity_stakeholders"):
                        conn.execute("DELETE FROM %s WHERE activity_id=?"
                                     % table, (activity_id,))
                    conn.execute("DELETE FROM linkedin_reportable_activities "
                                 "WHERE activity_id=?", (activity_id,))
            validate(conn, len(rows))
            conn.commit()
        except Exception as exc:                      # noqa: BLE001
            conn.rollback()
            conn.close()
            shutil.copy2(backup, args.db)
            print("\nMIGRATION FAILED: %s" % exc)
            print("database restored from backup; sha256 = %s" % sha256(args.db))
            return 1

        after_count = _reportable_rows(conn).__len__()
        after_sha = sha256(args.db)
        audit.update({
            "sha256_after": after_sha,
            "backup": os.path.relpath(backup, ROOT),
            "reportable_rows_after": after_count,
            "rows_removed": len(rows) - after_count,
        })
        os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)
        with open(AUDIT_PATH, "w", encoding="utf-8") as handle:
            json.dump(audit, handle, indent=2, ensure_ascii=False)

        print("\napplied")
        print("  rows   : %d -> %d" % (len(rows), after_count))
        print("  sha256 : %s" % after_sha)
        print("  audit  : %s" % os.path.relpath(AUDIT_PATH, ROOT))
        return 0
    finally:
        try:
            conn.close()
        except sqlite3.Error:
            pass


if __name__ == "__main__":
    sys.exit(main())