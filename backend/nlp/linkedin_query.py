"""Natural-language query engine for the LinkedIn REPORTABLE dataset.

The public reportable pipeline (STEP 9) is served here with the SAME public
HTTP response shape as the website ``/api/query`` endpoint so the Ask-the-Data
frontend needs a single renderer.  Every grounding and every aggregation goes
through ``linkedin_reportable`` helpers (``filters_fragment``,
``count_reportable``, ``analytics_*``), so NLQ counts always reconcile with the
Dashboard / Activities / Reports pages (one unique REPORTABLE activity = one
total; occurrence counts per category/department/stakeholder).

Nothing in this module touches the website database, the staging database or
the workbook.
"""

import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.linkedin_reportable import (
    CATEGORY_CANDIDATE_NAMES,
    REPORTABLE,
    _row_to_record,
    analytics_categories,
    analytics_departments,
    analytics_stakeholders,
    analytics_yearly,
    count_reportable,
    filters_fragment,
    get_reportable_connection,
)
from backend.nlp.query_executor import (
    OUT_OF_SCOPE_MESSAGE,
    STATUS_ANSWER,
    STATUS_UNSUPPORTED,
    STATUS_ZERO,
    ZERO_MESSAGE,
)

SCOPE_MESSAGE = (
    "I can answer questions about the TCE LinkedIn activity data: how many "
    "activities, workshops, seminars, technical festivals, FDPs, placements, "
    "sports, guest lectures and more, by academic year, category, department, "
    "or stakeholder. For example: 'How many workshops in 2025-26?', 'Which "
    "department had the most activities in 2024-25?' or 'Sports activities'."
)

LIST_LIMIT = 20

# ---------------------------------------------------------------------------
# Grounding vocabularies (all read from the reportable data, never hard-coded
# counts).  Keywords are only used to recognise intent; the VALUES come from
# availability/analytics at runtime.
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "ACHIEVEMENT": ["achievement", "award", "awards", "medals", "winner", "winners",
                    "recognised", "recognized"],
    "RESEARCH": ["research", "consultancy", "paper", "papers", "publication",
                 "publications", "patent", "projects"],
    "INDUSTRY": ["mou", "moa", "industrial visit", "industry visit", "collaboration"],
    "CLUB": ["clubs", "chapter", "chapters", "rotaract", "professional society"],
    "OUTREACH": ["outreach", "extension", "blood donation", "swachh", "community service"],
    "WORKSHOP": ["workshop", "workshops"],
    "CONFERENCE": ["conference", "conferences"],
    "SEMINAR": ["seminar", "seminars"],
    "GUEST_LECTURE": ["guest lecture", "guest talk", "special lecture", "invited talk",
                      "expert lecture", "expert talk", "guest lectures"],
    "FDP": ["fdp", "faculty development"],
    "HACKATHON": ["hackathon", "hack-a-thon", "hack day"],
    "CULTURAL": ["cultural", "annual day", "talent show", "dance", "music",
                 "singing", "elocution", "declamation"],
    "SPORTS": ["sports", "sport", "games", "athletics", "futsal", "sports meet",
               "cricket"],
    "NCC": ["ncc", "national cadet corps", "cadet"],
    "NSS": ["nss", "national service scheme"],
    "PLACEMENT": ["placement", "placements", "recruitment drive", "campus interview",
                  "hiring"],
    "INTERNSHIP": ["internship", "internships", "intern"],
    "ORIENTATION": ["orientation", "induction programme", "welcome"],
    "CAMPUS": ["campus tour", "campus life"],
    "WEBINAR": ["webinar", "webinars"],
    "ALUMNI": ["alumni", "alumni meet", "alumnus"],
    "SYMPOSIUM": ["symposium", "symposia"],
    "STTP": ["sttp", "short term training", "student training programme",
             "training programme"],
    "TECH_FEST": ["tech fest", "technical festival", "techfest", "technofest"],
}

