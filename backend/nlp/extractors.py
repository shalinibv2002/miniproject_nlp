"""Phase 4: Extract structured fields from free-text activity descriptions.

Methods:
  - Regex/rule patterns: dates, venues ('held at...', 'venue:'),
    resource persons ('resource person:', 'chief guest:').
  - spaCy NER: PERSON and ORG entities.
  - Dictionary/fuzzy match against the TCE department list (with aliases).

Anything not confidently extracted stays None/Unknown -- nothing is guessed.
"""

import logging
import re

from rapidfuzz import fuzz, process

from backend.nlp.dictionaries import load_department_dict

logger = logging.getLogger("tce.extractors")

_nlp = None


def get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        from backend.config import SPACY_MODEL
        try:
            _nlp = spacy.load(SPACY_MODEL)
        except OSError:
            logger.warning("spaCy model %s not found; NER disabled.", SPACY_MODEL)
            _nlp = None
    return _nlp


# ---------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------
VENUE_PATTERNS = [
    re.compile(r"\b(?:venue|venues)\s*[:is-]+\s*([A-Za-z0-9][^.\n]*?)(?=\s*(?:resource|date|for more|register|contact|organized|$)\.?\s)", re.IGNORECASE),
    re.compile(r"\bheld\s+at\s+([A-Za-z0-9][^.\n]*?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"\bconducted\s+at\s+([A-Za-z0-9][^.\n]*?)(?:\.|$)", re.IGNORECASE),
    re.compile(r"\bin\s+(the\s+)?([A-Za-z]+hall|auditorium|seminar\s+hall|campus|ground|field|lab[^\.,]*?)(?:\.|$)", re.IGNORECASE),
]

RESOURCE_PERSON_PATTERNS = [
    re.compile(
        r"(?:resource\s+persons?|speakers?|chief\s+guests?)\s*:\s*"
        r"([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*){1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:resource\s+person|chief\s+guest)\s+(?:is|was)\s+"
        r"([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*){1,3})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:delivered\s+by|given\s+by|addressed\s+by)\s+"
        r"([A-Z][A-Za-z.]*(?:\s+[A-Z][A-Za-z.]*){1,3})",
        re.IGNORECASE,
    ),
]

ORGANIZER_PATTERNS = [
    re.compile(
        r"(?:organized|organised)\s+by\s+(?:the\s+)?"
        r"([A-Za-z][^,.]{3,70}?)(?=\s*(?:was|were|on|at|in|for|conducted|held|to)|$)",
        re.IGNORECASE,
    ),
]

_PERSON_STOP = {"the", "and", "of", "on", "was", "were", "who", "delivered",
                "addressed", "graced", "a", "an", "in", "to", "from", "organised",
                "organized", "with", "his", "her"}


def _clean_person(raw):
    if not raw:
        return None
    tokens = raw.split()
    tokens = [t for t in tokens if t.rstrip(".").lower() not in _PERSON_STOP]
    if not tokens:
        return None
    name = " ".join(tokens).replace(" .", ".").strip(" ,.-")
    return name if len(name) >= 3 else None

# ---------------------------------------------------------------
# Keyword cues by category (shared with classifier baseline)
# ---------------------------------------------------------------
CATEGORY_KEYWORDS = {
    "Workshop": ["workshop", "hands-on", "certificate course", "training program", "training programme", "bootcamp"],
    "Seminar": ["seminar", "technical talk", "guest talk", "industry talk"],
    "Conference": ["conference", "international conference", "national conference"],
    "Symposium": ["symposium", "symposia"],
    "Guest Lecture": ["guest lecture", "special lecture", "invited lecture", "invited talk", "guest talk"],
    "Faculty Development Programme": ["fdp", "faculty development"],
    "Short Term Training Programme": ["sttp", "short term training", "short-term training"],
    "Hackathon": ["hackathon", "hack-a-thon"],
    "Technical Festival": ["technical festival", "tech fest", "symposium cum exhibition"],
    "Cultural Event": ["cultural", "competitions", "dance", "music", "cultural fest"],
    "Sports and Games": ["sports", "athletics", "tournament", "cricket", "football", "volleyball", "kabaddi", "fitness"],
    "NCC Activity": ["ncc", "national cadet corps", "cadet"],
    "NSS Activity": ["nss", "national service scheme", "blood donation", "swachh", "village adoption"],
    "Clubs and Chapters": ["club", "chapter", "society meeting", "ieee", "iste", "iie", "technical association"],
    "Outreach and Extension": ["outreach", "school students", "extension activity", "community", "rural", "awareness campaign"],
    "Industry Collaboration": ["mou", "industry", "collaboration", "industry visit", "memorandum of understanding"],
    "Achievement and Award": ["achievement", "award", "rank holder", "best outgoing", "international recognition", "awarded"],
    "Placement Activity": ["placement", "recruitment", "campus drive", "placement training", "career guidance", "career development"],
    "Internship": ["internship", "industrial training"],
    "Research and Consultancy": ["research", "consultancy", "patent", "sponsored", "funded project", "seed money"],
    "Alumni Event": ["alumni", "reunion", "silver jubilee reunion", "alumni meet"],
    "Orientation and Convocation": ["orientation", "convocation", "induction", "fresher"],
    "Campus Life": ["hostel", "campus", "canteen", "transport", "health camp", "medical camp"],
    "Webinar": ["webinar", "online session", "virtual talk", "online course", "online fdp"],
}

EXTRACTION_METHODS = {
    "regex": 6,
    "spacy": 5,
    "dictionary": 7,
}


def regex_extract_dates(text):
    """Return list of ISO dates found via patterns."""
    from backend.database.cleaner import normalize_date
    if not text:
        return []
    dates = []
    for token in re.split(r"[\s,;]+", text):
        d = normalize_date(token)
        if d and d not in dates:
            dates.append(d)
    # also catch exact date ranges
    for m in re.finditer(r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*,?\s*\d{4})\b", text, re.IGNORECASE):
        pass
    return dates


def _capture(pattern, text):
    """Try pattern; return first non-empty capture group or None."""
    m = pattern.search(text)
    if not m:
        return None
    for group in m.groups():
        if group and group.strip():
            return group.strip().rstrip(",").rstrip()
    return None


def extract_venue(text):
    if not text:
        return None
    for pattern in VENUE_PATTERNS:
        for m in pattern.finditer(text):
            val = ""
            for group in m.groups():
                if group and group.strip():
                    val = group.strip()
                    break
            if val:
                val = re.sub(r"\s+", " ", val)
                if 3 <= len(val) <= 60:
                    return val
    return None


def extract_resource_person(text):
    if not text:
        return None
    for pattern in RESOURCE_PERSON_PATTERNS:
        m = pattern.search(text)
        if m:
            person = _clean_person(m.group(1))
            if person:
                return person
    return None


def extract_organizer(text):
    if not text:
        return None
    for pattern in ORGANIZER_PATTERNS:
        m = pattern.search(text)
        if m:
            val = re.sub(r"\s+", " ", m.group(1)).strip(" ,")
            if 4 <= len(val) <= 70:
                return val
    return None


def extract_spacy_entities(text, nlp=None):
    """Return list of dicts {entity_type, entity_text, confidence} from spaCy NER."""
    nlp = nlp or get_nlp()
    if nlp is None or not text:
        return []
    doc = nlp(text)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ("PERSON", "ORG", "GPE", "DATE", "PRODUCT", "MONEY"):
            txt = ent.text.strip(" \n,.")
            if txt and len(txt) >= 3:
                entities.append({
                    "entity_type": ent.label_,
                    "entity_text": txt,
                    "confidence": float(ent._.char_span_confidence) if hasattr(ent._, "char_span_confidence") else 0.8,
                })
    return entities


def extract_department_mentions(text, min_score=80, conn=None):
    """Dictionary + fuzzy match for department mentions.

    Returns list of dicts {department_id, code, name, matched_term, score}.
    If the text clearly references a department by name/alias (exact), high
    confidence. Otherwise fuzzy matching, keeping only >= min_score.
    """
    if not text:
        return []
    depts = load_department_dict(conn)
    lower = text.lower()
    spans = []

    # exact alias match, longest term wins on overlapping spans
    for dept in depts:
        candidates = [dept["name"].lower(), (dept["short_name"] or "").lower()] + dept["aliases"]
        for cand in candidates:
            if not cand:
                continue
            offset = lower.find(cand)
            if offset >= 0:
                while offset >= 0:
                    spans.append((offset, offset + len(cand), dept, cand))
                    offset = lower.find(cand, offset + 1)
                break

    covered = set()
    for i, (s, e, _, _) in enumerate(spans):
        for j, (o_s, o_e, _, _) in enumerate(spans):
            if i != j and o_s <= s and e <= o_e and (o_e - o_s) > (e - s):
                covered.add(i)
                break
    matches = [{
        "department_id": spans[i][2]["id"],
        "code": spans[i][2]["code"],
        "name": spans[i][2]["name"],
        "matched_term": spans[i][3],
        "score": 100.0,
    } for i in range(len(spans)) if i not in covered]

    # fuzzy match against full names only to avoid over-matching short aliases
    if not matches:
        names = {d["name"].lower(): d for d in depts}
        best = process.extractOne(lower, list(names.keys()), scorer=fuzz.WRatio)
        if best and best[1] >= min_score:
            dept = names[best[0]]
            matches.append({
                "department_id": dept["id"],
                "code": dept["code"],
                "name": dept["name"],
                "matched_term": best[0],
                "score": float(best[1]),
            })
    return matches


def extract_keywords(text, min_len=4):
    """Naive keyword extraction: meaningful tokens (not stopwords, len>=4)."""
    if not text:
        return []
    nlp = get_nlp()
    keywords = []
    if nlp:
        doc = nlp(text)
        for token in doc:
            if token.is_stop or not token.is_alpha or len(token.text) < min_len:
                continue
            keywords.append(token.text.lower())
    else:
        stop = {"the", "and", "for", "with", "this", "that", "from", "held", "will", "was", "have", "been"}
        for tok in re.findall(r"[A-Za-z]{4,}", text.lower()):
            if tok not in stop:
                keywords.append(tok)
    return sorted(set(keywords))


def extract_all(text, nlp=None):
    """Run every extractor on one text block. Returns dict of results."""
    return {
        "dates": regex_extract_dates(text),
        "venue": extract_venue(text),
        "resource_person": extract_resource_person(text),
        "organizer": extract_organizer(text),
        "spacy_entities": extract_spacy_entities(text, nlp),
        "departments": extract_department_mentions(text),
        "keywords": extract_keywords(text),
    }