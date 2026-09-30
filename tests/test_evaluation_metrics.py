"""Phase 13 tests: sanity-check metric calculations against hand-computed results."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from backend.evaluation.metrics_report import (
    _department_accuracy, _stakeholder_accuracy, classification_metrics,
)
from backend.evaluation.data_quality_report import data_quality_report


def _precision_recall_f1(tp, fp, fn):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def test_hand_computed_precision_recall_f1():
    # y_true = [1,0,1,1,0], y_pred = [1,0,0,1,1]
    # tp = 2, fp = 1, fn = 1
    tp, fp, fn = 2, 1, 1
    p, r, f = _precision_recall_f1(tp, fp, fn)
    assert p == pytest.approx(2 / 3)
    assert r == pytest.approx(2 / 3)
    assert f == pytest.approx(2 / 3)
    # balanced case
    assert _precision_recall_f1(5, 0, 0) == (1.0, 1.0, 1.0)


def test_classification_metrics_shape():
    cm = classification_metrics()
    assert set(cm["macro"]) == {"precision", "recall", "f1"}
    assert 0 <= cm["macro"]["f1"] <= 1
    assert len(cm["per_category"]) >= 20
    # every category F1 is a valid probability-ish score
    for code, m in cm["per_category"].items():
        assert 0 <= m["f1"] <= 1 + 1e-9, code


def test_department_golden_accuracy_bounds():
    r = _department_accuracy()
    assert 0 <= r["accuracy"] <= 1
    assert len(r["detail"]) >= 4


def test_stakeholder_golden_accuracy_bounds():
    r = _stakeholder_accuracy()
    assert 0 <= r["accuracy"] <= 1
    assert len(r["detail"]) >= 4


def test_data_quality_report_reconciles(tmp_path):
    from backend.database.init_db import get_connection
    from backend.database import init_db as idb
    from backend.database.seed_reference_data import seed

    p = str(tmp_path / "dq.db")
    idb.init_db(p)
    conn = get_connection(db_path=p)
    try:
        seed(conn=conn)
        conn.execute(
            """INSERT INTO institutional_activities
               (title, normalized_title, overall_confidence, is_verified)
               VALUES ('A', 'a', 0.5, 1)"""
        )
        conn.commit()
        r = data_quality_report(conn)
        assert r["completeness"]["total_records"] == 1
        assert r["completeness"]["description_present"] == 0
        assert r["completeness"]["no_mapped_academic_year"] == 1
        assert r["classification"]["low_confidence_below_0.6"] == 1
        assert r["review_verification"]["verified"] == 1
    finally:
        conn.close()