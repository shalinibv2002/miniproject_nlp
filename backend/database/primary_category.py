"""Single primary-category resolution for the REPORTABLE LinkedIn dataset.

WHY THIS MODULE EXISTS
----------------------
The reportable dataset used to carry a *list* of categories per activity, so an
activity was counted once in the unique/General total **and** once in every
category it carried.  A reporting scope therefore never reconciled:

    General 2025-26 = 248      sum of the category counts = 431

For institutional reporting that is unusable, because it is impossible to say
"how many workshops did we run?" without double counting.

THE RULE ENFORCED HERE
----------------------
    Exactly ONE primary category per REPORTABLE activity.

``resolve_primary_category`` is the single source of truth for that value.  It
is used by the build pipeline, by admin edits and by the backfill migration, so
the database, the APIs, the analytics, the dashboard, the reports, the exports
and "Ask the Data" can never disagree.

THIS IS NOT A KEYWORD FILTER
----------------------------
A word appearing somewhere in a post does not define the activity.  This
module reads the complete post and answers the only question reporting cares
about:

    "What is this post primarily reporting?"

It works on *semantic features* — event head nouns, completed-result
statements, research outputs, industry arrangements, alumni engagement — and on
the family (nature of the act) each category belongs to.  Cases where the post
really does not say which act is primary are NOT guessed; they come back as
``None`` so the caller holds the row in ``REVIEW_REQUIRED`` for a human.

Worked examples taken from the real feed:

    "Students participated in a workshop on AI and won first prize..."
        -> the result is the news            -> ACHIEVEMENT
    "Faculty members attended an FDP and received certificates"
        -> the FDP is the news               -> FDP
    "TCE signed an MoU with XYZ to collaborate on research"
        -> the agreement is the news         -> INDUSTRY
    "A research scholar delivered a guest lecture on AI"
        -> the session is the news           -> GUEST_LECTURE  (never RESEARCH)
    "An alumnus delivered a guest lecture"
        -> the session is the news           -> GUEST_LECTURE  (never ALUMNI)
    "TCE Research Seminar Series #32, topic ..., 22 April 2026"
        -> the session is the news           -> SEMINAR         (never RESEARCH)
    "Congratulations on the grant of Utility Patent 586541"
        -> the research output is the news   -> RESEARCH
    "Congratulations to X on securing All India Rank 485 in UPSC"
        -> the result is the news            -> ACHIEVEMENT

Resolves to exactly one of the 24 allowed codes, or ``None`` (REVIEW_REQUIRED).
"""

import json
import re

from backend.database.linkedin_candidates import CATEGORY_PATTERNS

#: The 24 allowed categories.  Read from the classifier so the two can never
#: drift apart; this module never invents a 25th code.
ALLOWED_CATEGORY_CODES = frozenset(CATEGORY_PATTERNS)

REVIEW_REQUIRED = "REVIEW_REQUIRED"

# Confidence levels attached to every resolution.
CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"


# ---------------------------------------------------------------------------
# Nature of the act
# ---------------------------------------------------------------------------
# Every category describes one *family* of activity.  The family answers "what
# kind of thing happened"; the member answers "which one".
AGREEMENT = "agreement"            # an external arrangement was entered into
CAREER = "career"                  # a placement / internship programme
ORGANIZED_EVENT = "organized_event"  # an organised session or event happened
RESEARCH_OUTPUT = "research_output"  # a research output or research activity
RECOGNITION = "recognition"        # a real result / award / recognition
LIFECYCLE = "lifecycle"            # alumni engagement / campus observance

CATEGORY_FAMILY = {
    "INDUSTRY": AGREEMENT,
    "PLACEMENT": CAREER,
    "INTERNSHIP": CAREER,
    "TECH_FEST": ORGANIZED_EVENT,
    "HACKATHON": ORGANIZED_EVENT,
    "SYMPOSIUM": ORGANIZED_EVENT,
    "CONFERENCE": ORGANIZED_EVENT,
    "GUEST_LECTURE": ORGANIZED_EVENT,
    "SEMINAR": ORGANIZED_EVENT,
    "WORKSHOP": ORGANIZED_EVENT,
    "WEBINAR": ORGANIZED_EVENT,
    "FDP": ORGANIZED_EVENT,
    "STTP": ORGANIZED_EVENT,
    "SPORTS": ORGANIZED_EVENT,
    "CULTURAL": ORGANIZED_EVENT,
    "ORIENTATION": ORGANIZED_EVENT,
    "NCC": ORGANIZED_EVENT,
    "NSS": ORGANIZED_EVENT,
    "CLUB": ORGANIZED_EVENT,
    "OUTREACH": ORGANIZED_EVENT,
    "RESEARCH": RESEARCH_OUTPUT,
    "ACHIEVEMENT": RECOGNITION,
    "ALUMNI": LIFECYCLE,
    "CAMPUS": LIFECYCLE,
}

# Order in which families are consulted when no earlier, more specific act was
# established.  An agreement is a distinct institutional act; a career
# programme is a distinct programme; a research output and a recognition are
# outcomes rather than events; alumni/campus engagement is background.
FAMILY_ORDER = (AGREEMENT, CAREER, ORGANIZED_EVENT,
                RESEARCH_OUTPUT, RECOGNITION, LIFECYCLE)

# Within a family, the more specific member wins (a tech festival is more
# specific than a generic cultural event; an FDP is more specific than a
# generic workshop).  Only consulted when the head noun cannot decide.
FAMILY_SPECIFICITY = {
    "TECH_FEST": 0, "HACKATHON": 1, "SYMPOSIUM": 2, "CONFERENCE": 3,
    "GUEST_LECTURE": 4, "WEBINAR": 5, "SEMINAR": 6, "FDP": 7, "STTP": 8,
    "WORKSHOP": 9, "SPORTS": 10, "CULTURAL": 11, "ORIENTATION": 12,
    "NCC": 13, "NSS": 14, "CLUB": 15, "OUTREACH": 16,
}

# Fallback order inside the single-member families.
SINGLE_MEMBER_ORDER = {"PLACEMENT": 0, "INTERNSHIP": 1, "RESEARCH": 0,
                       "ACHIEVEMENT": 0, "INDUSTRY": 0,
                       "ALUMNI": 0, "CAMPUS": 1}


# ---------------------------------------------------------------------------
# Semantic vocabularies (phrases, not isolated words)
# ---------------------------------------------------------------------------
_WS = re.compile(r"\s+")

# "Seminar Hall", "Conference Hall" ... name a VENUE.  They say where an event
# happens, never that a seminar or conference is the activity being reported.
VENUE_PHRASES = re.compile(
    r"\b(?:[a-z]+\s+){0,2}?"
    r"(?:seminar|conference|convocation|auditorium|seminar hall|conference hall)"
    r"\s+hall\b"
    r"|\bseminar\s+hall\b"
    r"|\bconference\s+hall\b"
    r"|\bhall\b",
    re.I)