DEPARTMENT_KEYWORDS = {
    "General": ["institution-wide", "institute wide", "college wide",
                "across the college", "institute level", "general"],
}
# Specific department names are matched by their availability() names directly.
# Aliases map a user's natural phrasing to the canonical public department name.
DEPARTMENT_ALIASES = {
    "mca": "Computer Applications",
    "department of computer applications": "Computer Applications",
    "dept of computer applications": "Computer Applications",
    "computer applications dept": "Computer Applications",
    "mca department": "Computer Applications",
    "applied mathematics and computational science": None,  # canonical name handled below
}
# Explicit short aliases resolved to canonical department names.
DEPARTMENT_SHORT_ALIASES = {
    "mca": "Computer Applications",
    "computer applications": "Computer Applications",
}

_GENERAL_SCOPE_PATTERNS = (
    r"\bgeneral\s+activit",
    r"\bgeneral\s+achiev",
    r"\binstitution[- ]wide\b",
    r"\bcollege[- ]wide\b",
    r"\binstitute[- ]level\b",
)
_DEPARTMENTAL_SCOPE_PATTERNS = (
    r"\bdepart?mental\b",
    r"\bdepartment\s+(?:activit|reports?)\b",
)

YEAR_WISE_RE = re.compile(
    r"(?:year[- ]?wise|yearly|by\s+year|by\s+years|by\s+academic\s+year|"
    r"by\s+academic\s+years|across\s+year|across\s+years|"
    r"across\s+academic\s+year|across\s+academic\s+years|"
    r"per\s+year|per\s+years|each\s+year|every\s+year|year\s*[-–]?\s*by\s*[-–]?\s*year)")
RATE_RE = re.compile(r"\brate(?:s|d)?\b")
UNDATED_RE = re.compile(
    r"\bundated\b|\bwithout\s+(?:a\s+)?(?:reliable\s+)?date\b|\bno\s+(?:reliable\s+)?date\b|"
    r"\bmissing\s+(?:a\s+)?date\b|\b(?:records?|activities?)\s+without\s+dates?\b")

STAKEHOLDER_KEYWORDS = {
    "Students": ["student", "students"],
    "Faculty": ["faculty"],
    "Non-Teaching Staff": ["non-teaching", "non teaching", "support staff"],
    "Alumni": ["alumni", "alumnus"],
    "Institution": ["industry", "companies", "employers"],
    "Parents": ["parent", "parents"],
    "Government and Agencies": ["government", "agencies", "agencies"],
    "Community and Society": ["community", "society", "public"],
}

YEAR_RE = re.compile(
    r"(?:academic\s+years?\s*)?(\d{4})\s*[-–]\s*(\d{2}|\d{4})\b(?!-\d)")
YEAR_TO_RE = re.compile(
    r"(?:academic\s+years?\s*)?(\d{4})\s+(?:to|and|through(?:out)?)\s+(\d{2}|\d{4})\b")
SINGLE_YEAR_RE = re.compile(r"\b(\d{4})\b")

# Preferred ordering when several category keywords match (most specific first).
_CATEGORY_PRIORITY = [
    "GUEST_LECTURE", "HACKATHON", "TECH_FEST", "STTP", "SYMPOSIUM", "FDP",
    "CONFERENCE", "SEMINAR", "WEBINAR", "WORKSHOP", "PLACEMENT", "INTERNSHIP",
    "ORIENTATION", "NCC", "NSS", "CLUB", "OUTREACH", "CULTURAL", "SPORTS",
    "ACHIEVEMENT", "RESEARCH", "INDUSTRY", "CAMPUS", "ALUMNI",
]


def _contains_any(text, keywords):
    for kw in keywords:
        if kw in text:
            return True
    return False


