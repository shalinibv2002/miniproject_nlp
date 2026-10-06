# -*- coding: utf-8 -*-
"""Derived, report-grade activity fields extracted from a single canonical row.

Every field here is an *extract* of text that already exists on the row (the
post text in ``description``, the curated stakeholder/department lists and the
resolved ``activity_date``).  Nothing is invented: when a value cannot be found
with confidence the field is returned as an empty string and the report shows a
blank cell.

The module also owns ``clean_title``: the rule that a Title / Event Name /
Seminar Title / Research Topic column holds ONLY the title itself -- never the
surrounding LinkedIn caption, dates, venues, participant counts, hashtags or
promotional prose.

Only the categories listed in ``REPORT_FIELD_SPECS`` pay for this work; every
other category short-circuits through ``fields_for``.
"""
from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Shared normalisation helpers
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
#: markdown / social decoration: *, _, #, ~, `, > and the pipe separators that
#: LinkedIn captions use between the headline and the body.
_MD_RE = re.compile(r"[*_~`>#]+")
_HANDLE_RE = re.compile(r"@[\w.\-]+")
_BULLET_RE = re.compile(r"^[\s\-•·▪◦>\|]+")
#: Emoji, pictographs, dingbats, symbols and variation selectors.
_EMOJI_RE = re.compile(
    "[\u2190-\u21FF\u2300-\u27BF\u2B00-\u2BFF\u3030\u303D\uFE0F\uFE0E\u200D"
    "\u20E3\u2600-\u26FF\u2700-\u27BF\U0001F000-\U0001FAFF"
    "\U0001F1E6-\U0001F1FF]+")
#: Currency amounts: a fee or prize never belongs to a title.
_CURRENCY_RE = re.compile(r"[₹$€£¥]+|\b(?:rs\.?|inr|usd)\.?\s*\d[\d,.]*", re.I)
#: Trailing separators left behind once the decoration is stripped.
_TAIL_RE = re.compile(r"[\s\-–—:;,|/\\*_~#>\.\(\)\[\]\"']+$")
_LEAD_STOP_RE = re.compile(r"^[\s\-–—:;,|/\\*_~#>\.]+")
#: A word that only continues the sentence, never the title.
_STOPWORDS = frozenset("""
a an the and or of for to in on at by with from into over under about as is are
was were be been being this that these those it its their our your his her
you they we i us them him me my our new latest event events activity activities
""".split())


def _norm_ws(text):
    return _WS.sub(" ", text or "").strip()


def _strip_decoration(text):
    """Remove URLs, markdown, handles and emoji; keep the words."""
    if not text:
        return ""
    s = _URL_RE.sub(" ", text)
    s = _HANDLE_RE.sub(" ", s)
    s = _MD_RE.sub(" ", s)
    s = _EMOJI_RE.sub(" ", s)
    s = _CURRENCY_RE.sub(" ", s)
    s = unicodedata.normalize("NFKC", s)
    return _norm_ws(s)


def _tidy(value, limit=160):
    """Trim a fragment to a clean single-line report value."""
    s = _strip_decoration(value)
    s = _LEAD_STOP_RE.sub("", s)
    s = _TAIL_RE.sub("", s)
    s = _WS.sub(" ", s).strip()
    if len(s) > limit:
        cut = s[:limit].rstrip()
        sp = cut.rfind(" ")
        s = (cut[:sp] if sp > limit * 0.6 else cut).rstrip(_TAIL_RE)
    return s.strip()


def _content_words(value):
    return [w for w in re.findall(r"[A-Za-z0-9][\w''./&+-]*", value or "")
            if w.lower() not in _STOPWORDS]


# ---------------------------------------------------------------------------
# Title cleaning
# ---------------------------------------------------------------------------

#: Words that, when they start a new clause, prove the headline has ended and
#: the caption's prose has begun.  Matched case-sensitively at a clause start so
#: that a title such as "AI in Healthcare" is never cut in half.
_PROSE_OPENERS = (
    "The", "This", "That", "These", "Those", "Our", "We", "They", "It", "Its",
    "Their", "Students", "Student", "Faculty", "Participants", "Attendees",
    "An", "A", "On", "In", "At", "Held", "Organized", "Organised", "Conducted",
    "As", "Part", "With", "During", "Registration", "Register", "Cordially",
    "Invites", "Inviting", "Invite", "Successfully", "Glad", "Delighted",
    "Thanks", "Thank", "Celebrating", "Commemorating", "Marking", "Occasion",
    "Join", "Joining", "Welcome", "Explore", "Discover", "Learn", "Brought",
    "Took", "Was", "Were", "Has", "Have", "Had", "Is", "Are", "Am", "Everyone",
    "Ladies", "Gents", "Gathering", "Programme", "Program",
)
_OPENERS = "|".join(sorted(set(_PROSE_OPENERS), key=len, reverse=True))
#: A clause starts at the beginning of the block, right after a sentence mark,
#: a line break, a separator or a " - " dash.
_PROSE_RE = re.compile(
    r"(?:^|(?<=[.!?\n\r|•·–—])|(?<=\s-\s))\s*(?=(?:%s)\b)" % _OPENERS)
