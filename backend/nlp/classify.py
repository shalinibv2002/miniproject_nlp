"""Phase 5: apply the selected classifier to all activities.

Loads data/models/best_model.pkl, classifies every activity in
institutional_activities, and writes results to activity_categories
with confidence + classification_method_id.
"""

import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.nlp.preprocess import lemmatize
from backend.nlp.train_models import code_for_title, RuleBasedClassifier
from backend.config import EVALUATION_DIR

MODEL_DIR = os.path.join(os.path.dirname(EVALUATION_DIR), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "best_model.pkl")


def load_best_model():
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def _category_ids(conn, codes):
    ids = {}
    for code in codes:
        row = conn.execute("SELECT id FROM categories WHERE code=?", (code,)).fetchone()
        if row:
            ids[code] = row["id"]
    return ids


def _method_id(conn, model_name):
    if "Rule-Based" in model_name:
        return conn.execute(
            "SELECT id FROM classification_methods WHERE name LIKE 'Rule-Based%'"
        ).fetchone()["id"]
    return conn.execute(
        "SELECT id FROM classification_methods WHERE name LIKE 'TF-IDF + Logistic%'"
    ).fetchone()["id"]


def predict_labels(artifact, text):
    """Return list of (code, confidence) predicted for one text block."""
    kind = artifact.get("kind", "ml")
    if kind == "rule":
        matrix = artifact["model"].predict([text])
        labels = artifact["mlb"].classes_[matrix[0].astype(bool)]
        return [(code, 0.8) for code in labels]
    # ML path
    vec = artifact["vectorizer"].transform([lemmatize(text)])
    row = artifact["model"].predict(vec)
    labels = artifact["mlb"].classes_[row[0].astype(bool)]
    return [(code, 0.75) for code in labels]


def classify_all(conn=None):
    own = conn is None
    conn = conn or get_connection()
    artifact = load_best_model()
    method_id = _method_id(conn, artifact["model_name"])
    cat_ids = _category_ids(
        conn, [c for c in artifact["mlb"].classes_]
    )

    rows = conn.execute(
        "SELECT id, title, description FROM institutional_activities"
    ).fetchall()
    classified = 0
    try:
        for row in rows:
            text = " ".join(filter(None, [row["title"], row["description"]]))
            preds = predict_labels(artifact, text)
            if not preds:
                continue
            sorted_preds = sorted(preds, key=lambda p: p[1], reverse=True)
            for index, (code, confidence) in enumerate(sorted_preds):
                category_id = cat_ids.get(code)
                if category_id is None:
                    continue
                conn.execute(
                    """INSERT OR IGNORE INTO activity_categories
                       (activity_id, category_id, confidence,
                        classification_method_id, is_primary)
                       VALUES (?, ?, ?, ?, ?)""",
                    (row["id"], category_id, confidence, method_id,
                     1 if index == 0 else 0),
                )
            overall_conf = round(max(0.5, sum(c for _, c in sorted_preds) / len(sorted_preds)), 3)
            conn.execute(
                "UPDATE institutional_activities SET overall_confidence=? WHERE id=?",
                (overall_conf, row["id"]),
            )
            classified += 1
        conn.commit()
        return classified
    finally:
        if own:
            conn.close()


if __name__ == "__main__":
    n = classify_all()
    print(f"Classified {n} activities into activity_categories using {MODEL_PATH}")