"""Phase 4 - SAFE-TO-FIX cleanup batch (per report Section J + strict rules).

Applies only deterministic, non-speculative corrections:

1. Duplicate auto-merge (SAFE per report item 1 + STRICT RULE):
   - Rebuild a real duplicate-pair table (columns:
     activity_a, activity_b, method, score, status).
   - Auto-merge ONLY pairs that are EXACT normalized-title matches AND resolve
     to the SAME period AND share the SAME public-category set AND agree on
     department AND stakeholder. Fuzzy pairs stay status='pending'.
   - Merge keeps the canonical activity (richest description), re-points every
     provenance row (activity_sources, activity_categories, activity_departments,
     activity_stakeholders, activity_candidate_links, final_activity_metadata
     evidence) to the canonical id, merges evidence into the canonical metadata
     row, writes a review_history audit row per merge, then removes the
     duplicate institutional_activities row.

2. Park junk in the review queue (SAFE per report item 6, non-destructive):
   - 26 heuristic non-activities get review_queue rows (reason
     'heuristic-non-activity', status 'open') unless already flagged.
   - 10 existing 'validation-flag: missing-description' flags are left intact
     (already present and open).

Nothing else is changed: no category remapping, no General reclassification,
no department/stakeholder fills, no date backfill, no description invention.

Usage:
    python scripts/phase4_safe_fix_cleanup.py [db_path]

If db_path is omitted the live DATABASE_PATH is used. Pass a path to a copy
of the DB to dry-run safely.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.init_db import get_connection
from backend.database.category_catalog import PUBLIC_CATEGORY_CODES
from backend.database.department_catalog import normalize_department, GENERAL_NAME
from backend.database.period_catalog import PeriodResolver

REVIEWER = "phase4-safe-fix"
NOW = dt.datetime.now().isoformat(timespec="seconds")
LOG_DIR = Path("data/reports")


def q(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def log(conn, activity_id, field_name, old_value, new_value, action, reason):
    conn.execute(
        """INSERT INTO review_history
           (activity_id, field_name, old_value, new_value, action, reviewer, reason, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (activity_id, field_name, old_value, new_value, action, REVIEWER, reason, NOW),
    )


def build_merge_plan(conn, resolver):
    rows = q(
        conn,
        """SELECT a.id, a.title, a.normalized_title, a.description
           FROM institutional_activities a""",
    )
    by_id = {r["id"]: dict(r) for r in rows}

    cat_codes = {}
    for r in q(
        conn,
        """SELECT ac.activity_id aid, c.code FROM activity_categories ac
           JOIN categories c ON c.id = ac.category_id""",
    ):
        cat_codes.setdefault(r["aid"], set()).add(r["code"])

    meta = {}
    for r in q(
        conn,
        """SELECT activity_id, department_display, stakeholder_display, evidence_text
           FROM final_activity_metadata""",
    ):
        meta[r["activity_id"]] = {
            "dept": normalize_department(r["department_display"]),
            "stakeholder": (r["stakeholder_display"] or "").strip(),
            "evidence": r["evidence_text"] or "",
        }

    exact = {}
    for r in rows:
        key = (r["normalized_title"] or "").strip().lower()
        if key:
            exact.setdefault(key, []).append(r["id"])

    clusters = []
    all_exact_pairs = []
    for key, members in exact.items():
        if len(members) < 2:
            continue
        groups = {}
        for aid in members:
            period = resolver.period_for(aid)
            codes = tuple(sorted(cat_codes.get(aid, set()) & PUBLIC_CATEGORY_CODES))
            groups.setdefault((period, codes), []).append(aid)
        for (period, codes), group in groups.items():
            if len(group) < 2 or not codes:
                continue
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    all_exact_pairs.append(tuple(sorted((group[i], group[j]))))
            depts = {meta.get(m, {}).get("dept", GENERAL_NAME) for m in group}
            stakes = {meta.get(m, {}).get("stakeholder", "") for m in group}
            if len(depts) > 1 or len(stakes) > 1:
                continue
            descs = {m: (by_id[m]["description"] or "").strip() for m in group}
            canon = max(group, key=lambda m: (len(descs[m]), -m))
            dups = sorted(set(group) - {canon})
            clusters.append({
                "canonical": canon, "duplicates": dups,
                "period": period, "codes": list(codes),
            })

    clusters_deduped = clusters
    merged_ids = sorted(set(d for c in clusters_deduped for d in c["duplicates"]))
    dup_ids = set(merged_ids)
    return {"clusters": clusters_deduped, "merged_ids": merged_ids, "dup_ids": dup_ids,
            "exact_pairs": sorted(set(all_exact_pairs))}