_OPENER_HEAD_RE = re.compile(r"^(?:%s)\b" % _OPENERS)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
#: Openings that prove the line is an invitation / announcement, not a title.
#: Nouns such as "inauguration" are allowed: they appear in real titles
#: ("Successful Inauguration of the Alumni Student Council").
_ANNOUNCEMENT_RE = re.compile(
    r"\b(?:invites?|inviting|cordially|pleasure|proudly|gratefully|warmly|"
    r"request(?:s)?\s+you|join\s+us|being\s+held|scheduled|will\s+be\s+held|"
    r"organiz(?:e|ed|es|ing)|organis(?:e|ed|es|ing)|conduct(?:s|ed|ing)?\b|"
    r"felicitat(?:e|ed|es|ing)|inaugurat(?:e|ed|es|ing)|thanks\s+to|"
    r"grateful|congratulat\w*|registration\s+(?:is|now|open|closed)|"
    r"register\s+now|regards|sincerely|dept\b)\b", re.I)
#: A title is short; anything longer is a caption sentence.
_TITLE_WORD_MAX = 16
_TITLE_WORD_MIN = 2
_SCAN_LINES = 6
#: Tokens that belong to a date / time line, never to a title.  A bare year is
#: NOT one of them: event names carry their own year.
_DATE_TOKEN_RE = re.compile(
    r"^(?:[0-3]?\d[./-][0-3]?\d(?:[./-]\d{2,4})?|[0-3]?\d:\d{2}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*|"
    r"(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)|am|pm|ist|utc|"
    r"\d{1,2}(?:st|nd|rd|th)?)$", re.I)
_META_TOKEN_RE = re.compile(
    r"^(?:\d{1,4}|[0-3]?\d[./-][0-3]?\d(?:[./-]\d{2,4})?|[0-3]?\d:\d{2}|"
    r"(?:19|20)\d{2}|(?:19|20)\d{2}\s*[-–]\s*\d{2,4}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*|"
    r"(?:mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun|am|pm|ist|utc)|"
    r"date|time|venue|venue:|location|hall|auditorium|laboratory|lab|block|"
    r"building|ground|room|theatre|theater|online|offline|hybrid|"
    r"morning|evening|afternoon|night|noon|rsvp|register|registration|seat|"
    r"seats|admission|entry|contact|phone|email|qr|map|claude|celebrant|"
    r"session|slot)s?\.?\+?$", re.I)
#: A line that is nothing but hashtags carries no headline.
def _is_hashtag_line(line):
    return (line or "").count("#") >= 2
#: Labels that introduce logistics, never a headline.
_META_LABEL_RE = re.compile(
    r"^\W*(?:date|dates|time|venue|location|register|registration|rsvp|contact|"
    r"seats?|admission|entry|prize\s*pool|prize|perks?|fee|fees|"
    r"brochure|website|enquir\w+|queries|slots?|last\s+date|"
    r"reporting\s+time)\b\s*[:\-–—]", re.I)
#: "Congratulations to Mrs. K. Raji!" splits into a bare person name: that is a
#: recipient, never a headline.
_PERSON_FRAGMENT_RE = re.compile(
    r"^(?:(?:mr|mrs|ms|dr|prof)\.?\s+)?[A-Z][a-z]+(?:\s+[A-Z]\.?)*"
    r"(?:\s+[A-Z][a-z]+)?\s*[.!]?$")
#: A list enumerator ("1 Digital Twin Technologies ...") is not part of a title.
_LIST_ENUM_RE = re.compile(r"^\d{1,2}[.)]\s+")
#: A person with a job title is a speaker/guest line, not a title.
_ROLE_RE = re.compile(
    r"\b(?:principal|vice\s*chancellor|chancellor|registrar|dean|"
    r"professor|prof\.?|asst\.?\s*prof|associate\s*prof|assistant\s*prof|"
    r"director|co-?ordinator|chair(?:man|person)|president|"
    r"manager|officer|secretary|joint\s*commissioner|commissioner|collector|"
    r"inspector|governor|minister|councillor|"
    r"visiting\s+professor|research\s+scholar)\b", re.I)
#: A real headline never begins with a lower-case function word: such a segment
#: is the tail of the previous sentence.
_LOWERCASE_HEAD_RE = re.compile(r"^[a-z]")
#: The organiser's own name is never the title of the activity it organised.
_INSTITUTION_RE = re.compile(
    r"^(?:the\s+)?(?:thiagarajar\s+(?:college|school)(?:\s+of\s+[\w\s]+?)?|tce)"
    r"(?:\s*\([^)]{0,24}\)?)?"
    r"(?:\s*,\s*(?:madurai|chennai|coimbatore))?$", re.I)
_DEPARTMENT_HEAD_RE = re.compile(
    r"^(?:the\s+)?(?:dept|department)\s+of\s+[A-Z][\w\s,&'’.()-]*$", re.I)
#: A segment ending on a function word is the head of a longer sentence.
_DANGLING_RE = re.compile(
    r"\b(?:to|of|for|on|in|at|by|with|from|and|or|the|a|an|as|is|was|were|"
    r"that|which|our|its|their|his|her|my|your)$", re.I)
#: Result language describes a win, never the activity.
_RESULT_RE = re.compile(
    r"\b(?:secured|won|awarded|received|selected|ranked|congratulat\w*|"
    r"proud|celebrat\w*|achievement|prize|award)\b", re.I)
