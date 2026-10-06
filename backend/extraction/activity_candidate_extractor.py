"""Offline, evidence-preserving extraction from Step 2 raw source occurrences.

No canonical activity, final category, or duplicate decision is made here.
"""

import json
import os
import re
from datetime import date, datetime
from pathlib import Path

from backend.config import RAW_DATA_DIR
from backend.database.cleaner import normalize_unicode, normalize_whitespace
from backend.database.init_db import get_connection, init_db

ACTIVITY_TERMS = ("workshop", "seminar", "training", "fdp", "conference", "competition", "tournament",
                  "sports", "ncc", "nss", "camp", "marathon", "hackathon", "webinar", "activity",
                  "event", "award", "prize", "achievement", "mou", "collaboration", "outreach")
ACTION_TERMS = ("organized", "organised", "conducted", "held", "celebrated", "participated", "attended",
                "achieved", "won", "secured", "awarded", "received", "signed", "completed", "launched")
OUTCOME_RE = re.compile(r"\b(?:first|second|third|runner[- ]?up|winner|won|secured|awarded|received|best [\w ]+ award|gold medal|signed mou)\b[^.]{0,180}", re.I)
GENERIC_TITLES = {"home", "about", "contact", "department", "activities", "quick links", "major activities"}
# These source classes describe rules, administration, or payment rather than
# activity evidence. Their incidental words (e.g. "seminar" in a syllabus)
# must not create a candidate.
NON_ACTIVITY_SOURCE_TERMS = (
    "fee", "payment", "regulation", "syllabus", "research policy", "approval copy",
    "aicte approval", "academic calendar", "minutes of meeting", "exam phase",
)

DEPARTMENTS = {
    "Applied Mathematics and Computational Science": ("applied mathematics and computational science", "amcs"),
    "Architecture": ("architecture", "b.arch"), "Civil Engineering": ("civil engineering", "civil dept"),
    "Computer Science and Engineering": ("computer science and engineering", "cse"),
    "Computer Applications": ("computer applications", "mca"),
    "Electronics and Communication Engineering": ("electronics and communication engineering", "ece"),
    "Electrical and Electronics Engineering": ("electrical and electronics engineering", "eee"),
    "Information Technology": ("information technology", "it department"),
    "Mechanical Engineering": ("mechanical engineering", "mech"), "Mechatronics": ("mechatronics", "mct"),
    "Physics": ("department of physics",), "Chemistry": ("department of chemistry",),
    # Mathematics is a SEPARATE department from Applied Mathematics and
    # Computational Science: the aliases below are deliberately full phrases so a
    # "department of applied mathematics and computational science" mention can
    # only ever resolve to AMCS, never to Mathematics.
    "Mathematics": ("department of mathematics", "maths department", "math department"),
    "Fashion Technology": ("department of fashion technology", "fashion technology department"),
    "English": ("department of english",),
}
STAKEHOLDER_TERMS = {
    "STUDENTS": ("students", "student", "cadets", "volunteers"), "FACULTY": ("faculty", "professor", "teachers"),
    "STAFF": ("staff", "non-teaching"), "ALUMNI": ("alumni", "alumnus"),
    "INDUSTRY": ("industry", "company", "corporate", "decathlon"), "EXTERNAL": ("school students", "government school", "public"),
}
CATEGORY_HINTS = (("NSS", ("nss", "national service scheme")), ("NCC", ("ncc", "national cadet corps")),
                  ("SPORTS", ("sports", "tournament", "marathon", "cricket", "badminton", "hockey", "chess")),
                  ("FDP", ("fdp", "faculty development")), ("WORKSHOP", ("workshop",)),
                  ("SEMINAR", ("seminar",)), ("TRAINING", ("training", "coaching camp")),
                  ("COMPETITION", ("competition", "contest")), ("ACHIEVEMENT", ("award", "prize", "winner", "secured")),
                  ("MOU_COLLABORATION", ("mou", "memorandum of understanding", "collaboration")),
                  ("OUTREACH_EXTENSION", ("outreach", "blood donation", "community")),
                  ("EVENT", ("event", "organized", "organised", "conducted", "held")))


def normalize_content(text):
    """Normalize a copy of archived text; retain the archive untouched."""
    text = normalize_unicode(text or "").replace("\u00a0", " ")
    text = re.sub(r"[\u2013\u2014]", "-", text)
    text = re.sub(r"(?<=\w)-\s+(?=\w)", "", text)  # PDF hyphenated line breaks
    text = re.sub(r"\s+", " ", text)
    # TCE text archive has a stable navigation prefix and quick-links footer.
    if "Breadcrumb" in text:
        text = text.split("Breadcrumb", 1)[1]
    if "Quick Links" in text:
        text = text.split("Quick Links", 1)[0]
    return normalize_whitespace(text)