def _ground_category(question, available):
    """Return (code or None, name or None) for the category the question refers to."""
    lowered = question.lower()
    hits = {}
    for code, keywords in CATEGORY_KEYWORDS.items():
        if _contains_any(lowered, keywords):
            for kw in keywords:
                if kw in lowered:
                    hits[code] = hits.get(code, 0) + len(kw.split())
    if not hits:
        # fall back to the available display names (word-boundary match)
        for item in available:
            name = (item.get("name") or "").lower()
            if name and len(name) > 3 and (" " + name + " ") in (" " + lowered + " "):
                hits[item["code"]] = 1
    if not hits:
        return None, None
    code = sorted(hits, key=lambda c: (-hits[c], _CATEGORY_PRIORITY.index(c) if c in _CATEGORY_PRIORITY else 99))[0]
    name = None
    for item in available:
        if item["code"] == code:
            name = item["name"]
            break
    if not name:
        name = CATEGORY_CANDIDATE_NAMES.get(code, code)
    return code, name


def _ground_department(question, available):
    """Return (public department name or None) at word boundaries."""
    lowered = question.lower()
    for banner, keywords in DEPARTMENT_KEYWORDS.items():
        if _contains_any(lowered, keywords):
            return banner

    # Explicit short aliases (e.g. MCA -> Computer Applications) first.
    for phrase, canonical in DEPARTMENT_SHORT_ALIASES.items():
        if re.search(r"\b%s\b" % re.escape(phrase), lowered) and canonical in available:
            return canonical

    for name in available:
        if not name:
            continue
        low = name.lower()
        if low in ("general",):
            continue
        if len(low) > 3 and (" " + low + " ") in (" " + lowered + " "):
            return name
    return None


def _ground_scope(question):
    """Recognise general (institution-wide) vs departmental scope."""
    lowered = question.lower()
    if any(re.search(p, lowered) for p in _GENERAL_SCOPE_PATTERNS):
        return "general"
    if any(re.search(p, lowered) for p in _DEPARTMENTAL_SCOPE_PATTERNS):
        return "departmental"
    return None


def _ground_stakeholder(question):
    lowered = question.lower()
    hits = {}
    for name, keywords in STAKEHOLDER_KEYWORDS.items():
        if _contains_any(lowered, keywords):
            hits[name] = hits.get(name, 0) + 1
    if not hits:
        return None
    return sorted(hits, key=lambda n: -hits[n])[0]


def _normalise_year(question, available_years):
    """Return (available academic year or None, raw year text or None).

    When a raw year is recognised but not present in the reportable data the
    raw value is returned so the answer can say so honestly instead of
    fabricating a bucket.
    """
    m = YEAR_TO_RE.search(question)
    if m:
        start = int(m.group(1))
        end = int(m.group(2))
        candidate = "%d-%02d" % (start, (end % 100))
        if candidate in available_years:
            return candidate, None
        return None, "%d-%02d" % (start, (end % 100))
    m = YEAR_RE.search(question)
    if not m:
        m = SINGLE_YEAR_RE.search(question)
        if not m:
            return None, None
        start = int(m.group(1))
        year = "%d-%02d" % (start, (start + 1) % 100)
    else:
        start = int(m.group(1))
        end = int(m.group(2))
        year = "%d-%02d" % (start, (end % 100))
    if year in available_years:
        return year, None
    return None, year


def _criteria(used):
    labels = []
    if used.get("scope"):
        labels.append("Scope: %s activities" % ("General" if used["scope"] == "general" else "Departmental"))
    if used.get("year"):
        labels.append("Academic year: %s" % used["year"])
    if used.get("category_label"):
        labels.append("Category: %s" % used["category_label"])
    elif used.get("category"):
        labels.append("Category: %s" % used["category"])
    if used.get("department"):
        labels.append("Department: %s" % used["department"])
    if used.get("stakeholder"):
        labels.append("Stakeholder: %s" % used["stakeholder"])
    if used.get("date_status") == "undated":
        labels.append("Date status: undated (no reliable date in the post)")
    return labels


