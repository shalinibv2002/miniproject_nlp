"""Phase 5 tests: classification pipeline + model selection."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from backend.nlp.labeled_data import get_labeled_data, category_codes
from backend.nlp.train_models import (
    train_and_compare, RuleBasedClassifier, code_for_title,
)
from backend.nlp import classify


def test_labeled_corpus_nonempty():
    data = get_labeled_data()
    assert len(data) >= 100
    assert len(category_codes()) >= 20


def test_code_for_title_mapping():
    assert code_for_title("Workshop") == "WORKSHOP"
    assert code_for_title("Faculty Development Programme") == "FDP"


def test_rule_based_classifier_shape():
    texts = [t for t, _ in get_labeled_data()]
    labels = [c for _, c in get_labeled_data()]
    mlb = __import__("sklearn.preprocessing", fromlist=["MultiLabelBinarizer"]).MultiLabelBinarizer(
        classes=category_codes()
    )
    mlb.fit(labels)
    clf = RuleBasedClassifier(mlb)
    matrix = clf.predict(texts[:5])
    assert matrix.shape == (5, len(category_codes()))


def test_train_compare_runs_and_returns_best():
    out = train_and_compare(test_size=0.3, random_state=42, save=False)
    assert "best_model_name" in out
    assert out["best_model_name"] in out["results"]
    macro_f1s = [v["f1_macro"] for v in out["results"].values()]
    assert all(mf >= 0.0 and mf <= 1.0 for mf in macro_f1s)


def test_classify_predictions_are_codes():
    artifact = {
        "kind": "rule",
        "model": None,
        "mlb": None,
        "model_name": "Rule-Based Keyword Baseline",
    }
    # direct function test: predict_labels requires a real artifact
    from backend.nlp.train_models import load_corpus
    texts, labels = load_corpus()
    mlb = __import__("sklearn.preprocessing", fromlist=["MultiLabelBinarizer"]).MultiLabelBinarizer(
        classes=category_codes()
    )
    mlb.fit(labels)
    rule = RuleBasedClassifier(mlb)
    artifact["model"] = rule
    artifact["mlb"] = mlb
    preds = classify.predict_labels(artifact, "Workshop on python programming")
    codes = [c for c, _ in preds]
    assert "WORKSHOP" in codes
    for code, conf in preds:
        assert code in category_codes()
        assert 0 <= conf <= 1


def test_best_model_artifact_exists():
    from backend.config import EVALUATION_DIR
    path = os.path.join(os.path.join(os.path.dirname(EVALUATION_DIR), "models"), "best_model.pkl")
    assert os.path.exists(path), "best_model.pkl not saved"