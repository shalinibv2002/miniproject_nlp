"""Clean, public read endpoints for final institutional activities."""

import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Blueprint, request

from backend.database.init_db import get_connection
from backend.database.category_catalog import (
    DEPARTMENTAL_CATEGORIES, DEPARTMENTAL_CATEGORY_CODES, GENERAL_CATEGORIES,
    PUBLIC_CATEGORY_CODES, dimension_fields, public_category_name,
    resolve_departmental_category, resolve_general_category,
)
from backend.database.department_catalog import (
    GENERAL_NAME, PUBLIC_DEPARTMENTS, department_ids_clause,
    department_normalized_sql, normalize_department,
)
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, PeriodResolver, ids_in_clause,
    normalize_period, resolve_period,
)
from backend.routes.helpers import error_response, ok, paginate_args, page_response

bp = Blueprint("activities", __name__, url_prefix="/api")

PUBLIC_YEARS = ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
SORT_COLUMNS = {
    "date": "a.activity_date", "activity_date": "a.activity_date",
    "title": "a.title COLLATE NOCASE", "academic_year": "m.academic_year",
}
DEPARTMENT_NORM_SQL = department_normalized_sql()


def _public_row(row):
    """Project a database row to the deliberately small public contract.

    ``academic_year`` is the read-time resolved period (a short public key or
    ``Before 2021``) so the public UI never sees "Not available".
    """
    department = normalize_department(row["department"])
    return {
        "id": row["id"], "title": row["title"], "description": row["description"],
        "activity_date": row["activity_date"], "activity_date_text": row["activity_date_text"],
        "academic_year": resolve_period(
            row["academic_year"], row["activity_date"],
            row["activity_date_text"], row["evidence_text"]),
        "department": department,
        "stakeholder": row["stakeholder"] or "Students",
        "achievement_outcome": row["achievement_outcome"], "categories": [],
        "source_url": row["source_url"],
    }


def _categories(conn, activity_id):
    return [
        {"code": row["code"], "name": public_category_name(row["code"])}
        for row in conn.execute(
            """SELECT c.code FROM activity_categories ac
               JOIN categories c ON c.id = ac.category_id
               WHERE ac.activity_id = ? ORDER BY c.code""",
            (activity_id,),
        ).fetchall()
    ]


def _source_urls(conn, activity_id, primary_url):
    urls = [row["source_url"] for row in conn.execute(
        "SELECT source_url FROM activity_sources WHERE activity_id = ? ORDER BY source_url",
        (activity_id,),
    ).fetchall()]
    if primary_url and primary_url not in urls:
        urls.insert(0, primary_url)
    return urls


def _hydrate(conn, rows):
    items = []
    for row in rows:
        item = _public_row(row)
        item["categories"] = _categories(conn, item["id"])
        item["general_category"], item["departmental_category"] = dimension_fields(
            item["department"], item["categories"])
        items.append(item)
    return items


def _category_codes(conn, value):
    """Resolve a free-text category filter to canonical public category codes.

    Accepts a public code (``WORKSHOP``), a public display name (``Workshops``),
    a stored/legacy code, or a stored name so drill-down links, stored names,
    and hand-typed queries all resolve to the same activities.  Unknown values
    return an empty set (the caller turns that into a zero-row filter).
    """
    entered = (value or "").strip()
    if not entered:
        return set()
    upper = entered.upper()
    if upper in PUBLIC_CATEGORY_CODES:
        return {upper}
    codes = set()
    for resolver in (resolve_general_category, resolve_departmental_category):
        code = resolver(entered)
        if code:
            codes.add(code)
    if codes:
        return codes
    row = conn.execute(
        "SELECT code FROM categories WHERE UPPER(code) = ? OR LOWER(name) = LOWER(?)",
        (upper, entered),
    ).fetchone()
    if row:
        codes.add(row["code"])
    return codes


