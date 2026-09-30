# Step 9 — Public LinkedIn Activity Portal

## Objective

Ship the public-facing **LinkedIn Institutional Activity Reporting** site: a
fully data-driven portal that reports on the FINAL printable LinkedIn activity
dataset, side-by-side with the existing admin console. Public visitors get a
dashboard, browsable activities with drill-down filters, category / department /
stakeholder digests, filterable reports, and an honest "Ask the Data" natural
language interface. Internal validation machinery stays inside the admin
console at `/admin`.

## Data-source rule (hard constraint)

- Public pages read **only** `/api/linkedin/*`, which serves **only**
  `backend/database/linkedin_reportable.db` (the isolated, FINAL reportable
  dataset: 1,280 reportable activities, coverage ≈ Apr 2024 – Jun 2026).
- Nothing public queries or merges `data/tce_activity_intelligence.db` (the old
  2,258-row website dataset) or the staging/workbook databases.
- Verify-inside: NLQ and list endpoints share `filters_fragment` /
  `count_reportable` / `analytics_*`, so "1 reportable activity = 1 total"
  never diverges across pages.

## Public pages and routes (`frontend/src/main.jsx`)

Public routes are **not** auth-gated and live under `LinkedinPublicLayout`; the
admin console remains behind `RequireAdmin` at `/admin`.

| Route | Page | Source |
|---|---|---|
| `/` | `LinkedinPublicDashboard` | `/api/linkedin/analytics/overview` |
| `/activities` | `LinkedinPublicActivities` | `/api/linkedin/filters` + `/api/linkedin/activities` |
| `/activities/:activityId` | `LinkedinPublicActivityDetail` | `/api/linkedin/activities/:id` |
| `/categories` | `LinkedinPublicCategories` | `/api/linkedin/categories` |
| `/departments` | `LinkedinPublicDepartments` | `/api/linkedin/departments` |
| `/stakeholders` | `LinkedinPublicStakeholders` | `/api/linkedin/stakeholders` |
| `/reports` | `LinkedinPublicReports` | `/filters` + `/analytics/overview?<filters>` |
| `/query` | `LinkedinPublicQuery` | `POST/GET /api/linkedin/query` |

`Login` stays public; old public pages and the old `Layout.jsx` remain as files
but are no longer routed (their direct-import tests still pass).

## Additions and modifications

### Backend

- **`backend/nlp/linkedin_query.py`** (new) — NLQ engine with keyword grounding
  maps (`CATEGORY_KEYWORDS`, `DEPARTMENT_KEYWORDS`, `STAKEHOLDER_KEYWORDS`),
  `YEAR_RE` with a `(?!-\d)` guard, and intents: count, list, rank, compare,
  breakdown. Every aggregation reuses the reportable helpers so counts always
  reconcile with the dashboard. Configuration/balancing today:
  - list limit 20 activities; sorting date-desc first.
  - Honest zero handling: unavailable year (e.g. `1999-00`) → `status: "answer"`,
    `count: 0`, answer states "no available records exist for academic year …
    (available: …)". No-match grounding → `status: "zero"`.
  - **Sparse-attribution honesty:** ranking by a dimension (e.g. department)
    where matching activities exist but none carry that attribution now answers
    "N matching activities exist, but none name a specific department in the
    post text (based on available TCE LinkedIn posts)" instead of a misleading
    "no matching activities" (see `_answer_ranking`).
- **`backend/routes/linkedin_public.py`** (modified) — added
  `GET/POST /api/linkedin/query`: 400 on missing / >500 char questions, and the
  response is whitelisted to `{question, status, answer, count, activities,
  comparison, rows, chart, criteria, detail}`. The old website `/api/query`
  route is untouched.
- **`tests/test_linkedin_reportable.py`** (modified) — 9 new NLQ tests
  (missing/long question 400, count via category, list + privacy projection,
  ranking, honest ranking without attribution, compare, breakdown,
  unavailable-year honest zero, zero-result); suite: **344 passed** (was 335).

### Frontend

- **`src/components/LinkedinPublicLayout.jsx`** (new) — public shell with brand,
  nav (Dashboard, Activities, Categories, Departments, Stakeholders, Reports,
  Ask the Data), honest footer ("Based on available TCE LinkedIn posts"), and a
  `Staff login` link → `/admin/login`. No admin/internal links.
