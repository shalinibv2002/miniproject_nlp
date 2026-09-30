# TCE Activity Intelligence - Final Public UI Refactor - Report

_Generated 2026-09-13 from the live database; every number below is queried, not hardcoded._

## 1. What this refactor did

The public UI is now cleanly separated into **General (institution-wide)** and
**Department (exactly 14)** views, the three legacy category codes are hidden
from every public presentation, and the department master is exactly 14. The
2,351-activity dataset and the "Before 2021" read-time period system are
preserved and untouched.

**Database changed: NO** (row count still 2351; verified before/after).

## 2. Department master - exactly 14

`PUBLIC_DEPARTMENTS` in `backend/database/department_catalog.py` is now exactly
the 14 statutory departments (canonical order):

1. Civil Engineering
2. Chemistry
3. Computer Science and Engineering
4. Computer Science and Business Systems
5. Computer Applications
6. Applied Mathematics and Computational Science
7. Artificial Intelligence
8. Electronics and Communication Engineering
9. Electrical and Electronics Engineering
10. English
11. Information Technology
12. Mechanical Engineering
13. Mechatronics
14. T'SEDA (Architecture, Design, Planning)

Dropped from the old 17: **Fashion Technology, Mathematics, Physics** (no
curricular standing in the final master). Live per-department counts
(`/api/analytics/department`):

| Department | Activities |
|---|---|
| Information Technology | 259 |
| Civil Engineering | 231 |
| Electrical and Electronics Engineering | 205 |
| T'SEDA (Architecture, Design, Planning) | 165 |
| Electronics and Communication Engineering | 129 |
| Computer Science and Engineering | 111 |
| Applied Mathematics and Computational Science | 101 |
| Mechanical Engineering | 76 |
| Computer Science and Business Systems | 61 |
| Mechatronics | 47 |
| Chemistry | 46 |
| Artificial Intelligence | 41 |
| Computer Applications | 33 |
| English | 13 |

- Department universe (each of the 14 counted once): **1497** activities.
- Multi-department rows (`; `-joined) are counted per named department, so the
  per-department total (1518) exceeds 1497.
- **39 historical "Physics" rows are preserved in the database and still
  display "Physics" in the activities list** (least destructive choice); they are
  excluded from the master, selectors, and department analytics. `/api/
  analytics/department?department=Physics` returns 400.

## 3. Categories - 20 public General + 7 Departmental

`/api/categories` now returns the **20 unique public codes** (the 7 departmental
codes are a subset of the 20 general codes). Legacy codes were removed from
`CATEGORY_PUBLIC_NAMES` so they never render as display names.

- **General Categories (20):** Sports, Industry Collaboration, Achievement and
  Awards, Workshops, Research and Consultancy, NCC, NSS, Placement, Cultural,
  Outreach and Extension, Campus, Clubs and Chapters, Conference, Internship,
  Webinar, Seminar, Hackathon, FDP, Orientation, Guest Lecture.
- **Departmental Categories (7):** Achievement and Awards (705), Research and
  Consultancy (526), Industry Collaboration (169), Clubs and Chapters (56),
  Outreach and Extension (44), Workshops (15), Conference (2).
- Legacy usage in the live DB: STTP 1 activity, SYMPOSIUM 2, TECH_FEST 0.
  Exactly **one** activity carries *only* a legacy (SYMPOSIUM) category; it is
  preserved but appears uncategorized publicly (no fabricated category).

## 4. New dashboard analytics endpoints

| Endpoint | Payload |
|---|---|
| `GET /api/analytics/general` | `total_activities`, `periods_covered`, `period_breakdown`, `general_categories`, `year_category_breakdown` (General rows only) |
| `GET /api/analytics/department` | 14-dept overview: `total_activities`, `departments`, `period_breakdown`, `departmental_categories` |
| `GET /api/analytics/department?department=<name>` | One-department detail incl. period breakdown and category trends |
| Guards | `department=General` or `Physics` (or any out-of-master name) -> HTTP 400 |

- `department_analytics` is called with keyword `department=` (positional binds
  to `conn`); `_connection` accepts `*args, **kwargs`; `_year_category_rows`
  default is a `set()`.
- General dashboard live: **815** activities across 5 public periods + Before
  2021 (2021-22: 58, 2022-23: 71, 2023-24: 204, 2024-25: 108, 2025-26: 33,
  Before 2021: 341).

## 5. Frontend changes

- **Dashboard** (`Dashboard.jsx`): two tabs **General Activities | Department
  Activities**, fully driven by the two new analytics endpoints (no client-side
  recompute of the dataset). Department tab has `Select Department` (All + 14)
  bound to the global filter; no "General" option. Tab styles added to
  `index.css`.
- **Layout**: department filter now reads `All Departments` + exactly 14 (no
  General); stale "General" branch removed.
- **Categories**: two sections, **General Categories** (from
  `/api/general-categories`, 20) and **Departmental Categories** (from
  `/api/departmental-categories`, 7); drills via `general_category` /
  `departmental_category` filters.
- **Departments**: lists exactly 14; drill now uses the derived
  `departmental_category` field so only the 7 departmental category names drive
  the category step; never displays "General" or dept codes.
- Public copy uses **General Activities / Department Activities / General
  Categories / Departmental Categories**; there is no "Scope" anywhere.

## 6. Verification

- Backend: `python -m pytest tests -q` -> **193 passed** (incl. 7 new
  separation tests: exactly-14 master, 20 public codes only, General/isolation
  never mixes, legacy never exposed, Before-2021 presentation survives).
- Frontend: `npx vitest run` -> **46 passed / 9 files** (Dashboard, Layout,
  Categories, Departments updated for the new split).
- Lint: `npx oxlint src` -> warnings only (all pre-existing patterns or
  non-blocking).
- Build: `npx vite build` -> succeeds (pre-existing chunk-size notice only).
- Live smoke against the running server: all new endpoints return the expected
  shapes/guards above; no legacy codes appear in any payload the UI consumes;
  activities filters (`general_category`, `departmental_category`,
  `department+category`) return only General or only the requested department.

## 7. Issues / notes

- The sole legacy-only (SYMPOSIUM) activity is intentionally uncategorized in
  the public UI; the row and its provenance remain in the database.
- The 39 Physics rows remain as stored (no relabeling); they are visible only
  in the activities list as "Physics" and excluded from analytics/master.
- `filter`-ing via a hand-typed `category=<legacy code>` URL still resolves at
  the data layer (provenance); no public UI path constructs such a URL.
- Rows with no stored year still resolve to a public period ("Before 2021") at
  read time, so the six buckets always sum to the universe; no "Not available"
  bucket is exposed.