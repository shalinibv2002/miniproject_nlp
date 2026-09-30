"""Shared dictionaries: TCE department names + aliases loaded from the DB."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection

KEYWORDS_SUFFIX = [
    "dept", "department", "department of", "dept of",
    "association", "staff association", "students association",
]

INSTITUTION_WIDE_MARKERS = [
    "convocation", "naac visit", "nba visit", "nirf", "founder's day",
    "annual day", "inauguration of the college", "induction programme",
    "orientation programme", "teacher's day", "independence day",
    "republic day", "sports day", "campus-wide", "all departments",
]


def load_department_dict(conn=None):
    """Return a list of dicts: {id, code, name, short_name, aliases:[...]}."""
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute("SELECT id, code, name, short_name, aliases FROM departments").fetchall()
        result = []
        for row in rows:
            aliases = []
            for a in (row["aliases"] or "").split(","):
                a = a.strip().lower()
                if a:
                    aliases.append(a)
            result.append({
                "id": row["id"],
                "code": row["code"],
                "name": row["name"],
                "short_name": row["short_name"],
                "aliases": aliases,
            })
        return result
    finally:
        if own:
            conn.close()


def department_keywords():
    """Flat list of alias keywords (lowercased) for fuzzy/exact scanning."""
    keywords = set()
    for dept in load_department_dict():
        keywords.add(dept["name"].lower())
        if dept["short_name"]:
            keywords.add(dept["short_name"].lower())
        for alias in dept["aliases"]:
            keywords.add(alias)
    return sorted(keywords)


def is_institution_wide(text):
    """Heuristic: does the text suggest an institution-wide event?"""
    if not text:
        return False
    t = text.lower()
    return any(marker in t for marker in INSTITUTION_WIDE_MARKERS)