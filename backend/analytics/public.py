"""Read-only analytics over the Step 6 final activity dataset."""

from backend.database.init_db import get_connection
from backend.database.category_catalog import (
    DEPARTMENTAL_CATEGORIES, DEPARTMENTAL_CATEGORY_CODES,
    GENERAL_CATEGORIES, GENERAL_CATEGORY_CODES, PUBLIC_CATEGORY_CODES,
    public_category_name,
)
from backend.database.department_catalog import (
    GENERAL_NAME, PUBLIC_DEPARTMENTS, department_normalized_sql,
    normalize_department,
)
from backend.database.period_catalog import (
    PUBLIC_PERIOD_OPTIONS, PeriodResolver,
)

PUBLIC_YEARS = ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26")
DEPARTMENT_NORM_SQL = department_normalized_sql()
PUBLIC_DEPARTMENT_SET = frozenset(PUBLIC_DEPARTMENTS)


def _connection(func):
    def wrapped(conn=None, *args, **kwargs):
        own = conn is None
        conn = conn or get_connection()
        try:
            return func(conn, *args, **kwargs)
        finally:
            if own:
                conn.close()
    return wrapped


@_connection
def yearly_counts(conn):
    rows = conn.execute("""SELECT academic_year, COUNT(*) AS activity_count FROM final_activity_metadata
                         WHERE academic_year IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
                         GROUP BY academic_year""").fetchall()
    counts = {row["academic_year"]: row["activity_count"] for row in rows}
    return [{"academic_year": year, "activity_count": counts.get(year, 0)} for year in PUBLIC_YEARS]


@_connection
def period_breakdown(conn):
    """The six public period buckets, resolved at read time.

    Unlike ``yearly_counts`` (which reports the stored academic years only),
    this counts every activity exactly once across the five public periods
    plus ``Before 2021``, using the same read-time resolution the public UI
    presents.  The six counts always sum to the total activity universe.
    """
    resolver = PeriodResolver(conn=conn)
    return [{"academic_year": period, "activity_count": len(resolver.ids_for(period))}
            for period in PUBLIC_PERIOD_OPTIONS]


@_connection
def category_summary(conn):
    """The 27 public category codes (20 General + 7 Departmental) with counts.

    Legacy codes (Technical Festival, STTP, Symposium) and Alumni are
    intentionally excluded from every public output.
    """
    placeholders = ", ".join("?" for _ in PUBLIC_CATEGORY_CODES)
    rows = conn.execute(
        f"""SELECT c.code, c.name,
                  COUNT(DISTINCT ac.activity_id) AS activity_count
         FROM categories c
         LEFT JOIN activity_categories ac ON ac.category_id = c.id
         WHERE c.code IN ({placeholders})
         GROUP BY c.id, c.code, c.name
         ORDER BY activity_count DESC, c.name COLLATE NOCASE""",
        tuple(sorted(PUBLIC_CATEGORY_CODES)),
    ).fetchall()
    items = [{"code": row["code"], "name": public_category_name(row["code"]),
              "activity_count": row["activity_count"]} for row in rows]
    items.sort(key=lambda item: (-item["activity_count"], item["name"]))
    return items


