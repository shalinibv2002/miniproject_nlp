"""Validation: flag invalid records; never silently delete."""

from backend.database.cleaner import normalize_date


class ValidationResult:
    def __init__(self, valid=True, problems=None, needs_review=False):
        self.valid = valid
        self.problems = problems or []
        self.needs_review = needs_review

    def __repr__(self):
        return f"ValidationResult(valid={self.valid}, needs_review={self.needs_review}, problems={self.problems})"


def validate_record(record):
    """Validate a cleaned record.

    Returns a ValidationResult. Records with problems are flagged, never
    silently discarded. 'valid' is only False when the record is unusable
    (e.g. no title AND no content at all).
    """
    problems = []
    needs_review = False

    title = (record.get("title") or "").strip()
    description = (record.get("description") or "").strip()
    activity_date = (record.get("activity_date") or "").strip()

    if not title:
        problems.append("missing-title")
        needs_review = True
    if not description:
        problems.append("missing-description")
        needs_review = True
    if activity_date and normalize_date(activity_date) is None:
        problems.append("unparseable-date")
        needs_review = True

    valid = bool(title) or bool(description)
    return ValidationResult(valid=valid, problems=problems, needs_review=needs_review)