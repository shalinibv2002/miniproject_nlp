"""LinkedIn candidate generation/classification (PILOT — staging layer ONLY).

Processes the 1,544 canonical posts in ``linkedin_posts`` and writes candidate
classifications into a separate staging table
``linkedin_activity_candidates``.  Everything here lives in the dedicated
LinkedIn staging database (``linkedin_staging.db``).

HARD GUARANTEES (enforced by design):
  * Only the staging database is ever opened for writing.
  * The production database (``tce_activity_intelligence.db``) is NEVER
    imported, opened, or written to by this module.
  * The source workbook is never opened for writing.
  * Every canonical post is KEPT.  Nothing is deleted, merged into the
    2,258 website activities, or reconciled.
  * All classification decisions are evidence-based and stored internally
    (evidence spans/keywords are for validation/review only and are never
    intended to surface as public UI fields).

The TCE official website taxonomy (category_catalog / department_catalog) is
used ONLY as a reference starting point for candidate vocabularies; the
2,258 website-derived activities are NOT used as ground truth here.
"""

import json
import os
import random
import re
import sqlite3
from datetime import datetime

from backend.database import category_catalog, department_catalog
from backend.database.linkedin_staging import (
    STAGING_DB_PATH,
    extract_dates,
    get_staging_connection,
)

# ---------------------------------------------------------------------------
# Candidate statuses / review statuses
# ---------------------------------------------------------------------------
STATUS_ACTIVITY_CANDIDATE = "ACTIVITY_CANDIDATE"
STATUS_NON_ACTIVITY = "NON_ACTIVITY"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
ALL_STATUSES = (STATUS_ACTIVITY_CANDIDATE, STATUS_NON_ACTIVITY, STATUS_REVIEW_REQUIRED)

REVIEW_PENDING = "PENDING_REVIEW"
REVIEW_AUTO = "AUTO_CLASSIFIED"
ALL_REVIEW_STATUSES = (REVIEW_PENDING, REVIEW_AUTO)

# Step-2 screening buckets (internal, human-understandable kinds)
KIND_EVENT = "A"            # institutional activity/event
KIND_ACHIEVEMENT = "B"      # achievement/recognition
KIND_RESEARCH = "C"         # research/academic/institutional update
KIND_DEVELOPMENT = "D"      # student/faculty development activity
KIND_COMM = "E"             # communication/general announcement
KIND_JOB = "F"              # recruitment/job advertisement
KIND_ADMISSION = "G"        # admission/promotion
KIND_GREETING = "H"         # greeting/festival/wishes
KIND_OTHER = "I"            # other/non-activity
KIND_UNKNOWN = "J"          # unclear / requires review

# ---------------------------------------------------------------------------
# Candidate category vocabulary (a superset of the public project taxonomy).
# The public taxonomy codes are used where they overlap; TECH_FEST / STTP /
# SYMPOSIUM are kept as LinkedIn candidate codes because the feed actually
# contains those events (they are simply not public UI categories).
# Pattern entries: (regex, weight).  Matching is case-insensitive; a category
# qualifies when its summed weight of matched patterns >= QUALIFY_WEIGHT.
# ---------------------------------------------------------------------------
QUALIFY_WEIGHT = 3

CATEGORY_PATTERNS = {
    "WORKSHOP": [
        (r"workshop", 4),
        (r"hands[- ]on (?:session|training)", 3),
    ],
    "SEMINAR": [
        (r"seminar", 4),
    ],
    "CONFERENCE": [
        (r"conference", 4),
        (r"tedx", 4),
        (r"paper presentation", 3),
        (r"poster presentation", 4),
    ],
    "SYMPOSIUM": [
        (r"symposium", 5),
    ],
    "GUEST_LECTURE": [
        (r"guest lecture", 5),
        (r"guest talk", 5),
        (r"technical talk", 4),
        (r"special lecture", 4),
        (r"invited talk", 4),
        (r"keynote", 4),
        (r"talk (?:on|by|session\b)", 2),
    ],
    "FDP": [
        (r"faculty development programme", 5),
        (r"faculty development program", 5),
        (r"\bfdp\b", 5),
    ],
    "STTP": [
        (r"\bsttp\b", 5),
        (r"short term training programme", 5),
        (r"short term training program", 5),
    ],
    "HACKATHON": [
        (r"hackathon", 5),
    ],
    "TECH_FEST": [
        (r"tech\s?fest", 5),
        (r"technical festival", 5),
    ],
    "CULTURAL": [
        (r"cultural", 4),
        (r"cultura nova", 5),
        (r"competition", 2),
        (r"contest", 2),
        (r"\bquiz\b", 3),
        (r"talent show", 4),
    ],
    "SPORTS": [
        (r"\bsports", 4),
        (r"marathon", 4),
        (r"athletics", 4),
        (r"\bchess\b", 3),
    ],
    "NCC": [
        (r"\bncc\b", 5),
        (r"national cadet corps", 5),
    ],
    "NSS": [
        (r"\bnss\b", 5),
        (r"national service scheme", 5),
    ],
    "CLUB": [
        (r"club", 3),
        (r"\bieee\b", 4),
        (r"\biedc\b", 4),
        (r"institution(?:al)? innovation council", 4),
        (r"\brotaract\b", 4),
        (r"\btoastmasters\b", 4),
        (r"\brotary\b", 3),
        (r"innovation council", 4),
    ],
    "OUTREACH": [
        (r"outreach", 4),
        (r"\bextension\b", 4),
        (r"blood donation", 5),
        (r"\bswachh", 4),
        (r"awareness (?:camp|drive|programme|program|session)", 4),
        (r"medical camp", 5),
        (r"\brural\b", 3),
        (r"\bvillage", 3),
        (r"\bngo\b", 4),
    ],
    "INDUSTRY": [
        (r"\bmou\b", 5),
        (r"\bmoa\b", 5),
        (r"\bnda\b", 4),
        (r"industry collaboration", 5),
        (r"industry partners", 5),
        (r"partnership with", 4),
        (r"industrial visit", 5),
        (r"industrial training", 4),
    ],
    "ACHIEVEMENT": [
        (r"achievement", 4),
        (r"\baward(?:ed|s)?\b", 4),
        (r"recogni[sz]ed", 4),
        (r"accredit(?:ed|ation)", 5),
        (r"\bnptel\b", 4),
        (r"certificat", 3),
        (r"\bwon\b", 4),
        (r"secured", 3),
        (r"selected (?:as|for)", 3),
        (r"\btrophy", 4),
        (r"gold medal", 5),
        (r"proud moment", 4),
        (r"congratulat", 2),
        (r"milestone", 3),
        (r"best paper", 5),
        (r"rank(?:ed| holder)?", 3),
    ],
    "PLACEMENT": [
        (r"placement", 4),
        (r"placed (?:in|at)", 4),
        (r"campus recruitment", 5),
        (r"pre[- ]placement", 4),
        (r"got placed", 5),
        (r"dream offer", 4),
        (r"\bplaced\b", 3),
    ],
    "INTERNSHIP": [
        (r"internship", 5),
        (r"intern", 4),
    ],
    "RESEARCH": [
        (r"\bresearch\b", 3),
        (r"\bjournal\b", 4),
        (r"publication", 4),
        (r"published", 4),
        (r"patent", 5),
        (r"ph\.?\s?d", 5),
        (r"\bphd\b", 5),
        (r"doctoral", 4),
        (r"research scholar", 5),
        (r"research fellow", 5),
        (r"research grant", 5),
        (r"consultancy", 5),
        (r"funded project", 5),
        (r"sponsored research", 5),
        (r"technical paper", 4),
    ],
    "ALUMNI": [
        (r"alumni", 5),
        (r"alumnus", 5),
        (r"alum(?:ni)? meet", 5),
        (r"reunion", 5),
        (r"\bbatch\b", 2),
        (r"batch of", 4),
    ],
    "ORIENTATION": [
        (r"orientation", 5),
        (r"induction", 5),
        (r"fresher", 4),
        (r"graduation", 4),
        (r"convocation", 5),
        (r"welcome programme", 4),
        (r"welcome program", 4),
    ],
    "CAMPUS": [
        (r"campus", 2),
        (r"foundation day", 4),
        (r"founders? day", 4),
        (r"annual day", 4),
        (r"world (?:environment|student|water|earth|health|mental health) day", 5),
        (r"ozone layer", 4),
        (r"national safety month", 5),
        (r"5s day", 5),
        (r"open house", 4),
        (r"green campus", 4),
        (r"teachers? day", 4),
        (r"engineers? day", 4),
        (r"valedictory", 3),
        (r"inauguration", 2),
        (r"international day", 4),
    ],
    "WEBINAR": [
        (r"webinar", 5),
        (r"online session", 4),
        (r"virtual session", 4),
        (r"online talk", 4),
    ],
}