def _filters(conn, include_search=True):
    """Build public filters. Metadata is authoritative for final fields.

    ``academic_year`` accepts short keys (``2021-22``), long labels
    (``2021-2022``), the ``Before 2021`` bucket, and the legacy
    ``Not available`` spelling (which keeps its historical NULL semantics).
    The ``period`` argument is accepted as an alias so this endpoint matches
    the other public analytics endpoints.
    Period filtering always uses the resolved activity id set so recovered
    rows appear in the same period the public UI presents them under.
    """
    where, params = [], []
    academic_year = request.args.get("academic_year") or request.args.get("year") or request.args.get("period")
    if academic_year:
        if academic_year == "Not available":
            where.append("m.academic_year IS NULL")
        else:
            period = normalize_period(academic_year, default=None)
            if period is None:
                raise ValueError("academic_year must be a supported academic year or 'Before 2021'")
            clause, period_params = ids_in_clause(PeriodResolver(conn=conn).ids_for(period))
            where.append(clause)
            params.extend(period_params)

    category = (request.args.get("category") or "").strip()
    if category:
        codes = _category_codes(conn, category)
        if not codes:
            where.append("1 = 0")
        else:
            marks = ", ".join("?" for _ in codes)
            where.append(f"""EXISTS (SELECT 1 FROM activity_categories ac
                          JOIN categories c ON c.id = ac.category_id
                          WHERE ac.activity_id = a.id AND UPPER(c.code) IN ({marks}))""")
            params.extend(sorted(codes))

    department = (request.args.get("department") or "").strip()
    if department:
        clause, department_params = department_ids_clause(conn, department)
        where.append(clause)
        params.extend(department_params)

    stakeholder = (request.args.get("stakeholder") or "").strip()
    if stakeholder:
        where.append("COALESCE(m.stakeholder_display, 'Students') = ?")
        params.append(stakeholder)

    general_category = (request.args.get("general_category") or "").strip()
    if general_category:
        code = resolve_general_category(general_category)
        if not code:
            raise ValueError("general_category must be a supported General Category")
        where.append(f"""{DEPARTMENT_NORM_SQL} = 'General' AND
                      EXISTS (SELECT 1 FROM activity_categories gac
                             JOIN categories gc ON gc.id = gac.category_id
                             WHERE gac.activity_id = a.id AND UPPER(gc.code) = ?)""")
        params.append(code)

    departmental_category = (request.args.get("departmental_category") or "").strip()
    if departmental_category:
        code = resolve_departmental_category(departmental_category)
        if not code:
            raise ValueError("departmental_category must be a supported Departmental Category")
        where.append(f"""{DEPARTMENT_NORM_SQL} != 'General' AND
                      EXISTS (SELECT 1 FROM activity_categories dac
                             JOIN categories dc ON dc.id = dac.category_id
                             WHERE dac.activity_id = a.id AND UPPER(dc.code) = ?)""")
        params.append(code)

    for arg, operator in (("date_from", ">="), ("from_date", ">="), ("date_to", "<="), ("to_date", "<=")):
        value = request.args.get(arg)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{arg} must be an ISO date (YYYY-MM-DD)") from exc
            where.append(f"a.activity_date {operator} ?")
            params.append(value)

    if include_search:
        search = (request.args.get("q") or request.args.get("search") or "").strip()
        if search:
            like = f"%{search}%"
            where.append("""(a.title LIKE ? COLLATE NOCASE OR a.description LIKE ? COLLATE NOCASE
                          OR m.stakeholder_display LIKE ? COLLATE NOCASE
                          OR m.department_display LIKE ? COLLATE NOCASE
                          OR m.achievement_outcome LIKE ? COLLATE NOCASE
                          OR m.activity_date_text LIKE ? COLLATE NOCASE
                          OR m.evidence_text LIKE ? COLLATE NOCASE)""")
            params.extend([like] * 7)
    return where, params


def _order_by():
    sort = (request.args.get("sort") or "date").lower()
    if sort not in SORT_COLUMNS:
        raise ValueError("sort must be one of: date, activity_date, title, academic_year")
    direction = (request.args.get("order") or "desc").lower()
    if direction not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'")
    return f"{SORT_COLUMNS[sort]} {direction.upper()} NULLS LAST, a.id {direction.upper()}"


