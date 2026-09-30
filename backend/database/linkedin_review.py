"""LinkedIn candidate MANUAL REVIEW / VALIDATION stage (PILOT, review layer ONLY).

Loads the 200-post ``PENDING_REVIEW`` sample produced by
``backend/database/linkedin_candidates.py``, runs human-review heuristics that
propose *corrections / review decisions*, groups every sampled post into the
priority buckets A-H, and writes the manual-review report
(``data/audit/linkedin_manual_review_20260923.{json,md,csv}``).

HARD GUARANTEES (enforced by design):
  * ``linkedin_activity_candidates``, ``linkedin_posts`` and
    ``linkedin_post_occurrences`` are only ever READ.  Nothing is updated,
    deleted, re-classified, or merged with the 2,258 website activities.
  * The production database (``tce_activity_intelligence.db``) and
    ``merged-workbook.xlsx`` are never opened for writing.
  * All proposed corrections/review decisions are recorded in the REVIEW LAYER
    ONLY: a dedicated ``linkedin_manual_review_proposals`` table in the staging
    database plus the report artifacts under ``data/audit``.
  * Evidence-first and no accuracy claim: every proposal is a low/medium/high
    confidence review aid for a human; it is never applied automatically.
  * Academic year: explicit dates only, June 1 - May 31.  Undated posts stay
    undated; ambiguous multi-year posts stay flagged; no date is invented.
"""

import csv
import json
import os
import re
from datetime import datetime

from backend.database.linkedin_candidates import (
    CATEGORY_CANDIDATE_NAMES,
    CATEGORY_PATTERNS,
    FLAG_MULTI_YEAR,
    FLAG_PRE_2024,
    REVIEW_PENDING,
    REVIEW_SAMPLE_MAX,
    STAKEHOLDER_PUBLIC_NAMES,
    STATUS_ACTIVITY_CANDIDATE,
    STATUS_NON_ACTIVITY,
    STATUS_REVIEW_REQUIRED,
    STRICT_EVENT_CATEGORIES,
    _academic_year,
    _hits,
    _lower_clean,
    _match_all,
)
from backend.database.linkedin_staging import STAGING_DB_PATH, get_staging_connection

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT_DIR = os.path.normpath(os.path.join(_HERE, "..", "..", "data", "audit"))
REPORT_BASENAME = "linkedin_manual_review_20260923"

# ---------------------------------------------------------------------------
# Review groups (priority buckets A-H for the human reviewer).
# NOTE: these are review-priority groups and are deliberately distinct from the
# step-2 screening kinds A-J stored in linkedin_activity_candidates.kind.
# ---------------------------------------------------------------------------
REVIEW_GROUP_ORDER = ("A", "B", "C", "D", "E", "F", "G", "H")

REVIEW_GROUP_LABELS = {
    "A": "Activity - likely correct",
    "B": "Activity - category correction proposed",
    "C": "Activity - department correction proposed",
    "D": "Activity - stakeholder correction proposed",
    "E": "Non-activity - likely correct",
    "F": "Non-activity - should be activity (embedded event)",
    "G": "Review / unclear",
    "H": "Activity - date / academic-year issue",
}

REVIEW_GROUP_DESCRIPTIONS = {
    "A": "ACTIVITY_CANDIDATE with no field-level correction proposed. "
         "Confirm the activity type from the text and approve.",
    "B": "ACTIVITY_CANDIDATE where a category looks over-tagged or overlapping. "
         "Special attention: ACHIEVEMENT, RESEARCH, ALUMNI, INTERNSHIP, "
         "PLACEMENT, INDUSTRY, CAMPUS.",
    "C": "ACTIVITY_CANDIDATE where the department was inferred from generic "
         "technical terminology rather than an explicit department statement. "
         "Institution-wide activities should be marked General.",
    "D": "ACTIVITY_CANDIDATE where the stakeholder may have been inferred from "
         "an isolated word instead of an intended audience/participant.",
    "E": "NON_ACTIVITY (admission promo / job ad / greeting / announcement / "
         "thanks) with no embedded event detected. Confirm the communication "
         "separation and that no real event is hidden in the text.",
    "F": "NON_ACTIVITY that appears to contain a genuine embedded event "
         "(strong event term + explicit date). Proposes promoting the post to "
         "ACTIVITY_CANDIDATE.",
    "G": "REVIEW_REQUIRED: the classifier could not decide (weak/url-only text "
         "or insufficient evidence). Human decides from the text and URL.",
    "H": "ACTIVITY_CANDIDATE with a date/academic-year issue: multi-year "
         "ambiguity, pre-2024 evidence, or academic-year mismatch. Keep "
         "ambiguous/undated as flagged; never invent a date.",
}

