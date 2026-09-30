"""Step 6: conservative candidate-to-final activity promotion."""

import json
from collections import Counter

from backend.database.init_db import get_connection, init_db
from backend.database.normalizer import to_normalized_title


def _display(value):
    try:
        values = json.loads(value or "[]")
    except json.JSONDecodeError:
        values = []
    values = [v for v in values if v and v != "GENERAL"]
    return "; ".join(values) if values else "General"


def _stakeholders(value):
    try:
        values = json.loads(value or "[]")
    except json.JSONDecodeError:
        values = []
    values = [v.title() for v in values if v and v != "UNKNOWN"]
    return "; ".join(values) or None


def promote_candidates(conn=None, extraction_run_id=4):
    """Promote GOOD + classified candidates; exact title/date duplicates merge.

    REVIEW/NON_ACTIVITY records remain candidate evidence.  An undated record
    is never merged solely on title, avoiding edition/year over-merges.
    """
    init_db()
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            """SELECT c.*, o.source_url FROM activity_candidates c
               JOIN candidate_quality_reviews q ON q.candidate_id=c.id AND q.quality_status='GOOD'
               JOIN raw_source_occurrences o ON o.id=c.source_occurrence_id
               WHERE c.extraction_run_id=? AND EXISTS
                 (SELECT 1 FROM candidate_classifications cc WHERE cc.candidate_id=c.id)
               ORDER BY c.id""", (extraction_run_id,)
        ).fetchall()
        category_ids = dict(conn.execute("SELECT code,id FROM categories").fetchall())
        method_id = conn.execute("SELECT id FROM classification_methods WHERE name LIKE 'Rule-Based%' ").fetchone()[0]
        existing = {(r["normalized_title"], r["activity_date"]): r["id"] for r in conn.execute(
            "SELECT id,normalized_title,activity_date FROM institutional_activities"
        )}
        promoted = merged = 0
        activity_sources = Counter()
        for row in rows:
            normalized = to_normalized_title(row["title"])
            # exact date required for matching, including comparisons to the
            # original ten activities; NULL-date candidates stay distinct.
            key = (normalized, row["activity_date"])
            activity_id = existing.get(key) if row["activity_date"] else None
            if activity_id:
                merged += 1
            else:
                cur = conn.execute(
                    """INSERT INTO institutional_activities
                       (title,normalized_title,description,activity_date,source_url,overall_confidence)
                       VALUES (?,?,?,?,?,?)""",
                    (row["title"], normalized, row["description"], row["activity_date"], row["source_url"], .8),
                )
                activity_id = cur.lastrowid
                promoted += 1
                if row["activity_date"]:
                    existing[key] = activity_id
                conn.execute(
                    """INSERT INTO final_activity_metadata
                       (activity_id,activity_date_text,academic_year,department_display,stakeholder_display,
                        achievement_outcome,evidence_text) VALUES (?,?,?,?,?,?,?)""",
                    (activity_id, row["activity_date_text"], row["academic_year"], _display(row["department"]),
                     _stakeholders(row["stakeholder"]), row["achievement_outcome"], row["evidence_text"]),
                )
            conn.execute("INSERT OR IGNORE INTO activity_candidate_links (activity_id,candidate_id) VALUES (?,?)",
                         (activity_id, row["id"]))
            conn.execute("INSERT OR IGNORE INTO activity_sources (activity_id,source_url,raw_record_id,collected_at) VALUES (?,?,?,datetime('now'))",
                         (activity_id, row["source_url"], str(row["source_occurrence_id"])))
            for category in conn.execute("SELECT final_category FROM candidate_classifications WHERE candidate_id=?", (row["id"],)):
                category_id = category_ids[category["final_category"]]
                conn.execute("""INSERT OR IGNORE INTO activity_categories
                              (activity_id,category_id,confidence,classification_method_id,is_primary)
                              VALUES (?,?,?,?,?)""", (activity_id, category_id, .8, method_id, 0))
        conn.commit()
        return final_report(conn, extraction_run_id, promoted, merged)
    finally:
        if own:
            conn.close()


def final_report(conn, extraction_run_id=4, promoted=0, merged=0):
    """Return database-derived Step 6 metrics for promoted candidate records."""
    linked = "SELECT activity_id FROM activity_candidate_links l JOIN activity_candidates c ON c.id=l.candidate_id WHERE c.extraction_run_id=?"
    final_count = conn.execute(f"SELECT COUNT(DISTINCT activity_id) FROM ({linked})", (extraction_run_id,)).fetchone()[0]
    funnel = dict(conn.execute("""SELECT q.quality_status,COUNT(*) FROM candidate_quality_reviews q
                               JOIN activity_candidates c ON c.id=q.candidate_id WHERE c.extraction_run_id=? GROUP BY q.quality_status""", (extraction_run_id,)).fetchall())
    years = dict(conn.execute(f"""SELECT COALESCE(m.academic_year,'Not available'),COUNT(DISTINCT m.activity_id)
                                FROM final_activity_metadata m WHERE m.activity_id IN ({linked})
                                GROUP BY m.academic_year""", (extraction_run_id,)).fetchall())
    categories = dict(conn.execute(f"""SELECT cats.code,COUNT(DISTINCT ac.activity_id) FROM categories cats
       LEFT JOIN activity_categories ac ON ac.category_id=cats.id AND ac.activity_id IN ({linked})
       GROUP BY cats.code ORDER BY cats.code""", (extraction_run_id,)).fetchall())
    departments = dict(conn.execute(f"""SELECT m.department_display,COUNT(DISTINCT m.activity_id) FROM final_activity_metadata m
       WHERE m.activity_id IN ({linked}) GROUP BY m.department_display ORDER BY COUNT(*) DESC""", (extraction_run_id,)).fetchall())
    source_counts = Counter(r[0] for r in conn.execute(f"""SELECT COUNT(*) FROM activity_sources
       WHERE activity_id IN ({linked}) GROUP BY activity_id""", (extraction_run_id,)))
    return {"candidate_funnel": {"extracted": sum(funnel.values()), **funnel}, "final_activities": final_count,
            "promoted_new": promoted, "merged_duplicates": merged,
            "not_promoted": sum(funnel.values()) - final_count - merged,
            "academic_year_distribution": years, "category_distribution": categories,
            "department_distribution": departments, "source_support": {"one_source": source_counts[1],
            "multiple_sources": sum(v for k,v in source_counts.items() if k > 1)}}