#: A venue is never the title either.
_VENUE_RE = re.compile(
    r"\b(?:hall|auditorium|laboratory|lecture\s+hall|seminar\s+hall|"
    r"conference\s+hall|main\s+ground|ground\s+floor|class\s+room|"
    r"classroom|theatre|theater|lecture\s+theatre|auditorium)\b", re.I)


def _segments(text, limit_lines=_SCAN_LINES):
    """Candidate headline segments.

    A caption may put the headline on its own line, inside quotation marks or
    on either side of a "|" separator, so all three shapes are offered and the
    most title-like one wins.
    """
    out = []
    lines = []
    for line in (text or "").splitlines():
        if _strip_decoration(line):
            lines.append(line)
        if len(lines) >= limit_lines:
            break
    if not lines and (text or "").strip():
        lines = [(text or "").strip()]
    for line in lines:
        if _is_hashtag_line(line):
            continue
        clean = _strip_decoration(line)
        if clean:
            out.append(clean)
        for part in re.split(r"[“”\"']{1,2}", line):
            part = _strip_decoration(part)
            if part:
                out.append(part)
        for part in re.split(r"\s*[|•·]\s*", line):
            part = _strip_decoration(part)
            if part:
                out.append(part)
        for sentence in _SENTENCE_SPLIT_RE.split(clean, maxsplit=2)[:2]:
            if sentence and sentence != clean:
                out.append(sentence)
    return out


def _score_segment(segment, order=0):
    """How strongly a segment looks like a title rather than caption prose."""
    words = _content_words(segment)
    count = len(words)
    if count < _TITLE_WORD_MIN:
        return None
    score = 0.0
    if not _OPENER_HEAD_RE.match(segment):
        score += 3.0
    if _ANNOUNCEMENT_RE.search(segment):
        score -= 6.0
    if _ROLE_RE.search(segment):
        score -= 4.0
    if _META_LABEL_RE.match(segment):
        score -= 6.0
    if _LOWERCASE_HEAD_RE.match(segment):
        score -= 5.0
    if _INSTITUTION_RE.match(segment) or _DEPARTMENT_HEAD_RE.match(segment):
        score -= 5.0
    if _VENUE_RE.search(segment):
        score -= 4.0
    if _DANGLING_RE.search(segment):
        score -= 3.0
    if _RESULT_RE.search(segment):
        score -= 3.0
    tokens = segment.split()
    stripped = [t.strip(".,:;!?()[]\"'") for t in tokens]
    dates = sum(1 for t in stripped if _DATE_TOKEN_RE.match(t))
    if stripped and dates == len(stripped):
        return None
    if dates >= 2:
        score -= 4.0
    if _ROLE_ONLY_RE.match(segment):
        score -= 4.0
    if _PERSON_FRAGMENT_RE.match(segment) and len(_content_words(segment)) <= 3:
        score -= 4.0
    parts = [p.strip() for p in segment.split("|") if p.strip()]
    if len(parts) > 1 and all(
            _INSTITUTION_RE.match(p) or _DEPARTMENT_HEAD_RE.match(p)
            or re.fullmatch(r"(?:madurai|chennai|coimbatore|tce)", p, re.I)
            for p in parts):
        score -= 4.0
    if count <= _TITLE_WORD_MAX:
        score += 2.0
    else:
        score -= min(6.0, (count - _TITLE_WORD_MAX) * 0.4)
    if re.search(r"\b(?:19|20)\d{2}\b", segment):
        score += 0.5
    if _TAIL_RE.search(segment):
        score -= 1.0
    # Prefer the earliest line when two segments are equally title-like.
    score -= order * 0.2
    return score


def clean_title(text, limit=140):
    """Return only the activity title contained in ``text``.

    The rule: never return the caption, never append a date, venue, audience or
    promotional sentence, and never invent words.  When no headline can be
    isolated the first sentence of the post is returned (still only what the
    post says).
    """
    if not (text or "").strip():
        return "Untitled LinkedIn post"

    best = None
    best_score = None
    for order, segment in enumerate(_segments(text)):
        score = _score_segment(segment, order)
        if score is None:
            continue
        if best_score is None or score > best_score:
            best, best_score = segment, score

    if not best:
        fallback = _SENTENCE_SPLIT_RE.split(
            _strip_decoration((text or "").strip()), maxsplit=1)[0]
        best = _cut_at_prose(fallback, limit=limit)
    else:
        best = _cut_at_prose(best, limit=limit)

    best = _LIST_ENUM_RE.sub("", _tidy(best, limit=limit))
    if len(_content_words(best)) < 1:
        return "Untitled LinkedIn post"
    return best


def _cut_at_prose(text, limit):
    """Truncate ``text`` at the first clause that is clearly caption prose."""
    text = (text or "").strip()
    if not text:
        return ""
    for match in _PROSE_RE.finditer(text):
        cut = text[:match.start()].strip()
        if len(_content_words(cut)) >= 2:
            text = cut
            break
    else:
        # No clause boundary: fall back to the first sentence so a long caption
        # never becomes the title.
        head = _SENTENCE_SPLIT_RE.split(text, maxsplit=1)[0]
        if len(head.split()) > 24:
            text = head
    if len(text.split()) > 24:
        head = _SENTENCE_SPLIT_RE.split(text, maxsplit=1)[0]
        if len(head.split()) > 24:
            text = " ".join(text.split()[:24])
    return text[:limit].strip()


