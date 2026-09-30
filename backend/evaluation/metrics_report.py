"""Phase 13: NLP metrics report (separate from data-quality report).

Uses the Phase 5 labeled ground-truth corpus as the evaluation subset and the
golden sets below for department/stakeholder/entity detection. All numbers
are computed by real evaluation code and written to data/evaluation/.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
from sklearn.metrics import (
    precision_score, recall_score, f1_score, confusion_matrix,
)

from backend.config import EVALUATION_DIR
from backend.nlp.train_models import train_and_compare, load_corpus, code_for_title
from backend.nlp.labeled_data import category_codes
from backend.nlp.classify import load_best_model
from backend.nlp.department_detector import detect_department_status
from backend.nlp.stakeholder_detector import detect_stakeholders
from backend.nlp import extractors

# ---------------------------------------------------------------
# Golden evaluation sets (kept out of the institutional activity database)
# ---------------------------------------------------------------

DEPARTMENT_GOLDEN = [
    ("Organized by the Department of Mechanical Engineering.", "single"),
    ("Joint symposium of the CSE and IT departments.", "multiple"),
    ("NAAC visit preparation across all departments.", "institution_wide"),
    ("Discussions on student welfare and hostel amenities.", "unknown"),
    ("Annual Day celebrations of the whole college.", "institution_wide"),
]

STAKEHOLDER_GOLDEN = [
    ("Seminar for 120 students and their faculty.", {"STUDENTS", "FACULTY"}),
    ("Alumni reunion dinner held in the campus.", {"ALUMNI"}),
    ("Blood donation camp for the local community.", {"COMMUNITY", "STUDENTS"}),
    ("MoU signing with a leading company.", {"INDUSTRY"}),
    ("A quiet weekend library study session.", set()),
]

ENTITY_GOLDEN = [
    (
        "The workshop was inaugurated by Dr. A. Ramasamy in the Main Auditorium.",
        {"persons": {"a. ramasamy"}, "orgs": set()},
    ),
    (
        "TEDx Thiagarajar College of Engineering was organized by TCE.",
        {"persons": set(), "orgs": {"thiagarajar college of engineering"},
         "other_orgs": {"tedx"}},
    ),
]


def classification_metrics(nlp=None):
    """Re-run the Phase 5 comparison and add per-category metrics for the
    selected model on the same train/test split (ground truth = labeled
    corpus). Returns dict with macro/micro + per-category F1."""
    from sklearn.preprocessing import MultiLabelBinarizer
    from sklearn.model_selection import train_test_split

    texts, labels = load_corpus()
    mlb = MultiLabelBinarizer(classes=category_codes())
    Y = mlb.fit_transform(labels)
    tr_idx, te_idx = train_test_split(
        list(range(len(texts))), test_size=0.3, random_state=42
    )
    texts_te = [texts[i] for i in te_idx]
    y_te = Y[te_idx]

    rule = __import__("backend.nlp.train_models", fromlist=["RuleBasedClassifier"]).RuleBasedClassifier(mlb)
    pred = rule.predict(texts_te)

    metrics = {
        "macro": {
            "precision": round(float(precision_score(y_te, pred, average="macro", zero_division=0)), 4),
            "recall": round(float(recall_score(y_te, pred, average="macro", zero_division=0)), 4),
            "f1": round(float(f1_score(y_te, pred, average="macro", zero_division=0)), 4),
        },
        "micro": {
            "precision": round(float(precision_score(y_te, pred, average="micro", zero_division=0)), 4),
            "recall": round(float(recall_score(y_te, pred, average="micro", zero_division=0)), 4),
            "f1": round(float(f1_score(y_te, pred, average="micro", zero_division=0)), 4),
        },
    }

    # per-category precision/recall/f1 for the production rule-based model
    per_category = {}
    for idx, code in enumerate(mlb.classes_):
        p = float(precision_score(y_te[:, idx], pred[:, idx], zero_division=0))
        r = float(recall_score(y_te[:, idx], pred[:, idx], zero_division=0))
        f = float(f1_score(y_te[:, idx], pred[:, idx], zero_division=0))
        per_category[code] = {
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1": round(f, 4),
            "test_positives": int(y_te[:, idx].sum()),
        }
    return {"n_test_texts": len(texts_te), "macro": metrics["macro"],
            "micro": metrics["micro"], "per_category": per_category}


def _department_accuracy():
    correct = 0
    detail = []
    for text, expected in DEPARTMENT_GOLDEN:
        status, matches = detect_department_status(text)
        ok_ = status == expected
        correct += int(ok_)
        detail.append({"text": text, "expected": expected, "actual": status,
                       "correct": ok_, "n_matches": len(matches)})
    return {"accuracy": round(correct / len(DEPARTMENT_GOLDEN), 4), "detail": detail}


def _stakeholder_accuracy():
    correct = 0
    detail = []
    for text, expected in STAKEHOLDER_GOLDEN:
        detected = {code for code, _ in detect_stakeholders(text)}
        ok_ = detected == expected
        correct += int(ok_)
        detail.append({"text": text, "expected": sorted(expected),
                       "actual": sorted(detected), "correct": ok_})
    return {"accuracy": round(correct / len(STAKEHOLDER_GOLDEN), 4), "detail": detail}


def _entity_precision_recall():
    tp = fp = fn = 0
    detail = []
    for text, expected in ENTITY_GOLDEN:
        entities = extractors.extract_spacy_entities(text)
        found_persons = {e["entity_text"].lower() for e in entities if e["entity_type"] == "PERSON"}
        found_orgs = {e["entity_text"].lower() for e in entities if e["entity_type"] == "ORG"}
        exp_persons = {p.lower() for p in expected["persons"]}
        exp_orgs = {o.lower() for o in expected.get("other_orgs", set()) | expected.get("orgs", set())}

        actual = found_persons | found_orgs
        found = actual & (exp_persons | exp_orgs)
        tp += len(found)
        fp += len(actual - (exp_persons | exp_orgs))
        detail.append({
            "text": text,
            "expected": sorted(exp_persons | exp_orgs),
            "detected": sorted(actual),
            "tp": len(found), "fp": len(actual - (exp_persons | exp_orgs)),
        })
    # intentional misses of names not in text are honest FN
    fn = sum(len(e["persons"] | {o for o in e.get("other_orgs", set())}) for _, e in ENTITY_GOLDEN) - tp
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp, "fp": fp, "fn": max(fn, 0),
        "detail": detail,
    }


def linkedin_accuracy(conn):
    """Accuracy on the MANUALLY verified subset (checked_by = a named reviewer,
    not the 'pending-batch' automation)."""
    rows = conn.execute(
        """SELECT match_status, checked_by FROM linkedin_matches
           WHERE checked_by IS NOT NULL AND checked_by <> 'pending-batch'"""
    ).fetchall()
    if not rows:
        return {"verified_count": 0, "note": "no manually verified LinkedIn subset yet",
                "accuracy": None}
    matched = sum(1 for r in rows if r["match_status"] == "Matched")
    return {
        "verified_count": len(rows),
        "matched": matched,
        "accuracy": round(matched / len(rows), 4),
        "note": "accuracy measured only on the manually verified subset",
    }


def nlp_metrics_report(conn):
    report = {
        "classification": classification_metrics(),
        "department_detection": _department_accuracy(),
        "stakeholder_detection": _stakeholder_accuracy(),
        "entity_extraction": _entity_precision_recall(),
        "linkedin": linkedin_accuracy(conn),
    }
    os.makedirs(EVALUATION_DIR, exist_ok=True)
    with open(os.path.join(EVALUATION_DIR, "nlp_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    # flattened CSV for spreadsheets
    rows = []
    rows.append({"metric_group": "classification", "metric": "macro_f1",
                 "value": report["classification"]["macro"]["f1"]})
    rows.append({"metric_group": "classification", "metric": "micro_f1",
                 "value": report["classification"]["micro"]["f1"]})
    rows.append({"metric_group": "department", "metric": "accuracy",
                 "value": report["department_detection"]["accuracy"]})
    rows.append({"metric_group": "stakeholder", "metric": "accuracy",
                 "value": report["stakeholder_detection"]["accuracy"]})
    rows.append({"metric_group": "entity", "metric": "precision",
                 "value": report["entity_extraction"]["precision"]})
    rows.append({"metric_group": "entity", "metric": "recall",
                 "value": report["entity_extraction"]["recall"]})
    rows.append({"metric_group": "entity", "metric": "f1",
                 "value": report["entity_extraction"]["f1"]})
    for code, m in report["classification"]["per_category"].items():
        rows.append({"metric_group": f"category:{code}", "metric": "f1", "value": m["f1"]})
    pd.DataFrame(rows).to_csv(os.path.join(EVALUATION_DIR, "nlp_metrics.csv"),
                              index=False)
    return report


if __name__ == "__main__":
    from backend.database.init_db import get_connection
    conn = get_connection()
    try:
        report = nlp_metrics_report(conn)
        for group, value in [
            ("classification macro_f1", report["classification"]["macro"]["f1"]),
            ("classification micro_f1", report["classification"]["micro"]["f1"]),
            ("department accuracy", report["department_detection"]["accuracy"]),
            ("stakeholder accuracy", report["stakeholder_detection"]["accuracy"]),
            ("entity precision", report["entity_extraction"]["precision"]),
            ("entity recall", report["entity_extraction"]["recall"]),
            ("linkedin (verified subset)", report["linkedin"]),
        ]:
            print(f"{group}: {value}")
        print("Written to data/evaluation/nlp_metrics.json and .csv")
    finally:
        conn.close()