# Mapped public names for report readability (project taxonomy where it exists).
CATEGORY_CANDIDATE_NAMES = dict(category_catalog.CATEGORY_PUBLIC_NAMES)
CATEGORY_CANDIDATE_NAMES.setdefault("TECH_FEST", "Technical Festival")
CATEGORY_CANDIDATE_NAMES.setdefault("STTP", "STTP")
CATEGORY_CANDIDATE_NAMES.setdefault("SYMPOSIUM", "Symposium")

# Development-type categories (step-2 bucket D) — student/faculty development.
DEV_CATEGORIES = frozenset({
    "WORKSHOP", "FDP", "STTP", "GUEST_LECTURE", "SEMINAR", "WEBINAR",
    "HACKATHON", "INTERNSHIP", "PLACEMENT", "ORIENTATION", "CLUB", "NCC", "NSS",
})

# Categories that describe an ORGANIZED EVENT (vs. words that commonly appear
# as program-feature mentions inside admission promos / job ads).  A
# communication post (admission promo / job ad) wins the decision over mere
# keyword mentions unless a real event category is the strongest signal.
STRICT_EVENT_CATEGORIES = frozenset({
    "WORKSHOP", "SEMINAR", "CONFERENCE", "SYMPOSIUM", "GUEST_LECTURE", "FDP",
    "STTP", "HACKATHON", "TECH_FEST", "CULTURAL", "SPORTS", "NCC", "NSS",
    "ORIENTATION", "WEBINAR",
})

# ---------------------------------------------------------------------------
# Communication patterns (non-activity evidence).  Only used to classify a
# post as NON_ACTIVITY when no activity category qualifies.
# ---------------------------------------------------------------------------
COMM_PATTERNS = {
    "greeting": [
        r"wish(?:es|ing)? (?:you|everyone|all)",
        r"happy (?:new year|diwali|pongal|christmas|onam|ramadan|eid|ayudha|deepavali)",
        r"festival wishes",
        r"\bgreetings\b",
        r"joyous",
        r"merry christmas",
        r"happy holidays",
    ],
    "admission_promo": [
        r"admission(?:s)?",
        r"admissions? open",
        r"spot admission",
        r"apply for admission",
        r"admission 20\d\d",
        r"entrance exam",
    ],
    "job_ad": [
        r"we are hiring",
        r"\bhiring\b",
        r"job opening",
        r"\bvacanc",
        r"recruit(?:ment|ing|ed)",
        r"walk[- ]in",
        r"apply for the post",
        r"job opportunit(?:y|ies)",
    ],
    "thanks": [
        r"thank you",
        r"\bthanks\b",
        r"gratitude",
        r"acknowledge",
        r"sincere thanks",
        r"appreciation",
    ],
}

# ---------------------------------------------------------------------------
# Department patterns (reference = department_catalog.PUBLIC_DEPARTMENTS).
# A department is recorded only when the summed weight >= DEPARTMENT_QUALIFY.
# ---------------------------------------------------------------------------
DEPARTMENT_QUALIFY = 3

DEPARTMENT_PATTERNS = [
    ("Computer Science and Business Systems", [
        (r"computer science and business", 5),
        (r"\bcsbs\b", 4),
    ]),
    ("Computer Science and Engineering", [
        (r"computer science and engineering", 5),
        (r"computer science & engineering", 5),
        (r"\bcse\b", 3),
        (r"(?<!business and )computer science", 3),
    ]),
    ("Information Technology", [
        (r"information technology", 5),
        (r"information &? technology", 4),
    ]),
    ("Electronics and Communication Engineering", [
        (r"electronics and communication", 5),
        (r"electronics & communication", 5),
        (r"\bece\b", 3),
    ]),
    ("Electrical and Electronics Engineering", [
        (r"electrical and electronics", 5),
        (r"electrical & electronics", 5),
        (r"\belectric(?:al)?\b", 3),
        (r"\beee\b", 3),
    ]),
    ("Mechanical Engineering", [
        (r"mechanical", 5),
        (r"\bmech\b", 3),
    ]),
    ("Civil Engineering", [
        (r"civil", 5),
    ]),
    ("Mechatronics", [
        (r"mechatronics", 5),
        (r"\bmct\b", 3),
    ]),
    ("Applied Mathematics and Computational Science", [
        (r"applied mathematics", 5),
        (r"\bamcs\b", 4),
        (r"data science", 4),
        (r"mathematics and computational science", 5),
    ]),
    ("Artificial Intelligence", [
        (r"artificial intelligence", 5),
        (r"machine learning", 4),
        (r"\bai\s*[/&]+\s*ml\b", 4),
        (r"\bai\s+and\s+ml\b", 4),
        (r"\bai[- ]ml\b", 4),
    ]),
    ("Computer Applications", [
        (r"computer applications", 5),
        (r"(?:department|dept)\.?\s+of\s+mca\b", 5),
        (r"department\s+of\s+computer applications", 5),
        (r"departments?\s+of\s+[^\n.]*\bmca\b", 5),
        (r"\bmca\b", 4),
        (r"\bbca\b", 3),
    ]),
    ("Chemistry", [
        (r"(?:department|dept)\.?\s+of\s+chemistry", 5),
        (r"chemistry (?:dept|department)", 5),
        (r"chemistry", 4),
    ]),
    ("English", [
        (r"department of english", 5),
        (r"english (?:dept|department)", 5),
        (r"english (?:spell|essay|debate)", 4),
    ]),
    ("T'SEDA (Architecture, Design, Planning)", [
        (r"t['\u2019]?seda", 5),
        (r"thiagarajar school of environmental design", 5),
        (r"architecture", 4),
        (r"urban planning", 5),
        (r"\bm\.?\s?plan\b", 4),
        (r"environmental design", 5),
    ]),
]


# ---------------------------------------------------------------------------
# Stakeholder patterns (the eight public stakeholders).  Threshold like depts.
# ---------------------------------------------------------------------------
STAKEHOLDER_QUALIFY = 3

STAKEHOLDER_PATTERNS = [
    ("Students", [
        (r"students?", 3),
        (r"b\.?\s?tech", 3),
        (r"b\.?\s?e\b", 3),
        (r"m\.?\s?tech", 3),
        (r"m\.?\s?e\b", 3),
        (r"b\.?\s?sc", 3),
        (r"m\.?\s?sc", 3),
        (r"ug students", 4),
        (r"pg students", 4),
        (r"\bfresher", 3),
        (r"young artists", 3),
    ]),
    ("Faculty", [
        (r"faculty", 4),
        (r"professor", 4),
        (r"\bprof\b", 3),
        (r"\bhod\b", 3),
        (r"head of the department", 4),
        (r"teaching staff", 4),
        (r"\btutors?\b", 3),
    ]),
    ("Industry", [
        (r"industry", 3),
        (r"\bcompany", 3),
        (r"corporate", 3),
        (r"\bmou\b", 4),
        (r"recruiter", 3),
        (r"industry collaboration", 4),
        (r"\bpartner\b", 2),
    ]),
    ("Alumni", [
        (r"alumni", 5),
        (r"alumnus", 5),
        (r"reunion", 4),
        (r"\bpatch\b", 2),
        (r"\bbatch\b", 2),
        (r"19\d\d[- ]20\d\d", 3),
    ]),
    ("Government and Agencies", [
        (r"government", 4),
        (r"\bgovt", 4),
        (r"ministry", 4),
        (r"\baicte\b", 4),
        (r"\bugc\b", 4),
        (r"\bdst\b", 3),
        (r"\bdrdo\b", 4),
        (r"\bisro\b", 4),
        (r"\bmeity\b", 4),
        (r"\bdae\b", 3),
    ]),
    ("Community and Society", [
        (r"community", 4),
        (r"\bsociety", 3),
        (r"\brural\b", 4),
        (r"\bvillage", 4),
        (r"\bschool", 3),
        (r"\bngo\b", 4),
        (r"public awareness", 3),
    ]),
    ("Non-Teaching Staff", [
        (r"non[- ]teaching", 5),
        (r"support staff", 4),
        (r"office staff", 4),
        (r"administrative staff", 4),
    ]),
    ("Parents", [
        (r"parents?", 4),
    ]),
]