def academic_year(value, boundary_month=8, first_start_year=2021, last_start_year=2025):
    """Return an in-scope `YYYY-YY` for a real date using configurable Aug-Jul."""
    if not value:
        return None
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d").date()
    start = value.year if value.month >= boundary_month else value.year - 1
    if not first_start_year <= start <= last_start_year:
        return None
    return f"{start}-{str(start + 1)[-2:]}"


MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
ACADEMIC_YEAR_RE = re.compile(
    r"\b(?:academic\s+year|annual\s+report(?:\s+for)?|activities?\s+(?:for|during)\s+(?:the\s+)?academic\s+year)\s*[:\-]?\s*"
    r"(20(?:2[1-5]))\s*(?:[-–/]\s*)(\d{2}|20\d{2})\b", re.I)
DATE_PATTERNS = [
    re.compile(rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})\s*,?\s*(\d{{4}})\b", re.I),
    re.compile(rf"\b({MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?\s*,?\s*(\d{{4}})\b", re.I),
    re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b"),
    re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b"),
]


def extract_date(text):
    """Return ISO date and exact matched text, or `(None, None)` without guessing."""
    for index, pattern in enumerate(DATE_PATTERNS):
        match = pattern.search(text or "")
        if not match:
            continue
        raw, parts = match.group(0), match.groups()
        try:
            if index == 0:
                parsed = None
                for fmt in ("%d %B %Y", "%d %b %Y"):
                    try:
                        parsed = datetime.strptime(f"{parts[0]} {parts[1]} {parts[2]}", fmt).date(); break
                    except ValueError:
                        pass
                if parsed is None: continue
            elif index == 1:
                parsed = None
                for fmt in ("%d %B %Y", "%d %b %Y"):
                    try:
                        parsed = datetime.strptime(f"{parts[1]} {parts[0]} {parts[2]}", fmt).date(); break
                    except ValueError:
                        pass
                if parsed is None: continue
            elif index == 2:
                year = int(parts[2]); year += 2000 if year < 100 else 0
                parsed = date(year, int(parts[1]), int(parts[0]))
            else:
                parsed = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            continue
        return parsed.isoformat(), raw
    # A standalone year is useful provenance, but is not enough to invent a
    # calendar date or academic year (the Aug 1 boundary cannot be applied).
    year = re.search(r"\b(20\d{2})\b", text or "")
    return None, year.group(0) if year else None


def extract_academic_year_context(text):
    """Return an explicitly-labelled in-scope academic period, if unambiguous.

    Plain calendar years, URL years, and document metadata are intentionally not
    context: they cannot safely resolve an undated activity around Aug 1.
    """
    found = set()
    for match in ACADEMIC_YEAR_RE.finditer(text or ""):
        start, end = int(match.group(1)), match.group(2)
        end_year = int(end) if len(end) == 4 else 2000 + int(end)
        if end_year == start + 1 and 2021 <= start <= 2025:
            found.add(f"{start}-{str(end_year)[-2:]}")
    return next(iter(found)) if len(found) == 1 else None


def _has(text, terms):
    lower = text.lower()
    return [term for term in terms if re.search(r"\b" + re.escape(term) + r"\b", lower)]


def evidence_assessment(title, text):
    # Page titles are provenance, not activity evidence: e.g. an otherwise
    # empty page titled "NCC" must not become an activity candidate.
    body = (text or "").lower()
    categories, actions = _has(body, ACTIVITY_TERMS), _has(body, ACTION_TERMS)
    score = min(1.0, 0.18 * len(set(categories)) + 0.16 * len(set(actions)))
    return score >= 0.5, score, f"activity terms: {', '.join(categories[:4]) or 'none'}; actions: {', '.join(actions[:3]) or 'none'}"


def source_is_non_activity(url, title):
    # Archived filenames frequently use separators (`Research-Policy.pdf`).
    # Treat those separators as spaces before applying the existing source
    # class exclusions.
    source_identity = re.sub(r"[^a-z0-9]+", " ", f"{url or ''} {title or ''}".lower())
    return any(term in source_identity for term in NON_ACTIVITY_SOURCE_TERMS)