# ---------------------------------------------------------------------------
# Person / organisation extraction
# ---------------------------------------------------------------------------

_NAME = (r"(?:(?:Dr|Mr|Mrs|Ms|Prof|Prof\.|Er|Engr)\.?\s+)?"
         r"[A-Z][\w.'\-]*(?:\s+[A-Z][\w.'\-]*){0,4}")
_ORG_STOP = re.compile(
    r"\s+(?:and|with|along with|for|from|of the|in|at|on|regarding|to|"
    r"which|who|delivered|addressed|inaugurated|felicitated|presided|"
    r"alongside|the team|all|students|faculty|participants)\b.*$", re.I)

_CHIEF_GUEST_RES = (
    re.compile(r"chief\s*guest\s*(?:of\s+the\s+\w+\s+programme?)?\s*[:\-–—]?\s*(%s)"
               % _NAME),
    re.compile(r"(?:have|had|hosted|invited)\s+((?:Mr|Mrs|Ms|Dr|Prof)\.?\s+"
               r"[^,.\n]{2,60}),?\s+as\s+(?:our|the)?\s*chief\s*guest", re.I),
    re.compile(r"(?:inaugurat(?:ed|ion)|felicit(?:ated|ating)|presided\s+over)"
               r"\s+by\s+(%s)" % _NAME),
    re.compile(r"in\s+the\s+(?:presence|august)\s+of\s+(%s)" % _NAME),
    re.compile(r"blessed\s+by\s+(%s)" % _NAME),
    re.compile(r"(?:felicitated|welcomed)\s+(?:by\s+)?(%s)" % _NAME),
)
_SPEAKER_RES = (
    re.compile(r"(?:keynote|chief|main|invited|guest|resource|technical)\s*"
               r"speaker\s*(?:of\s+the\s+\w+\s+programme?)?\s*[:\-–—]?\s*(%s)"
               % _NAME),
    re.compile(r"(?:speaker|resource\s*person|resource\s*faculty|faculty|"
               r"presenter)\s*(?:name)?\s*[:\-–—]\s*(%s)" % _NAME),
    re.compile(r"(?:session|talk|lecture|webinar|workshop|programme|program)"
               r"\s+(?:on|about)?[^.:]{0,60}?\s+(?:by|with|featuring)\s+(%s)"
               % _NAME),
    re.compile(r"(?:led|conducted|presented|delivered|addressed|handled|guided)"
               r"\s+by\s+(%s)" % _NAME),
)
#: Qualifications and job titles that follow a person's name in a caption.
_TRAILING_ROLE_RE = re.compile(
    r"[,\-\s]*\b(?:alumnus|alumna|alumni|founder|co-?founder|chairman|"
    r"chairperson|president|vice\s*chancellor|chancellor|principal|"
    r"registrar|dean|head|director|manager|officer|secretary|co-?ordinator|"
    r"coordinator|professor|lecturer|engineer|architect|scientist|researcher|"
    r"student|research\s+scholar|founder|ceo|cfo|cto|coo|md|cfo|"
    r"[bp]\.?e\.?\s*\(?civil\)?|[bm]\.?tech|[bm]\.?sc|[bm]\.?a\b|mba|"
    r"[bm]\.?ph\.?d|b\.?ph\.?d|[bm]\.?e\b|civil|mechanical|electrical|"
    r"electronics|production|geotechnical|molecular|science|technology|"
    r"engineering|management|commerce|arts|services|systems|technologies)"
    r"(?:\s*\(?[A-Za-z.& ]{0,40}\)?)?$", re.I)


def _lines(text, limit=_SCAN_LINES):
    """The first few meaningful lines of a caption.

    Labelled fields ("Chief Guest: ...", "MoU Signed with ...") are searched
    line by line so a value can never swallow the rest of the caption.
    """
    out = []
    for line in (text or "").splitlines():
        clean = _strip_decoration(line)
        if clean:
            out.append(clean)
        if len(out) >= limit:
            break
    if not out and (text or "").strip():
        out = [_strip_decoration(" ".join((text or "").split()))]
    return out


def _strip_trailing_role(value):
    previous = None
    while previous != value:
        previous = value
        value = _ORG_TAIL_RE.sub("", value)
        value = _TRAILING_ROLE_RE.sub("", value).strip(" ,-–—")
    return value


#: A value that starts with a job title is a description, not a person's name.
_ROLE_ONLY_RE = re.compile(
    r"^(?:the\s+)?(?:chief|keynote|main|invited|guest|resource|technical|"
    r"presiding|honou?rary)\s+(?:guest|speaker)|"
    r"^(?:the\s+)?(?:guest|speaker|president|chairman|chairperson|head|"
    r"director|professor|principal|registrar|co-?ordinator|manager|officer|"
    r"secretary|alumnus|alumna|student|faculty|leader|organiser|organizer|"
    r"convener|coordinator)\b", re.I)


def _first_match(text, patterns, prefer_label=True):
    if not text:
        return ""
    labelled = patterns if prefer_label else patterns[::-1]
    for line in _lines(text):
        for pattern in labelled:
            match = pattern.search(line)
            if not match:
                continue
            value = _tidy(match.group(1))
            value = _ORG_STOP.sub("", value).strip()
            value = _strip_trailing_role(value)
            if _is_generic_actor(value) or _ROLE_ONLY_RE.search(value):
                continue
            if len(_content_words(value)) >= 2:
                return value
    return ""