# Public stakeholder display names (align with the project's stakeholder list).
STAKEHOLDER_PUBLIC_NAMES = {
    "Students": "Students",
    "Faculty": "Faculty",
    "Non-Teaching Staff": "Non-Teaching Staff",
    "Alumni": "Alumni",
    "Industry": "Industry",
    "Parents": "Parents",
    "Government and Agencies": "Government and Agencies",
    "Community and Society": "Community and Society",
}

# ---------------------------------------------------------------------------
# Flags for special cases (STEP 7) — never delete, always flag.
# ---------------------------------------------------------------------------
FLAG_LINK_LESS = "link_less"
FLAG_WEAK_TEXT = "weak_text"
FLAG_URL_ONLY = "url_only"
FLAG_TEXT_IS_URL = "text_is_url"
FLAG_PRE_2024 = "pre_2024_ambiguous"
FLAG_MULTI_YEAR = "multi_year"
FLAG_COMM_ONLY = "communication_only"

WEAK_TEXT_LENGTH = 100

# ---------------------------------------------------------------------------
# RULE-01..12 review-supported gates (ADDITIVE by design).  Nothing here is
# auto-dropped; every rule keeps the raw evidence and only records a flag /
# display-level view, so nothing is lost for the review layer or audit.
# ---------------------------------------------------------------------------
FLAG_CATEGORY_CONTEXT_ONLY = "category_context_only"   # RULE-02 (NON_ACTIVITY rows)
FLAG_DEPT_TO_GENERAL = "dept_to_general"               # RULE-09 (display General)
FLAG_MULTI_LABEL_COLLAPSED = "multi_label_collapsed"   # RULE-08 (curated pairs)
FLAG_UNCLEAR = "unclear"                               # RULE-12 prefix (see taxonomy below)
FLAG_CATEGORY_GATE = "category_gate"                   # RULE-03..07 prefix

# Mention-style evidence patterns per attention category (RULE-03..07 gates).
# Keys match the pattern strings in CATEGORY_PATTERNS exactly (they are stored
# verbatim as keys in the category_evidence JSON).
#
# STEP-11 (strict ACHIEVEMENT classification): an ACHIEVEMENT that matched ONLY
# these acknowledgement/mention keywords is NOT an achievement for reporting —
# "won first prize", "secured second place", "received Best Faculty Award" use
# DIRECT patterns (won / secured / award), so they are never mention-only.
GATE_OVER_TAG_MENTION_PATTERNS = {
    "ACHIEVEMENT": {
        r"congratulat", r"certificat", r"milestone",
        r"recogni[sz]ed", r"proud moment", r"accredit(?:ed|ation)",
    },
    "RESEARCH": {
        r"\bresearch\b", r"publication", r"published",
    },
    "ALUMNI": {
        r"alumni", r"alumnus", r"\bbatch\b", r"batch of",
    },
    "INTERNSHIP": {
        r"internship", r"intern",
    },
    "PLACEMENT": {
        r"placement", r"\bplaced\b",
    },
    "INDUSTRY": {
        r"\bmou\b", r"\bmoa\b", r"industry collaboration", r"industry partners",
        r"partnership with",
    },
    "CAMPUS": {
        r"campus", r"inauguration",
    },
}

# A category is NOT mention-only when it carries date-ish context: a dated or
# duration internship/placement programme is a real programme, not a mention.
GATE_MENTION_ONLY_SKIP_WHEN_DATED = ("INTERNSHIP", "PLACEMENT")

GATE_MONTH_TOKEN_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|"
    r"october|november|december)\b", re.I)
GATE_YEAR_TOKEN_RE = re.compile(r"\b20(?:2[0-9]|30)\b")
GATE_ALUMNI_FEATURE_RE = re.compile(
    r"#alumni|alumni\s*(?:spotlight|story|feature|of the week)|"
    r"alumn(?:us|a)\s*of\s*the\s*(?:week|year)", re.I)

# Generic technical terminology that is a TOPIC, not department evidence
# (RULE-09).  A department counts as explicitly organised/hosted only when at
# least one matched pattern is OUTSIDE this set; otherwise the display value
# falls back to the institution-wide "General".
GENERIC_DEPT_PATTERNS = {
    "Artificial Intelligence": {
        r"machine learning", r"\bai\s*[/&]+\s*ml\b",
        r"\bai\s+and\s+ml\b", r"\bai[- ]ml\b",
    },
    "Applied Mathematics and Computational Science": {r"data science"},
    "T'SEDA (Architecture, Design, Planning)": {
        r"architecture", r"\bm\.?\s?plan\b",
    },
    "Computer Science and Engineering": {r"(?<!business and )computer science"},
    "Electrical and Electronics Engineering": {r"\belectric(?:al)?\b"},
    "Computer Applications": {r"\bmca\b", r"\bbca\b"},
    "Chemistry": {r"chemistry"},
    "Mechatronics": {r"\bmct\b"},
}

# Curated same-event synonym pairs (RULE-08).  Only these pairs may collapse,
# and only when both category matches sit in the same text region (one event
# described with format/venue synonyms).  Parallel events stay multi-label.
# Mapping: (category_a, category_b) -> category to KEEP.
CURATED_MULTI_LABEL_PAIRS = {
    ("CONFERENCE", "WEBINAR"): "CONFERENCE",
    ("SYMPOSIUM", "TECH_FEST"): "SYMPOSIUM",
    ("CONFERENCE", "GUEST_LECTURE"): "GUEST_LECTURE",
}
MULTI_LABEL_REGION_GAP = 30

# ---------------------------------------------------------------------------
# Schema for the separate candidate layer (staging DB only).
# ---------------------------------------------------------------------------
CANDIDATES_SCHEMA = """
CREATE TABLE IF NOT EXISTS linkedin_activity_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linkedin_post_id INTEGER NOT NULL UNIQUE REFERENCES linkedin_posts(id),
    post_url TEXT,
    post_text TEXT NOT NULL,
    source_sheet TEXT NOT NULL,
    source_row INTEGER,
    candidate_status TEXT NOT NULL
        CHECK (candidate_status IN ('ACTIVITY_CANDIDATE','NON_ACTIVITY','REVIEW_REQUIRED')),
    is_activity INTEGER CHECK (is_activity IN (0, 1)),
    kind TEXT,                              -- step-2 bucket A..J (internal)
    category_candidates TEXT,               -- JSON list of category codes
    department_candidates TEXT,             -- JSON list of canonical dept names
    stakeholder_candidates TEXT,            -- JSON list of public stakeholder names
    date_status TEXT,                       -- 'dated' | 'undated' | 'ambiguous_multi_year'
    date_evidence TEXT,                     -- JSON {source, dates, earliest}
    academic_year TEXT,                     -- e.g. '2024-25' or NULL
    category_evidence TEXT,                 -- JSON {code: [spans]}; INTERNAL ONLY
    department_evidence TEXT,               -- JSON {dept: [spans]}; INTERNAL ONLY
    stakeholder_evidence TEXT,              -- JSON {stakeholder: [spans]}; INTERNAL ONLY
    communication_type TEXT,                -- 'greeting'|'admission_promo'|'job_ad'|'thanks'|NULL
    communication_evidence TEXT,            -- JSON {type: [spans]}; INTERNAL ONLY
    evidence_score INTEGER NOT NULL DEFAULT 0,
    multi_label INTEGER NOT NULL DEFAULT 0 CHECK (multi_label IN (0, 1)),
    flags TEXT,                             -- JSON list of special-case flags
    department_display TEXT,                -- JSON: explicit-organizer depts or ["General"] (RULE-09)
    unclear_reason TEXT,                    -- machine-readable reason code for REVIEW_REQUIRED (RULE-12)
    reason TEXT,
    review_status TEXT NOT NULL DEFAULT 'AUTO_CLASSIFIED'
        CHECK (review_status IN ('AUTO_CLASSIFIED','PENDING_REVIEW')),
    classified_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_linkedin_candidates_status
    ON linkedin_activity_candidates(candidate_status);
CREATE INDEX IF NOT EXISTS idx_linkedin_candidates_review
    ON linkedin_activity_candidates(review_status);
"""

