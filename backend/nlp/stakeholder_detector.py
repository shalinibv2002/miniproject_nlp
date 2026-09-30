"""Phase 6: rule-based stakeholder detection.

Keyword cues map text to one or more stakeholder groups; fall back to
'unknown' when unclear.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection

STAKEHOLDER_CUES = {
    "STUDENTS": [
        "students", "student", "student teams", "student projects", "ug students",
        "pg students", "students association", "student volunteers", "first year students",
        "final year students", "interns", "cadets", "participants received certificates",
        "code camp", "profr.?student", "girl students",
    ],
    "FACULTY": [
        "faculty", "faculty members", "teaching staff", "professors", "teachers",
        "faculty development", "fdp", "staff of the department", "teaching faculty",
        "non-teaching staff", "college faculty", "young faculty",
    ],
    "STAFF": [
        "non-teaching staff", "support staff", "administrative staff", "office staff",
        "technical staff", "laboratory staff",
    ],
    "ALUMNI": [
        "alumni", "alumnus", "alumni association", "silver jubilee reunion", "alumni meet",
        "alumni networking", "alumni webinar", "old students",
    ],
    "INDUSTRY": [
        "industry", "industries", "companies", "corporate", "company officials",
        "mou", "memorandum of understanding", "recruiters", "industry experts",
        "industry visits", "startup", "startup founder", "entrepreneurs",
    ],
    "PARENTS": [
        "parents", "guardians", "parents association", "parent teacher",
    ],
    "GOVERNMENT": [
        "government", "aicte", "ugc", "dst", "drdo", "isro", "ministry", "tnedu",
        "tnea", "sponsored by", "funded by", "agency", "nba", "naac", "nirf", "iqac",
        "tamil nadu government", "bharat", "india",
    ],
    "COMMUNITY": [
        "community", "rural", "village", "school students", "school children",
        "blood bank", "blood donation", "society", "public", "farmers", "local community",
        "nearby schools", "adopted village", "ngos", "underprivileged",
    ],
}

UNDERLINED_HINTS = ["workshop", "webinar", "conference", "seminar", "coaching",
                    "guidance", "training", "session", "camp"]


def detect_stakeholders(text):
    """Return list of stakeholder codes with confidence."""
    if not text:
        return []
    t = text.lower()
    found = []
    for code, cues in STAKEHOLDER_CUES.items():
        hit = any(cue in t for cue in cues)
        if hit:
            found.append((code, 0.8))
    # de-dup
    unique = {}
    for code, conf in found:
        unique[code] = max(unique.get(code, 0), conf)
    return sorted(unique.items())


def populate_stakeholders(conn=None, activity_id=None):
    own = conn is None
    conn = conn or get_connection()
    try:
        if activity_id:
            rows = conn.execute(
                "SELECT id, title, description FROM institutional_activities WHERE id=?",
                (activity_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, title, description FROM institutional_activities"
            ).fetchall()

        stakeholder_ids = {
            r["code"]: r["id"]
            for r in conn.execute("SELECT code, id FROM stakeholders").fetchall()
        }
        counts = {}
        for row in rows:
            text = " ".join(filter(None, [row["title"], row["description"]]))
            detections = detect_stakeholders(text)
            counts[row["id"]] = detections
            for index, (code, conf) in enumerate(detections):
                st_id = stakeholder_ids.get(code)
                if st_id:
                    conn.execute(
                        """INSERT OR IGNORE INTO activity_stakeholders
                           (activity_id, stakeholder_id, confidence, is_primary)
                           VALUES (?, ?, ?, ?)""",
                        (row["id"], st_id, conf, 1 if index == 0 else 0),
                    )
        conn.commit()
        return counts
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    counts = populate_stakeholders()
    print("Populated stakeholder matches for %d activities" % len(counts))