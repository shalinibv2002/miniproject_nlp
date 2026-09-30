"""Final LINKEDIN REPORTABLE dataset layer (dedicated, isolated dataset).

This module owns the FINAL reportable LinkedIn activity dataset in a dedicated
database (``linkedin_reportable.db``) that sits ABOVE the staging/audit layer:

    merged-workbook.xlsx
        -> linkedin_staging.db           (audit / source of truth)
        -> linkedin_activity_candidates  (validated classification)
        -> linkedin_reportable.db        (FINAL REPORTABLE dataset)   <-- here
        -> public/admin Flask API
        -> future public UI + Admin UI

HARD GUARANTEES (enforced by design):
  * Only ``linkedin_reportable.db`` is ever opened for writing.
  * ``linkedin_staging.db`` (linkedin_posts / linkedin_post_occurrences /
    linkedin_activity_candidates / linkedin_manual_review_proposals) is only
    ever READ, and never during a build are those tables modified.
  * ``linkedin_reportable.db`` is NOT the old website production database
    (``tce_activity_intelligence.db``); that database and the workbook are
    never touched.
  * Every canonical staging post receives exactly one final reportable row
    (1,544 rows).  Nothing is deleted and nothing is merged with the old
    2,258 website-derived activities.
  * Final status model: REPORTABLE | NON_ACTIVITY | REVIEW_REQUIRED.
      - REPORTABLE      -> ACTIVITY_CANDIDATE rows; the ONLY rows that enter
                           public reporting / analytics.
      - NON_ACTIVITY    -> communication / non-activity rows; traceable in
                           staging and in this layer, excluded from public
                           reporting.
      - REVIEW_REQUIRED -> uncertain rows; stay reviewable (never silently
                           promoted).  An admin PATCH can promote them; that
                           manual approval is recorded in validation_history.
  * Dates/academic years are NEVER invented:
      - activity_date  set ONLY when the post carries one explicit date
        (candidate date_status == 'dated') using its earliest explicit date.
      - academic_year  assigned ONLY when date_status == 'dated'
        (June 1 - May 31 convention).  Undated and ambiguous multi-year posts
        keep NULL dates/earning no academic year; the explicit date evidence
        is preserved in ``date_evidence`` for the admin layer.
  * Multi-label categories are preserved internally.  An activity with several
    categories is counted once in the unique total and once in each category it
    carries (documented counting semantics, tested).

Counting semantics (public consumers must rely on these):
  * unique_total_activities = COUNT(*) over reportable_status='REPORTABLE'.
  * category/department/stakeholder counts are OCCURRENCE counts: an activity
    carrying N categories contributes 1 to each of those N category counts.
  * The unique total is stable regardless of which filter is applied.
"""

import hashlib
import json
import os
import re
import sqlite3
from collections import Counter, OrderedDict
from datetime import datetime

from backend.database import category_catalog, department_catalog
from backend.database.linkedin_candidates import (
    CATEGORY_CANDIDATE_NAMES,
    CATEGORY_PATTERNS,
    FLAG_LINK_LESS,
    FLAG_PRE_2024,
    STAKEHOLDER_PUBLIC_NAMES,
    STATUS_ACTIVITY_CANDIDATE,
    STATUS_NON_ACTIVITY,
    STATUS_REVIEW_REQUIRED,
    WEAK_TEXT_LENGTH,
    _academic_year,
)
from backend.database.linkedin_staging import STAGING_DB_PATH

_HERE = os.path.dirname(os.path.abspath(__file__))
REPORTABLE_DB_PATH = os.path.join(_HERE, "linkedin_reportable.db")
DEFAULT_AUDIT_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "data", "audit"))
REPORT_BASENAME = "linkedin_final_reportable_dataset_20260923"
# Fallback provenance when a staging post predates the source_workbook column.
DEFAULT_SOURCE_WORKBOOK = "merged-workbook.xlsx"

# ---------------------------------------------------------------------------
# Final status vocabulary (maps 1:1 from the candidate status vocabulary).
# ---------------------------------------------------------------------------
REPORTABLE = "REPORTABLE"
NON_ACTIVITY = "NON_ACTIVITY"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
REPORTABLE_STATUSES = (REPORTABLE, NON_ACTIVITY, REVIEW_REQUIRED)

CANDIDATE_TO_REPORTABLE = {
    STATUS_ACTIVITY_CANDIDATE: REPORTABLE,
    STATUS_NON_ACTIVITY: NON_ACTIVITY,
    STATUS_REVIEW_REQUIRED: REVIEW_REQUIRED,
}

# Review statuses used by the admin validation layer.
REVIEW_UNREVIEWED = "UNREVIEWED"
REVIEW_NEEDS_REVIEW = "NEEDS_REVIEW"
REVIEW_APPROVED = "APPROVED"
REVIEW_STATUSES = (REVIEW_UNREVIEWED, REVIEW_NEEDS_REVIEW, REVIEW_APPROVED)

# Date-resolution statuses stored on every final row.
DATE_DATED = "dated"
DATE_UNDATED = "undated"
DATE_AMBIGUOUS = "ambiguous_multi_year"
DATE_STATUSES = (DATE_DATED, DATE_UNDATED, DATE_AMBIGUOUS)

# ---------------------------------------------------------------------------
# Vocabularies (validated during build and on admin edits).
# ---------------------------------------------------------------------------
FINAL_CATEGORY_CODES = frozenset(CATEGORY_PATTERNS)          # the 24 LinkedIn codes
FINAL_DEPARTMENTS = frozenset(
    (department_catalog.GENERAL_NAME,) + department_catalog.PUBLIC_DEPARTMENTS
)
FINAL_STAKEHOLDERS = frozenset(STAKEHOLDER_PUBLIC_NAMES)

# Public activity identity/classification fields.  Everything else is internal
# (evidence, scoring, heuristics, provenance pins, the raw LinkedIn post text)
# and admin-only.  ``summary`` is the concise, structured public description;
# the raw ``description`` never leaves the reportable table.
PUBLIC_FIELDS = (
    "activity_id", "title", "summary", "post_url", "activity_date",
    "academic_year", "category", "categories", "department", "departments",
    "stakeholder", "stakeholders", "source",
)

# Fields an admin PATCH may change (immutable provenance fields are excluded).
ADMIN_EDITABLE_FIELDS = (
    "title", "description", "categories", "departments", "stakeholders",
    "activity_date", "academic_year", "reportable_status", "review_status",
)

# Fields that must never change after a row is created (provenance/source).
IMMUTABLE_FIELDS = (
    "activity_id", "staging_post_id", "staging_candidate_id", "post_url",
    "activity_urn_id", "source", "source_workbook", "source_sheet",
    "source_row", "occurrence_count", "source_occurrence_ids",
    "collected_at", "resolved_via", "category_candidates",
    "department_candidates", "stakeholder_candidates", "department_display",
    "category_evidence", "department_evidence", "stakeholder_evidence",
    "communication_type", "communication_evidence", "evidence_score",
    "multi_label", "flags", "unclear_reason", "reason", "kind",
)

ACADEMIC_YEAR_RE = re.compile(r"^\d{4}-\d{2}$")
_WS_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+", re.I)
_HASH_RE = re.compile(r"^[#＃]")