def build_fuzzy_pairs(conn, resolver, activities):
    try:
        from rapidfuzz import fuzz
    except Exception:
        return []
    by_period = {}
    for a in activities:
        p = resolver.period_for(a["id"])
        key = (a["normalized_title"] or "").strip().lower()
        if key:
            by_period.setdefault(p, []).append(a)
    prep = re.compile(r"[^a-z0-9]+")

    def sig(a):
        toks = [t for t in prep.sub(" ", (a["normalized_title"] or "").lower()).split() if len(t) > 2]
        return tuple(sorted(set(toks))[:3])

    pairs = []
    seen = set()
    for period, group in by_period.items():
        buckets = {}
        for a in group:
            buckets.setdefault(sig(a), []).append(a)
        for bucket in buckets.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    ai, aj = bucket[i], bucket[j]
                    pair = tuple(sorted((ai["id"], aj["id"])))
                    if pair in seen:
                        continue
                    ratio = fuzz.token_sort_ratio(ai["title"] or "", aj["title"] or "")
                    if ratio >= 97:
                        seen.add(pair)
                        pairs.append({"a": ai["id"], "b": aj["id"], "score": round(ratio, 1),
                                      "period_a": period, "period_b": period})
    return pairs


def collect_heuristic_flags(conn):
    rows = q(
        conn,
        """SELECT a.id, a.title, a.description, m.evidence_text
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id""",
    )
    boilerplate = re.compile(
        r"^\s*(events?\s*(\||-|–|:)|menu|home\s*\|?|about\s*(\||$)|contact(\s*(\||$))"
        r"|academics(\s*(\||$))|admission|\s*\|\s*tce\s*$|page not found|404|"
        r"campus\s*life|student life|quick links|site map|search results|coming soon)",
        re.I,
    )
    flagged = []
    for r in rows:
        title = (r["title"] or "").strip()
        desc = (r["description"] or "").strip()
        reasons = []
        if boilerplate.match(title):
            reasons.append("boilerplate/navigation-style title")
        if not desc and not (r["evidence_text"] or "").strip():
            reasons.append("no description and no evidence text")
        if reasons:
            flagged.append({"id": r["id"], "title": title, "reasons": reasons})
    return flagged


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", nargs="?", default=None)
    args = parser.parse_args(argv)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection(args.db_path)
    resolver = PeriodResolver(conn=conn)
    run = {"timestamp": NOW, "reviewer": REVIEWER, "steps": []}
    try:
        activities_rows = q(conn, """SELECT id, title, normalized_title FROM institutional_activities""")
        activities = [dict(r) for r in activities_rows]

        plan = build_merge_plan(conn, resolver)
        merged = plan["merged_ids"]
        run["merge_clusters"] = len(plan["clusters"])
        run["duplicates_merged"] = len(merged)
        run["total_before"] = len(activities)
        run["total_after"] = len(activities) - len(merged)

        # ---- step 1: duplicate pair table ----
        conn.execute("DROP TABLE IF EXISTS duplicate_pairs_safefix")
        conn.execute(
            """CREATE TABLE duplicate_pairs_safefix (
                activity_a INTEGER, activity_b INTEGER, method TEXT,
                score REAL, status TEXT, created_at TEXT)"""
        )
        for a, b in plan["exact_pairs"]:
            method = "exact-normalized-title"
            status = "merged" if a in merged or b in merged else "pending"
            conn.execute(
                "INSERT INTO duplicate_pairs_safefix VALUES (?,?,?,?,?,?)",
                (a, b, method, 100.0, status, NOW))
        fuzzy = build_fuzzy_pairs(conn, resolver, activities)
        exact_set = set(plan["exact_pairs"])
        for p in fuzzy:
            pair = sorted((p["a"], p["b"]))
            if tuple(pair) in exact_set:
                continue
            conn.execute(
                "INSERT INTO duplicate_pairs_safefix VALUES (?,?,?,?,?,?)",
                tuple(pair) + ("fuzzy-token-sort-geq97", p["score"], "pending", NOW))
        run["pair_table_total"] = conn.execute(
            "SELECT COUNT(*) FROM duplicate_pairs_safefix").fetchone()[0]
        run["pair_table_merged"] = conn.execute(
            "SELECT COUNT(*) FROM duplicate_pairs_safefix WHERE status='merged'").fetchone()[0]
        run["pair_table_pending"] = conn.execute(
            "SELECT COUNT(*) FROM duplicate_pairs_safefix WHERE status='pending'").fetchone()[0]

        # ---- step 2: execute the merges ----
        merge_log = []
        for c in plan["clusters"]:
            canon = c["canonical"]
            for dup in c["duplicates"]:
                merge_log.append(merge_duplicate(conn, canon, dup, c["period"], c["codes"]))
        run["steps"].append({"action": "merge_duplicates", "detail": merge_log})

        # ---- step 3: park heuristic flags (non-destructive) ----
        flags = collect_heuristic_flags(conn)
        flagged_ids = {f["id"] for f in flags}
        existing = {r["activity_id"] for r in q(conn, """SELECT activity_id FROM review_queue""")}
        parked = 0
        parked_detail = []
        for f in flags:
            if f["id"] in existing:
                continue
            conn.execute(
                """INSERT INTO review_queue
                   (activity_id, reason, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (f["id"], "validation-flag: " + "; ".join(f["reasons"]), "open", NOW, NOW))
            parked += 1
            parked_detail.append({"activity_id": f["id"], "reason": f["reasons"]})
        run["steps"].append({"action": "park_review_flags", "count": parked, "detail": parked_detail})
        run["review_flags_parked"] = parked
        run["review_flags_total_open"] = conn.execute(
            "SELECT COUNT(*) FROM review_queue WHERE status='open'").fetchone()[0]

        conn.commit()
    finally:
        conn.close()

    run["ok"] = True
    run["expected_reference"] = {
        "total_before": 2320, "work_invariant": 97, "general_invariant": 813,
        "ws2025_invariant": 10, "it2025_invariant": 29, "tseda2024_invariant": 47,
    }
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = LOG_DIR / f"part27_safefix_run_{stamp}.json"
    out.write_text(json.dumps(run, indent=2, default=str), encoding="utf-8")
    print(out)
    return run


def merge_duplicate(conn, canon, dup, period, codes):
    detail = {"canonical": canon, "duplicate": dup, "period": period, "codes": codes}

    # preserve the primary source_url on the canonical if it currently lacks one
    canon_row = q(conn, "SELECT source_url FROM institutional_activities WHERE id=?", (canon,))[0]
    dup_row = q(conn, "SELECT source_url FROM institutional_activities WHERE id=?", (dup,))[0]
    if not (canon_row["source_url"] or "").strip() and (dup_row["source_url"] or "").strip():
        conn.execute("UPDATE institutional_activities SET source_url=? WHERE id=?",
                     (dup_row["source_url"], canon))
        detail["primary_source_url_inherited"] = dup_row["source_url"]

    # preserve every source URL/provenance row by re-pointing them at canonical
    dup_srcs = q(conn, """SELECT * FROM activity_sources WHERE activity_id=?""", (dup,))
    kept_urls = set()
    for r in q(conn, """SELECT source_url FROM activity_sources WHERE activity_id=?""", (canon,)):
        kept_urls.add(r["source_url"])
    moved = 0
    for row in dup_srcs:
        if row["source_url"] in kept_urls:
            conn.execute("DELETE FROM activity_sources WHERE id=?", (row["id"],))
            continue
        conn.execute("UPDATE activity_sources SET activity_id=? WHERE id=?", (canon, row["id"]))
        kept_urls.add(row["source_url"])
        moved += 1
    srcs = q(conn, """SELECT source_url FROM activity_sources WHERE activity_id=?""", (canon,))
    detail["source_urls"] = [r["source_url"] for r in srcs]
    detail["source_rows_moved"] = moved
    detail["source_rows_duplicate_urls_removed"] = len(dup_srcs) - moved

    # re-point candidate links (dedupe on (activity_id, candidate_id))
    for r in q(conn, "SELECT id, candidate_id FROM activity_candidate_links WHERE activity_id=?", (dup,)):
        exists = q(conn, "SELECT 1 FROM activity_candidate_links WHERE activity_id=? AND candidate_id=?",
                   (canon, r["candidate_id"]))
        if exists:
            conn.execute("DELETE FROM activity_candidate_links WHERE id=?", (r["id"],))
        else:
            conn.execute("UPDATE activity_candidate_links SET activity_id=? WHERE id=?",
                         (canon, r["id"]))
    detail["candidate_links_moved"] = True

    # re-point period-recovery audit trail and any linkedin matches
    if q(conn, "SELECT 1 FROM period_recovery_audit WHERE activity_id=?", (canon,)):
        # canonical already holds its own 1:1 recovery telemetry; removing the
        # dup's row avoids orphaning (UNIQUE(activity_id)); noted in the log.
        n = conn.execute("DELETE FROM period_recovery_audit WHERE activity_id=?", (dup,)).rowcount
        detail["period_recovery_audit_rows_removed_after_canonical_owns_recovery"] = n
    else:
        conn.execute("UPDATE period_recovery_audit SET activity_id=? WHERE activity_id=?",
                     (canon, dup))
        detail["period_recovery_audit_repointed"] = True
    conn.execute("UPDATE linkedin_matches SET activity_id=? WHERE activity_id=?",
                 (canon, dup))

    # union categories/departments/stakeholders (dedupe on target + method rank)
    for link_table, fk in (
        ("activity_categories", "category_id"),
        ("activity_departments", "department_id"),
        ("activity_stakeholders", "stakeholder_id"),
    ):
        dup_rows = q(conn, f"SELECT * FROM {link_table} WHERE activity_id=?", (dup,))
        for row in dup_rows:
            exists = q(
                conn,
                f"SELECT 1 FROM {link_table} WHERE activity_id=? AND {fk}=?",
                (canon, row[fk]),
            )
            if not exists:
                conn.execute(
                    f"UPDATE {link_table} SET activity_id=? WHERE id=?", (canon, row["id"]))
            else:
                conn.execute(f"DELETE FROM {link_table} WHERE id=?", (row["id"],))

    def merge_metadata(target_row, source_row):
        if not source_row:
            return
        if not target_row:
            return
        fields = (
            ("activity_date_text", "activity_date_text"),
            ("academic_year", "academic_year"),
            ("department_display", "department_display"),
            ("stakeholder_display", "stakeholder_display"),
            ("achievement_outcome", "achievement_outcome"),
        )
        for tgt_field, src_field in fields:
            src_val = source_row[src_field]
            if src_val is None or str(src_val).strip() == "":
                continue
            cur = target_row[tgt_field]
            if cur is None or str(cur).strip() == "":
                conn.execute(f"UPDATE final_activity_metadata SET {tgt_field}=? WHERE activity_id=?",
                             (src_val, canon))
                continue
            if tgt_field == "evidence_text":
                pass  # evidence merged separately below
        tgt_ev = (target_row["evidence_text"] or "").strip()
        src_ev = (source_row["evidence_text"] or "").strip()
        if src_ev and tgt_ev and src_ev != tgt_ev:
            merged = f"{tgt_ev}\n{src_ev}"
            conn.execute("UPDATE final_activity_metadata SET evidence_text=? WHERE activity_id=?",
                         (merged, canon))
        elif src_ev and not tgt_ev:
            conn.execute("UPDATE final_activity_metadata SET evidence_text=? WHERE activity_id=?",
                         (src_ev, canon))
        detail["evidence_merged_from"] = dup

    canon_meta = q(conn, "SELECT * FROM final_activity_metadata WHERE activity_id=?", (canon,))
    dup_meta = q(conn, "SELECT * FROM final_activity_metadata WHERE activity_id=?", (dup,))
    if dup_meta:
        if not canon_meta:
            conn.execute("UPDATE final_activity_metadata SET activity_id=? WHERE activity_id=?",
                         (canon, dup))
        else:
            merge_metadata(canon_meta[0], dup_meta[0])
            conn.execute("DELETE FROM final_activity_metadata WHERE activity_id=?", (dup,))
    detail["metadata"] = "merged-into-canonical"

    # audit trail for the merge
    old = q(conn, "SELECT title FROM institutional_activities WHERE id=?", (dup,))
    new = q(conn, "SELECT title FROM institutional_activities WHERE id=?", (canon,))
    log(conn, canon, "duplicate_activity_id", dup, canon, "merge",
        f"exact-title same-period({period}) same-category({','.join(codes)}) "
        f"'{old[0]['title'] if old else ''}' -> '{new[0]['title'] if new else ''}'")

    # remove the duplicate activity row last (after all provenance is re-pointed)
    conn.execute("DELETE FROM institutional_activities WHERE id=?", (dup,))
    detail["deleted"] = dup
    return detail


if __name__ == "__main__":
    main()