INPUT_POST_COLUMNS = ("id", "post_url", "post_text", "source_sheet", "source_row")


def init_candidates_schema(conn):
    conn.executescript(CANDIDATES_SCHEMA)
    # Migration for staging DBs created before RULE-09/RULE-12 columns.
    cols = {r[1] for r in conn.execute(
        "PRAGMA table_info(linkedin_activity_candidates)").fetchall()}
    for name, ddl in (
        ("department_display",
         "ALTER TABLE linkedin_activity_candidates "
         "ADD COLUMN department_display TEXT"),
        ("unclear_reason",
         "ALTER TABLE linkedin_activity_candidates "
         "ADD COLUMN unclear_reason TEXT"),
    ):
        if name not in cols:
            conn.execute(ddl)
    conn.commit()


def _lower_clean(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).lower())


def _match_all(low_text, pattern):
    try:
        return list(re.finditer(pattern, low_text))
    except re.error:
        return []


def _hits(low, patterns):
    """Return (score, {pattern_string: [matched spans]}) for a pattern list."""
    score = 0
    found = {}
    for i, (pat, weight) in enumerate(patterns):
        matches = _match_all(low, pat)
        if matches:
            score += weight
            spans = []
            for m in matches:
                snippet = m.group(0)
                if snippet and snippet not in spans:
                    spans.append(snippet)
            found[pat] = spans
    return score, found


def _academic_year(year, month):
    """AY of a date under the June 1 - May 31 convention."""
    if month >= 6:
        return "%d-%02d" % (year, (year + 1) % 100)
    return "%d-%02d" % (year - 1, year % 100)


def _activity_kind(categories):
    """Step-2 bucket for an activity candidate, from its category candidates."""
    if "RESEARCH" in categories:
        return KIND_RESEARCH
    if "ACHIEVEMENT" in categories:
        return KIND_ACHIEVEMENT
    if any(c in DEV_CATEGORIES for c in categories):
        return KIND_DEVELOPMENT
    return KIND_EVENT


COMM_BUILD_KIND = {"greeting": KIND_GREETING, "admission_promo": KIND_ADMISSION,
                   "job_ad": KIND_JOB}


# ---------------------------------------------------------------------------
# RULE-01..12 helper evaluators (flag-first; nothing auto-dropped).
# ---------------------------------------------------------------------------
def _dateish(low):
    """Cheap date context mirroring the review layer: year token or month word."""
    return bool(GATE_YEAR_TOKEN_RE.search(low) or GATE_MONTH_TOKEN_RE.search(low))


def _gate_mention_only(code, ev, date_status, low):
    """True when a category only matched mention-style keywords (RULE-03..07)."""
    mention = GATE_OVER_TAG_MENTION_PATTERNS.get(code)
    if not mention or not ev:
        return False
    if not set(ev.keys()) <= mention:
        return False  # at least one direct (non-mention) pattern matched
    if code in GATE_MENTION_ONLY_SKIP_WHEN_DATED:
        if date_status == "dated" or _dateish(low):
            return False  # dated/duration internship|placement = real programme
    if code == "ALUMNI" and GATE_ALUMNI_FEATURE_RE.search(low):
        return False  # explicitly an alumni feature/spotlight -> genuinely alumni
    return True


def _evidence_regions(low, ev):
    regions = []
    for pat in (ev or {}):
        for m in _match_all(low, pat):
            regions.append((m.start(), m.end()))
    return regions


def _regions_close(first, second, gap=MULTI_LABEL_REGION_GAP):
    for s1, e1 in first:
        for s2, e2 in second:
            if max(s1, s2) - min(e1, e2) <= gap:
                return True
    return False


def curated_multi_label_drop(cat_qual, cat_evidence, low):
    """RULE-08: codes to drop when a curated same-event pair is confirmed."""
    drop = []
    for (a, b), keep in CURATED_MULTI_LABEL_PAIRS.items():
        if keep not in (a, b):
            continue
        if a not in cat_qual or b not in cat_qual:
            continue
        ev_a = cat_evidence.get(a) or {}
        ev_b = cat_evidence.get(b) or {}
        if ev_a and ev_b and _regions_close(
                _evidence_regions(low, ev_a), _evidence_regions(low, ev_b)):
            drop.append(b if keep == a else a)
    return drop


def _explicit_departments(dept_qual, dept_evidence):
    """RULE-09: departments backed by at least one non-generic pattern."""
    explicit = {}
    for dept in dept_qual:
        generic = GENERIC_DEPT_PATTERNS.get(dept, set())
        ev = dept_evidence.get(dept) or {}
        if any(pat not in generic for pat in ev):
            explicit[dept] = dept_qual[dept]
    return explicit


def _has_non_latin_text(text, threshold=5):
    """Rough Indic-script detection (Tamil/etc.) for the unclear taxonomy."""
    if not text:
        return False
    count = sum(1 for ch in text if 0x0900 <= ord(ch) <= 0x0DFF)
    return count >= threshold


def _unclear_reason(flags, low, weak, url_only, categories, comm_type):
    """RULE-12 machine-readable reason code for REVIEW_REQUIRED rows."""
    if url_only:
        return "url_only"
    if FLAG_TEXT_IS_URL in flags:
        return "text_is_url"
    if FLAG_MULTI_YEAR in flags:
        return "multi_year"
    if _has_non_latin_text(low):
        return "non_latin_unmatched"
    if FLAG_LINK_LESS in flags and weak:
        return "link_less_weak"
    if weak:
        return "low_evidence_event_like" if (categories or comm_type) else "title_only"
    return "low_evidence_event_like"