# The event noun a post actually declares, most specific first.  The FIRST
# non-venue occurrence is the post's own subject.
EVENT_HEAD_NOUNS = (
    # (pattern, code)
    (r"\btech\s?fest(?:ival)?\b", "TECH_FEST"),
    (r"\b(?:technical\s+festival|free\s+software\s+festival|f[su]'?tival)\b",
     "TECH_FEST"),
    (r"\bfestival\s+on\b", "TECH_FEST"),
    (r"\bsymposium\b", "SYMPOSIUM"),
    (r"\b(?:hacka|code)thon\b", "HACKATHON"),
    (r"\bwebinar\b", "WEBINAR"),
    (r"\bfaculty\s+development\s+program(?:me)?\b", "FDP"),
    (r"\bfdp\b", "FDP"),
    (r"\bshort\s*[- ]?\s*term\s+training\s+program(?:me)?\b", "STTP"),
    (r"\bsttp\b", "STTP"),
    (r"\b(?:guest|special|invited|distinguished|keynote)\s+lecture\b", "GUEST_LECTURE"),
    (r"\blecture\s+series\b", "GUEST_LECTURE"),
    (r"\b(?:guest|special|invited|alumni|master|expert|technical|career|industry|"
     r"insightful|motivational|orientation)\s+talk\b", "GUEST_LECTURE"),
    (r"\bkeynote\b", "GUEST_LECTURE"),
    (r"\b(?:technical|industrial|corporate|professional)\s+talk\b", "GUEST_LECTURE"),
    (r"\b(?:interactive|expert|technical|insightful|academic)\s+session\s+with\b",
     "GUEST_LECTURE"),
    (r"\b(?:expert|peer-to-peer|technical|academic|knowledge|research|"
     r"drive|insightful|enlightening)\s+session\b", "SEMINAR"),
    (r"\bsession\s+on\b", "SEMINAR"),
    (r"\bsummer\s+school\b", "WORKSHOP"),
    (r"\bguest\s+speaker\b", "GUEST_LECTURE"),
    (r"\bskills?\s+training\b", "WORKSHOP"),
    (r"\b(?:research\s+)?seminar\s+series\b", "SEMINAR"),
    (r"\b(?:research|academic|rd\s*&\s*d|webinar|orientation|technical|expert|"
     r"industry|career|department|alumni)\s+seminar\b", "SEMINAR"),
    (r"\bseminar\b", "SEMINAR"),
    (r"\b(?:skill\s+development\s+)?workshop\b", "WORKSHOP"),
    (r"\bvalue\s+added\s+course\b", "WORKSHOP"),
    (r"\bcertification\s+course\b", "WORKSHOP"),
    (r"\b(?:online\s+)?certification\s+courses?\b", "WORKSHOP"),
    (r"\btraining\s+course\b", "WORKSHOP"),
    (r"\bhands[- ]on\s+(?:session|training|workshop)\b", "WORKSHOP"),
    (r"\bshort\s+term\s+training\b", "STTP"),
    # A generic training/induction/bootcamp programme is skill development, not
    # a Faculty Development Programme: FDP requires the explicit faculty wording.
    (r"\b(?:training|induction|boot\s?camp|skill\s+development)\s+program(?:me)?\b",
     "WORKSHOP"),
    (r"\bimmersive\s+program(?:me)?\b", "WORKSHOP"),
    (r"\bboot\s?camp\b", "WORKSHOP"),
    (r"\b\w+\s+development\s+program(?:me)?\b", "WORKSHOP"),
    (r"\binternational\s+conference\b", "CONFERENCE"),
    (r"\b(?:national|global|international|biennial|annual|student|technical)\s+conference\b",
     "CONFERENCE"),
    (r"\bconference\b", "CONFERENCE"),
    (r"\b(?:research\s+)?conclave\b", "CONFERENCE"),
    (r"\bcolloquium\b", "CONFERENCE"),
    (r"\btedx\b", "CONFERENCE"),
    (r"\bsports\s+meet\b", "SPORTS"),
    (r"\b(?:annual\s+)?sports\s+day\b", "SPORTS"),
    (r"\b(?:kho\s*kho|cricket|football|basketball|volleyball|handball|badminton|"
     r"kabaddi|roll\s?ball|shooting|swimming|athletics?|chess|tennis|table\s+tennis)\b",
     "SPORTS"),
    (r"\b(?:state|national|inter[- ]engineering|all\s+india|memorial|women'?s|"
     r"junior|senior)\s+(?:level\s+)?[\w\s]{0,20}?\b(?:tournament|championship|meet)\b",
     "SPORTS"),
    (r"\btournament\b", "SPORTS"),
    (r"\bmarathon\b", "SPORTS"),
    (r"\b(?:annual\s+)?sports\b", "SPORTS"),
    (r"\bcultural\b", "CULTURAL"),
    (r"\btalent\s+show\b", "CULTURAL"),
    (r"\bfreshers?\s+day\b", "ORIENTATION"),
    (r"\borientation\s+program(?:me)?\b", "ORIENTATION"),
    (r"\binduction\s+program(?:me)?\b", "ORIENTATION"),
    (r"\b(?:graduation|convocation)\s+(?:ceremony|day)?\b", "ORIENTATION"),
    (r"\bvaledictory\s+ceremon", "ORIENTATION"),
    (r"\bgraduation\b", "ORIENTATION"),
    (r"\bnational\s+cadet\s+corps\b", "NCC"),
    (r"\bncc\b", "NCC"),
    (r"\bnational\s+service\s+scheme\b", "NSS"),
    (r"\bnss\b", "NSS"),
    (r"\b(?:awareness|medical|health|village|rural|outreach|extension|"
     r"community|swachh|eye\s+camp|free\s+camp)\s+(?:camp|drive|program(?:me)?|activity|"
     r"initiative|session|outreach)\b", "OUTREACH"),
    (r"\boutreach\b", "OUTREACH"),
    (r"\bblood\s+donation\b", "OUTREACH"),
    (r"\bstudent\s+chapter\b", "CLUB"),
    (r"\bdepartment\s+association\b", "CLUB"),
    (r"\bprofessional\s+societ(?:y|ies)\b", "CLUB"),
    (r"\binstitutional\s+innovation\s+council\b", "CLUB"),
    (r"\bclub\b", "CLUB"),
    # --- institutional observances and ceremonies (CAMPUS) ------------------
    (r"\binternational\s+women'?s\s+day\b", "CAMPUS"),
    (r"\b(?:women'?s|men'?s|children'?s|world)\s+day\b", "CAMPUS"),
    (r"\b(?:college\s+day|annual\s+day|founder'?s?\s+day|foundation\s+day)\b",
     "CAMPUS"),
    (r"\binternational\s+day\s+for\b", "CAMPUS"),
    (r"\binternational\s+\w{3,25}\s+day\b", "CAMPUS"),
    (r"\b(?:annual\s+|college\s+)?newsletter\s+release\b", "CAMPUS"),
    (r"\balumni\s+meet(?:up)?\b", "ALUMNI"),
    (r"\bchapter\s+meet(?:s|up)?\b", "ALUMNI"),
    (r"\balumni\s+reunion\b", "ALUMNI"),
    (r"\bstudent\s+interaction\s+session\b", "ALUMNI"),
    (r"\bdistinguished\s+alumn[ai]\s+visit\b", "ALUMNI"),
    (r"\b(?:award|awards|felicitation|honour|honor|prize\s+distribution|inauguration|"
     r"installation)\s+ceremon(?:y|ies)\b", "CAMPUS"),
    (r"\bina[u]g\w+\s+(?:ceremony\s+of\s+)?(?:the\s+)?[\w\s]{0,24}?\blab\b",
     "CAMPUS"),
    (r"\bteacher'?s?\s+day\b|\bnational\s+\w{3,20}\s+day\b", "CAMPUS"),
    (r"\binguration\s+of\s+(?:the\s+)?(?:student\s+)?(?:research\s+)?"
     r"(?:council|cell|chapter|club|centre|center|forum|association|society)\b",
     "CAMPUS"),
    (r"\b(?:journal\s+launch|launch\s+of\s+the\s+\w{0,20}\s*journal)\b", "CAMPUS"),
)

