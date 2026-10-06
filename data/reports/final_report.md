# TCE Institutional Activity Intelligence and Evaluation System

## Final Case-Study Report (Thiagarajar College of Engineering, Madurai)

_Generated 2026-10-06 16:43 from the live database — every number below is computed, not hardcoded._


## 1. Executive Summary

Presents the purpose, method, principal results, and data-quality verdict of the Activity Intelligence System in five lines.

**Measured results (this build):**

| Metric | Value |
|---|---|
| Total activities loaded | 7 |
| Verified activities | 3 |
| Open review tasks | 0 |
| Classification macro-F1 (rule-based, held-out) | 0.7347 |
| Department detection accuracy | 0.8 |
| Entity extraction F1 | 0.8 |

## 2. Introduction and Objectives

Problems addressed (scattered institutional activity records), the objectives of collection-extraction-classification-analytics across a free toolchain.


## 3. Case Study Context: Thiagarajar College of Engineering

Institutional context: 17 departments, multi-stakeholder outreach, public events pages as the primary lawful source.

**Reference data:** 17 departments; 24 categories; 8 stakeholder groups; 5 academic years (2020-2021 … 2024-2025).

## 4. Related Work and Literature Review

Positioning relative to institutional analytics dashboards, keyword baselines vs. TF-IDF multi-label classification, rule-based NLQ.


## 5. Methodology Overview

14-phase build: schema, collection, cleaning, extraction, classification, review, cross-reference, analytics, API, UI, NLQ, evaluation, reporting.


## 6. System Architecture

SQLite relational core, Python/Flask backend, React/Vite frontend, rule-based NLP with spaCy + scikit-learn.


## 7. Data Sources and Collection

Verified public TCE pages (robots.txt-respecting crawler); events page as the primary lawful feed.

**Collection outcome:**
| Item | Value |
|---|---|
| Raw archive JSON snapshots | 4 |
| Raw archive records | 26 |
| Unique raw events | 10 |

## 8. Data Cleaning and Validation

Unicode/whitespace/punctuation normalisation, HTML stripping, date standardisation, validation flags.


## 9. Deduplication Strategy

FuzzyWRatio title similarity, date consistency; auto-merge only at ≥95 with matching dates, else pending review.

**Dedup outcome (latest pipeline run):**
| Item | Value |
|---|---|
| Duplicate pairs auto-merged (≥95 + same date) | 0 |
| Duplicate pairs pending review (≥70) | 0 |

## 10. Information Extraction

regex retreat in dates/venue/organizer, spaCy NER for persons/orgs, dictionary+fuzzy department matching.


## 11. NLP Multi-label Classification

24 institutional categories; rule-based keyword baseline vs TF-IDF logistic/SVM/NB multi-label classifiers.

**Model comparison (held-out test split, Phase 5 / 13):**
| Model | macro-F1 | micro-F1 |
|---|---|---|
| Rule-Based Keyword Baseline | 0.7347 / 0.8312 |
| TF-IDF + LogisticRegression (OvR) | 0.2917 / 0.4091 |
| TF-IDF + LinearSVC (OvR) | 0.25 / 0.3721 |
| TF-IDF + MultinomialNB (OvR) | 0.0 / 0.0 |
| Selected model | Rule-Based Keyword Baseline |
| Training corpus size | 110 |

## 12. Model Selection and Evaluation

Held-out macro-F1 comparison; the rule-based baseline selected with documented, reproducible numbers.

**Model comparison (held-out test split, Phase 5 / 13):**
| Model | macro-F1 | micro-F1 |
|---|---|---|
| Rule-Based Keyword Baseline | 0.7347 / 0.8312 |
| TF-IDF + LogisticRegression (OvR) | 0.2917 / 0.4091 |
| TF-IDF + LinearSVC (OvR) | 0.25 / 0.3721 |
| TF-IDF + MultinomialNB (OvR) | 0.0 / 0.0 |
| Selected model | Rule-Based Keyword Baseline |
| Training corpus size | 110 |

## 13. Department Detection

Single/multiple/institution-wide/unknown classification from name + alias matching with institution-wide markers.


## 14. Stakeholder Detection

Keyword-driven association of activities to the 8 stakeholder groups.


## 15. Human-in-the-Loop Review

Low-confidence queue, field edit, merge, approve/reject, full review_history audit trail.


## 16. LinkedIn Cross-Reference

Free, legitimate workflow: search-term building, manual verification subset, honest 'Not Checked' defaults.


## 17. Analytics and KPIs

Overview, year, department, category, stakeholder, LinkedIn, and data-quality aggregates, all computed live.


## 18. Flask REST API Design

Pagination, validation, parameterised SQL, structured logging, consistent JSON errors.

**Exposed endpoints:** `/api/activities`, `/api/activities/:id`, `/api/years`, `/api/departments`, `/api/categories`, `/api/stakeholders`, `/api/analytics/{overview, yearly, departments, categories, stakeholders, linkedin, data-quality}`, `/api/search`, `/api/review`, `POST /api/review/:id/{edit,approve,reject,linkedin}`, `POST /api/collection/run`, `POST /api/query`.