# ---------------------------------------------------------------------------
# Schema for the final reportable dataset (a dedicated database).
# ---------------------------------------------------------------------------
REPORTABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS linkedin_reportable_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id TEXT NOT NULL UNIQUE,           -- public stable key 'LI-<id>'
    staging_post_id INTEGER NOT NULL UNIQUE,    -- linkedin_posts.id
    staging_candidate_id INTEGER,               -- linkedin_activity_candidates.id
    reportable_status TEXT NOT NULL
        CHECK (reportable_status IN ('REPORTABLE','NON_ACTIVITY','REVIEW_REQUIRED')),

    -- public identity / reporting fields
    title TEXT,
    description TEXT,
    post_url TEXT,
    activity_date TEXT,
    academic_year TEXT,
    categories TEXT,                            -- JSON [codes] (curated public list)
    departments TEXT,                           -- JSON [names] (RULE-09 display list)
    stakeholders TEXT,                          -- JSON [names]
    source TEXT NOT NULL DEFAULT 'TCE LinkedIn',
    date_status TEXT,                           -- 'dated'|'undated'|'ambiguous_multi_year'
    classification_status TEXT,                 -- 'AUTO_CLASSIFIED'|'PENDING_REVIEW'
    review_status TEXT NOT NULL DEFAULT 'UNREVIEWED'
        CHECK (review_status IN ('UNREVIEWED','NEEDS_REVIEW','APPROVED')),

    -- provenance (final record -> staging -> original Excel row)
    activity_urn_id TEXT,                       -- urn:li:activity:<id>
    source_workbook TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    source_row INTEGER,
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    source_occurrence_ids TEXT,                 -- JSON [occurrence ids]
    collected_at TEXT,
    resolved_via TEXT,

    -- admin / internal fields (NEVER exposed through public endpoints)
    kind TEXT,                                  -- step-2 screening bucket (internal)
    category_candidates TEXT,                   -- JSON [codes] (all evidence labels)
    department_candidates TEXT,                 -- JSON [names]
    stakeholder_candidates TEXT,                -- JSON [names]
    department_display TEXT,                    -- JSON [names] (RULE-09)
    date_evidence TEXT,                         -- JSON {source, dates, earliest, academic_year_evidence}
    category_evidence TEXT,                     -- JSON {code: [spans]}
    department_evidence TEXT,                   -- JSON {dept: [spans]}
    stakeholder_evidence TEXT,                  -- JSON {stakeholder: [spans]}
    communication_type TEXT,
    communication_evidence TEXT,
    evidence_score INTEGER NOT NULL DEFAULT 0,
    multi_label INTEGER NOT NULL DEFAULT 0,
    flags TEXT,                                 -- JSON [special-case flags]
    unclear_reason TEXT,
    reason TEXT,
    is_manually_validated INTEGER NOT NULL DEFAULT 0,
    manual_overrides TEXT,                      -- JSON {field: value} (admin edits)
    validation_history TEXT,                    -- JSON [ {field, old, new, by, at, note} ]
    built_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_reportable_activity
    ON linkedin_reportable_activities(activity_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_reportable_post
    ON linkedin_reportable_activities(staging_post_id);
CREATE INDEX IF NOT EXISTS idx_reportable_status
    ON linkedin_reportable_activities(reportable_status);
CREATE INDEX IF NOT EXISTS idx_reportable_ay
    ON linkedin_reportable_activities(academic_year);
CREATE INDEX IF NOT EXISTS idx_reportable_date
    ON linkedin_reportable_activities(activity_date);

-- normalized occurrence tables (REPORTABLE activities only).
-- Used by public filters + analytics; rebuilt on every build and admin edit.
CREATE TABLE IF NOT EXISTS linkedin_activity_categories (
    activity_id TEXT NOT NULL REFERENCES linkedin_reportable_activities(activity_id),
    category_code TEXT NOT NULL,
    PRIMARY KEY (activity_id, category_code)
);
CREATE TABLE IF NOT EXISTS linkedin_activity_departments (
    activity_id TEXT NOT NULL REFERENCES linkedin_reportable_activities(activity_id),
    department TEXT NOT NULL,
    PRIMARY KEY (activity_id, department)
);
CREATE TABLE IF NOT EXISTS linkedin_activity_stakeholders (
    activity_id TEXT NOT NULL REFERENCES linkedin_reportable_activities(activity_id),
    stakeholder TEXT NOT NULL,
    PRIMARY KEY (activity_id, stakeholder)
);
CREATE INDEX IF NOT EXISTS idx_lr_cat_code ON linkedin_activity_categories(category_code);
CREATE INDEX IF NOT EXISTS idx_lr_dept_name ON linkedin_activity_departments(department);
CREATE INDEX IF NOT EXISTS idx_lr_stak_name ON linkedin_activity_stakeholders(stakeholder);

CREATE TABLE IF NOT EXISTS build_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_reportable_connection(db_path=None):
    """Open a connection to the FINAL REPORTABLE database only."""
    path = db_path or REPORTABLE_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_reportable_schema(conn):
    conn.executescript(REPORTABLE_SCHEMA)
    conn.commit()


def _ro_staging(db_path):
    """Open the staging database READ-ONLY (never mutated by this layer)."""
    path = db_path or STAGING_DB_PATH
    conn = sqlite3.connect("file:%s?mode=ro" % path.replace("\\", "/"), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class WorkbookInventory:
    """Lightweight read-only inventory of the source workbook (path/hash/sheets).

    Never opens the workbook for writing.  Replaces an earlier dependency that
    did not exist in this repository.
    """

    def __init__(self, path=None):
        from backend.database.linkedin_staging import WORKBOOK_PATH
        self.path = path or WORKBOOK_PATH
        self.sha256 = None
        self.sheet_names = []
        if not os.path.exists(self.path):
            return
        self.sha256 = sha256_file(self.path)
        try:
            import openpyxl
            wb = openpyxl.load_workbook(self.path, read_only=True)
            self.sheet_names = list(wb.sheetnames)
            wb.close()
        except Exception:
            self.sheet_names = []


# ---------------------------------------------------------------------------
# Title / public value derivation (deterministic, non-destructive).
# ---------------------------------------------------------------------------
def derive_title(text, limit=140):
    """A readable title for an activity: a cleaned extract of the post text.

    This is an extract (never fabricated prose).  URLs, extra whitespace and
    leading hashtags are stripped; the first sentence is used, capped at
    ``limit`` characters.
    """
    s = _WS_RE.sub(" ", (text or "")).strip()
    s = _URL_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    s = _HASH_RE.sub("", s).strip().lstrip(":-–— ")
    if not s:
        return "Untitled LinkedIn post"
    m = re.split(r"(?<=[.!?])\s+", s, maxsplit=1)[0]
    candidate = m or s
    if len(candidate) <= limit:
        return candidate
    cut = candidate[:limit].rstrip(",;: ")
    return cut + "…"


# ---------------------------------------------------------------------------
# Public summary (STEP-11 rewrite): a structured report-style description of
# an activity, synthesised deterministically from the classified facts of the
# row (organising department, activity type, date, audience, award recipient).
#
# Reporting rules (honesty by construction):
#   * Only facts already classified on the row are asserted: departments,
#     stakeholders, date/academic-year and categories.
#   * The topic and any award recipient are EXTRACTED from the post text and
#     are optional — when they cannot be found the sentence is simply dropped,
#     the generator never invents prose.
#   * The raw LinkedIn post text is NEVER echoed verbatim; the summary reads
#     like a report ("The Department of Computer Applications (MCA) has
#     conducted a workshop on the topic "AI" on 15 January 2026 for students."),
#     not like the original post.
# ---------------------------------------------------------------------------
_SUMMARY_VERBS = {
    "WORKSHOP": ("conducted a workshop", "workshop"),
    "SEMINAR": ("delivered a seminar", "seminar"),
    "CONFERENCE": ("hosted a conference", "conference"),
    "SYMPOSIUM": ("hosted a symposium", "symposium"),
    "GUEST_LECTURE": ("arranged a guest lecture", "guest lecture"),
    "FDP": ("conducted a Faculty Development Programme", "programme"),
    "STTP": ("conducted a Short-Term Training Programme", "programme"),
    "HACKATHON": ("organised a hackathon", "hackathon"),
    "TECH_FEST": ("organised a technical festival", "technical festival"),
    "CULTURAL": ("organised a cultural event", "cultural event"),
    "SPORTS": ("organised a sports event", "sports event"),
    "NCC": ("conducted an NCC activity", "NCC activity"),
    "NSS": ("conducted an NSS activity", "NSS activity"),
    "CLUB": ("conducted a club activity", "club activity"),
    "OUTREACH": ("conducted an outreach activity", "outreach activity"),
    "INDUSTRY": ("held an industry collaboration programme", "industry programme"),
    "ACHIEVEMENT": ("celebrated an achievement", "achievement"),
    "PLACEMENT": ("organised a placement drive", "placement drive"),
    "INTERNSHIP": ("arranged an internship programme", "internship programme"),
    "RESEARCH": ("announced a research milestone", "research milestone"),
    "ALUMNI": ("hosted an alumni event", "alumni event"),
    "ORIENTATION": ("held an orientation programme", "orientation programme"),
    "CAMPUS": ("organised a campus event", "campus event"),
    "WEBINAR": ("delivered a webinar", "webinar"),
}
_SUMMARY_DEFAULT_VERB = ("organised an activity", "activity")
_SUMMARY_DEPT_ALIAS = {"Computer Applications": "Computer Applications (MCA)"}
_SUMMARY_NOISE_NAMES = {
    "the team", "our team", "the winner", "the winners", "the award",
    "the trophy", "the gold medal", "the medal", "the prize", "team",
    "student", "students", "department", "departments", "college",
    "college of engineering", "the college",
}
_QCHARS = "\u201c\u201d\u2018\u2019\"'`"
_QCH = re.escape(_QCHARS)
_SUMMARY_TOPIC_LEAD_RE = re.compile(
    r"\b(?:workshop|seminar|symposium|conference|webinar|programme|program|training|"
    r"session|hackathon|competition|championship|contest|fest(?:ival)?|drive|bootcamp|"
    r"lecture|camp|course|certification|meet|exhibition|talk|orientation|initiative)\b"
    r"\s+(?i:on|upon|about|titled|entitled)"
    r"(?:\s+(?i:the)\s+(?i:topic|theme|title|subject))?\s*(?:(?i:of|on)\s+)?", re.I)
_SUMMARY_TOPIC_TAIL_RE = re.compile(
    r"\s*([A-Za-z0-9&+.:/'%s-][A-Za-z0-9 &()+./:'%s-]{2,79}?)"
    r"(?=[%s]|\s*[,.!?;]|\s*(?i:at|for|by|with|on|from|whose|was|were|has|have|had)\b\s|"
    r"\s*(?i:organi[sz]ed|organi[sz]ing|hosted|held|planned|scheduled|commenced|"
    r"concluded|conducted|took place)\b\s|\s+$|$)"
    % ("\u2019", "\u2019", _QCH), re.I)
_SUMMARY_AWARDEE_AFTER_RE = re.compile(
    r"(?i:(?:awarded to|congratulations to|congratulate(?:s)?|felicitat(?:e|ed|es)|"
    r"honou?r(?:ed|ing)|honou?ree(?: of)?|recipient(?: of|:)|winner(?:s)?(?: of|:)|"
    r"given to|\bwon by))"
    r"\s+((?i:dr\.?|prof\.?|mr\.?|ms\.?|mrs\.?|er\.?)?(?:\s*[A-Z]\.)*\s*"
    r"[A-Z][a-zA-Z]{1,}(?:\s+[A-Z][a-zA-Z]{1,}){0,3})")
_SUMMARY_NAME_AWARD_VERB_RE = re.compile(
    r"((?i:dr\.?|prof\.?|mr\.?|ms\.?|mrs\.?|er\.?)(?:\s*[A-Z]\.)*\s+"
    r"[A-Z][a-zA-Z]{1,}(?:\s+[A-Z][a-zA-Z]{1,}){0,3})"
    r"\s+(?i:has been|have been|was|were)?\s*"
    r"(?i:felicitated|honou?red|awarded|won|bagged|secured|received|grabbed|bestowed)")
_SUMMARY_ACHIEVE_HINT_RE = re.compile(
    r"\b(?:won|bagged|secured|received|grabbed|awarded|recipient|selected|honou?red|"
    r"felicitated)\b", re.I)
_TOPIC_BAD_FRAG_RE = re.compile(
    r"(?i)^[a-z]['\u2019]?\s|,\s+(let|the|an?|of|to|in|on|for|with|and|a)\s*$")
_SUMMARY_EMOJI_RANGE = (
    list(range(0x1F000, 0x1FAFF + 1))   # emoji pictographs
    + list(range(0x2600, 0x27BF + 1))   # misc symbols / dingbats
    + list(range(0x1F1E6, 0x1F1FF + 1)) # regional indicators
)
_SUMMARY_EMOJI_RE = re.compile(
    "[" + "".join("\\U%08x" % cp for cp in _SUMMARY_EMOJI_RANGE) + "]", re.UNICODE)


def _row_get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except ValueError:
            return []
    return []


def _topic_ok(candidate):
    if not candidate or len(candidate) < 2 or not any(c.isalpha() for c in candidate):
        return False
    if _TOPIC_BAD_FRAG_RE.search(candidate):
        return False
    if len(candidate) < 4 and not candidate[0].isupper():
        return False
    return True


def _extract_topic(text, limit=70):
    """Extract the subject of an activity (e.g. "AI", "Generative AI") from the
    post text.  Returns None (never fabricates) when no topic can be found."""
    if not (text or "").strip():
        return None
    s = _WS_RE.sub(" ", _URL_RE.sub(" ", text or ""))
    s = _SUMMARY_EMOJI_RE.sub(" ", s)
    lead = _SUMMARY_TOPIC_LEAD_RE.search(s)
    if lead:
        body = s[lead.end():].lstrip(" \t" + _QCHARS)
        tail = _SUMMARY_TOPIC_TAIL_RE.match(body)
        if tail:
            candidate = tail.group(1)
        else:
            head = re.split(r"[.!,;?]|\s(?i:at|for|by|with|on|organi[sz]ed|organi[sz]ing)"
                            r"\b\s", body, maxsplit=1)[0]
            candidate = head
        candidate = _WS_RE.sub(" ", candidate).strip(" \t-–—" + _QCHARS)
        if _topic_ok(candidate.strip(" ,;:.-–—" + _QCHARS)):
            return candidate.strip(" ,;:.-–—" + _QCHARS)[:limit]
    for m in re.finditer(r"[%s]([A-Za-z0-9][^%s\n]{3,80})[%s]"
                         % (_QCH, _QCH, _QCH), s):
        candidate = _WS_RE.sub(" ", m.group(1)).strip(" ,;:.-–—" + _QCHARS)
        if _topic_ok(candidate) and not _SUMMARY_ACHIEVE_HINT_RE.search(candidate):
            return candidate[:limit]
    return None


def _extract_awardee(text):
    """Extract the person/team that received an award (e.g. "Dr. R. Meena").
    Only directly-named recipients are reported; None when unknown."""
    if not (text or "").strip():
        return None
    s = _WS_RE.sub(" ", text or "")
    for m in _SUMMARY_AWARDEE_AFTER_RE.finditer(s):
        name = _WS_RE.sub(" ", m.group(1)).strip(" .-–—")
        if name and name.lower() not in _SUMMARY_NOISE_NAMES and len(name) >= 3:
            return name
    m = _SUMMARY_NAME_AWARD_VERB_RE.search(s)
    if m:
        name = _WS_RE.sub(" ", m.group(1)).strip(" .-–—")
        if name and name.lower() not in _SUMMARY_NOISE_NAMES and len(name) >= 3:
            return name
    return None


def _organiser_phrase(depts):
    depts = [d for d in (_json_list(depts) or []) if d and d != "General"]
    if not depts:
        return "Thiagarajar College of Engineering", False
    cleaned = [_SUMMARY_DEPT_ALIAS.get(d, d) for d in depts]
    if len(cleaned) == 1:
        return "The Department of " + cleaned[0], False
    if len(cleaned) == 2:
        return "The Departments of %s and %s" % (cleaned[0], cleaned[1]), True
    return ("The Departments of %s and %s" % (", ".join(cleaned[:-1]), cleaned[-1]),
            True)


def _audience_phrase(staks):
    staks = [s for s in (_json_list(staks) or []) if s]
    if not staks:
        return None
    lowered = [s.lower() for s in staks]
    if len(lowered) == 1:
        return lowered[0]
    if len(lowered) == 2:
        return lowered[0] + " and " + lowered[1]
    return ", ".join(lowered[:-1]) + " and " + lowered[-1]


def _format_report_date(activity_date):
    if not activity_date:
        return None
    try:
        d = datetime.strptime(activity_date[:10], "%Y-%m-%d")
    except ValueError:
        return None
    return d.strftime("%d %B %Y").lstrip("0")


def derive_public_summary(row, limit=480):
    """A structured, report-style description of an activity for the public.

    Composes one factual sentence from the classification already on the row:
    who organised it, what happened + topic, when it happened, for whom, and
    (for award posts) who received the honour.  The raw LinkedIn post text is
    never included — nothing is invented, unknown facts (no topic/date/audience/
    awardee) simply shorten the report.
    """
    if not row:
        return "No activity recorded."
    codes = _json_list(_row_get(row, "categories"))
    kind_code = next((c for c in codes if c in _SUMMARY_VERBS), None)
    verb, _noun = (_SUMMARY_VERBS[kind_code] if kind_code else _SUMMARY_DEFAULT_VERB)

    subject, plural = _organiser_phrase(_row_get(row, "departments"))
    topic = _extract_topic(_row_get(row, "description")) if kind_code != "ACHIEVEMENT" else None
    date_text = _format_report_date(_row_get(row, "activity_date"))
    audience = _audience_phrase(_row_get(row, "stakeholders"))
    awardee = _extract_awardee(_row_get(row, "description")) if kind_code == "ACHIEVEMENT" else None

    clause = "on the topic \"%s\"" % topic if topic else None
    when = "on " + date_text if date_text else None
    aud = "for " + audience if audience else None
    tail = " ".join(x for x in (clause, when, aud) if x)

    helper = "have" if plural else "has"
    parts = ["%s %s %s%s." % (subject, helper, verb, " " + tail if tail else "")]
    if awardee:
        parts.append("The recognition was received by %s." % awardee)

    summary = " ".join(parts)
    if len(summary) > limit:
        return summary[:limit].rstrip(" ,;:") + "…"
    return summary


def primary_value(values, fallback=None):
    """First element of a display list (headline value), else fallback."""
    if not values:
        return fallback
    return values[0]


def _clean_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


# ---------------------------------------------------------------------------
# Vocabulary validation helpers (shared by build + admin edits).
# ---------------------------------------------------------------------------
def validate_categories(codes):
    codes = _clean_list(codes)
    bad = [c for c in codes if c not in FINAL_CATEGORY_CODES]
    if bad:
        raise ValueError("invalid category codes: %s" % sorted(bad))
    return codes


def validate_departments(names):
    names = _clean_list(names)
    bad = [n for n in names if n not in FINAL_DEPARTMENTS]
    if bad:
        raise ValueError(
            "invalid department names (must be a public department or 'General'): %s" % bad)
    return names


def validate_stakeholders(names):
    names = _clean_list(names)
    bad = [n for n in names if n not in FINAL_STAKEHOLDERS]
    if bad:
        raise ValueError("invalid stakeholder names: %s" % bad)
    return names


def validate_academic_year(value):
    if value is None or value == "":
        return None
    if not ACADEMIC_YEAR_RE.match(str(value)):
        raise ValueError("academic_year must look like '2025-26'")
    return str(value)


# ---------------------------------------------------------------------------
# Final row derivation from a staging candidate row (the ONLY translation step).
# ---------------------------------------------------------------------------
def _candidate_json(row, key):
    raw = row[key] if key in row.keys() else None
    if not raw:
        return [] if key.endswith("_candidates") or key in (
            "categories", "departments", "stakeholders", "flags") else None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return raw


def derive_final_row(post, candidate, occurrence_ids, occurrence_count):
    """Map one canonical post + candidate to a final reportable row dict."""
    activity_id = "LI-%05d" % post["id"]
    pid = post["id"]
    cand_status = candidate["candidate_status"]
    reportable_status = CANDIDATE_TO_REPORTABLE.get(cand_status, REVIEW_REQUIRED)

    date_status = candidate["date_status"] or "undated"
    date_evidence = _candidate_json(candidate, "date_evidence") or {}
    explicit_dates = date_evidence.get("dates") or []
    earliest = date_evidence.get("earliest")

    # A date/academic year is reportable ONLY when a single explicit date exists.
    if date_status == "dated" and earliest:
        activity_date = earliest
        y, m = int(earliest[:4]), int(earliest[5:7])
        academic_year = _academic_year(y, m)
    else:
        activity_date = None
        academic_year = None

    categories = _candidate_json(candidate, "category_candidates") or []
    categories = [c for c in categories]  # curated list already reflects RULE-08

    # RULE-09 display list: explicit-organizer departments or ["General"].
    departments = [d for d in (_candidate_json(candidate, "department_display") or [])]
    stakeholders = _candidate_json(candidate, "stakeholder_candidates") or []

    flags = _candidate_json(candidate, "flags") or []
    classification_status = candidate["review_status"] or "AUTO_CLASSIFIED"
    review_status = REVIEW_UNREVIEWED
    if classification_status == "PENDING_REVIEW":
        review_status = REVIEW_NEEDS_REVIEW

    return {
        "activity_id": activity_id,
        "staging_post_id": pid,
        "staging_candidate_id": candidate["id"],
        "reportable_status": reportable_status,
        "title": derive_title(post["post_text"]),
        "description": post["post_text"],
        "post_url": post["post_url"],
        "activity_date": activity_date,
        "academic_year": academic_year,
        "categories": categories,
        "departments": departments,
        "stakeholders": stakeholders,
        "source": "TCE LinkedIn",
        "date_status": date_status,
        "classification_status": classification_status,
        "review_status": review_status,
        "activity_urn_id": post["activity_id"],
        "source_workbook": _post_workbook(post),
        "source_sheet": post["source_sheet"],
        "source_row": post["source_row"],
        "occurrence_count": occurrence_count,
        "source_occurrence_ids": occurrence_ids,
        "collected_at": post["collected_at"],
        "resolved_via": post["resolved_via"],
        "kind": candidate["kind"],
        "category_candidates": _candidate_json(candidate, "category_candidates") or [],
        "department_candidates": _candidate_json(candidate, "department_candidates") or [],
        "stakeholder_candidates": _candidate_json(candidate, "stakeholder_candidates") or [],
        "department_display": [d for d in (_candidate_json(candidate, "department_display") or [])],
        "date_evidence": {
            "source": date_evidence.get("source", "explicit_text"),
            "dates": explicit_dates,
            "earliest": earliest,
            "academic_year_evidence": _candidate_json(
                candidate, "academic_year") if False else _candidate_ay(candidate),
        },
        "category_evidence": _candidate_json(candidate, "category_evidence") or {},
        "department_evidence": _candidate_json(candidate, "department_evidence") or {},
        "stakeholder_evidence": _candidate_json(candidate, "stakeholder_evidence") or {},
        "communication_type": candidate["communication_type"],
        "communication_evidence": _candidate_json(candidate, "communication_evidence") or {},
        "evidence_score": candidate["evidence_score"],
        "multi_label": candidate["multi_label"],
        "flags": flags,
        "unclear_reason": candidate["unclear_reason"],
        "reason": candidate["reason"],
        "is_manually_validated": 0,
        "manual_overrides": {},
        "validation_history": [],
        "date_evidence_flags": _date_evidence_flags(flags),
    }


def _post_workbook(post):
    """Source workbook of a staging post.

    Reads the staging provenance column added by the incremental importer and
    falls back to the historical default, so an older staging database without
    the column keeps producing the previous behaviour.
    """
    try:
        value = post["source_workbook"] if "source_workbook" in post.keys() else None
    except (AttributeError, TypeError):
        value = None
    return value or DEFAULT_SOURCE_WORKBOOK


def _candidate_ay(candidate):
    """Candidate-level academic year (used as admin evidence only)."""
    try:
        return candidate["academic_year"]
    except (IndexError, KeyError):
        return None


def _date_evidence_flags(flags):
    """Derive admin date-issue signals from candidate flags."""
    return {
        "pre_2024": FLAG_PRE_2024 in (flags or []),
        "link_less": FLAG_LINK_LESS in (flags or []),
    }


# ---------------------------------------------------------------------------
# UPSERT + normalized table maintenance
# ---------------------------------------------------------------------------
def _upsert_final_row(conn, row):
    conn.execute(
        """INSERT INTO linkedin_reportable_activities
           (activity_id, staging_post_id, staging_candidate_id, reportable_status,
            title, description, post_url, activity_date, academic_year,
            categories, departments, stakeholders, source, date_status,
            classification_status, review_status,
            activity_urn_id, source_workbook, source_sheet, source_row,
            occurrence_count, source_occurrence_ids, collected_at, resolved_via,
            kind, category_candidates, department_candidates, stakeholder_candidates,
            department_display, date_evidence, category_evidence,
            department_evidence, stakeholder_evidence, communication_type,
            communication_evidence, evidence_score, multi_label, flags,
            unclear_reason, reason, is_manually_validated, manual_overrides,
            validation_history, built_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))
           ON CONFLICT(staging_post_id) DO UPDATE SET
            staging_candidate_id=excluded.staging_candidate_id,
            reportable_status=excluded.reportable_status,
            title=excluded.title, description=excluded.description,
            post_url=excluded.post_url, activity_date=excluded.activity_date,
            academic_year=excluded.academic_year, categories=excluded.categories,
            departments=excluded.departments, stakeholders=excluded.stakeholders,
            date_status=excluded.date_status,
            classification_status=excluded.classification_status,
            activity_urn_id=excluded.activity_urn_id,
            source_sheet=excluded.source_sheet, source_row=excluded.source_row,
            occurrence_count=excluded.occurrence_count,
            source_occurrence_ids=excluded.source_occurrence_ids,
            collected_at=excluded.collected_at, resolved_via=excluded.resolved_via,
            kind=excluded.kind, category_candidates=excluded.category_candidates,
            department_candidates=excluded.department_candidates,
            stakeholder_candidates=excluded.stakeholder_candidates,
            department_display=excluded.department_display,
            date_evidence=excluded.date_evidence,
            category_evidence=excluded.category_evidence,
            department_evidence=excluded.department_evidence,
            stakeholder_evidence=excluded.stakeholder_evidence,
            communication_type=excluded.communication_type,
            communication_evidence=excluded.communication_evidence,
            evidence_score=excluded.evidence_score, multi_label=excluded.multi_label,
            flags=excluded.flags, unclear_reason=excluded.unclear_reason,
            reason=excluded.reason, updated_at=datetime('now')""",
        (
            row["activity_id"], row["staging_post_id"], row["staging_candidate_id"],
            row["reportable_status"], row["title"], row["description"],
            row["post_url"], row["activity_date"], row["academic_year"],
            json.dumps(row["categories"]), json.dumps(row["departments"]),
            json.dumps(row["stakeholders"]), row["source"], row["date_status"],
            row["classification_status"], row["review_status"],
            row["activity_urn_id"], row["source_workbook"], row["source_sheet"],
            row["source_row"], row["occurrence_count"],
            json.dumps(row["source_occurrence_ids"]), row["collected_at"],
            row["resolved_via"], row["kind"], json.dumps(row["category_candidates"]),
            json.dumps(row["department_candidates"]),
            json.dumps(row["stakeholder_candidates"]),
            json.dumps(row["department_display"]), json.dumps(row["date_evidence"]),
            json.dumps(row["category_evidence"]), json.dumps(row["department_evidence"]),
            json.dumps(row["stakeholder_evidence"]), row["communication_type"],
            json.dumps(row["communication_evidence"]), row["evidence_score"],
            row["multi_label"], json.dumps(row["flags"]), row["unclear_reason"],
            row["reason"], row["is_manually_validated"],
            json.dumps(row["manual_overrides"]), json.dumps(row["validation_history"]),
        ),
    )


def refresh_normalized(conn, activity_id=None):
    """Rebuild the three normalized occurrence tables from REPORTABLE rows.

    Only REPORTABLE activities participate in public analytics.  Pass
    ``activity_id`` to refresh a single row (after an admin edit), otherwise all
    rows are rebuilt from the selected JSON lists.
    """
    if activity_id is None:
        conn.execute("DELETE FROM linkedin_activity_stakeholders")
        conn.execute("DELETE FROM linkedin_activity_departments")
        conn.execute("DELETE FROM linkedin_activity_categories")
        row_ids = None
    else:
        row_ids = (activity_id,)
    if row_ids is None:
        rows = conn.execute(
            "SELECT activity_id, categories, departments, stakeholders "
            "FROM linkedin_reportable_activities WHERE reportable_status=?",
            (REPORTABLE,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT activity_id, categories, departments, stakeholders "
            "FROM linkedin_reportable_activities "
            "WHERE activity_id=? AND reportable_status=?",
            (activity_id, REPORTABLE),
        ).fetchall()
    for row in rows:
        for code in (json.loads(row["categories"]) if row["categories"] else []):
            conn.execute(
                "INSERT OR IGNORE INTO linkedin_activity_categories (activity_id, category_code) "
                "VALUES (?, ?)", (row["activity_id"], code))
        for dept in (json.loads(row["departments"]) if row["departments"] else []):
            conn.execute(
                "INSERT OR IGNORE INTO linkedin_activity_departments (activity_id, department) "
                "VALUES (?, ?)", (row["activity_id"], dept))
        for stak in (json.loads(row["stakeholders"]) if row["stakeholders"] else []):
            conn.execute(
                "INSERT OR IGNORE INTO linkedin_activity_stakeholders (activity_id, stakeholder) "
                "VALUES (?, ?)", (row["activity_id"], stak))


def _preserve_overrides(existing, row):
    """Re-apply admin edits from a previous build onto a fresh computed row."""
    if not existing:
        return row
    overrides = json.loads(existing["manual_overrides"]) if existing["manual_overrides"] else {}
    if overrides:
        for field, value in overrides.items():
            if field in ("title", "description"):
                row[field] = value
            elif field in ("categories", "departments", "stakeholders"):
                row[field] = list(value)
            elif field in ("activity_date", "academic_year"):
                row[field] = value
            elif field == "reportable_status":
                row["reportable_status"] = value
            elif field == "review_status":
                row["review_status"] = value
    if existing["is_manually_validated"]:
        row["is_manually_validated"] = existing["is_manually_validated"]
    if existing["validation_history"]:
        row["validation_history"] = json.loads(existing["validation_history"])
    row["review_status"] = existing["review_status"] or row["review_status"]
    return row


# ---------------------------------------------------------------------------
# Build / refresh (deterministic, idempotent, provenance-preserving)
# ---------------------------------------------------------------------------
EXPECTED_STAGING = {
    "posts": 1544, "occurrences": 2094, "candidates": 1544,
}


def _read_posts(conn):
    """Read canonical staging posts, with the source_workbook column if present.

    Staging databases created before the incremental importer have no
    ``source_workbook`` column; the read falls back to the historical column
    list so the build keeps working unchanged.
    """
    base = ("id, post_url, activity_id, post_text, source_sheet, source_row, "
            "collected_at, resolved_via")
    try:
        return conn.execute(
            "SELECT " + base + ", source_workbook FROM linkedin_posts ORDER BY id"
        ).fetchall()
    except sqlite3.OperationalError:
        return conn.execute(
            "SELECT " + base + " FROM linkedin_posts ORDER BY id").fetchall()


def _read_staging(conn):
    occurrences = {}
    for r in conn.execute(
            "SELECT id, linkedin_post_id FROM linkedin_post_occurrences "
            "ORDER BY id").fetchall():
        occurrences.setdefault(r["linkedin_post_id"], []).append(r["id"])

    posts = _read_posts(conn)
    candidates = conn.execute(
        "SELECT * FROM linkedin_activity_candidates ORDER BY linkedin_post_id").fetchall()
    by_post = {r["linkedin_post_id"]: r for r in candidates}
    return posts, candidates, occurrences, by_post


def build_reportable_dataset(staging_db_path=None, reportable_db_path=None,
                             audit_dir=None, preserve_overrides=True):
    """Deterministically rebuild the FINAL REPORTABLE dataset.

    Reads the staging layer read-only, writes ONLY the reportable database, and
    returns a build/audit summary dict.  Safe to run repeatedly: final rows are
    upserted by staging_post_id (no duplicates) and admin edits are re-applied
    when ``preserve_overrides`` is True.
    """
    reportable_path = reportable_db_path or REPORTABLE_DB_PATH
    staging_ro = _ro_staging(staging_db_path)
    conn = get_reportable_connection(reportable_path)
    try:
        posts, candidates, occurrences, by_post = _read_staging(staging_ro)
        init_reportable_schema(conn)
        # preserve existing admin state (overrides + validation history)
        existing = {}
        if preserve_overrides:
            existing = {
                r["staging_post_id"]: r
                for r in conn.execute(
                    "SELECT staging_post_id, manual_overrides, is_manually_validated, "
                    "validation_history, review_status FROM linkedin_reportable_activities"
                ).fetchall()
            }

        rows = []
        for post in posts:
            candidate = by_post.get(post["id"])
            if candidate is None:
                raise RuntimeError(
                    "staging post %d has no candidate row; run generate_candidates first"
                    % post["id"])
            occ_ids = occurrences.get(post["id"], [])
            row = derive_final_row(post, candidate, occ_ids, len(occ_ids))
            if preserve_overrides:
                row = _preserve_overrides(existing.get(post["id"]), row)
            _upsert_final_row(conn, row)
            rows.append(row)
        refresh_normalized(conn)

        workbook = WorkbookInventory()
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('built_at', ?)",
            (datetime.now().isoformat(timespec="seconds"),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('source_rows', ?)",
            (str(len(rows)),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('workbook_sha256', ?)",
            (workbook.sha256,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('workbook_path', ?)",
            (workbook.path,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('source_workbooks', ?)",
            (json.dumps(_contributing_workbooks(conn)),),
        )
        conn.commit()

        summary = build_audit_summary(conn, rows, staging_ro, workbook)
        if audit_dir is not None:
            write_audit_report(summary, out_dir=audit_dir)
        return summary
    finally:
        conn.close()
        staging_ro.close()


# ---------------------------------------------------------------------------
# Audit / integrity summary
# ---------------------------------------------------------------------------
def _contributing_workbooks(conn):
    """Per-source-workbook row counts of the current reportable dataset.

    Keeps every incremental source traceable from the reportable layer alone.
    """
    rows = conn.execute(
        "SELECT source_workbook, source_sheet, COUNT(*) AS n "
        "FROM linkedin_reportable_activities GROUP BY source_workbook, source_sheet "
        "ORDER BY source_workbook, source_sheet").fetchall()
    out = OrderedDict()
    for r in rows:
        book = r["source_workbook"] or DEFAULT_SOURCE_WORKBOOK
        entry = out.setdefault(book, {"rows": 0, "sheets": {}})
        entry["rows"] += r["n"]
        entry["sheets"][r["source_sheet"]] = r["n"]
    return out


def build_audit_summary(conn, rows, staging_ro, workbook=None):
    def count_of(pred):
        return sum(1 for r in rows if pred(r))

    counts = Counter(r["reportable_status"] for r in rows)
    cat_occ = Counter()
    dept_occ = Counter()
    stak_occ = Counter()
    ay_occ = Counter()
    dated = {"dated": 0, "undated": 0, "ambiguous_multi_year": 0}
    url_ok = 0
    flags = Counter()
    source_sheet = Counter()
    for r in rows:
        if r["reportable_status"] == REPORTABLE:
            for c in r["categories"]:
                cat_occ[c] += 1
            for d in r["departments"]:
                dept_occ[d] += 1
            for s in r["stakeholders"]:
                stak_occ[s] += 1
            if r["academic_year"]:
                ay_occ[r["academic_year"]] += 1
        if r["date_status"] in dated:
            dated[r["date_status"]] += 1
        if r["post_url"]:
            url_ok += 1
        source_sheet[r["source_sheet"]] += 1
        for f in (r["flags"] or []):
            flags[f] += 1

    # integrity
    invalid_categories = sorted({c for r in rows if r["reportable_status"] == REPORTABLE
                                 for c in r["categories"] if c not in FINAL_CATEGORY_CODES})
    invalid_departments = sorted({d for r in rows if r["reportable_status"] == REPORTABLE
                                  for d in r["departments"] if d not in FINAL_DEPARTMENTS})
    invalid_stakeholders = sorted({s for r in rows if r["reportable_status"] == REPORTABLE
                                   for s in r["stakeholders"] if s not in FINAL_STAKEHOLDERS})
    invalid_ays = sorted({r["academic_year"] for r in rows
                          if r["academic_year"] and not ACADEMIC_YEAR_RE.match(r["academic_year"])})
    duplicate_ids = len(rows) - len({r["activity_id"] for r in rows})

    staging_stats = {
        "posts": len(rows),
        "occurrences": sum(r["occurrence_count"] for r in rows),
        "candidates": len(rows),
        "pending_review": count_of(lambda r: r["classification_status"] == "PENDING_REVIEW"),
        "expected": dict(EXPECTED_STAGING),
    }

    month_occ = Counter()
    for r in rows:
        if r["reportable_status"] == REPORTABLE and r["activity_date"]:
            month_occ[r["activity_date"][:7]] += 1

    summary = {
        "meta": {
            "title": "Final LinkedIn Reportable Dataset",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "database": "backend/database/linkedin_reportable.db",
            "scope": "canonical LinkedIn posts only; never merged with the 2,258 website activities",
        },
        "source": {
            "workbook": workbook.path if workbook else "merged-workbook.xlsx",
            "workbook_sha256": workbook.sha256 if workbook else None,
            "sheets": workbook.sheet_names if workbook else [],
            "raw_rows": staging_stats["occurrences"],
        },
        "staging": {
            "canonical_posts": staging_stats["posts"],
            "duplicate_occurrences": staging_stats["occurrences"] - staging_stats["posts"],
            "candidates": staging_stats["candidates"],
            "pending_review_sample": staging_stats["pending_review"],
            "expected": staging_stats["expected"],
        },
        "classification": {
            "by_status": dict(counts),
            "reportable": counts.get(REPORTABLE, 0),
            "non_activity": counts.get(NON_ACTIVITY, 0),
            "review_required": counts.get(REVIEW_REQUIRED, 0),
            "category_occurrences": dict(sorted(cat_occ.items(), key=lambda kv: (-kv[1], kv[0]))),
            "department_occurrences": dict(sorted(dept_occ.items(), key=lambda kv: (-kv[1], kv[0]))),
            "stakeholder_occurrences": dict(sorted(stak_occ.items(), key=lambda kv: (-kv[1], kv[0]))),
        },
        "dates": {
            "dated": dated["dated"],
            "undated": dated["undated"],
            "ambiguous_multi_year": dated["ambiguous_multi_year"],
            "convention": "academic_year assigned ONLY for single explicit dates; "
                          "June 1 - May 31; no invented dates/years.",
            "academic_year_distribution": dict(sorted(ay_occ.items())),
            "by_month_reportable": dict(sorted(month_occ.items())),
        },
        "provenance": {
            "url_verified": url_ok,
            "link_less": staging_stats["posts"] - url_ok,
            "url_coverage_pct": round(100.0 * url_ok / staging_stats["posts"], 2)
                                if staging_stats["posts"] else 0.0,
            "source_sheet_distribution": dict(sorted(source_sheet.items())),
            "occurrence_counts": {
                "single_occurrence_posts": sum(1 for r in rows if r["occurrence_count"] == 1),
                "multi_occurrence_posts": sum(1 for r in rows if r["occurrence_count"] > 1),
            },
        },
        "integrity": {
            "no_duplicate_final_ids": duplicate_ids == 0,
            "no_invalid_categories": not invalid_categories,
            "no_invalid_departments": not invalid_departments,
            "no_invalid_stakeholders": not invalid_stakeholders,
            "no_invalid_academic_years": not invalid_ays,
            "all_traceable": all(r["staging_post_id"] for r in rows),
            "invalid_category_values": invalid_categories,
            "invalid_department_values": invalid_departments,
            "invalid_stakeholder_values": invalid_stakeholders,
            "invalid_academic_years": invalid_ays,
            "duplicate_id_count": duplicate_ids,
        },
        "build": {
            "mode": "upsert by staging_post_id (idempotent)",
            "admin_overrides_preserved": preserve_overrides if "preserve_overrides" in vars() else None,
            "flags": dict(sorted(flags.items(), key=lambda kv: (-kv[1], kv[0]))),
        },
    }
    return summary


def write_audit_report(summary, out_dir=None):
    """Write MD + JSON audit reports (return the paths)."""
    out_dir = out_dir or DEFAULT_AUDIT_DIR
    os.makedirs(out_dir, exist_ok=True)
    md_path = os.path.join(out_dir, REPORT_BASENAME + ".md")
    json_path = os.path.join(out_dir, REPORT_BASENAME + ".json")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    cls = summary["classification"]
    stg = summary["staging"]
    src = summary["source"]
    dt = summary["dates"]
    prov = summary["provenance"]
    integ = summary["integrity"]

    with open(md_path, "w", encoding="utf-8") as f:
        w = f.write
        w("# Final LinkedIn Reportable Dataset — Audit Report\n\n")
        w("- Generated: %s\n" % summary["meta"]["generated_at"])
        w("- Database: `%s`\n" % summary["meta"]["database"])
        w("- Scope: %s\n\n" % summary["meta"]["scope"])
        w("## Source\n\n")
        w("- Workbook: `%s`\n" % src["workbook"])
        w("- Workbook SHA-256: `%s`\n" % src["workbook_sha256"])
        w("- Sheets: %s\n" % ", ".join(src["sheets"]))
        w("- Raw workbook rows: %s\n\n" % src["raw_rows"])
        w("## Staging\n\n")
        w("- Canonical posts: %s\n" % stg["canonical_posts"])
        w("- Duplicate occurrences: %s\n" % stg["duplicate_occurrences"])
        w("- Candidates: %s\n" % stg["candidates"])
        w("- PENDING_REVIEW sample: %s\n\n" % stg["pending_review_sample"])
        w("## Classification (final reportable status)\n\n")
        w("| Status | Count |\n|---|---|\n")
        for status in ("REPORTABLE", "NON_ACTIVITY", "REVIEW_REQUIRED"):
            w("| %s | %s |\n" % (status, cls["by_status"].get(status, 0)))
        w("\n### Category occurrence counts (REPORTABLE only)\n\n")
        for k, v in cls["category_occurrences"].items():
            w("- %s: %d\n" % (k, v))
        w("\n### Department occurrence counts (REPORTABLE only)\n\n")
        for k, v in cls["department_occurrences"].items():
            w("- %s: %d\n" % (k, v))
        w("\n### Stakeholder occurrence counts (REPORTABLE only)\n\n")
        for k, v in cls["stakeholder_occurrences"].items():
            w("- %s: %d\n" % (k, v))
        w("\n## Dates\n\n")
        w("- dated: %d\n" % dt["dated"])
        w("- undated: %d\n" % dt["undated"])
        w("- ambiguous multi-year: %d\n" % dt["ambiguous_multi_year"])
        w("- Convention: %s\n" % dt["convention"])
        w("\nAcademic-year distribution (reportable only):\n\n")
        if dt["academic_year_distribution"]:
            for k, v in dt["academic_year_distribution"].items():
                w("- %s: %d\n" % (k, v))
        else:
            w("- (none)\n")
        w("\nReportable activities by month (reliable dates only):\n\n")
        for k, v in dt["by_month_reportable"].items():
            w("- %s: %d\n" % (k, v))
        w("\n## Provenance\n\n")
        w("- URL-verified posts: %d\n" % prov["url_verified"])
        w("- Link-less posts: %d\n" % prov["link_less"])
        w("- URL coverage: %.2f%%\n" % prov["url_coverage_pct"])
        w("- Source sheet distribution:\n")
        for k, v in prov["source_sheet_distribution"].items():
            w("  - %s: %d\n" % (k, v))
        w("- Occurrences: single=%d multi=%d\n\n" % (
            prov["occurrence_counts"]["single_occurrence_posts"],
            prov["occurrence_counts"]["multi_occurrence_posts"]))
        w("## Integrity\n\n")
        for key, label in (
            ("no_duplicate_final_ids", "No duplicate final activity IDs"),
            ("no_invalid_categories", "No invalid categories"),
            ("no_invalid_departments", "No invalid departments"),
            ("no_invalid_stakeholders", "No invalid stakeholders"),
            ("no_invalid_academic_years", "No impossible academic years"),
            ("all_traceable", "All final records traceable to staging"),
        ):
            w("- %s: **%s**\n" % (label, integ[key]))
        w("\n## Counting semantics\n\n")
        w("- `unique total activities` = REPORTABLE rows (stable regardless of filters).\n")
        w("- category / department / stakeholder counts are OCCURRENCE counts;\n")
        w("  an activity carrying N categories counts once in each of those N buckets.\n")
        w("- The public dashboard total, filtered lists and every analytics endpoint are\n")
        w("  computed from this same dataset.\n")
    return md_path, json_path


# ---------------------------------------------------------------------------
# Public query helpers (single query-builder shared by list + analytics, so the
# dashboard total and every filtered/analytic count can never diverge).
# ---------------------------------------------------------------------------
class ReportableFilters:
    """Build a WHERE clause over the reportable table (alias ``r``)."""

    def __init__(self, args):
        self.args = args or {}
        self.clauses = []
        self.params = []

    def _get(self, *keys):
        for key in keys:
            value = (self.args.get(key) or "").strip()
            if value:
                return value
        return None

    def _add(self, clause, *params):
        self.clauses.append(clause)
        self.params.extend(params)

    def apply(self):
        args = self.args
        status = self._get("status", "reportable_status")
        if status is None:
            status = REPORTABLE
        if status.upper() == "ALL":
            pass  # admin convenience: no status restriction
        elif status not in REPORTABLE_STATUSES:
            raise ValueError("status must be one of: %s" % ", ".join(REPORTABLE_STATUSES))
        else:
            self._add("r.reportable_status = ?", status)

        review_status = self._get("review_status")
        if review_status:
            if review_status not in REVIEW_STATUSES:
                raise ValueError("review_status must be one of: %s"
                                 % ", ".join(REVIEW_STATUSES))
            self._add("r.review_status = ?", review_status)

        date_status = self._get("date_status", "date")
        if date_status:
            if date_status not in DATE_STATUSES:
                raise ValueError("date_status must be one of: %s"
                                 % ", ".join(DATE_STATUSES))
            self._add("r.date_status = ?", date_status)

        confidence = self._get("confidence")
        if confidence:
            if confidence not in ("low", "medium", "high"):
                raise ValueError("confidence must be low|medium|high")
            if confidence == "low":
                self._add("r.evidence_score <= 4")
            elif confidence == "high":
                self._add("r.evidence_score >= 8")
            else:
                self._add("r.evidence_score BETWEEN 4 AND 7")

        academic_year = self._get("academic_year", "year")
        if academic_year:
            if not ACADEMIC_YEAR_RE.match(academic_year):
                raise ValueError("academic_year must look like '2025-26'")
            self._add("r.academic_year = ?", academic_year)

        from_year = self._get("from_year")
        if from_year:
            if not ACADEMIC_YEAR_RE.match(from_year):
                raise ValueError("from_year must look like '2025-26'")
            self._add("CAST(substr(r.academic_year, 1, 4) AS INTEGER) >= ?",
                      int(from_year.split("-")[0]))

        to_year = self._get("to_year")
        if to_year:
            if not ACADEMIC_YEAR_RE.match(to_year):
                raise ValueError("to_year must look like '2025-26'")
            self._add("CAST(substr(r.academic_year, 1, 4) AS INTEGER) <= ?",
                      int(to_year.split("-")[0]))

        category = self._get("category")
        if category:
            code = category.upper()
            if code not in FINAL_CATEGORY_CODES:
                # Accept the public display name too (e.g. "Workshops") and
                # resolve it back to the canonical code.
                for candidate, name in CATEGORY_CANDIDATE_NAMES.items():
                    if name and name.upper() == code:
                        code = candidate
                        break
                else:
                    raise ValueError(
                        "category must be one of: %s"
                        % ", ".join(sorted(CATEGORY_CANDIDATE_NAMES)))
            self._add("EXISTS (SELECT 1 FROM linkedin_activity_categories ac "
                      "WHERE ac.activity_id = r.activity_id AND ac.category_code = ?)", code)

        department = self._get("department")
        if department:
            if department not in FINAL_DEPARTMENTS:
                raise ValueError(
                    "department must be a public department or 'General'")
            self._add("EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                      "WHERE ad.activity_id = r.activity_id AND ad.department = ?)",
                      department)

        scope = self._get("scope")
        if scope:
            scope = scope.lower()
            # Two completely separate activity worlds: institution-wide
            # (General) activities vs activities attributed to a specific
            # department.  General activities carry either no department or
            # exactly ["General"]; departmental activities carry at least one
            # real department name.
            if scope not in ("general", "departmental"):
                raise ValueError("scope must be 'general' or 'departmental'")
            if scope == "general":
                self._add("NOT EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                          "WHERE ad.activity_id = r.activity_id AND ad.department != ?)",
                          "General")
            else:
                self._add("EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                          "WHERE ad.activity_id = r.activity_id AND ad.department != ?)",
                          "General")

        stakeholder = self._get("stakeholder")
        if stakeholder:
            if stakeholder not in FINAL_STAKEHOLDERS:
                raise ValueError("stakeholder must be a supported stakeholder name")
            self._add("EXISTS (SELECT 1 FROM linkedin_activity_stakeholders ast "
                      "WHERE ast.activity_id = r.activity_id AND ast.stakeholder = ?)",
                      stakeholder)

        date_from = self._get("date_from", "from_date")
        if date_from:
            try:
                datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_from must be an ISO date (YYYY-MM-DD)")
            self._add("r.activity_date >= ?", date_from)

        date_to = self._get("date_to", "to_date")
        if date_to:
            try:
                datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                raise ValueError("date_to must be an ISO date (YYYY-MM-DD)")
            self._add("r.activity_date <= ?", date_to)

        search = self._get("search", "q")
        if search:
            like = "%" + search + "%"
            self._add("(r.title LIKE ? COLLATE NOCASE OR r.description LIKE ? "
                      "COLLATE NOCASE)", like, like)
        return " AND ".join(self.clauses), self.params

    def where_sql(self, prefix=" WHERE "):
        sql, params = self.apply()
        return (prefix + sql) if sql else "", params


def filters_fragment(args):
    """Return (where_sql, params) for the reportable table (alias ``r``)."""
    return ReportableFilters(args).where_sql()


def count_reportable(conn, args=None):
    where, params = filters_fragment(args)
    sql = "SELECT COUNT(*) AS c FROM linkedin_reportable_activities r" + where
    return conn.execute(sql, params).fetchone()["c"]


def _row_to_record(row):
    """Build the public projection of a final reportable row."""
    categories = json.loads(row["categories"]) if row["categories"] else []
    departments = json.loads(row["departments"]) if row["departments"] else []
    stakeholders = json.loads(row["stakeholders"]) if row["stakeholders"] else []

    # Resolve any category name to a canonical public name via the candidate map.
    cat_items = [
        {"code": code, "name": CATEGORY_CANDIDATE_NAMES.get(code, code)}
        for code in categories
    ]

    return OrderedDict((
        ("activity_id", row["activity_id"]),
        ("title", row["title"]),
        ("summary", derive_public_summary(row)),
        ("post_url", row["post_url"]),
        ("activity_date", row["activity_date"]),
        ("academic_year", row["academic_year"]),
        ("category", primary_value(
            [i["name"] for i in cat_items], fallback=None)),
        ("categories", cat_items),
        ("department", primary_value(departments, fallback="General" if departments == [] else None)),
        ("departments", departments),
        ("stakeholder", primary_value(stakeholders)),
        ("stakeholders", stakeholders),
        ("source", row["source"]),
    ))


# ---------------------------------------------------------------------------
# Analytic aggregations (all over REPORTABLE rows in the SAME reportable DB).
# ---------------------------------------------------------------------------
def analytics_yearly(conn, args=None):
    where, params = filters_fragment(args)
    sql = ("SELECT r.academic_year, COUNT(*) AS total FROM "
           "linkedin_reportable_activities r" + where + " AND r.academic_year IS NOT NULL "
           "GROUP BY r.academic_year ORDER BY r.academic_year")
    return [{"academic_year": row["academic_year"], "activity_count": row["total"]}
            for row in conn.execute(sql, params).fetchall()]


def analytics_categories(conn, args=None):
    where, params = filters_fragment(args)
    sql = ("SELECT ac.category_code AS category, COUNT(*) AS total FROM "
           "linkedin_activity_categories ac "
           "JOIN linkedin_reportable_activities r ON r.activity_id = ac.activity_id " + where +
           " GROUP BY ac.category_code ORDER BY total DESC, ac.category_code")
    return [{"category": row["category"], "name": CATEGORY_CANDIDATE_NAMES.get(row["category"], row["category"]),
             "activity_count": row["total"]}
            for row in conn.execute(sql, params).fetchall()]


def analytics_departments(conn, args=None):
    where, params = filters_fragment(args)
    sql = ("SELECT ad.department, COUNT(*) AS total FROM "
           "linkedin_activity_departments ad "
           "JOIN linkedin_reportable_activities r ON r.activity_id = ad.activity_id " + where +
           " GROUP BY ad.department ORDER BY total DESC, ad.department")
    return [{"department": row["department"], "activity_count": row["total"]}
            for row in conn.execute(sql, params).fetchall()]


def analytics_stakeholders(conn, args=None):
    where, params = filters_fragment(args)
    sql = ("SELECT ast.stakeholder, COUNT(*) AS total FROM "
           "linkedin_activity_stakeholders ast "
           "JOIN linkedin_reportable_activities r ON r.activity_id = ast.activity_id " + where +
           " GROUP BY ast.stakeholder ORDER BY total DESC, ast.stakeholder")
    return [{"stakeholder": row["stakeholder"], "activity_count": row["total"]}
            for row in conn.execute(sql, params).fetchall()]


def analytics_overview(conn, args=None):
    base_args = {k: v for k, v in (args or {}).items()}
    total = count_reportable(conn, base_args)
    yearly = analytics_yearly(conn, base_args)
    cats = analytics_categories(conn, base_args)
    depts = analytics_departments(conn, base_args)
    staks = analytics_stakeholders(conn, base_args)
    dated_where, dated_params = filters_fragment(base_args)
    dated = conn.execute(
        "SELECT r.date_status, COUNT(*) AS c FROM linkedin_reportable_activities r "
        + dated_where + " GROUP BY r.date_status", dated_params).fetchall()
    url_where, url_params = filters_fragment(base_args)
    with_url = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities r "
        + url_where + " AND r.post_url IS NOT NULL", url_params).fetchone()["c"]

    # activities by month (reliable dates only)
    month_where, month_params = filters_fragment(base_args)
    months = conn.execute(
        "SELECT substr(r.activity_date, 1, 7) AS ym, COUNT(*) AS c FROM "
        "linkedin_reportable_activities r " + month_where + " AND r.activity_date IS NOT NULL "
        "GROUP BY ym ORDER BY ym", month_params).fetchall()

    # The two separate activity worlds share the SAME reportable dataset.
    general_args = dict(base_args, scope="general")
    departmental_args = dict(base_args, scope="departmental")
    general_total = count_reportable(conn, general_args)
    departmental_total = count_reportable(conn, departmental_args)
    general_cats = analytics_categories(conn, general_args)
    departmental_cats = analytics_categories(conn, departmental_args)

    return {
        "total_reportable_activities": total,
        "activities_by_academic_year": yearly,
        "activities_by_category": cats,
        "activities_by_department": depts,
        "activities_by_stakeholder": staks,
        "activities_by_month": [{"month": row["ym"], "activity_count": row["c"]}
                                for row in months],
        "date_status": {row["date_status"]: row["c"] for row in dated},
        "general_departmental": {
            "general": general_total,
            "departmental": departmental_total,
        },
        "general_categories": general_cats,
        "departmental_categories": departmental_cats,
        "departments_covered": len([d for d in depts if d["department"] != "General"]),
        "categories_covered": len(cats),
        "stakeholders_covered": len(staks),
        "source_coverage": {
            "source": "TCE LinkedIn",
            "with_url": with_url,
            "without_url": total - with_url,
            "url_coverage_pct": round(100.0 * with_url / total, 2) if total else 0.0,
        },
    }


# ---------------------------------------------------------------------------
# Availability endpoints (data-driven; never seeded/hard-coded).
# ---------------------------------------------------------------------------
def availability(conn):
    years = conn.execute(
        "SELECT DISTINCT academic_year FROM linkedin_reportable_activities "
        "WHERE reportable_status=? AND academic_year IS NOT NULL ORDER BY academic_year",
        (REPORTABLE,)).fetchall()
    cats = conn.execute(
        "SELECT DISTINCT category_code FROM linkedin_activity_categories ORDER BY category_code"
    ).fetchall()
    depts = conn.execute(
        "SELECT DISTINCT department FROM linkedin_activity_departments ORDER BY department"
    ).fetchall()
    staks = conn.execute(
        "SELECT DISTINCT stakeholder FROM linkedin_activity_stakeholders ORDER BY stakeholder"
    ).fetchall()
    date_range = conn.execute(
        "SELECT MIN(activity_date) AS mn, MAX(activity_date) AS mx FROM "
        "linkedin_reportable_activities WHERE reportable_status=? "
        "AND activity_date IS NOT NULL", (REPORTABLE,)).fetchone()
    return {
        "years": [r["academic_year"] for r in years],
        "categories": [{"code": r["category_code"],
                        "name": CATEGORY_CANDIDATE_NAMES.get(r["category_code"], r["category_code"])}
                       for r in cats],
        "departments": [r["department"] for r in depts],
        "stakeholders": [r["stakeholder"] for r in staks],
        "date_range": {
            "earliest": date_range["mn"],
            "latest": date_range["mx"],
        },
    }


def _serialize_rows(rows):
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Admin helpers (rich inspection + manual validation/editing).
# ---------------------------------------------------------------------------
def admin_record(row):
    """The full admin/internal representation of a final reportable row."""
    rec = {
        "activity_id": row["activity_id"],
        "staging_post_id": row["staging_post_id"],
        "staging_candidate_id": row["staging_candidate_id"],
        "reportable_status": row["reportable_status"],
        "title": row["title"],
        "description": row["description"],
        "post_url": row["post_url"],
        "activity_date": row["activity_date"],
        "academic_year": row["academic_year"],
        "categories": json.loads(row["categories"]) if row["categories"] else [],
        "departments": json.loads(row["departments"]) if row["departments"] else [],
        "stakeholders": json.loads(row["stakeholders"]) if row["stakeholders"] else [],
        "date_status": row["date_status"],
        "classification_status": row["classification_status"],
        "review_status": row["review_status"],
        "is_manually_validated": row["is_manually_validated"],
        "category_candidates": json.loads(row["category_candidates"]) if row["category_candidates"] else [],
        "department_candidates": json.loads(row["department_candidates"]) if row["department_candidates"] else [],
        "stakeholder_candidates": json.loads(row["stakeholder_candidates"]) if row["stakeholder_candidates"] else [],
        "department_display": json.loads(row["department_display"]) if row["department_display"] else [],
        "date_evidence": json.loads(row["date_evidence"]) if row["date_evidence"] else {},
        "category_evidence": json.loads(row["category_evidence"]) if row["category_evidence"] else {},
        "department_evidence": json.loads(row["department_evidence"]) if row["department_evidence"] else {},
        "stakeholder_evidence": json.loads(row["stakeholder_evidence"]) if row["stakeholder_evidence"] else {},
        "communication_type": row["communication_type"],
        "communication_evidence": json.loads(row["communication_evidence"]) if row["communication_evidence"] else {},
        "evidence_score": row["evidence_score"],
        "multi_label": row["multi_label"],
        "flags": json.loads(row["flags"]) if row["flags"] else [],
        "unclear_reason": row["unclear_reason"],
        "reason": row["reason"],
        "kind": row["kind"],
        "manual_overrides": json.loads(row["manual_overrides"]) if row["manual_overrides"] else {},
        "validation_history": json.loads(row["validation_history"]) if row["validation_history"] else [],
        "provenance": {
            "source": row["source"],
            "source_workbook": row["source_workbook"],
            "source_sheet": row["source_sheet"],
            "source_row": row["source_row"],
            "occurrence_count": row["occurrence_count"],
            "source_occurrence_ids": json.loads(row["source_occurrence_ids"]) if row["source_occurrence_ids"] else [],
            "collected_at": row["collected_at"],
            "resolved_via": row["resolved_via"],
            "activity_urn_id": row["activity_urn_id"],
        },
    }
    return rec


def admin_update(conn, activity_id, data, reviewer=None, note=None):
    """Apply an admin edit to a final reportable row.

    Only ADMIN_EDITABLE_FIELDS may change; provenance/classification evidence is
    immutable.  Every edit is recorded in validation_history.  Returns the
    updated admin record.
    """
    row = conn.execute(
        "SELECT * FROM linkedin_reportable_activities WHERE activity_id = ?",
        (activity_id,)).fetchone()
    if row is None:
        return None

    body = data or {}
    overrides = dict(json.loads(row["manual_overrides"]) if row["manual_overrides"] else {})
    history = list(json.loads(row["validation_history"]) if row["validation_history"] else [])
    now = datetime.now().isoformat(timespec="seconds")
    actor = (reviewer or "admin").strip() or "admin"

    updates = {}
    for field in ADMIN_EDITABLE_FIELDS:
        if field not in body:
            continue
        new_raw = body[field]
        if field in ("categories", "departments", "stakeholders"):
            new_value = validate_categories(new_raw) if field == "categories" \
                else validate_departments(new_raw) if field == "departments" \
                else validate_stakeholders(new_raw)
            old_value = json.loads(row[field]) if row[field] else []
        elif field == "academic_year":
            new_value = validate_academic_year(new_raw)
            old_value = row["academic_year"]
        elif field == "reportable_status":
            if new_raw not in REPORTABLE_STATUSES:
                raise ValueError("reportable_status must be one of: %s"
                                 % ", ".join(REPORTABLE_STATUSES))
            new_value = new_raw
            old_value = row["reportable_status"]
        elif field == "review_status":
            if new_raw not in REVIEW_STATUSES:
                raise ValueError("review_status must be one of: %s"
                                 % ", ".join(REVIEW_STATUSES))
            new_value = new_raw
            old_value = row["review_status"]
        else:
            new_value = new_raw if new_raw not in (None, "") else None
            old_value = row[field] if row[field] is not None else None

        if new_value != old_value:
            updates[field] = new_value
            overrides[field] = new_value
            history.append({"field": field, "old": old_value, "new": new_value,
                            "by": actor, "at": now,
                            "note": note or "admin manual correction"})

    if not updates:
        return admin_record(row)

    validated = int(bool(history))
    if validated or body.get("reportable_status") == REPORTABLE:
        validated = int("reportable_status" in updates
                        or "categories" in updates
                        or "activity_date" in updates
                        or "academic_year" in updates
                        or validated)

    set_fields = {
        "description": "description", "title": "title", "activity_date":
        "activity_date", "academic_year": "academic_year",
        "reportable_status": "reportable_status", "review_status": "review_status",
    }

    if "description" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET description=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["description"], activity_id))
    if "title" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET title=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["title"], activity_id))
    if "activity_date" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET activity_date=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["activity_date"], activity_id))
    if "academic_year" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET academic_year=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["academic_year"], activity_id))
    if "categories" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET categories=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (json.dumps(updates["categories"]), activity_id))
    if "departments" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET departments=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (json.dumps(updates["departments"]), activity_id))
    if "stakeholders" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET stakeholders=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (json.dumps(updates["stakeholders"]), activity_id))
    if "reportable_status" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET reportable_status=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["reportable_status"], activity_id))
    if "review_status" in updates:
        conn.execute("UPDATE linkedin_reportable_activities SET review_status=?, updated_at=datetime('now') "
                     "WHERE activity_id=?", (updates["review_status"], activity_id))

    conn.execute(
        "UPDATE linkedin_reportable_activities SET manual_overrides=?, "
        "validation_history=?, is_manually_validated=?, updated_at=datetime('now') "
        "WHERE activity_id=?",
        (json.dumps(overrides), json.dumps(history), validated, activity_id))
    conn.commit()

    # keep the normalized occurrence tables consistent with the selected values
    conn.execute("DELETE FROM linkedin_activity_categories WHERE activity_id=?", (activity_id,))
    conn.execute("DELETE FROM linkedin_activity_departments WHERE activity_id=?", (activity_id,))
    conn.execute("DELETE FROM linkedin_activity_stakeholders WHERE activity_id=?", (activity_id,))
    refresh_normalized(conn, activity_id=activity_id)
    conn.commit()

    fresh = conn.execute(
        "SELECT * FROM linkedin_reportable_activities WHERE activity_id=?",
        (activity_id,)).fetchone()
    return admin_record(fresh)