def split_activity_blocks(text):
    """Split prose/list archives into candidate evidence blocks without page=activity assumptions."""
    # Do not split a leading year written as `2024. Description`; later dates
    # such as `15 March 2024. Next activity...` remain sentence boundaries.
    protected = re.sub(r"^(\s*20\d{2})\.", r"\1<YEAR_DOT>", text)
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", protected)
    blocks = []
    for sentence in sentences:
        sentence = normalize_whitespace(sentence).replace("<YEAR_DOT>", ".")
        low = sentence.lower()
        if len(sentence) >= 24 and (_has(low, ACTION_TERMS) or _has(low, ACTIVITY_TERMS)):
            blocks.append(sentence)
    # Numbered list entries can be activity names without a sentence-ending
    # period. Limit markers to 1-99: a four-digit year such as `2024. Alumni`
    # is a date/year, never a list marker.
    list_marker = re.compile(r"(?<!\d)\b(?:[1-9]|[1-9]\d)[.)]\s+")
    if list_marker.search(text):
        for entry in list_marker.split(text):
            entry = normalize_whitespace(entry)
            if 12 <= len(entry) <= 400 and _has(entry, ACTIVITY_TERMS):
                blocks.append(entry)
    seen, unique = set(), []
    for block in blocks:
        key = re.sub(r"\W+", "", block.lower())
        if key not in seen:
            seen.add(key); unique.append(block)
    return unique


def title_from_block(block):
    title = re.split(r"\b(?:was|were|is|are|has|have|organized|organised|conducted|held|celebrated|participated|won|secured|awarded)\b", block, 1, flags=re.I)[0]
    title = re.sub(r"^(?:the|a|an|as part of)\s+", "", title.strip(), flags=re.I)
    title = re.sub(r"\s+(?:on|at|from)\s+\d.*$", "", title, flags=re.I).strip(" -:;,")
    if not title or title.lower() in GENERIC_TITLES or len(title) > 220:
        title = block[:220].rsplit(" ", 1)[0]
    return title


def extract_departments(text):
    found = []
    lower = text.lower()
    for name, aliases in DEPARTMENTS.items():
        if any(re.search(r"\b" + re.escape(alias) + r"\b", lower) for alias in aliases):
            found.append(name)
    if found:
        return found, "; ".join(found)
    if re.search(r"\b(?:thiagarajar college of engineering|tce|our college|college campus)\b", lower):
        return ["GENERAL"], "General (institution-wide TCE reference)"
    return ["GENERAL"], "General"


def extract_stakeholders(text):
    lower = text.lower(); found = []
    for code, terms in STAKEHOLDER_TERMS.items():
        if any(re.search(r"\b" + re.escape(term) + r"\b", lower) for term in terms):
            found.append(code)
    if not found and re.search(r"\b(?:tce|thiagarajar college)\b", lower):
        found.append("INSTITUTION")
    return found or ["UNKNOWN"], "; ".join(found) if found else None


def category_hint(text):
    lower = text.lower()
    for label, terms in CATEGORY_HINTS:
        if any(term in lower for term in terms):
            return label
    return "OTHER"


def extract_keywords(text):
    lower = text.lower()
    return [term.upper() if term in {"ncc", "nss", "fdp", "mou", "ai"} else term.title()
            for term in ACTIVITY_TERMS if re.search(r"\b" + re.escape(term) + r"\b", lower)][:8]


