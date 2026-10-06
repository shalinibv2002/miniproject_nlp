"""Category-specific report schemas: the ONE column definition for every report.

The 2026-10-03 category-wise audit (``data/audit/
category_wise_report_design_audit_20261003.json``) proved that the
Achievement/Award layout does not describe every activity.  ``Name`` and
``Achievement Description`` are only meaningful for ACHIEVEMENT; a workshop, a
sports meet or a club inauguration is described by its Title, Date, Academic
Year and source post.

This module is the single source of truth for those column sets:

  * ``report_columns(category, scope)``       - the columns for one category
  * ``report_columns_for_records(records)``   - the columns for a result set
  * ``report_schema_payload()``               - the JSON served to the UI

Every surface reads it: the report preview, the on-screen report table, the
XLSX/PDF exports and Ask-the-Data exports.  There is no second report format.

Design rules (from the task + audit):

  * Department appears ONLY in a departmental report, never in a general one --
    with one deliberate exception: the Alumni Meet Department column names the
    alumnus' own course and batch, which is part of the row's identity.
  * ``LinkedIn URL`` is always the trailing column: it is a read-only
    reference for validation, never a counting or classification input.
  * Missing or unreliable information stays blank.  Nothing is manufactured.
  * Columns are chosen per category only.  They never depend on how many
    stakeholder/department values an activity carries, so one activity is
    always exactly one report row.
  * Title-bearing columns hold ONLY the title: no dates, venues, participant
    counts, hashtags or promotional prose.  Explanatory text belongs to the
    matching Description column.
  * ``PLACEMENT`` is retired from the active taxonomy; its records are
    reclassified into the most accurate remaining category.
"""

GENERAL = "general"
DEPARTMENTAL = "departmental"
SCOPES = (GENERAL, DEPARTMENTAL)

# ``None`` is the serial number: it is generated at write time.
SNO = ("S.No", None)
TITLE = ("Title", "title")
STAKEHOLDER = ("Stakeholder", "stakeholder_display")
NAME = ("Name", "name")
DEPARTMENT = ("Department", "department_display")
AWARD_CATEGORY = ("Award Category", "award_category")
DESCRIPTION = ("Achievement Description", "achievement_description")
DATE = ("Date", "report_date")
ACADEMIC_YEAR = ("Academic Year", "academic_year_display")
LINKEDIN_URL = ("LinkedIn URL", "post_url")

# --- Columns required by the revised category contracts -------------------
# Every field below is DERIVED from the one canonical row (see
# ``backend/database/report_fields.py``); none of them is a new database column
# and none of them is composed prose.  A value that the source post does not
# state stays blank.
ALUMNI_NAME = ("Alumni Name", "alumni_name")
ALUMNI_DEPARTMENT = ("Department", "alumni_department")
TOPIC_THEME = ("Topic/Theme", "topic_theme")
CHIEF_GUEST = ("Chief Guest", "chief_guest")
TOPIC = ("Topic", "title")
SPEAKER = ("Speaker", "speaker")
EVENT_NAME = ("Event Name", "title")
EVENT_DESCRIPTION = ("Event Description", "event_description")
EVENT_DESCRIPTION_SHORT = ("Description", "event_description")
THEME_DESCRIPTION = ("Theme/Description", "event_description")
MOU_WITH = ("Signed MOU With", "mou_with")
PURPOSE = ("Purpose", "purpose")
DURATION = ("Duration", "duration")
DATE_RANGE = ("Date (From-To)", "date_range")
LOCATION = ("Location", "location")
RESEARCH_TOPIC = ("Research Topic", "title")
STAKEHOLDER_NAME = ("Stakeholder Name", "stakeholder_name")
SEMINAR_TITLE = ("Seminar Title", "title")

