"""Normalized titles for deduplication and search."""

import re

from backend.database.cleaner import normalize_unicode, normalize_whitespace, normalize_punctuation


def to_normalized_title(title):
    """Lowercase, punctuation-stripped, whitespace-normalized title."""
    if not title:
        return ""
    t = normalize_unicode(str(title))
    t = t.lower()
    t = normalize_punctuation(t)
    t = normalize_whitespace(t)
    return t