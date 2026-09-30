"""Incremental LinkedIn workbook import (append-only, idempotent).

Adds NEW TCE LinkedIn posts from an additional faculty workbook into the
EXISTING LinkedIn staging layer WITHOUT reloading, replacing or renumbering
anything that is already there.

    <new-workbook>.xlsx
        -> linkedin_staging.db            (append-only; existing rows untouched)
        -> linkedin_activity_candidates   (EXISTING classifier, new posts only)
        -> linkedin_reportable.db         (EXISTING build, overrides preserved)

Design constraints honoured here:
  * The existing pipeline is reused, never forked.  Workbook reading, text
    canonicalization, activity-id extraction and the near-duplicate thresholds
    all come from :mod:`backend.database.linkedin_staging`.
  * Deduplication reuses the SAME rule the original load already applies
    ACROSS sheets: exact normalized-text equality.  Near-exact matching against
    already-committed historical posts is *reported* (as
    ``POSSIBLE_DUPLICATE_REVIEW``) but never auto-merged, because merging would
    retroactively rewrite historical canonical posts.
  * Near-exact duplicates WITHIN the incoming file ARE collapsed, mirroring
    ``linkedin_staging._load`` step 2c.
  * Every raw incoming row is preserved as an occurrence.
  * Idempotent: running twice produces zero new canonical posts and zero new
    occurrences.  ``linkedin_posts`` ids are never renumbered, so the reportable
    layer's ``staging_post_id`` foreign keys and admin overrides stay valid.

Only ``linkedin_staging.db`` is opened for writing here.  The reportable
database, the old website production database and every workbook are read-only.
"""

import os
import re
from collections import Counter, OrderedDict

from rapidfuzz import fuzz

from backend.database import linkedin_staging as staging
from backend.database.linkedin_staging import (
    NEAR_DUP_LENGTH_RATIO,
    NEAR_DUP_WRATIO,
    extract_activity_id,
    get_staging_connection,
    init_staging_schema,
    normalize_post_text,
    read_sheet_rows,
)

DEFAULT_SOURCE_WORKBOOK = "merged-workbook.xlsx"

# Import classification buckets (internal).
EXISTING_DUPLICATE = "EXISTING_DUPLICATE"
NEW_POST = "NEW_POST"
POSSIBLE_DUPLICATE_REVIEW = "POSSIBLE_DUPLICATE_REVIEW"
NEW_FILE_DUPLICATE = "NEW_FILE_DUPLICATE"

# A leading single-line, short cell at the top of a sheet is a workbook title
# banner (e.g. "Posts from June 2026 - September 2026"), not a LinkedIn post.
TITLE_BANNER_MAX_CHARS = 100

# Backward-compatible, additive provenance columns.
PROVENANCE_COLUMNS = (
    ("linkedin_posts", "source_workbook",
     "ALTER TABLE linkedin_posts ADD COLUMN source_workbook TEXT"),
    ("linkedin_post_occurrences", "source_workbook",
     "ALTER TABLE linkedin_post_occurrences ADD COLUMN source_workbook TEXT"),
)


# ---------------------------------------------------------------------------
# Schema extension (additive only)
# ---------------------------------------------------------------------------
def ensure_provenance_columns(conn):
    """Add ``source_workbook`` provenance columns when missing.

    Backward compatible and idempotent: existing rows keep working and are
    stamped with the historical default workbook so provenance stays truthful.
    """
    init_staging_schema(conn)
    added = []
    for table, column, ddl in PROVENANCE_COLUMNS:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(%s)" % table).fetchall()}
        if column in cols:
            continue
        conn.execute(ddl)
        conn.execute("UPDATE %s SET %s = ? WHERE %s IS NULL"
                     % (table, column, column), (DEFAULT_SOURCE_WORKBOOK,))
        added.append("%s.%s" % (table, column))
    conn.commit()
    return added


# ---------------------------------------------------------------------------
# Workbook reading (reuses the existing reader)
# ---------------------------------------------------------------------------
def _norm_title(text):
    return re.sub(r"[^a-z0-9]+", "", (text or "").strip().lower())


