"""Step 4 adapter: classify pending candidates without promoting activities.

It deliberately reuses the selected rule baseline's category cues and
multi-label semantics.  Candidate hints are evidence for validation only.
"""

from collections import Counter

from sklearn.preprocessing import MultiLabelBinarizer

from backend.database.init_db import get_connection, init_db
from backend.nlp.labeled_data import category_codes
from backend.nlp.train_models import RuleBasedClassifier


def classify_text(text):
    """Return the existing classifier's final category codes, never hints."""
    mlb = MultiLabelBinarizer(classes=category_codes())
    mlb.fit([category_codes()])
    matrix = RuleBasedClassifier(mlb).predict([text or ""])
    return list(mlb.classes_[matrix[0].astype(bool)])


def hint_status(category_hint, final_categories, category):
    """Validate a stored hint; do not translate or alter final categories."""
    if not category_hint or category_hint == "OTHER":
        return "NO_HINT"
    if category_hint in final_categories:
        return "CONSISTENT" if category == category_hint else "SUPPORTING"
    return "DIFFERENT"


def classify_candidates(conn=None, extraction_run_id=4):
    """Classify one extraction run into candidate_classifications only."""
    init_db()
    own = conn is None
    conn = conn or get_connection()
    try:
        rows = conn.execute(
            "SELECT id, title, description, evidence_text, category_hint FROM activity_candidates "
            "WHERE extraction_run_id=? ORDER BY id", (extraction_run_id,)
        ).fetchall()
        inserted = 0
        for row in rows:
            # Title and description are the normal existing classifier input;
            # evidence supplements an incomplete archive-derived description.
            text = " ".join(filter(None, (row["title"], row["description"], row["evidence_text"])))
            categories = classify_text(text)
            for category in categories:
                conn.execute(
                    """INSERT OR IGNORE INTO candidate_classifications
                       (candidate_id, final_category, classification_confidence, category_hint, hint_match_status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (row["id"], category, 0.8, row["category_hint"],
                     hint_status(row["category_hint"], categories, category)),
                )
                inserted += conn.execute("SELECT changes()").fetchone()[0]
        conn.commit()
        return classification_report(conn, extraction_run_id, inserted)
    finally:
        if own:
            conn.close()


def classification_report(conn, extraction_run_id, inserted=0):
    """Return database-derived Step 4 counts; does not mutate candidate data."""
    candidate_count = conn.execute(
        "SELECT COUNT(*) FROM activity_candidates WHERE extraction_run_id=?", (extraction_run_id,)
    ).fetchone()[0]
    assignments = conn.execute(
        """SELECT COUNT(*) FROM candidate_classifications cc
           JOIN activity_candidates c ON c.id=cc.candidate_id WHERE c.extraction_run_id=?""",
        (extraction_run_id,),
    ).fetchone()[0]
    classified = conn.execute(
        """SELECT COUNT(DISTINCT cc.candidate_id) FROM candidate_classifications cc
           JOIN activity_candidates c ON c.id=cc.candidate_id WHERE c.extraction_run_id=?""",
        (extraction_run_id,),
    ).fetchone()[0]
    multi = conn.execute(
        """SELECT COUNT(*) FROM (SELECT cc.candidate_id FROM candidate_classifications cc
           JOIN activity_candidates c ON c.id=cc.candidate_id WHERE c.extraction_run_id=?
           GROUP BY cc.candidate_id HAVING COUNT(*) > 1)""", (extraction_run_id,),
    ).fetchone()[0]
    distribution = dict(conn.execute(
        """SELECT cats.code, COUNT(CASE WHEN c.extraction_run_id=? THEN cc.id END)
           FROM categories cats LEFT JOIN candidate_classifications cc ON cc.final_category=cats.code
           LEFT JOIN activity_candidates c ON c.id=cc.candidate_id GROUP BY cats.code ORDER BY cats.code""",
        (extraction_run_id,),
    ).fetchall())
    years = {year: conn.execute(
        "SELECT COUNT(*) FROM activity_candidates WHERE extraction_run_id=? AND academic_year IS ?",
        (extraction_run_id, year),
    ).fetchone()[0] for year in ("2021-22", "2022-23", "2023-24", "2024-25", "2025-26", None)}
    year_category = [dict(row) for row in conn.execute(
        """SELECT COALESCE(c.academic_year, 'UNRESOLVED') AS academic_year,
                   cc.final_category, COUNT(*) AS assignments
           FROM candidate_classifications cc JOIN activity_candidates c ON c.id=cc.candidate_id
           WHERE c.extraction_run_id=? GROUP BY c.academic_year, cc.final_category
           ORDER BY academic_year, final_category""", (extraction_run_id,)
    )]
    combinations = [dict(row) for row in conn.execute(
        """SELECT c.category_hint, GROUP_CONCAT(cc.final_category) AS final_categories, COUNT(*) AS candidates
           FROM activity_candidates c JOIN candidate_classifications cc ON cc.candidate_id=c.id
           WHERE c.extraction_run_id=? GROUP BY c.id""", (extraction_run_id,)
    )]
    hint_summary = Counter()
    for row in conn.execute(
        """SELECT c.category_hint, GROUP_CONCAT(cc.final_category) AS final_categories
           FROM activity_candidates c LEFT JOIN candidate_classifications cc ON cc.candidate_id=c.id
           WHERE c.extraction_run_id=? GROUP BY c.id""", (extraction_run_id,)):
        finals = set((row["final_categories"] or "").split(",")) - {""}
        hint = row["category_hint"]
        if not hint or hint == "OTHER":
            status = "NO_HINT"
        elif hint in finals:
            # The hint validates one final label while the extra labels are
            # retained as independent multi-label evidence.
            status = "SUPPORTING" if len(finals) > 1 else "CONSISTENT"
        else:
            status = "DIFFERENT"
        hint_summary[status] += 1
    return {"candidates_processed": candidate_count, "classified_candidates": classified,
            "unclassified_candidates": candidate_count - classified, "total_assignments": assignments,
            "multi_label_candidates": multi, "inserted_assignments": inserted,
            "category_distribution": distribution, "academic_year_distribution": years,
            "hint_validation": dict(hint_summary), "year_category_distribution": year_category,
            "hint_combinations": combinations}
