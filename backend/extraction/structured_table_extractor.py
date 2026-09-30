"""Structure-aware extraction from run_7 department sub-page archives.

Reads the archived HTML for each run_7 occurrence, isolates the page content
region (between `Breadcrumb` and `Quick Links`), and emits activity candidates
from the site's own tables with header-driven column mapping.

Accuracy is the priority: only page types whose tables describe genuine
institutional activities are handled; bibliographies, student placement
lists, PhD/outcome lists, newsletter and magazine pages are deliberately
skipped (they are evidence, not activities).
"""

import json
import re
from datetime import date, datetime
from pathlib import Path

from bs4 import BeautifulSoup

from backend.config import RAW_DATA_DIR
from backend.database.cleaner import normalize_unicode, normalize_whitespace
from backend.database.normalizer import to_normalized_title
from backend.extraction.activity_candidate_extractor import DATE_PATTERNS

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
_FIRST_RANGE_YEAR = 2021
_LAST_RANGE_YEAR = 2025
_SCOPE_YEARS = set(range(_FIRST_RANGE_YEAR, _LAST_RANGE_YEAR + 1))


def clean(value):
    return normalize_whitespace(normalize_unicode(value or "")).replace("\u00a0", " ")


def parse_year_period(text):
    """Return in-scope `YYYY-YY` for an explicit `YYYY-YYYY`/`YYYY-YY` range."""
    m = re.search(r"\b(20\d{2})\s*[-–/]\s*(20\d{2})\b", text or "")
    if not m:
        m = re.search(r"\b(20\d{2})\s*[-–/]\s*(\d{2})\b", text or "")
        if not m:
            return None
        start = int(m.group(1))
        end = 2000 + int(m.group(2))
    else:
        start, end = int(m.group(1)), int(m.group(2))
    if end != start + 1 or start not in _SCOPE_YEARS:
        return None
    return f"{start}-{str(end)[-2:]}"