# LinkedIn sheet exports open with a single short line such as
# "Posts from June 2026 - September 2026". A bare length cap cannot tell that
# apart from a genuinely short post, so require positive evidence that the row
# is the export's own title: it either echoes the workbook filename, or matches
# the "Posts ... <year>" export convention.
_EXPORT_TITLE_RE = re.compile(r"^posts?\b.*\b(19|20)\d{2}\b", re.IGNORECASE)


def _is_title_banner(text, workbook_stem=None):
    t = (text or "").strip()
    if not t or "\n" in t or len(t) > TITLE_BANNER_MAX_CHARS:
        return False
    if workbook_stem:
        nt, ns = _norm_title(t), _norm_title(workbook_stem)
        if nt and ns and (nt == ns or nt.startswith(ns) or ns.startswith(nt)):
            return True
    return bool(_EXPORT_TITLE_RE.match(t))


def read_workbook_records(workbook_path, sheets=None):
    """Return ``(sheet_names, records, banners)`` for one workbook.

    Reuses ``linkedin_staging.read_sheet_rows`` so both 'Post title'/'Post link'
    sheets and header-less sheets are handled by the existing code, and
    additionally drops leading workbook title banners.
    """
    import pandas as pd

    xl = pd.ExcelFile(workbook_path)
    sheet_names = list(xl.sheet_names)
    wanted = sheet_names if sheets is None else [s for s in sheets if s in sheet_names]
    workbook_stem = os.path.splitext(os.path.basename(workbook_path))[0]
    records = []
    banners = []
    for sheet in wanted:
        rows = read_sheet_rows(workbook_path, sheet)
        banner_open = True
        for rec in rows:
            if banner_open and _is_title_banner(rec["text"], workbook_stem):
                banners.append({"sheet": sheet, "row": rec["row"],
                                "text": rec["text"]})
                continue
            banner_open = False
            records.append(rec)
    return wanted, records, banners


# ---------------------------------------------------------------------------
# Comparison / classification (read-only)
# ---------------------------------------------------------------------------
class _LengthIndex:
    """Existing normalized texts bucketed by length for the near-dup scan.

    Pure speed optimisation: the project's near-duplicate rule already requires
    ``min_len/max_len >= NEAR_DUP_LENGTH_RATIO``, so texts outside the length
    window can never qualify and are skipped.
    """

    def __init__(self, rows):
        self.by_len = {}
        for r in rows:
            n = r["normalized_text"]
            if n:
                self.by_len.setdefault(len(n), []).append(r)

    def candidates(self, length):
        lo = int(length * NEAR_DUP_LENGTH_RATIO)
        hi = int(length / NEAR_DUP_LENGTH_RATIO) + 1
        out = []
        for size in range(lo, hi + 1):
            out.extend(self.by_len.get(size, ()))
        return out

    def best(self, norm):
        best_row, best_score = None, 0.0
        for r in self.candidates(len(norm)):
            score = fuzz.WRatio(norm, r["normalized_text"])
            if score > best_score:
                best_row, best_score = r, score
                if best_score >= 100.0:
                    break
        return best_row, best_score


def _load_existing(conn):
    empty = ([], {}, {}, {}, set())
    if not _has_staging_tables(conn):
        # A staging DB that does not exist yet simply has no committed posts.
        return empty
    posts = conn.execute(
        "SELECT id, post_url, activity_id, normalized_text, post_text, "
        "source_sheet, source_row FROM linkedin_posts ORDER BY id").fetchall()
    by_norm, by_url, by_aid = {}, {}, {}
    for r in posts:
        if r["normalized_text"]:
            by_norm.setdefault(r["normalized_text"], r)
        if r["post_url"]:
            by_url.setdefault(r["post_url"], r)
        if r["activity_id"]:
            by_aid.setdefault(r["activity_id"], r)
    seen_occ = set()
    for r in conn.execute(
            "SELECT source_workbook, source_sheet, source_row, normalized_text "
            "FROM linkedin_post_occurrences"):
        seen_occ.add((r["source_workbook"] or "", r["source_sheet"], r["source_row"],
                      r["normalized_text"]))
    return posts, by_norm, by_url, by_aid, seen_occ