def _describe(used):
    """Short human description of the active filters for NLQ answer text."""
    parts = []
    if used.get("category_label"):
        parts.append(used["category_label"])
    elif used.get("category"):
        parts.append(used["category"])
    if used.get("scope") == "general":
        parts.append("General (institution-wide)")
    elif used.get("scope") == "departmental":
        parts.append("Departmental")
    if used.get("department") and used.get("scope") != "general" or (
            used.get("department") and used.get("department") != "General"):
        parts.append("for %s" % used["department"])
    if used.get("stakeholder"):
        parts.append("involving %s" % used["stakeholder"])
    if used.get("year"):
        parts.append("during %s" % used["year"])
    if used.get("date_status") == "undated":
        parts.append("for which no reliable date is known")
    return " ".join(parts).strip()


def _active_filters(used):
    args = {"status": REPORTABLE}
    for key in ("year", "category", "department", "stakeholder"):
        if used.get(key):
            args[key] = used[key]
    if used.get("scope"):
        args["scope"] = used["scope"]
    if used.get("date_status"):
        args["date_status"] = used["date_status"]
    return args


def _fetch_rows(conn, args, limit=LIST_LIMIT):
    where, params = filters_fragment(args)
    rows = conn.execute(
        "SELECT * FROM linkedin_reportable_activities r" + where +
        " ORDER BY r.activity_date DESC NULLS LAST, r.activity_id DESC LIMIT ?",
        params + [limit],
    ).fetchall()
    return [_row_to_record(r) for r in rows]


def _grouped_counts(conn, args, dimension):
    fn = {"department": analytics_departments,
          "category": analytics_categories,
          "stakeholder": analytics_stakeholders,
          "year": analytics_yearly}[dimension]
    return fn(conn, args)


def _rows_and_chart(rows, label_key):
    chart_rows = [{"label": row[label_key], "value": row["activity_count"]}
                  for row in rows if row.get("activity_count", 0) > 0]
    return chart_rows, {"data": [{"label": r["label"], "value": r["value"]} for r in chart_rows]}


# ---------------------------------------------------------------------------
# Intent handlers
# ---------------------------------------------------------------------------
def _blocked_year(used):
    """True when the question named an academic year with no available records."""
    return bool(used.get("year_unavailable"))


def _answer_count(question, conn, used, note):
    if _blocked_year(used):
        return {"status": STATUS_ANSWER, "answer": (
            "0 matching activities: %s." % (note or "").strip()),
            "count": 0, "activities": []}
    args = _active_filters(used)
    count = count_reportable(conn, args)
    noun = "activity" if count == 1 else "activities"
    describe = _describe(used)
    if count == 0:
        body = ("No %s activities were found for the selected combination of "
                "filters (based on the available TCE LinkedIn posts)."
                % (describe or "matching"))
        return {"status": STATUS_ZERO, "answer": body,
                "count": 0, "activities": []}
    sentence = ("%d %s %s." % (count, noun, describe)) if describe else \
        ("%d matching %s found." % (count, noun))
    return {"status": STATUS_ANSWER, "answer": sentence,
            "count": count, "activities": _fetch_rows(conn, args)}


def _answer_list(question, conn, used, note):
    if _blocked_year(used):
        return {"status": STATUS_ZERO, "answer": ZERO_MESSAGE,
                "count": 0, "activities": []}
    args = _active_filters(used)
    count = count_reportable(conn, args)
    items = _fetch_rows(conn, args)
    if count == 0:
        describe = _describe(used)
        body = ("No matching records found for %s. Based on the available TCE "
                "LinkedIn posts, no activities exist for that exact "
                "combination." % (describe or "the selected criteria"))
        return {"status": STATUS_ZERO, "answer": body,
                "count": 0, "activities": []}
    first = items[0] if len(items) == 1 else None
    shown = " up to %d shown" % LIST_LIMIT if count > len(items) else ""
    describe = _describe(used)
    if describe:
        answer = "%d %s%s (based on available TCE LinkedIn posts)." % (
            count, describe, shown)
    else:
        noun = "activity" if count == 1 else "activities"
        answer = "Found %d matching %s%s (based on available TCE LinkedIn posts)." % (count, noun, shown)
    return {
        "status": STATUS_ANSWER,
        "answer": answer,
        "count": count,
        "activities": items,
        "detail": first,
    }


