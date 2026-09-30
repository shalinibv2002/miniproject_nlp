"""Query System V2: translate a natural-language question into a safe internal plan.

The interpreter keeps every internal detail (intents, filters, grouping,
aggregation) inside this module.  The public response is assembled later by
``query_executor`` and never exposes the plan to the UI.

The plan structure:

    {
        "kind": KIND_*,
        "group_by": "year" | "department" | "category" | None,
        "order": "desc" | "asc" | None,
        "limit": int | None,
        "filters": {
            "periods": frozenset(public period keys) | None,
            "department": canonical public department name | None,
            "category": (code, public name) | None,
            "stakeholder": stakeholder display value | None,
            "dimension": "general" | "departmental" | None,
            "activity_name": str | None,
        },
        "compare": [ {label, filters}, {label, filters} ] | None,
        "message": clarification text | None,
    }
"""

from __future__ import annotations

import re

from backend.database.category_catalog import (
    CATEGORY_PUBLIC_NAMES, PUBLIC_CATEGORY_CODES,
)
from backend.database.department_catalog import (
    DEPARTMENT_ALIASES, GENERAL_NAME, PUBLIC_DEPARTMENTS,
    department_normalized_sql, normalize_department,
)
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, PUBLIC_PERIOD_LABELS, year_to_period,
)
from backend.nlp.extractors import CATEGORY_KEYWORDS
from backend.nlp.train_models import code_for_title

KIND_COUNT = "count"
KIND_LIST = "list"
KIND_HIGHEST = "highest"
KIND_LOWEST = "lowest"
KIND_RANKING = "ranking"
KIND_TOP_N = "top_n"
KIND_TREND = "trend"
KIND_BREAKDOWN = "breakdown"
KIND_COMPARE = "compare"
KIND_DETAIL = "detail"
KIND_CLARIFICATION = "clarification"
KIND_UNSUPPORTED = "unsupported"

# ---------------------------------------------------------------------------
# Phrase catalogs
# ---------------------------------------------------------------------------

_BEFORE_2021_CUES = (
    "before 2021", "prior to 2021", "pre-2021", "pre 2021",
    "before the year 2021", "prior to the year 2021",
    "before 2020", "prior to 2020", "pre-2020", "pre 2020",
    "before 2019", "before 2018",
)

_COUNT_CUES = ("how many", "count of", "number of", "how much", "total",
               "total number", "how often", "what is the count")
_LIST_CUES = ("list", "show", "which", "name", "find", "give me", "what are",
              "tell me", "enumerate", "display")
_COMPARE_CUES = ("compare", "vs", "versus", "more than", "which has more")

_SUPERLATIVE_HIGH_CUES = ("most", "highest", "maximum", "best")
_SUPERLATIVE_LOW_CUES = ("least", "fewest", "lowest", "minimum")

_RANK_CUES = ("rank", "ranking", "ranked", "sort by", "sorted by", "order by")
_TREND_CUES = ("trend", "year-wise", "year wise", "yearwise", "over the years",
               "year on year", "year-on-year", "across years", "by year",
               "by period", "per year")
_BREAKDOWN_CUES = ("breakdown", "department-wise", "department wise",
                   "category-wise", "category wise", "grouped by",
                   "per department", "per category", "by department",
                   "by category", "departmental breakdown")

_DETAIL_CUES = (
    "when was", "when did", "when is", "when will", "in which year",
    "which year", "who organized", "who organised", "who conducted",
    "who held", "who hosted", "who organized", "where was", "where did",
    "tell me about", "tell us about", "give details", "more details",
    "details about", "details of", "details on", "what happened",
)

# Words that signal the question is about institutional activity data.
_TOPIC_CUES = (
    "activity", "activities", "category", "categories", "period", "year",
    "workshop", "workshops", "seminar", "seminars", "conference", "conferences",
    "research", "achievement", "achievements", "award", "sports", "club",
    "clubs", "chapter", "chapters", "society", "society", "ncc", "nss", "fdp",
    "hackathon", "hackathon", "cultural", "outreach", "industry",
    "internship", "placement", "orientation", "webinar", "campus",
    "stakeholder", "stakeholders", "student", "students", "faculty", "staff",
    "department", "departments", "dept", "count", "how many", "number",
    "trend", "rank", "ranking", "top", "most", "least", "compare",
)