def compare(conn, records, workbook_name=""):
    """Classify every incoming record against the committed staging layer.

    Returns ``(decisions, stats)``.  Purely read-only.
    """
    posts, by_norm, by_url, by_aid, seen_occ = _load_existing(conn)
    existing_index = _LengthIndex(posts)

    decisions = []
    file_owner = {}          # normalized_text -> entry owning the canonical post
    file_order = []          # normalized_texts in first-seen order

    def register(norm, target_id, decision):
        """Remember the first incoming row that speaks for this post text.

        Registered for EVERY first-seen row, including rows that turned out to
        be duplicates of an already-committed post.  That is what makes a
        second run of the importer idempotent: a within-file near-duplicate
        resolves to the same canonical post instead of becoming a new one.
        """
        if not norm or norm in file_owner:
            return
        file_owner[norm] = {"target_id": target_id, "norm": norm,
                            "decision": decision, "occurrences": []}
        file_order.append(norm)

    for rec in records:
        text = rec["text"]
        url = rec.get("url") or ""
        norm = normalize_post_text(text)
        aid = extract_activity_id(url) if url else None
        # The workbook is part of the natural key: the same sheet/row/text in a
        # different workbook is a distinct source occurrence, not a replay.
        occ_key = (workbook_name, rec["sheet"], rec["row"], norm)

        d = {
            "sheet": rec["sheet"], "row": rec["row"],
            "text": text, "normalized_text": norm,
            "post_url": url or None, "activity_id": aid,
            "classification": None, "match_basis": None,
            "existing_post_id": None, "target_post_id": None,
            "occurrences": [occ_key],
            "occurrence_already_present": occ_key in seen_occ,
        }

        # 1) URL-based duplicate of a committed post.
        if url:
            hit = (by_aid.get(aid) if aid else None) or by_url.get(url)
            if hit is not None:
                d.update(classification=EXISTING_DUPLICATE, match_basis="url",
                         existing_post_id=hit["id"], target_post_id=hit["id"])
                register(norm, hit["id"], d)
                decisions.append(d)
                continue

        # 2) exact normalized-text duplicate of a committed post.
        hit = by_norm.get(norm) if norm else None
        if hit is not None:
            d.update(classification=EXISTING_DUPLICATE, match_basis="text_exact",
                     existing_post_id=hit["id"], target_post_id=hit["id"])
            register(norm, hit["id"], d)
            decisions.append(d)
            continue

        # 3) within-file exact duplicate.
        entry = file_owner.get(norm) if norm else None
        if entry is not None:
            entry["occurrences"].append(occ_key)
            d.update(classification=NEW_FILE_DUPLICATE, match_basis="text_exact_in_file",
                     existing_post_id=entry["target_id"],
                     target_post_id=entry["target_id"],
                     _owner_entry=entry)
            decisions.append(d)
            continue

        # 4) within-file near-exact duplicate (mirrors linkedin_staging._load 2c).
        near_entry, near_score = (None, 0.0)
        if norm:
            for n in file_order:
                lr = min(len(norm), len(n)) / max(len(norm), len(n))
                if lr < NEAR_DUP_LENGTH_RATIO:
                    continue
                s = fuzz.WRatio(norm, n)
                if s > near_score:
                    near_entry, near_score = file_owner[n], s
                    if near_score >= 100.0:
                        break
        if near_entry is not None and near_score >= NEAR_DUP_WRATIO:
            near_entry["occurrences"].append(occ_key)
            d.update(classification=NEW_FILE_DUPLICATE, match_basis="text_near_in_file",
                     existing_post_id=near_entry["target_id"],
                     target_post_id=near_entry["target_id"],
                     near_score=round(near_score, 2),
                     _owner_entry=near_entry)
            decisions.append(d)
            continue

        # 5) genuinely new post (possibly a near-match to a historical post).
        near_post, score = existing_index.best(norm) if norm else (None, 0.0)
        if near_post is not None and score >= NEAR_DUP_WRATIO:
            d.update(classification=POSSIBLE_DUPLICATE_REVIEW,
                     match_basis="text_near_existing",
                     existing_post_id=near_post["id"], near_score=round(score, 2))
        else:
            d.update(classification=NEW_POST, match_basis="unique")
        register(norm, None, d)
        file_owner[norm]["occurrences"].append(occ_key)
        decisions.append(d)

    return decisions, {"existing_canonical_posts": len(posts)}


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------
def _insert_post(conn, d, workbook_name, resolved_via):
    conn.execute(
        "INSERT INTO linkedin_posts "
        "(post_url, activity_id, post_text, normalized_text, resolved_via, "
        " source_sheet, source_row, source_workbook) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (d["post_url"], d["activity_id"], d["text"], d["normalized_text"],
         resolved_via, d["sheet"], d["row"], workbook_name),
    )
    return conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


