"""Phase 8: build LinkedIn search terms per activity (free, manual workflow)."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import re


def clean_term(term):
    term = re.sub(r"[^a-zA-Z0-9 ]", " ", term).strip()
    return re.sub(r"\s+", " ", term)


def build_search_terms(title, description=None, activity_date=None,
                       department=None, person_name=None):
    """Return a list of increasingly-specific LinkedIn search queries.

    NEVER fabricate a post URL; these terms are for a human (or an approved
    API) to search the public TCE LinkedIn page.
    """
    terms = []
    base = clean_term(title or "")

    if base:
        terms.append(base)
        if department:
            terms.append(f"{base} {department}")
        if activity_date:
            yyyy = (activity_date or "")[:4]
            if len(yyyy) == 4:
                terms.append(f"{base} {yyyy}")

    if person_name:
        terms.append(f"{base} {clean_term(person_name)}")

    if description:
        # pick a distinctive phrase if the title is too generic
        phrases = [s for s in re.split(r"[.\n;]", description) if len(s.split()) >= 4]
        for phrase in phrases[:2]:
            phrase = clean_term(phrase)
            if phrase and phrase not in terms:
                terms.append(phrase)

    # de-dup, keep order
    seen = set()
    unique = []
    for t in terms:
        if t and t not in seen:
            seen.add(t)
            unique.append(t)
    return unique


def build_per_activity_terms(conn, activity_id):
    row = conn.execute(
        """SELECT a.title, a.description, a.activity_date, d.name AS department
           FROM institutional_activities a
           LEFT JOIN activity_departments ad ON ad.activity_id = a.id AND ad.is_primary = 1
           LEFT JOIN departments d ON d.id = ad.department_id
           WHERE a.id = ?""",
        (activity_id,),
    ).fetchone()
    if not row:
        return []
    person = conn.execute(
        """SELECT entity_text FROM activity_entities
           WHERE activity_id=? AND entity_type IN ('PERSON','ORG') LIMIT 1""",
        (activity_id,),
    ).fetchone()
    return build_search_terms(
        row["title"], row["description"], row["activity_date"],
        row["department"], person["entity_text"] if person else None,
    )