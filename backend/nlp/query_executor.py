"""Query System V2: execute a safe internal plan against the public dataset.

The executor reads the activity universe exactly like the dashboard analytics
(normalised departments, read-time resolved periods, public category codes) so
every answer reconciles with the rest of the app.  It only ever writes the
public response contract — internal plan details never leave this module.
"""

from __future__ import annotations

import re

from backend.database.category_catalog import (
    CATEGORY_PUBLIC_NAMES, PUBLIC_CATEGORY_CODES, dimension_fields,
)
from backend.database.department_catalog import (
    GENERAL_NAME, PUBLIC_DEPARTMENTS, department_normalized_sql,
    normalize_department,
)
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, PUBLIC_PERIOD_LABELS, PeriodResolver,
    ids_in_clause, resolve_period,
)
from backend.nlp.query_interpreter import (
    KIND_BREAKDOWN, KIND_CLARIFICATION, KIND_COMPARE, KIND_COUNT, KIND_DETAIL,
    KIND_HIGHEST, KIND_LIST, KIND_LOWEST, KIND_RANKING, KIND_TOP_N,
    KIND_TREND, KIND_UNSUPPORTED,
)

STATUS_ANSWER = "answer"
STATUS_ZERO = "zero"
STATUS_UNSUPPORTED = "unsupported"
STATUS_CLARIFICATION = "clarification"

ZERO_MESSAGE = "No matching activities were found for the selected criteria."
OUT_OF_SCOPE_MESSAGE = (
    "I can answer questions about TCE activities, categories, departments, "
    "academic periods, achievements, workshops, research, collaborations, "
    "and related institutional activities."
)

_NOUN_TRIM = re.compile(
    r"\b(?:seminar|workshops?|symposium|conference|tech fest|hack-a-thon|hackathon|"
    r"camp|bootcamp|drive|meet(?:ing)?|day|talk|talks|programme|program|event|"
    r"ceremony|fest(?:ival)?|expo|exhibition|session|orientation|induction|"
    r"convocation|inauguration|competition|tournament|webinar|lectures?|training|"
    r"course|awareness|rally|meetup|celebration|screening|campaign)\b",
    re.IGNORECASE,
)