_EVENT_NOUNS = frozenset({
    "seminar", "workshop", "workshops", "symposium", "conference", "tech fest",
    "hackathon", "hack-a-thon", "camp", "bootcamp", "drive", "meet", "meeting",
    "day", "talk", "talks", "programme", "program", "event", "ceremony", "fest",
    "festival", "expo", "exhibition", "session", "orientation", "induction",
    "convocation", "inauguration", "competition", "tournament", "webinar",
    "lecture", "lectures", "training", "course", "awareness", "rally", "meetup",
    "celebration", "screening", "exhibition", "run", "campaign",
})

_DETAIL_RESERVED_FIRST = frozenset({
    "which", "how", "what", "who", "when", "where", "why", "list", "show",
    "name", "tell", "give", "find", "compare", "rank", "in", "on", "at", "the",
    "a", "an", "and", "or", "of", "to", "from", "during", "between", "about",
    "for", "than", "by", "with", "was", "were", "is", "are", "has", "have",
    "had", "did", "does", "had", "our", "your", "top", "best", "most", "least",
    "total", "any", "many", "much", "such", "their", "there", "this", "that",
    "held", "conducted", "organized", "organised", "made", "took", "been",
})

_PUBLIC_PERIOD_SET = frozenset(PUBLIC_PERIODS)
_PUBLIC_PERIOD_LABELS_LOWER = {
    PUBLIC_PERIOD_LABELS[key].lower().replace(" ", ""): key
    for key in PUBLIC_PERIOD_LABELS
}
_PUBLIC_PERIOD_SHORT_LOWER = {key.replace("-", ""): key for key in PUBLIC_PERIODS}


def _empty_filters():
    return {"periods": None, "department": None, "category": None,
            "stakeholder": None, "dimension": None, "activity_name": None}


def _new_plan():
    return {"kind": KIND_UNSUPPORTED, "group_by": None, "order": None,
            "limit": None, "filters": _empty_filters(), "compare": None,
            "message": None}


# ---------------------------------------------------------------------------
# Period extraction
# ---------------------------------------------------------------------------

_ACADEMIC_SPAN = re.compile(
    r"(?<!\d)((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)?\d{2})(?!\d)")
_YEAR_SPAN = re.compile(r"(?<!\d)((?:19|20)\d{2})\s*[-–—]\s*(?:((?:19|20)\d{2}))(?!\d)")
_SINGLE_YEAR = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def _short_period(start, end):
    """Return the short public period for an (start, end) academic span."""
    if end != start + 1:
        return None
    candidate = f"{start}-{str(end)[-2:]}"
    if candidate in _PUBLIC_PERIOD_SET:
        return candidate
    return None