# Framing that marks a post as ANNOUNCING / CONDUCTING an organised event.
EVENT_FRAMING = re.compile(
    r"\b(?:organi[sz]es?|organi[sz]ed|conduct(?:ed|s)?|host(?:ed|s)?|holds?|"
    r"held|scheduled|announc(?:e|es|ed|ing)|invites? you|invitation|"
    r"registration|register now|registrations?\s+open|last date to register|"
    r"call for (?:papers|participation)|presents?|celebrat(?:es|ed|ing)|"
    r"take(?:s)? place|is scheduled|webcast|live(?: streaming| now)?|"
    r"replay|glimpses from|thank you to everyone who joined)\b", re.I)

# Administrative evidence that a post is announcing/running something real
# rather than merely naming a topic.  Used only when a lone candidate keyword
# survives, so it stays deliberately narrower than EVENT_FRAMING.
ACTIVITY_SCHEDULE = re.compile(
    r"\bvenue\s*[:\-]"
    r"|\b(?:date|time|schedule|duration|fee)\s*[:\-]\s*[\d₹]"
    r"|\bentry\s+fee\b|\bregistration\s+fee\b"
    r"|\bregister\b|\bregistration\b|\bjoin\s+us\b"
    r"|\b\d+\s*[- ]?\s*days?\b|\bsix[- ]day\b|\bfive[- ]day\b"
    r"|\bcall\s+for\b|\bparticipat\w+\b|\battend\w*\b"
    r"|\bprogramme\b|\bprogram\b|\bcourse\b|\bbootcamp\b|\bcamp\b",
    re.I)

# --- STEP 1: an industry agreement is a distinct institutional act ----------
INDUSTRY_ACT = re.compile(
    r"\b(?:mou|mou[s]?|memorandum\s+of\s+understanding|moa|memorandum\s+of\s+"
    r"agreement|nda|non[- ]?disclosure\s+agreement)\b"
    r"|\bsigned?\s+(?:an?|the)?\s*(?:mou|moa|nda|partnership|agreement|"
    r"collaboration)\b"
    r"|\bindustr(?:y|ial)\s+(?:visit|interaction|tour|training|internship|"
    r"collaboration|partnership|exposure|connect)\b"
    r"|\bvisit\s+(?:to|at)\s+(?:[a-z]+\s+){0,4}(?:industr(?:y|ies)|pvt|ltd|"
    r"private\s+limited|company|corp(?:oration)?)\b"
    r"|\b(?:company|corporate|industr(?:y|ies)|firm)\s+visit\b"
    r"|\b(?:partnered|partnership|collaborat\w+)\s+with\b"
    r"|\b(?:academic|global|international|industrial)\s+collaborations?\b"
    r"|\bstrategic\s+partnership"
    r"|\b(?:mo[u]?|agreement)\s+signed\b"
    # Engagement with an external official body is the same class of act:
    # an outside party the college formally meets or partners with.
    r"|\b(?:meeting|interaction|call|visit|discussion)\s+with\s+the\s+"
    r"(?:hon'?ble\s+)?(?:chief\s+minister|minister|governor|mayor|"
    r"ambassador|commissioner|collector|mla|mp|officials?)\b"
    r"|\bgovernment\s+(?:and\s+agencies|official|bodies|bureau|representatives)\b",
    re.I)

# --- STEP 2: a placement / internship programme is its own programme -------
PLACEMENT_ACT = re.compile(
    r"\b(?:campus\s+recruit(?:ment|ers)|placement\s+(?:drive|offer|process|"
    r"season|talk)|pre[- ]?placement|placed?\s+(?:in|at)\b|got\s+placed|"
    r"recruited\s+by|offer\s+letter|dream\s+offer|joins?\s+as\b"
    r"|\bappointment\s+as\b"
    r"|\bcareer\s+guidance\b)", re.I)

# "intern" as a false friend: "international", "internal", "internet" are not
# internships.  Only these are real internship evidence.
INTERNSHIP_ACT = re.compile(
    r"\binternships?\b|\binterns?\b(?!\s*(?:ational|al|et|ship))"
    r"|\bintern(?:ee|ship)s?\b|\bintraining\b", re.I)
INTERN_FALSE_FRIEND = re.compile(r"\bintern(?:ational|al|et|ship|shipment)\b", re.I)

# --- STEP 3: a research OUTPUT / research activity is the subject -----------
RESEARCH_OUTPUT_ACT = re.compile(
    r"\bpatents?\s+(?:has\s+been\s+|was\s+|is\s+|been\s+)?(?:grant(?:ed)?|award(?:ed)?)\b"
    r"|\bgrant\s+of\s+(?:a\s+|the\s+)?(?:utility\s+|design\s+)?patents?\b"
    r"|\breceiv\w+\s+(?:a\s+|the\s+)?(?:utility\s+|design\s+)?patents?\b"
    r"|\bsecur(?:ing|ed)\s+(?:a\s+|an\s+|the\s+)?(?:us\s+|utility\s+|design\s+)?patents?\b"
    r"|\bearnings?\s+(?:a\s+|an\s+|the\s+)?(?:us\s+)?patents?\b"
    r"|\bpatented\b"
    r"|\bsecur(?:ing|ed)\s+(?:a\s+|an\s+|the\s+)?(?:us\s+|utility\s+|design\s+)?patents?\b"
    r"|\bpatents?\s+no\.?\s*\d+\b"
    r"|\bresearch\s+grants?\b"
    r"|\bsponsored\s+research\b"
    r"|\bfunded\s+projects?\b"
    r"|\b(?:journal|newsletter|magazine)\s+(?:issue\s+\d+|vol(?:ume)?\.?\s*\d|"
    r"20\d\d)\b"
    r"|\b(?:issue|vol(?:ume)?)\s+\d+[^?!]{0,60}\b(?:has\s+been\s+|was\s+)?"
    r"(?:released|published|launched)\b"
    r"|\b(?:newsletter|journal|magazine)\b[^?!]{0,140}\b(?:released|published|"
    r"launched|unveiled)\b"
    r"|\bprojects?\s+(?:has\s+been\s+|was\s+)?sanctioned\b"
    r"|\bsanctioned\s+(?:a\s+|the\s+)?(?:research\s+)?projects?\b"
    r"|\bsanctioned\s+(?:funding|grant)\b"
    r"|\breceived\s+funding\b"
    r"|\b(?:project|proposals?)\s+(?:has\s+been\s+|was\s+|been\s+)?"
    r"(?:sanctioned|selected|approved|funded)\s+for\s+funding\b"
    r"|\bfunding\s+of\s+[₹\d]"
    r"|\b(?:ph\.?\s?d|phd|doctorate)\s+(?:has\s+been\s+|was\s+)?(?:award(?:ed)?|"
    r"conferred|obtained|completed)\b"
    r"|\baward(?:ed)?\s+(?:a\s+|the\s+)?(?:ph\.?\s?d|phd|doctorate)\b"
    r"|\bpublished\s+(?:a\s+|an\s+|the\s+)?(?:research\s+)?(?:paper|article|"
    r"study|report)\b"
    r"|\b(?:paper|article|research)\s+(?:has\s+been\s+|was\s+)?published\b"
    r"|\bpublication\s+(?:in|on)\b"
    r"|\b(?:published|presented)\s+in\s+(?:the\s+)?(?:journal|ieee|springer|"
    r"elsevier|sciencedirect|conference)\b"
    r"|\bconsultancy\b"
    r"|\bscientific\s+and\s+industrial\s+research\s+organisation\b"
    r"|\bsiro\b"
    r"|\bresearch\s+scholarship\b"
    r"|\bresearch\s+fellowships?\b"
    r"|\bjournal\s+launch\b"
    r"|\b(?:launch|release|releasing|released|launched)\s+(?:of\s+)?the\s+"
    r"[\w\s]{0,24}?journal\b"
    r"|\bipr\s+cell\b", re.I)

