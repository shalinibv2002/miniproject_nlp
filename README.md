# Institutional Activity Intelligence and Evaluation System

NLP case study for **Thiagarajar College of Engineering, Madurai**: a free-toolchain
system that collects, cleans, extracts, classifies, reviews, cross-references,
analyses and queries institutional activity records, with a React dashboard, a
Flask REST API, natural-language querying, a formal evaluation, and a final report.

## Stack (100% free)

- **Backend**: Python 3.10, Flask + Flask-CORS, SQLite (row factory), spaCy
  (`en_core_web_sm`), scikit-learn, rapidfuzz, pandas.
- **Frontend**: React 18 + Vite + react-router-dom + recharts; Vitest + Testing Library.
- **Exports**: openpyxl, reportlab.
- **Tests**: pytest (119 tests), Vitest.

## Quick start

```bash
python -m venv .venv && .\.venv\Scripts\Activate.ps1   # Windows
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm

python -m backend.database.init_db    # schema + seed reference data
python -m backend.collectors.tce_events_collector  # collection -> data/raw

# API
python -m backend.app                 # http://localhost:5000  (or python backend/app.py)

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                           # http://localhost:5173 (proxies /api -> :5000)
```

## Reproduce every result (one-liners)

```bash
python -m backend.database.pipeline                          # load/clean/dedup raw data
python -m backend.evaluation.run_evaluation                  # NLP + data-quality metrics
python -m backend.reports.report_generator                   # final_report.md + .xlsx
python -m backend.reports.export_pdf                         # .pdf export
python -m backend.reports.presentation                       # slides (Marp markdown)

python -m pytest -q                                     # 119 tests
cd frontend && npm run test && npm run build
```

## Architecture

```
backend/
  config.py                 # paths, LINKEDIN_* policies, RAW_DATA_DIR
  app.py                    # Flask create_app + route registration
  database/                 # schema, seed, get_connection, pipeline + cleaner/validator
  collectors/               # robots-respecting crawler (public TCE pages)
  nlp/                      # classification, department/stakeholder detection,
                            # entity extraction, retrieval
  review/                   # human-in-the-loop service (edit/merge/approve/reject)
  linkedin/                 # search-term builder + manual-match workflow
  analytics/                # overview/year/department/category/stakeholder/LinkedIn
  evaluation/               # metrics_report, data_quality_report, run_evaluation
  routes/                   # activities, analytics, review, collection, query
  reports/                  # report_generator, export_pdf, presentation
frontend/                   # React dashboard (Vite)
data/
  raw/                      # collected archives (real, public TCE events)
  exports/                  # .xlsx / .pdf deliverables
  reports/                  # final_report.md, presentation.md
  evaluation/               # model_comparison.*, nlp_metrics.*, data_quality_report.*
tests/                      # pytest suite
```

## Deliberate decisions (documented in docs/)

- **Rule-based keyword classifier** is the shipped model (macro-F1 0.7347 vs
  LR 0.29/SVC 0.25/NB 0.00); see `docs/model_selection.md`.
- **Honesty rules**: never fabricate TCE data; unmapped years and unknown
  categories stay visible; LinkedIn defaults to "Not Checked" and is never
  scraped (`LINKEDIN_AUTO_METHOD=manual`).
- **Reproducible pipeline**: re-running `run_pipeline` never duplicates
  activities and resets per-run diagnostics.
- **Injection-safe NLQ**: intent templates + parameterised SQL; unmapped years
  answered as zero with an explicit note.

## Report & slides

- `data/reports/final_report.md` — 31-section case-study report, every number
  computed from the live database.
- `data/exports/tce_activity_intelligence.xlsx` — analytics sheets.
- `data/exports/tce_activity_intelligence_report.pdf` — printable report.
- `data/reports/presentation.md` — deck (open with Marp/reveal).