class ActivityCandidateExtractor:
    def __init__(self, conn=None, archive_root=RAW_DATA_DIR, academic_boundary_month=8):
        self.conn = conn
        self.archive_root = Path(archive_root)
        self.academic_boundary_month = academic_boundary_month

    def _read_source(self, row):
        path = row["text_archive_path"]
        if not path:
            raise FileNotFoundError("source has no extracted text archive")
        return (self.archive_root / path).read_text(encoding="utf-8", errors="replace")

    def run(self, collection_run_id=5, max_sources=None, minimum_evidence_score=0.5, dry_run=False):
        init_db()
        own = self.conn is None
        conn = self.conn or get_connection()
        metrics = {"sources_considered": 0, "sources_processed": 0, "sources_skipped": 0,
                   "sources_with_activity_evidence": 0, "sources_without_activity_evidence": 0,
                   "html_sources_processed": 0, "pdf_sources_processed": 0, "activity_candidates": 0,
                   "html_candidates": 0, "pdf_candidates": 0, "sources_zero_candidates": 0, "failures": 0}
        try:
            cur = conn.execute("INSERT INTO extraction_runs (collection_run_id, minimum_evidence_score, dry_run) VALUES (?, ?, ?)",
                               (collection_run_id, minimum_evidence_score, int(dry_run)))
            extraction_run_id = cur.lastrowid; conn.commit()
            sql = "SELECT * FROM raw_source_occurrences WHERE collection_run_id=? ORDER BY id"
            rows = conn.execute(sql, (collection_run_id,)).fetchall()
            if max_sources is not None:
                rows = rows[:max_sources]
            for row in rows:
                metrics["sources_considered"] += 1
                try:
                    normalized = normalize_content(self._read_source(row))
                    if source_is_non_activity(row["source_url"], row["page_title"]):
                        metrics["sources_skipped"] += 1; metrics["sources_without_activity_evidence"] += 1
                        self._telemetry(conn, extraction_run_id, row["id"], False, 0.0,
                                        "non-activity administrative/policy source", 0, "SKIPPED")
                        continue
                    contains, score, reason = evidence_assessment(row["page_title"], normalized)
                    if not contains or score < minimum_evidence_score:
                        metrics["sources_skipped"] += 1; metrics["sources_without_activity_evidence"] += 1
                        self._telemetry(conn, extraction_run_id, row["id"], False, score, reason, 0, "SKIPPED")
                        continue
                    metrics["sources_processed"] += 1; metrics["sources_with_activity_evidence"] += 1
                    metrics[f"{row['source_type']}_sources_processed"] += 1
                    source_academic_year = extract_academic_year_context(normalized)
                    candidates = [self._candidate(row, block, source_academic_year) for block in split_activity_blocks(normalized)]
                    # Step 3 retains undated evidence, but does not put a
                    # known out-of-scope date/year into the five-year workbench.
                    candidates = [c for c in candidates if self._candidate_is_in_scope(c)]
                    if not candidates:
                        metrics["sources_zero_candidates"] += 1
                    for candidate in candidates:
                        if not dry_run:
                            self._insert(conn, extraction_run_id, row["id"], candidate)
                        metrics["activity_candidates"] += 1; metrics[f"{row['source_type']}_candidates"] += 1
                    self._telemetry(conn, extraction_run_id, row["id"], True, score, reason, len(candidates), "SUCCESS")
                except Exception as exc:
                    metrics["failures"] += 1
                    self._telemetry(conn, extraction_run_id, row["id"], False, 0.0, "read/extract failure", 0, "FAILED", str(exc))
            conn.execute("UPDATE extraction_runs SET finished_at=datetime('now'), status='completed', metrics_json=? WHERE id=?",
                         (json.dumps(metrics, sort_keys=True), extraction_run_id)); conn.commit()
            return {"extraction_run_id": extraction_run_id, **metrics}
        except Exception:
            conn.rollback(); raise
        finally:
            if own: conn.close()

    def _candidate(self, row, block, source_academic_year=None):
        activity_date, date_text = extract_date(block)
        # An exact date is strongest. Explicit academic-year wording in the
        # block is next. A document-level period can be inherited only when it
        # is the sole explicitly-labelled period in that source.
        context_year = extract_academic_year_context(block) or source_academic_year
        assigned_year = academic_year(activity_date, self.academic_boundary_month) if activity_date else context_year
        departments, department_text = extract_departments(block)
        stakeholders, stakeholder_text = extract_stakeholders(block)
        outcome = OUTCOME_RE.search(block)
        confidence = min(0.95, 0.45 + (0.2 if activity_date else 0) + (0.15 if category_hint(block) != "OTHER" else 0) + (0.1 if departments else 0))
        return {"title": title_from_block(block), "description": block, "activity_date": activity_date,
                "activity_date_text": date_text, "academic_year": assigned_year,
                "category_hint": category_hint(block), "department": json.dumps(departments), "department_text": department_text,
                "stakeholder": json.dumps(stakeholders), "stakeholder_text": stakeholder_text,
                "achievement_outcome": outcome.group(0) if outcome else None, "keywords_json": json.dumps(extract_keywords(block)),
                "evidence_text": block[:1200], "extraction_method": "RULE_BASED_TEXT_BLOCK",
                "extraction_confidence": confidence}

    @staticmethod
    def _candidate_is_in_scope(candidate):
        if candidate["activity_date"]:
            return candidate["academic_year"] is not None
        year = candidate["activity_date_text"]
        return not (year and year.isdigit() and not 2021 <= int(year) <= 2025)

    @staticmethod
    def _insert(conn, run_id, source_id, c):
        conn.execute("""INSERT INTO activity_candidates
          (extraction_run_id,source_occurrence_id,title,description,activity_date,activity_date_text,academic_year,category_hint,
           department,department_text,stakeholder,stakeholder_text,achievement_outcome,keywords_json,evidence_text,
           extraction_method,extraction_confidence)
          VALUES (:run_id,:source_id,:title,:description,:activity_date,:activity_date_text,:academic_year,:category_hint,
                  :department,:department_text,:stakeholder,:stakeholder_text,:achievement_outcome,:keywords_json,:evidence_text,
                  :extraction_method,:extraction_confidence)""", {**c, "run_id": run_id, "source_id": source_id})

    @staticmethod
    def _telemetry(conn, run_id, source_id, contains, score, reason, count, status, error=None):
        conn.execute("""INSERT INTO source_extraction_telemetry
          (extraction_run_id,source_occurrence_id,contains_activity_evidence,evidence_score,reason,candidates_extracted,extraction_status,error_message)
          VALUES (?,?,?,?,?,?,?,?)""", (run_id, source_id, int(contains), score, reason, count, status, error))
        conn.commit()


if __name__ == "__main__":
    print(json.dumps(ActivityCandidateExtractor().run(), indent=2))
