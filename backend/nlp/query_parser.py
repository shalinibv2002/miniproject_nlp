"""Phase 12: rule-based natural-language query parser.

Extracts intent (count/list/compare) and grounded entities (year, category,
department, stakeholder) from a plain-English question. All downstream
execution uses a fixed set of safe, parameterized SQL templates — user text is
never interpolated into SQL.
"""

import re

from backend.nlp.extractors import CATEGORY_KEYWORDS
from backend.nlp.train_models import code_for_title

INTENT_COUNT = "count"
INTENT_LIST = "list"
INTENT_COMPARE = "compare"

_COUNT_CUES = ["how many", "count of", "number of", "how much", "total",
               "total number", "how often"]
_LIST_CUES = ["list", "show", "which", "name", "find", "give me",
              "what are", "tell me", "enumerate", "display"]
_COMPARE_CUES = ["compare", "vs ", "versus", "more than", "vs.", "which has more"]

_YEAR_PAT = re.compile(
    r"(?<!\d)((?:19|20)\d{2})\s*[-–—]\s*((?:19|20)?\d{2})(?!\d)",
    re.IGNORECASE,
)
_SINGLE_YEAR_PAT = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def normalize_year(text):
    """Return a (start_year, end_year) tuple or None for a year phrase."""
    m = _YEAR_PAT.search(text)
    if m:
        start = int(m.group(1))
        end_txt = m.group(2)
        if len(end_txt) == 4:
            end = int(end_txt)
        else:
            end = (start // 100) * 100 + int(end_txt)
        if end == start + 1:
            return (start, end)
        return None
    m = _SINGLE_YEAR_PAT.search(text)
    if m:
        y = int(m.group(1))
        return (y, y + 1)
    return None


def _match_categories(text):
    t = text.lower()
    found = []
    for category_name, cues in CATEGORY_KEYWORDS.items():
        if any(cue in t for cue in cues):
            found.append((code_for_title(category_name), category_name))
    # de-dup preserving order
    seen, unique = set(), []
    for code, name in found:
        if code not in seen:
            seen.add(code)
            unique.append((code, name))
    return unique


def _match_departments(text, conn=None):
    """Exact mention matching with word boundaries — never fuzzy on queries.

    Short codes/aliases ('it', 'me', 'ai') are only matched as whole words to
    avoid matching inside unrelated words like 'activ'it'ies'.
    """
    import re as _re
    if not text:
        return []
    from backend.nlp.dictionaries import load_department_dict
    t = text.lower()
    found = []
    for dept in load_department_dict(conn):
        candidates = [dept["name"].lower()] + dept["aliases"]
        if dept.get("short_name"):
            candidates.append(dept["short_name"].lower())
        for cand in candidates:
            if not cand:
                continue
            pattern = _re.compile(r"\b" + _re.escape(cand) + r"\b")
            if pattern.search(t):
                found.append((dept["code"], dept["name"]))
                break
    return found


# NLQ-specific stakeholder cues: descriptive words only. Abbreviations that
# overlap with categories ("fdp", "sttp", "ncc", "nss") are intentionally
# excluded so a category question doesn't get an extra stakeholder filter.
_STAKEHOLDER_CUES_NLQ = {
    "STUDENTS": ["students", "student"],
    "FACULTY": ["faculty", "teachers", "professors", "teaching staff"],
    "STAFF": ["non-teaching staff", "support staff", "office staff", "technical staff", "administrative staff"],
    "ALUMNI": ["alumni", "alumnus"],
    "INDUSTRY": ["industry", "industries", "companies", "corporate", "recruiters", "startup", "entrepreneur"],
    "PARENTS": ["parents", "guardians"],
    "GOVERNMENT": ["government", "aicte", "ugc", "dst ", "drdo", "isro", "ministry"],
    "COMMUNITY": ["school students", "school children", "community", "rural", "village"],
}


def _match_stakeholders(text):
    t = text.lower()
    found = []
    for code, cues in _STAKEHOLDER_CUES_NLQ.items():
        if any(cue in t for cue in cues):
            found.append((code, code.title()))
    return found


def _split_compare_sides(text):
    """Split a comparison into two sides when separated by vs/versus/and."""
    parts = re.split(r"\b(?:vs[.:]?|versus)\b", text, flags=re.IGNORECASE)
    if len(parts) == 2:
        return parts[0], parts[1]
    return text, None


def detect_intent(text):
    t = text.lower()
    if any(cue in t for cue in _COMPARE_CUES):
        return INTENT_COMPARE
    if any(cue in t for cue in _COUNT_CUES):
        return INTENT_COUNT
    if any(cue in t for cue in _LIST_CUES):
        return INTENT_LIST
    return INTENT_LIST


def parse_question(text, conn=None):
    """Return structured intent + grounded filters."""
    intent = detect_intent(text)
    year = normalize_year(text)
    categories = _match_categories(text)
    departments = _match_departments(text, conn=conn)
    stakeholders = _match_stakeholders(text)

    result = {
        "intent": intent,
        "filters": {
            "year": year,
            "category": categories[0][0] if categories else None,
            "category_name": categories[0][1] if categories else None,
            "department": departments[0][0] if departments else None,
            "department_name": departments[0][1] if departments else None,
            "stakeholder": stakeholders[0][0] if stakeholders else None,
        },
        "entities": {"categories": categories, "departments": departments},
    }
    if intent == INTENT_COMPARE:
        left, right = _split_compare_sides(text)
        result["compare"] = {
            "left": {
                "category": _match_categories(left) if left else [],
                "department": _match_departments(left, conn=conn) if left else [],
            },
            "right": {
                "category": _match_categories(right) if right else [],
                "department": _match_departments(right, conn=conn) if right else [],
            },
        }
    return result