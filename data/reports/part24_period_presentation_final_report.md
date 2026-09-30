# TCE Activity Intelligence — Part 24: Period Presentation ("Before 2021") — Final Report

_Generated 2026-09-13 from the live database; every number below is queried from the live DB or the pinned test suite, not hardcoded._

## 1. Scope of this part

This part finalises how academic periods are *presented* on the public site. The stored dataset is unchanged (2,351 activities, 2,341 metadata rows — no rebuild, no rescrape). Prior phases wrote the authoritative stored `academic_year` for 1,511 rows. This part makes the remaining rows recoverable and transparent by resolving a period at **read time** and grouping everything that predates the stored window (or cannot be reliably placed) under a single public **`Before 2021`** bucket. The public UI now exposes periods as **All + five academic years + Before 2021** — the legacy "Not available" filter has been removed from public filters.

## 2. Period model after this part

Every public period value is a resolved, bucketised value produced by `backend/database/period_catalog.py` (`PeriodResolver`). Resolution priority for each activity:

1. Stored `academic_year` (public five-year key) wins when present.
2. Otherwise, a real structured `activity_date` maps to its academic year (2020/earlier → `Before 2021`; 2021-2025 → matching year; 2026 → 2025-26).
3. Otherwise, `activity_date_text` when it carries a single unambiguous year.
4. Otherwise, `evidence_text` when it carries a single unambiguous year.
5. Otherwise → **`Before 2021`** (the historical/unresolved bucket).

### Resolved six-bucket distribution (live DB, via `/api/analytics/overview` → `period_breakdown`)

| Period | Activities |
|---|---|
| 2021-22 | 167 |
| 2022-23 | 179 |
| 2023-24 | 446 |
| 2024-25 | 373 |
| 2025-26 | 368 |
| Before 2021 | 818 |
| **Total** | **2351** |

The six buckets sum exactly to the 2,351-activity universe. This complements (and differs from) the stored-year matrix (166/178/446/372/349 + 830 with no stored year), which remains available as `yearly_breakdown`; the two are intentionally separate so both views stay accurate.

## 3. Confirmed pre-2021 vs grouped unresolved

- **29 activities** were individually confirmed (via fixed-evidences rows) to be genuinely pre-2021 activities from earlier TCE data; all 29 sit inside the `Before 2021` bucket.
- **`Before 2021` contains 818 rows in total.** The remaining rows are older or undated records whose only available year signals are missing, ambiguous (year spans), or embedded inside long ID strings that the resolver deliberately rejects. **The report deliberately does NOT claim all 818 are confirmed pre-2021 activities** — only 29 are evidence-confirmed; the rest are grouped historically because no reliable in-window period can be established.

## 4. Public behaviour changes

- **Filters (`/api/activities`):** `academic_year` now accepts short keys (`2021-22`), full labels (`2021-2022`), `Before 2021` variants (`before 2021`, `prior to 2021`, `pre-2021`), and the legacy `Not available` spelling. The five public keys **and** `Before 2021` filter through the resolved activity-id set, so a recovered row appears in the same period the UI labels it with. `Not available` keeps its historical `academic_year IS NULL` semantics (test DB expectations preserved).
- **Period filter no longer leaks:** public filters expose only All + five years + `Before 2021`; a recovered/undated row shows `Before 2021` instead of `Not available`.
- **List/detail:** `academic_year` on every public item is now the resolved value (`2021-22`…`2025-26` or `Before 2021`), never `Not available`. Each of the five evidence-audited rows resolves to its audited period (305→2021-22, 2367→2022-23, 348→2024-25, 666→2025-26, 3435→2025-26).
- **NLQ (`/api/query`):** "before 2021 / prior to 2021 / pre-2021" queries are intercepted before year parsing so they answer the historical bucket and never collapse to the 2021-22 period. Period-filtered NLQ results use the same resolved id sets, and returned activities carry the resolved public period.
- **List/item key sets are unchanged** (exact key-contract preserved: `id, title, description, activity_date, activity_date_text, academic_year, department, general_category, departmental_category, stakeholder, achievement_outcome, categories, source_url`). `evidence_text` is used internally for resolution and is never exposed.
- **Dashboard:** "Activities by Period" now renders the resolved six-bucket `period_breakdown` when present, falling back to `yearly.yearly_breakdown` for older responses. The total KPI remains the stored total.