def parse_exact_date(text):
    """Return ISO date, raw match, or (None, None); mirrors extract_date."""
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
                if parsed is None:
                    continue
            elif index == 1:
                parsed = None
                for fmt in ("%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
                    try:
                        parsed = datetime.strptime(f"{parts[1]} {parts[0]} {parts[2]}", fmt).date(); break
                    except ValueError:
                        pass
                if parsed is None:
                    continue
            elif index == 2:
                year = int(parts[2]); year += 2000 if year < 100 else 0
                parsed = date(year, int(parts[1]), int(parts[0]))
            else:
                parsed = date(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            continue
        return parsed.isoformat(), raw
    return None, None


def academic_year(value):
    """Map an ISO date to an in-scope `YYYY-YY` (Aug-Jul boundary)."""
    if not value:
        return None
    d = date.fromisoformat(value)
    start = d.year if d.month >= 8 else d.year - 1
    if start not in _SCOPE_YEARS:
        return None
    return f"{start}-{str(start + 1)[-2:]}"


# ---------------------------------------------------------------------------
# Slug -> display name mapping (matches existing department_display values)
# ---------------------------------------------------------------------------
SLUG_TO_DISPLAY = {
    "architecture": "Architecture",
    "artificial-intelligence": "Artificial Intelligence",
    "chemistry": "Chemistry",
    "civil-engineering": "Civil Engineering",
    "computer-applications": "Computer Applications",
    "computer-science-and-business-system": "Computer Science and Business System",
    "computer-science-engineering": "Computer Science and Engineering",
    "data-science": "Data Science",
    "electrical-and-electronics-engineering": "Electrical and Electronics Engineering",
    "electronics-and-communication-engineering": "Electronics and Communication Engineering",
    "english": "English and Humanities",
    "information-technology": "Information Technology",
    "mathematics": "Applied Mathematics and Computational Science",
    "mechanical-engineering": "Mechanical Engineering",
    "mechatronics": "Mechatronics",
    "physics": "Physics",
}

# page type -> default category code(s)
DEFAULT_CATEGORY = {
    "mou": ["INDUSTRY"],
    "achievements": ["ACHIEVEMENT"],
    "awards": ["ACHIEVEMENT"],
    "patents": ["RESEARCH"],
    "sponsored-research": ["RESEARCH"],
    "consultancy-projects": ["RESEARCH"],
    "industry-interface": ["INDUSTRY", "RESEARCH"],
    "outreach-activities": ["OUTREACH"],
    "past-events": [],
    "upcoming-events": [],
    "associations": None,          # keyword-derived, CLUB fallback
    "professional-societies": None,
}


def page_type_for(url):
    if not url:
        return None
    seg = url.rstrip("/").rsplit("/", 1)[-1]
    if seg in {"achievements", "awards-recognitions", "awards-and-recognitions"}:
        return "achievements" if seg == "achievements" else "awards"
    if seg in {"consultancy-projects"}:
        return "consultancy-projects"
    if seg in {"patent", "patents"}:
        return "patents"
    if seg in {"sponsored-research", "research"}:
        return "sponsored-research"
    if seg in {"outreach-activities"}:
        return "outreach-activities"
    if seg in {"associations"}:
        return "associations"
    if seg in {"professional-societies", "professional-society"}:
        return "professional-societies"
    if seg in {"past-events"}:
        return "past-events"
    if seg in {"upcoming-events"}:
        return "upcoming-events"
    if seg in {"mou"}:
        return "mou"
    if seg in {"industry-interface"}:
        return "industry-interface"
    return None


def department_for(url):
    parts = [p for p in (url or "").split("/") if p]
    try:
        i = parts.index("departments")
    except ValueError:
        return None
    return SLUG_TO_DISPLAY.get(parts[i + 1]) if i + 1 < len(parts) else None


# ---------------------------------------------------------------------------
# Header-driven column mapping
# ---------------------------------------------------------------------------
SLOT_PATTERNS = [
    ("s_no", r"^(?:s\.?\s?no\.?|sl\.?\s?no\.?|sl\.?no\.?|no\.?|serial\s?no\.?|#|sno\.?)\s*$|\bs\.no\b|\bsl\.?\s?no\b"),
    ("title", r"title|project\s?title|theme|nature\s+of\s+work|consultancy\s+work|event?s?\s+name|name\s+of\s+the\s+activity|name\s+of\s+activity|outreach\s+activity|contest|competition|achievement|award\b|name\s+of.*programme|name\s+of\s+the\s+event|name\s+of\s+the\s+program|name\s+of\s+professional\s+society"),
    ("person", r"name\s+of\s+the\s+faculty|name\s+of\s+faculty|faculty\b|staff|inventor|applicant|recipient|name\s+of\s+the\s+student|name\s+of\s+student|name\s+of\s+staff|team\b|person|expert|resource\s+person|faculty\s*[-/]\s*in.?charge|coordinator|speaker"),
    ("org", r"industry|company|funding\s+agency|institution|agency|organization|organisation|location|place\b|target\s+audience|audience"),
    ("program", r"programme\b|program\b|event\s*/\s*competition|competition\b|event\b|conference|position"),
    ("year", r"academic\s+year|\byear\b|period\b|duration\b|year\s+of\s+signing|filed|date\s*/?\s*duration|date\s*/\s*period"),
    ("date", r"\bdate\b|held\s+on|\bon\s+\d|event\s+name\s*&\s*date"),
    ("amount", r"amount|rupees|rs\.?|lakh|cost|price|sanctioned|invoice"),
    ("status", r"status|no\.\s*of\s+students|participated"),
    ("regno", r"register\s+no|reg\.?\s*no|roll\s+no"),
    ("details", r"details\b|description|purpose\b|activity\b|activities\b|invited\s+experts|outcome\b|impact\b|remarks|proceedings|winning\s+position"),
]
SLOT_NAMES = ["s_no", "title", "person", "org", "program", "year", "date", "amount", "status", "regno", "details"]


def slot_index(slots, name):
    for idx, slot in slots.items():
        if slot == name:
            return idx
    return None


def classify_header(cells):
    """Return {slot: index} from a header row, or None if it is not a header."""
    slots = {}
    for idx, cell in enumerate(cells):
        c = clean(cell).lower()
        if not c:
            continue
        for slot, pattern in SLOT_PATTERNS:
            if slot in slots.values():
                continue
            if re.search(pattern, c, re.I):
                slots[idx] = slot
                break
    if len(slots) < 2:
        return None
    return slots


def is_header_row(cells):
    c = [clean(x).lower() for x in cells]
    nonempty = [x for x in c if x]
    if len(nonempty) < 2:
        return False
    if classify_header(cells) and len(classify_header(cells)) >= 2:
        return True
    named = sum(1 for x in nonempty if re.search(r"(s\.no|sl\.no|name|title|year|date|amount|activity|details|industry|agency|status|faculty|event|period|company|award|programme|program|duration|theme|expert|no\.?$)", x))
    return named >= len(nonempty) - 1 and all(len(x) <= 40 for x in nonempty)


def extract_tables(html):
    i = html.find("Breadcrumb")
    j = html.find("Quick Links")
    if i >= 0:
        html = html[i:]
    if j >= 0:
        html = html[:j]
    soup = BeautifulSoup(html, "lxml")
    return soup.find_all("table")


def rows_with_data(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = [clean(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
        if any(cells):
            rows.append(cells)
    return rows


def band_year(cells):
    """Return an in-scope academic year if a row is a year-band marker."""
    joined = " ".join(clean(c) for c in cells)
    return parse_year_period(joined)


def short_title(text, limit=220):
    text = re.sub(r"\s+", " ", clean(text)).strip(" .;:-")
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0]
    return text


_BOUNDARY = re.compile(
    r"\s+(?:curriculum|placement|internship|industrial\s+visit|student\b|faculty\b|research\b|"
    r"project\s+work|studies\s+and\s+consultancy|joint\b|consultancy\b|training\b|"
    r"design\s+and\s+development|exchange\s+of|collaborativ|signed\b|associat|and\s+r\s*&\s*d\b)",
    re.I,
)
_YEAR_LABEL = re.compile(r"\byears?\s*[:\-]?\s*(20\d{2})\b", re.I)
_YEAR_ANY = re.compile(r"(?:^|\D)(20\d{2})(?:\D|$)")


def extract_year_label(text):
    m = _YEAR_LABEL.search(text or "")
    return int(m.group(1)) if m else None


def years_in(text):
    return set(int(m.group(1)) for m in _YEAR_ANY.finditer(text or "") if m.group(1))


def clean_org_cell(text):
    """Trim a MoU org/details cell to the industry/institute name + short theme."""
    text = clean(text)
    if len(text) > 60:
        m = _BOUNDARY.search(text)
        if m:
            text = text[: m.start()]
    text = _YEAR_LABEL.sub("", text)
    text = re.sub(r"[-,]\s*(?:19|20)\d{2}\s*$", "", text.strip())
    return clean(text).strip(" ,.-")


def parse_mou_cell(cell):
    """Return (org_name, theme) or (None, None) from a MoU cell."""
    text = clean(cell)
    if not text:
        return None, None
    low = text.lower()
    if "signed with" in low:
        head = text.split("signed with", 1)[1]
        head = head.strip().lstrip("\u201c\"'").strip()
        head = re.split(
            r"\s+(?:for|to\b|in\s+the\s+year|under)\s+", head, maxsplit=1
        )[0]
        seg = clean(head).strip(" .-\u201c\u201d\"")
        if not seg or seg.lower() == "mou" or len(seg) < 2:
            return None, None
        return seg, None
    if re.match(r"^mou$", low):
        return None, None
    org = clean_org_cell(text)
    return org or None, None


# ---------------------------------------------------------------------------
# Candidate construction
# ---------------------------------------------------------------------------
def make_candidate(page_type, candidates_cache, *, title, description=None, activity_date=None,
                   activity_date_text=None, academic_year_val=None, categories=None,
                   department=None, stakeholder=None, achievement_outcome=None, evidence=None,
                   confidence=0.85):
    """Insert a structured candidate for the current page into the store."""
    category_hint = ",".join(categories or DEFAULT_CATEGORY.get(page_type) or ["OTHER"])
    dept_json = json.dumps([department] if department else ["GENERAL"])
    cand = {
        "title": short_title(title),
        "description": description or short_title(title),
        "activity_date": activity_date,
        "activity_date_text": clean(activity_date_text) if activity_date_text else (activity_date if activity_date else None),
        "academic_year": academic_year_val,
        "category_hint": category_hint,
        "department": dept_json,
        "department_text": department or "General",
        "stakeholder": json.dumps(stakeholder or ["UNKNOWN"]),
        "stakeholder_text": "; ".join(stakeholder or []) or None,
        "achievement_outcome": achievement_outcome,
        "keywords_json": json.dumps([]),
        "evidence_text": (evidence or description or title)[:1200],
        "extraction_method": "STRUCTURED_TABLE",
        "extraction_confidence": confidence,
        "categories": categories or DEFAULT_CATEGORY.get(page_type) or [],
    }
    candidates_cache.append(cand)


def in_scope(candidate):
    if candidate["activity_date"]:
        return academic_year(candidate["activity_date"]) is not None
    text = candidate["activity_date_text"] or ""
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", text)]
    if years:
        return any(2021 <= y <= 2026 for y in years)
    return True


# ===========================================================================
# Page-type handlers
# ===========================================================================

def add_mou_candidate(url, out, org_pairs, year_int, theme=None, year_text=None, academic_year_val=None):
    """org_pairs: list of (org, theme) to emit."""
    for org, org_theme in org_pairs:
        if not org or len(org) < 2 or org.lower() == "mou":
            continue
        tt = org_theme or theme
        title = f"MoU with {org}"
        if tt and clean(tt) != clean(org):
            title = f"MoU with {org} – {short_title(tt, 160)}"
        make_candidate(
            "mou", out, title=title,
            description=short_title((org_theme or theme or org), 500),
            activity_date_text=year_text,
            academic_year_val=academic_year_val,
            categories=["INDUSTRY"],
            department=department_for(url), stakeholder=["INDUSTRY"],
            confidence=0.9,
        )


def mo_u_academic_year(year_int):
    """Map a MoU year-of-agreement to an in-window academic year, else None."""
    if not year_int:
        return None
    if 2021 <= year_int <= 2025:
        return f"{year_int}-{str(year_int + 1)[-2:]}"
    return None


def handle_mou(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        org_cell = by_slot.get("org") or by_slot.get("details")
        theme_cell = by_slot.get("title") or by_slot.get("details")
        joined = " ".join(c for c in cells if c)
        year_band = band_year(cells)
        raw_years = years_in(joined) | years_in(by_slot.get("year") or "")
        year_int = extract_year_label(joined)
        if not year_int:
            year_int = min(raw_years) if raw_years else None
        if year_int and year_int < 2021:
            continue
        if year_int and year_int > 2026:
            continue
        if year_band and year_band[:4] not in {"2021", "2022", "2023", "2024", "2025"}:
            continue
        ay = mo_u_academic_year(year_int)
        if org_cell and clean(org_cell):
            org, org_theme = parse_mou_cell(org_cell)
            if org:
                add_mou_candidate(
                    url, out, [(org, org_theme)], year_int,
                    theme=theme_cell if clean(theme_cell) != clean(org_cell) else None,
                    year_text=by_slot.get("year") or (str(year_int) if year_int else None),
                    academic_year_val=year_band or ay,
                )
                continue
        if clean(theme_cell):
            theme = parse_mou_cell(theme_cell)[0] or theme_cell
            if len(theme.split()) >= 2:
                add_mou_candidate(
                    url, out, [(theme, None)], year_int,
                    year_text=by_slot.get("year"),
                    academic_year_val=year_band or ay,
                )


def handle_achievements(url, table, out, seen_keys):
    rows = rows_with_data(table)
    band = None
    # Determine header row (skip band rows and sub-headers)
    header_idx, slots, band = None, None, None
    for i, cells in enumerate(rows):
        if band_year(cells) and not is_header_row(cells):
            band = band_year(cells); continue
        if is_header_row(cells):
            slots = classify_header(cells)
            if slots:
                header_idx = i
            break
    if header_idx is None or not slots:
        return
    groups = {}
    for cells in rows[header_idx + 1:]:
        b = band_year(cells)
        if b and not is_header_row(cells):
            band = b; continue
        if is_header_row(cells) and classify_header(cells):
            band = None; continue
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        person = by_slot.get("person")
        award = by_slot.get("title")
        program = by_slot.get("program") or by_slot.get("org")
        year_cell = by_slot.get("year")
        year_val = band
        if year_cell:
            from_list = parse_year_period(year_cell)
            if from_list:
                year_val = from_list
        if not award or clean(award).lower() in {"-", "nil", "na", "n/a", "activity", "award"}:
            continue
        key = (to_normalized_title(award), to_normalized_title(program or ""), year_val or "")
        groups.setdefault(key, {"award": award, "program": program, "year": year_val,
                                "people": [], "regs": []}).setdefault("people", [])
        if person and clean(person):
            groups[key]["people"].append(person)
        if by_slot.get("regno") and clean(by_slot.get("regno")):
            groups[key]["regs"].append(clean(by_slot.get("regno")))
    for (ak, pk, yk), g in sorted(groups.items()):
        title = g["award"]
        if g["program"] and to_normalized_title(g["program"]) not in to_normalized_title(g["award"]):
            title = f"{short_title(g['award'], 150)} – {short_title(g['program'], 80)}"
        people = list(dict.fromkeys(g["people"]))
        desc = short_title(g["award"], 500)
        if people:
            desc += ". Awarded to: " + "; ".join(people[:12])
        if g["regs"]:
            desc += " (Regno: " + ", ".join(g["regs"][:6]) + ")"
        if g["year"]:
            desc += f" ({g['year']})"
        key = (to_normalized_title(title), yk)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        make_candidate(
            "achievements", out, title=title, description=desc[:1200],
            activity_date_text=f"Year: {g['year']}" if g["year"] else None,
            academic_year_val=g["year"],
            categories=["ACHIEVEMENT"], department=department_for(url),
            stakeholder=(["FACULTY"] if any("dr" in p.lower() or "prof" in p.lower() for p in people) else ["STUDENTS"]),
            achievement_outcome="Award / Recognition", confidence=0.88,
        )


def handle_patents(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title") or by_slot.get("details")
        if not title or clean(title).lower() in {"-", "nil", "na"}:
            continue
        filed = (by_slot.get("year") or "") + " " + (by_slot.get("date") or "")
        full = " ".join(c for c in cells if c)
        iso, raw = parse_exact_date(full)
        desc_parts = [p for p in [by_slot.get("person"), by_slot.get("status"), by_slot.get("amount")] if p]
        make_candidate(
            "patents", out, title=title,
            description=short_title("Patent: " + title + (". " + "; ".join(desc_parts) if desc_parts else ""), 700),
            activity_date=iso, activity_date_text=raw or filed.strip(),
            academic_year_val=academic_year(iso) if iso else (parse_year_period(full) if not iso else None),
            categories=["RESEARCH"],
            department=department_for(url),
            stakeholder=["FACULTY"],
            achievement_outcome="Patent", confidence=0.9,
        )


def handle_research_sponsored(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    for cells in rows[1:]:
        band = band_year(cells)
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title") or by_slot.get("details")
        if not title or clean(title).lower() in {"-", "nil", "na"}:
            continue
        agency = by_slot.get("org")
        amount = by_slot.get("amount")
        duration = by_slot.get("year")
        full = " ".join(c for c in cells if c)
        ay = band or parse_year_period(duration or "") or parse_year_period(full)
        desc = short_title(title, 500)
        extras = " | ".join(x for x in [agency or "", amount or "", duration or ""] if x)
        if extras:
            desc += f". {extras}"
        make_candidate(
            "sponsored-research", out, title=title, description=desc,
            activity_date_text=duration or None, academic_year_val=ay,
            categories=["RESEARCH"],
            department=department_for(url), stakeholder=["FACULTY", "INDUSTRY"] if agency else ["FACULTY"],
            confidence=0.86,
        )


def handle_consultancy_projects(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title") or by_slot.get("details")
        if not title or clean(title).lower() in {"-", "nil", "na"}:
            continue
        org = by_slot.get("org") or by_slot.get("person")
        amount = by_slot.get("amount")
        full = " ".join(c for c in cells if c)
        ay = band_year(cells) or parse_year_period(full)
        desc = short_title(title, 500)
        extras = " | ".join(x for x in [org or "", amount or ""] if x)
        if extras:
            desc += f". {extras}"
        make_candidate(
            "consultancy-projects", out, title=title, description=desc,
            activity_date_text=by_slot.get("year"), academic_year_val=ay,
            categories=["RESEARCH"], department=department_for(url),
            stakeholder=["INDUSTRY"] if org else ["FACULTY"], confidence=0.85,
        )


def handle_industry_interface(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    labels = " ".join(clean(c).lower() for c in rows[0])
    if "mou" in labels or "year of signing" in labels or "theme of mou" in labels:
        handle_mou(url, table, out)
        return
    handle_consultancy_projects(url, table, out)


def handle_outreach(url, table, out):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    band = None
    for cells in rows[1:]:
        b = band_year(cells)
        if b and not is_header_row(cells):
            band = b; continue
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title") or by_slot.get("details") or by_slot.get("person")
        if not title and len(cells) == 1 and cells[0] and len(clean(cells[0])) > 12:
            title = cells[0]
        if not title or clean(title).lower() in {"-", "nil", "na"}:
            continue
        if re.match(r"^\(\s*(?:i+|v+|x+|ii+|iii+|iv+|vi+|viii+)\s*\)|\s*\(?\d{1,2},\s*[A-Z][a-z]+\s*\d{4}", clean(title)):
            continue
        full = " ".join(c for c in cells if c)
        iso, raw = parse_exact_date(full)
        ay = band or (academic_year(iso) if iso else parse_year_period(full))
        loc = by_slot.get("org") or by_slot.get("program")
        desc = short_title(title, 500)
        if loc and clean(loc):
            desc += f". {loc}"
        make_candidate(
            "outreach-activities", out, title=title, description=desc,
            activity_date=iso, activity_date_text=raw or None, academic_year_val=ay,
            categories=["OUTREACH"], department=department_for(url),
            stakeholder=["EXTERNAL", "STUDENTS"], confidence=0.88,
        )


def category_for_event_title(title):
    t = clean(title).lower()
    for code, cues in {
        "SPORTS": ["sports", "cricket", "badminton", "tournament", "marathon", "athletics", "football", "kabaddi", "volley"],
        "WORKSHOP": ["workshop", "training programme", "bootcamp", "boot camp"],
        "HACKATHON": ["hackathon"],
        "WEBINAR": ["webinar"],
        "SEMINAR": ["seminar"],
        "CONFERENCE": ["conference"],
        "GUEST_LECTURE": ["guest lecture", "expert lecture", "keynote", "technical talk", "techtalk", "tech talk"],
        "FDP": ["fdp", "faculty development"],
        "STTP": ["sttp", "short term training"],
        "SYMPOSIUM": ["symposium"],
        "TECH_FEST": ["tech fest", "technical fest"],
        "INTERNSHIP": ["internship"],
        "ORIENTATION": ["orientation"],
        "CULTURAL": ["cultural", "ethnic", "dance", "music", "celebration", "fest", "talent"],
        "NSS": ["nss"],
        "NCC": ["ncc"],
        "ALUMNI": ["alumni"],
        "INDUSTRY": ["industry visit", "industrial visit"],
        "ACHIEVEMENT": ["design contest", "paper presentation", "quiz", "competition", "contest"],
    }.items():
        if any(cue in t for cue in cues):
            return code
    return "CLUB"


def handle_event_tables(url, table, out, page_type, seen_event_keys):
    rows = rows_with_data(table)
    if not rows:
        return
    # Skip aggregate/count tables: no recognisable header, or cells are counts.
    if not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    header_lower = " ".join(clean(c) for c in rows[0]).lower()
    count_table = bool(re.search(r"count|number of events|total", header_lower))
    title_slot = slot_index(slots, "title")
    if count_table or title_slot is None:
        return
    date_slot = slot_index(slots, "date") or slot_index(slots, "year")
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title")
        if not title or clean(title).lower() in {"-", "nil", "na", "event"}:
            continue
        if any(re.fullmatch(r"\d{1,3}(?:\s*[-/–]\s*\d{1,3})?", clean(c)) for c in cells):
            pass
        full = " ".join(c for c in cells if c)
        iso, raw = parse_exact_date(full)
        ay = academic_year(iso) if iso else parse_year_period(full)
        if page_type == "past-events" and not iso and not ay:
            continue
        desc = short_title(title, 500)
        date_label = by_slot.get("date") or by_slot.get("year") or raw or None
        if date_label and clean(date_label):
            desc += f". {date_label}"
        key = (to_normalized_title(title), iso or "")
        if key in seen_event_keys:
            continue
        seen_event_keys.add(key)
        categories = DEFAULT_CATEGORY.get(page_type) or [category_for_event_title(title)]
        program_val = by_slot.get("program")
        if program_val and clean(program_val) and category_for_event_title(program_val) != "CLUB":
            categories = [category_for_event_title(program_val)]
        make_candidate(
            page_type, out, title=title, description=desc,
            activity_date=iso, activity_date_text=raw or None, academic_year_val=ay,
            categories=categories, department=department_for(url),
            stakeholder=None, confidence=0.8,
        )


def handle_associations(url, table, out, seen_event_keys):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    title_slot = slot_index(slots, "title")
    if title_slot is None:
        return
    header_lower = " ".join(clean(c) for c in rows[0]).lower()
    if "office position" in header_lower or "register" in header_lower:
        return
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title")
        if not title or clean(title).lower() in {"-", "nil", "na", "event"}:
            continue
        if cells and len(cells) >= 2 and re.fullmatch(r"\d+", clean(cells[0])) and not clean(title):
            continue
        full = " ".join(c for c in cells if c)
        iso, raw = parse_exact_date(full)
        ay = academic_year(iso) if iso else parse_year_period(full)
        experts = by_slot.get("details")
        desc = short_title(title, 500)
        if experts and clean(experts) and clean(experts) != "Nil":
            desc += f". Resource: {short_title(experts, 300)}"
        key = (to_normalized_title(title), iso or "")
        if key in seen_event_keys:
            continue
        seen_event_keys.add(key)
        if iso and academic_year(iso) is not None:
            make_candidate(
                "associations", out, title=title, description=desc,
                activity_date=iso, activity_date_text=raw or None, academic_year_val=ay,
                categories=[category_for_event_title(title)], department=department_for(url),
                stakeholder=["STUDENTS"], confidence=0.8,
            )


def handle_professional_societies(url, table, out, seen_event_keys):
    rows = rows_with_data(table)
    if not rows or not is_header_row(rows[0]):
        return
    slots = classify_header(rows[0])
    if not slots:
        return
    details_slot = slot_index(slots, "details")
    title_slot = slot_index(slots, "title")
    if details_slot is None:
        return
    for cells in rows[1:]:
        by_slot = {slot: cells[idx] for idx, slot in slots.items() if idx < len(cells)}
        title = by_slot.get("title")
        activities = by_slot.get("details")
        if not title or not activities or clean(activities).lower() in {"-", "nil", "na", "activities"}:
            continue
        full = " ".join(c for c in cells if c)
        org_cell = by_slot.get("org")
        if org_cell and clean(org_cell):
            pass
        ay = band_year(cells) or parse_year_period(full)
        iso, raw = parse_exact_date(full)
        if iso:
            ay = academic_year(iso)
        year_label = extract_year_label(full)
        if year_label and not 2021 <= year_label <= 2026 and not iso:
            continue
        key = (to_normalized_title(title), iso or "")
        if key in seen_event_keys:
            continue
        seen_event_keys.add(key)
        make_candidate(
            "professional-societies", out, title=title,
            description=short_title(f"{title}. Activities: {activities}", 700),
            activity_date=iso, activity_date_text=raw or by_slot.get("year"),
            academic_year_val=ay,
            categories=[category_for_event_title(activities) if category_for_event_title(activities) != "CLUB" else "CLUB"],
            department=department_for(url),
            stakeholder=["STUDENTS"], confidence=0.72,
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
SKIPPED_TYPES = {
    "publications", "publication", "higher-studies", "higherstudies", "internship",
    "academic-research", "academics-research", "newsletter", "magazine-altitude",
    "visiting-faculty", "visiting-faculty-research-fellowship", "projects",
}


class StructuredTableExtractor:
    def __init__(self, archive_root=RAW_DATA_DIR):
        self.archive_root = Path(archive_root)

    def extract_source(self, row):
        """row: sqlite3.Row with archive_path, source_url, page_title, id."""
        url = row["source_url"]
        page_type = page_type_for(url)
        if not page_type or page_type in SKIPPED_TYPES:
            return {"page_type": page_type, "candidates": [], "skipped": True, "reason": "type-not-handled"}
        path = row["archive_path"]
        html = (self.archive_root / path).read_text(encoding="utf-8", errors="replace")
        out = []
        seen_ach = set()
        seen_ev = set()
        for table in extract_tables(html):
            raw_rows = rows_with_data(table)
            if len(raw_rows) < 2:
                continue
            try:
                if page_type == "mou":
                    handle_mou(url, table, out)
                elif page_type in {"achievements", "awards"}:
                    handle_achievements(url, table, out, seen_ach)
                elif page_type == "patents":
                    handle_patents(url, table, out)
                elif page_type == "sponsored-research":
                    handle_research_sponsored(url, table, out)
                elif page_type == "consultancy-projects":
                    handle_consultancy_projects(url, table, out)
                elif page_type == "industry-interface":
                    handle_industry_interface(url, table, out)
                elif page_type == "outreach-activities":
                    handle_outreach(url, table, out)
                elif page_type == "associations":
                    handle_associations(url, table, out, seen_ev)
                elif page_type == "professional-societies":
                    handle_professional_societies(url, table, out, seen_ev)
                elif page_type in {"past-events", "upcoming-events"}:
                    handle_event_tables(url, table, out, page_type, seen_ev)
            except Exception:
                continue
        candidates = [c for c in out if in_scope(c)]
        return {"page_type": page_type, "candidates": candidates, "skipped": False, "reason": None}