GUIDELINES = [
    "Groups A-H are review-priority buckets; they are NOT the step-2 screening "
    "kinds A-J stored in linkedin_activity_candidates.kind.",
    "Every proposal is a PROPOSED correction/review decision recorded in the "
    "review layer only (linkedin_manual_review_proposals table + this report). "
    "Nothing is applied to linkedin_activity_candidates, the production "
    "database, or merged-workbook.xlsx.",
    "Evidence-first: confirm from the post text (and the URL when present) "
    "before accepting a proposal; reject any proposal the text does not support.",
    "Academic year uses EXPLICIT dates only, June 1 - May 31. Undated posts "
    "stay undated; ambiguous multi-year posts stay flagged; no date is invented "
    "from sheet names or surrounding posts.",
    "Department must come from explicit evidence in the post. Generic technical "
    "terminology is not department evidence; institution-wide activities should "
    "be marked General.",
    "Stakeholder is the intended audience/participants of the activity, not an "
    "isolated word inside an unrelated sentence or a profile/bio line.",
    "Multi-label categories are kept only when the post genuinely reports "
    "multiple distinct activity types; same-event synonyms should collapse to "
    "the dominant category.",
    "Communication separation: admission promos, job ads, greetings, "
    "congratulations, general announcements and thanks are NON_ACTIVITY; a "
    "genuine event embedded in such a post must be promoted (group F).",
    "Over-tag attention categories: ACHIEVEMENT, RESEARCH, ALUMNI, "
    "INTERNSHIP, PLACEMENT, INDUSTRY, CAMPUS - keyword mentions of these in "
    "promos/profiles do not make the post an instance of that activity.",
    "No accuracy claim is made; this report is a review aid for a human "
    "evaluator. The classifier must be scored against the human labels.",
]

# ---------------------------------------------------------------------------
# Over-tag attention (the 7 categories most likely to be keyword-over-tagged).
# A category is flagged for review when ALL of its matched evidence patterns
# are generic mention-style terms (no direct 'this post is about X' evidence).
# ---------------------------------------------------------------------------
OVER_TAG_CATEGORIES = ("ACHIEVEMENT", "RESEARCH", "ALUMNI", "INTERNSHIP",
                       "PLACEMENT", "INDUSTRY", "CAMPUS")