## 19. React Dashboard

Vite + React + recharts; global filters; KPI cards and charts driven entirely by /api/analytics/* responses.


## 20. Natural-Language Query System

Plug-in safe, parameterised templates from intent-filters; no freeform SQL; 'unmapped year' answered honestly as 0.


## 21. Five-Year Trend Analysis

Seeded academic years with honest handling of events beyond the mapped window.

**Yearly breakdown (mapped academic years):**
| Academic Year | Activities | Verified |
|---|---|---|
| 2020-2021 | 0 / 0 |
| 2021-2022 | 0 / 0 |
| 2022-2023 | 0 / 0 |
| 2023-2024 | 0 / 0 |
| 2024-2025 | 0 / 0 |

## 22. Department-wise Analysis

Involvement and primary counts per department, with multi-department reconciliation.

**Department involvement (top rows):**
| Department | Involvement | Primary |
|---|---|---|
| Automobile Engineering | 0 / 0 |
| Chemistry | 0 / 0 |
| Chemical Engineering | 0 / 0 |
| Civil Engineering | 0 / 0 |
| Computer Science and Engineering | 0 / 0 |
| Electronics and Communication Engineering | 0 / 0 |
| Electrical and Electronics Engineering | 0 / 0 |
| English and Humanities | 0 / 0 |
| Fashion Technology | 0 / 0 |
| Information Technology | 0 / 0 |

## 23. Category-wise Analysis

Classification counts, primary counts, mean confidence per category.

**Categories by classification count (top rows):**
| Category | Count | Primary | Avg conf |
|---|---|---|---|
| Workshop | 5 / 0 / None |
| Achievement and Award | 1 / 0 / None |
| Research and Consultancy | 1 / 0 / None |
| Alumni Event | 0 / 0 / None |
| Campus Life | 0 / 0 / None |
| Clubs and Chapters | 0 / 0 / None |
| Conference | 0 / 0 / None |
| Cultural Event | 0 / 0 / None |
| Faculty Development Programme | 0 / 0 / None |
| Guest Lecture | 0 / 0 / None |

## 24. Stakeholder-wise Analysis

Involvement counts, primary counts, mean confidence per stakeholder group.

**Stakeholders:**
| Stakeholder | Involvement | Primary | Avg conf |
|---|---|---|---|
| Students | 3 / 0 / None |
| Alumni | 0 / 0 / None |
| Community and Society | 0 / 0 / None |
| Faculty | 0 / 0 / None |
| Government and Agencies | 0 / 0 / None |
| Industry | 0 / 0 / None |
| Parents | 0 / 0 / None |
| Non-Teaching Staff | 0 / 0 / None |

## 25. LinkedIn Visibility Analysis

Match-status breakdown; coverage measured only over the manually verified subset.

**LinkedIn match-status breakdown:**
| Status | Count |
|---|---|
| Manual-verification coverage ratio | 0 |

## 26. Data Quality Assessment

Field completeness, unknown category/department counts, low-confidence records, review backlog, collection failures.

**Completeness (fraction of fields filled):**
| Field | Filled / total |
|---|---|
| date_present | 6 / 7 |
| venue_present | 0 / 7 |
| organizer_present | 0 / 7 |
| description_present | 5 / 7 |
| source_present | 5 / 7 |
| confidence_present | 3 / 7 |
| no_mapped_academic_year | 7 / 7 |
**Flags:**
| Item | Value |
|---|---|
| Collection errors open | 0 |
| Review backlog | 0 |
| LinkedIn unmatched/unchecked | 0 |
| Records with no mapped academic year | 7 |

## 27. Evaluation and Validation

Reproducible NLP metrics (macro/micro F1, department/stakeholder accuracy, entity P/R/F) plus pipeline reconciliation.

| Metric | Value |
|---|---|
| Classification macro-F1 | 0.7347 |
| Classification micro-F1 | 0.8312 |
| Department accuracy | 0.8 |
| Stakeholder accuracy | 0.8 |
| Entity precision | 0.6667 |
| Entity recall | 1.0 |
| Entity F1 | 0.8 |

## 28. Limitations

Small labeled corpus, single-year 2026 feed for the case study, LinkedIn manual-only workflow, no LLM dependency.


## 29. Ethical and Data-Integrity Considerations

No fabricated records; only verified public sources; no LinkedIn scraping; audit history on every mutation.


## 30. Future Work

Collecting more years, growing real labeled data, LLM-only parsing step for NLQ, Postgres migration on free tier, RBAC for reviewers.


## 31. Conclusion

The system meets the case-study objective with a free, transparent, reproducible toolchain.

**Verdict:** a free, transparent, reproducible pipeline that loads 7 real activities, classifies them with macro-F1 0.7347, and stands fully auditable via its review_history audit trail.