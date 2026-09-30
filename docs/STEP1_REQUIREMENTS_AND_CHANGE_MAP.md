# Step 1 — Frozen Requirements and Incremental Change Map

## Purpose and boundaries

This document freezes the requirements for the **NLP-Based Institutional
Activity Intelligence and Evaluation System** for Thiagarajar College of
Engineering (TCE).  The official TCE website is the primary dataset; LinkedIn
is secondary, optional cross-reference only.

The agreed primary analytical period is academic years **2021–22 through
2025–26**, using a configurable **August–July** academic-year boundary.  This
is not a calendar-year analysis.  2020–21 is outside the primary five-year
scope unless explicitly added later.

This is a planning artefact.  It intentionally makes no database, collector,
frontend, NLP, or data changes.

## Incremental implementation decision

The current application can be modified incrementally; a rewrite is not
required. Retain the Flask application factory/routes, React/Vite shell,
SQLite migration path, activity/source relationship pattern, raw archive
format, review history, report/export utilities, and test harness. Replace or
extend only the components that conflict with these requirements.

## Requirement-to-component map

| Current component | Current behaviour | Required behaviour | Decision | Reason / dependency |
|---|---|---|---|---|
| `backend/collectors/tce_events_collector.py` | Crawls one Events URL; CLI limits to 10; no discovery/pagination | Discover relevant official public pages/documents and collect source-specific activity data with diagnostics | Modify; add source collectors | Define source inventory and crawl policy first |
| `backend/collectors/base_collector.py` | Polite fetch/retry/raw archive support | Shared crawl telemetry for discovered/processed/failed pages and PDFs | Modify | Reuse fetch/archive foundations |
| `backend/database/pipeline.py` | Loads raw JSON, validates, dedupes, writes activities | Preserve source provenance, merge source occurrences, apply correct academic year | Modify | Schema migration and source record contract first |
| `backend/database/schema.sql` | Activity/category/department/stakeholder/source links exist | Add/extend academic-year configuration, source title/section/date, source occurrences, participant/programme/detail fields and crawl diagnostics | Modify via migrations | Do not discard existing data/tables |
| `backend/database/seed_reference_data.py` | 2020–25 years; non-required taxonomy/master values | Seed 2021–22…2025–26, required categories, department master and stakeholder model | Modify | Confirm exact aliases and migration strategy first |
| `backend/nlp/classify.py` / training files | Keyword baseline plus small synthetic evaluation corpus | Multi-label required taxonomy; evaluate on reviewed real TCE records | Modify | Taxonomy and real review labels first |
| Department/stakeholder detectors | Existing masters and internal status terminology | Evidence-only mapping to agreed masters; General/Institution-wide and clean stakeholder values | Modify | Master-data migration first |
| `backend/nlp/extractors.py`, `enrich.py` | Basic dates, venue, organizer, entities, keywords | Capture available programme, participants, achievement/award/competition details, source metadata | Extend | Source-specific parsers feed reliable fields |
| `backend/database/deduplicator.py` | Pairwise title/date dedupe, diagnostics without candidate activity IDs | Cross-source duplicate candidates and merged source occurrences | Modify | Stable source occurrence identifiers required |
| `backend/analytics/*` | Live aggregates but unusable five-year buckets | Coverage-qualified five-year, category, department, stakeholder and trend summaries | Modify | Correct date/year and real collection first |
| `backend/nlp/query_*` | Safe templates, but only simple count/list/limited compare | Correct questions about high/low year, trends and all required dimensions | Extend | Analytics/query semantics after schema/master updates |
| `backend/linkedin/*` | Manual, secondary non-scraping queue | Keep secondary and optional; never gate TCE records | Keep with minor UI/API adaptation | Existing safety model is aligned |
| `frontend/src/pages/*` | Generic dashboard/reference tables; exposes confidence and department status | Institutional results UI; clean departments, View Source, five-year and specialist analyses; no NLP internals | Modify | Backend response contract first |
| `frontend/src/services/api.js`, layout/UI primitives | Shared API access, routing and layout | Continue to use for incremental new views | Keep | Existing integration works |
| Reports/evaluation | DB-derived artifacts but unsupported coverage claims and synthetic NLP metrics | Coverage-qualified reports; separate field completeness from source coverage; use real evaluation set | Modify | Data coverage and reviewed labels first |
| Tests | Strong synthetic unit/API checks | Add fixture-based official-page/PDF, pagination, AY-boundary, provenance, and real-sample regression tests | Extend | Preserve current unit tests |

## Frozen user-facing rules

- Present institutional results, not model/keyword/TF-IDF/confidence internals.
- UI department display is clean name(s), or consistently `General` when no
  source-supported department exists; do not expose cardinality/status labels.
- Activities may have multiple categories/departments/stakeholders internally.
- Every activity retains official source URL and a user-facing View Source
  affordance when appropriate.
- Never fabricate activities, URLs, LinkedIn matches, dates, departments, or
  coverage claims.

## Required implementation order

1. Freeze source inventory, taxonomy, master data, source-record contract and
   academic-year configuration.
2. Add compatible schema migrations and revise pipeline/dedup/provenance.
3. Implement discovery plus source-specific official-site/PDF collectors with
   telemetry; collect only after this design is reviewed.
4. Upgrade extraction/classification/detection and build reviewed real-data
   evaluation samples.
5. Implement analytics/NLQ semantics, then simplify and extend the frontend.
6. Make reports and tests coverage-aware; regenerate exports only from the
   validated database.