def _base_select():
    return f"""SELECT a.id, a.title, a.description, a.activity_date, a.source_url,
                      m.activity_date_text, m.academic_year, m.evidence_text,
                      {DEPARTMENT_NORM_SQL} AS department,
                      m.stakeholder_display AS stakeholder, m.achievement_outcome
               FROM institutional_activities a
               LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""


@bp.get("/activities")
def list_activities():
    conn = get_connection()
    try:
        offset, page_size = paginate_args()
        where, params = _filters(conn)
        where_sql = "WHERE " + " AND ".join(where) if where else ""
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM institutional_activities a "
            f"LEFT JOIN final_activity_metadata m ON m.activity_id=a.id {where_sql}", params
        ).fetchone()["c"]
        rows = conn.execute(
            f"{_base_select()} {where_sql} ORDER BY {_order_by()} LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        page = offset // page_size + 1
        return ok(page_response(_hydrate(conn, rows), total, page, page_size))
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/activities/<int:activity_id>")
def get_activity(activity_id):
    conn = get_connection()
    try:
        row = conn.execute(f"{_base_select()} WHERE a.id = ?", (activity_id,)).fetchone()
        if not row:
            return error_response("activity not found", 404)
        item = _public_row(row)
        item["categories"] = _categories(conn, activity_id)
        item["general_category"], item["departmental_category"] = dimension_fields(
            item["department"], item["categories"])
        item["official_sources"] = _source_urls(conn, activity_id, item["source_url"])
        if not item["source_url"] and item["official_sources"]:
            item["source_url"] = item["official_sources"][0]
        return ok(item)
    finally:
        conn.close()


@bp.get("/years")
def list_years():
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT academic_year, COUNT(*) AS activity_count FROM final_activity_metadata
               WHERE academic_year IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
               GROUP BY academic_year"""
        ).fetchall()
        counts = {row["academic_year"]: row["activity_count"] for row in rows}
        return ok([{"academic_year": year, "activity_count": counts.get(year, 0)} for year in PUBLIC_YEARS])
    finally:
        conn.close()