def chief_guest(text):
    """The chief guest of a conference / orientation, or "" when absent."""
    clean = _strip_decoration(text)
    return _first_match(clean, _CHIEF_GUEST_RES)


def speaker(text):
    """The speaker / resource person of a session, or "" when absent."""
    clean = _strip_decoration(text)
    return _first_match(clean, _SPEAKER_RES)


def stakeholder_name(text, stakeholders=None, role_res=None):
    """A named person attached to a row (research guide, alumnus, ...)."""
    for item in stakeholders or []:
        value = ""
        if isinstance(item, dict):
            if item.get("kind") == "person" and item.get("value"):
                value = item["value"]
        elif isinstance(item, str):
            value = item
        if value and not _is_generic_actor(value):
            return _tidy(value)
    clean = _strip_decoration(text)
    for pattern in role_res or ():
        match = pattern.search(clean)
        if match:
            value = _ORG_STOP.sub("", _tidy(match.group(1))).strip()
            if len(_content_words(value)) >= 2 and not _is_generic_actor(value):
                return value
    return ""


_RESEARCH_GUIDE_RES = (
    re.compile(r"(?:under\s+the\s+guidance\s+of|guided\s+by|mentor(?:ed)?\s+by|"
               r"supervis(?:ed|or)\s+by)\s+(%s)" % _NAME),
    re.compile(r"principal\s+investigator\s*[:\-–—]?\s*(%s)" % _NAME),
)
_ALUMNI_NAME_RES = (
    # Only an explicit roll-call counts: "our alumni, namely X, Y", "alumni
    # Mr. X".  A bare "alumni" followed by any capitalised word is not a name.
    re.compile(r"(?:our\s+)?(?:alumni|alumnus|alumini)\s*(?:meeting\s+)?"
               r"(?:namely|including|name(?:d|s)?)\s*[:\-–—]?\s*(%s)" % _NAME, re.I),
    re.compile(r"(?:our\s+)?(?:alumni|alumnus|alumini)\s+(?:—|-|–|:)\s*"
               r"((?:Dr|Mr|Mrs|Ms|Prof)\.?\s+[^,.\n]{2,60})", re.I),
)


# ---------------------------------------------------------------------------
# Duration / location / purpose / MOU
# ---------------------------------------------------------------------------

_NUMBER_WORD = (r"one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
                r"single|half|full|multi|\d+(?:\.\d+)?")
_DURATION_RES = (
    re.compile(r"\b(%s)[\s\-]*(day|days|week|weeks|hour|hours|hrs|month|months|"
               r"semester|semesters|session|sessions|term)\b" % _NUMBER_WORD, re.I),
    re.compile(r"\b(day|days|week|weeks|hour|hours|hrs|month|months|"
               r"semester|semesters)\s+(long|duration)?\b", re.I),
    re.compile(r"\b(a\s+)?(one|three|five|six|seven)-?\s*(day|week)\b", re.I),
)
_LOCATION_RES = (
    re.compile(r"(?:venue|location|venue\s*&\s*location)\s*[:\-–—]\s*([^.;\n]{3,90})", re.I),
    re.compile(r"(?:held|conducted|organis(?:ed|ing)|organiz(?:ed|ing))\s+at\s+"
               r"(?:the\s+)?([^.;\n]{3,90})", re.I),
    re.compile(r"\bat\s+([A-Z][\w&.\-]*(?:\s+[\w&.\-]+){0,6}?"
               r"\s(?:Hall|Auditorium|Lab|Library|Block|Building|Campus|"
               r"Ground\s+Floor|Conference\s+Room|Classroom|Theatre))\b"),
    re.compile(r"([A-Z][\w&.\-]*(?:\s+[\w&.\-]+){0,4}\s+"
               r"(?:Auditorium|Seminar\s+Hall|Conference\s+Hall|Lab))\b"),
)
_PURPOSE_RES = (
    re.compile(r"(?:purposes?|objectives?|aims?|goal)\s*(?:of\s+(?:the\s+\w+\s+)?)?"
               r"[:\-–—]\s*([^.;\n]{3,140})", re.I),
    re.compile(r"(?:with\s+(?:the\s+)?(?:sole\s+)?(?:aim|objective|purpose)\s+"
               r"(?:of|to)?|in\s+order\s+to|so\s+as\s+to)\s+([^.;\n]{3,140})", re.I),
    re.compile(r"[^.;\n]{0,60}?\bto\s+(facilitate|strengthen|enhance|promote|"
               r"support|foster|provide|develop|bridge|encourage|advance|"
               r"improve|establish|formalize|formalise)\s+([^.;\n]{3,140})", re.I),
)
_MOU_RES = (
    re.compile(r"mou\s*(?:was\s+|is\s+)?(?:signed|executed|entered)\s*"
               r"(?:between|by|with)\s+([^.;\n]{3,120})", re.I),
    re.compile(r"(?:signed|executed|entered)\s+(?:an?\s+)?(?:mou|mo\.|m\.o\.u)"
               r"\s*(?:between|by|with)\s+([^.;\n]{3,120})", re.I),
    re.compile(r"(?:mou|mo\.|m\.o\.u)\s*[:\-–—]\s*([^.;\n]{3,120})"),
    re.compile(r"(?:tie[-\s]?up|collaboration|partnership|agreement)\s+"
               r"(?:with|and|between)\s+([^.;\n]{3,120})", re.I),
)
_ORG_CLEAN_RE = re.compile(r"^(?:an?|the)\s+", re.I)
_ORG_TAIL_RE = re.compile(
    r"\s*,?\s*(?:at|of|from)\s+[A-Z][\w.&]*(?:\s+[A-Z][\w.&]*)*\s*"
    r"(?:University|College|Institute|School|Academy|Technologies|Technology|"
    r"Solutions|Systems|Ltd|Limited|Pvt|Private)\b.*$")