def publish_record(conn, activity_id, reviewer=None, note=None):
    """Explicit "Save & Publish" promotion for one reportable record.

    Publishing is NEVER silent: this dedicated action flips
    ``reportable_status`` -> REPORTABLE and ``review_status`` -> APPROVED,
    marks the row manually validated, records an explicit entry in
    ``validation_history``, persists the decision in ``manual_overrides`` (so a
    dataset rebuild cannot re-classify it away), and refreshes the normalized
    tables so the record becomes immediately visible on the public frontend.

    Already-published + approved records return unchanged (idempotent; no
    history spam).  Returns the updated admin record, or None when the id is
    unknown.
    """
    row = conn.execute(
        "SELECT * FROM linkedin_reportable_activities WHERE activity_id = ?",
        (activity_id,)).fetchone()
    if row is None:
        return None

    now = datetime.now().isoformat(timespec="seconds")
    actor = (reviewer or "admin").strip() or "admin"
    history = list(json.loads(row["validation_history"]) if row["validation_history"] else [])
    old_status = row["reportable_status"]
    old_review = row["review_status"] or REVIEW_UNREVIEWED

    transitions = []
    if old_status != REPORTABLE:
        transitions.append(("reportable_status", old_status, REPORTABLE))
    if old_review != REVIEW_APPROVED:
        transitions.append(("review_status", old_review, REVIEW_APPROVED))
    if not transitions:
        return admin_record(row)

    overrides = dict(json.loads(row["manual_overrides"]) if row["manual_overrides"] else {})
    for field, old, new in transitions:
        history.append({"field": field, "old": old, "new": new,
                        "by": actor, "at": now,
                        "note": note or "admin save & publish"})
        overrides[field] = new

    conn.execute(
        "UPDATE linkedin_reportable_activities SET reportable_status=?, review_status=?, "
        "is_manually_validated=1, manual_overrides=?, validation_history=?, "
        "updated_at=datetime('now') WHERE activity_id=?",
        (REPORTABLE, REVIEW_APPROVED, json.dumps(overrides),
         json.dumps(history), activity_id))
    conn.commit()

    # Keep the normalized occurrence tables consistent so the newly published
    # record turns up immediately in public lists + analytics.
    conn.execute("DELETE FROM linkedin_activity_categories WHERE activity_id=?", (activity_id,))
    conn.execute("DELETE FROM linkedin_activity_departments WHERE activity_id=?", (activity_id,))
    conn.execute("DELETE FROM linkedin_activity_stakeholders WHERE activity_id=?", (activity_id,))
    refresh_normalized(conn, activity_id=activity_id)
    conn.commit()

    fresh = conn.execute(
        "SELECT * FROM linkedin_reportable_activities WHERE activity_id=?",
        (activity_id,)).fetchone()
    return admin_record(fresh)