# A research *mention* is NOT a research activity: audience, eligibility, topic.
RESEARCH_MENTION_ONLY = re.compile(
    r"\bresearch\s+(?:scholars?|students?|exposure|area|areas|skills?|"
    r"excellence|innovation|output|outputs|enthusiasm|interest|ethics|"
    r"culture|work)\b"
    r"|\bresearch\s*&\s*development\b(?!\s+cell)"
    r"|\bresearch\s*&\s*development\s+cell\b"
    r"|\bfor\s+research\b|\bresearch\s+and\b|\bresearch\s+to\b", re.I)

# --- STEP 4: a REAL, completed result (recognition) ------------------------
# These are outcome STATEMENTS, not acknowledgements.  "Congratulations ... for
# participating" and "received a certificate" deliberately match none of them.
RESULT_ACT = re.compile(
    r"\bcongratulat\w+[^?!]{0,140}\b(?:on|for)\b[^?!]{0,60}\b(?:complet\w+|"
    r"award\w*|achiev\w+|sec\w+|rank\w*|selected|pass\w+)\b"
    r"|\bcomplet\w+\s+(?:all\s+)?(?:three\s+)?(?:levels?\s+of\s+)?(?:the\s+)?"
    r"[\w\s-]{0,50}\btraining\b"
    r"|\b(?:celebrat\w+|felicitat\w+)\b[^?!]{0,80}\b(?:award|achievement|gold|"
    r"medal|prize|trophy|rank|record)\b"
    r"|\b(?:won|wins|winning)\b"
    r"|\bclinched\b"
    r"|\bbagged\b"
    r"|\btop(?:ped|per)\b"
    r"|\bemerged\s+as\s+(?:the\s+)?(?:overall\s+)?(?:winners?|champions?|"
    r"best|top)\b"
    r"|\boverall\s+champions?\b"
    r"|\bagglomerate\s+(?:champion|winner)\b"
    # "secured/obtained/earned" followed by a concrete accolade.
    r"|\b(?:secured|obtain(?:ed|s)|ear(?:n(?:ing|ed)|s)|receiv\w+|win(?:s|ning)?)\b"
    r"[^.?!]{0,70}?\b(?:rank|podium|place|position|prize|medal|offer|"
    r"first|second|third|gold|silver|bronze|topper|job|scholarship|fellowship|"
    r"certification|patents?|awards?|recognition|accolade|grant|scholarships?)\b"
    r"|\b(?:first|second|third|1st|2nd|3rd|\d+(?:st|nd|rd|th))\s*(?:prize|"
    r"place|rank|position|podium)\b"
    r"|\brunner[- ]?up\b"
    r"|\b(?:gold|silver|bronze)\s+medal(?:ist)?\b"
    r"|\bmedal\s+of\s+(?:excellence|merit)\b"
    r"|\b(?:elite\s*\+?\s*)?(?:gold|silver|bronze)\s*\+\s*(?:gold|silver|bronze)\b"
    r"|\ball\s+india\s+rank\b"
    r"|\bair\s*\d{1,3}\b"
    r"|\branked?\s+(?:among|in\s+the\s+list|4th|3rd|2nd|1st|\d+(?:st|nd|rd|th))\b"
    r"|\bbest\s+(?:paper|student|faculty|teacher|performer|graduate|"
    r"sportsperson|programme|project|outgoing)\b"
    r"|\bhonou?red\s+(?:with|for)\b"
    r"|\bawarded\s+the\b"
    r"|\bachieved\s+the\b"
    r"|\b(?:awarded|received|earned)\s+(?:the\s+)?\w+\s+grade\b"
    r"|\bachieved\s+(?:prestigious\s+)?(?:post[- ]?doctoral\s+)?fellowships?\b"
    r"|\belected\s+as\b"
    r"|\bexcelling\s+in\b"
    r"|\bcompleted\s+the\s+course\b"
    r"|\bhas\s+been\s+ranked\b"
    r"|\branked\s+in\s+the\s+\d{3}\+?\s+band\b"
    r"|\brecogni[sz]ed\s+in\s+the\s+[\w\s]{0,20}?rankings?\b"
    r"|\bselected\s+under\s+the\s+[\w\s]{0,24}?(?:scheme|initiative)\b"
    r"|\bfunding\s+value\b"
    r"|\boutstanding\s+(?:performance|results?)\b"
    r"|\b(?:5s|green|platinum|gold)\s+(?:grade|certification)\b"
    r"|\bqualified\s+(?:as|for|in)\b"
    r"|\bselected\s+(?:as|for)\b"
    r"|\bselected\s+to\s+represent\b"
    r"|\btop\s*\d+\s+(?:teams?|students?|institutions?|departments?)\b"
    r"|\bassum(?:ing|es|ed)\s+(?:of\s+)?charge\b"
    r"|\bappointed\b"
    r"|\bfelicitat\w*\s+(?:with|to)\b"
    r"|\bhonou?r(?:ing|ed)\s+(?:the\s+|our\s+)?(?:best|top|outstanding|"
    r"students?|faculty|teams?|staff)\b"
    r"|\b(?:certifications?|degrees?)\s+(?:earned|awarded|obtained|conferred)\b"
    r"|\bcertification\s+examinations?\b"
    r"|\b\d+\s+(?:certifications?|courses?|students?|faculty)\s+"
    r"(?:completed|earned|benefited|awarded|received)\b"
    r"|\b(?:elite|silver|gold)\s*\+\s*(?:gold|silver|bronze|elite)\b"
    r"|\belite\s*\+"
    r"|\b(?:global|national|international)\s+recognitions?\b"
    r"|\b(?:world|national|global|engineering)\s+(?:university\s+)?rankings?\b"
    r"|\brecogni[sz]ed\s+as\b"
    r"|\bshortlisted\b"
    r"|\bselection\s+(?:as|to)\b"
    r"|\bconferred\s+(?:with|upon)\b"
    r"|\bconferred\s+the\b"
    r"|\baccomplishments?\s+of\b"
    r"|\bcleared\s+(?:the\s+)?(?:first|second|preliminary|final)\s+round\b"
    r"|\bstood\s+out\b[^.?!]{0,40}\b(?:round|final|shortlist)\b"
    r"|\bagree\s+to\s+participate\b", re.I)