_PURPOSE_TAIL_RE = re.compile(
    r"\s+(?:which\s+aims?|aiming|aims|in\s+order|so\s+as|to\s+(?:benefit|"
    r"support|help)\b).*$", re.I)
#: Labels and collective nouns that name no individual person.
_GENERIC_ACTOR_RE = re.compile(
    r"^\s*(?:the\s+)?(?:alumni|alumnus|alumini|students?|graduates?|batch|"
    r"guest|speaker|faculty|staff|participants?|attendees?|team|members?|"
    r"organizers?|organisers?|co-?ordinators?|everyone|all|management|"
    r"department|dept|college|company|company limited|ltd|pvt|technologies|"
    r"solutions|systems|services|industries|industry|academy|institute|"
    r"university|council|committee|forum|society|association|cell|club|"
    r"community(?:\s+and\s+society)?|public|government(?:\s+and\s+agencies)?|"
    r"entrepreneurs|startups?|companies|corporate|professionals?|"
    r"researchers?|scholars?|interns?)\b\s*$", re.I)
#: A trailing clause that is a call to action, not part of the organisation's
#: name ("..., invites", ", was signed", ", today").
_CTA_TAIL_RE = re.compile(
    r"\s*[,;]?\s*\b(?:invites?|inviting|welcomes?|welcoming|congratulates?|"
    r"announces?|announced|thanks?|thank\s+you|begins?|began|ends?|concludes?|"
    r"concluded|held|signed|executed|entered|is\s+signed|was\s+signed|"
    r"were\s+signed|were\s+exchanged|took\s+place|recently|on\s+\d{1,2}\s+\w+|"
    r"today|together)\b.*$", re.I)
#: A closing adverb after the organisation name ("..., warmly").
_ADVERB_TAIL_RE = re.compile(
    r"\s*,\s*(?:warmly|cordially|gratefully|proudly|pleasantly|happily|"
    r"sincerely|heartily|resoundingly|special|heartfelt)\b.*$", re.I)
#: A purpose that stops on a dangling conjunction or comma.
_DANGLING_TAIL_RE = re.compile(
    r"\s*[,;:]?\s*\b(?:and|or|with|for|to|in|of|the|a|an|as|by|on|that|which|"
    r"its|their)\b\s*$", re.I)


def _is_generic_actor(value):
    """True when the phrase names an audience or an organisation, not a person."""
    value = (value or "").strip()
    if not value:
        return True
    return bool(_GENERIC_ACTOR_RE.match(value))


def _search_lines(text, patterns, post=None):
    """Run ``patterns`` line by line and post-process the first usable match."""
    for line in _lines(text, limit=12):
        for pattern in patterns:
            match = pattern.search(line)
            if not match:
                continue
            value = _tidy(match.group(1), limit=120)
            value = _PURPOSE_TAIL_RE.sub("", value)
            value = _ORG_TAIL_RE.sub("", value)
            value = _CTA_TAIL_RE.sub("", value)
            value = _ADVERB_TAIL_RE.sub("", value)
            value = _ORG_STOP.sub("", value)
            value = _ORG_CLEAN_RE.sub("", value).strip()
            value = _DANGLING_TAIL_RE.sub("", value).strip(" ,;:.")
            if post is not None:
                value = post(value)
            if len(_content_words(value)) >= 2:
                return value
    return ""


def duration(text):
    """An explicit duration stated by the post (e.g. "2 Days"), else ""."""
    clean = _strip_decoration(text)
    if not clean:
        return ""
    for pattern in _DURATION_RES:
        match = pattern.search(clean)
        if match:
            parts = [p for p in match.groups() if p]
            value = _tidy(" ".join(parts), limit=40)
            if not value or value.lower() in ("day", "days", "week", "weeks"):
                continue
            if re.fullmatch(r"(day|days|week|weeks|hour|hours|hrs|month|months|"
                            r"semester|semesters|session|sessions|term|long|duration)",
                            value, re.I):
                continue
            return value
    return ""


def location(text):
    """An explicit venue/location stated by the post, else ""."""
    return _search_lines(text, _LOCATION_RES)


def mou_with(text):
    """The counterparty of an MoU / partnership, else ""."""
    return _search_lines(text, _MOU_RES)


def purpose(text):
    """The stated purpose/objective of an MoU or event, else ""."""
    return _search_lines(text, _PURPOSE_RES[:2], post=_trim_leading_cue)


def _trim_leading_cue(value):
    """``purposes: X`` -> ``X`` (drop the verb a pattern may have captured)."""
    return re.sub(r"^(?:is|are|was|were|of|to)\s+", "", value).strip()


# ---------------------------------------------------------------------------
# Dates, departments, batches
# ---------------------------------------------------------------------------