def admin_summary(conn):
    """Aggregate statics for the Admin dashboard (one reportable dataset)."""
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities").fetchone()["c"]
    by_status = {
        row["reportable_status"]: row["c"]
        for row in conn.execute(
            "SELECT reportable_status, COUNT(*) AS c FROM linkedin_reportable_activities "
            "GROUP BY reportable_status").fetchall()
    }
    by_class_status = {
        row["classification_status"]: row["c"]
        for row in conn.execute(
            "SELECT classification_status, COUNT(*) AS c FROM linkedin_reportable_activities "
            "GROUP BY classification_status").fetchall()
    }
    by_review_status = {
        row["review_status"]: row["c"]
        for row in conn.execute(
            "SELECT review_status, COUNT(*) AS c FROM linkedin_reportable_activities "
            "GROUP BY review_status").fetchall()
    }
    dated = {
        row["date_status"]: row["c"]
        for row in conn.execute(
            "SELECT date_status, COUNT(*) AS c FROM linkedin_reportable_activities "
            "GROUP BY date_status").fetchall()
    }
    link_less = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities "
        "WHERE post_url IS NULL OR post_url = ''").fetchone()["c"]
    with_url = total - link_less
    flagged = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities "
        "WHERE flags LIKE ? OR flags LIKE ? OR flags LIKE ?",
        ('%link_less%', '%weak_text%', '%unclear%')).fetchone()["c"]
    unresolved = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities "
        "WHERE reportable_status=? OR review_status=?",
        (REVIEW_REQUIRED, REVIEW_NEEDS_REVIEW)).fetchone()["c"]
    validated = conn.execute(
        "SELECT COUNT(*) AS c FROM linkedin_reportable_activities "
        "WHERE is_manually_validated=1").fetchone()["c"]

    return {
        "total_raw_rows": conn.execute(
            "SELECT SUM(occurrence_count) AS c FROM linkedin_reportable_activities"
        ).fetchone()["c"] or 0,
        "total_canonical_posts": total,
        "total_reportable_activities": by_status.get(REPORTABLE, 0),
        "total_non_activities": by_status.get(NON_ACTIVITY, 0),
        "total_review_required": by_status.get(REVIEW_REQUIRED, 0),
        "by_classification_status": by_class_status,
        "by_review_status": by_review_status,
        "by_category": {row["category_code"]: row["c"] for row in conn.execute(
            "SELECT category_code, COUNT(*) AS c FROM linkedin_activity_categories "
            "GROUP BY category_code ORDER BY c DESC")},
        "by_department": {row["department"]: row["c"] for row in conn.execute(
            "SELECT department, COUNT(*) AS c FROM linkedin_activity_departments "
            "GROUP BY department ORDER BY c DESC")},
        "by_stakeholder": {row["stakeholder"]: row["c"] for row in conn.execute(
            "SELECT stakeholder, COUNT(*) AS c FROM linkedin_activity_stakeholders "
            "GROUP BY stakeholder ORDER BY c DESC")},
        "dated_vs_undated": dated,
        "academic_year_availability": {
            row["academic_year"]: row["c"]
            for row in conn.execute(
                "SELECT academic_year, COUNT(*) AS c FROM linkedin_reportable_activities "
                "WHERE reportable_status=? AND academic_year IS NOT NULL "
                "GROUP BY academic_year ORDER BY academic_year", (REPORTABLE,))
        },
        "link_vs_linkless": {"with_url": with_url, "without_url": link_less},
        "unresolved_or_flagged": unresolved,
        "flagged_records": flagged,
        "manually_validated": validated,
        "validation_stats": {
            "sample_pending_review": by_class_status.get("PENDING_REVIEW", 0),
            "auto_classified": by_class_status.get("AUTO_CLASSIFIED", 0),
            "needs_review": by_review_status.get(REVIEW_NEEDS_REVIEW, 0),
            "approved": by_review_status.get(REVIEW_APPROVED, 0),
        },
    }