def _department_counts(conn):
    """Counts for the fixed public department master — exactly the 17.

    Institution-wide ("General") activities are intentionally NOT part of the
    department view and are skipped here (they belong to the General
    dashboard).  Multi-department rows ('; '-joined canonical names) are
    counted against every one of the 17 departments they name; zero counts
    stay visible.  Stored values are normalised part by part (catalog aliases
    apply), so rows that store an alias such as ``Architecture`` also count
    under the canonical master name ``T'SEDA (Architecture, Design,
    Planning)``.  Values outside the 17 are preserved but never presented as a
    department.
    """
    counts = {name: 0 for name in PUBLIC_DEPARTMENTS}
    rows = conn.execute(
        """SELECT m.department_display FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
    ).fetchall()
    for row in rows:
        normalised = normalize_department(row["department_display"])
        if normalised == GENERAL_NAME:
            continue
        for part in normalised.split("; "):
            if part in counts:
                counts[part] = counts.get(part, 0) + 1
    return [{"department": name, "activity_count": counts[name]}
            for name in PUBLIC_DEPARTMENTS]


@_connection
def department_summary(conn):
    return _department_counts(conn)


def _literal(value):
    return "'" + str(value).replace("'", "''") + "'"


@_connection
def general_category_summary(conn):
    """The 20 General Category options with institution-wide activity counts."""
    rows = conn.execute(
        f"""SELECT c.code,
                   COUNT(DISTINCT CASE WHEN {DEPARTMENT_NORM_SQL} = {_literal(GENERAL_NAME)}
                                  THEN ac.activity_id END) AS activity_count
            FROM categories c
            LEFT JOIN activity_categories ac ON ac.category_id = c.id
            LEFT JOIN final_activity_metadata m ON m.activity_id = ac.activity_id
            GROUP BY c.id, c.code""").fetchall()
    counts = {row["code"]: row["activity_count"] or 0 for row in rows}
    items = [{"code": item["code"], "name": item["name"],
              "activity_count": counts.get(item["code"], 0)}
             for item in GENERAL_CATEGORIES]
    items.sort(key=lambda item: (-item["activity_count"], item["name"]))
    return items


def _split_departments(value):
    return [part.strip() for part in (value or "").split(";") if part.strip()]


@_connection
def departmental_category_summary(conn):
    """Per-department activity counts across the seven Departmental Categories.

    Returns a list of ``{department, categories: [{code, name, activity_count}]}``
    ordered by total departmental activity (descending).  Only departments with
    at least one departmental classification appear.
    """
    placeholders = ", ".join("?" for _ in DEPARTMENTAL_CATEGORY_CODES)
    rows = conn.execute(
        f"""SELECT {DEPARTMENT_NORM_SQL} AS dpt, c.code, COUNT(DISTINCT a.id) AS activity_count
            FROM institutional_activities a
            LEFT JOIN final_activity_metadata m ON m.activity_id = a.id
            LEFT JOIN activity_categories ac ON ac.activity_id = a.id
            LEFT JOIN categories c ON c.id = ac.category_id
            WHERE c.code IN ({placeholders})
            GROUP BY dpt, c.code""",
        tuple(DEPARTMENTAL_CATEGORY_CODES),
    ).fetchall()
    raw = {}
    for row in rows:
        for department in _split_departments(row["dpt"]):
            if department == GENERAL_NAME:
                continue
            bucket = raw.setdefault(department, {})
            bucket[row["code"]] = bucket.get(row["code"], 0) + row["activity_count"]

    result = []
    for department, counts in raw.items():
        categories = [
            {"code": item["code"], "name": item["name"],
             "activity_count": counts.get(item["code"], 0)}
            for item in DEPARTMENTAL_CATEGORIES
        ]
        categories = [category for category in categories if category["activity_count"] > 0]
        if not categories:
            continue
        total = sum(category["activity_count"] for category in categories)
        result.append({"department": department, "_total": total, "categories": categories})
    result.sort(key=lambda item: (-item["_total"], item["department"]))
    for item in result:
        item.pop("_total", None)
    return result


@_connection
def year_category_breakdown(conn):
    """Year (resolved period) x public category counts for stored years.

    Only the 27 public category codes are reported; legacy codes are excluded.
    ``academic_year`` here uses the stored public years ("Before 2021" rows are
    not stored, so the resolved variant lives in the dashboard-specific
    analytics).
    """
    placeholders = ", ".join("?" for _ in PUBLIC_CATEGORY_CODES)
    rows = conn.execute(
        f"""SELECT m.academic_year, c.code AS category_code,
                    COUNT(DISTINCT m.activity_id) AS activity_count
             FROM final_activity_metadata m
             JOIN activity_categories ac ON ac.activity_id = m.activity_id
             JOIN categories c ON c.id = ac.category_id
             WHERE m.academic_year IN ('2021-22','2022-23','2023-24','2024-25','2025-26')
               AND c.code IN ({placeholders})
             GROUP BY m.academic_year, c.id, c.code
             ORDER BY m.academic_year, c.code""",
        tuple(sorted(PUBLIC_CATEGORY_CODES)),
    ).fetchall()
    return [{"academic_year": row["academic_year"], "category_code": row["category_code"],
             "category": public_category_name(row["category_code"]),
             "activity_count": row["activity_count"]} for row in rows]


def _resolved_universe(conn):
    """Per-activity (id, normalised department, resolved period, category codes).

    Mirrors the exact read-time normalisation the public UI presents: periods
    are resolved the same way as ``PeriodResolver`` (so the six buckets and the
    two views always reconcile), departments use the catalog normalisation, and
    category codes come from the stored ``activity_categories`` rows.
    """
    resolver = PeriodResolver(conn=conn)
    rows = conn.execute(
        """SELECT a.id, m.department_display
           FROM institutional_activities a
           LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
    ).fetchall()
    items = [
        {"id": row["id"], "department": normalize_department(row["department_display"]),
         "period": resolver.period_for(row["id"])}
        for row in rows
    ]
    codes = {}
    for row in conn.execute(
        """SELECT ac.activity_id AS aid, c.code
           FROM activity_categories ac
           JOIN categories c ON c.id = ac.category_id"""
    ).fetchall():
        codes.setdefault(row["aid"], set()).add(row["code"])
    return items, codes


def _bucket_counts(items):
    counts = {period: 0 for period in PUBLIC_PERIOD_OPTIONS}
    for item in items:
        counts[item["period"]] = counts.get(item["period"], 0) + 1
    return counts


def _period_rows(bucket_counts):
    return [{"academic_year": period, "activity_count": bucket_counts[period]}
            for period in PUBLIC_PERIOD_OPTIONS]


def _category_counts(items, codes, master):
    buckets = []
    for entry in master:
        count = sum(1 for item in items if entry["code"] in codes.get(item["id"], ()))
        if count:
            buckets.append({"code": entry["code"], "name": entry["name"],
                            "activity_count": count})
    buckets.sort(key=lambda item: (-item["activity_count"], item["name"]))
    return buckets