# Column widths, keyed by field, so a narrow schema never inherits the width of
# a column it does not have.
COLUMN_WIDTHS = {
    None: 8,
    "title": 46,
    "stakeholder_display": 20,
    "name": 28,
    "department_display": 26,
    "alumni_department": 26,
    "award_category": 22,
    "achievement_description": 62,
    "report_date": 16,
    "date_range": 26,
    "academic_year_display": 14,
    "post_url": 34,
    "alumni_name": 26,
    "topic_theme": 40,
    "chief_guest": 26,
    "speaker": 26,
    "event_description": 62,
    "mou_with": 32,
    "purpose": 46,
    "duration": 16,
    "location": 26,
    "stakeholder_name": 26,
}


def _activity(stakeholder=False, department=False):
    """Activity report: Title (+ Stakeholder, + Department when relevant)."""
    columns = [SNO, TITLE]
    if department:
        columns.append(DEPARTMENT)
    if stakeholder:
        columns.append(STAKEHOLDER)
    columns.extend((DATE, ACADEMIC_YEAR, LINKEDIN_URL))
    return columns


def _achievement(department=False):
    """The only schema with Name / Award Category / Achievement Description."""
    columns = [SNO, STAKEHOLDER, NAME]
    if department:
        columns.append(DEPARTMENT)
    columns.extend((AWARD_CATEGORY, DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL))
    return columns


# The general (institution-wide) activity layout.  Used for a category the
# audit did not customise and for a result set that mixes categories.
DEFAULT_GENERAL = _activity()
# The departmental activity layout: Department is mandatory here.
DEFAULT_DEPARTMENTAL = _activity(department=True)

# ---------------------------------------------------------------------------
# Per-category schemas.
#
# The fifteen categories below carry the revised column contract (Chief Guest,
# Speaker, Duration, Location, Signed MOU With, Purpose, Alumni Name,
# Topic/Theme, Event Description, ...).  Every other category keeps the audit
# layout it had.  ``PLACEMENT`` is no longer an active reporting category: its
# records are reclassified into the most accurate remaining category (see
# ``scripts/migrate_reportable_placement_dedup.py``).
# ---------------------------------------------------------------------------
_GENERAL_ACTIVITY = _activity()                      # no Stakeholder
_GENERAL_ACTIVITY_WITH_STAKEHOLDER = _activity(stakeholder=True)
_DEPARTMENTAL_ACTIVITY = _activity(department=True)
_DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER = _activity(stakeholder=True, department=True)