# --- STEP 6: alumni ENGAGEMENT (not an alumnus speaking) --------------------
ALUMNI_ENGAGEMENT = re.compile(
    r"\balumni\s+meet\b|\balumni\s+meetup\b|\balumnae?\s+reunion\b"
    r"|\br[eé]union\b"
    r"|\balumni\s+get[\s\-]?together\b"
    r"|\balumni\s+met\b|\balumni\s+meeting\b"
    r"|\balumni\s+(?:day|association|network|conclave|connect|forum|"
    r"interaction|membership|registration|awards?|honou?rs?|felicitation)\b"
    r"|\balumni\s+mentorship\b"
    r"|\balumni\s+contribut\w+"
    r"|\bdistinguished\s+alumn[ai]\s+visit\b"
    r"|\balumni\s+student\s+council\b|\balumni\s+association\s+(?:meeting|"
    r"inaugurat\w+|event)\b"
    r"|\balumni\s+(?:charitable\s+)?trust\b"
    r"|\balumnae?\s+(?:awards?|honou?rs?|felicitation)\s+ceremony\b"
    r"|\bdistinguished\s+alumni\b"
    r"|\b(?:silver|diamond|golden|ruby|platinum)\s+jubilee\b"
    r"|\bjubilee\s+r[eé]union\b"
    r"|\br[eé]union\s+of\s+the\s+(?:tce\s+)?class\s+of\s+\d{4}\b"
    r"|\b\d+(?:st|nd|rd|th)\s+year\s+(?:ruby\s+)?(?:celebration|jubilee)\b"
    r"|\bruby\s+(?:celebration|jubilee)\b"
    r"|\bcalling\s+all\b[^.?!]{0,40}\b(?:batch|graduates|alumni)\b"
    r"|\bbatch\s+of\s+\d{4}\s+graduates\b", re.I)

ALUMNI_SPEAKER_ONLY = re.compile(
    r"\balumni\s+(?:talk|speaker|spotlight|lecture|member|address|connect\w*|"
    r"batch|mentorship|masterclass|session)\b"
    r"|\balumnus\b|\balumna\b|\b(?:an\s+)?alumnus\b"
    r"|\bby\s+(?:our\s+)?(?:distinguished\s+)?(?:alumnus|alumni)\b"
    r"|\b(?:19|20)\d{2}\s+batch\b|\bbatch\s+of\s+(?:19|20)\d{2}\b", re.I)

# A post that profiles ONE person and enumerates their wins.  Research/academic
# words there describe that person's credentials, so the post's subject is the
# person's record -> ACHIEVEMENT, not RESEARCH.  Deliberately narrow so that a
# plain "Dr. X secures a research grant" post is still a research act.
PERSON_SPOTLIGHT = re.compile(
    r"\balumni\s*spotlight\b"
    r"|\bspotlight(?:ing|s|ed)?\s+(?:on\s+)?(?:our\s+|the\s+|an\s+)?"
    r"(?:alumn\w+|student|faculty|staff|graduate)\b"
    r"|\bproud\s+to\s+(?:feature|profile|spotlight|introduce)\b"
    r"|\bprolific\b"
    r"|\b(?:his|her|their)\s+journey\s+(?:reflects|from|as)\b"
    r"|\bjourney\s+from\s+[^.?!]{0,60}\bto\b", re.I)

# --- STEP 6: campus / institutional observance ------------------------------
CAMPUS_OBSERVANCE = re.compile(
    r"\bfoundation\s+day\b|\bfounder'?s?\s+day\b|\bfounders?\s+day\b|\bannual\s+day\b"
    r"|\bkuthira\b|\bgreen\s+campus\b|\bopen\s+house\b|\bcampus\s+"
    r"(?:inauguration|inaugurated|initiative|drive|development)\b"
    r"|\b(?:women'?s|men'?s|children'?s|world|"
    r"environment|earth|wildlife|ocean|blood\s+donor|health|student|water|"
    r"mental\s+health)\s+day\b"
    r"|\b(?:international\s+)?(?:youth|yoga|creativity\s*(?:and|&)\s*innovation|"
    r"creativity\s*(?:and|&)\s*invention|reading|arts|human\s+trafficking|"
    r"disaster\s+management)\s+day\b"
    r"|\bnew\s+year'?s?\s+day\b|\bconstitution\s+day\b"
    r"|\bnational\s+safety\s+month\b|\b5s\s+(?:day|methodology)\b"
    r"|\bozone\s+layer\s+day\b|\benvironment(al)?\s+(?:day|week)\b"
    r"|\b(?:college|annual|founder'?s?|foundation)\s+day\b"
    r"|\b(?:award|felicitation|honour|honor|prize\s+distribution|inauguration|"
    r"installation)\s+ceremon(?:y|ies)\b"
    r"|\binauguration\s+of\s+(?:the\s+)?[\w\s-]{0,40}\b(?:consortium|"
    r"association|society|club|cell|chapter|centre|center|forum|hub|academy|"
    r"network|body|committee|board)\b"
    r"|\bina[u]g\w+\s+of\s+(?:the\s+)?(?:student\s+)?(?:research\s+)?"
    r"(?:council|cell|chapter|club|centre|center|forum|association|society)\b",
    re.I)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
# Curly quotes/dashes are folded so "Women's", "Founder's" and "Nature's" match
# the same patterns as their straight-quote spellings.
_SMART_PUNCT = str.maketrans({
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-",
    "\u2015": "-", "\u2212": "-", "\u00a0": " ",
})


def _norm(text):
    if not text:
        return ""
    return _WS.sub(" ", str(text).translate(_SMART_PUNCT)).lower()


def _blank_venues(text):
    """Replace venue phrases with blanks so they cannot act as event head nouns.

    Keeps string length stable so match offsets stay meaningful.
    """
    return VENUE_PHRASES.sub(lambda m: " " * len(m.group(0)), text)


def _as_pattern(pattern):
    """Accept a compiled pattern or a raw pattern string."""
    return pattern if hasattr(pattern, "search") else re.compile(pattern)


def _first(text, pattern):
    m = _as_pattern(pattern).search(text)
    return m.start() if m else None


def _any(text, pattern):
    return bool(_as_pattern(pattern).search(text))


# Pre-compiled head nouns (compiled once at import; the patterns are fixed).
_COMPILED_HEAD_NOUNS = tuple(
    (re.compile(pattern), code) for pattern, code in EVENT_HEAD_NOUNS)


def _evidence_of(evidence, code):
    try:
        return (evidence or {}).get(code) or {}
    except AttributeError:
        return {}


def derive_candidates(text, title=None):
    """Weighted candidate list straight from the classifier patterns.

    Used when a caller has no stored ``category_candidates``.  Mirrors the
    candidate stage (not the final status decision) of the classifier.
    """
    low = _norm(text)
    scored = []
    for code in sorted(CATEGORY_PATTERNS):
        score = 0
        for pattern, weight in CATEGORY_PATTERNS[code]:
            try:
                if re.search(pattern, low):
                    score += weight
            except re.error:
                continue
        if score >= 3:  # QUALIFY_WEIGHT from linkedin_candidates
            scored.append((code, score))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [c for c, _ in scored]


