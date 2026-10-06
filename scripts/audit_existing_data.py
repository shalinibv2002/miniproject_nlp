"""Phase 4 - existing-data audit (READ-ONLY).

Produces data/audit/existing_data_audit_YYYYMMDD.{json,md} against the live
database (config.DATABASE_PATH).  It never writes to the DB, never deletes,
never merges, and never mutates metadata: everything below is diagnostic and
uses the same read-time resolvers the public UI uses so the counts reconcile
with the running application.

Usage:
    python scripts/audit_existing_data.py [db_path] [--stamp STAMP]
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.init_db import get_connection
from backend.database.category_catalog import (
    CATEGORY_PUBLIC_NAMES, DEPARTMENTAL_CATEGORIES, GENERAL_CATEGORIES,
    PUBLIC_CATEGORY_CODES,
)
from backend.database.department_catalog import (
    GENERAL_NAME, PUBLIC_DEPARTMENTS, normalize_department,
)
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, PUBLIC_PERIOD_OPTIONS, PeriodResolver,
    resolve_period,
)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ = True
except Exception:  # pragma: no cover
    fuzz = None
    RAPIDFUZZ = False

TODAY = dt.date.today()
OUT_DIR = Path("data/audit")


def q(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", nargs="?", default=None)
    parser.add_argument("--stamp", default=None)
    args = parser.parse_args(argv)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    connection = get_connection(args.db_path)  # read-only connection to the live DB
    try:
        audit = audit_database(connection)
    finally:
        connection.close()

    stamp = args.stamp or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"existing_data_audit_{stamp}.json"
    md_path = OUT_DIR / f"existing_data_audit_{stamp}.md"
    json_path.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    md_path.write_text(render_markdown(audit), encoding="utf-8")
    print(f"JSON -> {json_path}")
    print(f"MD   -> {md_path}")
    return audit


def audit_database(conn):
    resolver = PeriodResolver(conn=conn)
    activities = []
    rows = q(
        conn,
        """SELECT a.id, a.title, a.normalized_title, a.description, a.activity_date,
                  a.activity_date_end, a.venue, a.organizer, a.resource_person,
                  a.overall_confidence, a.is_verified, a.source_url,
                  m.academic_year AS stored_year, m.activity_date_text,
                  m.department_display, m.stakeholder_display, m.achievement_outcome,
                  m.evidence_text
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id""",
    )
    for r in rows:
        act = dict(r)
        act["period"] = resolver.period_for(r["id"])
        act["dept"] = normalize_department(r["department_display"])
        activities.append(act)

    by_id = {a["id"]: a for a in activities}

    cat_codes = collections.defaultdict(set)
    for r in q(
        conn,
        """SELECT ac.activity_id AS aid, c.code
           FROM activity_categories ac JOIN categories c ON c.id = ac.category_id""",
    ):
        cat_codes[r["aid"]].add(r["code"])
    for a in activities:
        a["codes"] = cat_codes[a["id"]]

    links = collections.defaultdict(list)
    for r in q(
        conn,
        """SELECT activity_id, candidate_id FROM activity_candidate_links""",
    ):
        links[r["activity_id"]].append(r["candidate_id"])

    cand_class = {}
    cand_quality = {}
    for r in q(
        conn,
        """SELECT candidate_id, final_category, classification_confidence, category_hint,
                  hint_match_status
           FROM candidate_classifications""",
    ):
        cand_class[r["candidate_id"]] = dict(r)
    for r in q(conn, """SELECT candidate_id, quality_status, quality_reason FROM candidate_quality_reviews"""):
        cand_quality[r["candidate_id"]] = dict(r)

    sources = {}
    for r in q(
        conn,
        """SELECT s.activity_id, s.source_url, s.raw_record_id,
                  COALESCE(rg.name,'') AS reg_name, COALESCE(rg.source_type,'') AS reg_type
           FROM activity_sources s
           LEFT JOIN source_registry rg ON rg.id = s.source_registry_id""",
    ):
        sources.setdefault(r["activity_id"], []).append(dict(r))

    audits = {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "db_path": str(conn.execute("SELECT 'tce_activity_intelligence'").fetchone()[0]),
        "overall": overall(activities, cat_codes, sources),
        "period_audit": period_audit(activities, conn),
        "category_audit": category_audit(activities, cat_codes),
        "general_breakdown": general_breakdown(activities),
        "category_text_advisory": category_text_advisory(activities, cat_codes),
        "department_audit": department_audit(activities),
        "stakeholder_audit": stakeholder_audit(activities),
        "duplicate_audit": duplicate_audit(activities),
        "non_activity_audit": non_activity_audit(activities, links, conn),
        "source_audit": source_audit(activities, sources, conn),
        "date_audit": date_audit(activities),
        "description_audit": description_audit(activities),
        "coverage": coverage(activities, cat_codes),
        "sanity": sanity_checks(activities, cat_codes),
        "existing_flags": existing_flags(conn),
    }
    return audits


def overall(activities, cat_codes, sources):
    total = len(activities)
    no_source = [a for a in activities if not sources.get(a["id"]) and not a["source_url"]]
    no_date = [a for a in activities if not a["activity_date"]]
    no_cat = [a for a in activities if not (cat_codes[a["id"]] & PUBLIC_CATEGORY_CODES)]
    no_cat_any = [a for a in activities if not cat_codes[a["id"]]]
    no_dept = [a for a in activities if not (a["department_display"] or "").strip()]
    no_stake = [a for a in activities if not (a["stakeholder_display"] or "").strip()]
    weak_desc = [a for a in activities if text_len(a["description"]) < 20]

    return {
        "total_records": total,
        "has_structured_date": total - len(no_date),
        "missing_date": len(no_date),
        "has_public_category": total - len(no_cat),
        "missing_public_category": len(no_cat),
        "missing_any_category": len(no_cat_any),
        "missing_department_field": len(no_dept),
        "missing_stakeholder_field": len(no_stake),
        "missing_source": len(no_source),
        "weak_or_empty_description": len(weak_desc),
        "example_missing_category": sample_titles(no_cat, 3),
        "example_missing_stakeholder": sample_titles(no_stake, 3),
        "example_missing_source": sample_titles(no_source, 3),
        "example_missing_date": sample_titles(no_date, 3),
    }


def sample_titles(items, n):
    titles = []
    for a in items:
        t = (a["title"] or "").strip()
        if t and t not in titles:
            titles.append(t)
        if len(titles) >= n:
            break
    return titles


def text_len(value):
    return len(str(value or "").strip())


def period_audit(activities, conn):
    by_resolved = collections.Counter(a["period"] for a in activities)
    stored = collections.Counter()
    for a in activities:
        key = a["stored_year"] or "(missing)"
        stored[key] += 1
    unknown_no_trail = [
        a for a in activities
        if a["period"] == BEFORE_2021
        and not a["activity_date"]
        and not year_token(a["activity_date_text"]) and not year_token(a["evidence_text"])
    ]
    outside = {k: v for k, v in sorted(stored.items()) if k not in PUBLIC_PERIODS and k != "(missing)"}
    return {
        "resolved": {k: by_resolved.get(k, 0) for k in PUBLIC_PERIOD_OPTIONS},
        "stored_academic_year_distribution": dict(sorted(stored.items())),
        "records_outside_intended_period": outside,
        "stored_year_missing": stored.get("(missing)", 0),
        "presented_as_before_2021_with_no_date_or_year_evidence": len(unknown_no_trail),
        "example_unknown_period": sample_titles(unknown_no_trail, 3),
    }


YEAR_TOKEN = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def year_token(*texts):
    for text in texts:
        if not text:
            continue
        if YEAR_TOKEN.search(str(text)):
            return True
    return False


def category_audit(activities, cat_codes):
    code_counts = collections.Counter()
    for a in activities:
        for code in cat_codes[a["id"]]:
            code_counts[code] += 1
    public = {
        code: code_counts.get(code, 0)
        for code in sorted(PUBLIC_CATEGORY_CODES)
    }
    legacy = {
        code: count for code, count in sorted(code_counts.items())
        if code not in PUBLIC_CATEGORY_CODES
    }
    multi_cat = [a for a in activities if len(cat_codes[a["id"]]) > 1]
    general_activities = [a for a in activities if a["dept"] == GENERAL_NAME]
    general_cat_counts = collections.Counter()
    for a in general_activities:
        for code in cat_codes[a["id"]]:
            general_cat_counts[code] += 1
    by_dept_scope = collections.Counter(
        "general" if a["dept"] == GENERAL_NAME else "departmental" for a in activities
    )
    return {
        "public_category_counts": dict(sorted(public.items(), key=lambda kv: (-kv[1], kv[0]))),
        "legacy_non_public_codes": legacy,
        "multi_category_activities": len(multi_cat),
        "example_multi_category": [
            {"id": a["id"], "title": a["title"], "codes": sorted(cat_codes[a["id"]])}
            for a in multi_cat[:5]
        ],
        "general_scope_activities": len(general_activities),
        "general_scope_category_counts": dict(
            sorted(general_cat_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        "scope_split": dict(by_dept_scope),
        "uncategorized_activities": sum(1 for a in activities if not cat_codes[a["id"]]),
        "high_outliers": [code for code, count in public.items() if count >= 200],
        "low_outliers": [code for code, count in public.items() if 0 < count < 5],
    }


DEPT_HINT = re.compile(
    r"\b(?:cse|cs|it|ece|eee|civil|mech(?:anical)?|arch(?:itecture)?|"
    r"chemistry|physics|mathematics|computer science|computer applications|"
    r"mee?chatronics|data science|ai|artificial intelligence|"
    r"biotech|mca|cse-?)(?: engineering| department| dept| dept\.)?\b",
    re.I,
)
INST_MARKERS = re.compile(
    r"\b(?:tce|thiagarajar|institution[- ]wide|college[- ]wide|all (?:the )?dept"
    r"|inter ?departmental|anna university|college day|annual sports|campus|"
    r"central (?:library|office)|hostel|training & placement|t&p)"
    r"|\bwomens\b|\bmens\b",
    re.I,
)


def general_breakdown(activities):
    """Estimate why the General (institution-wide) bucket is so large.

    Advisory only: uses title/description/evidence keywords and date presence to
    bucket General records into institution-wide vs departmental-but-unassigned
    vs insufficient-information. Nothing is reclassified.
    """
    general = [a for a in activities if a["dept"] == GENERAL_NAME]
    buckets = collections.Counter()
    examples = collections.defaultdict(list)
    for a in general:
        text = " ".join(filter(None, [a["title"], a["description"], a["evidence_text"]]))
        has_date = bool(a["activity_date"])
        title_only = not (a["description"] or "").strip() and not (a["evidence_text"] or "").strip()
        has_dept = DEPT_HINT.search(text)
        has_inst = INST_MARKERS.search(text)
        if has_dept and not has_inst:
            bucket = "departmental_text_present"
        elif has_inst:
            bucket = "institution_wide_markers"
        elif title_only:
            bucket = "insufficient_info_title_only"
        elif not has_date:
            bucket = "no_date_but_some_evidence"
        else:
            bucket = "dated_no_clear_scope"
        buckets[bucket] += 1
        if len(examples[bucket]) < 6:
            examples[bucket].append({"id": a["id"], "title": (a["title"] or "")[:70]})
    return {
        "general_total": len(general),
        "bucket_counts": dict(buckets.most_common()),
        "bucket_examples": {k: v for k, v in examples.items()},
        "note": "Advisory keyword/date classification. Dept-specific sporting or "
                "award text can still be institution-wide; inspection recommended.",
    }


CATEGORY_KEYWORDS = {
    "WORKSHOP": ["workshop"],
    "HACKATHON": ["hackathon"],
    "WEBINAR": ["webinar", "online seminar", "virtual talk"],
    "FDP": ["fdp", "faculty development program"],
    "STTP": ["sttp"],
    "GUEST_LECTURE": ["guest lecture", "guest talk", "distinguished lecture"],
    "CONFERENCE": ["conference"],
    "SYMPOSIUM": ["symposium"],
    "SEMINAR": ["seminar"],
    "NCC": ["ncc"],
    "OUTREACH": ["outreach", "extension activity", "blood donation", "campus cleaning"],
    "PLACEMENT": ["placement drive", "placement training", "campus recruitment"],
    "INTERNSHIP": ["internship"],
    "RESEARCH": ["patent", "patents", "sponsored research", "sponsored project"],
    "INDUSTRY": ["mou", "memorandum of understanding", "mo us"],
    "SPORTS": ["sports day", "tournament", "inter-college", "athletics meet"],
    "CULTURAL": ["cultural", "fresher's"],
    "CLUB": ["student chapter", "institution's innovation council"],
    "CAMPUS": ["campus"],
}


def category_text_advisory(activities, cat_codes):
    specific = {"WORKSHOP", "HACKATHON", "WEBINAR", "FDP", "STTP", "GUEST_LECTURE",
                "CONFERENCE", "SYMPOSIUM", "SEMINAR", "NCC", "INTERNSHIP", "PLACEMENT"}
    flags = []
    for a in activities:
        text = " ".join(filter(None, [a["title"], a["description"], a["evidence_text"]])).lower()
        suggestions = set()
        for code, words in CATEGORY_KEYWORDS.items():
            if any(w in text for w in words):
                suggestions.add(code)
        stored = {code for code in cat_codes[a["id"]] if code in PUBLIC_CATEGORY_CODES}
        conflicting = (suggestions & specific) - stored
        if conflicting:
            flags.append({
                "id": a["id"], "title": a["title"],
                "stored": sorted(stored),
                "suggested_by_text": sorted(conflicting),
            })
    return {
        "advisory_flagged": len(flags),
        "examples": flags[:25],
        "note": "Text-vs-category advisory only; highlights likely mislabelled "
                "records for human review. Nothing is changed.",
    }


def department_audit(activities):
    public_counts = collections.Counter()
    general = 0
    other = collections.Counter()
    multi = []
    for a in activities:
        parts = [p for p in a["dept"].split("; ") if p]
        if a["dept"] == GENERAL_NAME:
            general += 1
            continue
        if len(parts) > 1:
            multi.append(a)
        for part in parts:
            if part in PUBLIC_DEPARTMENTS:
                public_counts[part] += 1
            else:
                other[part] += 1
    return {
        "general_institution_wide": general,
        "public_departments": {name: public_counts.get(name, 0) for name in PUBLIC_DEPARTMENTS},
        "out_of_master_values": dict(sorted(other.items(), key=lambda kv: -kv[1])),
        "multi_department_records": len(multi),
        "multi_department_examples": [
            {"id": a["id"], "title": a["title"], "departments": a["dept"]} for a in multi[:8]
        ],
        "storage_spelling_variants": dict(collections.Counter(
            str(a["department_display"] or "").strip() for a in activities
        ).most_common()),
    }


def stakeholder_audit(activities):
    values = collections.Counter(a["stakeholder_display"] or "(missing)" for a in activities)
    return {
        "counts": dict(sorted(values.items(), key=lambda kv: -kv[1])),
        "missing": values.get("(missing)", 0),
        "values_outside_supported_set": {
            k: v for k, v in sorted(values.items())
            if k == "(missing)" or not any(s in k for s in
                ("Students", "Faculty", "Staff", "Alumni", "Industry", "Institution", "External"))
        },
    }


def _norm_url(url):
    return re.sub(r"^https?://(www\.)?", "", (url or "").strip().lower()).rstrip("/")


def duplicate_audit(activities):
    by_url = collections.defaultdict(list)
    for a in activities:
        urls = set()
        if a["source_url"]:
            urls.add(_norm_url(a["source_url"]))
        # primary source_url is also the first activity_sources row, so url
        # duplicates are detected from the primary field here.
        for u in urls:
            by_url[u].append(a)

    url_dups = []
    for url, group in by_url.items():
        if len(group) > 1:
            ids = sorted({a["id"] for a in group})
            url_dups.append({"url": url, "activity_ids": ids, "count": len(ids)})

    exact_title = collections.defaultdict(list)
    for a in activities:
        key = (a["normalized_title"] or "").strip().lower()
        if key:
            exact_title[key].append(a)
    exact_title_groups = [
        [a["id"] for a in group] for group in exact_title.values() if len(group) > 1
    ]

    fuzzy_groups = fuzzy_title_groups(activities)

    strong = []
    for group in exact_title_groups:
        strong.append([activity_summary(a) for a in activities if a["id"] in group])
    for du in url_dups:
        strong_group = [a for a in activities if a["id"] in du["activity_ids"]]
        strong.append([activity_summary(a) for a in strong_group])

    return {
        "exact_source_url_groups": url_dups,
        "exact_normalized_title_groups": exact_title_groups,
        "exact_normalized_title_count": sum(len(g) for g in exact_title_groups),
        "fuzzy_likely_groups": fuzzy_groups["likely"],
        "fuzzy_possible_groups": fuzzy_groups["possible"],
        "fuzzy_likely_count": sum(len(g) for g in fuzzy_groups["likely"]),
        "fuzzy_possible_count": sum(len(g) for g in fuzzy_groups["possible"]),
        "strong_duplicate_groups": strong,
        "existing_duplicate_candidates_rows": None,  # filled later from existing_flags
    }


def activity_summary(a):
    return {
        "id": a["id"], "title": a["title"], "period": a["period"],
        "department": a["dept"], "codes": sorted(a.get("codes", ())),
        "source_url": a["source_url"],
    }


def fuzzy_title_groups(activities):
    if not RAPIDFUZZ:
        return {"likely": [], "possible": []}
    by_period = collections.defaultdict(list)
    for a in activities:
        key = (a["normalized_title"] or "").strip().lower()
        if key:
            by_period[a["period"]].append(a)

    prep = re.compile(r"[^a-z0-9]+")

    def sig(a):
        toks = [t for t in prep.sub(" ", (a["normalized_title"] or "").lower()).split() if len(t) > 2]
        return sorted(set(toks))[:3]

    likely, possible = [], []
    seen = set()
    for period, group in by_period.items():
        buckets = collections.defaultdict(list)
        for a in group:
            buckets[tuple(sig(a))].append(a)
        for bucket in buckets.values():
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    ai, aj = bucket[i], bucket[j]
                    pair = tuple(sorted((ai["id"], aj["id"])))
                    if pair in seen:
                        continue
                    ratio = fuzz.token_sort_ratio(
                        ai["title"] or "", aj["title"] or "")
                    if ratio >= 97:
                        seen.add(pair)
                        likely.append({"a": ai["id"], "b": aj["id"], "ratio": round(ratio, 1)})
                    elif ratio >= 93:
                        seen.add(pair)
                        possible.append({"a": ai["id"], "b": aj["id"], "ratio": round(ratio, 1)})
    likely = dedupe_pair_groups(likely, activities)
    possible = dedupe_pair_groups(possible, activities)
    return {"likely": likely, "possible": possible}


def dedupe_pair_groups(pairs, activities):
    """Keep only pairs that are not already covered by an exact match."""
    by_id = {a["id"]: a for a in activities}
    groups = []
    used = set()
    for entry in pairs:
        ids = (entry["a"], entry["b"])
        if ids[0] in used or ids[1] in used:
            continue
        used.update(ids)
        groups.append({
            "ids": list(ids),
            "ratio": entry["ratio"],
            "titles": [by_id[i]["title"] for i in ids],
            "periods": [by_id[i]["period"] for i in ids],
        })
    return groups[:60]


def non_activity_audit(activities, links, conn):
    boilerplate = re.compile(
        r"^\s*(events?\s*(\||-|–|:)|menu|home\s*\|?|about\s*(\||$)|contact(\s*(\||$))"
        r"|academics(\s*(\||$))|admission|\s*\|\s*tce\s*$|page not found|404|"
        r"campus\s*life|student life|quick links|site map|search results|coming soon)",
        re.I,
    )
    cand_by_activity = reverse_links(links)
    quality = {}
    for r in q(conn, """SELECT candidate_id, quality_status, quality_reason FROM candidate_quality_reviews"""):
        quality[r["candidate_id"]] = dict(r)

    flagged = []
    for a in activities:
        title = (a["title"] or "").strip()
        desc = (a["description"] or "").strip()
        reasons = []
        if boilerplate.match(title):
            reasons.append("boilerplate/navigation-style title")
        if not desc and not (a["evidence_text"] or "").strip():
            reasons.append("no description and no evidence text")
        if reasons:
            flagged.append({"id": a["id"], "title": title, "reasons": reasons})

    non_activity_candidates = []
    for aid, cand_ids in cand_by_activity.items():
        for cid in cand_ids:
            row = quality.get(cid)
            if row and row.get("quality_status") == "NON_ACTIVITY":
                non_activity_candidates.append({"activity_id": aid, "reason": row.get("quality_reason")})

    return {
        "flag_heuristic_non_activity": flagged,
        "flag_heuristic_non_activity_count": len(flagged),
        "example_flagged": flagged[:10],
        "candidate_quality_reviewed_non_activity": non_activity_candidates,
        "candidate_quality_reviewed_non_activity_count": len(non_activity_candidates),
        "note": "Heuristic flags are advisory only; nothing is deleted or reclassified.",
    }


def reverse_links(links):
    out = collections.defaultdict(list)
    for aid, cids in links.items():
        out[aid].extend(cids)
    return out


def source_audit(activities, sources, conn):
    with_sources = 0
    seen_urls = set()
    by_reg_type = collections.Counter()
    no_trace = set()
    for a in activities:
        rows = sources.get(a["id"], [])
        if rows:
            with_sources += 1
            for row in rows:
                if row["source_url"]:
                    seen_urls.add(_norm_url(row["source_url"]))
                if row["reg_type"]:
                    by_reg_type[row["reg_type"]] += 1
        elif not a["source_url"]:
            no_trace.add(a["id"])
    reg_counts = q(conn, """SELECT name, url, source_type, active FROM source_registry""")
    return {
        "activities_with_activity_sources": with_sources,
        "activities_with_primary_source_url": sum(1 for a in activities if a["source_url"]),
        "activities_with_no_traceable_source": len(no_trace),
        "distinct_source_urls": len(seen_urls),
        "source_registry": [dict(r) for r in reg_counts],
        "source_type_distribution": dict(sorted(by_reg_type.items(), key=lambda kv: -kv[1])),
        "example_no_trace": [
            {"id": a["id"], "title": a["title"]}
            for a in activities if a["id"] in no_trace
        ][:5],
    }


def _parse_date(value):
    if not value:
        return None, None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(text, fmt).date(), text
        except ValueError:
            continue
    m = re.match(r"^(\d{4})-(\d{2})", text)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), 1), text
        except ValueError:
            return None, text
    return None, text


def date_audit(activities):
    invalid = []
    future = []
    inconsistent = []
    only_year = []
    multiple_dates = []
    for a in activities:
        d, raw = _parse_date(a["activity_date"])
        if a["activity_date"] and d is None:
            invalid.append(a)
        if d and d > TODAY:
            future.append(a)
        if d:
            implied = resolve_period(a["stored_year"], d.isoformat(), None, None)
            if a["stored_year"] in PUBLIC_PERIODS and implied != a["stored_year"]:
                inconsistent.append(a)
        if d is None and year_token(a["activity_date_text"]) and not year_token(a["evidence_text"]):
            only_year.append(a)
        text_dates = set(YEAR_TOKEN.findall(a["activity_date_text"] or ""))
        text_dates |= set(YEAR_TOKEN.findall(a["evidence_text"] or ""))
        if len(text_dates) > 1:
            multiple_dates.append(a)
    return {
        "invalid_structured_date": len(invalid),
        "future_date": len(future),
        "structured_date_inconsistent_with_stored_year": len(inconsistent),
        "only_year_in_text_no_structured_date": len(only_year),
        "multiple_years_mentioned_in_source_text": len(multiple_dates),
        "date_range": {
            "min": min((_parse_date(a["activity_date"])[0] for a in activities if _parse_date(a["activity_date"])[0]), default=None),
            "max": max((_parse_date(a["activity_date"])[0] for a in activities if _parse_date(a["activity_date"])[0]), default=None),
        },
        "example_future": sample_titles(future, 3),
        "example_inconsistent": [
            {"id": a["id"], "title": a["title"], "date": a["activity_date"],
             "stored": a["stored_year"], "resolved": a["period"]} for a in inconsistent[:5]
        ],
        "example_invalid": sample_titles(invalid, 3),
    }


def description_audit(activities):
    empty = [a for a in activities if not (a["description"] or "").strip()]
    short = [a for a in activities
             if 0 < len((a["description"] or "").strip()) < 20]
    title_repeated = []
    for a in activities:
        desc = (a["description"] or "").strip().lower()
        title = (a["title"] or "").strip().lower()
        if desc and title and (desc == title or (len(desc) <= len(title) and desc in title)):
            title_repeated.append(a)
    with_outcome = [a for a in activities if (a["achievement_outcome"] or "").strip()]
    with_venue = [a for a in activities if (a["venue"] or "").strip()]
    with_organizer = [a for a in activities if (a["organizer"] or "").strip()]
    with_resource = [a for a in activities if (a["resource_person"] or "").strip()]
    return {
        "empty": len(empty),
        "short_lt_20_chars": len(short),
        "description_equals_title": len(title_repeated),
        "example_empty": sample_titles(empty, 5),
        "example_short": [{"id": a["id"], "title": a["title"], "description": a["description"]} for a in short[:5]],
        "example_title_repeated": sample_titles(title_repeated, 5),
        "with_achievement_outcome": len(with_outcome),
        "with_venue": len(with_venue),
        "with_organizer": len(with_organizer),
        "with_resource_person": len(with_resource),
    }


def coverage(activities, cat_codes):
    total = {period: 0 for period in PUBLIC_PERIOD_OPTIONS}
    cats = {period: set() for period in PUBLIC_PERIOD_OPTIONS}
    depts = {period: set() for period in PUBLIC_PERIOD_OPTIONS}
    stakes = {period: set() for period in PUBLIC_PERIOD_OPTIONS}
    matrix = collections.defaultdict(lambda: collections.Counter())
    for a in activities:
        p = a["period"]
        total[p] += 1
        cats[p].update(cat_codes[a["id"]] & PUBLIC_CATEGORY_CODES)
        if a["dept"] != GENERAL_NAME:
            depts[p].update(a["dept"].split("; "))
        if (a["stakeholder_display"] or "").strip():
            stakes[p].update((a["stakeholder_display"] or "").split("; "))
        for code in cat_codes[a["id"]] & PUBLIC_CATEGORY_CODES:
            matrix[code][p] += 1
    rows = []
    for p in PUBLIC_PERIOD_OPTIONS:
        rows.append({
            "academic_year": p, "activities": total[p],
            "categories": len(cats[p]), "departments": len(depts[p]),
            "stakeholders": len(stakes[p]),
        })
    category_rows = {
        code: {p: matrix[code].get(p, 0) for p in PUBLIC_PERIOD_OPTIONS}
        for code in sorted(PUBLIC_CATEGORY_CODES)
    }
    return {"five_year": rows, "category_by_year": category_rows}


def sanity_checks(activities, cat_codes):
    workshop_all = sum(1 for a in activities if "WORKSHOP" in cat_codes[a["id"]])
    general = sum(1 for a in activities if a["dept"] == GENERAL_NAME)
    ws_2025 = sum(1 for a in activities
                  if a["period"] == "2025-26" and "WORKSHOP" in cat_codes[a["id"]])
    it_ach_2025 = sum(1 for a in activities
                      if a["period"] == "2025-26" and a["dept"] != GENERAL_NAME
                      and "Information Technology" in a["dept"].split("; ")
                      and "ACHIEVEMENT" in cat_codes[a["id"]])
    tseda_2024 = sum(1 for a in activities
                     if a["period"] == "2024-25"
                     and "T'SEDA (Architecture, Design, Planning)" in a["dept"].split("; "))
    return {
        "WORKSHOP_total": workshop_all,
        "General_normalized_total": general,
        "2025-26_Workshops": ws_2025,
        "2025-26_IT_Achievements": it_ach_2025,
        "2024-25_T'SEDA": tseda_2024,
        "expected": {  # user's Phase-3 sanity constants
            "WORKSHOP_all_scope": 97, "General_institution_wide": 813,
            "2025-26_Workshops_all_scope": 10, "2025-26_IT_Achievements": 50,
            "2024-25_T'SEDA": 47,
        },
    }


def existing_flags(conn):
    review = q(conn, """SELECT activity_id, reason, status FROM review_queue""")
    recovery = q(
        conn,
        """SELECT recovery_method, COUNT(*) c FROM period_recovery_audit
           GROUP BY recovery_method ORDER BY c DESC""",
    )
    return {
        "open_review_flags": [dict(r) for r in review],
        "period_recovery_breakdown": [dict(r) for r in recovery],
        "period_recovery_total": q(conn, "SELECT COUNT(*) c FROM period_recovery_audit")[0]["c"],
    }


def render_markdown(audit):
    L = []
    L.append("# Existing Data Audit — TCE Activity Intelligence (read-only)")
    L.append("")
    L.append(f"Generated: {audit['timestamp']}")
    L.append("")
    o = audit["overall"]
    L.append("## 1. Overall")
    L.append("")
    for key, label in [
        ("total_records", "Total activity records"),
        ("has_structured_date", "With structured date"),
        ("missing_date", "Missing date"),
        ("has_public_category", "With public category"),
        ("missing_public_category", "Missing public category"),
        ("missing_any_category", "Missing any category (no category rows)"),
        ("missing_department_field", "Missing department field"),
        ("missing_stakeholder_field", "Missing stakeholder field"),
        ("missing_source", "Missing source"),
        ("weak_or_empty_description", "Weak/empty descriptions (<20 chars)"),
    ]:
        L.append(f"- {label}: **{o.get(key)}**")
    L.append("")

    L.append("## 2. Academic-period audit (read-time resolution)")
    L.append("")
    L.append("| Period | Activities |")
    L.append("| ------ | ----------:|")
    for p, c in audit["period_audit"]["resolved"].items():
        L.append(f"| {p} | {c} |")
    L.append("")
    L.append(f"- Records presented as `Before 2021` with **no** date and **no** year evidence: "
             f"`{audit['period_audit']['presented_as_before_2021_with_no_date_or_year_evidence']}`")
    L.append(f"- Stored `academic_year` missing: `{audit['period_audit']['stored_year_missing']}`")
    L.append(f"- Stored year outside the five public periods: `{audit['period_audit']['records_outside_intended_period']}`")
    L.append("")

    ca = audit["category_audit"]
    L.append("## 3. Category audit")
    L.append("")
    L.append("### Public category counts (all scopes)")
    L.append("")
    L.append("| Code | Public name | Activities |")
    L.append("| ---- | ----------- | ----------:|")
    for code, count in ca["public_category_counts"].items():
        L.append(f"| {code} | {CATEGORY_PUBLIC_NAMES.get(code, code)} | {count} |")
    L.append("")
    L.append(f"- Legacy/non-public codes still stored: `{ca['legacy_non_public_codes']}`")
    L.append(f"- General-scope (institution-wide) activities: `{ca['general_scope_activities']}`")
    L.append("")
    L.append("### General (institution-wide) category distribution")
    L.append("")
    for code, count in ca["general_scope_category_counts"].items():
        L.append(f"- {CATEGORY_PUBLIC_NAMES.get(code, code)}: {count}")
    L.append("")

    gb = audit["general_breakdown"]
    L.append("### General bucket analysis (advisory — why General is so large)")
    L.append("")
    for bucket, count in gb["bucket_counts"].items():
        L.append(f"- **{bucket}**: {count}")
        for ex in gb["bucket_examples"].get(bucket, []):
            L.append(f"  - #{ex['id']} `{ex['title']}`")
    L.append("")
    L.append(f"> {gb['note']}")
    L.append("")

    cta = audit["category_text_advisory"]
    L.append("### Category vs text inconsistency (advisory)")
    L.append("")
    L.append(f"- Records whose text suggests a different specific category than stored: "
             f"**{cta['advisory_flagged']}**")
    for ex in cta["examples"][:15]:
        L.append(f"  - #{ex['id']} `{ex['title'][:60]}` stored={ex['stored']} "
                 f"text-suggests={ex['suggested_by_text']}")
    L.append("")
    L.append(f"> {cta['note']}")
    L.append("")

    da = audit["department_audit"]
    L.append("## 4. Department audit")
    L.append("")
    L.append(f"- Institution-wide (General): **{da['general_institution_wide']}**")
    L.append("")
    L.append("| Department | Activities |")
    L.append("| ---------- | ----------:|")
    for dept, count in da["public_departments"].items():
        L.append(f"| {dept} | {count} |")
    L.append("")
    L.append(f"- Multi-department records: **{da['multi_department_records']}** (counted in every applicable department; never duplicated)")
    for ex in da["multi_department_examples"]:
        L.append(f"  - #{ex['id']} `{ex['title'][:80]}` → {ex['departments']}")
    L.append("")
    if da["out_of_master_values"]:
        L.append(f"- Values outside the 17-department master (kept, not relabelled): `{da['out_of_master_values']}`")
        L.append("")

    sa = audit["stakeholder_audit"]
    L.append("## 5. Stakeholder audit")
    L.append("")
    L.append("| Stakeholder | Activities |")
    L.append("| ------------ | ----------:|")
    for k, v in sa["counts"].items():
        L.append(f"| {k} | {v} |")
    L.append("")
    if sa["values_outside_supported_set"]:
        L.append(f"- Outside the supported set (incl. missing): `{sa['values_outside_supported_set']}`")
        L.append("")

    dup = audit["duplicate_audit"]
    L.append("## 6. Duplicate audit")
    L.append("")
    L.append(f"- Exact source-URL groups: **{len(dup['exact_source_url_groups'])}**")
    for g in dup["exact_source_url_groups"]:
        L.append(f"  - `{g['url']}` → ids {g['activity_ids']}")
    L.append(f"- Exact normalized-title groups: **{len(dup['exact_normalized_title_groups'])}** "
             f"(activities involved: {dup['exact_normalized_title_count']})")
    L.append(f"- Fuzzy LIKELY groups (token-sort ratio ≥97, same period): **{dup['fuzzy_likely_count']}**")
    for g in dup["fuzzy_likely_groups"]:
        L.append(f"  - {g['ratio']}: ids {g['ids']} `{g['titles'][0][:60]}` | `{g['titles'][1][:60]}`")
    L.append(f"- Fuzzy POSSIBLE groups (ratio ≥93): **{dup['fuzzy_possible_count']}**")
    L.append("")

    na = audit["non_activity_audit"]
    L.append("## 7. Non-activity audit (advisory)")
    L.append("")
    L.append(f"- Heuristic flags: **{na['flag_heuristic_non_activity_count']}**")
    if na["example_flagged"]:
        L.append("Examples:")
        for f in na["example_flagged"][:8]:
            L.append(f"  - #{f['id']} `{f['title'][:70]}` — {', '.join(f['reasons'])}")
    L.append("")
    L.append(f"- Candidate quality reviews marked NON_ACTIVITY: **{na['candidate_quality_reviewed_non_activity_count']}**")
    L.append("")

    src = audit["source_audit"]
    L.append("## 8. Source / provenance audit")
    L.append("")
    L.append(f"- Activities with `activity_sources` rows: **{src['activities_with_activity_sources']}**")
    L.append(f"- Activities with a primary `source_url`: **{src['activities_with_primary_source_url']}**")
    L.append(f"- Activities with **no traceable source**: **{src['activities_with_no_traceable_source']}**")
    L.append(f"- Distinct source URLs: **{src['distinct_source_urls']}**")
    L.append("")
    L.append("| Source registry | Type | Active | URL |")
    L.append("| --------------- | ---- | ------ | --- |")
    for r in src["source_registry"]:
        L.append(f"| {r['name']} | {r['source_type']} | {r['active']} | {r['url']} |")
    L.append("")

    da_ = audit["date_audit"]
    L.append("## 9. Date audit")
    L.append("")
    for key, label in [
        ("invalid_structured_date", "Invalid structured date"),
        ("future_date", "Future date"),
        ("structured_date_inconsistent_with_stored_year", "Date inconsistent with stored academic year"),
        ("only_year_in_text_no_structured_date", "Only year available in source text"),
        ("multiple_years_mentioned_in_source_text", "Multiple years mentioned in source text"),
    ]:
        L.append(f"- {label}: **{da_.get(key)}**")
    L.append(f"- Date range: `{da_['date_range']}`")
    L.append("")

    desc = audit["description_audit"]
    L.append("## 10. Description-quality audit")
    L.append("")
    L.append(f"- Empty descriptions: **{desc['empty']}**")
    L.append(f"- Short (<20 chars): **{desc['short_lt_20_chars']}**")
    L.append(f"- Description equals title: **{desc['description_equals_title']}**")
    L.append(f"- Rich fields: outcome {desc['with_achievement_outcome']}, venue {desc['with_venue']}, "
             f"organizer {desc['with_organizer']}, resource person {desc['with_resource_person']}")
    L.append("")

    cov = audit["coverage"]
    L.append("## 11. Five-year coverage")
    L.append("")
    L.append("| Academic Year | Activities | Categories | Departments | Stakeholders |")
    L.append("| ------------- | ----------:| ----------:| -----------:| ------------:|")
    for row in cov["five_year"]:
        L.append(f"| {row['academic_year']} | {row['activities']} | {row['categories']} | {row['departments']} | {row['stakeholders']} |")
    L.append("")
    L.append("### Category × academic year (resolved periods)")
    L.append("")
    L.append("| Category | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | Before 2021 |")
    L.append("|----------|-------:|-------:|-------:|-------:|-------:|-----------:|")
    for code, row in cov["category_by_year"].items():
        name = CATEGORY_PUBLIC_NAMES.get(code, code)
        L.append(f"| {name} | {row.get('2021-22',0)} | {row.get('2022-23',0)} | {row.get('2023-24',0)} | {row.get('2024-25',0)} | {row.get('2025-26',0)} | {row.get('Before 2021',0)} |")
    L.append("")

    san = audit["sanity"]
    L.append("## 12. Sanity checks (live DB)")
    L.append("")
    L.append("| Check | Live DB | Expected (user constants) |")
    L.append("| ----- | ------: | -------------------------: |")
    L.append(f"| WORKSHOP (all scopes) | {san['WORKSHOP_total']} | {san['expected']['WORKSHOP_all_scope']} |")
    L.append(f"| General (institution-wide) | {san['General_normalized_total']} | {san['expected']['General_institution_wide']} |")
    L.append(f"| 2025-26 Workshops (all scopes) | {san['2025-26_Workshops']} | {san['expected']['2025-26_Workshops_all_scope']} |")
    L.append(f"| 2025-26 IT Achievements | {san['2025-26_IT_Achievements']} | {san['expected']['2025-26_IT_Achievements']} |")
    tseda = san["2024-25_T'SEDA"]
    tseda_exp = san['expected']["2024-25_T'SEDA"]
    L.append(f"| 2024-25 T'SEDA | {tseda} | {tseda_exp} |")
    L.append("")

    flags = audit["existing_flags"]
    L.append("## 13. Existing internal flags")
    L.append("")
    L.append(f"- Open review-queue flags: `{len(flags['open_review_flags'])}`")
    for r in flags["open_review_flags"][:12]:
        L.append(f"  - activity #{r['activity_id']} — {r['reason']}")
    L.append(f"- Period-recovery audit rows: `{flags['period_recovery_total']}` "
             f"({flags['period_recovery_breakdown']})")
    L.append("")

    return "\n".join(L)


if __name__ == "__main__":
    main()