_DMY = r"(?:\d{1,2}\s+(?:January|February|March|April|May|June|July|August|"
_DMY += r"September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|"
_DMY += r"Sep|Oct|Nov|Dec)[a-z]*\.?,?\s+\d{4}|"
_DMY += r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|"
_DMY += r"(?:January|February|March|April|May|June|July|August|September|"
_DMY += r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
_DMY += r"[a-z]*\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})"
_RANGE_RE = re.compile(r"(?:from\s+)?(%s)\s*(?:-|–|—|to|till|until|and)\s*(%s)"
                       % (_DMY, _DMY), re.I)
_BATCH_RE = re.compile(
    r"(?:batch\s*(?:of\s*)?|batch\s*-?\s*|['’]\s*)((?:19|20)\d{2})\b", re.I)
#: "1997 Batch", "1981-1985 Batch" -- the year(s) the batch passed.
_BATCH_SUFFIX_RE = re.compile(
    r"((?:19|20)\d{2})\s*(?:[-–]\s*(?:19|20)?\d{2})?\s*batch\b", re.I)
_BATCH_SHORT_RE = re.compile(r"batch\s*['’]\s*(\d{2})\b", re.I)
_GENERIC_BATCH_TAIL_RE = re.compile(r"batch\s*(?:of\s*)?['’]?\s*\d{2}\b", re.I)
#: The department an alumnus batch belongs to, when the post names no canonical
#: department: "TCE CSE 1997 Batch" -> CSE.  Required to be an ALL-CAPS acronym
#: next to the batch, so "Alumni Meet 2026" can never become a batch.
_ACRONYM_BATCH_RE = re.compile(r"\b([A-Z]{2,5})\s*(?:19|20)\d{2}\s*batch\b")
_DEPT_STOP = frozenset(("and", "of", "the", "for", "in", "at", "dept",
                        "department", "s"))


def date_range(text, single_date=None):
    """A From-To period stated by the post; falls back to its single date."""
    clean = _strip_decoration(text)
    match = _RANGE_RE.search(clean) if clean else None
    if match:
        left, right = _tidy(match.group(1), 40), _tidy(match.group(2), 40)
        if left and right:
            return "%s – %s" % (left, right)
    if single_date:
        return _tidy(single_date, limit=40)
    if clean:
        found = re.search(_DMY, clean)
        if found:
            return _tidy(found.group(0), limit=40)
    return ""


def batch_year(text):
    """The passing batch stated by the post ("2016 Batch"), else "".

    Both orders are read, because posts write "batch of 2016" and "1997 Batch"
    alike.  The event year is never a batch: the word "batch" must be there.
    """
    clean = _strip_decoration(text)
    if not clean:
        return ""
    match = _BATCH_RE.search(clean) or _BATCH_SUFFIX_RE.search(clean)
    if match:
        return match.group(1)
    return ""


_PAREN_ACRONYM_RE = re.compile(r"\(([A-Z][A-Za-z&.]{1,9})\)")


def department_acronym(name):
    """Canonical department name -> the acronym used in report columns.

    ``Computer Applications (MCA)`` keeps the acronym the catalog already states
    (``MCA``) instead of deriving a different one from the same words.
    """
    name = (name or "").strip()
    if not name:
        return ""
    stated = _PAREN_ACRONYM_RE.search(name)
    if stated:
        return stated.group(1).upper()
    words = [w for w in re.split(r"[^A-Za-z0-9]+", name) if w]
    if not words:
        return ""
    initials = "".join(w[0] for w in words
                       if w.lower() not in _DEPT_STOP and w.lower() != "s")
    if len(initials) >= 2:
        return initials.upper()
    single = words[0].upper()
    return single if len(single) <= 8 else single[:8]


def alumni_department_label(departments, text):
    """``CSE (2016 Batch)`` when a batch is stated, otherwise ``CSE``.

    The department comes from the row's canonical departments when it has any.
    Many alumni posts name no department at all, so the fallback is the acronym
    the post puts next to the batch ("TCE CSE 1997 Batch").  Nothing is invented:
    with neither a department nor a batch the column stays blank.
    """
    names = []
    for item in departments or []:
        value = item.get("name") if isinstance(item, dict) else item
        value = (value or "").strip()
        if value and value.lower() != "general":
            names.append(value)
    batch = batch_year(text)
    if not names and text:
        stated = _ACRONYM_BATCH_RE.search(_strip_decoration(text))
        if stated:
            names = [stated.group(1)]
    if not names:
        return ""
    out = []
    for name in names:
        label = department_acronym(name) or name
        if batch:
            label = "%s (%s Batch)" % (label, batch)
        out.append(label)
    return " and ".join(out)


# ---------------------------------------------------------------------------
# Descriptions
# ---------------------------------------------------------------------------