# Mention-style evidence patterns per attention category.  Keys must match the
# pattern strings used in linkedin_candidates.CATEGORY_PATTERNS exactly
# (they are stored verbatim as keys in the category_evidence JSON).
OVER_TAG_MENTION_PATTERNS = {
    "ACHIEVEMENT": {
        r"congratulat", r"certificat", r"milestone", r"secured",
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

# Categories where a mention-only flag is suppressed when the post carries a
# date-ish context: a dated/duration internship or placement announcement is a
# real programme, not a keyword mention.
MENTION_ONLY_SKIP_WHEN_DATED = ("INTERNSHIP", "PLACEMENT")

MONTH_TOKEN_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"january|february|march|april|june|july|august|september|"
    r"october|november|december)\b", re.I)
YEAR_TOKEN_RE = re.compile(r"\b20(?:2[0-9]|30)\b")

# Positive signal that a post is genuinely ABOUT an alum (a feature/spotlight),
# not merely mentioning the alumni network.  These make the ALUMNI mention-only
# flag unnecessary (the post is clearly an alumni activity).
ALUMNI_FEATURE_RE = re.compile(
    r"#alumni|alumni\s*(?:spotlight|story|feature|of the week)|"
    r"alumn(?:us|a)\s*of\s*the\s*(?:week|year)", re.I)

# ---------------------------------------------------------------------------
# Department over-inference: generic technical terminology that is a TOPIC, not
# department evidence.  Keys are canonical department names as stored in
# DEPARTMENT_PATTERNS; values are pattern strings copied verbatim from there.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Stakeholder over-inference: isolated words that do not identify an audience.
# ---------------------------------------------------------------------------
ISOLATED_STAKEHOLDER_PATTERNS = {
    "Alumni": {r"19\d\d[- ]20\d\d", r"\bbatch\b", r"\bpatch\b"},
    "Industry": {r"\bcompany\b", r"\bpartner\b", r"corporate"},
    "Community and Society": {r"\bsociety\b", r"\bschool\b"},
    "Students": {r"\bfresher\b", r"young artists"},
}

# Category pairs that commonly describe the SAME event (multi-label collapse
# check).  Parallel-event categories (WORKSHOP/HACKATHON/CULTURAL/SPORTS) are
# intentionally excluded: festivals really do run several activity types.
SEMANTIC_OVERLAP_GROUPS = frozenset({
    "CONFERENCE", "SYMPOSIUM", "SEMINAR", "GUEST_LECTURE", "FDP", "STTP",
    "WEBINAR", "TECH_FEST",
})

# Facility words around an event term ("seminar hall", "workshop facilities")
# mean the term describes infrastructure, not a scheduled event.
FACILITY_CONTEXT_RE = re.compile(
    r"\b(hall|room|facilit|laborator|lab|infrastructure|equipment)\b", re.I)

# Minimum summed weight of matched STRICT-event patterns before an embedded
# event is even proposed for a communication post.
STRONG_EVENT_MIN_WEIGHT = 4

# Date/academic-year rules that place an activity post in group H.
DATE_ISSUE_RULES = frozenset({"ay_mismatch", "multi_year_keep", "pre_2024_keep"})

# ---------------------------------------------------------------------------
# Review-layer schema (staging DB only; separate from the candidates table).
# ---------------------------------------------------------------------------
REVIEW_PROPOSALS_SCHEMA = """
CREATE TABLE IF NOT EXISTS linkedin_manual_review_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linkedin_post_id INTEGER NOT NULL REFERENCES linkedin_posts(id),
    field TEXT NOT NULL,                -- status|category|department|stakeholder|academic_year|date
    rule TEXT NOT NULL,                 -- heuristic rule id
    is_correction INTEGER NOT NULL DEFAULT 0 CHECK (is_correction IN (0, 1)),
    confidence TEXT NOT NULL,           -- low|medium|high
    current TEXT,                       -- current value / evidence summary
    proposed TEXT,                      -- PROPOSED correction / review decision
    rationale TEXT,
    evidence_spans TEXT,                -- JSON list (INTERNAL ONLY)
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_linkedin_review_props_post
    ON linkedin_manual_review_proposals(linkedin_post_id);
"""


def init_review_schema(conn):
    conn.executescript(REVIEW_PROPOSALS_SCHEMA)
    conn.commit()


# ---------------------------------------------------------------------------
# Proposal helpers
# ---------------------------------------------------------------------------
def _proposal(field, rule, is_correction, confidence, current, proposed,
              rationale, evidence_spans=None):
    return {
        "field": field,
        "rule": rule,
        "is_correction": bool(is_correction),
        "confidence": confidence,
        "current": current,
        "proposed": proposed,
        "rationale": rationale,
        "evidence_spans": list(evidence_spans or []),
    }


def _spans(ev):
    """Flatten a {pattern: [matched snippets]} evidence dict into a list."""
    out = []
    for snippets in (ev or {}).values():
        for s in snippets:
            if s not in out:
                out.append(s)
    return out


def rec_low_text(rec):
    return _lower_clean(rec.get("post_text") or "")


def _has_dateish(rec):
    """Cheap date context: an explicit date, a year token, or any month word."""
    low = rec_low_text(rec)
    return bool(YEAR_TOKEN_RE.search(low) or MONTH_TOKEN_RE.search(low))


# ---------------------------------------------------------------------------
# Heuristic 1 - over-tagging of the 7 attention categories (group B)
# ---------------------------------------------------------------------------
def propose_category_over_tag(rec):
    """Flag attention categories whose ONLY evidence is mention-style keywords.

    Only meaningful for posts already classified as activities: for NON_ACTIVITY
    posts the category candidates are deliberately kept as program-feature
    mention context (see propose_comm_separation), not as a classification.
    """
    if rec.get("candidate_status") != STATUS_ACTIVITY_CANDIDATE:
        return []
    out = []
    for code in rec.get("category_candidates") or []:
        mention = OVER_TAG_MENTION_PATTERNS.get(code)
        if not mention:
            continue
        ev = (rec.get("category_evidence") or {}).get(code)
        if not ev:
            continue
        if not set(ev.keys()) <= mention:
            continue  # at least one direct (non-mention) pattern matched
        if code in MENTION_ONLY_SKIP_WHEN_DATED:
            if rec.get("date_status") == "dated" or _has_dateish(rec):
                continue  # dated/duration internship|placement = real programme
        if code == "ALUMNI" and ALUMNI_FEATURE_RE.search(rec_low_text(rec)):
            continue  # explicitly an alumni feature/spotlight -> genuinely alumni
        out.append(_proposal(
            field="category",
            rule="cat_over_tag:%s" % code,
            is_correction=True,
            confidence="low",
            current=code,
            proposed="verify over-tag: remove %s unless the text is clearly about it"
                     % CATEGORY_CANDIDATE_NAMES.get(code, code),
            rationale="%s qualified via mention-style keyword(s) only "
                      "(%s); a keyword mention does not make the post an "
                      "instance of this activity."
                      % (code, ", ".join(_spans(ev)) or "n/a"),
            evidence_spans=_spans(ev),
        ))
    return out


# ---------------------------------------------------------------------------
# Heuristic 2 - department inferred from generic technical terms (group C)
# ---------------------------------------------------------------------------
def _has_explicit_dept_evidence(rec):
    """True when some department matched via an explicit (non-generic) pattern."""
    for dept, ev in (rec.get("department_evidence") or {}).items():
        generic = GENERIC_DEPT_PATTERNS.get(dept, set())
        if any(pat not in generic for pat in ev):
            return True
    return False


def propose_department_generic(rec):
    if rec.get("candidate_status") != STATUS_ACTIVITY_CANDIDATE:
        return []
    out = []
    explicit_present = _has_explicit_dept_evidence(rec)
    for dept in rec.get("department_candidates") or []:
        generic = GENERIC_DEPT_PATTERNS.get(dept)
        if not generic:
            continue
        ev = (rec.get("department_evidence") or {}).get(dept)
        if not ev:
            continue
        if not set(ev.keys()) <= generic:
            continue  # an explicit department statement also matched
        confidence = "medium" if explicit_present else "low"
        out.append(_proposal(
            field="department",
            rule="dept_generic_term",
            is_correction=True,
            confidence=confidence,
            current=dept,
            proposed="verify department: drop '%s' (route to General or the "
                     "explicitly named department) unless the post names this "
                     "department" % dept,
            rationale="%s matched only via generic technical term(s) '%s'; "
                      "generic terminology is a topic, not department evidence.%s"
                      % (dept, ", ".join(_spans(ev)),
                         " Another department is named explicitly in the post."
                         if explicit_present else ""),
            evidence_spans=_spans(ev),
        ))
    return out


# ---------------------------------------------------------------------------
# Heuristic 3 - stakeholder inferred from an isolated word (group D)
# ---------------------------------------------------------------------------
def propose_stakeholder_isolated(rec):
    if rec.get("candidate_status") != STATUS_ACTIVITY_CANDIDATE:
        return []
    out = []
    for stak in rec.get("stakeholder_candidates") or []:
        isolated = ISOLATED_STAKEHOLDER_PATTERNS.get(stak)
        if not isolated:
            continue
        ev = (rec.get("stakeholder_evidence") or {}).get(stak)
        if not ev:
            continue
        if not set(ev.keys()) <= isolated:
            continue
        out.append(_proposal(
            field="stakeholder",
            rule="stakeholder_isolated",
            is_correction=True,
            confidence="low",
            current=STAKEHOLDER_PUBLIC_NAMES.get(stak, stak),
            proposed="verify stakeholder: drop '%s' unless the post shows this "
                     "group as the intended audience/participants"
                     % STAKEHOLDER_PUBLIC_NAMES.get(stak, stak),
            rationale="%s matched only via isolated word(s) '%s'; the audience "
                      "of an activity is not implied by an isolated mention "
                      "(e.g. a profile/bio line or an unrelated sentence)."
                      % (stak, ", ".join(_spans(ev))),
            evidence_spans=_spans(ev),
        ))
    return out


# ---------------------------------------------------------------------------
# Heuristic 4 - embedded event inside a communication post (group F)
# ---------------------------------------------------------------------------
def _strict_event_weight(code, ev):
    weights = dict(CATEGORY_PATTERNS[code])
    return sum(weights.get(pat, 0) for pat in (ev or {}))


def _facility_context(low, ev):
    """True when the matched event term sits next to facility words."""
    for pat in (ev or {}):
        for m in _match_all(low, pat):
            window = low[max(0, m.start() - 30):min(len(low), m.end() + 30)]
            if FACILITY_CONTEXT_RE.search(window):
                return True
    return False


def propose_embedded_event(rec):
    """NON_ACTIVITY posts that hide a real event (strong term + explicit date).

    Communication separation is assumed correct by the classifier; this rule
    keeps genuine activities that were embedded in promo/general text visible
    instead of silently swallowed by the communication decision.
    """
    if rec.get("candidate_status") != STATUS_NON_ACTIVITY:
        return []
    if rec.get("date_status") != "dated":
        return []  # an embedded event almost always carries an explicit date
    low = rec_low_text(rec)
    out = []
    for code in sorted(rec.get("category_evidence") or {}):
        if code not in STRICT_EVENT_CATEGORIES:
            continue
        ev = rec["category_evidence"][code]
        if _strict_event_weight(code, ev) < STRONG_EVENT_MIN_WEIGHT:
            continue
        if _facility_context(low, ev):
            continue  # "seminar hall" etc. = infrastructure, not an event
        out.append(_proposal(
            field="status",
            rule="embedded_event_possible",
            is_correction=True,
            confidence="low",
            current="NON_ACTIVITY",
            proposed="verify: promote to ACTIVITY_CANDIDATE and review categories",
            rationale="communication post (%s) contains the strict event "
                      "category %s with weight %d plus an explicit date; the "
                      "event may be embedded in the promotion/announcement."
                      % (rec.get("communication_type") or "n/a", code,
                         _strict_event_weight(code, ev)),
            evidence_spans=_spans(ev),
        ))
    return out


# ---------------------------------------------------------------------------
# Heuristic 5 - multi-label categories describing the same event (group B)
# ---------------------------------------------------------------------------
def _evidence_regions(low, ev):
    regions = []
    for pat in (ev or {}):
        for m in _match_all(low, pat):
            regions.append((m.start(), m.end()))
    return regions


def _regions_close(first, second, gap=30):
    for s1, e1 in first:
        for s2, e2 in second:
            if max(s1, s2) - min(e1, e2) <= gap:
                return True
    return False


def propose_multi_label_overlap(rec):
    if rec.get("candidate_status") != STATUS_ACTIVITY_CANDIDATE:
        return []
    cats = [c for c in (rec.get("category_candidates") or [])
            if c in SEMANTIC_OVERLAP_GROUPS]
    if len(cats) < 2:
        return []
    low = rec_low_text(rec)
    ev_by_cat = rec.get("category_evidence") or {}
    regions = {c: _evidence_regions(low, ev_by_cat.get(c)) for c in cats}
    out = []
    for i in range(len(cats)):
        for j in range(i + 1, len(cats)):
            a, b = cats[i], cats[j]
            if not _regions_close(regions[a], regions[b], gap=30):
                continue
            out.append(_proposal(
                field="category",
                rule="multi_label_overlap",
                is_correction=True,
                confidence="low",
                current="%s + %s" % (a, b),
                proposed="verify multi-label: if both describe the SAME event, "
                         "keep only the dominant category (%s)"
                         % max((a, b), key=lambda c: -_strict_weight(c, ev_by_cat.get(c))),
                rationale="%s and %s matched within the same region of the "
                          "text (gap <= 30 chars); same-event synonyms should "
                          "not be kept as separate activity types." % (a, b),
                evidence_spans=_spans(ev_by_cat.get(a))[:3]
                              + _spans(ev_by_cat.get(b))[:3],
            ))
    return out


def _strict_weight(code, ev):
    if code not in CATEGORY_PATTERNS:
        return 0
    weights = dict(CATEGORY_PATTERNS[code])
    return sum(weights.get(pat, 0) for pat in (ev or {}))


# ---------------------------------------------------------------------------
# Heuristic 6 - date / academic-year consistency (group H)
# ---------------------------------------------------------------------------
def propose_date_ay(rec):
    out = []
    earliest = (rec.get("date_evidence") or {}).get("earliest")
    stored = rec.get("academic_year")
    status = rec.get("date_status")

    recomputed = None
    if earliest:
        try:
            y, m = int(earliest[:4]), int(earliest[5:7])
            recomputed = _academic_year(y, m)
        except (ValueError, IndexError):
            recomputed = None
    if recomputed and stored != recomputed:
        out.append(_proposal(
            field="academic_year",
            rule="ay_mismatch",
            is_correction=True,
            confidence="medium",
            current="%s" % (stored or "NULL"),
            proposed="set academic_year=%s (June 1 - May 31 from earliest "
                     "explicit date %s)" % (recomputed, earliest),
            rationale="stored academic_year does not match the AY recomputed "
                      "from the earliest explicit date.",
            evidence_spans=[earliest],
        ))
    if status == "undated" and stored:
        out.append(_proposal(
            field="academic_year",
            rule="ay_mismatch",
            is_correction=True,
            confidence="medium",
            current=stored,
            proposed="clear academic_year (post is undated)",
            rationale="an academic year is stored although the post has no "
                      "explicit date; undated posts stay undated.",
            evidence_spans=[],
        ))
    if status == "undated" and not stored:
        pass  # correct: undated and no AY invented
    if FLAG_MULTI_YEAR in (rec.get("flags") or []):
        out.append(_proposal(
            field="date",
            rule="multi_year_keep",
            is_correction=False,
            confidence="high",
            current="ambiguous_multi_year (%s)" % ", ".join(
                (rec.get("date_evidence") or {}).get("dates") or []),
            proposed="keep ambiguous_multi_year; do NOT collapse to one AY",
            rationale="the post carries explicit dates in more than one "
                      "academic year; the ambiguity must stay flagged.",
            evidence_spans=(rec.get("date_evidence") or {}).get("dates") or [],
        ))
    if FLAG_PRE_2024 in (rec.get("flags") or []):
        out.append(_proposal(
            field="date",
            rule="pre_2024_keep",
            is_correction=False,
            confidence="high",
            current="pre-2024 evidence (%s)" % (earliest or "n/a"),
            proposed="keep flagged; confirm the post belongs to the dataset "
                     "before any publication",
            rationale="earliest explicit date is before 2024 and the sheet "
                      "period may not cover it; never silently re-date.",
            evidence_spans=[earliest] if earliest else [],
        ))
    return out


# ---------------------------------------------------------------------------
# Heuristic 7 - communication separation verification (notes, any status)
# ---------------------------------------------------------------------------
def propose_comm_separation(rec):
    """Notes for NON_ACTIVITY posts: separation is recorded, categories are
    program-feature mention context only, and the reviewer must still check
    that no genuine event is hidden (see propose_embedded_event)."""
    if rec.get("candidate_status") != STATUS_NON_ACTIVITY:
        return []
    ctype = rec.get("communication_type")
    out = [_proposal(
        field="status",
        rule="comm_separation_confirmed",
        is_correction=False,
        confidence="high",
        current="NON_ACTIVITY (%s)" % (ctype or "n/a"),
        proposed="keep NON_ACTIVITY after reading the text",
        rationale="communication posts (admission promo, job ad, greeting, "
                  "congratulation, announcement, thanks) are separated from "
                  "activities; verify the text is genuinely a communication.",
        evidence_spans=_spans(rec.get("communication_evidence") or {}),
    )]
    if rec.get("category_candidates"):
        out.append(_proposal(
            field="category",
            rule="comm_mention_context",
            is_correction=False,
            confidence="high",
            current=", ".join(rec["category_candidates"]),
            proposed="context only: do NOT count as the post's activity type",
            rationale="category keywords are program-feature mentions inside a "
                      "communication post (reason: %s); they are kept as "
                      "evidence, not as a classification."
                      % (rec.get("reason") or "n/a"),
            evidence_spans=sum(
                (_spans(rec["category_evidence"].get(c))
                 for c in rec["category_candidates"]
                 if (rec.get("category_evidence") or {}).get(c)), []),
        ))
    return out


# ---------------------------------------------------------------------------
# Group assignment (single primary group per post, fixed precedence)
# ---------------------------------------------------------------------------
def primary_group(rec, proposals):
    """Return the review group letter for one record.

    Precedence: G (undecided) > F (non-activity should be activity) >
    E (non-activity correct) > B (category) > C (department) >
    D (stakeholder) > H (date/AY) > A (activity correct).
    """
    if rec.get("candidate_status") == STATUS_REVIEW_REQUIRED:
        return "G"
    corrections = [p for p in proposals if p["is_correction"]]
    if rec.get("candidate_status") == STATUS_NON_ACTIVITY:
        if any(p["field"] == "status" for p in corrections):
            return "F"
        return "E"
    fields = {p["field"] for p in corrections}
    if "category" in fields:
        return "B"
    if "department" in fields:
        return "C"
    if "stakeholder" in fields:
        return "D"
    if any(p["rule"] in DATE_ISSUE_RULES for p in proposals):
        return "H"
    return "A"


def validate_record(rec):
    """Attach review_group + proposals to a record.  Returns (group, proposals)."""
    proposals = []
    for fn in (propose_category_over_tag,
               propose_department_generic,
               propose_stakeholder_isolated,
               propose_embedded_event,
               propose_multi_label_overlap,
               propose_date_ay,
               propose_comm_separation):
        proposals.extend(fn(rec))
    group = primary_group(rec, proposals)
    rec["review_group"] = group
    rec["proposals"] = proposals
    return group, proposals


def validate_all(records):
    for rec in records:
        validate_record(rec)
    return records


# ---------------------------------------------------------------------------
# Loading the PENDING_REVIEW sample (read-only)
# ---------------------------------------------------------------------------
LIST_JSON_KEYS = ("category_candidates", "department_candidates",
                  "stakeholder_candidates", "flags")
DICT_JSON_KEYS = ("date_evidence", "category_evidence", "department_evidence",
                  "stakeholder_evidence", "communication_evidence")


def record_from_row(row):
    rec = dict(row)
    for key in LIST_JSON_KEYS:
        rec[key] = json.loads(rec[key]) if rec.get(key) else []
    for key in DICT_JSON_KEYS:
        rec[key] = json.loads(rec[key]) if rec.get(key) else {}
    return rec


def load_review_sample(conn, expected=REVIEW_SAMPLE_MAX):
    """Read the PENDING_REVIEW sample (read-only; never updates candidates)."""
    rows = conn.execute(
        "SELECT * FROM linkedin_activity_candidates "
        "WHERE review_status=? ORDER BY linkedin_post_id",
        (REVIEW_PENDING,),
    ).fetchall()
    records = [record_from_row(r) for r in rows]
    if expected is not None and len(records) != expected:
        raise RuntimeError(
            "PENDING_REVIEW sample has %d rows; expected %d. "
            "Run backend.database.linkedin_candidates.run_pilot first."
            % (len(records), expected))
    return records


def snippet(rec, limit=200):
    text = re.sub(r"\s+", " ", rec.get("post_text") or "").strip()
    return text[:limit]


def _activity_word(rec):
    return {1: "activity", 0: "non-activity", None: "undecided"}.get(
        rec.get("is_activity"), "undecided")


# ---------------------------------------------------------------------------
# Summary + review-layer persistence
# ---------------------------------------------------------------------------
def build_summary(records):
    groups = {g: 0 for g in REVIEW_GROUP_ORDER}
    rules = {}
    by_field = {}
    attention = {c: 0 for c in OVER_TAG_CATEGORIES}
    statuses = {}
    corrections = 0
    notes = 0
    for rec in records:
        groups[rec["review_group"]] = groups.get(rec["review_group"], 0) + 1
        statuses[rec["candidate_status"]] = statuses.get(rec["candidate_status"], 0) + 1
        for p in rec["proposals"]:
            rules[p["rule"]] = rules.get(p["rule"], 0) + 1
            if p["is_correction"]:
                corrections += 1
                by_field[p["field"]] = by_field.get(p["field"], 0) + 1
                if p["rule"].startswith("cat_over_tag:"):
                    code = p["rule"].split(":", 1)[1]
                    attention[code] = attention.get(code, 0) + 1
            else:
                notes += 1
    return {
        "review_sample_size": len(records),
        "review_status": "PENDING_REVIEW in linkedin_activity_candidates "
                         "(unchanged by this review stage)",
        "group_counts": groups,
        "sample_status_counts": statuses,
        "activity_needing_correction": groups["B"] + groups["C"] + groups["D"],
        "non_activity_needing_correction": groups["F"],
        "correction_counts_by_field": dict(sorted(by_field.items())),
        "proposal_counts_by_rule": dict(
            sorted(rules.items(), key=lambda kv: (-kv[1], kv[0]))),
        "total_proposed_corrections": corrections,
        "total_review_notes": notes,
        "attention_category_over_tag_counts": attention,
        "groups": {
            g: {"label": REVIEW_GROUP_LABELS[g],
                "description": REVIEW_GROUP_DESCRIPTIONS[g],
                "count": groups[g]}
            for g in REVIEW_GROUP_ORDER
        },
    }


def persist_proposals(conn, records):
    """Write proposals to the REVIEW LAYER ONLY (staging DB, own table).

    Idempotent: the table is emptied first so re-running the review replaces
    the previous proposal set.  The candidates table is never touched.
    """
    init_review_schema(conn)
    conn.execute("DELETE FROM linkedin_manual_review_proposals")
    total = 0
    for rec in records:
        for p in rec["proposals"]:
            conn.execute(
                """INSERT INTO linkedin_manual_review_proposals
                   (linkedin_post_id, field, rule, is_correction, confidence,
                    current, proposed, rationale, evidence_spans)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rec["linkedin_post_id"], p["field"], p["rule"],
                 1 if p["is_correction"] else 0, p["confidence"],
                 p["current"], p["proposed"], p["rationale"],
                 json.dumps(p["evidence_spans"])),
            )
            total += 1
    conn.commit()
    return total


def run_review(conn, records):
    """Validate the sample and persist proposals (review layer only)."""
    validate_all(records)
    persisted = persist_proposals(conn, records)
    summary = build_summary(records)
    summary["proposals_persisted"] = persisted
    summary["proposals_table"] = "linkedin_manual_review_proposals (staging DB)"
    return records, summary


# ---------------------------------------------------------------------------
# Report writers (JSON + Markdown + Excel-friendly CSV)
# ---------------------------------------------------------------------------
def _meta():
    return {
        "title": "LinkedIn Candidate Manual Review Report",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sample": "200 posts marked PENDING_REVIEW in "
                  "backend/database/linkedin_staging.db -> "
                  "linkedin_activity_candidates",
        "scope": "staging/review layer only",
        "groups": "A-H review-priority buckets (see guidelines)",
        "disclaimer": (
            "This is a review aid for a human evaluator. Proposed corrections "
            "and review decisions are recorded in the review layer only "
            "(linkedin_manual_review_proposals + this report); nothing is "
            "applied to linkedin_activity_candidates, the production database "
            "or merged-workbook.xlsx. Internal evidence spans are never public "
            "UI fields. No accuracy claim is made."
        ),
    }


def _record_json(rec):
    return {
        "linkedin_post_id": rec["linkedin_post_id"],
        "post_url": rec.get("post_url"),
        "post_text": rec.get("post_text") or "",
        "snippet": snippet(rec),
        "source_sheet": rec.get("source_sheet"),
        "source_row": rec.get("source_row"),
        "candidate_status": rec.get("candidate_status"),
        "is_activity": rec.get("is_activity"),
        "kind": rec.get("kind"),
        "activity_or_not": _activity_word(rec),
        "category_candidates": rec.get("category_candidates") or [],
        "department_candidates": rec.get("department_candidates") or [],
        "stakeholder_candidates": rec.get("stakeholder_candidates") or [],
        "date_status": rec.get("date_status"),
        "date_evidence": rec.get("date_evidence") or {},
        "academic_year": rec.get("academic_year"),
        "communication_type": rec.get("communication_type"),
        "communication_evidence": rec.get("communication_evidence") or {},
        "evidence_score": rec.get("evidence_score"),
        "multi_label": rec.get("multi_label"),
        "flags": rec.get("flags") or [],
        "reason": rec.get("reason"),
        "review_group": rec["review_group"],
        "proposals": rec["proposals"],
    }


def build_review_report(records, summary):
    groups = {}
    for g in REVIEW_GROUP_ORDER:
        ids = [r["linkedin_post_id"] for r in records if r["review_group"] == g]
        groups[g] = {
            "label": REVIEW_GROUP_LABELS[g],
            "description": REVIEW_GROUP_DESCRIPTIONS[g],
            "count": len(ids),
            "post_ids": ids,
        }
    return {
        "meta": _meta(),
        "summary": summary,
        "guidelines": GUIDELINES,
        "groups": groups,
        "records": [_record_json(r) for r in records],
    }


def _md_post(rec):
    L = ["### Post #%d" % rec["linkedin_post_id"], ""]
    L.append("- Source: `%s` row `%s` | URL: %s"
             % (rec.get("source_sheet"), rec.get("source_row"),
                rec.get("post_url") or "none (link-less)"))
    L.append("- Decision: **%s** / %s (kind `%s`, reason: %s)"
             % (rec.get("candidate_status"), _activity_word(rec),
                rec.get("kind"), rec.get("reason") or "n/a"))
    if rec.get("communication_type"):
        L.append("- Communication type: `%s`" % rec["communication_type"])
    L.append("- Categories: %s"
             % (", ".join(rec.get("category_candidates") or []) or "-"))
    L.append("- Departments: %s"
             % (", ".join(rec.get("department_candidates") or []) or "-"))
    L.append("- Stakeholders: %s"
             % (", ".join(rec.get("stakeholder_candidates") or []) or "-"))
    de = rec.get("date_evidence") or {}
    L.append("- Date: status `%s` | dates: %s | AY: `%s`"
             % (rec.get("date_status"),
                ", ".join(de.get("dates") or []) or "none",
                rec.get("academic_year") or "undated"))
    L.append("- Flags: %s | evidence_score: %s | multi_label: %s"
             % (", ".join(rec.get("flags") or []) or "-",
                rec.get("evidence_score"), rec.get("multi_label")))
    if rec["proposals"]:
        L.append("- Proposals:")
        for p in rec["proposals"]:
            L.append("  - `%s` %s · rule=`%s` · confidence=%s · "
                     "current: %s → proposed: %s"
                     % ("CORRECTION" if p["is_correction"] else "note",
                        p["field"], p["rule"], p["confidence"],
                        (p["current"] or "-").replace("|", "/"),
                        (p["proposed"] or "-").replace("|", "/")))
            if p.get("rationale"):
                L.append("    - rationale: %s"
                         % p["rationale"].replace("|", "/"))
    else:
        L.append("- Proposals: none")
    L.append("- Text: %s" % snippet(rec, 400))
    L.append("")
    return L


def write_reports(records, summary, out_dir=None):
    out_dir = out_dir or DEFAULT_OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    report = build_review_report(records, summary)

    json_path = os.path.join(out_dir, REPORT_BASENAME + ".json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    md_path = os.path.join(out_dir, REPORT_BASENAME + ".md")
    L = ["# LinkedIn Candidate Manual Review Report (2026-09-23)", ""]
    L.append("- Generated: %s" % report["meta"]["generated_at"])
    L.append("- Sample: %d posts, PENDING_REVIEW (staging/review layer only)"
             % summary["review_sample_size"])
    L.append("- Disclaimer: %s" % report["meta"]["disclaimer"])
    L.append("")
    L.append("## 1. How to use this report")
    L.append("")
    for line in GUIDELINES:
        L.append("- %s" % line)
    L.append("")
    L.append("## 2. Summary counts")
    L.append("")
    L.append("### 2.1 Review groups A-H (partition of the %d sampled posts)"
             % summary["review_sample_size"])
    L.append("")
    L.append("| Group | Label | Posts |")
    L.append("|---|---|---|")
    for g in REVIEW_GROUP_ORDER:
        L.append("| %s | %s | %d |"
                 % (g, REVIEW_GROUP_LABELS[g], summary["group_counts"][g]))
    L.append("")
    L.append("### 2.2 Proposed corrections by field")
    L.append("")
    if summary["correction_counts_by_field"]:
        L.append("| Field | Corrections |")
        L.append("|---|---|")
        for k, v in summary["correction_counts_by_field"].items():
            L.append("| %s | %d |" % (k, v))
    else:
        L.append("No corrections proposed.")
    L.append("")
    L.append("Total proposed corrections: %d | review notes: %d | "
             "proposals persisted: %d"
             % (summary["total_proposed_corrections"],
                summary["total_review_notes"],
                summary.get("proposals_persisted", 0)))
    L.append("")
    L.append("### 2.3 Proposed corrections by rule")
    L.append("")
    L.append("| Rule | Count |")
    L.append("|---|---|")
    for k, v in summary["proposal_counts_by_rule"].items():
        L.append("| %s | %d |" % (k, v))
    L.append("")
    L.append("### 2.4 Over-tag attention (7 categories, group B subset)")
    L.append("")
    L.append("| Category | Posts flagged |")
    L.append("|---|---|")
    for code in OVER_TAG_CATEGORIES:
        L.append("| %s | %d |"
                 % (CATEGORY_CANDIDATE_NAMES.get(code, code),
                    summary["attention_category_over_tag_counts"][code]))
    L.append("")
    L.append("### 2.5 Sample composition by candidate status")
    L.append("")
    L.append("| Status | Posts |")
    L.append("|---|---|")
    for k, v in summary["sample_status_counts"].items():
        L.append("| %s | %d |" % (k, v))
    L.append("")

    for g in REVIEW_GROUP_ORDER:
        recs = [r for r in records if r["review_group"] == g]
        L.append("## Group %s - %s (%d posts)"
                 % (g, REVIEW_GROUP_LABELS[g], len(recs)))
        L.append("")
        L.append("> %s" % REVIEW_GROUP_DESCRIPTIONS[g])
        L.append("")
        if not recs:
            L.append("_No posts in this group._")
            L.append("")
            continue
        for rec in recs:
            L.extend(_md_post(rec))

    L.append("## Integrity notes")
    L.append("")
    L.append("- The %d sampled posts are READ from linkedin_activity_candidates; "
             "their candidate_status, categories and review_status are unchanged."
             % summary["review_sample_size"])
    L.append("- Proposed corrections/review decisions live ONLY in "
             "`linkedin_manual_review_proposals` (staging DB) and this report.")
    L.append("- Canonical posts remain 1,544; raw occurrences remain 2,094; the "
             "production database (2,258 website activities) and "
             "merged-workbook.xlsx were not touched.")
    L.append("- No accuracy claim: the human labels from this report are needed "
             "before any evaluation statement.")
    L.append("")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))

    csv_path = os.path.join(out_dir, REPORT_BASENAME + ".csv")
    columns = [
        "linkedin_post_id", "source_sheet", "source_row", "has_url", "post_url",
        "candidate_status", "activity_or_not", "kind",
        "category_candidates", "department_candidates", "stakeholder_candidates",
        "date_status", "academic_year", "date_earliest", "date_dates",
        "communication_type", "flags", "evidence_score", "multi_label",
        "review_reason", "review_group", "correction_count", "proposal_count",
        "proposals", "snippet",
    ]
    # utf-8-sig (BOM) so Excel on Windows opens the CSV with correct accents.
    with open(csv_path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for rec in records:
            de = rec.get("date_evidence") or {}
            writer.writerow({
                "linkedin_post_id": rec["linkedin_post_id"],
                "source_sheet": rec.get("source_sheet"),
                "source_row": rec.get("source_row"),
                "has_url": "yes" if rec.get("post_url") else "no",
                "post_url": rec.get("post_url") or "",
                "candidate_status": rec.get("candidate_status"),
                "activity_or_not": _activity_word(rec),
                "kind": rec.get("kind"),
                "category_candidates": "; ".join(rec.get("category_candidates") or []),
                "department_candidates": "; ".join(rec.get("department_candidates") or []),
                "stakeholder_candidates": "; ".join(rec.get("stakeholder_candidates") or []),
                "date_status": rec.get("date_status"),
                "academic_year": rec.get("academic_year") or "undated",
                "date_earliest": de.get("earliest") or "",
                "date_dates": "; ".join(de.get("dates") or []),
                "communication_type": rec.get("communication_type") or "",
                "flags": "; ".join(rec.get("flags") or []),
                "evidence_score": rec.get("evidence_score"),
                "multi_label": rec.get("multi_label"),
                "review_reason": rec.get("reason") or "",
                "review_group": rec["review_group"],
                "correction_count": sum(1 for p in rec["proposals"] if p["is_correction"]),
                "proposal_count": len(rec["proposals"]),
                "proposals": "; ".join(
                    "%s[%s]%s" % (p["rule"],
                                  "correction" if p["is_correction"] else "note",
                                  "" if not p["is_correction"] else " -> %s" % p["proposed"])
                    for p in rec["proposals"]),
                "snippet": snippet(rec, 200),
            })

    return {"json": json_path, "md": md_path, "csv": csv_path}


# ---------------------------------------------------------------------------
# Entry point (staging/review layer only)
# ---------------------------------------------------------------------------
def run_manual_review(db_path=STAGING_DB_PATH, out_dir=None):
    conn = get_staging_connection(db_path)
    try:
        records = load_review_sample(conn)
        records, summary = run_review(conn, records)
        paths = write_reports(records, summary, out_dir=out_dir)
        return records, summary, paths
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="LinkedIn candidate manual review (review layer only).")
    parser.add_argument("--db", default=STAGING_DB_PATH)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    recs, summary, paths = run_manual_review(db_path=args.db, out_dir=args.out)
    print("LinkedIn manual review complete (review layer only).")
    print("  sample: %d posts (PENDING_REVIEW unchanged)"
          % summary["review_sample_size"])
    print("  groups: " + " ".join(
        "%s=%d" % (g, summary["group_counts"][g]) for g in REVIEW_GROUP_ORDER))
    print("  proposed corrections: %d | review notes: %d | persisted: %d"
          % (summary["total_proposed_corrections"],
             summary["total_review_notes"],
             summary.get("proposals_persisted", 0)))
    print("  report json: %s" % paths["json"])
    print("  report md:   %s" % paths["md"])
    print("  report csv:  %s" % paths["csv"])