def admin_review_queue(conn, args=None):
    """Records needing manual review (filters: reason/category/department/date/confidence/status)."""
    args = args or {}
    clauses = ["(r.reportable_status=? OR r.review_status=? OR r.classification_status=? OR "
               "r.flags LIKE ? OR r.flags LIKE ? OR r.flags LIKE ?)"]
    params = [REVIEW_REQUIRED, REVIEW_NEEDS_REVIEW, "PENDING_REVIEW",
              '%weak_text%', '%unclear%', '%multi_year%']

    reason = (args.get("reason") or "").strip()
    if reason:
        clauses.append("r.unclear_reason = ?")
        params.append(reason)
    status = (args.get("status") or "").strip()
    if status:
        if status not in REPORTABLE_STATUSES:
            raise ValueError("status must be one of: %s" % ", ".join(REPORTABLE_STATUSES))
        clauses.append("r.reportable_status = ?")
        params.append(status)
    category = (args.get("category") or "").strip()
    if category:
        clauses.append("EXISTS (SELECT 1 FROM linkedin_activity_categories ac "
                       "WHERE ac.activity_id = r.activity_id AND ac.category_code = ?)")
        params.append(category.upper())
    department = (args.get("department") or "").strip()
    if department:
        clauses.append("EXISTS (SELECT 1 FROM linkedin_activity_departments ad "
                       "WHERE ad.activity_id = r.activity_id AND ad.department = ?)")
        params.append(department)
    date_status = (args.get("date") or "").strip()
    if date_status:
        clauses.append("r.date_status = ?")
        params.append(date_status)
    confidence = (args.get("confidence") or "").strip()
    if confidence in ("low", "medium", "high"):
        op = "<=" if confidence == "low" else ">=" if confidence == "high" else "BETWEEN"
        if op == "BETWEEN":
            clauses.append("r.evidence_score BETWEEN 4 AND 7")
        else:
            clauses.append("r.evidence_score %s ?" % op)
            params.append(4 if confidence == "low" else 8)
    elif confidence:
        raise ValueError("confidence must be low|medium|high")

    sql = ("SELECT r.* FROM linkedin_reportable_activities r WHERE " +
           " AND ".join(clauses) + " ORDER BY r.staging_post_id")
    rows = conn.execute(sql, params).fetchall()
    return [admin_record(r) for r in rows]


