"""Text cleaning: strip HTML, normalize whitespace/unicode/punctuation/dates."""

import re
import unicodedata
from datetime import datetime


_HAS_EMOJI = None
try:
    import emoji
    _HAS_EMOJI = True
except ImportError:
    _HAS_EMOJI = False


HTML_TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
WHITESPACE_RE = re.compile(r"\s+")
PUNCT_KEEP = re.compile(r"[^\w\s]+", re.UNICODE)

MONTHS_SHORT = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONTHS_LONG = r"(January|February|March|April|May|June|July|August|September|October|November|December)"

DATE_PATTERNS = [
    ("%Y-%m-%d", re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")),
    ("%d %b %Y", re.compile(rf"\b(\d{{1,2}})\s+{MONTHS_SHORT}[a-z]*\s*,?\s*(\d{{4}})\b", re.IGNORECASE)),
    ("%d %B %Y", re.compile(rf"\b(\d{{1,2}})\s+{MONTHS_LONG}\s*,?\s*(\d{{4}})\b", re.IGNORECASE)),
    ("%b %d, %Y", re.compile(rf"\b{MONTHS_SHORT}[a-z]*\s+(\d{{1,2}})\s*,?\s*(\d{{4}})\b", re.IGNORECASE)),
    ("%d/%m/%Y", re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")),
    ("%d-%m-%Y", re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b")),
]


def _emoji_safe(text):
    return text


def strip_html(text):
    if not text:
        return ""
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = HTML_TAG_RE.sub(" ", text)
    return text


def normalize_unicode(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    if _HAS_EMOJI:
        try:
            text = emoji.replace_emoji(text, "")
        except Exception:  # noqa: BLE001
            pass
    else:
        text = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF\U0000FE00-\U0000FE0F]", "", text)
    return text


def normalize_whitespace(text):
    if not text:
        return ""
    return WHITESPACE_RE.sub(" ", text).strip()


def normalize_punctuation(text):
    if not text:
        return ""
    return PUNCT_KEEP.sub(" ", text)


def normalize_date(date_text):
    """Return YYYY-MM-DD from a variety of common formats, else None."""
    if not date_text:
        return None
    text = date_text.strip()
    for fmt, pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            parts = m.groups()
            try:
                if fmt == "%Y-%m-%d":
                    dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                elif fmt in ("%d %b %Y", "%d %B %Y"):
                    month = int(month_to_num(parts[1]))
                    dt = datetime(int(parts[2]), month, int(parts[0]))
                elif fmt == "%b %d, %Y":
                    month = int(month_to_num(parts[0]))
                    dt = datetime(int(parts[2]), month, int(parts[1]))
                else:
                    dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}


def month_to_num(month_name):
    return MONTH_NAMES.get(month_name.lower()[:3])


def clean_text(text):
    """Full cleaning pipeline on a single text string."""
    text = strip_html(text)
    text = normalize_unicode(text)
    text = normalize_whitespace(text)
    return text


def clean_record(record):
    """Apply cleaning to a record dict. Returns a NEW dict."""
    cleaned = dict(record)
    for field in ("title", "description", "venue", "organizer", "resource_person"):
        if cleaned.get(field):
            cleaned[field] = clean_text(str(cleaned[field]))
    if cleaned.get("activity_date"):
        cleaned["activity_date"] = normalize_date(str(cleaned["activity_date"]))
    if cleaned.get("activity_date_end"):
        cleaned["activity_date_end"] = normalize_date(str(cleaned["activity_date_end"]))
    return cleaned