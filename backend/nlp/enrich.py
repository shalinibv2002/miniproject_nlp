"""Apply Phase 4 extraction to all activities and persist entities/keywords."""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.nlp import extractors

logger = logging.getLogger("tce.enrich")

ENTITY_TYPES = {
    "PERSON", "ORG", "DATE", "GPE", "VENUE", "AWARD", "TOPIC", "MONEY", "PRODUCT", "OTHER",
}


def method_id(conn, name):
    row = conn.execute(
        "SELECT id FROM classification_methods WHERE name LIKE ?", (f"%{name}%",)
    ).fetchone()
    return row["id"] if row else None


def enrich_activity(conn, activity_id, nlp=None):
    row = conn.execute(
        "SELECT id, title, description FROM institutional_activities WHERE id=?",
        (activity_id,),
    ).fetchone()
    if row is None:
        return 0, 0
    text = " ".join(filter(None, [row["title"], row["description"]]))

    results = extractors.extract_all(text, nlp)
    ent_count = 0
    kw_count = 0

    regex_method = method_id(conn, "Regex")
    spacy_method = method_id(conn, "SpaCy")
    dict_method = method_id(conn, "Dictionary Fuzzy")

    seen_entities = set()
    for ent in results["spacy_entities"]:
        key = (ent["entity_type"], ent["entity_text"])
        if key in seen_entities:
            continue
        seen_entities.add(key)
        if ent["entity_type"] not in ENTITY_TYPES:
            continue
        conn.execute(
            """INSERT OR IGNORE INTO activity_entities
               (activity_id, entity_type, entity_text, confidence, extraction_method_id)
               VALUES (?, ?, ?, ?, ?)""",
            (activity_id, ent["entity_type"], ent["entity_text"],
             min(ent["confidence"], 1.0), spacy_method),
        )
        ent_count += 1

    if results["venue"]:
        conn.execute(
            """INSERT OR IGNORE INTO activity_entities
               (activity_id, entity_type, entity_text, confidence, extraction_method_id)
               VALUES (?, 'VENUE', ?, 0.85, ?)""",
            (activity_id, results["venue"], regex_method),
        )
        ent_count += 1

    if results["resource_person"]:
        conn.execute(
            """INSERT OR IGNORE INTO activity_entities
               (activity_id, entity_type, entity_text, confidence, extraction_method_id)
               VALUES (?, 'PERSON', ?, 0.85, ?)""",
            (activity_id, results["resource_person"], regex_method),
        )
        ent_count += 1

    if results["organizer"]:
        conn.execute(
            """INSERT OR IGNORE INTO activity_entities
               (activity_id, entity_type, entity_text, confidence, extraction_method_id)
               VALUES (?, 'ORG', ?, 0.80, ?)""",
            (activity_id, results["organizer"], regex_method),
        )
        ent_count += 1

    for dept in results["departments"]:
        conn.execute(
            """INSERT OR IGNORE INTO activity_entities
               (activity_id, entity_type, entity_text, confidence, extraction_method_id)
               VALUES (?, 'ORG', ?, ?, ?)""",
            (activity_id, dept["name"], dept["score"] / 100.0, dict_method),
        )
        ent_count += 1

    for kw in results["keywords"]:
        conn.execute(
            """INSERT OR IGNORE INTO activity_keywords
               (activity_id, keyword, weight) VALUES (?, ?, 0.5)""",
            (activity_id, kw),
        )
        kw_count += 1

    return ent_count, kw_count


def enrich_all(conn=None, activity_id=None):
    own = conn is None
    conn = conn or get_connection()
    nlp = extractors.get_nlp()
    try:
        if activity_id:
            rows = [{"id": activity_id}]
        else:
            rows = conn.execute("SELECT id FROM institutional_activities").fetchall()
        for row in rows:
            e, k = enrich_activity(conn, row["id"], nlp)
            logger.info("Activity %s: +%d entities, +%d keywords", row["id"], e, k)
        conn.commit()
        return len(rows)
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    n = enrich_all()
    print(f"Enriched {n} activities")