def short_description(text, words=50, title=None):
    """A factual, caption-derived description of about ``words`` words.

    The description is drawn from the post itself (never composed from a
    template), so it can only restate what the source says.  The headline is
    dropped so the description adds information instead of repeating the title,
    and a leading "we are delighted to share..." announcement is skipped in
    favour of the sentence that states what actually happened.
    """
    clean = _strip_decoration(text)
    if not clean:
        return ""
    body = _norm_ws(clean)
    if title:
        headline = _tidy(_strip_decoration(title), limit=200)
        if headline:
            first_line = _first_line_with(body, headline)
            if first_line and len(_content_words(first_line)) >= 3:
                body = first_line
    body = _first_factual_sentence(body)
    tokens = body.split()
    if not tokens:
        return ""
    if len(tokens) <= words:
        return _tidy(body, limit=len(body) + 40)
    head = " ".join(tokens[:words])
    last = head.rfind(".")
    if last > words // 2:
        return _tidy(head[:last + 1], limit=len(head) + 40)
    return _tidy(head.rstrip(",;: ") + "...", limit=len(head) + 40)


#: "We are delighted to share that X" states nothing X does not; the factual
#: sentence is the one after it.  Only used while a factual sentence remains.
_PROMO_SENTENCE_RE = re.compile(
    r"^(?:we|i|the\s+\w+)\s+(?:are|is|was|were|feel|felt|remain|remains)?\s*"
    r"[^.!?]{0,40}?\b(?:delighted|pleased|proud|happy|excited|honoured|"
    r"honored|thrilled|glad)\b", re.I)


def _first_factual_sentence(body):
    """Skip leading promotional announcements; keep everything else."""
    sentences = _SENTENCE_SPLIT_RE.split(body)
    if len(sentences) < 2:
        return body
    start = 0
    while start < len(sentences) - 1 and _PROMO_SENTENCE_RE.match(sentences[start]):
        start += 1
    if start:
        rest = " ".join(sentences[start:]).strip()
        if len(_content_words(rest)) >= 3:
            return rest
    return body


def _first_line_with(body, headline):
    """``body`` from the first line after the headline, else ``body``."""
    tokens = body.split()
    n = len(headline.split())
    if not n or len(tokens) <= n:
        return body
    if [t.strip(".,:;!?'\"") for t in tokens[:n]] != \
            [t.strip(".,:;!?'\"") for t in headline.split()]:
        return body
    rest = tokens[n:]
    if len(_content_words(" ".join(rest))) < 3:
        return body
    return " ".join(rest)


# ---------------------------------------------------------------------------
# Per-category field requirements
# ---------------------------------------------------------------------------

REPORT_FIELD_SPECS = {
    "ALUMNI": ("alumni_name", "alumni_department", "topic_theme"),
    "CONFERENCE": ("chief_guest",),
    "GUEST_LECTURE": ("speaker",),
    "HACKATHON": ("event_description",),
    "INDUSTRY": ("mou_with", "purpose"),
    "INTERNSHIP": ("duration", "date_range"),
    "NCC": ("event_description",),
    "NSS": ("event_description",),
    "ORIENTATION": ("chief_guest",),
    "OUTREACH": ("location",),
    "RESEARCH": ("stakeholder_name",),
    "SEMINAR": ("speaker", "event_description"),
    "SPORTS": ("event_description",),
    "SYMPOSIUM": ("event_description",),
    "WORKSHOP": ("duration",),
}

_TOPIC_RES = (
    re.compile(r"(?:topic|theme|on\s+the\s+topics?)\s*(?:of\s+\w+\s+)?"
               r"[:\-–—]\s*[\"“']?([^\"”'.;\n]{3,90})", re.I),
    re.compile(r"\bon\s+the\s+(?:topic|theme)\s+[\"“']([^\"”'\n]{3,90})[\"”']", re.I),
    re.compile(r"\b(?:topic|theme)\s+(?:was|is)\s+[\"“']?([^\"”'.;\n]{3,90})", re.I),
    re.compile(r"\bdeliberations?\s+on\s+([^\"”'.;\n]{3,90})", re.I),
    re.compile(r"[\"“']([^\"”'\n]{4,80})[\"”']\s*(?:theme|topic)", re.I),
)


def topic_theme(text):
    """The topic/theme a session was held on, else ""."""
    return _search_lines(text, _TOPIC_RES)


def _derive(field, row, text):
    if field == "chief_guest":
        return chief_guest(text)
    if field == "speaker":
        return speaker(text)
    if field == "duration":
        return duration(text)
    if field == "location":
        return location(text)
    if field == "mou_with":
        return mou_with(text)
    if field == "purpose":
        return purpose(text)
    if field == "topic_theme":
        return topic_theme(text)
    if field == "date_range":
        return date_range(text, row.get("activity_date"))
    if field == "event_description":
        # The headline to drop is the CLEANED title, so the description starts
        # at the first sentence that is not the title.
        return short_description(text, title=clean_title(text))
    if field == "alumni_name":
        return stakeholder_name(text, row.get("stakeholders"), _ALUMNI_NAME_RES)
    if field == "stakeholder_name":
        return stakeholder_name(text, row.get("stakeholders"), _RESEARCH_GUIDE_RES)
    if field == "alumni_department":
        return alumni_department_label(row.get("departments"), text)
    return ""


def fields_for(category_code, row=None, text=None):
    """Derived report fields for one row of ``category_code``.

    Returns an ``OrderedDict`` containing only the keys that category actually
    shows, so untouched categories cost nothing and their exports are byte
    identical to before.
    """
    needed = REPORT_FIELD_SPECS.get(category_code or "", ())
    if not needed:
        return OrderedDict()
    row = row or {}
    text = text if text is not None else (row.get("description") or "")
    out = OrderedDict()
    for field in needed:
        out[field] = _derive(field, row, text)
    return out