def extract_period(text):
    """Return a frozenset of public period keys, else a clarification string.

    ``text`` is the lowercased question.  ``None`` means no period mentioned.
    A frozenset means the question pins one or more public periods.
    A string is an honest clarification request (e.g. an unimplemented span).
    """
    t = text
    if any(cue in t for cue in _BEFORE_2021_CUES):
        return frozenset({BEFORE_2021})

    m = _ACADEMIC_SPAN.search(t)
    if m:
        start, end = int(m.group(1)), int(m.group(2))
        if len(m.group(2)) == 2:
            end = (start // 100) * 100 + end
        short = _short_period(start, end)
        if short:
            return frozenset({short})
        if end == start + 1 and start < 2021:
            return frozenset({BEFORE_2021})
        if end == start + 1 and start >= 2026:
            return "Do you mean academic year 2025-2026?"
        if end > 2026:
            return "Do you mean academic year 2025-2026?"
        candidate_short = _short_period(start, end)
        if candidate_short:
            return frozenset({candidate_short})
        return "Do you mean academic year 2025-2026?"

    m = _SINGLE_YEAR.search(t)
    if m:
        year = int(m.group(1))
        if year <= 2020:
            return frozenset({BEFORE_2021})
        if year >= 2026:
            return "Do you mean academic year 2025-2026?"
        return frozenset({year_to_period(year)})
    return None


def periods_in_range(start, end):
    """Public periods covering a calendar-year range ``start``..``end``."""
    if start > end:
        start, end = end, start
    periods = set()
    for year in range(start, end + 1):
        if year <= 2020:
            periods.add(BEFORE_2021)
        elif year <= 2025:
            periods.add(year_to_period(year))
        else:
            periods.add("2025-26")
    return frozenset(periods)


# "from 2021 to 2026" style ranges are translated before single periods are
# considered so the two year tokens never resolve independently.
_YEAR_RANGE_RE = re.compile(
    r"(?:from|between)\s+(20\d{2})\s*(?:to|until|and)\s+(20\d{2})")


def extract_year_range(text):
    """Return ``(start, end)`` for a From/To calendar range, else None."""
    m = _YEAR_RANGE_RE.search(text)
    if not m:
        return None
    start, end = int(m.group(1)), int(m.group(2))
    if start > end:
        start, end = end, start
    return (start, end)


# ---------------------------------------------------------------------------
# Department resolution
# ---------------------------------------------------------------------------

ALL_CAPS_ALIASES = frozenset({"it", "ai", "ca", "me", "ce"})
_AZ = frozenset("abcdefghijklmnopqrstuvwxyz")


def _uppercase_token_ok(text, alias):
    """Short aliases need an all-caps token to avoid false positives.

    ``it`` is extremely common prose ("It was...") so it requires the exact
    all-caps form ``IT``; the same rule keeps ``AI``/``CA``/``ME``/``CE`` safe.
    """
    if len(alias) <= 2 and alias.isalpha() and alias.lower() not in ALL_CAPS_ALIASES:
        # Other short aliases also require all-caps occurrence.
        return bool(re.search(rf"\b{re.escape(alias.upper())}\b", text))
    if alias.lower() == "it":
        return bool(re.search(r"\bIT\b", text))
    return bool(re.search(rf"\b{re.escape(alias.upper())}\b", text))


def resolve_department(text, conn):
    """Return the canonical public department name for a question, or None.

    Whole-word, case-insensitive matching for long names; short aliases (CSE,
    ECE, IT, AI, ...) only match when typed in a safe form so prose never
    triggers a department (e.g. "Give me the..." never becomes Mechanical).
    """
    lowered = text.lower()
    hits = []

    db_names = _db_department_names(conn)
    for name in sorted(set(db_names) | set(PUBLIC_DEPARTMENTS), key=len, reverse=True):
        if not name or len(name) < 3:
            continue
        if re.search(rf"\b{re.escape(name.lower())}\b", lowered):
            hits.append((len(name), name))

    for alias, canonical in DEPARTMENT_ALIASES.items():
        if len(alias) <= 2:
            if _uppercase_token_ok(text, alias):
                hits.append((len(canonical), canonical))
            continue
        if re.search(rf"\b{re.escape(alias.lower())}\b", lowered):
            hits.append((len(canonical), canonical))

    if not hits:
        return None
    best = max(hits, key=lambda pair: (pair[0], pair[1]))
    return best[1]


def _db_department_names(conn):
    """Distinct normalised department display values live in this DB."""
    if conn is None:
        return []
    expr = department_normalized_sql()
    rows = conn.execute(
        f"SELECT DISTINCT {expr} AS department FROM institutional_activities a "
        "LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"
    ).fetchall()
    return [row["department"] for row in rows if row["department"]]


# ---------------------------------------------------------------------------
# Category resolution
# ---------------------------------------------------------------------------

def _category_by_name(name):
    from backend.database.category_catalog import (
        GENERAL_CATEGORIES, DEPARTMENTAL_CATEGORIES,
    )
    lowered = name.lower()
    for item in (*GENERAL_CATEGORIES, *DEPARTMENTAL_CATEGORIES):
        if item["name"].lower() == lowered or item["code"].lower() == lowered:
            return item["code"]
    return code_for_title(name)


def resolve_category(text):
    """Return ``(code, public_name)`` for the most specific category mention.

    Only public categories are ever returned.  Multiple potential matches are
    resolved by the longest matched phrase so "international conference" beats
    "conference" and a single unambiguous topic wins over guessing.
    """
    t = text.lower()
    found = {}  # code -> (match_len, public_name)
    for name, cues in CATEGORY_KEYWORDS.items():
        code = code_for_title(name)
        if code not in PUBLIC_CATEGORY_CODES:
            continue
        for cue in cues:
            if cue in t:
                key = (len(cue), name)
                if code not in found or key[0] > found[code][0]:
                    found[code] = (len(cue), CATEGORY_PUBLIC_NAMES.get(code, cue))
    for code in PUBLIC_CATEGORY_CODES:
        public_name = CATEGORY_PUBLIC_NAMES.get(code, "")
        if public_name and public_name.lower() in t:
            if code not in found or len(public_name) > found[code][0]:
                found[code] = (len(public_name), public_name)

    if not found:
        return None
    code = max(found.items(), key=lambda pair: pair[1][0])[0]
    return (code, found[code][1])


# ---------------------------------------------------------------------------
# Stakeholder resolution
# ---------------------------------------------------------------------------

def resolve_stakeholder(text, conn, lowered=None):
    """Return a stakeholder display value mentioned in the question, or None.

    Display values are read from the live metadata so multi-stakeholder
    values ("Students; Faculty") are understood part by part.  Short singular/
    plural forms ("student" for "Students") are matched too, but only when the
    question already talks about activities (applied by the caller).
    """
    if conn is None:
        return None
    tl = (lowered or text.lower())
    try:
        values = [row["stakeholder_display"] for row in conn.execute(
            "SELECT DISTINCT stakeholder_display FROM final_activity_metadata "
            "WHERE stakeholder_display IS NOT NULL AND TRIM(stakeholder_display) != ''"
        ).fetchall()]
    except Exception:
        return None
    tokens = sorted(
        {part.strip() for value in values for part in value.split(";") if part.strip()},
        key=len, reverse=True)
    for token in tokens:
        token_l = token.lower()
        if token_l in tl:
            return token
        if token_l.endswith("s") and token_l[:-1] in tl:
            return token
    return None


# ---------------------------------------------------------------------------
# Event-phrase & detail extraction
# ---------------------------------------------------------------------------

_EVENT_NOUN_RE = re.compile(r"\b(" + "|".join(sorted(_EVENT_NOUNS)) + r")\b", re.IGNORECASE)
_TITLE_RUN_RE = re.compile(
    r"\b(?:[A-Z][A-Za-z]+(?:[ -][A-Z][A-Za-z]+){0,4})\b")
_QUOTED_RE = re.compile(r"\"([^\"]+)\"|'([^']+)'")


def _phrase_is_valid(phrase):
    words = phrase.split()
    if not words or len(words) > 8:
        return False
    first = words[0].lower().strip(".,;:!?")
    if first in _DETAIL_RESERVED_FIRST or first.isdigit():
        return False
    # A phrase without any event noun must be at least two words long to
    # avoid treating stray capitalized words as named events.
    if not _EVENT_NOUN_RE.search(phrase) and len(words) < 2:
        return False
    return True


def _known_entity_phrases(conn):
    """Department/category/stakeholder names that must never become an
    event name (e.g. "Information Technology" is a department, not a title)."""
    phrases = set(PUBLIC_DEPARTMENTS)
    phrases.add(GENERAL_NAME)
    phrases.update(CATEGORY_PUBLIC_NAMES.values())
    for name in _db_department_names(conn):
        for part in name.split("; "):
            if part:
                phrases.add(part)
    if conn is not None:
        try:
            rows = conn.execute(
                "SELECT DISTINCT stakeholder_display FROM final_activity_metadata "
                "WHERE stakeholder_display IS NOT NULL").fetchall()
            for row in rows:
                for part in (row["stakeholder_display"] or "").split(";"):
                    part = part.strip()
                    if part:
                        phrases.add(part)
        except Exception:
            pass
    return sorted(phrases, key=len, reverse=True)


def _mask_known_entities(text, conn):
    """Replace known entity names with equal-length spaces so only real
    event/proper-noun titles remain as title-case runs."""
    masked = text
    for phrase in _known_entity_phrases(conn):
        masked = re.sub(
            re.escape(phrase), lambda match: " " * len(match.group(0)),
            masked, flags=re.IGNORECASE)
    return masked


def extract_event_phrase(text, conn=None):
    """Return a quoted or title-case event phrase, or None.

    For example "When was the Future Ready seminar conducted?" yields
    "Future Ready seminar".  Department/category/stakeholder names and
    reserved question words are never consumed as part of the name.
    """
    quoted = _QUOTED_RE.search(text)
    if quoted:
        phrase = quoted.group(1) or quoted.group(2)
        if phrase and _phrase_is_valid(phrase):
            return phrase.strip()

    masked = _mask_known_entities(text, conn)

    candidates = []
    for match in _TITLE_RUN_RE.finditer(masked):
        run = match.group(0).strip()
        if not run:
            continue
        if any(word.isupper() for word in run.split()):
            continue
        words = run.split()
        if len(words) < 2 or len(words) > 6:
            continue
        candidates.append((match.start(), run))

    if not candidates:
        return None

    candidates.sort(key=lambda pair: -len(pair[1]))
    for position, run in candidates:
        phrase = run
        # Optionally include a trailing event noun ("Future Ready seminar").
        remainder = text[position + len(run):]
        noun_match = _EVENT_NOUN_RE.match(remainder.lstrip())
        if noun_match and not noun_match.group(1)[0].isupper():
            phrase = f"{run} {noun_match.group(1)}"
        if _phrase_is_valid(phrase):
            return " ".join(phrase.split())
    for position, run in candidates:
        if _phrase_is_valid(run):
            return " ".join(run.split())
    return None


# ---------------------------------------------------------------------------
# Question-type detection
# ---------------------------------------------------------------------------

def _detect_superlative(text):
    lowered = text.lower()
    if any(cue in lowered for cue in _SUPERLATIVE_HIGH_CUES):
        return "highest"
    if any(cue in lowered for cue in _SUPERLATIVE_LOW_CUES):
        return "lowest"
    return None


def _has_compare_cue(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _COMPARE_CUES)


def _has_rank_cue(text):
    lowered = " " + text.lower() + " "
    for cue in _RANK_CUES:
        if cue in lowered:
            return True
    return False


def _has_trend_cue(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _TREND_CUES)


def _has_breakdown_cue(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _BREAKDOWN_CUES)


def _has_count_cue(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _COUNT_CUES)


def _has_list_cue(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _LIST_CUES)


_TOP_N_RE = re.compile(r"\btop\s+(\d+)\b", re.IGNORECASE)


def _top_n(text):
    m = _TOP_N_RE.search(text)
    if not m:
        return None
    value = int(m.group(1))
    return min(max(value, 1), 50)


def _infer_group(text):
    lowered = text.lower()
    if re.search(r"\byear\b", lowered) or "period" in lowered \
            or "academic year" in lowered:
        return "year"
    if "department" in lowered or re.search(r"\bdept\b|department s\b", lowered):
        return "department"
    if "category" in lowered or "categories" in lowered:
        return "category"
    return None


def _in_scope(text):
    lowered = text.lower()
    return any(cue in lowered for cue in _TOPIC_CUES)


# ---------------------------------------------------------------------------
# Comparison sides
# ---------------------------------------------------------------------------

def _resolve_entity(tail, conn):
    """Resolve one comparison side to a labelled filter dict or None."""
    filters = _empty_filters()
    label = tail.strip()
    department = resolve_department(tail, conn)
    if department:
        filters["department"] = department
        if re.search(r"\b(?:activities?|initiatives?|programs?|programmes?|events?)\b",
                     tail.lower()):
            label = department
        else:
            label = department
        return {"label": label, "filters": filters}
    category = resolve_category(tail)
    if category:
        filters["category"] = category
        return {"label": category[1], "filters": filters}
    lowered = tail.lower()
    period = extract_period(lowered)
    if isinstance(period, frozenset) and period:
        filters["periods"] = period
        return {"label": ", ".join(PUBLIC_PERIOD_LABELS.get(p, p) for p in sorted(period)),
                "filters": filters}
    if lowered in ("students", "student", "faculty", "staff", "alumni",
                   "industry", "parents", "government", "community"):
        stakeholders = {"students": "Students", "student": "Students",
                        "faculty": "Faculty", "staff": "Staff",
                        "alumni": "Alumni", "industry": "Industry",
                        "parents": "Parents", "government": "Government and Agencies",
                        "community": "Community and Society"}
        filters["stakeholder"] = stakeholders[lowered]
        return {"label": stakeholders[lowered], "filters": filters}
    return None


def _split_compare_tail(tail):
    """Split a compare tail like "workshops and seminars" into two sides."""
    for separator in (r"\s+and\s+", r"\s+or\s+", r"\s*,\s*"):
        for match in re.finditer(separator, tail, flags=re.IGNORECASE):
            left = tail[:match.start()].strip()
            right = tail[match.end():].strip()
            if _resolve_entity(left, None) and _resolve_entity(right, None):
                return left, right
    return None, None


def _compare_sides(text, conn):
    """Return two comparison-side dicts, or None."""
    split = re.split(r"\b(?:vs[.:]?|versus)\b", text, flags=re.IGNORECASE)
    if len(split) == 2 and split[1].strip():
        left, right = split[0].strip(), split[1].strip()
    elif "compare" in text.lower():
        tail = re.sub(r"^\s*compare\b", "", text, count=1, flags=re.IGNORECASE).strip().rstrip("?.:;")
        left, right = _split_compare_tail(tail)
        if not left:
            return None
    else:
        return None

    left_side = _resolve_entity(left, conn)
    right_side = _resolve_entity(right, conn) if right else None
    if not left_side or not right_side:
        return None
    return [left_side, right_side]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def interpret(question, conn=None):
    """Interpret ``question`` into a safe, self-contained execution plan."""
    text = (question or "").strip()
    tl = text.lower()
    plan = _new_plan()

    # 1. Period mentions come first so English phrases never shadow them.
    year_range = extract_year_range(tl)
    if year_range:
        period_result = periods_in_range(*year_range)
    else:
        period_result = extract_period(tl)

    if isinstance(period_result, str):
        plan["kind"] = KIND_CLARIFICATION
        plan["message"] = period_result
        return plan
    if period_result:
        plan["filters"]["periods"] = period_result

    # 2. Detail questions about a named event.
    activity_name = extract_event_phrase(text, conn)
    superlative = _detect_superlative(tl)
    has_compare = _has_compare_cue(tl)
    has_rank = _has_rank_cue(tl)
    top_n = _top_n(text)
    if (activity_name and any(cue in tl for cue in _DETAIL_CUES)
            and not superlative and not has_compare
            and top_n is None and not has_rank):
        plan["kind"] = KIND_DETAIL
        plan["filters"]["activity_name"] = activity_name
        return plan

    # 3. Everything else resolves entities against the text minus the name.
    match_text = text
    if activity_name:
        match_text = match_text.replace(activity_name, " ", 1)
    match_lower = match_text.lower()

    dimension = None
    if "general category" in match_lower or "institution-wide" in match_lower \
            or "institution wide" in match_lower or "general activities" in match_lower:
        dimension = "general"
    elif "departmental" in match_lower or "department category" in match_lower:
        dimension = "departmental"

    department = resolve_department(match_text, conn)
    category = resolve_category(match_text)
    stakeholder = resolve_stakeholder(match_text, conn, lowered=match_lower) if conn else None

    # A category + stakeholder spelling overlap (e.g. Industry Collaboration vs
    # Industry) is disambiguated by dropping the stakeholder read.
    if category and category[0] == "INDUSTRY" and stakeholder == "Industry":
        stakeholder = None

    has_activity_context = ("activit" in match_lower or "workshop" in match_lower
                            or "program" in match_lower or "event" in match_lower
                            or department or category or dimension
                            or plan["filters"]["periods"])
    if stakeholder and not has_activity_context:
        stakeholder = None

    plan["filters"]["department"] = department
    plan["filters"]["category"] = category
    plan["filters"]["stakeholder"] = stakeholder
    plan["filters"]["dimension"] = dimension

    # 4. Compare (two explicit sides).
    if has_compare:
        sides = _compare_sides(text, conn)
        if sides:
            plan["kind"] = KIND_COMPARE
            plan["compare"] = sides
            plan["filters"] = _empty_filters()
            return plan

    # 5. Top-N rankings.
    if top_n is not None:
        group = _infer_group(match_lower)
        if not group:
            group = "department" if department else ("year" if plan["filters"]["periods"] else None)
        if group:
            plan["kind"] = KIND_TOP_N
            plan["group_by"] = group
            plan["limit"] = top_n
            return plan

    # 6. Rankings by an axis.
    if has_rank:
        group = _infer_group(match_lower)
        if not group:
            group = "department" if department else "category"
        if group:
            plan["kind"] = KIND_RANKING
            plan["group_by"] = group
            return plan
        plan["kind"] = KIND_UNSUPPORTED
        return plan

    # 7. Superlatives ("most", "least", ...).
    if superlative:
        group = _infer_group(match_lower)
        if not group:
            group = "year" if ("period" in match_lower or "year" in match_lower) else "year"
        plan["kind"] = KIND_HIGHEST if superlative == "highest" else KIND_LOWEST
        plan["group_by"] = group
        plan["order"] = "desc" if superlative == "highest" else "asc"
        return plan

    # 8. Year-wise trend.
    if _has_trend_cue(tl):
        plan["kind"] = KIND_TREND
        plan["group_by"] = _infer_group(match_lower) or "year"
        return plan

    # 9. Explicit breakdowns.
    if _has_breakdown_cue(tl):
        group = _infer_group(match_lower)
        if group:
            plan["kind"] = KIND_BREAKDOWN
            plan["group_by"] = group
            return plan

    # 10. Counts and lists.
    if _has_count_cue(tl):
        plan["kind"] = KIND_COUNT
        return plan
    if _has_list_cue(tl):
        plan["kind"] = KIND_LIST
        return plan

    # 11. No recognised pattern.
    if _in_scope(tl):
        plan["kind"] = KIND_LIST
        return plan
    plan["kind"] = KIND_UNSUPPORTED
    return plan