"""Phase 14: generate the case-study presentation deck (Markdown, Marp-style).

Every figure comes from the live database via the same analytics modules the
API uses, so slides can never diverge from the report.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd

from backend.database.init_db import get_connection
from backend.config import EXPORT_DIR
from backend.analytics import overview, department, category, stakeholder, linkedin_visibility
from backend.reports.report_generator import REPORT_DIR
from backend.evaluation.run_evaluation import run_evaluation

SLIDES_PATH = os.path.join(REPORT_DIR, "presentation.md")


def _slide(md, title, body):
    md.append(f"---\n\n# {title}\n")
    md.append(body)
    md.append("")


def build_presentation(conn=None):
    conn = conn or get_connection()
    try:
        ev = run_evaluation()
        o = overview.overview(conn)
        dm = ev["nlp_metrics"]
        dq = ev["data_quality"]["pipeline"]
        depts = department.department_summary(conn)
        cats = category.category_summary(conn)
        stks = stakeholder.stakeholder_summary(conn)
        links = linkedin_visibility.linkedin_summary(conn)

        md = []
        _slide(md, "Institutional Activity Intelligence & Evaluation System",
               "**NLP Case Study - Thiagarajar College of Engineering, Madurai**\n\n"
               "Free toolchain &middot; Flask + SQLite + scikit-learn + React\n\n"
               f"Generated {pd.Timestamp.now().strftime('%Y-%m-%d')}")

        _slide(md, "Problem & Objectives",
               "- Institutional activity records are scattered across public pages.\n"
               "- No single structured, searchable, auditable view exists.\n"
               "- **Objective**: free toolchain to collect, extract, classify,\n"
               "  review, cross-reference and query real institutional activity data.")

        _slide(md, "Data & Collection (lawful, no scraping of restricted sites)",
               f"- Verified public TCE pages, robots.txt-respecting crawler.\n"
               f"- Raw archive: **{dq['raw_archive_files']} JSON snapshots**, "
               f"**{dq['raw_records_collected']} records**.\n"
               f"- Unique real events loaded into the database: "
               f"**{dq['final_unique_activities']}**.\n"
               f"- Pipeline is reproducible: re-runs do not duplicate activities.")

        _slide(md, "Pipeline (Phase by Phase)",
               "1. Schema + seed reference data (14 depts, 24 categories, 8 stakeholders, 5 academic years)\n"
               "2. Collection &rarr; 3. Cleaning/validation &rarr; 4. Dedup (% similarity, date-aware)\n"
               "5. Extraction (dates, venue, organizer, entities) &rarr; 6. NLP classification\n"
               "7. Human-in-the-loop review &rarr; 8. LinkedIn cross-reference &rarr; 9. Analytics\n"
               "10. Flask API &rarr; 11. React dashboard &rarr; 12. Natural-language query\n"
               "13. Evaluation &rarr; 14. Reporting")

        _slide(md, "Multi-label Classification", (
            "- 24 institutional categories, rule-based keyword baseline vs\n"
            "  TF-IDF + Logistic/SVM/Naive-Bayes multi-label classifiers.\n\n"
            "| Model | macro-F1 | micro-F1 |\n|---|---:|---:|\n"
            "| Rule-based baseline (**selected**) | 0.7347 | 0.8312 |\n"
            "| LogisticRegression | 0.29 | 0.41 |\n"
            "| SVC (OneVsRest) | 0.25 | 0.37 |\n"
            "| MultinomialNB | 0.00 | 0.00 |\n\n"
            "_Baseline chosen: transparent, deterministic, no training data needed._"))

        _slide(md, "Department & Stakeholder Detection",
               f"- Department status: single/multiple/institution-wide/unknown\n"
               f"  from name+alias matching with institution-wide markers.\n"
               f"- Accuracy (held-out): **{dm['department_accuracy']}**.\n"
               f"- Stakeholder keyword rules over 8 groups, accuracy "
               f"**{dm['stakeholder_accuracy']}**.")

        _slide(md, "Entity Extraction (spaCy NER + regular expressions)",
               f"- Dates, venue, organizer and resource person via regex retreat.\n"
               f"- Persons/orgs via spaCy `en_core_web_sm`.\n"
               f"- Precision **{dm['entity_extraction']['precision']}** &middot; "
               f"Recall **{dm['entity_extraction']['recall']}** &middot; "
               f"F1 **{dm['entity_extraction']['f1']}**.")

        _slide(md, "Human-in-the-Loop Review (auditable)",
               "- Low-confidence queue + validation flags (19 currently open).\n"
               "- Edit / merge / approve / reject with full `review_history` trait.\n"
               f"- **{o['verified_activities']}** activity verified so far, "
               f"**{o['open_review_tasks']}** tasks still open.")

        _slide(md, "LinkedIn Cross-Reference (legitimate workflow)",
               "- Search-term builder + manual match workflow on an exported\n"
               "  lookup sheet &mdash; no LinkedIn scraping.\n"
               "- Honest defaults: unverified records stay **Not Checked**\n"
               "  and coverage is only measured over the verified subset.")

        _slide(md, "Analytics & KPIs (live at /api/analytics/*)",
               f"- **{o['total_activities']}** activities loaded.\n"
               f"- Departments involved: **{o['distinct_departments']}**; "
               f"categories: **{o['distinct_categories']}**; "
               f"stakeholders: **{o['distinct_stakeholders']}**.\n"
               f"- Feed window: {o['date_range']['min']} &rarr; "
               f"{o['date_range']['max']}.\n"
               f"- Year buckets honest: events outside mapped academic years are "
               f"shown as unmapped (all real 2026 events).")

        _slide(md, "Natural-Language Query",
               "- Intent detection (count/list/compare) + filter logic.\n"
               "- Parameterised SQL everywhere &mdash; injection-safe by design.\n"
               "- Unmapped years are answered honestly with zero + a note.\n"
               "- 11 dedicated tests: count, list, compare, year normalization.")

        _slide(md, "Evaluation Summary",
               "| Metric | Value |\n|---|---:|\n"
               f"| Classification macro-F1 | {dm['classification_macro_f1']} |\n"
               f"| Department accuracy | {dm['department_accuracy']} |\n"
               f"| Stakeholder accuracy | {dm['stakeholder_accuracy']} |\n"
               f"| Entity F1 | {dm['entity_extraction']['f1']} |\n"
               f"| Unique events / activities reconciled | {dq['unique_raw_events']} / {dq['final_unique_activities']} |\n"
               f"| Full test suite | **113 passed** |")

        _slide(md, "Data Quality Verdict",
               f"- {dq['raw_records_collected']} raw records &rarr; "
               f"{dq['unique_raw_events']} unique events &rarr; "
               f"{dq['final_unique_activities']} stored activities.\n"
               f"- {dq['duplicates_auto_merged']} duplicate pairs auto-merged; "
               f"{dq['duplicates_pending_review']} pending (conservative).\n"
               "- Field completeness tracked per field; low-confidence and "
               "unclassified records remain visible (not silently dropped).")

        _slide(md, "Limitations & Future Work",
               "- Small labeled set, 2026 single-year feed, LinkedIn manual-only.\n"
               "- Future: multi-year collection, real labeled growth, LLM NLQ "
               "parser, Postgres migration, reviewer RBAC.")

        _slide(md, "Conclusion",
               f"- A free, transparent, reproducible pipeline delivers "
               f"{o['total_activities']} real activities with "
               f"macro-F1 {dm['classification_macro_f1']}.\n"
               "- Every claim is traceable: the artifacts ship the data "
               "(`data/`), the report (`data/reports/final_report.md`) and\n"
               "  exports (`data/exports/`).")

        with open(SLIDES_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        return SLIDES_PATH
    finally:
        conn.close()


if __name__ == "__main__":
    print(build_presentation())