def _insert_occurrence(conn, post_id, d, reason, dup_flag, workbook_name):
    conn.execute(
        "INSERT INTO linkedin_post_occurrences "
        "(linkedin_post_id, source_sheet, source_row, post_url, post_text, "
        " normalized_text, duplicate_flag, duplicate_reason, source_workbook) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (post_id, d["sheet"], d["row"], d["post_url"], d["text"],
         d["normalized_text"], dup_flag, reason, workbook_name),
    )


_COUNT_TABLES = OrderedDict((
    ("canonical_posts", "linkedin_posts"),
    ("occurrences", "linkedin_post_occurrences"),
    ("candidates", "linkedin_activity_candidates"),
))


def _table_exists(conn, table):
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone() is not None


def _counts(conn):
    """Row counts per staging table; tables that do not exist yet count as 0."""
    out = OrderedDict()
    for label, table in _COUNT_TABLES.items():
        if _table_exists(conn, table):
            out[label] = conn.execute(
                "SELECT COUNT(*) AS c FROM %s" % table).fetchone()["c"]
        else:
            out[label] = 0
    return out


def _has_staging_tables(conn):
    return _table_exists(conn, "linkedin_posts")


def import_workbook(workbook_path, db_path=None, sheets=None, dry_run=False):
    """Append genuinely new posts from ``workbook_path`` to the staging DB.

    Returns a report dict.  ``dry_run=True`` performs the full comparison and
    writes nothing at all.
    """
    db_path = db_path or staging.STAGING_DB_PATH
    workbook_name = os.path.basename(workbook_path)
    sheet_names, records, banners = read_workbook_records(workbook_path, sheets)

    conn = get_staging_connection(db_path)
    try:
        if dry_run:
            # Never create tables during a dry run, but still be able to report
            # against a DB that does not exist yet.
            added_columns = []
            before = (_counts(conn) if _has_staging_tables(conn)
                      else OrderedDict((label, 0) for label in _COUNT_TABLES))
        else:
            # Create/extend the schema first so a brand-new staging DB works.
            added_columns = ensure_provenance_columns(conn)
            before = _counts(conn)
        decisions, meta = compare(conn, records, workbook_name)

        by_class = Counter(d["classification"] for d in decisions)
        new_decisions = [d for d in decisions
                         if d["classification"] in (NEW_POST, POSSIBLE_DUPLICATE_REVIEW)]
        possible = [d for d in decisions
                    if d["classification"] == POSSIBLE_DUPLICATE_REVIEW]
        skipped_occ = [d for d in decisions if d["occurrence_already_present"]]

        new_post_ids = []
        if not dry_run:
            # 1) create the new canonical posts first so every duplicate
            #    occurrence can resolve its owner id in one place below.
            for d in new_decisions:
                resolved_via = ("text_near"
                                if d["classification"] == POSSIBLE_DUPLICATE_REVIEW else None)
                d["target_post_id"] = _insert_post(conn, d, workbook_name, resolved_via)
                new_post_ids.append(d["target_post_id"])
            # 1b) A within-file duplicate that points at a post created during
            #     THIS run captured target_post_id=None back in compare(), before
            #     the owner existed. Re-resolve those now that it has an id,
            #     otherwise the duplicate's occurrence would be silently dropped.
            for d in decisions:
                entry = d.get("_owner_entry")
                if not entry:
                    continue
                owner = entry.get("decision") or {}
                owner_id = owner.get("target_post_id")
                if owner_id is not None:
                    d["target_post_id"] = owner_id
                    d["existing_post_id"] = owner_id
            by_id = {r["id"]: r for r in conn.execute(
                "SELECT id, post_url FROM linkedin_posts").fetchall()}
            # 2) one occurrence per incoming row, attached to its canonical post.
            for d in decisions:
                if d["occurrence_already_present"]:
                    continue
                target = d["target_post_id"]
                if target is None or target not in by_id:
                    continue
                if d["classification"] in (NEW_POST, POSSIBLE_DUPLICATE_REVIEW):
                    reason, dup = "unique", 0
                elif d["match_basis"] == "url":
                    reason, dup = "duplicate_url", 1
                elif by_id[target]["post_url"]:
                    reason, dup = "url_match_resolved", 0
                else:
                    reason, dup = "duplicate_text_exact", 1
                _insert_occurrence(conn, target, d, reason, dup, workbook_name)
            conn.commit()
            after = _counts(conn)
        else:
            after = before

        return {
            "workbook": os.path.abspath(workbook_path),
            "workbook_name": workbook_name,
            "workbook_sha256": _sha256(workbook_path),
            "workbook_bytes": os.path.getsize(workbook_path),
            "sheets": sheet_names,
            "title_banners_skipped": banners,
            "incoming_rows": len(records),
            "existing_canonical_posts_before": meta["existing_canonical_posts"],
            "classification": dict(by_class),
            "possible_duplicates": [
                {"sheet": d["sheet"], "row": d["row"], "near_score": d.get("near_score"),
                 "existing_post_id": d["existing_post_id"]} for d in possible],
            "occurrence_already_present": len(skipped_occ),
            "new_post_ids": new_post_ids,
            "staging_before": before,
            "staging_after": after,
            "schema_columns_added": added_columns,
            "dry_run": dry_run,
            "decisions": [{k: v for k, v in d.items() if k != "_owner_entry"}
                          for d in decisions],
        }
    finally:
        conn.close()