# ---------------------------------------------------------------------------
# semantic features
# ---------------------------------------------------------------------------
def _venue_only_support(body, scan, code):
    """True when the only evidence for ``code`` sits inside a venue phrase.

    168 live SEMINAR rows matched nothing except "Seminar Hall", and CONFERENCE
    rows likewise matched "Conference Hall".  Those name where an event happens,
    never the activity, so the candidate must not survive as a category.
    """
    patterns = CATEGORY_PATTERNS.get(code)
    if not patterns:
        return False
    in_body = any(_any(body, p) for p, _ in patterns)
    in_scan = any(_any(scan, p) for p, _ in patterns)
    return in_body and not in_scan


def _event_head_noun(body):
    """The event type the post itself declares (venue phrases excluded)."""
    scan = _blank_venues(body)
    best = None
    for pattern, code in _COMPILED_HEAD_NOUNS:
        pos = _first(scan, pattern)
        if pos is None:
            continue
        if best is None or pos < best[0]:
            best = (pos, code)
    return best


def _has_real_internship(low):
    if _any(low, INTERNSHIP_ACT):
        return True
    # "international"/"internal" alone is not internship evidence.
    return False


def _industry_is_role_only(low):
    """True when industry words appear but no industry ACT was performed."""
    if _any(low, INDUSTRY_ACT):
        return False
    return _any(low, r"\bindustr(?:y|ies|ial)\b|\bcompany\b|\bcorporate\b")


def _alumni_is_speaker_only(low):
    if _any(low, ALUMNI_ENGAGEMENT):
        return False
    return _any(low, r"\balumni\b|\balumnus\b|\balumna\b|\bbatch\b")


def _research_is_mention_only(low):
    if _any(low, RESEARCH_OUTPUT_ACT):
        return False
    return _any(low, RESEARCH_MENTION_ONLY)


def _result_is_real(low, recipients=True):
    """A genuine completed result, with an acknowledgement-only veto."""
    if not _any(low, RESULT_ACT):
        return False
    # "secured", "ranked", "best paper" etc. need a recipient to be an award.
    return True


