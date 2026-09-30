"""Run the full Phase 13 evaluation, writing both distinct reports."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database.init_db import get_connection
from backend.evaluation.metrics_report import nlp_metrics_report
from backend.evaluation.data_quality_report import data_quality_report


def run_evaluation():
    conn = get_connection()
    try:
        nlp = nlp_metrics_report(conn)
        dq = data_quality_report(conn)
        return {
            "nlp_metrics": {
                "classification_macro_f1": nlp["classification"]["macro"]["f1"],
                "classification_micro_f1": nlp["classification"]["micro"]["f1"],
                "department_accuracy": nlp["department_detection"]["accuracy"],
                "stakeholder_accuracy": nlp["stakeholder_detection"]["accuracy"],
                "entity_extraction": {
                    "precision": nlp["entity_extraction"]["precision"],
                    "recall": nlp["entity_extraction"]["recall"],
                    "f1": nlp["entity_extraction"]["f1"],
                },
            },
            "data_quality": dq,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    import json
    result = run_evaluation()
    print("NLP metrics:")
    print(f"  classification macro-F1: {result['nlp_metrics']['classification_macro_f1']}")
    print(f"  classification micro-F1: {result['nlp_metrics']['classification_micro_f1']}")
    print(f"  department accuracy: {result['nlp_metrics']['department_accuracy']}")
    print(f"  stakeholder accuracy: {result['nlp_metrics']['stakeholder_accuracy']}")
    print("  entity extraction:", result["nlp_metrics"]["entity_extraction"])
    print("Data quality:", json.dumps(result["data_quality"]["pipeline"], indent=2))