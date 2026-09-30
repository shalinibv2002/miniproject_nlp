"""Public academic-period presentation.

The institution's public timeline is exactly five academic periods plus one
honest historical bucket:

    ``2021-22`` ``2022-23`` ``2023-24`` ``2024-25`` ``2025-26``  "Before 2021"

Stored ``final_activity_metadata.academic_year`` stays authoritative for the
five public periods.  Rows whose metadata carries no academic year are
recovered at read time where the evidence is unambiguous (a real activity date
or a single clear year inside the collected evidence/date text); everything
else is presented once in the ``Before 2021`` bucket.

Nothing here changes institutional metadata — resolution is read-time only, by
design, so evidence, provenance and category assignments are never destroyed.
No public UI ever shows "Not available" as a period.
"""

from __future__ import annotations

import re
from typing import Iterable, Optional

from backend.database.init_db import get_connection

# Public period keys are the short catalog forms used everywhere in metadata
# and by the analytics API (including the pinned /api/years contract).
PUBLIC_PERIODS = ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
BEFORE_2021 = "Before 2021"

# Display labels used by the public UI.  Labels intentionally mirror the
# existing frontend tests ("2021-2022", ...) while the keys stay short.
PUBLIC_PERIOD_LABELS = {
    "2021-22": "2021-2022", "2022-23": "2022-2023", "2023-24": "2023-2024",
    "2024-25": "2024-2025", "2025-26": "2025-2026",
    BEFORE_2021: BEFORE_2021,
}

# Every option the public filter exposes — five periods and the Before-2021
# bucket.  There is deliberately no NULL / "Not available" / "unresolved" /
# "unknown" option.
PUBLIC_PERIOD_OPTIONS = PUBLIC_PERIODS + (BEFORE_2021,)

_YEAR_TOKEN = re.compile(r"(?<!\d)(20\d{2})(?!\d)")


def ids_in_clause(ids, chunk=900):
    """Return ``(sql_fragment, params)`` for ``a.id IN (...)`` over ``ids``.

    ID lists are chunked to stay under SQLite's per-statement bound-parameter
    limit.  An empty set resolves to ``1 = 0`` so a "no ids" filter (e.g. an
    empty Before-2021 bucket) returns zero rows instead of a degenerate IN.
    """
    ids = sorted(ids or ())
    if not ids:
        return "1 = 0", []
    clauses = []
    params = []
    for start in range(0, len(ids), chunk):
        part = ids[start:start + chunk]
        marks = ", ".join("?" for _ in part)
        clauses.append(f"a.id IN ({marks})")
        params.extend(part)
    return "(" + " OR ".join(clauses) + ")", params


def period_label(period: Optional[str]) -> str:
    """Public display text for a period key; unknown/missing -> Before 2021."""
    if not period:
        return BEFORE_2021
    return PUBLIC_PERIOD_LABELS.get(period, BEFORE_2021)


def normalize_period(value: Optional[str], default: Optional[str] = None) -> Optional[str]:
    """Accept a short key or a display label and return the short key.

    Matches are normalised to the short catalog key so any of the following
    resolve consistently: ``2024-25``, ``2024-2025``, ``2025-26``, and the
    special ``Before 2021`` spellings ``before 2021``/``prior to 2021``/
    ``pre-2021``.  Unknown values return ``default``.
    """
    if not value:
        return default
    v = str(value).strip()
    if v in PUBLIC_PERIOD_LABELS:
        return v
    t = v.lower().replace(" ", "").replace("·", "").replace("-", "")
    for key, label in PUBLIC_PERIOD_LABELS.items():
        if t in (key.replace("-", ""), label.replace("-", "").replace(" ", "")):
            return key
    if any(cue in t for cue in
           ("before2021", "priorto2021", "prior2021", "pre2021", "before-2021")):
        return BEFORE_2021
    if t in ("notavailable",):
        return default or BEFORE_2021
    return default


def year_to_period(year: int) -> str:
    """Clamp a calendar year to the short public period it belongs to."""
    if year <= 2020:
        return BEFORE_2021
    if year == 2021:
        return "2021-22"
    if year == 2022:
        return "2022-23"
    if year == 2023:
        return "2023-24"
    if year == 2024:
        return "2024-25"
    return "2025-26"  # 2025 and 2026 both belong to the last public period.