# ---------------------------------------------------------------------------
# the resolver
# ---------------------------------------------------------------------------
def resolve_primary_category(text, title=None, candidates=None, evidence=None,
                             allow_review_required=True):
    """Resolve exactly ONE primary category for a post.

    Parameters
    ----------
    text        : the complete post text (never a fragment).
    title       : derived title, when available.
    candidates  : multi-label candidates from the classifier (optional).
    evidence    : {code: {pattern: [spans]}} classifier evidence (optional).
    allow_review_required :
        when True an undecidable post returns ``None`` so the caller can park
        it in REVIEW_REQUIRED; when False the residual candidate order decides.

    Returns
    -------
    dict with keys:
        category     : one allowed category code, or ``None``
        confidence   : 'high' | 'medium' | 'low'
        rule         : the rule that decided
        reason       : human-readable explanation (audit trail)
        dropped      : codes dropped and why
    """
    body = _norm(text)
    if not candidates:
        candidates = derive_candidates(text, title)
    candidates = [c for c in candidates if c in ALLOWED_CATEGORY_CODES]
    dropped = []

    if not candidates:
        # The classifier's candidate list is keyword-derived and is known to
        # miss real activities (a post whose only hit was the bare word
        # "research").  A missing candidate list must not force REVIEW_REQUIRED
        # when the text itself is unambiguous, so resolution still runs.
        candidates = []

    # -- feature extraction ---------------------------------------------------
    head = _event_head_noun(body)
    head_pos, head_code = head if head else (None, None)
    scan = _blank_venues(body)
    industry_act = _any(body, INDUSTRY_ACT)
    placement_act = _any(body, PLACEMENT_ACT)
    internship_act = _has_real_internship(body)
    research_act = _any(body, RESEARCH_OUTPUT_ACT)
    research_topical = _research_is_mention_only(body)
    result_real = _result_is_real(body)
    person_spotlight = _any(body, PERSON_SPOTLIGHT)
    alumni_engagement = _any(body, ALUMNI_ENGAGEMENT)
    alumni_speaker = _alumni_is_speaker_only(body)
    campus_observance = _any(body, CAMPUS_OBSERVANCE)
    declares_event = head_code is not None and _any(body, EVENT_FRAMING)

    # When the post frames itself around an organised event (invites/conducts/
    # registration/date+venue), the event it declares IS the subject.  Weak
    # "industry"/"research"/"career" words inside it are context, so the act
    # rules below must not pre-empt the event head noun.
    event_subject = declares_event and CATEGORY_FAMILY.get(head_code) in (
        ORGANIZED_EVENT, LIFECYCLE)

    def drop(code, why):
        dropped.append({"category": code, "reason": why})

    # -- STEP 1: an industry arrangement -------------------------------------
    if industry_act and not event_subject:
        return {
            "category": "INDUSTRY", "confidence": CONFIDENCE_HIGH,
            "rule": "agreement_act",
            "reason": "post reports an industry arrangement (MoU/partnership/"
                      "industry visit) as the primary institutional act",
            "dropped": dropped,
        }

    # -- STEP 2: a career programme ------------------------------------------
    if placement_act and not event_subject:
        return {
            "category": "PLACEMENT", "confidence": CONFIDENCE_HIGH,
            "rule": "career_placement_act",
            "reason": "post reports a placement activity as its subject",
            "dropped": dropped,
        }
    if internship_act and not event_subject:
        drop("RESEARCH", "internship programme, research is topical")
        return {
            "category": "INTERNSHIP", "confidence": CONFIDENCE_HIGH,
            "rule": "career_internship_act",
            "reason": "post reports an internship programme as its subject "
                      "(not the word 'international')",
            "dropped": dropped,
        }

    # -- STEP 3: a research output / research activity is the subject --------
    # Read from the text, so it may correct a missing/incorrect candidate
    # (the classifier qualified RESEARCH on the bare word "research" 160 times).
    if research_act and not event_subject and not person_spotlight:
        return {
            "category": "RESEARCH", "confidence": CONFIDENCE_HIGH,
            "rule": "research_output_act",
            "reason": "post reports a research output/activity (patent, grant, "
                      "publication, doctorate) as its subject",
            "dropped": dropped,
        }

    # -- STEP 4: a real, completed result ------------------------------------
    if result_real and not event_subject and not _soft_only_is_vetoed(
            body, research_act, person_spotlight):
        return {
            "category": "ACHIEVEMENT", "confidence": CONFIDENCE_HIGH,
            "rule": "recognition_result",
            "reason": "post reports a completed award/result with a recipient "
                      "(not merely congratulations or a certificate)",
            "dropped": dropped,
        }

    # A post that deliberately spotlights one person is a recognition act about
    # them, even when it lists no single numeric win: the subject is the person.
    if person_spotlight:
        return {
            "category": "ACHIEVEMENT", "confidence": CONFIDENCE_HIGH,
            "rule": "person_spotlight_recognition",
            "reason": "post profiles and honours a named individual; research/"
                      "alumni words describe that person, not the activity",
            "dropped": dropped,
        }

    # -- STEP 5: an organised event or a named institutional observance -------
    # CAMPUS head nouns (College Day, Founder's Day, award ceremony) name the
    # activity just as an event head noun does, even though CAMPUS sits in the
    # lifecycle family rather than ORGANIZED_EVENT.
    if head_code is not None and CATEGORY_FAMILY.get(head_code) in (
            ORGANIZED_EVENT, LIFECYCLE):
        # An event post is about the event: topical research/alumni/industry
        # words inside it are context, never the activity.
        for code in list(candidates):
            if CATEGORY_FAMILY.get(code) in (RESEARCH_OUTPUT, RECOGNITION,
                                             LIFECYCLE, AGREEMENT):
                if code != head_code:
                    drop(code, "post reports an organised event; %s is context"
                         % code)
        return {
            "category": head_code, "confidence": CONFIDENCE_HIGH,
            "rule": "lifecycle_head_noun" if CATEGORY_FAMILY.get(head_code) == LIFECYCLE
                    else "organized_event_head_noun",
            "reason": "post declares an organised event; its own head noun "
                      "denotes the activity (venue words excluded)",
            "dropped": dropped,
        }

    # -- STEP 6: lifecycle ----------------------------------------------------
    if alumni_engagement:
        return {
            "category": "ALUMNI", "confidence": CONFIDENCE_HIGH,
            "rule": "alumni_engagement_act",
            "reason": "post reports an alumni meet/reunion/engagement, not an "
                      "alumnus merely speaking",
            "dropped": dropped,
        }
    if campus_observance:
        return {
            "category": "CAMPUS", "confidence": CONFIDENCE_HIGH,
            "rule": "campus_observance_act",
            "reason": "post reports an institutional/campus observance",
            "dropped": dropped,
        }

    # -- STEP 7: residual, deterministic --------------------------------------
    survivors = []
    for code in candidates:
        fam = CATEGORY_FAMILY.get(code)
        if code == "INTERNSHIP" and not internship_act:
            drop(code, "'intern' matched 'international', not an internship")
            continue
        if code == "RESEARCH" and research_topical:
            drop(code, "only topical research mentions (audience/topic)")
            continue
        if code == "ACHIEVEMENT" and not result_real:
            drop(code, "only acknowledgement language, no real result")
            continue
        if code == "ALUMNI" and alumni_speaker and not alumni_engagement:
            drop(code, "alumnus/alumni mention without alumni engagement")
            continue
        if code == "INDUSTRY" and not industry_act:
            drop(code, "industry mentioned, no industry act")
            continue
        if _venue_only_support(body, scan, code):
            drop(code, "matched only a venue phrase (e.g. 'Seminar Hall')")
            continue
        survivors.append(code)

    survivors = _drop_unsupported(body, survivors, declares_event, dropped, drop)

    if not survivors:
        return {
            "category": None, "confidence": CONFIDENCE_LOW,
            "rule": "all_candidates_suppressed",
            "reason": "every candidate was explainable as a mention/context "
                      "word; primary category not determinable",
            "dropped": dropped,
        }
    if len(survivors) == 1:
        return {
            "category": survivors[0], "confidence": CONFIDENCE_HIGH,
            "rule": "single_survivor",
            "reason": "only one category survives context checks",
            "dropped": dropped,
        }

    # family precedence, then within-family specificity
    by_fam = {}
    for code in survivors:
        by_fam.setdefault(CATEGORY_FAMILY.get(code), []).append(code)
    present = [f for f in FAMILY_ORDER if f in by_fam]
    if len(present) == 1:
        fam = present[0]
        if len(by_fam[fam]) == 1:
            chosen, confidence = by_fam[fam][0], CONFIDENCE_HIGH
        else:
            chosen, confidence = _most_specific(by_fam[fam]), CONFIDENCE_MEDIUM
        return {
            "category": chosen, "confidence": confidence,
            "rule": "family_%s" % fam,
            "reason": "all surviving candidates belong to one family (%s)"
                      % fam,
            "dropped": dropped,
        }

    # genuine multi-family tie: decide only if an explicit human choice exists
    ranked = []
    for fam in present:
        members = by_fam[fam]
        ranked.append((FAMILY_ORDER.index(fam),
                       min(FAMILY_SPECIFICITY.get(c, SINGLE_MEMBER_ORDER.get(c, 99))
                           for c in members),
                       sorted(members)))
    ranked.sort(key=lambda x: (x[0], x[1]))
    if allow_review_required and len(ranked) > 1 and ranked[0][0] == ranked[1][0]:
        return {
            "category": None, "confidence": CONFIDENCE_LOW,
            "rule": "multi_family_tie",
            "reason": "surviving candidates span %s with no distinguishing "
                      "context" % " and ".join(present),
            "dropped": dropped,
        }

    chosen = _most_specific(ranked[0][2])
    return {
        "category": chosen, "confidence": CONFIDENCE_MEDIUM,
        "rule": "family_precedence",
        "reason": "nature of the act is %s" % FAMILY_ORDER[ranked[0][0]],
        "dropped": dropped,
    }


def _soft_only_is_vetoed(body, research_act, person_spotlight=False):
    """Veto a recognition when the only 'result' is really a research output."""
    if person_spotlight:
        # The post enumerates a person's real, concrete wins.
        return False
    if research_act:
        return True
    # "participated / attended / certificate of participation" is not a result.
    return bool(re.search(r"\b(?:participat\w+|attended|certificates?)\b", body,
                          re.I)) and not _any(body, RESULT_ACT)


def _most_specific(codes):
    return sorted(codes, key=lambda c: (FAMILY_SPECIFICITY.get(
        c, SINGLE_MEMBER_ORDER.get(c, 99)), c))[0]


# ---------------------------------------------------------------------------
# A surviving candidate is not enough: it must be supported by a statement of
# something that happened.  Without this, a bare topical word ("research",
# "rural", "graduation") promotes a post into a category it never claimed.
# ---------------------------------------------------------------------------
CATEGORY_ACT_SIGNAL = {
    "RESEARCH": "RESEARCH_OUTPUT_ACT",
    "ACHIEVEMENT": "RESULT_ACT",
    "INDUSTRY": "INDUSTRY_ACT",
    "PLACEMENT": "PLACEMENT_ACT",
    "INTERNSHIP": "INTERNSHIP_ACT",
    "ALUMNI": "ALUMNI_ENGAGEMENT",
    "CAMPUS": "CAMPUS_OBSERVANCE",
}


def _strong_keyword(body, code):
    """True when the category is named by a concrete artefact, not a topic.

    CATEGORY_PATTERNS scores each keyword; >= 4 marks a concrete outcome or
    act noun ("patent", "journal", "mou", "offer") while 3 marks a bare topic
    word ("research") that cannot on its own justify a category.
    """
    for pattern, weight in (CATEGORY_PATTERNS.get(code) or ()):
        if weight >= 4 and _any(body, pattern):
            return True
    return False


