"""Contains admin services for the admin dashboard.

Covers:
  * overview - counts for the admin dashboard
  * add / update / delete activities with relationship-safe metadata handling
  * management list with the same public presentations the user UI uses
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.database.normalizer import to_normalized_title
from backend.database.category_catalog import (
    DEPARTMENTAL_CATEGORIES, GENERAL_CATEGORIES,
    resolve_departmental_category, resolve_general_category,
)
from backend.database.department_catalog import (
    GENERAL_NAME, PUBLIC_DEPARTMENTS, department_ids_clause,
    department_normalized_sql, normalize_department,
)
from backend.database.period_catalog import (
    BEFORE_2021, PUBLIC_PERIODS, PeriodResolver, normalize_period,
)

DEPARTMENT_NORM_SQL = department_normalized_sql()
PUBLIC_DEPARTMENT_SET = frozenset(PUBLIC_DEPARTMENTS)
PUBLIC_PERIOD_SET = set(PUBLIC_PERIODS)

# Presentable public names for the admin form choices.
CATEGORY_NAME_BY_CODE = {
    item["code"]: item["name"]
    for item in (*GENERAL_CATEGORIES, *DEPARTMENTAL_CATEGORIES)
}

STAKEHOLDER_NAMES = (
    "Students", "Faculty", "Non-Teaching Staff", "Alumni", "Industry",
    "Parents", "Government and Agencies", "Community and Society",
)


class AdminValidationError(ValueError):
    """Raised when admin input cannot be safely persisted."""


def public_stakeholder_names():
    return list(STAKEHOLDER_NAMES)


def _stakeholder_id(conn, display):
    if not display:
        return None
    row = conn.execute(
        "SELECT id FROM stakeholders WHERE name = ? COLLATE NOCASE",
        (str(display).strip(),),
    ).fetchone()
    return row["id"] if row else None


def _category_id(conn, code):
    row = conn.execute("SELECT id FROM categories WHERE code = ?", (code,)).fetchone()
    return row["id"] if row else None


def _verified_status_id(conn):
    row = conn.execute("SELECT id FROM verification_statuses WHERE code='verified'").fetchone()
    return row["id"] if row else None


def _resolve_scope_and_department(scope, department):
    """Return the canonical department_display for a scope input.

    ``general`` maps to the institution-wide value; ``departmental`` requires
    one of the exactly-14 public departments.
    """
    scope = (scope or "general").strip().lower()
    if scope in ("general", "institution-wide", "institution_wide"):
        return GENERAL_NAME
    if scope in ("departmental", "department"):
        canonical = normalize_department(department)
        if canonical == GENERAL_NAME or canonical not in PUBLIC_DEPARTMENT_SET:
            raise AdminValidationError(
                "department must be one of the 14 public departments for a departmental activity")
        return canonical
    if department and department.strip():
        canonical = normalize_department(department)
        if canonical != GENERAL_NAME and canonical in PUBLIC_DEPARTMENT_SET:
            return canonical
    return GENERAL_NAME


def _resolve_category(scope, department_display, category_code):
    """Validate and return the single category code for the activity dimension."""
    if department_display == GENERAL_NAME:
        code = resolve_general_category(category_code)
        if not code:
            raise AdminValidationError("general category must be one of the 20 General Categories")
        return code
    code = resolve_departmental_category(category_code)
    if not code:
        raise AdminValidationError("departmental category must be one of the 7 Departmental Categories")
    return code


def _resolve_academic_year(value):
    """Short key (or None) to store: Before 2021 maps to NULL by design."""
    key = normalize_period(value)
    if not key:
        return None
    if key == BEFORE_2021:
        return None
    if key in PUBLIC_PERIOD_SET:
        return key
    return None


def _normalise_date(value):
    if not value:
        return None
    text = str(value).strip()
    try:
        from datetime import date
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise AdminValidationError("activity_date must be an ISO date (YYYY-MM-DD)") from exc


def _build_achievement(achievement_outcome, student_name, register_number):
    """Fold optional student/register details into the achievement text."""
    pieces = []
    if student_name and str(student_name).strip():
        pieces.append(f"Student Name: {str(student_name).strip()}")
    if register_number and str(register_number).strip():
        pieces.append(f"Register No. {str(register_number).strip()}")
    base = (achievement_outcome or "").strip()
    prefix = " | ".join(pieces)
    if prefix and base:
        return f"{prefix} - {base}"
    if prefix:
        return prefix
    return base or None


def overview(conn=None):
    """Admin management overview: totals, mixes, periods, categories, departments."""
    own = conn is None
    conn = conn or get_connection()
    try:
        resolver = PeriodResolver(conn=conn)
        total = conn.execute("SELECT COUNT(*) AS c FROM institutional_activities").fetchone()["c"]
        rows = conn.execute(
            "SELECT m.department_display AS dpt FROM institutional_activities a "
            "LEFT JOIN final_activity_metadata m ON m.activity_id=a.id"
        ).fetchall()
        general = sum(1 for row in rows if normalize_department(row["dpt"]) == GENERAL_NAME)
        departmental = total - general
        period_counts = {period: len(resolver.ids_for(period))
                         for period in (*PUBLIC_PERIODS, BEFORE_2021)}
        categories = list(conn.execute(
            """SELECT c.code, c.name, COUNT(DISTINCT ac.activity_id) AS activity_count
               FROM categories c
               LEFT JOIN activity_categories ac ON ac.category_id = c.id
               GROUP BY c.id ORDER BY activity_count DESC, c.code"""
        ).fetchall())
        department_counts = {name: 0 for name in PUBLIC_DEPARTMENTS}
        for row in rows:
            normalised = normalize_department(row["dpt"])
            if normalised == GENERAL_NAME:
                continue
            for part in normalised.split("; "):
                if part in department_counts:
                    department_counts[part] += 1
        attention = conn.execute(
            "SELECT COUNT(*) AS c FROM review_queue WHERE status IN ('open','in_progress')"
        ).fetchone()["c"]
        recent = list(conn.execute(
            """SELECT id, title, activity_date, source_url
               FROM institutional_activities ORDER BY id DESC LIMIT 8"""
        ).fetchall())
        return {
            "total_activities": total,
            "general_activities": general,
            "departmental_activities": departmental,
            "period_breakdown": [{"academic_year": period, "activity_count": period_counts[period]}
                                 for period in (*PUBLIC_PERIODS, BEFORE_2021)],
            "category_totals": [dict(row) for row in categories],
            "department_totals": [{"department": name, "activity_count": department_counts[name]}
                                  for name in PUBLIC_DEPARTMENTS],
            "records_requiring_attention": attention,
            "recent_activities": [dict(row) for row in recent],
        }
    finally:
        if own:
            conn.close()


def _admin_row(conn, row, resolver):
    department = normalize_department(row["department_display"])
    item = {
        "id": row["id"], "title": row["title"], "description": row["description"],
        "activity_date": row["activity_date"], "activity_date_text": row["activity_date_text"],
        "academic_year": resolver.period_for(row["id"]),
        "department": department,
        "stakeholder": row["stakeholder_display"] or "Students",
        "achievement_outcome": row["achievement_outcome"],
        "source_url": row["source_url"], "updated_at": row["updated_at"],
        "categories": [],
    }
    for category in conn.execute(
            """SELECT c.code, c.name FROM activity_categories ac
               JOIN categories c ON c.id = ac.category_id
               WHERE ac.activity_id = ? ORDER BY c.code""", (row["id"],)).fetchall():
        item["categories"].append(dict(category))
    cat_codes = {str(c["code"]).upper() for c in item["categories"]}
    item["general_category"] = None
    item["departmental_category"] = None
    if department == GENERAL_NAME:
        selected = [CATEGORY_NAME_BY_CODE[code] for code in
                    (c["code"] for c in GENERAL_CATEGORIES) if code in cat_codes]
        if selected:
            item["general_category"] = "; ".join(selected)
    else:
        selected = [CATEGORY_NAME_BY_CODE[code] for code in
                    (c["code"] for c in DEPARTMENTAL_CATEGORIES) if code in cat_codes]
        if selected:
            item["departmental_category"] = "; ".join(selected)
    return item


def list_activities(conn=None, period=None, department=None, general_category=None,
                    departmental_category=None, stakeholder=None, search=None,
                    limit=200):
    """Management list with public-style presentations plus edit/delete targets."""
    own = conn is None
    conn = conn or get_connection()
    try:
        resolver = PeriodResolver(conn=conn)
        params = []
        clauses = []
        sql = (f"SELECT a.id, a.title, a.description, a.activity_date, a.source_url, a.updated_at, "
               f"m.activity_date_text, m.academic_year, m.department_display, "
               f"m.stakeholder_display, m.achievement_outcome "
               f"FROM institutional_activities a "
               f"LEFT JOIN final_activity_metadata m ON m.activity_id=a.id")

        if period:
            ids = resolver.ids_for(period)
            if not ids:
                return []
            marks = ", ".join("?" for _ in ids)
            clauses.append(f"a.id IN ({marks})")
            params.extend(int(i) for i in ids)
        if department:
            clause, department_params = department_ids_clause(conn, department)
            clauses.append(clause)
            params.extend(department_params)
        if general_category:
            code = resolve_general_category(general_category)
            if not code:
                raise AdminValidationError("general_category must be a supported General Category")
            clauses.append(
                f"{DEPARTMENT_NORM_SQL} = 'General' AND EXISTS "
                f"(SELECT 1 FROM activity_categories gac JOIN categories gc ON gc.id=gac.category_id "
                f" WHERE gac.activity_id=a.id AND gc.code=?)")
            params.append(code)
        if departmental_category:
            code = resolve_departmental_category(departmental_category)
            if not code:
                raise AdminValidationError("departmental_category must be a supported Departmental Category")
            clauses.append(
                f"{DEPARTMENT_NORM_SQL} != 'General' AND EXISTS "
                f"(SELECT 1 FROM activity_categories dac JOIN categories dc ON dc.id=dac.category_id "
                f" WHERE dac.activity_id=a.id AND dc.code=?)")
            params.append(code)
        if stakeholder:
            clauses.append("m.stakeholder_display LIKE ?")
            params.append(f"%{str(stakeholder).strip()}%")
        if search:
            like = f"%{str(search).strip()}%"
            clauses.append(
                "(a.title LIKE ? COLLATE NOCASE OR a.description LIKE ? COLLATE NOCASE "
                "OR m.stakeholder_display LIKE ? COLLATE NOCASE)")
            params.extend([like, like, like])
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = conn.execute(f"{sql}{where} ORDER BY a.id DESC LIMIT ?",
                            params + [int(limit)]).fetchall()
        return [_admin_row(conn, row, resolver) for row in rows]
    finally:
        if own:
            conn.close()


def _activity_exists(conn, activity_id):
    return conn.execute(
        "SELECT 1 FROM institutional_activities WHERE id=?", (activity_id,)).fetchone() is not None


def add_activity(conn=None, data=None):
    """Insert a new activity with relationship-safe metadata.
    Returns the new activity id and the count of links it created."""
    data = dict(data or {})
    own = conn is None
    conn = conn or get_connection()
    try:
        title = (data.get("title") or "").strip()
        if not title:
            raise AdminValidationError("title is required")
        department_display = _resolve_scope_and_department(
            data.get("scope"), data.get("department"))
        category_code = _resolve_category(
            data.get("scope"), department_display, data.get("category"))
        academic_year = _resolve_academic_year(data.get("academic_year"))
        activity_date = _normalise_date(data.get("activity_date"))
        stakeholder = (data.get("stakeholder") or "Students").strip()
        achievement = _build_achievement(
            data.get("achievement_outcome"), data.get("student_name"), data.get("register_number"))
        source_url = (data.get("source_url") or "").strip()

        cur = conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, description, activity_date, source_url,
                is_verified, verification_status_id, overall_confidence,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 1, ?, 1.0, datetime('now'), datetime('now'))""",
            (title, to_normalized_title(title), (data.get("description") or "").strip() or None,
             activity_date, source_url or None, _verified_status_id(conn)),
        )
        activity_id = cur.lastrowid
        conn.execute(
            """INSERT INTO final_activity_metadata
               (activity_id, activity_date_text, academic_year, department_display,
                stakeholder_display, achievement_outcome, evidence_text, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (activity_id, (data.get("activity_date_text") or "").strip() or None,
             academic_year, department_display, stakeholder,
             achievement, (data.get("description") or "").strip() or None),
        )
        links = 0
        category_id = _category_id(conn, category_code)
        if category_id:
            conn.execute(
                "INSERT OR IGNORE INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                (activity_id, category_id))
            links += 1
        if source_url:
            conn.execute(
                "INSERT INTO activity_sources (activity_id, source_url) VALUES (?, ?)",
                (activity_id, source_url))
            links += 1
        stakeholder_id = _stakeholder_id(conn, stakeholder)
        if stakeholder_id:
            conn.execute(
                "INSERT OR IGNORE INTO activity_stakeholders (activity_id, stakeholder_id) VALUES (?, ?)",
                (activity_id, stakeholder_id))
            links += 1
        conn.execute(
            """INSERT INTO review_history
               (activity_id, field_name, old_value, new_value, action, reviewer, reason)
               VALUES (?, 'activity_id', '', ?, 'edit', 'admin', 'created via admin dashboard')""",
            (activity_id, str(activity_id)))
        conn.commit()
        return activity_id, links
    finally:
        if own:
            conn.close()


def activity_detail(conn=None, activity_id=None):
    """Full record for prefilling the admin add/edit form.

    Returns the stored academic year (short key), the canonical department,
    the validated category code for the dimension, and the stakeholder display.
    """
    own = conn is None
    conn = conn or get_connection()
    try:
        row = conn.execute(
            f"SELECT a.id, a.title, a.description, a.activity_date, a.source_url, "
            f"m.activity_date_text, m.academic_year, m.department_display, "
            f"m.stakeholder_display, m.achievement_outcome "
            f"FROM institutional_activities a "
            f"LEFT JOIN final_activity_metadata m ON m.activity_id=a.id WHERE a.id=?",
            (activity_id,)).fetchone()
        if not row:
            return None
        department = normalize_department(row["department_display"])
        categories = [dict(c) for c in conn.execute(
            """SELECT c.code, c.name FROM activity_categories ac
               JOIN categories c ON c.id=ac.category_id WHERE ac.activity_id=?
               ORDER BY c.code""", (activity_id,)).fetchall()]
        codes = {str(c["code"]).upper() for c in categories}
        category_code = None
        if department == GENERAL_NAME:
            for item in GENERAL_CATEGORIES:
                if item["code"] in codes:
                    category_code = item["code"]
                    break
        else:
            for item in DEPARTMENTAL_CATEGORIES:
                if item["code"] in codes:
                    category_code = item["code"]
                    break
        return {
            "id": row["id"], "title": row["title"], "description": row["description"],
            "activity_date": row["activity_date"], "activity_date_text": row["activity_date_text"],
            "academic_year": row["academic_year"], "department": department,
            "scope": "general" if department == GENERAL_NAME else "departmental",
            "category": category_code,
            "stakeholder": row["stakeholder_display"] or "Students",
            "achievement_outcome": row["achievement_outcome"],
            "source_url": row["source_url"],
        }
    finally:
        if own:
            conn.close()


def update_activity(conn=None, activity_id=None, data=None):
    """Update an activity and its related metadata safely.
    Category/stakeholder/source link rows are reconciled to avoid duplicates."""
    data = dict(data or {})
    own = conn is None
    conn = conn or get_connection()
    try:
        if not _activity_exists(conn, activity_id):
            raise AdminValidationError("activity not found")
        title = (data.get("title") or "").strip()
        if not title:
            raise AdminValidationError("title is required")
        department_display = _resolve_scope_and_department(
            data.get("scope"), data.get("department"))
        category_code = _resolve_category(
            data.get("scope"), department_display, data.get("category"))
        academic_year = _resolve_academic_year(data.get("academic_year"))
        activity_date = _normalise_date(data.get("activity_date"))
        stakeholder = (data.get("stakeholder") or "Students").strip()
        achievement = _build_achievement(
            data.get("achievement_outcome"), data.get("student_name"), data.get("register_number"))
        source_url = (data.get("source_url") or "").strip()

        conn.execute("UPDATE institutional_activities SET "
                     "title=?, normalized_title=?, description=?, activity_date=?, "
                     "source_url=?, updated_at=datetime('now') WHERE id=?",
                     (title, to_normalized_title(title),
                      (data.get("description") or "").strip() or None,
                      activity_date, source_url or None, activity_id))
        conn.execute("UPDATE final_activity_metadata SET "
                     "academic_year=?, department_display=?, stakeholder_display=?, "
                     "achievement_outcome=?, activity_date_text=?, updated_at=datetime('now') "
                     "WHERE activity_id=?",
                     (academic_year, department_display, stakeholder, achievement,
                      (data.get("activity_date_text") or "").strip() or None, activity_id))
        conn.execute("DELETE FROM activity_categories WHERE activity_id=?", (activity_id,))
        category_id = _category_id(conn, category_code)
        if category_id:
            conn.execute(
                "INSERT OR IGNORE INTO activity_categories (activity_id, category_id) VALUES (?, ?)",
                (activity_id, category_id))
        conn.execute("DELETE FROM activity_sources WHERE activity_id=?", (activity_id,))
        if source_url:
            conn.execute(
                "INSERT INTO activity_sources (activity_id, source_url) VALUES (?, ?)",
                (activity_id, source_url))
        conn.execute("DELETE FROM activity_stakeholders WHERE activity_id=?", (activity_id,))
        stakeholder_id = _stakeholder_id(conn, stakeholder)
        if stakeholder_id:
            conn.execute(
                "INSERT OR IGNORE INTO activity_stakeholders (activity_id, stakeholder_id) VALUES (?, ?)",
                (activity_id, stakeholder_id))
        conn.execute(
            "INSERT INTO review_history (activity_id, field_name, old_value, new_value, "
            "action, reviewer, reason) VALUES (?, 'activity_id', '', ?, 'edit', 'admin', "
            "'updated via admin dashboard')",
            (activity_id, str(activity_id)))
        conn.commit()
        return activity_id
    finally:
        if own:
            conn.close()


def delete_activity(conn=None, activity_id=None):
    """Delete an activity and its related metadata.  Uses FK CASCADE for the
    child rows and explicitly cleans up duplicate_candidates (which is the one
    table without a cascade pointing back at the activity)."""
    own = conn is None
    conn = conn or get_connection()
    try:
        if not _activity_exists(conn, activity_id):
            raise AdminValidationError("activity not found")
        conn.execute("DELETE FROM duplicate_candidates WHERE activity_id_a=? OR activity_id_b=?",
                     (activity_id, activity_id))
        conn.execute("DELETE FROM institutional_activities WHERE id=?", (activity_id,))
        conn.commit()
        return True
    finally:
        if own:
            conn.close()