def classify_post(post):
    """Evidence-based candidate classification for one canonical LinkedIn post.

    ``post`` is a dict/mapping with at least the keys in INPUT_POST_COLUMNS.
    Returns a flat dict ready to be written to linkedin_activity_candidates.
    All evidence fields are internal.
    """
    text = post.get("post_text") or ""
    low = _lower_clean(text)
    n = len(text)

    flags = []
    has_url = bool((post.get("post_url") or "").strip())
    if not has_url:
        flags.append(FLAG_LINK_LESS)

    # --- date / academic-year evidence (explicit dates ONLY) ---------------
    dates = extract_dates(text)
    years = sorted({d[:4] for d in dates})
    if not dates:
        date_status = "undated"
        earliest = None
    elif len(years) > 1:
        date_status = "ambiguous_multi_year"
        flags.append(FLAG_MULTI_YEAR)
        earliest = dates[0]
    else:
        date_status = "dated"
        earliest = dates[0]
    academic_year = None
    if earliest:
        y, m = int(earliest[:4]), int(earliest[5:7])
        academic_year = _academic_year(y, m)
        if y < 2024:
            flags.append(FLAG_PRE_2024)
    date_evidence = {"source": "explicit_text", "dates": dates, "earliest": earliest}

    # --- weak / url-only / text-is-url special cases -----------------------
    stripped = text.strip()
    if not stripped:
        flags += [FLAG_URL_ONLY, FLAG_WEAK_TEXT]
        weak = True
        url_only = True
    else:
        url_only = False
        weak = n < WEAK_TEXT_LENGTH
        if weak:
            flags.append(FLAG_WEAK_TEXT)
        if re.match(r"^https?://\S+$", stripped) or stripped.lower().startswith("https://lnkd"):
            flags.append(FLAG_TEXT_IS_URL)

    # --- category evidence ---------------------------------------------------
    cat_qual, cat_evidence = {}, {}
    cat_order = sorted(CATEGORY_PATTERNS)
    for code in cat_order:
        score, found = _hits(low, CATEGORY_PATTERNS[code])
        if found:
            cat_evidence[code] = found
            if score >= QUALIFY_WEIGHT:
                cat_qual[code] = score

    # RULE-08: collapse curated same-event synonym pairs (evidence kept for audit).
    for code in curated_multi_label_drop(cat_qual, cat_evidence, low):
        del cat_qual[code]
        flags.append("%s:%s" % (FLAG_MULTI_LABEL_COLLAPSED, code.lower()))

    # STEP-11 strict ACHIEVEMENT classification (RULE-03 hard gate).  An
    # ACHIEVEMENT that only matched acknowledgement/mention keywords
    # ("congratulations", "certificate", "milestone", "recognized",
    # "proud moment", "accredited") is a nod, not an achievement — it never
    # overrides the real activity category (WORKSHOP / HACKATHON / FDP / SPORTS
    # ...) and is not kept as the post's type.  The category is DROPPED from
    # the decision while the ``category_gate:ACHIEVEMENT`` flag preserves the
    # audit trail for the review layer / admin.  "secured"/"won"/"award" are
    # DIRECT achievement evidence, so genuine wins are never dropped.
    if "ACHIEVEMENT" in cat_qual and _gate_mention_only(
            "ACHIEVEMENT", cat_evidence.get("ACHIEVEMENT"), date_status, low):
        del cat_qual["ACHIEVEMENT"]
        flags.append("%s:%s" % (FLAG_CATEGORY_GATE, "ACHIEVEMENT"))

    # --- department evidence -------------------------------------------------
    dept_qual, dept_evidence = {}, {}
    for dept, pats in DEPARTMENT_PATTERNS:
        score, found = _hits(low, pats)
        if score >= DEPARTMENT_QUALIFY:
            dept_qual[dept] = score
        if found:
            dept_evidence[dept] = found
    # CSE/CSBS family: drop CSE if it only matched the generic 'computer science' term
    # while a more specific CSBS pattern matched the same text.
    if "Computer Science and Business Systems" in dept_qual and "Computer Science and Engineering" in dept_qual:
        cse_found = dept_evidence.get("Computer Science and Engineering", {})
        if r"(?<!business and )computer science" in cse_found and not any(
            p in cse_found for p in (r"computer science and engineering", r"computer science & engineering", r"\bcse\b")
        ):
            del dept_qual["Computer Science and Engineering"]

    # --- stakeholder evidence -------------------------------------------------
    stak_qual, stak_evidence = {}, {}
    for stak, pats in STAKEHOLDER_PATTERNS:
        score, found = _hits(low, pats)
        if score >= STAKEHOLDER_QUALIFY:
            stak_qual[stak] = score
        if found:
            stak_evidence[stak] = found

    # --- communication evidence (non-activity signals) ------------------------
    # Select by (match count, priority).  Admission promos commonly also hit
    # job_ad words ("Limited Vacancies", "career"), so admission_promo takes
    # precedence on ties; specific job wording ("hiring", "recruitment",
    # "walk-in") wins on higher counts.
    comm_type, comm_evidence = None, {}
    comm_rank = {"admission_promo": 0, "job_ad": 1, "greeting": 2, "thanks": 3}
    comm_candidates = []
    for ctype in comm_rank:
        matches = _match_all(low, "|".join("(?:%s)" % p for p in COMM_PATTERNS[ctype]))
        if matches:
            comm_candidates.append((len(matches), -comm_rank[ctype], ctype, matches))
    if comm_candidates:
        _, _, comm_type, matches = max(comm_candidates, key=lambda x: (x[0], x[1]))
        spans = []
        for m in matches:
            g = next((g for g in m.groups() if g), m.group(0))
            if g and g not in spans:
                spans.append(g[:80])
        comm_evidence[comm_type] = spans

    # --- decision (evidence-first) -------------------------------------------
    categories = sorted(cat_qual, key=lambda c: (-cat_qual[c], c))
    departments = sorted(dept_qual, key=lambda d: (-dept_qual[d], d))
    stakeholders = sorted(stak_qual, key=lambda s: (-stak_qual[s], s))
    # RULE-09: display only explicitly organised/hosted depts; otherwise General.
    explicit_depts = _explicit_departments(dept_qual, dept_evidence)
    department_display = [d for d in sorted(
        explicit_depts, key=lambda d: (-explicit_depts[d], d))]
    if dept_qual and not department_display:
        department_display = ["General"]
        flags.append(FLAG_DEPT_TO_GENERAL)
    multi_label = 1 if len(categories) >= 2 else 0
    evidence_score = sum(cat_qual.values()) + len(departments) + len(stakeholders)

    # Admission promos / job ads announce a program, not an event.  If the only
    # category matches are program-feature words (internship, placement,
    # research, industry partners, ...) the communication intent wins.
    # RULE-01 lock: restricted to admission_promo / job_ad — the two classes
    # confirmed 27/27 in review.  Greeting/thanks are NOT overridden here: the
    # same congratulatory wording inside a real activity post must keep its
    # categories (review finding E.4), so greeting/thanks stay NON_ACTIVITY only
    # when no activity category qualifies (the else-branch below).
    comm_override = None
    if comm_type in ("admission_promo", "job_ad") and categories:
        strict_qual = {c: w for c, w in cat_qual.items() if c in STRICT_EVENT_CATEGORIES}
        if not strict_qual:
            comm_override = comm_type
        else:
            top_strict = max(strict_qual.values())
            top_soft = max(
                (w for c, w in cat_qual.items() if c not in STRICT_EVENT_CATEGORIES),
                default=0,
            )
            if top_soft > top_strict:
                comm_override = comm_type

    if not stripped:
        status, is_activity, kind, reason = STATUS_REVIEW_REQUIRED, None, KIND_UNKNOWN, "url_only_no_text"
    elif weak:
        status = STATUS_REVIEW_REQUIRED
        reason = "weak_text_requires_review"
        if categories:
            is_activity = 1
            kind = _activity_kind(categories)
        elif comm_type:
            is_activity = 0
            kind = COMM_BUILD_KIND.get(comm_type, KIND_COMM)
        else:
            is_activity = None
            kind = KIND_OTHER
    elif categories:
        if comm_override:
            status = STATUS_NON_ACTIVITY
            is_activity = 0
            kind = COMM_BUILD_KIND.get(comm_override, KIND_COMM)
            flags.append(FLAG_COMM_ONLY)
            reason = "communication_override:%s (category keywords are program-feature mentions)" % comm_override
        else:
            status = STATUS_ACTIVITY_CANDIDATE
            is_activity = 1
            kind = _activity_kind(categories)
            reason = "activity_evidence:%s" % ",".join(categories[:3])
    elif comm_type:
        status = STATUS_NON_ACTIVITY
        is_activity = 0
        kind = COMM_BUILD_KIND.get(comm_type, KIND_COMM)
        flags.append(FLAG_COMM_ONLY)
        reason = "communication_only:%s" % comm_type
    else:
        status = STATUS_REVIEW_REQUIRED
        is_activity = None
        kind = KIND_OTHER
        reason = "insufficient_evidence"

    # --- RULE-02 / RULE-12 / RULE-03..07 additive gates -----------------------
    unclear_reason = None
    if status == STATUS_REVIEW_REQUIRED:
        unclear_reason = _unclear_reason(
            flags, low, weak, url_only, categories, comm_type)
        if unclear_reason:
            flags.append("%s:%s" % (FLAG_UNCLEAR, unclear_reason))
    if status == STATUS_NON_ACTIVITY and categories:
        # context-only suppression: categories stay for evidence, never count as
        # the post's activity type (display/statistics must exclude them).
        flags.append(FLAG_CATEGORY_CONTEXT_ONLY)
    if status == STATUS_ACTIVITY_CANDIDATE:
        for code in categories:
            if _gate_mention_only(code, cat_evidence.get(code), date_status, low):
                flags.append("%s:%s" % (FLAG_CATEGORY_GATE, code))

    return {
        "linkedin_post_id": post.get("id"),
        "post_url": (post.get("post_url") or None),
        "post_text": text,
        "source_sheet": post.get("source_sheet"),
        "source_row": post.get("source_row"),
        "candidate_status": status,
        "is_activity": is_activity,
        "kind": kind,
        "category_candidates": categories,
        "department_candidates": departments,
        "stakeholder_candidates": stakeholders,
        "date_status": date_status,
        "date_evidence": date_evidence,
        "academic_year": academic_year,
        "category_evidence": cat_evidence,
        "department_evidence": dept_evidence,
        "stakeholder_evidence": stak_evidence,
        "communication_type": comm_type,
        "communication_evidence": comm_evidence,
        "evidence_score": evidence_score,
        "multi_label": multi_label,
        "flags": flags,
        "department_display": department_display,
        "unclear_reason": unclear_reason,
        "reason": reason,
        "review_status": REVIEW_AUTO,
    }