- **`src/components/linkedinPublic.jsx`** (new) — shared `Chart` (recharts bars,
  accent `#a03252`), `BarList`, `LoadingState` / `ErrorState` / `EmptyState`,
  `ClickableCountList` (count + share + drill link).
- **Eight new page components** under `src/pages/linkedin/` (see route table).
  Highlights:
  - Activities: filter panel driven by `/filters`; Apply/Reset keep the URL in
    sync via `useSearchParams` (deep-linkable); 12/page with pager.
  - Reports: filterable overview with KPI total + "Reliably Dated" share and
    by-year/by-category/by-department/by-stakeholder breakdowns.
  - Ask the Data: input + example chips, renders answer, criteria tags,
    activity cards, chart/rows and comparison table from one response shape.
- **`src/main.jsx`** (modified) — public routes under `LinkedinPublicLayout`,
  admin under `RequireAdmin`; removed old imports of the superseded pages/layout.
- **`src/lib/linkedin.js`** (modified) — public label helpers
  (`publicCategoryLabel` + `PUBLIC_CATEGORY_FALLBACK`, `publicDepartmentLabel`
  (empty → General), `publicSourceLabel`, `formatPublicDate`,
  `dateStatusSummary`).
- **`src/index.css`** (modified) — public filter-panel, activity-card grid,
  clickable-count-list, query form, detail card, pager + responsive styles.
- **Tests** — `publicFixtures.js` + 7 test files (`LinkedinPublicLayout`,
  `Dashboard`, `Activities`, `ActivityDetail`, `Dimensions`, `Reports`,
  `Query`): **23 tests** added; full frontend suite **114 passed** (was 91).
  Chart-bearing pages assert static BarList/KPI DOM, not recharts tick marks.

## Correctness and privacy invariants

- **Single source of truth:** all public counts derive from the reportable DB
  at runtime; no hard-coded numbers anywhere. Verified against the real DB
  (temp copy): total 1,280; categories sum 2,425 because multi-label records
  count once per label — every drill-down still reconciles with the shared
  count (smoke step 9: filtered API total == `count_reportable`).
- **Date limitation labelled honestly:** "Date-based charts include only
  reliably dated posts"; undated records (829) are counted in totals but
  excluded from date-based charts.
- **Privacy projection:** public records expose only activity_id, title,
  description, post_url, date, year, categories, departments, stakeholder,
  source. Evidence/confidence/validation/provenance/staging fields are never
  rendered (frontend tests assert absence of internal labels).

## Public vs admin separation

The admin console (`/api/admin/linkedin/*`, pages under `LinkedinAdmin*`) holds
all validation/evidence/override machinery; the public portal renders only the
read-only projection. `RequireAdmin` still guards `/admin`; public pages carry
no auth. Smoke verified admin login still works at `/admin/login`.

## Verification

- Backend: `python -m pytest tests -q` → **344 passed**.
- Frontend: `npx vitest run` → **114 passed (24 files)**; `npm run lint`
  warnings-only; `npm run build` succeeds.
- Manual smoke (23 steps, temp copy of the real DB, read-only):
  overview totals = 1,280, projections clean of internal keys, combined-filter
  counts reconcile, detail 404, dimensions, empty results, NLQ count == shared
  count, sparse-year honesty, unavailable-year honesty, whitelisted response
  keys, empty-question 400.

## Files changed

- `backend/nlp/linkedin_query.py` (new), `backend/routes/linkedin_public.py`,
  `tests/test_linkedin_reportable.py`.
- `frontend/src/components/LinkedinPublicLayout.jsx`,
  `frontend/src/components/linkedinPublic.jsx`,
  `frontend/src/pages/linkedin/LinkedinPublicDashboard.jsx`,
  `LinkedinPublicActivities.jsx`, `LinkedinPublicActivityDetail.jsx`,
  `LinkedinPublicCategories.jsx`, `LinkedinPublicDepartments.jsx`,
  `LinkedinPublicStakeholders.jsx`, `LinkedinPublicReports.jsx`,
  `LinkedinPublicQuery.jsx` plus 7 `*.test.jsx` files and `publicFixtures.js`,
  `frontend/src/main.jsx`, `frontend/src/index.css`,
  `frontend/src/lib/linkedin.js`.

## Remaining notes

- Departments/stakeholders breakdowns reflect only attribution found in post
  text; records without attribution are silently absent from those charts
  (they are still in totals). The NLQ ranking now says so explicitly.
- `dist/` is a build artefact; chunk-size is above 500 kB (pre-existing,
  warning only).