def _answer_ranking(question, conn, used, note, superlative):
    if _blocked_year(used):
        return {"question": question, "status": STATUS_ZERO,
                "answer": ZERO_MESSAGE, "count": 0, "activities": [],
                "criteria": _criteria(used)}
    dimension = used.get("group_by") or "department"
    axis = {"year": "academic year", "department": "department",
            "category": "category", "stakeholder": "stakeholder"}[dimension]
    args = _active_filters(used)
    rows = _grouped_counts(conn, args, dimension)
    active = [r for r in rows if r.get("activity_count", 0) > 0]
    base = {"question": question, "status": STATUS_ANSWER,
            "criteria": _criteria(used)}
    total = count_reportable(conn, args)
    if not active and total == 0:
        return {**base, "status": STATUS_ZERO, "answer": ZERO_MESSAGE,
                "count": 0, "activities": []}
    if not active:
        noun = "activity" if total == 1 else "activities"
        return {
            **base,
            "answer": "%d matching %s exist, but none name a specific %s in the "
                      "post text (based on available TCE LinkedIn posts)%s." % (
                total, noun, axis, note or ""),
            "count": total,
            "activities": _fetch_rows(conn, args),
            "rows": [],
            "chart": {"data": []},
            "comparison": [],
        }
    label_key = {"year": "academic_year",
                 "department": "department",
                 "category": "name",
                 "stakeholder": "stakeholder"}[dimension]
    ranked = sorted(active, key=lambda r: (r["activity_count"], r[label_key]),
                    reverse=superlative == "highest")
    winner = ranked[0]
    winner_count = winner["activity_count"]
    verdict = "most" if superlative == "highest" else "fewest"
    noun = "activity" if winner_count == 1 else "activities"
    chart_rows, chart = _rows_and_chart(ranked[:10], label_key)
    return {
        **base,
        "answer": "%s had the %s activities (by %s)%s." % (
            winner[label_key], verdict, axis, note or ""),
        "count": None,
        "activities": [],
        "rows": chart_rows,
        "chart": chart,
        "comparison": [{"entity": r[label_key], "activity_count": r["activity_count"]}
                       for r in ranked],
    }


def _answer_breakdown(question, conn, used, note):
    if _blocked_year(used):
        return {"question": question, "status": STATUS_ZERO,
                "answer": ZERO_MESSAGE, "count": 0, "activities": [],
                "criteria": _criteria(used)}
    dimension = (used.get("group_by") or "category")
    args = _active_filters(used)
    rows = _grouped_counts(conn, args, dimension)
    active = [r for r in rows if r.get("activity_count", 0) > 0]
    base = {"question": question, "status": STATUS_ANSWER,
            "criteria": _criteria(used)}
    label_key = {"year": "academic_year", "department": "department",
                 "category": "name", "stakeholder": "stakeholder"}[dimension]
    total = count_reportable(conn, args)
    if not active and total == 0:
        # Honest, useful response instead of a flat refusal: point at what the
        # dataset actually contains for the context of the question.
        describe = _describe(used) or "the selected criteria"
        avail_ay = []
        for r in analytics_yearly(conn, {"status": REPORTABLE}):
            if r.get("activity_count", 0) > 0:
                avail_ay.append(r["academic_year"])
        return {**base, "status": STATUS_ZERO,
                "answer": ("No matching %s in the available LinkedIn dataset. "
                           "Available dated academic year(s): %s."
                           % (describe, ", ".join(avail_ay) if avail_ay else "none")),
                "count": 0, "activities": [], "rows": [], "chart": {"data": []},
                "comparison": []}
    total_text = ("%d activities in total" % total) if total else "no matching activities"
    chart_rows, chart = _rows_and_chart(active, label_key)
    return {
        **base,
        "answer": "Breakdown by %s of %s (%s)%s." % (
            dimension, _describe(used) or "matching activities", total_text,
            note or ""),
        "count": total,
        "activities": [],
        "rows": chart_rows,
        "chart": chart,
        "comparison": [{"entity": r[label_key], "activity_count": r["activity_count"]}
                       for r in active],
    }