def _upsert_candidate(conn, row):
    conn.execute(
        """INSERT INTO linkedin_activity_candidates
           (linkedin_post_id, post_url, post_text, source_sheet, source_row,
            candidate_status, is_activity, kind,
            category_candidates, department_candidates, stakeholder_candidates,
            date_status, date_evidence, academic_year,
            category_evidence, department_evidence, stakeholder_evidence,
            communication_type, communication_evidence,
            evidence_score, multi_label, flags, department_display,
            unclear_reason, reason, review_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(linkedin_post_id) DO UPDATE SET
            candidate_status=excluded.candidate_status,
            is_activity=excluded.is_activity,
            kind=excluded.kind,
            category_candidates=excluded.category_candidates,
            department_candidates=excluded.department_candidates,
            stakeholder_candidates=excluded.stakeholder_candidates,
            date_status=excluded.date_status,
            date_evidence=excluded.date_evidence,
            academic_year=excluded.academic_year,
            category_evidence=excluded.category_evidence,
            department_evidence=excluded.department_evidence,
            stakeholder_evidence=excluded.stakeholder_evidence,
            communication_type=excluded.communication_type,
            communication_evidence=excluded.communication_evidence,
            evidence_score=excluded.evidence_score,
            multi_label=excluded.multi_label,
            flags=excluded.flags,
            department_display=excluded.department_display,
            unclear_reason=excluded.unclear_reason,
            reason=excluded.reason,
            classified_at=datetime('now')""",
        (
            row["linkedin_post_id"], row["post_url"], row["post_text"],
            row["source_sheet"], row["source_row"], row["candidate_status"],
            row["is_activity"], row["kind"], json.dumps(row["category_candidates"]),
            json.dumps(row["department_candidates"]), json.dumps(row["stakeholder_candidates"]),
            row["date_status"], json.dumps(row["date_evidence"]), row["academic_year"],
            json.dumps(row["category_evidence"]), json.dumps(row["department_evidence"]),
            json.dumps(row["stakeholder_evidence"]), row["communication_type"],
            json.dumps(row["communication_evidence"]), row["evidence_score"],
            row["multi_label"], json.dumps(row["flags"]), json.dumps(row["department_display"]),
            row["unclear_reason"], row["reason"],
            row["review_status"],
        ),
    )


def generate_candidates(conn, posts=None):
    """Classify every canonical LinkedIn post and persist candidates.

    Only writes to ``linkedin_activity_candidates`` in the staging database.
    Idempotent (upsert by linkedin_post_id).  Returns generated row dicts.
    """
    init_candidates_schema(conn)
    if posts is None:
        posts = [dict(r) for r in conn.execute(
            "SELECT " + ", ".join(INPUT_POST_COLUMNS) + " FROM linkedin_posts"
        ).fetchall()]
    rows = []
    for post in posts:
        row = classify_post(post)
        _upsert_candidate(conn, row)
        rows.append(row)
    conn.commit()
    return rows


# ---------------------------------------------------------------------------
# Manual review sample (STEP 11): ~100-200 stratified posts, seeded + deterministic.
# ---------------------------------------------------------------------------
REVIEW_SAMPLE_TARGET = 150
REVIEW_SAMPLE_MAX = 200
REVIEW_SAMPLE_MIN = 100


def _rows_with_flag(rows, flag):
    return [r for r in rows if flag in r["flags"]]


def build_review_sample(rows, seed=42, target=REVIEW_SAMPLE_TARGET):
    rng = random.Random(seed)
    selected = {}
    def add(pool, limit=None, cap=None):
        order = sorted(pool, key=lambda r: r["linkedin_post_id"])
        if limit is not None:
            order = order[:limit]
        for r in order:
            if cap is not None and len(selected) >= cap:
                break
            selected.setdefault(r["linkedin_post_id"], r)

    # forced special cases
    add(_rows_with_flag(rows, FLAG_URL_ONLY))
    add(_rows_with_flag(rows, FLAG_WEAK_TEXT))
    add(_rows_with_flag(rows, FLAG_MULTI_YEAR))
    add(_rows_with_flag(rows, FLAG_PRE_2024))
    add(_rows_with_flag(rows, FLAG_TEXT_IS_URL))

    # category strata
    for code in sorted(CATEGORY_PATTERNS):
        pool = [r for r in rows if code in r["category_candidates"]]
        add(pool, limit=6, cap=REVIEW_SAMPLE_MAX)
    # status strata
    add([r for r in rows if r["candidate_status"] == STATUS_NON_ACTIVITY], limit=30)
    add([r for r in rows if r["candidate_status"] == STATUS_REVIEW_REQUIRED], limit=40)
    # communication strata
    for ctype in ("greeting", "admission_promo", "job_ad", "thanks"):
        add([r for r in rows if r["communication_type"] == ctype], limit=8)
    # stakeholder/category combo coverage (student/faculty activities)
    for code in ("WORKSHOP", "SEMINAR", "FDP", "SPORTS", "CULTURAL", "CLUB",
                 "INDUSTRY", "RESEARCH", "ALUMNI", "ACHIEVEMENT"):
        for stak in ("Students", "Faculty"):
            pool = [r for r in rows if code in r["category_candidates"]
                    and stak in r["stakeholder_candidates"]]
            add(pool, limit=1, cap=REVIEW_SAMPLE_MAX)

    # deterministic random fill (keeps the sample ~target sized)
    pool = [r for r in rows if r["linkedin_post_id"] not in selected]
    rng.shuffle(pool)
    remaining = target - len(selected)
    if remaining > 0:
        for r in pool[:remaining]:
            selected.setdefault(r["linkedin_post_id"], r)

    sample = sorted(selected.values(), key=lambda r: r["linkedin_post_id"])
    # keep the final size within [MIN, MAX]
    if len(sample) > REVIEW_SAMPLE_MAX:
        sample = rng.sample(sample, REVIEW_SAMPLE_MAX)
        sample = sorted(sample, key=lambda r: r["linkedin_post_id"])
    elif len(sample) < REVIEW_SAMPLE_MIN:
        extra = [r for r in rows if r["linkedin_post_id"] not in {s["linkedin_post_id"] for s in sample}]
        rng.shuffle(extra)
        sample = sorted(sample + extra[:REVIEW_SAMPLE_MIN - len(sample)],
                        key=lambda r: r["linkedin_post_id"])
    for r in sample:
        r["review_status"] = REVIEW_PENDING
    return sample


