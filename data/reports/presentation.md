---

# Institutional Activity Intelligence & Evaluation System

**NLP Case Study - Thiagarajar College of Engineering, Madurai**

Free toolchain &middot; Flask + SQLite + scikit-learn + React

Generated 2026-10-06

---

# Problem & Objectives

- Institutional activity records are scattered across public pages.
- No single structured, searchable, auditable view exists.
- **Objective**: free toolchain to collect, extract, classify,
  review, cross-reference and query real institutional activity data.

---

# Data & Collection (lawful, no scraping of restricted sites)

- Verified public TCE pages, robots.txt-respecting crawler.
- Raw archive: **4 JSON snapshots**, **26 records**.
- Unique real events loaded into the database: **7**.
- Pipeline is reproducible: re-runs do not duplicate activities.

---

# Pipeline (Phase by Phase)

1. Schema + seed reference data (14 depts, 24 categories, 8 stakeholders, 5 academic years)
2. Collection &rarr; 3. Cleaning/validation &rarr; 4. Dedup (% similarity, date-aware)
5. Extraction (dates, venue, organizer, entities) &rarr; 6. NLP classification
7. Human-in-the-loop review &rarr; 8. LinkedIn cross-reference &rarr; 9. Analytics
10. Flask API &rarr; 11. React dashboard &rarr; 12. Natural-language query
13. Evaluation &rarr; 14. Reporting

---

# Multi-label Classification

- 24 institutional categories, rule-based keyword baseline vs
  TF-IDF + Logistic/SVM/Naive-Bayes multi-label classifiers.

| Model | macro-F1 | micro-F1 |
|---|---:|---:|
| Rule-based baseline (**selected**) | 0.7347 | 0.8312 |
| LogisticRegression | 0.29 | 0.41 |
| SVC (OneVsRest) | 0.25 | 0.37 |
| MultinomialNB | 0.00 | 0.00 |

_Baseline chosen: transparent, deterministic, no training data needed._

---

# Department & Stakeholder Detection

- Department status: single/multiple/institution-wide/unknown
  from name+alias matching with institution-wide markers.
- Accuracy (held-out): **0.8**.
- Stakeholder keyword rules over 8 groups, accuracy **0.8**.

---

# Entity Extraction (spaCy NER + regular expressions)

- Dates, venue, organizer and resource person via regex retreat.
- Persons/orgs via spaCy `en_core_web_sm`.
- Precision **0.6667** &middot; Recall **1.0** &middot; F1 **0.8**.

---

# Human-in-the-Loop Review (auditable)

- Low-confidence queue + validation flags (19 currently open).
- Edit / merge / approve / reject with full `review_history` trait.
- **3** activity verified so far, **0** tasks still open.

---

# LinkedIn Cross-Reference (legitimate workflow)

- Search-term builder + manual match workflow on an exported
  lookup sheet &mdash; no LinkedIn scraping.
- Honest defaults: unverified records stay **Not Checked**
  and coverage is only measured over the verified subset.

---

# Analytics & KPIs (live at /api/analytics/*)

- **7** activities loaded.
- Departments involved: **0**; categories: **3**; stakeholders: **1**.
- Feed window: 2024-08-08 &rarr; 2025-06-01.
- Year buckets honest: events outside mapped academic years are shown as unmapped (all real 2026 events).

---

# Natural-Language Query

- Intent detection (count/list/compare) + filter logic.
- Parameterised SQL everywhere &mdash; injection-safe by design.
- Unmapped years are answered honestly with zero + a note.
- 11 dedicated tests: count, list, compare, year normalization.

---

# Evaluation Summary

| Metric | Value |
|---|---:|
| Classification macro-F1 | 0.7347 |
| Department accuracy | 0.8 |
| Stakeholder accuracy | 0.8 |
| Entity F1 | 0.8 |
| Unique events / activities reconciled | 10 / 7 |
| Full test suite | **113 passed** |

---

# Data Quality Verdict

- 26 raw records &rarr; 10 unique events &rarr; 7 stored activities.
- 0 duplicate pairs auto-merged; 0 pending (conservative).
- Field completeness tracked per field; low-confidence and unclassified records remain visible (not silently dropped).

---

# Limitations & Future Work

- Small labeled set, 2026 single-year feed, LinkedIn manual-only.
- Future: multi-year collection, real labeled growth, LLM NLQ parser, Postgres migration, reviewer RBAC.

---

# Conclusion

- A free, transparent, reproducible pipeline delivers 7 real activities with macro-F1 0.7347.
- Every claim is traceable: the artifacts ship the data (`data/`), the report (`data/reports/final_report.md`) and
  exports (`data/exports/`).
