"""Shared, read-only public department catalog.

This module is the single source of truth for the fixed public department
master and the SQL expression used to normalise
`final_activity_metadata.department_display` at read time.  The
General/Departmental dimension of an activity is derived from the normalised
department: ``General`` means institution-wide, any other value means a
specific department.

Everything here is derived from the stored display value and never writes to
the database: no schema change, no data mutation, no re-extraction.  Raw
values are intentionally preserved; only the public presentation normalises.
"""

GENERAL_NAME = "General"

# Tokens that mean "no reliably supported department" (institution-wide).
GENERAL_LOWERCASE = frozenset({
    "", "general", "institution-wide", "institution wide", "unknown",
})

# Fixed public department master — exactly the 14 academic departments.
# Every entry must always be presented (counts may be 0).  Order is the
# canonical presentation order.  General is deliberately NOT a department
# option: institution-wide activities are presented separately, and any other
# stored value (e.g. the historical "Physics" rows) stays out of the fixed
# 14-department view without ever being relabelled.
PUBLIC_DEPARTMENTS = (
    "Civil Engineering",
    "Chemistry",
    "Computer Science and Engineering",
    "Computer Science and Business Systems",
    "Computer Applications",
    "Applied Mathematics and Computational Science",
    "Artificial Intelligence",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "English",
    "Information Technology",
    "Mechanical Engineering",
    "Mechatronics",
    "T'SEDA (Architecture, Design, Planning)",
)

# lowercase stored value -> canonical public department name.  This covers the
# only aliases observed in the final dataset; already-canonical values pass
# through untouched.
DEPARTMENT_ALIASES = {
    "it": "Information Technology",
    "civil": "Civil Engineering",
    "eee": "Electrical and Electronics Engineering",
    "ece": "Electronics and Communication Engineering",
    "cse": "Computer Science and Engineering",
    "mechanical": "Mechanical Engineering",
    "mechatronics": "Mechatronics",
    "chemistry": "Chemistry",
    "physics": "Physics",
    "english": "English",
    "ca": "Computer Applications",
    "csbs": "Computer Science and Business Systems",
    "ai": "Artificial Intelligence",
    "amcs": "Applied Mathematics and Computational Science",
    "architecture": "T'SEDA (Architecture, Design, Planning)",
    "data science": "Applied Mathematics and Computational Science",
    "computer science and business system": "Computer Science and Business Systems",
    "english and humanities": "English",
}

DEPARTMENT_MASTER = (GENERAL_NAME,) + PUBLIC_DEPARTMENTS


def _sql_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def department_normalized_sql(alias="m"):
    """SQLite CASE expression mapping department_display to a canonical name."""
    expr = f"{alias}.department_display"
    general_list = ", ".join(
        _sql_literal(value) for value in sorted(GENERAL_LOWERCASE) if value
    )
    whens = "".join(
        f" WHEN {_sql_literal(key)} THEN {_sql_literal(canonical)}"
        for key, canonical in sorted(DEPARTMENT_ALIASES.items())
    )
    return (
        f"CASE WHEN {expr} IS NULL OR TRIM({expr}) = ''"
        f" OR LOWER(TRIM({expr})) IN ({general_list})"
        f" THEN {_sql_literal(GENERAL_NAME)}"
        f" ELSE CASE LOWER(TRIM({expr})){whens}"
        f" ELSE TRIM({expr}) END END"
    )


def normalize_department(value):
    """Return the canonical public department name for a stored display value.

    Returns GENERAL_NAME for institution-wide / unknown values, maps known
    aliases to the canonical master, and passes canonical values through.
    Multi-department values ('; '-joined) are normalised part by part.
    """
    if value is None:
        return GENERAL_NAME
    text = str(value).strip()
    if not text:
        return GENERAL_NAME
    if text.lower() in GENERAL_LOWERCASE:
        return GENERAL_NAME
    parts = [part.strip() for part in text.split(";") if part.strip()]
    if not parts:
        return GENERAL_NAME
    return "; ".join(
        DEPARTMENT_ALIASES.get(part.lower(), part) for part in parts
    )


class DepartmentResolver:
    """Cached read-time resolution of activities to canonical departments.

    Uses the same Python ``normalize_department`` as the presentation layer so
    alias handling can never drift from what the UI displays.  Single-department
    rows land in one bucket, multi-department rows are counted in every
    canonical department they name, and institution-wide rows land in
    ``General``.  Read-only: nothing is written back.
    """

    def __init__(self, conn=None):
        self._conn = conn
        self._own = conn is None
        self._by_department = None

    def _load(self):
        if self._by_department is not None:
            return
        from backend.database.init_db import get_connection
        conn = self._conn or get_connection()
        try:
            rows = conn.execute(
                """SELECT a.id, m.department_display
                   FROM institutional_activities a
                   LEFT JOIN final_activity_metadata m ON m.activity_id = a.id"""
            ).fetchall()
            by_department = {}
            for row in rows:
                normalised = normalize_department(row["department_display"])
                if normalised == GENERAL_NAME:
                    by_department.setdefault(GENERAL_NAME, set()).add(row["id"])
                    continue
                for part in normalised.split("; "):
                    by_department.setdefault(part, set()).add(row["id"])
            self._by_department = {
                name: frozenset(ids) for name, ids in by_department.items()
            }
        finally:
            if self._own:
                conn.close()

    @property
    def by_department(self):
        self._load()
        return self._by_department

    def ids_for(self, department):
        self._load()
        if not department:
            return frozenset()
        return self._by_department.get(normalize_department(department), frozenset())


def department_ids_clause(conn, department):
    """Return ``(sql_fragment, params)`` for ``a.id IN (...)`` over one department.

    The fragment references the ``a`` alias (the institutional_activities
    table) exactly like ``ids_in_clause``; an unknown/empty department resolves
    to ``1 = 0`` so a filter can never silently return everything.
    """
    from backend.database.period_catalog import ids_in_clause
    return ids_in_clause(DepartmentResolver(conn=conn).ids_for(department))