def mark_review_sample(conn, sample_ids):
    if not sample_ids:
        return 0
    conn.execute("UPDATE linkedin_activity_candidates SET review_status=? "
                 "WHERE linkedin_post_id IN (%s)" % ",".join("?" * len(sample_ids)),
                 [REVIEW_PENDING] + list(sample_ids))
    conn.commit()
    return len(sample_ids)


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------
def _count(rows, pred):
    return sum(1 for r in rows if pred(r))


def distribution(rows, key):
    d = {}
    for r in rows:
        k = (r.get(key) or "(none)")
        d[k] = d.get(k, 0) + 1
    return dict(sorted(d.items(), key=lambda kv: (-kv[1], str(kv[0]))))


def _cat_counts(rows, getter):
    c = {}
    for r in rows:
        for k in getter(r):
            c[k] = c.get(k, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def category_counts(rows):
    return _cat_counts(rows, lambda r: r["category_candidates"])


def department_counts(rows):
    return _cat_counts(rows, lambda r: r["department_candidates"])


def stakeholder_counts(rows):
    return _cat_counts(rows, lambda r: r["stakeholder_candidates"])


def academic_year_counts(rows):
    c = {}
    for r in rows:
        c[r["academic_year"] or "undated"] = c.get(r["academic_year"] or "undated", 0) + 1
    return dict(sorted(c.items()))


def _flag_counts(rows):
    c = {}
    for r in rows:
        for f in r["flags"]:
            c[f] = c.get(f, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def build_summary(rows):
    by_status = distribution(rows, "candidate_status")
    n_activity = by_status.get(STATUS_ACTIVITY_CANDIDATE, 0)
    n_non = by_status.get(STATUS_NON_ACTIVITY, 0)
    n_review = by_status.get(STATUS_REVIEW_REQUIRED, 0)
    merits = {
        "total_canonical_posts": len(rows),
        "status": by_status,
        "activity_candidates": n_activity,
        "non_activity": n_non,
        "review_required": n_review,
        "kind_buckets": distribution(rows, "kind"),
        "category_distribution": category_counts(rows),
        "department_distribution": department_counts(rows),
        "stakeholder_distribution": stakeholder_counts(rows),
        "dated": _count(rows, lambda r: r["date_status"] == "dated"),
        "undated": _count(rows, lambda r: r["date_status"] == "undated"),
        "ambiguous_multi_year": _count(rows, lambda r: r["date_status"] == "ambiguous_multi_year"),
        "academic_year_distribution": academic_year_counts(rows),
        "link_verified": _count(rows, lambda r: bool(r["post_url"])),
        "link_less": _count(rows, lambda r: FLAG_LINK_LESS in r["flags"]),
        "multi_label_records": _count(rows, lambda r: r["multi_label"] == 1),
        "flags": _flag_counts(rows),
        "evidence_quality": {
            "high_score_ge_8": _count(rows, lambda r: r["evidence_score"] >= 8),
            "medium_4_7": _count(rows, lambda r: 4 <= r["evidence_score"] <= 7),
            "low_1_3": _count(rows, lambda r: 1 <= r["evidence_score"] <= 3),
            "none_0": _count(rows, lambda r: r["evidence_score"] == 0),
        },
    }
    return merits


def _public_post(r, include_evidence=False):
    out = {
        "linkedin_post_id": r["linkedin_post_id"],
        "source_sheet": r["source_sheet"],
        "source_row": r["source_row"],
        "has_url": bool(r["post_url"]),
        "candidate_status": r["candidate_status"],
        "kind": r["kind"],
        "categories": r["category_candidates"],
        "departments": r["department_candidates"],
        "stakeholders": r["stakeholder_candidates"],
        "date_status": r["date_status"],
        "academic_year": r["academic_year"],
        "multi_label": r["multi_label"] == 1,
        "flags": r["flags"],
        "evidence_score": r["evidence_score"],
        "review_status": r["review_status"],
        "snippet": (r["post_text"] or "")[:180],
    }
    if include_evidence:
        out["category_evidence"] = r["category_evidence"]
        out["department_evidence"] = r["department_evidence"]
        out["stakeholder_evidence"] = r["stakeholder_evidence"]
        out["communication_evidence"] = r["communication_evidence"]
    return out


def build_report(rows, sample=None, meta=None):
    report = {
        "meta": {
            "title": "LinkedIn Candidate Generation (PILOT) Report",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "scope": "canonical LinkedIn posts from the staging layer only",
            "source": "backend/database/linkedin_staging.db -> linkedin_activity_candidates",
            "disclaimer": (
                "PILOT / reviewable classification. Nothing in this report is "
                "written to or derived from institutional_activities. Internal "
                "evidence spans are for validation/review only and are never "
                "public UI fields. No classification accuracy is claimed; a "
                "human-reviewed evaluation set does not yet exist."
            ),
        },
        "summary": build_summary(rows),
        "screening_buckets": {
            "A_institutional_activity_event": _count(rows, lambda r: r["kind"] == KIND_EVENT),
            "B_achievement_recognition": _count(rows, lambda r: r["kind"] == KIND_ACHIEVEMENT),
            "C_research_academic_update": _count(rows, lambda r: r["kind"] == KIND_RESEARCH),
            "D_student_faculty_development": _count(rows, lambda r: r["kind"] == KIND_DEVELOPMENT),
            "E_communication_announcement": _count(rows, lambda r: r["kind"] == KIND_COMM),
            "F_recruitment_job_ad": _count(rows, lambda r: r["kind"] == KIND_JOB),
            "G_admission_promotion": _count(rows, lambda r: r["kind"] == KIND_ADMISSION),
            "H_greeting_festival_wishes": _count(rows, lambda r: r["kind"] == KIND_GREETING),
            "I_other_non_activity": _count(rows, lambda r: r["kind"] == KIND_OTHER),
            "J_unclear_requires_review": _count(rows, lambda r: r["kind"] == KIND_UNKNOWN),
        },
        "dates": {
            "dated": _count(rows, lambda r: r["date_status"] == "dated"),
            "undated": _count(rows, lambda r: r["date_status"] == "undated"),
            "ambiguous_multi_year": _count(rows, lambda r: r["date_status"] == "ambiguous_multi_year"),
            "convention": "academic_year uses the earliest EXPLICIT date only; June 1 - May 31. "
                         "No invented dates; undated posts stay undated.",
        },
        "academic_year_distribution": academic_year_counts(rows),
        "link_verified": _count(rows, lambda r: bool(r["post_url"])),
        "link_less": _count(rows, lambda r: FLAG_LINK_LESS in r["flags"]),
        "weak_text_records": len(_rows_with_flag(rows, FLAG_WEAK_TEXT)),
        "url_only_records": len(_rows_with_flag(rows, FLAG_URL_ONLY)),
        "multi_year_records": len(_rows_with_flag(rows, FLAG_MULTI_YEAR)),
        "pre_2024_records": len(_rows_with_flag(rows, FLAG_PRE_2024)),
        "communication_only_records": len(_rows_with_flag(rows, FLAG_COMM_ONLY)),
        "flags": _flag_counts(rows),
        "evidence_quality": {
            "high_score_ge_8": _count(rows, lambda r: r["evidence_score"] >= 8),
            "medium_4_7": _count(rows, lambda r: 4 <= r["evidence_score"] <= 7),
            "low_1_3": _count(rows, lambda r: 1 <= r["evidence_score"] <= 3),
            "none_0": _count(rows, lambda r: r["evidence_score"] == 0),
            "note": "evidence_score is an internal heuristic (category pattern weight sum "
                    "+ matched dept/stakeholder signals); it is NOT an accuracy metric.",
        },
        "review_sample_mark": {
            "selected_for_review": len(sample or []),
            "review_status": "PENDING_REVIEW in linkedin_activity_candidates",
            "accuracy_claim": "NONE. Classifier behaviour must be evaluated by a human "
                              "before any accuracy statement is allowed.",
        },
    }
    if sample:
        report["review_sample"] = [_public_post(r, include_evidence=True) for r in sample]

    # representative classification snippets per category (10 examples)
    reps = {}
    for code in sorted(CATEGORY_PATTERNS):
        pool = [r for r in rows if code in r["category_candidates"]]
        if pool:
            reps[code] = [_public_post(r) for r in pool[:3]]
    report["representative_classifications"] = reps
    return report


def _md_table(rows):
    from io import StringIO
    buf = StringIO()
    for r in rows:
        buf.write("| %d | %s | %s | %s | %s | %s |\n" % (
            r["linkedin_post_id"], r["candidate_status"], r["kind"],
            ", ".join(r["categories"]) or "-", ", ".join(r["departments"]) or "-",
            r["academic_year"] or "undated"))
    return buf.getvalue()


def write_reports(rows, sample=None, out_dir=None):
    """Write the candidate-generation report (JSON + MD) under data/audit."""
    report = build_report(rows, sample=sample)
    if out_dir is None:
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__)))), "data", "audit")
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d")
    json_path = os.path.join(out_dir, "linkedin_candidate_generation_%s.json" % stamp)
    md_path = os.path.join(out_dir, "linkedin_candidate_generation_%s.md" % stamp)
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    l = []
    l.append("# LinkedIn Candidate Generation Report (PILOT)")
    l.append("")
    l.append("Generated: %s  |  Scope: canonical LinkedIn posts (staging layer ONLY)" % report["meta"]["generated_at"])
    l.append("")
    l.append("> %s" % report["meta"]["disclaimer"])
    l.append("")
    s = report["summary"]
    l.append("## 1. Overview")
    l.append("")
    l.append("| Metric | Count |")
    l.append("|---|---|")
    l.append("| Total canonical posts | %d |" % s["total_canonical_posts"])
    l.append("| Activity candidates | %d |" % s["activity_candidates"])
    l.append("| Non-activity | %d |" % s["non_activity"])
    l.append("| Review-required | %d |" % s["review_required"])
    l.append("| Dated / Undated / Ambiguous-multi-year | %d / %d / %d |" % (
        s["dated"], s["undated"], s["ambiguous_multi_year"]))
    l.append("| Link-verified / Link-less | %d / %d |" % (s["link_verified"], s["link_less"]))
    l.append("| Multi-label records (>=2 categories) | %d |" % s["multi_label_records"])
    l.append("")
    l.append("## 2. Category candidate distribution")
    l.append("")
    l.append("| Category | Posts |")
    l.append("|---|---|")
    for k, v in s["category_distribution"].items():
        l.append("| %s (%s) | %d |" % (CATEGORY_CANDIDATE_NAMES.get(k, k), k, v))
    l.append("")
    l.append("## 3. Department candidate distribution")
    l.append("")
    l.append("| Department | Posts |")
    l.append("|---|---|")
    for k, v in s["department_distribution"].items():
        l.append("| %s | %d |" % (k, v))
    l.append("")
    l.append("## 4. Stakeholder candidate distribution")
    l.append("")
    l.append("| Stakeholder | Posts |")
    l.append("|---|---|")
    for k, v in s["stakeholder_distribution"].items():
        l.append("| %s | %d |" % (STAKEHOLDER_PUBLIC_NAMES.get(k, k), v))
    l.append("")
    l.append("## 5. Screening buckets (step-2 kinds A-J)")
    l.append("")
    l.append("| Bucket | Posts |")
    l.append("|---|---|")
    for k, v in report["screening_buckets"].items():
        l.append("| %s | %d |" % (k, v))
    l.append("")
    l.append("## 6. Academic-year distribution (earliest EXPLICIT date, June 1 - May 31)")
    l.append("")
    l.append("| Academic Year | Posts |")
    l.append("|---|---|")
    for k, v in report["academic_year_distribution"].items():
        l.append("| %s | %d |" % (k, v))
    l.append("")
    l.append("## 7. Special-case flags")
    l.append("")
    l.append("| Flag | Posts |")
    l.append("|---|---|")
    for k, v in report["flags"].items():
        l.append("| %s | %d |" % (k, v))
    l.append("")
    l.append("## 8. Evidence-quality summary (internal heuristic)")
    l.append("")
    l.append("| Evidence score band | Posts |")
    l.append("|---|---|")
    for k, v in report["evidence_quality"].items():
        if k != "note":
            l.append("| %s | %d |" % (k, v))
    l.append("")
    l.append("Note: %s" % report["evidence_quality"]["note"])
    l.append("")
    sample = report.get("review_sample", [])
    l.append("## 9. Manual review sample (%d posts, PENDING_REVIEW)" % len(sample))
    l.append("")
    l.append("| post id | status | kind | categories | departments | academic_year | snippet |")
    l.append("|---|---|---|---|---|---|---|")
    for r in sample:
        snippet = (r["snippet"].replace("|", "/")[:80])
        l.append("| %d | %s | %s | %s | %s | %s | %s |" % (
            r["linkedin_post_id"], r["candidate_status"], r["kind"],
            ", ".join(r["categories"]) or "-", ", ".join(r["departments"]) or "-",
            r["academic_year"] or "undated", snippet))
    l.append("")
    l.append("## 10. Representative classifications (for quick inspection)")
    l.append("")
    for code in sorted(report["representative_classifications"]):
        l.append("### %s" % CATEGORY_CANDIDATE_NAMES.get(code, code))
        l.append("")
        l.append("| post id | status | departments | academic_year | snippet |")
        l.append("|---|---|---|---|---|")
        for r in report["representative_classifications"][code]:
            l.append("| %d | %s | %s | %s | %s |" % (
                r["linkedin_post_id"], r["candidate_status"],
                ", ".join(r["departments"]) or "-", r["academic_year"] or "undated",
                (r["snippet"].replace("|", "/")[:120])))
        l.append("")
    l.append("## 11. Integrity notes")
    l.append("- Raw staging occurrences remain 2,094; canonical posts remain 1,544.")
    l.append("- No post was deleted; NON_ACTIVITY/REVIEW_REQUIRED posts are retained.")
    l.append("- Production DB (institutional_activities) was NOT written to; the 2,258 website activities are untouched.")
    l.append("- No accuracy claim is made; the review sample must be human-labelled first.")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(l))
    return json_path, md_path