def _year_category_rows(items, codes, allowed_codes):
    counts = {}
    for item in items:
        for code in (codes.get(item["id"], set()) & allowed_codes):
            key = (item["period"], code)
            counts[key] = counts.get(key, 0) + 1
    order = {period: index for index, period in enumerate(PUBLIC_PERIOD_OPTIONS)}
    return [
        {"academic_year": period, "category_code": code,
         "category": public_category_name(code), "activity_count": count}
        for (period, code), count in sorted(
            counts.items(), key=lambda pair: (order[pair[0][0]], pair[0][1]))
    ]


@_connection
def general_analytics(conn, general_category=None, academic_year=None):
    """The public General (institution-wide) dashboard payload.

    Institution-wide only: counts resolved-period rows whose normalised
    department is ``General``, reports the 20 General Category options, and
    never mixes in department-specific activity.  An optional General Category
    code restricts every reported series to institution-wide activities that
    carry that category.  An optional ``academic_year`` short key restricts
    every series to that single resolved period.
    """
    items, codes = _resolved_universe(conn)
    if academic_year:
        items = [item for item in items if item["period"] == academic_year]
    general = [item for item in items if item["department"] == GENERAL_NAME]
    if general_category:
        code = str(general_category).upper().strip()
        general = [item for item in general if code in codes.get(item["id"], ())]
    return {
        "total_activities": len(general),
        "periods_covered": [period for period, count in _bucket_counts(general).items()
                            if count > 0],
        "period_breakdown": _period_rows(_bucket_counts(general)),
        "general_categories": _category_counts(general, codes, GENERAL_CATEGORIES),
        "year_category_breakdown": _year_category_rows(general, codes, GENERAL_CATEGORY_CODES),
    }


@_connection
def department_analytics(conn, department=None, departmental_category=None, academic_year=None):
    """The public Department dashboard payload over the exactly-17 master.

    ``department=None`` returns the overview of all 17 departments (General and
    out-of-master values are excluded).
    Giving one canonical department name returns that department alone.  An
    optional Departmental Category code restricts every reported series to
    department activities carrying that category.  An optional ``academic_year``
    short key restricts every series to that single resolved period.
    """
    requested = normalize_department(department) if department else None
    if requested == GENERAL_NAME or (requested is not None and requested not in PUBLIC_DEPARTMENT_SET):
        raise ValueError("department must be one of the 17 public departments")

    items, codes = _resolved_universe(conn)
    if academic_year:
        items = [item for item in items if item["period"] == academic_year]

    def belongs(item):
        parts = item["department"].split("; ")
        if requested is not None:
            return requested in parts
        return any(part in PUBLIC_DEPARTMENT_SET for part in parts)

    selected = [item for item in items if belongs(item)]
    if departmental_category:
        code = str(departmental_category).upper().strip()
        selected = [item for item in selected if code in codes.get(item["id"], ())]

    if requested is not None:
        return {
            "department": requested,
            "total_activities": len(selected),
            "periods_covered": [period for period, count in _bucket_counts(selected).items()
                                if count > 0],
            "period_breakdown": _period_rows(_bucket_counts(selected)),
            "departmental_categories": _category_counts(
                selected, codes, DEPARTMENTAL_CATEGORIES),
            "year_category_breakdown": _year_category_rows(
                selected, codes, DEPARTMENTAL_CATEGORY_CODES),
        }

    department_counts = {name: 0 for name in PUBLIC_DEPARTMENTS}
    for item in selected:
        for part in item["department"].split("; "):
            if part in department_counts:
                department_counts[part] += 1
    departments = [{"department": name, "activity_count": department_counts[name]}
                   for name in PUBLIC_DEPARTMENTS]
    departments.sort(key=lambda row: (-row["activity_count"], row["department"]))
    return {
        "total_activities": len(selected),
        "departments": departments,
        "period_breakdown": _period_rows(_bucket_counts(selected)),
        "departmental_categories": _category_counts(
            selected, codes, DEPARTMENTAL_CATEGORIES),
    }


@_connection
def overview(conn):
    total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]
    dates = conn.execute("SELECT MIN(activity_date) AS min_date, MAX(activity_date) AS max_date FROM institutional_activities").fetchone()
    sources = conn.execute("SELECT COUNT(DISTINCT source_url) AS c FROM activity_sources").fetchone()["c"]
    categories, departments, yearly = category_summary(conn), _department_counts(conn), yearly_counts(conn)
    general_totals = general_category_summary(conn)
    departmental_totals = departmental_category_summary(conn)
    return {"total_activities": total, "date_range": {"min": dates["min_date"], "max": dates["max_date"]},
            "distinct_categories": len([c for c in categories if c["activity_count"]]),
            "distinct_departments": len([d for d in departments if d["activity_count"]]),
            "distinct_sources": sources, "yearly_breakdown": yearly,
            "period_breakdown": period_breakdown(conn),
            "category_totals": categories, "department_totals": departments,
            "general_category_totals": [row for row in general_totals if row["activity_count"] > 0],
            "departmental_category_totals": departmental_totals}