def _available_departments(conn):
    """Public department names present in the reportable dataset."""
    return [d for d in conn.execute(
        "SELECT DISTINCT department FROM linkedin_activity_departments "
        "ORDER BY department").fetchall() if d["department"] != "General"]


def _commodity_side(text, available):
    """Best-effort single entity for a compare side."""
    cat_code, cat_name = _ground_category(text, available["categories"])
    if cat_code:
        return ("category", cat_name or cat_code, cat_code)
    dept = _ground_department(text, available["departments"])
    if dept:
        return ("department", dept, dept)
    stak = _ground_stakeholder(text)
    if stak:
        return ("stakeholder", stak, stak)
    return (None, None, None)


def _answer_compare(question, conn, used, note, available):
    sides = re.split(r"\s+(?:vs\.?|versus|compare|compared|or)\s+", question,
                     flags=re.IGNORECASE)
    if len(sides) < 2:
        return None
    left = _commodity_side(sides[0], available)
    right = _commodity_side(sides[-1], available)
    if left[0] is None or right[0] is None or left[0] != right[0]:
        return None
    dimension, left_name, left_key = left
    _, right_name, right_key = right
    if left_key == right_key:
        return None
    args = _active_filters(used)
    mapping = {"category": ("category", left_key), "department": ("department", left_key),
               "stakeholder": ("stakeholder", left_key)}
    results = []
    for name, key in ((left_name, left_key), (right_name, right_key)):
        side_args = dict(args)
        side_args[mapping[dimension][0]] = key
        results.append({"label": name, "count": count_reportable(conn, side_args)})
    lc, rc = results[0]["count"], results[1]["count"]
    if lc == rc:
        verdict = "Both have the same number of matching activities (%d vs %d)." % (lc, rc)
    elif lc > rc:
        verdict = "%s has more activities than %s (%d vs %d)." % (left_name, right_name, lc, rc)
    else:
        verdict = "%s has more activities than %s (%d vs %d)." % (right_name, left_name, rc, lc)
    chart_rows = [{"label": r["label"], "value": r["count"]} for r in results]
    base = {"question": question, "status": STATUS_ANSWER,
            "criteria": _criteria(used)}
    return {
        **base,
        "answer": verdict,
        "count": max(lc, rc),
        "activities": [],
        "rows": chart_rows,
        "chart": {"data": chart_rows},
        "comparison": [{"entity": r["label"], "activity_count": r["count"]} for r in results],
        "criteria": [left_name, right_name],
    }


