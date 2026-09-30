# LinkedIn Incremental Import Audit - June-September 2026

Generated: 2026-09-28T22:07:44

## 1. Source workbook

| Field | Value |
|---|---|
| File | `backend\database\Posts From June 2026 - September 2026.xlsx` |
| SHA-256 | `f20868b7d1ee3c452e324074265ec1954efd18835d0ec0a2fc96ada39851d563` |
| Size | 68515 bytes |
| Sheet used | `All posts` |
| Layout | row 1 blank, row 2 export title banner, rows 3-227 = 225 posts |
| `Post link` column | absent |
| Embedded shortened URLs | 11 |
| LinkedIn activity IDs | not present (resolved by text matching) |

## 2. What changed

The workbook was appended to the existing staging layer. No historical row was reloaded, replaced or renumbered, and no classifier or category rule was changed.

| Metric | Before | After | Delta |
|---|---|---|---|
| Staging canonical posts | 1544 | 1747 | +203 |
| Staging occurrences | 2094 | 2319 | +225 |
| Reportable rows | 1544 | 1747 | +203 |
| REPORTABLE | 1227 | 1398 | +171 |
| NON_ACTIVITY | 112 | 121 | +9 |
| REVIEW_REQUIRED | 205 | 228 | +23 |
| Manually validated | 16 | 16 | 0 |
| Approved | 13 | 13 | 0 |

## 3. Deduplication of the 225 incoming rows

| Outcome | Rows | Treatment |
|---|---|---|
| New canonical posts | 203 | Imported and classified |
| Existing exact-text duplicates | 21 | Occurrence recorded against the already-committed post; no new post |
| Within-file near duplicate | 1 | Collapsed onto its owner in the same file (WRatio 97.1) |
| Possible duplicates vs history | 0 | None found, so nothing was held back for duplicate review |
| Export title banner | 1 | Skipped, not a post |

Rule applied: exact normalized-text equality against committed staging. Within-file near duplicates collapse at WRatio >= 95 and length ratio >= 0.80. A near-match against already-committed history would be flagged `POSSIBLE_DUPLICATE_REVIEW` and never silently merged, because merging would rewrite historical posts.

## 4. Classification of the 203 new posts

| Class | Count |
|---|---|
| Activity -> REPORTABLE | 171 |
| NON_ACTIVITY | 9 |
| REVIEW_REQUIRED | 23 |
| Undated (no explicit date) | 57 |

Dates were never invented: a post is dated only where the text states a date. Undated posts are visible in the admin layer but excluded from date-based reporting.

## 5. Academic year 2026-27 (the newly covered year)

| Measure | Count |
|---|---|
| REPORTABLE in AY 2026-27 | 118 |
|   of which from the new workbook | 115 |
| NON_ACTIVITY in AY 2026-27 | 9 |
| REVIEW_REQUIRED in AY 2026-27 | 20 |
| Dated rows, all statuses | 147 |
| June-Sep 2026 reportable posts | 114 |

The 115th new-workbook post in AY 2026-27 carries an October 2026 date, which is why the strict June-September count is 114. Both are genuinely dated posts, not re-dated history.

June-September 2026 is genuinely present, not folded into another year: months covered are `2026-06`, `2026-07`, `2026-08`, `2026-09`.

Reportable totals by academic year:

| Academic year | Before | After | Delta |
|---|---|---|---|
| 2023-24 | 10 | 10 | +0 |
| 2024-25 | 261 | 261 | +0 |
| 2025-26 | 325 | 328 | +3 |
| 2026-27 | 3 | 118 | +115 |
| 2027-28 | 0 | 1 | +1 |

Category spread across AY 2026-27 (multi-label, so labels exceed activity count):

| Category | Count |
|---|---|
| RESEARCH | 31 |
| SEMINAR | 31 |
| ALUMNI | 16 |
| INTERNSHIP | 16 |
| CLUB | 12 |
| OUTREACH | 12 |
| CONFERENCE | 11 |
| GUEST_LECTURE | 11 |
| ACHIEVEMENT | 9 |
| ORIENTATION | 9 |
| WORKSHOP | 9 |
| INDUSTRY | 6 |
| WEBINAR | 6 |
| CAMPUS | 5 |
| FDP | 4 |
| CULTURAL | 2 |
| HACKATHON | 2 |
| SPORTS | 2 |
| NSS | 1 |
| PLACEMENT | 1 |
| STTP | 1 |

Departments contributing in AY 2026-27: Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Civil Engineering, Computer Applications, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering, General, Information Technology, Mechanical Engineering, Mechatronics, T'SEDA (Architecture, Design, Planning).

Stakeholders in AY 2026-27: Alumni, Community and Society, Faculty, Government and Agencies, Industry, Non-Teaching Staff, Parents, Students.

## 6. Provenance

A `source_workbook` column was added additively to `linkedin_posts` and `linkedin_post_occurrences`. Historical rows were backfilled as `merged-workbook.xlsx`, so every post and every raw row remains traceable to the file it came from.

| Source workbook | Canonical posts | Occurrences |
|---|---|---|
| merged-workbook.xlsx | 1544 | 2094 |
| Posts From June 2026 - September 2026.xlsx | 203 | 225 |

## 7. What was preserved

- 12 duplicate normalized-text groups pre-date this import; they are distinct activity IDs, and none involve the new sheet.
- 8 undated historical records carry academic years via pre-existing manual overrides; these are intentional and were left untouched.
- All 16 manual-override records are byte-for-byte identical before and after, including reviewer attribution and validation history.
- Historical per-sheet occurrence counts are unchanged.
- `linkedin_posts` ids were never renumbered, so existing `staging_post_id` references stay valid.
- The 24-category vocabulary is unchanged and no new category code was introduced.
- The production website database `data/tce_activity_intelligence.db` was never opened for writing; its SHA-256 still starts with `FD3C77F876B11D18`.

## 8. Verification performed

| Check | Result |
|---|---|
| Data consistency checks | 38/38 passed |
| Backend test suite | 375 passed |
| Frontend test suite | 119 passed (24 files) |
| Frontend lint | 0 errors, 31 pre-existing warnings |
| Frontend production build | success |
| Real-data API smoke test | 64 checks, 64 passed, 0 failed |

The real-data smoke test exercises Dashboard, activity detail, categories, departments, stakeholders, academic years, filters, analytics, report preview and export, Ask the Data, and the admin layer (login, summary, review queue, per-record detail, and a manual override round trip) against the live databases, with no mocks. The smoke run snapshots both live DBs and restores them on exit, so verification leaves the data byte-identical.

Public API responses were checked to expose only the intended public fields; internal evidence and review columns remain admin-only.

## 9. Records needing human review

23 posts from the new workbook are `REVIEW_REQUIRED` and are waiting in the admin review queue. They are deliberately not published. 9 new posts are classified NON_ACTIVITY and 57 are undated.

## 10. Files

- `backend/database/linkedin_incremental_import.py` - new append-only importer
- `backend/database/linkedin_reportable.py` - provenance-aware reportable build
- `backend/database/linkedin_staging.db` - updated staging database
- `backend/database/linkedin_reportable.db` - updated reportable database
- `tests/test_linkedin_incremental_import.py` - importer tests (8)
- `data/backup/linkedin_staging_20260928_145221.db` - pre-import staging backup
- `data/backup/linkedin_reportable_20260928_145221.db` - pre-import reportable backup