def _load_universe(conn):
    """Per-activity (id, department, period, stakeholder) plus category codes.

    Uses the exact same read-time normalisation as the public analytics so
    counts always reconcile with the dashboards.
    """
    resolver = PeriodResolver(conn=conn)
    rows = conn.execute(
        """SELECT a.id, m.department_display, m.stakeholder_display
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
    ).fetchall()
    items = [
        {"id": row["id"],
         "department": normalize_department(row["department_display"]),
         "period": resolver.period_for(row["id"]),
         "stakeholder": row["stakeholder_display"]}
        for row in rows
    ]
    codes = {}
    for row in conn.execute(
            "SELECT ac.activity_id AS aid, c.code FROM activity_categories ac "
            "JOIN categories c ON c.id = ac.category_id").fetchall():
        codes.setdefault(row["aid"], set()).add(row["code"])
    return items, codes


def _satisfies(item, codes, filters):
    periods = filters.get("periods")
    if periods and item["period"] not in periods:
        return False
    department = filters.get("department")
    if department and department not in item["department"].split("; "):
        return False
    category = filters.get("category")
    if category and category[0] not in codes.get(item["id"], set()):
        return False
    dimension = filters.get("dimension")
    if dimension == "general" and item["department"] != GENERAL_NAME:
        return False
    if dimension == "departmental" and item["department"] == GENERAL_NAME:
        return False
    stakeholder = filters.get("stakeholder")
    if stakeholder and stakeholder.lower() not in (item["stakeholder"] or "").lower():
        return False
    return True


def _matching_ids(items, codes, filters):
    return [item["id"] for item in items if _satisfies(item, codes, filters)]


def _fetch_public(conn, activity_ids, limit=50):
    """Public activity rows for the given ids (auditable, no internals)."""
    if not activity_ids:
        return []
    clause, params = ids_in_clause(sorted(set(activity_ids), reverse=True))
    department = department_normalized_sql()
    rows = conn.execute(
        f"""SELECT a.id, a.title, a.description, a.activity_date, a.source_url,
                   m.activity_date_text, m.academic_year, m.evidence_text,
                   {department} AS department,
                   m.stakeholder_display AS stakeholder, m.achievement_outcome
            FROM institutional_activities a
            LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
            WHERE {clause}
            ORDER BY a.activity_date DESC NULLS LAST, a.id DESC
            LIMIT ?""",
        params + [limit],
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["academic_year"] = resolve_period(
            row["academic_year"], row["activity_date"],
            row["activity_date_text"], row["evidence_text"])
        item["department"] = item["department"] or "General"
        item["categories"] = [dict(c) for c in conn.execute(
            """SELECT c.code, c.name FROM activity_categories ac
               JOIN categories c ON c.id = ac.category_id
               WHERE ac.activity_id = ? ORDER BY c.name""", (item["id"],)).fetchall()]
        item["general_category"], item["departmental_category"] = dimension_fields(
            item["department"], item["categories"])
        result.append(item)
    return result


def _criteria_list(filters):
    out = []
    if filters.get("category"):
        out.append(filters["category"][1])
    periods = filters.get("periods")
    if periods:
        for period in sorted(periods):
            out.append(PUBLIC_PERIOD_LABELS.get(period, period))
    if filters.get("department"):
        out.append(filters["department"])
    if filters.get("stakeholder"):
        out.append(filters["stakeholder"])
    dimension = filters.get("dimension")
    if dimension == "general":
        out.append("General / institution-wide")
    elif dimension == "departmental":
        out.append("Departmental")
    if filters.get("activity_name"):
        out.append(filters["activity_name"])
    return out


def _subject(filters):
    if filters.get("category"):
        return filters["category"][1].lower()
    return "activities"


def _context_suffix(filters):
    bits = []
    if filters.get("department"):
        bits.append(f"in {filters['department']}")
    if filters.get("stakeholder"):
        bits.append(f"for {filters['stakeholder']}")
    suffix = (" " + " ".join(bits)) if bits else ""
    prefix = filters.get("dimension") == "general" and " (institution-wide)" or ""
    return suffix + prefix


def _grouped_counts(plan, items, codes, include_before=False):
    """Return (counts dict, ordered key list) for the plan's group axis."""
    group = plan["group_by"]
    filters = plan["filters"]
    if group == "year":
        order = list(PUBLIC_PERIODS) + ([BEFORE_2021] if include_before else [])
        counts = {period: 0 for period in order}
        for item in items:
            if not _satisfies(item, codes, filters):
                continue
            counts[item["period"]] = counts.get(item["period"], 0) + 1
        return counts, order
    if group == "department":
        order = list(PUBLIC_DEPARTMENTS)
        counts = {name: 0 for name in order}
        for item in items:
            if not _satisfies(item, codes, filters):
                continue
            for part in item["department"].split("; "):
                if part in counts:
                    counts[part] = counts.get(part, 0) + 1
        return counts, order
    # category cohort
    counts = {}
    for item in items:
        if not _satisfies(item, codes, filters):
            continue
        for code in (codes.get(item["id"], set()) & PUBLIC_CATEGORY_CODES):
            counts[code] = counts.get(code, 0) + 1
    return counts, list(counts)


def _display_label(group, key):
    if group == "year":
        return PUBLIC_PERIOD_LABELS.get(key, key)
    if group == "category":
        return CATEGORY_PUBLIC_NAMES.get(key, key)
    return key


def _display_rows(plan, counts, order):
    group = plan["group_by"]
    return [{"label": _display_label(group, key), "value": counts[key]}
            for key in order]


def _comparison_rows(plan, counts, order):
    group = plan["group_by"]
    if group == "year":
        return [{"academic_year": period, "activity_count": counts.get(period, 0)}
                for period in PUBLIC_PERIODS]
    if group == "category":
        return [{"category": _display_label("category", code), "activity_count": count}
                for code, count in sorted(counts.items(),
                                          key=lambda pair: (-pair[1], pair[0]))]
    ordered = sorted(PUBLIC_DEPARTMENTS,
                     key=lambda name: (counts.get(name, 0), name), reverse=True)
    return [{"department": name, "activity_count": counts.get(name, 0)}
            for name in ordered]


def _chart(rows):
    return {"data": [{"label": row["label"], "value": row["value"]} for row in rows]}


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _execute_retrieve(plan, base, conn, universe):
    items, codes = universe
    ids = _matching_ids(items, codes, plan["filters"])
    count = len(ids)
    if count == 0:
        return {**base, "status": STATUS_ZERO, "answer": ZERO_MESSAGE,
                "count": 0, "activities": []}
    activities = _fetch_public(conn, ids)
    noun = "activity" if count == 1 else "activities"
    if plan["kind"] == KIND_COUNT:
        answer = f"{count} matching {noun} found."
    else:
        answer = f"Found {count} matching {noun}."
    return {**base, "status": STATUS_ANSWER, "answer": answer, "count": count,
            "activities": activities}


def _execute_detail(plan, base, conn, universe):
    name = plan["filters"]["activity_name"]
    candidates = [name.lower()]
    words = name.split()
    if len(words) > 1 and _NOUN_TRIM.fullmatch(words[-1]):
        candidates.append(" ".join(words[:-1]).lower())
    ids = []
    rows = conn.execute(
        """SELECT a.id, a.title, a.description, m.activity_date_text
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
    ).fetchall()
    for row in rows:
        haystack = " ".join(filter(None, (
            row["title"], row["description"], row["activity_date_text"]
        ))).lower()
        if any(needle and needle in haystack for needle in candidates):
            ids.append(row["id"])
    count = len(ids)
    if count == 0:
        return {**base, "status": STATUS_ZERO, "answer": ZERO_MESSAGE,
                "count": 0, "activities": []}
    activities = _fetch_public(conn, ids)
    detail = activities[0]
    noun = "activity" if count == 1 else "activities"
    answer = f"Here are the details for the {name} ({count} matching {noun})."
    return {**base, "status": STATUS_ANSWER, "answer": answer, "count": count,
            "activities": activities, "detail": detail}


def _execute_compare(plan, base, conn, universe):
    items, codes = universe
    results = []
    for side in plan["compare"]:
        ids = _matching_ids(items, codes, side["filters"])
        results.append({"label": side["label"], "count": len(ids)})
    left, right = results
    lc, rc = left["count"], right["count"]
    if lc == rc:
        answer = f"{left['label']} and {right['label']} both have {lc} matching activities."
    elif lc > rc:
        answer = f"{left['label']} has more activities than {right['label']} ({lc} vs {rc})."
    else:
        answer = f"{right['label']} has more activities than {left['label']} ({rc} vs {lc})."
    comparison = [{"entity": side["label"], "activity_count": side["count"]}
                  for side in results]
    chart_rows = [{"label": side["label"], "value": side["count"]}
                  for side in results]
    return {**base, "status": STATUS_ANSWER, "answer": answer,
            "count": max(lc, rc), "activities": [],
            "rows": chart_rows, "chart": _chart(chart_rows),
            "comparison": comparison, "criteria": [left["label"], right["label"]]}


def _execute_grouped(plan, base, conn, universe, include_before=False):
    items, codes = universe
    group = plan["group_by"]
    kind = plan["kind"]
    counts, order = _grouped_counts(plan, items, codes, include_before)

    axis = {"year": "period", "department": "department", "category": "category"}.get(group, group)

    if kind in (KIND_HIGHEST, KIND_LOWEST):
        active = [key for key in order if counts.get(key, 0) > 0]
        if not active:
            return {**base, "status": STATUS_ZERO, "answer": ZERO_MESSAGE,
                    "count": 0, "activities": []}
        reverse = kind == KIND_HIGHEST
        ranked = sorted(active, key=lambda key: (counts[key], key), reverse=reverse)
        winner = ranked[0]
        winner_count = counts[winner]
        verdict = "most" if kind == KIND_HIGHEST else "fewest"
        noun = "activity" if winner_count == 1 else "activities"
        winner_filters = dict(plan["filters"])
        if group == "year":
            winner_filters["periods"] = frozenset({winner})
            label = _display_label("year", winner)
        elif group == "department":
            winner_filters["department"] = winner
            label = winner
        else:
            winner_filters["category"] = (winner, _display_label("category", winner))
            label = _display_label("category", winner)
        answer = (f"{label} had the {verdict} {_subject(plan['filters'])} "
                  f"with {winner_count} matching {noun}.{_context_suffix(plan['filters'])}")
        ids = _matching_ids(items, codes, winner_filters)
        activities = _fetch_public(conn, ids)

        active_sorted = sorted(active, key=lambda key: (counts[key], key), reverse=reverse)
        rows = _display_rows(plan, counts, active_sorted)
        return {**base, "status": STATUS_ANSWER, "answer": answer,
                "count": winner_count, "activities": activities,
                "rows": rows, "chart": _chart(rows),
                "comparison": _comparison_rows(plan, counts, order)}

    if kind == KIND_RANKING:
        sort = sorted(order, key=lambda key: (counts[key], key), reverse=True)
        rows = _display_rows(plan, counts, sort)
        shown = "; ".join(f"{row['label']} ({row['value']})" for row in rows[:5])
        answer = f"{_subject(plan['filters']).capitalize()} by {axis}: {shown}."
        return {**base, "status": STATUS_ANSWER, "answer": answer, "count": None,
                "activities": [], "rows": rows, "chart": _chart(rows),
                "comparison": _comparison_rows(plan, counts, order)}

    if kind == KIND_TOP_N:
        limit = plan["limit"] or 5
        active = [key for key in order if counts.get(key, 0) > 0]
        picked = sorted(active, key=lambda key: (counts[key], key), reverse=True)[:limit]
        rows = _display_rows(plan, counts, picked)
        shown = "; ".join(f"{row['label']} ({row['value']})" for row in rows)
        answer = f"Top {len(rows)} {axis}s by {_subject(plan['filters'])}: {shown}."
        return {**base, "status": STATUS_ANSWER, "answer": answer, "count": None,
                "activities": [], "rows": rows, "chart": _chart(rows),
                "comparison": _comparison_rows(plan, counts, order)}

    if kind == KIND_TREND:
        rows = _display_rows(plan, counts, order)
        shown = "; ".join(f"{row['label']} ({row['value']})" for row in rows)
        answer = f"{_subject(plan['filters']).capitalize()} by period: {shown}."
        return {**base, "status": STATUS_ANSWER, "answer": answer, "count": None,
                "activities": [], "rows": rows, "chart": _chart(rows),
                "comparison": _comparison_rows(plan, counts, order)}

    if kind == KIND_BREAKDOWN:
        nonzero = [key for key in order if counts.get(key, 0) > 0]
        shown_order = sorted(nonzero, key=lambda key: (counts[key], key), reverse=True)
        rows = _display_rows(plan, counts, shown_order)
        shown = "; ".join(f"{row['label']} ({row['value']})" for row in rows[:5])
        answer = f"{_subject(plan['filters']).capitalize()} by {axis}: {shown}."
        return {**base, "status": STATUS_ANSWER, "answer": answer, "count": None,
                "activities": [], "rows": rows, "chart": _chart(rows),
                "comparison": _comparison_rows(plan, counts, order)}

    return {**base, "status": STATUS_UNSUPPORTED, "answer": OUT_OF_SCOPE_MESSAGE,
            "count": 0, "activities": []}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def execute(plan, question, conn):
    """Run an interpreted plan and return the public response contract."""
    base = {"question": question, "criteria": _criteria_list(plan["filters"])}

    if plan["kind"] == KIND_CLARIFICATION:
        return {**base, "status": STATUS_CLARIFICATION, "answer": plan["message"],
                "count": 0, "activities": []}
    if plan["kind"] == KIND_UNSUPPORTED:
        return {**base, "status": STATUS_UNSUPPORTED, "answer": OUT_OF_SCOPE_MESSAGE,
                "count": 0, "activities": []}

    universe = _load_universe(conn)

    if plan["kind"] == KIND_DETAIL:
        return _execute_detail(plan, base, conn, universe)
    if plan["kind"] == KIND_COMPARE:
        return _execute_compare(plan, base, conn, universe)
    if plan["kind"] in (KIND_COUNT, KIND_LIST):
        return _execute_retrieve(plan, base, conn, universe)
    if plan["kind"] == KIND_TREND:
        return _execute_grouped(plan, base, conn, universe, include_before=True)
    return _execute_grouped(plan, base, conn, universe, include_before=False)