def _sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def summarize(report):
    """Compact, JSON-friendly view of an import report (no post bodies)."""
    out = {k: v for k, v in report.items() if k != "decisions"}
    out["possible_duplicate_count"] = len(report["possible_duplicates"])
    return out


def _print_report(report):
    print("=" * 70)
    print("LINKEDIN INCREMENTAL IMPORT")
    print("=" * 70)
    print("workbook          : %s" % report["workbook_name"])
    print("workbook sha256   : %s" % report["workbook_sha256"])
    print("workbook bytes    : %d" % report["workbook_bytes"])
    print("sheets            : %s" % ", ".join(report["sheets"]))
    print("title banners     : %d skipped" % len(report["title_banners_skipped"]))
    print("incoming rows     : %d" % report["incoming_rows"])
    print("-" * 70)
    for key in (EXISTING_DUPLICATE, NEW_FILE_DUPLICATE, POSSIBLE_DUPLICATE_REVIEW, NEW_POST):
        print("  %-24s %d" % (key, report["classification"].get(key, 0)))
    print("-" * 70)
    print("staging BEFORE    : %s" % dict(report["staging_before"]))
    print("staging AFTER     : %s" % dict(report["staging_after"]))
    print("schema columns    : %s" % (", ".join(report["schema_columns_added"]) or "(none)"))
    print("dry run           : %s" % report["dry_run"])
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Append new LinkedIn posts from an extra workbook to the staging DB.")
    parser.add_argument("workbook", nargs="?",
                        default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "Posts From June 2026 - September 2026.xlsx"))
    parser.add_argument("--db", default=None, help="staging DB path")
    parser.add_argument("--sheet", action="append", dest="sheets", default=None,
                        help="import only this sheet (repeatable)")
    parser.add_argument("--dry-run", action="store_true",
                        help="compare only; write nothing")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="write the machine-readable report to this path")
    args = parser.parse_args()

    result = import_workbook(args.workbook, db_path=args.db, sheets=args.sheets,
                             dry_run=args.dry_run)
    _print_report(result)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(summarize(result), fh, indent=2, default=str)
        print("json report   : %s" % args.json_out)