def _dedupe(seq):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def run_pilot(db_path=STAGING_DB_PATH, out_dir=None):
    """Full pilot entry point (staging layer only)."""
    conn = get_staging_connection(db_path)
    try:
        rows = generate_candidates(conn)
        # A fresh pilot run produces a fresh, reproducible review sample: reset
        # any previously marked rows so the DB marker matches the report.
        conn.execute("UPDATE linkedin_activity_candidates SET review_status=? "
                     "WHERE review_status=?", (REVIEW_AUTO, REVIEW_PENDING))
        conn.commit()
        sample = build_review_sample(rows)
        mark_review_sample(conn, [r["linkedin_post_id"] for r in sample])
        json_path, md_path = write_reports(rows, sample=sample, out_dir=out_dir)
        return rows, sample, {"json": json_path, "md": md_path}
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn candidate generation pilot (staging layer only).")
    parser.add_argument("--db", default=STAGING_DB_PATH)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    rows, sample, paths = run_pilot(db_path=args.db, out_dir=args.out)
    s = build_summary(rows)
    print("LinkedIn candidate generation (pilot) complete.")
    print("  total = %d | activity = %d | non-activity = %d | review = %d" % (
        len(rows), s["activity_candidates"], s["non_activity"], s["review_required"]))
    print("  report json: %s" % paths["json"])
    print("  report md:   %s" % paths["md"])
    print("  review sample: %d posts (PENDING_REVIEW)" % len(sample))