## 5. Frontend changes

- **New shared module:** `frontend/src/lib/periods.js` — `PERIOD_LABELS`, `ALL_PERIODS`, `periodLabel()` (unknown → `Before 2021`).
- **`Layout.jsx` + `index.css`:** complete restyle to the official TCE maroon identity — maroon top header with brand mark + horizontal nav, cream/white body, charcoal text, grey borders, maroon accents/gold KPI trim, restrained shadow and rounding, accessible mobile nav with hamburger toggle. Filter toolbar (Period, Department, General Category, Departmental Category, Sort Order, Reset) now includes a **`Before 2021`** option; the public `Not available` period option was removed.
- **Pages:** `Activities`, `ActivityDetails`, `Query`, `Categories`, `Departments` share `periodLabel` (fallback `Before 2021`). `Dashboard` uses `period_breakdown` with fallback and maroon/red chart colors.

## 6. Files modified / created in this part

**Backend**
- `backend/database/period_catalog.py` — top-level `get_connection` import; `ids_in_clause()` chunked IN-helper; `normalize_period` fixes (hyphen-insensitive matching, `prior to 2021` cue, default handling).
- `backend/routes/activities.py` — added `m.evidence_text` to `_base_select`; `_filters(conn)` resolves period params to id sets (legacy `Not available` → NULL); `_public_row` emits the resolved `academic_year`.
- `backend/analytics/public.py` — new `period_breakdown` (six resolved buckets) added to `/api/analytics/overview`; `yearly_breakdown` untouched.
- `backend/nlp/query_engine.py` — `before 2021` cue interception; period filters via resolved id sets; `_public_rows` resolves `academic_year`.

**Tests**
- `tests/test_periods.py` — **new** (15 tests): resolution rules, public filters, detail, overview bucket sums, NLQ before-2021 interception.

**Frontend**
- `frontend/src/lib/periods.js` — new shared period module.
- `frontend/src/components/Layout.jsx`, `frontend/src/index.css` — maroon restyle + `Before 2021` option.
- `frontend/src/pages/Dashboard.jsx`, `Activities.jsx`, `ActivityDetails.jsx`, `Query.jsx`, `Categories.jsx`, `Departments.jsx` — shared period labels / breakdown.
- `frontend/src/components/Layout.test.jsx`, `frontend/src/pages/Activities.test.jsx`, `frontend/src/pages/ActivityDetails.test.jsx` — updated to `Before 2021` expectations.

## 7. Verification results

| Check | Result |
|---|---|
| Backend tests (`pytest tests -q`) | **186 passed** (171 existing + 15 new) |
| Frontend tests (`vitest run`) | **43 passed** (9 files) |
| Lint (`oxlint`) | clean; only pre-existing style warnings |
| Production build (`vite build`) | **success** (10.77 kB css / 650.50 kB js) |
| Live smoke (list/filter/detail/overview/NLQ/years) | **passed** — `period_breakdown` sums to 2,351; before-2021 filter total 818; audited details resolve correctly; NLQ "before 2021" = 818; `/api/years` still exactly 5 entries |
| Leak scan (10 public endpoints) | **clean** — no `scope/confidence/candidate/classifier/verification/review/sql/intent/evidence_text` |
| Item key-set contract | **exact** on all + before-2021 payloads |
| Period values | always one of the five keys or `Before 2021`; never `Not available` |
| Dataset universe | validated at 2,351 activities / 2,341 metadata rows (unchanged) |

## 8. Intentionally unchanged (documented, not regressions of this part)

- `/api/review/*` and `POST /api/collection/run` remain as shipped in earlier phases (developer-only workflows; outside the public scope this part touches).
- Vite chunk-size warning (>500 kB) is pre-existing and cosmetic; no behavioural impact.

## 9. Summary

The stored dataset is untouched and final at 2,351 activities. Read-time period resolution now yields a clean public six-period presentation (167 / 179 / 446 / 373 / 368 / 818 = 2,351), the public period model is fully wired end-to-end (API → NLQ → dashboard → list/detail → filters), and the site carries the official TCE maroon visual identity. 29 activities are evidence-confirmed pre-2021; the 818-row `Before 2021` bucket deliberately includes undated/ambiguous records that cannot be reliably placed in the five-year window, and this distinction is not overstated in the UI or this report.