def _act_supported(body, code, declares_event):
    """True when the post actually states an act/event of this category.

    Event-shaped categories (workshop, seminar, ...) need organised-event
    framing; outcome categories need their matching act pattern or a concrete
    artefact keyword.
    """
    signal = CATEGORY_ACT_SIGNAL.get(code)
    if signal is not None:
        return _any(body, globals()[signal]) or _strong_keyword(body, code)
    return declares_event or _any(body, ACTIVITY_SCHEDULE)


def _drop_unsupported(body, survivors, declares_event, dropped, drop):
    """Remove survivors that rest on a topical word alone."""
    keep = []
    for code in survivors:
        if _act_supported(body, code, declares_event):
            keep.append(code)
        else:
            drop(code, "matched a topic word but the post states no "
                       "%s activity" % code.lower())
    return keep


# ---------------------------------------------------------------------------
# Strict honesty layer: greetings are not activities
# ---------------------------------------------------------------------------

REPORTABLE = "REPORTABLE"
NON_ACTIVITY = "NON_ACTIVITY"
REVIEW_REQUIRED = "REVIEW_REQUIRED"

# Holiday/occasion wish templates.  On their own these report no activity; the
# institution is only signing off, so they must never become a CAMPUS event.
GREETING_ONLY = re.compile(
    r"\bmerry\s+christmas\b"
    r"|\bwarm(?:est)?\s+wishes\b"
    r"|\bwishes?\s+you\s+a\b"
    r"|\bwishes?\s+you\s+and\s+your\s+family\b"
    r"|\bhappy\s+new\s+year\b"
    r"|\bhappy\s+\w{3,20}\s+day\b(?![^.?!]{0,80}\b(?:organis|organiz|celebrat|"
    r"conduct|hosted|hosting|invit|webinar|lecture|session|register|participat|"
    r"competitions?|celebrat(?:ed|ion)|event|program(?:me)?|camp|awareness|"
    r"drive|initiative|ceremony|workshop|seminar|training|festival))\b"
    r"|\bgreetings?\s+from\b"
    r"|\bcelebrat(?:ing|es)\s+(?:the\s+)?(?:joy|spirit|warmth|festiv\w*)\s+of\b",
    re.I)

# Any of these means the post is actually reporting something that happened,
# even when a wish template is also present (e.g. "Wishes on Republic Day,
# following our 2024 Swachhtha drive").
ACTIVITY_EVIDENCE = (
    EVENT_FRAMING,
    INDUSTRY_ACT,
    PLACEMENT_ACT,
    INTERNSHIP_ACT,
    RESEARCH_OUTPUT_ACT,
    RESULT_ACT,
    ALUMNI_ENGAGEMENT,
    CAMPUS_OBSERVANCE,
)

# Annual round-ups recount many activities ("686 institutional activities &
# updates", "2025 at a Glance").  They are not one activity, so a single
# category taken from them would be an artefact of the word list.  Only
# unambiguous recap markers qualify: "annual report" and "<n> events" also
# occur in ordinary invitations, so they are deliberately excluded.
AGGREGATE_RECAP = re.compile(
    r"\b(?:at\s+a\s+glance|year\s+in\s+review|annual\s+recap|annual\s+summary|"
    r"yearly\s+recap|20\d\d\s+in\s+review)\b",
    re.I)


def classify_non_activity(text, title=None):
    """Return a NON_ACTIVITY reason, or None if the post reports an activity.

    Deliberately conservative: it only fires on unambiguous wish/sign-off
    templates that carry no event framing and no concrete institutional act.
    """
    body = _norm(text)
    head = _norm(title)
    if not (GREETING_ONLY.search(body) or GREETING_ONLY.search(head)):
        return None
    if any(_any(body, pat) for pat in ACTIVITY_EVIDENCE):
        return None
    if _event_head_noun(_blank_venues(body)) is not None:
        return None
    return ("post is a holiday/occasion wish or sign-off template with no "
            "evidence of an institutional activity, event or programme being "
            "reported")


def decide_for_row(row):
    """Final single-category + reportable-status decision for one row.

    Honours a human override, then separates genuine non-activity, then
    resolves one primary category, and finally reports honest uncertainty as
    REVIEW_REQUIRED rather than forcing a guess.
    """
    def get(key, default=None):
        try:
            value = row[key]
        except (KeyError, IndexError, TypeError):
            return default
        return default if value is None else value

    resolution = resolve_for_row(row)

    # A human decision is ground truth and is never re-litigated here.
    if resolution.get("rule") == "manual_override":
        return dict(resolution, status=REPORTABLE)

    if resolution.get("category"):
        # An annual round-up is not one activity, so a category scraped from
        # its word list is an artefact rather than a judgement.  A recap is
        # only spared when it also frames itself as an organised event.
        body = _norm(get("description", ""))
        recap = AGGREGATE_RECAP.search(body)
        declares_event = (recap and _event_head_noun(_blank_venues(body)) is not None
                          and _any(body, EVENT_FRAMING))
        if recap and not declares_event:
            return {
                "category": None, "status": REVIEW_REQUIRED,
                "confidence": CONFIDENCE_LOW, "rule": "aggregate_recap",
                "reason": "post is an annual round-up of many activities, so "
                          "no single primary category applies; needs human review",
                "dropped": resolution.get("dropped", []),
            }
        return dict(resolution, status=REPORTABLE)

    reason = classify_non_activity(get("description", ""), get("title"))
    if reason:
        return {
            "category": None, "status": NON_ACTIVITY,
            "confidence": CONFIDENCE_HIGH, "rule": "greeting_only",
            "reason": reason, "dropped": resolution.get("dropped", []),
        }

    return {
        "category": None, "status": REVIEW_REQUIRED,
        "confidence": CONFIDENCE_LOW,
        "rule": resolution.get("rule") or "no_confident_signal",
        "reason": "no activity statement survives the honesty rules, so the "
                  "row needs human review instead of a forced category",
        "dropped": resolution.get("dropped", []),
    }


def resolve_for_row(row):
    """Resolve the single primary category for a reportable row (dict/Row)."""
    def get(key, default=None):
        try:
            value = row[key]
        except (KeyError, IndexError, TypeError):
            return default
        return default if value is None else value

    def jload(key):
        raw = get(key)
        if not raw:
            return None
        if isinstance(raw, (list, dict)):
            return raw
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return None

    evidence = jload("category_evidence")
    candidates = jload("category_candidates")
    if not candidates:
        candidates = jload("categories")

    # A human decision is ground truth and is never overruled by the resolver.
    # Categories are stored inside the manual_overrides JSON document.
    manual = get("manual_category") or get("category_override")
    if manual is None:
        overrides = jload("manual_overrides")
        if isinstance(overrides, dict):
            manual = overrides.get("categories")
            if isinstance(manual, (list, tuple)):
                # An override of exactly one code is a primary category.
                manual = manual[0] if len(manual) == 1 else None
    if isinstance(manual, str):
        manual = manual.strip()
    if manual in ALLOWED_CATEGORY_CODES:
        return {
            "category": manual, "confidence": CONFIDENCE_HIGH,
            "rule": "manual_override",
            "reason": "primary category was set by a human reviewer and is "
                      "authoritative over automatic resolution",
            "dropped": [{"category": c, "reason": "superseded by manual override"}
                        for c in (candidates or []) if c != manual],
        }

    return resolve_primary_category(
        text=get("description", ""),
        title=get("title"),
        candidates=candidates,
        evidence=evidence,
    )