"""Phase 12+v2: execute parsed NLQ intents; V2 public path via interpreter."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.nlp.query_parser import parse_question, INTENT_COUNT, INTENT_LIST, INTENT_COMPARE


class BoundedFilter:
    """Represents a grounded activity filter built from parsed entities."""

    def __init__(self, conn):
        self.conn = conn
        self._joins = []
        self._wheres = []
        self._params = []

    def by_year(self, start_year):
        row = self.conn.execute(
            "SELECT id FROM academic_years WHERE start_year=?", (start_year,)
        ).fetchone()
        if row:
            self._wheres.append("a.activity_year_id = ?")
            self._params.append(row["id"])
            return True
        return False

    def by_category_code(self, code):
        self._joins.append(
            "JOIN activity_categories ac ON ac.activity_id = a.id JOIN categories c ON c.id = ac.category_id"
        )
        self._wheres.append("c.code = ?")
        self._params.append(code)

    def by_department_code(self, code):
        self._joins.append(
            "JOIN activity_departments ad ON ad.activity_id = a.id JOIN departments d ON d.id = ad.department_id"
        )
        self._wheres.append("d.code = ?")
        self._params.append(code)

    def by_stakeholder_code(self, code):
        self._joins.append(
            "JOIN activity_stakeholders ast ON ast.activity_id = a.id JOIN stakeholders s ON s.id = ast.stakeholder_id"
        )
        self._wheres.append("s.code = ?")
        self._params.append(code)

    def count(self):
        joins = " ".join(set(self._joins))
        where = ("WHERE " + " AND ".join(self._wheres)) if self._wheres else ""
        row = self.conn.execute(
            f"SELECT COUNT(DISTINCT a.id) AS c FROM institutional_activities a {joins} {where}",
            self._params,
        ).fetchone()
        return row["c"]

    def fetch(self, limit=50):
        joins = " ".join(set(self._joins))
        where = ("WHERE " + " AND ".join(self._wheres)) if self._wheres else ""
        rows = self.conn.execute(
            f"""SELECT DISTINCT a.id, a.title, a.activity_date, a.source_url
                FROM institutional_activities a {joins} {where}
                ORDER BY a.activity_date DESC, a.id DESC
                LIMIT ?""",
            self._params + [limit],
        ).fetchall()
        return [dict(r) for r in rows]


def _legacy_answer_question(question, conn=None):
    """Answer a plain-English question using safe templates.

    Returns {intent, filters, answer, count, activities}. The 'year' filter
    uses the mapped academic-year bucket when it exists; otherwise 0 is
    returned honestly with an explanatory note.
    """
    own = conn is None
    conn = conn or get_connection()
    try:
        parsed = parse_question(question, conn=conn)
        intent = parsed["intent"]
        f = parsed["filters"]
        filters_used = {k: v for k, v in f.items() if v is not None}

        if intent == INTENT_COMPARE:
            return _answer_compare(conn, question, parsed)

        bf = BoundedFilter(conn)
        note = ""
        if f["year"]:
            mapped = bf.by_year(f["year"][0])
            if not mapped:
                # Bucket for this academic year doesn't exist (e.g. events
                # dated beyond the seeded 2020-2025 years). Answer is 0 for
                # that year, honestly, rather than silently dropping the filter.
                bf._wheres.append("1 = 0")
                note = f" no academic-year bucket starts in {f['year'][0]}"
        if f["category"]:
            bf.by_category_code(f["category"])
        if f["department"]:
            bf.by_department_code(f["department"])
        if f["stakeholder"]:
            bf.by_stakeholder_code(f["stakeholder"])

        count = bf.count()
        items = bf.fetch()

        label = f["category_name"] or f["department_name"] or f["stakeholder"]
        where_txt = "in the system" if not label and not f["year"] else \
            (f" matching '{label}'" if label else "") + \
            (f" in academic year {f['year'][0]}-{f['year'][1]}" if f["year"] else "")

        if intent == INTENT_COUNT:
            answer = f"{count} matching activit{'y' if count == 1 else 'ies'}{where_txt}."
        else:
            if count == 0:
                answer = f"No matching activities{where_txt}."
            else:
                answer = f"{count} matching activit{'y' if count == 1 else 'ies'}{where_txt} found."

        if note:
            filters_used["_note"] = note.strip()

        return {
            "intent": intent,
            "question": question,
            "filters": {k: v for k, v in filters_used.items()},
            "answer": answer,
            "count": count,
            "activities": items,
        }
    finally:
        if own:
            conn.close()


def _public_answer(question, conn):
    """Query System V2: interpret the question, then execute against public data.

    All internal interpretation and aggregation live in the interpreter and
    executor modules; this function only bridges them for the public path.
    """
    from backend.nlp.query_executor import execute
    from backend.nlp.query_interpreter import interpret
    return execute(interpret(question, conn=conn), question, conn)


def answer_question(question, conn=None):
    """Answer from final public metadata when present; preserve legacy test support."""
    own = conn is None
    conn = conn or get_connection()
    try:
        has_final_rows = conn.execute("SELECT EXISTS(SELECT 1 FROM final_activity_metadata) AS value").fetchone()["value"]
        if has_final_rows:
            return _public_answer(question, conn)
        return _legacy_answer_question(question, conn)
    finally:
        if own:
            conn.close()


def _answer_compare(conn, question, parsed):
    cmp_ = parsed.get("compare") or {}
    left, right = cmp_.get("left", {}), cmp_.get("right", {})

    def entity(ff):
        if ff.get("category"):
            return ("category", ff["category"][0][0])  # [0]=tuple (code,name)
        if ff.get("department"):
            return ("department", ff["department"][0][0])
        return (None, None)

    le, lv = entity(left)
    re_, rv = entity(right)
    if le is None or re_ is None:
        # no clear two sides — fall back to a general list
        bf = BoundedFilter(conn)
        items = bf.fetch()
        f = parsed["filters"]
        return {
            "intent": INTENT_LIST,
            "question": question,
            "filters": {k: v for k, v in f.items() if v is not None},
            "answer": f"{len(items)} activities found in the system.",
            "count": len(items),
            "activities": items,
        }

    def cnt(kind, code):
        bf = BoundedFilter(conn)
        if kind == "category":
            bf.by_category_code(code)
        else:
            bf.by_department_code(code)
        return bf.count()

    c_left = cnt(le, lv)
    c_right = cnt(re_, rv)
    if c_left == c_right:
        verdict = "Both sides are equal"
        answer = (f"{verdict} ({c_left} vs {c_right}).")
    elif c_left > c_right:
        verdict = f"{lv} has more than {rv}"
        answer = f"{verdict} ({c_left} vs {c_right})."
    else:
        verdict = f"{rv} has more than {lv}"
        answer = f"{verdict} ({c_left} vs {c_right})."

    return {
        "intent": INTENT_COMPARE,
        "question": question,
        "filters": {"compare_left": lv, "compare_right": rv},
        "answer": answer,
        "count": None,
        "activities": [],
    }
