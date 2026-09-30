"""Phase 5: train and compare four multi-label classifiers.

Trains on the labeled training corpus (backend/nlp/labeled_data.py) with a
shared train/test split and saves a comparison table to data/evaluation/.
The best model + vectorizer + binarizer are persisted to data/models/.
"""

import json
import os
import pickle
import sys

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.nlp.extractors import CATEGORY_KEYWORDS
from backend.nlp.labeled_data import get_labeled_data, category_codes
from backend.nlp.preprocess import lemmatize, clean_for_vectorization
from backend.config import EVALUATION_DIR

MODEL_DIR = os.path.join(os.path.dirname(EVALUATION_DIR), "models")

# ---------------------------------------------------------------
# Rule-based keyword baseline
# ---------------------------------------------------------------
class RuleBasedClassifier:
    def __init__(self, mlb):
        self.mlb = mlb

    def predict(self, texts):
        rows = []
        for t in texts:
            labels = set()
            t_lower = clean_for_vectorization(t).lower()
            for category_name, cues in CATEGORY_KEYWORDS.items():
                if any(cue in t_lower for cue in cues):
                    code = code_for_title(category_name)
                    if code:
                        labels.add(code)
            rows.append(labels)
        return self.mlb.transform(rows)


def code_for_title(category_name):
    mapping = {
        "Workshop": "WORKSHOP", "Seminar": "SEMINAR", "Conference": "CONFERENCE",
        "Symposium": "SYMPOSIUM", "Guest Lecture": "GUEST_LECTURE",
        "Faculty Development Programme": "FDP",
        "Short Term Training Programme": "STTP", "Hackathon": "HACKATHON",
        "Technical Festival": "TECH_FEST", "Cultural Event": "CULTURAL",
        "Sports and Games": "SPORTS", "NCC Activity": "NCC", "NSS Activity": "NSS",
        "Clubs and Chapters": "CLUB", "Outreach and Extension": "OUTREACH",
        "Industry Collaboration": "INDUSTRY", "Achievement and Award": "ACHIEVEMENT",
        "Placement Activity": "PLACEMENT", "Internship": "INTERNSHIP",
        "Research and Consultancy": "RESEARCH", "Alumni Event": "ALUMNI",
        "Orientation and Convocation": "ORIENTATION", "Campus Life": "CAMPUS",
        "Webinar": "WEBINAR",
    }
    return mapping.get(category_name, "")


# ---------------------------------------------------------------
# Training
# ---------------------------------------------------------------
def make_models():
    return {
        "TF-IDF + LogisticRegression (OvR)": OneVsRestClassifier(
            LogisticRegression(max_iter=3000, C=1.0, solver="liblinear",
                               class_weight="balanced")
        ),
        "TF-IDF + LinearSVC (OvR)": OneVsRestClassifier(
            LinearSVC(max_iter=5000, C=1.0, class_weight="balanced")
        ),
        "TF-IDF + MultinomialNB (OvR)": OneVsRestClassifier(MultinomialNB(alpha=1.0)),
    }


def _metrics(y_true, y_pred, average):
    return {
        f"precision_{average}": round(float(precision_score(y_true, y_pred, average=average, zero_division=0)), 4),
        f"recall_{average}": round(float(recall_score(y_true, y_pred, average=average, zero_division=0)), 4),
        f"f1_{average}": round(float(f1_score(y_true, y_pred, average=average, zero_division=0)), 4),
    }


def load_corpus():
    data = get_labeled_data()
    texts = [t for t, _ in data]
    labels = [c for _, c in data]
    return texts, labels


def train_and_compare(test_size=0.3, random_state=42, save=True):
    os.makedirs(EVALUATION_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    texts, labels = load_corpus()

    mlb = MultiLabelBinarizer(classes=category_codes())
    Y = mlb.fit_transform(labels)

    # index-based split so the rule-based baseline uses the same test texts
    indices = list(range(len(texts)))
    tr_idx, te_idx = train_test_split(indices, test_size=test_size, random_state=random_state)

    texts_tr = [texts[i] for i in tr_idx]
    texts_te = [texts[i] for i in te_idx]
    y_tr = Y[tr_idx]
    y_te = Y[te_idx]

    # Fit vectorizer ONLY on training text (no leakage)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
    lemmatized_tr = [lemmatize(t) for t in texts_tr]
    X_tr = vectorizer.fit_transform(lemmatized_tr)
    X_te = vectorizer.transform([lemmatize(t) for t in texts_te])

    results = {}

    # Rule-based baseline
    rule = RuleBasedClassifier(mlb)
    rule_pred = rule.predict(texts_te)
    results["Rule-Based Keyword Baseline"] = {
        **_metrics(y_te, rule_pred, "macro"),
        **_metrics(y_te, rule_pred, "micro"),
    }

    trained = {"Rule-Based Keyword Baseline": rule}
    for name, model in make_models().items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        results[name] = {
            **_metrics(y_te, pred, "macro"),
            **_metrics(y_te, pred, "micro"),
        }
        trained[name] = model

    best_name = max(results, key=lambda k: results[k]["f1_macro"])
    best_model = trained[best_name]
    best_kind = "ml" if best_name in make_models() else "rule"

    if save:
        with open(os.path.join(MODEL_DIR, "best_model.pkl"), "wb") as f:
            pickle.dump({
                "model": best_model,
                "vectorizer": vectorizer,
                "mlb": mlb,
                "model_name": best_name,
                "kind": best_kind,
            }, f)

        comparison_rows = [
            {"model": m, **metrics, "selected": "yes" if m == best_name else ""}
            for m, metrics in results.items()
        ]
        pd.DataFrame(comparison_rows).to_csv(
            os.path.join(EVALUATION_DIR, "model_comparison.csv"), index=False
        )
        with open(os.path.join(EVALUATION_DIR, "model_comparison.json"), "w", encoding="utf-8") as f:
            json.dump({
                "best_model": best_name,
                "n_samples": len(texts),
                "n_train": len(tr_idx),
                "n_test": len(te_idx),
                "results": results,
            }, f, indent=2)

    print(f"Best model: {best_name}")
    for m, metrics in results.items():
        print(f"  {m}  macro-F1={metrics['f1_macro']}  micro-F1={metrics['f1_micro']}")

    return {"results": results, "best_model_name": best_name, "mlb_classes": list(mlb.classes_)}


if __name__ == "__main__":
    out = train_and_compare()
    df = pd.DataFrame(out["results"]).T
    print(df[["precision_macro", "recall_macro", "f1_macro",
              "precision_micro", "recall_micro", "f1_micro"]].to_string())