CATEGORY_SCHEMAS = {
    # --- revised contracts -------------------------------------------------
    # Alumni Meet: the alumnus and the batch they belonged to identify the
    # row, so Department is meaningful in the general report too.
    "ALUMNI": (
        [SNO, ALUMNI_NAME, ALUMNI_DEPARTMENT, TOPIC_THEME,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, ALUMNI_NAME, ALUMNI_DEPARTMENT, TOPIC_THEME,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "CONFERENCE": (
        [SNO, CHIEF_GUEST, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, CHIEF_GUEST, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "GUEST_LECTURE": (
        [SNO, TOPIC, SPEAKER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, TOPIC, SPEAKER, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "HACKATHON": (
        [SNO, TITLE, EVENT_DESCRIPTION, STAKEHOLDER,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, TITLE, EVENT_DESCRIPTION, DEPARTMENT, STAKEHOLDER,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "INDUSTRY": (
        [SNO, MOU_WITH, PURPOSE, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, DEPARTMENT, MOU_WITH, PURPOSE, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "INTERNSHIP": (
        [SNO, TITLE, DURATION, DATE_RANGE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, TITLE, DURATION, DEPARTMENT, DATE_RANGE,
         ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "NCC": (
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "NSS": (
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "ORIENTATION": (
        [SNO, EVENT_NAME, CHIEF_GUEST, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, EVENT_NAME, CHIEF_GUEST, DEPARTMENT,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "OUTREACH": (
        [SNO, TITLE, THEME_DESCRIPTION, LOCATION, DATE, ACADEMIC_YEAR,
         LINKEDIN_URL],
        [SNO, TITLE, THEME_DESCRIPTION, DEPARTMENT, LOCATION, DATE,
         ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "RESEARCH": (
        [SNO, RESEARCH_TOPIC, STAKEHOLDER, STAKEHOLDER_NAME,
         EVENT_DESCRIPTION_SHORT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, RESEARCH_TOPIC, STAKEHOLDER, STAKEHOLDER_NAME, DEPARTMENT,
         EVENT_DESCRIPTION_SHORT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "SEMINAR": (
        [SNO, SEMINAR_TITLE, EVENT_DESCRIPTION_SHORT, SPEAKER,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, SEMINAR_TITLE, EVENT_DESCRIPTION_SHORT, SPEAKER, DEPARTMENT,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "SPORTS": (
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "SYMPOSIUM": (
        [SNO, EVENT_NAME, EVENT_DESCRIPTION_SHORT, STAKEHOLDER,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, EVENT_NAME, EVENT_DESCRIPTION_SHORT, DEPARTMENT, STAKEHOLDER,
         DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    "WORKSHOP": (
        [SNO, TITLE, DURATION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
        [SNO, TITLE, DURATION, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    ),
    # --- unchanged audit layouts -------------------------------------------
    "FDP": (_GENERAL_ACTIVITY, _DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER),
    # Same story as SYMPOSIUM: reports like an FDP, taxonomy untouched.
    "STTP": (_GENERAL_ACTIVITY, _DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER),
    # The audit retires TECH_FEST from public reporting (2 records, 0% dates).
    # The code stays, so its existing records must still render: they fall back
    # to the plain activity layout rather than inventing achievement fields.
    "TECH_FEST": (DEFAULT_GENERAL, DEFAULT_DEPARTMENTAL),
    "CULTURAL": (_GENERAL_ACTIVITY_WITH_STAKEHOLDER, _DEPARTMENTAL_ACTIVITY),
    "CLUB": (_GENERAL_ACTIVITY_WITH_STAKEHOLDER, _DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER),
    "CAMPUS": (_GENERAL_ACTIVITY_WITH_STAKEHOLDER, _DEPARTMENTAL_ACTIVITY),
    "WEBINAR": (_GENERAL_ACTIVITY, _DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER),
    "ACHIEVEMENT": (_achievement(), _achievement(department=True)),
}

SCHEMA_CATEGORY_CODES = tuple(sorted(CATEGORY_SCHEMAS))

#: Categories that are no longer part of the active reporting taxonomy.  Their
#: codes stay readable so historical rows, exports and audits never crash, but
#: the migration guarantees no row carries one.
RETIRED_CATEGORY_CODES = ("PLACEMENT",)

# The audit recommendation the implementation deviates from, with the reason.
AUDIT_ALIGNMENT = {
    # ACHIEVEMENT: the audit's column list has no Date and calls the award
    # field "Award Title"; the delivered schema keeps a real Date column (blank
    # when unknown) and labels the field "Award Category".
    "ACHIEVEMENT": "Date column added; 'Award Title' reported as 'Award Category'.",
    # "Post URL" is delivered as "LinkedIn URL".
    "_url_label": "Audit's 'Post URL' is delivered as 'LinkedIn URL'.",
}

# The revised column contract, which supersedes the audit's ``recommended_columns``
# for these categories.  Recorded so the delivered schema can be diffed against
# the request without re-reading it.
SPEC_ALIGNMENT = {
    "ALUMNI": "Alumni Meet: Alumni Name, Department (CSE (2016 Batch) when the "
              "post states the batch), Topic/Theme, Date, Academic Year, URL.",
    "CONFERENCE": "Chief Guest, Organizing Department, Date, Academic Year, URL.",
    "GUEST_LECTURE": "Topic, Speaker, Department, Date, Academic Year, URL.",
    "HACKATHON": "Existing columns kept, Description added (~50 factual words).",
    "INDUSTRY": "No Title column: Signed MOU With and Purpose identify the row.",
    "INTERNSHIP": "Duration added; Date is reported as Date (From-To).",
    "NCC": "Event Name, Event Description, Date, Academic Year, URL.",
    "NSS": "Same layout as NCC; records are never merged between the two.",
    "ORIENTATION": "Event Name, Chief Guest, Department, Date, AY, URL.",
    "OUTREACH": "Theme/Description and Location added.",
    "RESEARCH": "Research Topic, Stakeholder, Stakeholder Name, Description.",
    "SEMINAR": "Seminar Title, Description, Speaker, Department.",
    "SPORTS": "Event Name, Event Description, Date, Academic Year, URL.",
    "SYMPOSIUM": "Event Name, Description, Department, Stakeholder.",
    "WORKSHOP": "Duration added; Stakeholder dropped.",
    "PLACEMENT": "Retired from the active taxonomy; records reclassified.",
}


def normalize_scope(scope=None, department=None):
    """Resolve the reporting scope.

    A request is departmental when it says so, or when it names a real
    department; everything else is a general (institution-wide) report.
    """
    value = (scope or "").strip().lower()
    if value in SCOPES:
        return value
    if value:
        raise ValueError("scope must be 'general' or 'departmental'")
    department = (department or "").strip()
    if department and department.lower() != "general":
        return DEPARTMENTAL
    return GENERAL


def normalize_category(category=None):
    """Upper-case a category code; empty/None means 'not category-specific'."""
    return (category or "").strip().upper() or None


def category_of_record(record):
    """The single primary category code of one projected record."""
    if not record:
        return None
    categories = record.get("categories") or []
    if categories:
        first = categories[0]
        if isinstance(first, dict):
            return normalize_category(first.get("code"))
        return normalize_category(first)
    return normalize_category(record.get("category_code"))


def report_columns(category=None, scope=None):
    """Report columns for one category in one scope.

    An unknown, missing or mixed category falls back to the plain activity
    layout for the requested scope, so a report always renders.
    """
    resolved = normalize_scope(scope)
    code = normalize_category(category)
    schema = CATEGORY_SCHEMAS.get(code)
    if schema is None:
        return list(DEFAULT_DEPARTMENTAL if resolved == DEPARTMENTAL else DEFAULT_GENERAL)
    return list(schema[0] if resolved == GENERAL else schema[1])


def report_columns_for_records(records, scope=None):
    """Columns for a result set.

    When every record shares one primary category (a category-filtered report)
    that category's schema is used.  A mixed result set uses the plain activity
    layout: one table has one column set, and no row is ever duplicated or
    dropped because of it.
    """
    codes = {category_of_record(record) for record in (records or [])}
    codes.discard(None)
    if len(codes) == 1:
        return report_columns(codes.pop(), scope)
    return report_columns(None, scope)


def column_labels(columns):
    return [label for label, _field in columns]


def column_widths(columns):
    return [COLUMN_WIDTHS.get(field, 20) for _label, field in columns]


#: Every projection key any schema can ask for.  The public/admin projections
#: and the export allow-lists are built from this, so a new column cannot be
#: added to a schema and then silently dropped on its way out.
ALL_REPORT_FIELDS = tuple(sorted(
    {field for _label, field in DEFAULT_GENERAL + DEFAULT_DEPARTMENTAL
     if field}
    | {field for schema in CATEGORY_SCHEMAS.values()
       for _label, field in schema[0] + schema[1] if field}
))


def report_schema_payload():
    """JSON payload describing every category schema (served to the UI)."""
    return {
        "default": {
            GENERAL: column_labels(DEFAULT_GENERAL),
            DEPARTMENTAL: column_labels(DEFAULT_DEPARTMENTAL),
        },
        "retired": list(RETIRED_CATEGORY_CODES),
        "categories": {
            code: {
                GENERAL: column_labels(schema[0]),
                DEPARTMENTAL: column_labels(schema[1]),
            }
            for code, schema in sorted(CATEGORY_SCHEMAS.items())
        },
    }