def _unique_year_tokens(text: Optional[str]):
    """Distinct calendar-year tokens in ``text`` (2000-2099), if any.

    Academic-year spans ("2023-24", "2022-2024") genuinely contain two distinct
    years and so never return a single year — they are deliberately excluded
    rather than guessing at either side.  Long patent/application numbers
    ("202441009072") do not produce a token at all.
    """
    if not text:
        return None
    tokens = {int(token) for token in _YEAR_TOKEN.findall(text)}
    if 2000 <= min(tokens) <= 2099 if tokens else False:
        return frozenset(tokens)
    return None


def single_evidence_year(*texts: Optional[str]) -> Optional[int]:
    """Return the one unambiguous calendar year across the given text fields.

    A year is only returned when exactly one distinct year is present across
    all merged fields.  Spans and multi-year catalogue text produce ``None``.
    """
    merged = " ".join(text for text in texts if text)
    tokens = {int(token) for token in _YEAR_TOKEN.findall(merged)}
    if len(tokens) == 1 and 2000 <= min(tokens) <= 2099:
        return min(tokens)
    return None


def resolve_period(academic_year=None, activity_date=None,
                   activity_date_text=None, evidence_text=None) -> str:
    """Deterministic, read-only period resolution for one activity.

    Order of authority:
      1. The stored academic year, when it is one of the five public periods.
      2. A real structured activity date.
      3. A single unambiguous year inside the free-text evidence.

    Any activity that reaches the end is presented in the ``Before 2021``
    bucket.  This intentionally groups undated/ambiguous history honestly
    under Before 2021 instead of inventing a period.
    """
    if academic_year in PUBLIC_PERIODS:
        return academic_year

    year = None
    if activity_date:
        try:
            year = int(str(activity_date)[:4])
        except (ValueError, TypeError):
            year = None
    if year is None:
        year = single_evidence_year(activity_date_text, evidence_text)
    if year is not None:
        return year_to_period(year)
    return BEFORE_2021


class PeriodResolver:
    """Cached read-time resolution over the whole public activity set.

    One instance is cheap and thread-safe for reads; callers may reuse it
    across requests.  It never opens its own connection unless the caller
    provides ``conn``.
    """

    def __init__(self, conn=None):
        self._conn = conn
        self._own = conn is None
        self._map = None  # {activity_id: short period}
        self._by_period = None  # {short period: frozenset(activity_id)}

    def _load(self):
        if self._map is not None:
            return
        conn = self._conn or get_connection()
        try:
            rows = conn.execute(
                """SELECT a.id, m.academic_year, a.activity_date,
                          m.activity_date_text, m.evidence_text
                   FROM institutional_activities a
                   LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
            ).fetchall()
            period_map = {
                row["id"]: resolve_period(
                    row["academic_year"], row["activity_date"],
                    row["activity_date_text"], row["evidence_text"])
                for row in rows
            }
            by_period = {}
            for activity_id, period in period_map.items():
                by_period.setdefault(period, set()).add(activity_id)
            self._map = period_map
            self._by_period = {period: frozenset(ids) for period, ids in by_period.items()}
        finally:
            if self._own:
                conn.close()

    @property
    def period_map(self):
        self._load()
        return self._map

    @property
    def by_period(self):
        self._load()
        return self._by_period

    def period_for(self, activity_id) -> str:
        return self.period_map.get(activity_id, BEFORE_2021)

    def ids_for(self, period: Optional[str]):
        self._load()
        if not period:
            return frozenset()
        key = normalize_period(period)
        if key not in PUBLIC_PERIODS and key != BEFORE_2021:
            key = BEFORE_2021
        return self._by_period.get(key, frozenset())

    def close(self):
        if self._own and self._conn is not None:
            try:
                self._conn.close()
            finally:
                self._conn = None


if __name__ == "__main__":  # pragma: no cover - standalone sanity check
    from backend.database.init_db import get_connection
    resolver = PeriodResolver(conn=get_connection())
    print(len(resolver.period_map), "activities resolved")
    for period in PUBLIC_PERIOD_OPTIONS:
        print(f"  {period_label(period):12} {len(resolver.ids_for(period))}")
    resolver.close()