@bp.get("/departments")
def list_departments():
    conn = get_connection()
    try:
        # Exactly the 14 public departments.  Institution-wide ("General")
        # activities belong to the General view and are never listed here;
        # out-of-master stored values (e.g. historical "Physics" rows) are
        # preserved in the data but never presented as a department option.
        # Multi-department rows count against every canonical department they
        # name (catalog aliases apply per part).  An optional ``period``
        # restricts the counts to one resolved academic period so the
        # drill-down keeps the user's filter through every step.
        counts = {name: 0 for name in PUBLIC_DEPARTMENTS}
        sql = """SELECT m.department_display FROM institutional_activities a
                 LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
        params = []
        period = (request.args.get("period") or request.args.get("academic_year") or "").strip()
        if period:
            clause, period_params = ids_in_clause(PeriodResolver(conn=conn).ids_for(period))
            sql += f" WHERE {clause}"
            params = list(period_params)
        rows = conn.execute(sql, params).fetchall()
        for row in rows:
            normalised = normalize_department(row["department_display"])
            if normalised == GENERAL_NAME:
                continue
            for part in normalised.split("; "):
                if part in counts:
                    counts[part] += 1
        return ok([{"department": name, "activity_count": counts[name]}
                   for name in PUBLIC_DEPARTMENTS])
    finally:
        conn.close()


@bp.get("/categories")
def list_categories():
    """The public category codes (20 General; the 7 Departmental are a subset).

    Legacy codes (Technical Festival, STTP, Symposium) and Alumni are excluded
    from every public category list.  Accepts optional ``period`` and
    ``department`` filters so the counts match the drill-down, plus
    ``general_category``/``departmental_category`` to narrow to one dimension.
    Public display names are returned instead of stored names.
    """
    conn = get_connection()
    try:
        period_clause, period_params = _category_period_clause(conn)
        placeholders = ", ".join("?" for _ in PUBLIC_CATEGORY_CODES)
        where = [f"c.code IN ({placeholders})"]
        params = list(sorted(PUBLIC_CATEGORY_CODES))

        department = (request.args.get("department") or "").strip()
        if department:
            clause, department_params = department_ids_clause(conn, department)
            where.append(clause)
            params.extend(department_params)

        general_category = (request.args.get("general_category") or "").strip()
        if general_category:
            code = resolve_general_category(general_category)
            if not code:
                raise ValueError("general_category must be a supported General Category")
            where.append(f"{DEPARTMENT_NORM_SQL} = 'General'")
            where.append("UPPER(c.code) = ?")
            params.append(code)

        departmental_category = (request.args.get("departmental_category") or "").strip()
        if departmental_category:
            code = resolve_departmental_category(departmental_category)
            if not code:
                raise ValueError("departmental_category must be a supported Departmental Category")
            where.append(f"{DEPARTMENT_NORM_SQL} != 'General'")
            where.append("UPPER(c.code) = ?")
            params.append(code)

        rows = conn.execute(
            f"""SELECT c.code,
                       COUNT(DISTINCT CASE WHEN {period_clause} THEN ac.activity_id END) AS activity_count
                FROM categories c
                LEFT JOIN activity_categories ac ON ac.category_id = c.id
                LEFT JOIN institutional_activities a ON a.id = ac.activity_id
                LEFT JOIN final_activity_metadata m ON m.activity_id = ac.activity_id
                WHERE {' AND '.join(where)}
                GROUP BY c.id, c.code""",
            list(period_params) + params,
        ).fetchall()
        counts = {row["code"]: row["activity_count"] or 0 for row in rows}
        items = [{"code": code, "name": public_category_name(code),
                  "activity_count": counts.get(code, 0)}
                 for code in sorted(PUBLIC_CATEGORY_CODES)]
        items.sort(key=lambda item: (-item["activity_count"], item["name"]))
        return ok(items)
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/general-categories")
def list_general_categories():
    """The 20 General Category options with institution-wide activity counts.

    Accepts an optional ``period`` (short key, ``Before 2021``, or display
    label) to restrict the counts to a single academic period.
    """
    conn = get_connection()
    try:
        period_clause, period_params = _category_period_clause(conn)
        rows = conn.execute(
            f"""SELECT c.code,
                       COUNT(DISTINCT CASE WHEN {DEPARTMENT_NORM_SQL} = 'General'
                                      AND {period_clause}
                                      THEN ac.activity_id END) AS activity_count
               FROM categories c
               LEFT JOIN activity_categories ac ON ac.category_id = c.id
               LEFT JOIN final_activity_metadata m ON m.activity_id = ac.activity_id
               GROUP BY c.id, c.code""",
            tuple(period_params),
        ).fetchall()
        counts = {row["code"]: row["activity_count"] or 0 for row in rows}
        items = [{"code": item["code"], "name": item["name"],
                  "activity_count": counts.get(item["code"], 0)}
                 for item in GENERAL_CATEGORIES]
        items.sort(key=lambda item: (-item["activity_count"], item["name"]))
        if request.args.get("period"):
            items = [item for item in items if item["activity_count"] > 0]
        return ok(items)
    finally:
        conn.close()


def _category_period_clause(conn):
    """Return (sql_expr, params) restricting category counts to one period.

    Produces ``ac.activity_id IN (?, ...)`` (chunked under SQLite's bound
    parameter limit), ``1 = 0`` for an empty bucket, or ``1 = 1`` for no
    period filter.
    """
    period = (request.args.get("period") or "").strip()
    if not period:
        return "1 = 1", []
    ids = sorted(PeriodResolver(conn=conn).ids_for(period))
    if not ids:
        return "1 = 0", []
    clauses, params = [], []
    for start in range(0, len(ids), 900):
        part = ids[start:start + 900]
        marks = ", ".join("?" for _ in part)
        clauses.append(f"ac.activity_id IN ({marks})")
        params.extend(part)
    return "(" + " OR ".join(clauses) + ")", params


@bp.get("/departmental-categories")
def list_departmental_categories():
    """The seven Departmental Category options.

    With no ``department`` the global departmental counts are returned.  For a
    real department only the categories with data for that department are
    returned (data-driven options); ``department=General`` returns an empty
    list.  An optional ``period`` restricts counts to one academic period.
    """
    conn = get_connection()
    try:
        department = (request.args.get("department") or "").strip()
        canonical = normalize_department(department) if department else None
        period_clause, period_params = _category_period_clause(conn)

        def items_from(counts):
            out = [{"code": item["code"], "name": item["name"],
                    "activity_count": counts.get(item["code"], 0)}
                   for item in DEPARTMENTAL_CATEGORIES]
            out.sort(key=lambda item: (-item["activity_count"], item["name"]))
            return out

        if canonical == "General":
            return ok([])
        if canonical:
            placeholders = ", ".join("?" for _ in DEPARTMENTAL_CATEGORY_CODES)
            department_clause, department_params = department_ids_clause(conn, canonical)
            rows = conn.execute(
                f"""SELECT c.code, COUNT(DISTINCT a.id) AS activity_count
                    FROM institutional_activities a
                    LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
                    LEFT JOIN activity_categories ac ON ac.activity_id = a.id
                    LEFT JOIN categories c ON c.id = ac.category_id
                    WHERE {department_clause}
                      AND c.code IN ({placeholders})
                      AND {period_clause}
                    GROUP BY c.code""",
                tuple(department_params) + tuple(DEPARTMENTAL_CATEGORY_CODES) + tuple(period_params),
            ).fetchall()
            counts = {row["code"]: row["activity_count"] for row in rows}
            items = items_from(counts)
            return ok([item for item in items if item["activity_count"] > 0])
        rows = conn.execute(
            f"""SELECT c.code,
                       COUNT(DISTINCT CASE WHEN {DEPARTMENT_NORM_SQL} != 'General'
                                      AND {period_clause}
                                      THEN ac.activity_id END) AS activity_count
               FROM categories c
               LEFT JOIN activity_categories ac ON ac.category_id = c.id
               LEFT JOIN final_activity_metadata m ON m.activity_id = ac.activity_id
               GROUP BY c.id, c.code""",
            tuple(period_params),
        ).fetchall()
        counts = {row["code"]: row["activity_count"] or 0 for row in rows}
        items = items_from(counts)
        if request.args.get("period"):
            items = [item for item in items if item["activity_count"] > 0]
        return ok(items)
    finally:
        conn.close()


@bp.get("/stakeholders")
def list_stakeholders():
    """The distinct public stakeholder values with activity counts.

    Supports optional ``period``, ``department``, ``category``,
    ``general_category`` and ``departmental_category`` filters so the
    drill-down can show period- and scope-correct stakeholder counts.
    """
    conn = get_connection()
    try:
        where, params = [], []
        period = (request.args.get("period") or request.args.get("academic_year") or "").strip()
        if period:
            clause, period_params = ids_in_clause(PeriodResolver(conn=conn).ids_for(period))
            where.append(clause)
            params.extend(period_params)
        department = (request.args.get("department") or "").strip()
        if department:
            clause, department_params = department_ids_clause(conn, department)
            where.append(clause)
            params.extend(department_params)
        general_category = (request.args.get("general_category") or "").strip()
        if general_category:
            code = resolve_general_category(general_category)
            if not code:
                raise ValueError("general_category must be a supported General Category")
            where.append(f"""{DEPARTMENT_NORM_SQL} = 'General' AND
                          EXISTS (SELECT 1 FROM activity_categories gac
                                 JOIN categories gc ON gc.id = gac.category_id
                                 WHERE gac.activity_id = a.id AND UPPER(gc.code) = ?)""")
            params.append(code)
        departmental_category = (request.args.get("departmental_category") or "").strip()
        if departmental_category:
            code = resolve_departmental_category(departmental_category)
            if not code:
                raise ValueError("departmental_category must be a supported Departmental Category")
            where.append(f"""{DEPARTMENT_NORM_SQL} != 'General' AND
                          EXISTS (SELECT 1 FROM activity_categories dac
                                 JOIN categories dc ON dc.id = dac.category_id
                                 WHERE dac.activity_id = a.id AND UPPER(dc.code) = ?)""")
            params.append(code)
        category = (request.args.get("category") or "").strip()
        if category:
            codes = _category_codes(conn, category)
            if not codes:
                where.append("1 = 0")
            else:
                marks = ", ".join("?" for _ in codes)
                where.append(f"""EXISTS (SELECT 1 FROM activity_categories sac
                              JOIN categories sc ON sc.id = sac.category_id
                              WHERE sac.activity_id = a.id AND UPPER(sc.code) IN ({marks}))""")
                params.extend(sorted(codes))
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""
        rows = conn.execute(
            f"""SELECT COALESCE(m.stakeholder_display, 'Students') AS stakeholder,
                       COUNT(*) AS activity_count
                FROM institutional_activities a
                LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
                {where_sql}
                GROUP BY COALESCE(m.stakeholder_display, 'Students')
                ORDER BY activity_count DESC, stakeholder""",
            params,
        ).fetchall()
        return ok([dict(row) for row in rows])
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()


@bp.get("/search")
def search_activities():
    q = (request.args.get("q") or "").strip()
    if not q:
        return error_response("missing 'q' query parameter", 400)
    conn = get_connection()
    try:
        where, params = _filters(conn)
        rows = conn.execute(
            f"{_base_select()} WHERE {' AND '.join(where)} ORDER BY {_order_by()} LIMIT 50", params
        ).fetchall()
        return ok({"data": _hydrate(conn, rows), "query": q, "status": "ok"})
    except ValueError as exc:
        return error_response(str(exc), 400)
    finally:
        conn.close()