def admin_options(conn):
    """Data-driven filter/option vocabulary for the Admin console.

    Everything the frontend needs to build filters and edit dropdowns is
    derived from either the fixed schema vocabularies or the actual rows in
    this reportable database (never hard-coded in the UI).
    """
    categories = sorted(
        ({"code": code, "name": CATEGORY_CANDIDATE_NAMES.get(code, code)}
         for code in FINAL_CATEGORY_CODES),
        key=lambda item: item["name"].lower())
    years = [row["academic_year"] for row in conn.execute(
        "SELECT DISTINCT academic_year FROM linkedin_reportable_activities "
        "WHERE academic_year IS NOT NULL ORDER BY academic_year").fetchall()]
    reasons = [row["unclear_reason"] for row in conn.execute(
        "SELECT DISTINCT unclear_reason FROM linkedin_reportable_activities "
        "WHERE unclear_reason IS NOT NULL ORDER BY unclear_reason").fetchall()]
    dates = [row["date_status"] for row in conn.execute(
        "SELECT DISTINCT date_status FROM linkedin_reportable_activities "
        "ORDER BY date_status").fetchall()]
    return {
        "statuses": list(REPORTABLE_STATUSES),
        "review_statuses": list(REVIEW_STATUSES),
        "date_statuses": dates,
        "categories": categories,
        "departments": sorted(FINAL_DEPARTMENTS),
        "stakeholders": sorted(FINAL_STAKEHOLDERS),
        "academic_years": years,
        "review_reasons": reasons,
        "confidence_levels": ["low", "medium", "high"],
    }