def answer_question(question, conn=None):
    """Answer a plain-English question about the LinkedIn reportable dataset."""
    own = conn is None
    conn = conn or get_reportable_connection()
    try:
        available = conn.execute(
            "SELECT DISTINCT academic_year FROM linkedin_reportable_activities "
            "WHERE reportable_status=? AND academic_year IS NOT NULL ORDER BY academic_year",
            (REPORTABLE,)).fetchall()
        avail_years = [r["academic_year"] for r in available]
        categories = conn.execute(
            "SELECT DISTINCT category_code FROM linkedin_activity_categories ORDER BY category_code"
        ).fetchall()
        avail_categories = [{"code": r["category_code"], "name": ""} for r in categories]
        departments = conn.execute(
            "SELECT DISTINCT department FROM linkedin_activity_departments ORDER BY department"
        ).fetchall()
        avail_departments = [r["department"] for r in departments]
        available = {"years": avail_years, "categories": avail_categories,
                     "departments": avail_departments}

        lowered = question.lower()
        used = {}

        year, raw_year = _normalise_year(question, avail_years)
        note = ""
        if raw_year:
            used["year_unavailable"] = raw_year
            note = " no available records exist for academic year %s (available: %s)" % (
                raw_year, ", ".join(avail_years) if avail_years else "none")
        elif year:
            used["year"] = year

        cat_code, cat_name = _ground_category(question, avail_categories)
        if cat_code:
            used["category"] = cat_code
            used["category_label"] = cat_name or cat_code

        dept = _ground_department(question, avail_departments)
        scope = _ground_scope(question)
        # "general" is an institution-wide scope marker, not a department.
        if dept == "General":
            if not scope:
                scope = "general"
            dept = None
        if dept:
            used["department"] = dept
        if scope:
            used["scope"] = scope

        stak = _ground_stakeholder(question)
        if stak:
            used["stakeholder"] = stak

        if UNDATED_RE.search(lowered):
            used["date_status"] = "undated"

        year_wise = bool(YEAR_WISE_RE.search(lowered))
        if year_wise:
            used["group_by"] = "year"

        base = {"question": question, "criteria": _criteria(used)}
        # The grounded selection travels with the answer so the Ask-the-Data
        # report exports use the same category-specific columns as the Report
        # Generator.
        base["category_code"] = used.get("category")
        base["scope"] = used.get("scope")
        base["department"] = used.get("department")

        compare = _answer_compare(question, conn, used, note, available)
        if compare:
            return compare

        # "year wise / by year / across years" asks for a grouped breakdown.
        if used.get("group_by") == "year":
            return {**base, **_answer_breakdown(question, conn, used, note)}

        if re.search(r"\b(?:how many|count)\b", lowered):
            return {**base, **_answer_count(question, conn, used, note)}

        # "rate the achievements of X" -> a measurable reporting request:
        # treat as a grouped count/breakdown, never an arbitrary score.
        if RATE_RE.search(lowered) and (used.get("category") or used.get("department")
                                        or used.get("stakeholder") or used.get("scope")):
            dimension = ("department" if used.get("category")
                         else "category" if used.get("department")
                         else "stakeholder" if used.get("stakeholder")
                         else "year" if used.get("year")
                         else "category")
            used["group_by"] = dimension
            return {**base, **_answer_breakdown(question, conn, used, note)}

        if re.search(r"\b(?:most|highest|maximum|largest)\b", lowered):
            dimension = ("department" if re.search(r"\b(?:department|dept|branch)\b", lowered)
                         else "category" if re.search(r"\b(?:category|categories)\b", lowered)
                         else "stakeholder" if re.search(r"\b(?:stakeholder|audience)\b", lowered)
                         else "year" if re.search(r"\b(?:year|academic year)\b", lowered)
                         else "department")
            used["group_by"] = dimension
            return {**base, **_answer_ranking(question, conn, used, note, "highest")}

        if re.search(r"\b(?:fewest|lowest|least|minimum)\b", lowered):
            dimension = ("department" if re.search(r"\b(?:department|dept|branch)\b", lowered)
                         else "category" if re.search(r"\b(?:category|categories)\b", lowered)
                         else "year" if re.search(r"\b(?:year|academic year)\b", lowered)
                         else "department")
            used["group_by"] = dimension
            return {**base, **_answer_ranking(question, conn, used, note, "lowest")}

        if re.search(r"\b(?:breakdown|distribut|report|how are|categoris|categoriz|what (?:categories|departments|stakeholders)|\ball\b)"
                     + r"|\btypes?\b|\bcategories are available\b", lowered) or \
                (re.search(r"\bwhat\b", lowered) and re.search(r"\b(categories|departments|stakeholders)\b", lowered)):
            dimension = ("stakeholder" if re.search(r"\bstakeholders?\b", lowered)
                         else "department" if re.search(r"\bdepartments?\b", lowered)
                         else "category" if re.search(r"\bcategor", lowered)
                         else "year" if re.search(r"\byears?\b", lowered)
                         else "category")
            used["group_by"] = dimension
            return {**base, **_answer_breakdown(question, conn, used, note)}

        if re.search(r"\b(?:show|list|find|display|tell|about|details?|give|get)\b", lowered) or not used:
            return {**base, **_answer_list(question, conn, used, note)}

        return {**base, "status": STATUS_UNSUPPORTED, "answer": SCOPE_MESSAGE,
                "count": None, "activities": []}
    finally:
        if own:
            conn.close()