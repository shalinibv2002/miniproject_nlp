"""Shared, read-only public category catalog.

Single source of truth for the two public category fields:

  * General Category      - applies only to institution-wide activities whose
                            normalised department is ``General``.
  * Departmental Category - applies only to department-specific activities
                            (normalised department is a real department).

Everything here is derived from stored category codes and the normalised
department value; it never writes to the database and never mutates data.
Raw values are preserved; only the public presentation maps them.
"""

from backend.database.department_catalog import GENERAL_NAME, normalize_department

# Public name for every stored category code.  These are the human-facing
# labels shown in the UI and returned by the public API.
CATEGORY_PUBLIC_NAMES = {
    "ACHIEVEMENT": "Achievement and Awards",
    "RESEARCH": "Research and Consultancy",
    "INDUSTRY": "Industry Collaboration",
    "CLUB": "Clubs and Chapters",
    "OUTREACH": "Outreach and Extension",
    "WORKSHOP": "Workshops",
    "CONFERENCE": "Conference",
    "SEMINAR": "Seminar",
    "GUEST_LECTURE": "Guest Lecture",
    "FDP": "FDP",
    "HACKATHON": "Hackathon",
    "CULTURAL": "Cultural",
    "SPORTS": "Sports",
    "NCC": "NCC",
    "NSS": "NSS",
    "PLACEMENT": "Placement",
    "INTERNSHIP": "Internship",
    "ORIENTATION": "Orientation",
    "CAMPUS": "Campus",
    "WEBINAR": "Webinar",
    # Display name only; the stored code stays ``ALUMNI``.
    "ALUMNI": "Alumni Meet",
}

# Public presentation explicitly excludes the three legacy institutional
# categories (Technical Festival, STTP, Symposium).  AIA activities that still
# carry those stored codes keep their records and provenance; the codes are
# simply never presented as public categories.  The Alumni code is excluded
# for the same reason (it is a stakeholder grouping, not an activity category).

# Canonical General Category master, in presentation order.  Tech Fest, STTP
# and Symposium are intentionally excluded (justified legacy choices) along
# with the Alumni category, giving exactly the 20 required options.
GENERAL_CATEGORIES = (
    {"code": "ACHIEVEMENT", "name": "Achievement and Awards"},
    {"code": "RESEARCH", "name": "Research and Consultancy"},
    {"code": "INDUSTRY", "name": "Industry Collaboration"},
    {"code": "CLUB", "name": "Clubs and Chapters"},
    {"code": "OUTREACH", "name": "Outreach and Extension"},
    {"code": "WORKSHOP", "name": "Workshops"},
    {"code": "CONFERENCE", "name": "Conference"},
    {"code": "SEMINAR", "name": "Seminar"},
    {"code": "GUEST_LECTURE", "name": "Guest Lecture"},
    {"code": "FDP", "name": "FDP"},
    {"code": "HACKATHON", "name": "Hackathon"},
    {"code": "CULTURAL", "name": "Cultural"},
    {"code": "SPORTS", "name": "Sports"},
    {"code": "NCC", "name": "NCC"},
    {"code": "NSS", "name": "NSS"},
    {"code": "PLACEMENT", "name": "Placement"},
    {"code": "INTERNSHIP", "name": "Internship"},
    {"code": "ORIENTATION", "name": "Orientation"},
    {"code": "CAMPUS", "name": "Campus"},
    {"code": "WEBINAR", "name": "Webinar"},
)

# Canonical Departmental Category master.  Only these seven categories are
# valid classifications for department-specific activities.
DEPARTMENTAL_CATEGORIES = (
    {"code": "ACHIEVEMENT", "name": "Achievement and Awards"},
    {"code": "RESEARCH", "name": "Research and Consultancy"},
    {"code": "INDUSTRY", "name": "Industry Collaboration"},
    {"code": "CLUB", "name": "Clubs and Chapters"},
    {"code": "OUTREACH", "name": "Outreach and Extension"},
    {"code": "WORKSHOP", "name": "Workshops"},
    {"code": "CONFERENCE", "name": "Conference"},
)

GENERAL_CATEGORY_CODES = frozenset(item["code"] for item in GENERAL_CATEGORIES)
DEPARTMENTAL_CATEGORY_CODES = frozenset(item["code"] for item in DEPARTMENTAL_CATEGORIES)

# Every code the public presentation surfaces: the 20 General Categories plus
# the seven Departmental Categories.  Legacy codes (Technical Festival, STTP,
# Symposium) and Alumni are excluded from public outputs.
PUBLIC_CATEGORY_CODES = GENERAL_CATEGORY_CODES | DEPARTMENTAL_CATEGORY_CODES

# Order is the canonical presentation order (most specific first).
GENERAL_CATEGORY_ORDER = tuple(item["code"] for item in GENERAL_CATEGORIES)
DEPARTMENTAL_CATEGORY_ORDER = tuple(item["code"] for item in DEPARTMENTAL_CATEGORIES)


def public_category_name(code):
    """Return the public display name for a stored category code."""
    return CATEGORY_PUBLIC_NAMES.get(str(code).upper(), str(code))


def _resolve(value, master):
    """Resolve a category code or public name to a canonical master code."""
    entered = (value or "").strip()
    if not entered:
        return None
    upper = entered.upper()
    if upper in {item["code"] for item in master}:
        return upper
    lowered = entered.lower()
    for item in master:
        if item["name"].lower() == lowered or str(item["code"]).lower() == lowered:
            return item["code"]
    return None


def resolve_general_category(value):
    """Resolve a General Category value (code or public name) to a code.

    Returns None for anything that is not one of the 20 General Category
    options.
    """
    return _resolve(value, GENERAL_CATEGORIES)


def resolve_departmental_category(value):
    """Resolve a Departmental Category value (code or public name) to a code.

    Returns None for anything that is not one of the seven Departmental
    Category options.
    """
    return _resolve(value, DEPARTMENTAL_CATEGORIES)


def _join_public(names):
    return "; ".join(names)


def dimension_fields(department, categories):
    """Map an activity to its two public category fields.

    An institution-wide activity (normalised department ``General``) may carry
    a General Category; a department-specific activity may carry a Departmental
    Category.  Each field is the '; '-joined public names of the categories
    that belong to that dimension, or None when nothing applies.

    Returns (general_category, departmental_category).
    """
    dept = normalize_department(department) if department else GENERAL_NAME
    codes = {str(category.get("code", "")).upper() for category in (categories or [])}
    general_category = departmental_category = None
    if dept == GENERAL_NAME:
        selected = [public_category_name(code) for code in GENERAL_CATEGORY_ORDER if code in codes]
        if selected:
            general_category = _join_public(selected)
    else:
        selected = [public_category_name(code) for code in DEPARTMENTAL_CATEGORY_ORDER if code in codes]
        if selected:
            departmental_category = _join_public(selected)
    return general_category, departmental_category