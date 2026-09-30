# Final LinkedIn Reportable Dataset — Audit Report

- Generated: 2026-09-28T15:01:21
- Database: `backend/database/linkedin_reportable.db`
- Scope: canonical LinkedIn posts only; never merged with the 2,258 website activities

## Source

- Workbook: `D:\miniproject_nlp\backend\database\merged-workbook.xlsx`
- Workbook SHA-256: `ca6a57ee907ec3fba45a7d5e02086d4253ecd3c371103b50d33f0f308a358cbc`
- Sheets: April 2024 - June 2025, June 2025-June 2026, Jan - Sep 2025, May - June 2026, Sep to Dec 2025
- Raw workbook rows: 2319

## Staging

- Canonical posts: 1747
- Duplicate occurrences: 572
- Candidates: 1747
- PENDING_REVIEW sample: 200

## Classification (final reportable status)

| Status | Count |
|---|---|
| REPORTABLE | 1398 |
| NON_ACTIVITY | 121 |
| REVIEW_REQUIRED | 228 |

### Category occurrence counts (REPORTABLE only)

- RESEARCH: 404
- ACHIEVEMENT: 338
- SEMINAR: 235
- ALUMNI: 216
- INTERNSHIP: 191
- WORKSHOP: 190
- CLUB: 176
- GUEST_LECTURE: 85
- INDUSTRY: 81
- OUTREACH: 74
- CONFERENCE: 68
- FDP: 66
- CAMPUS: 64
- CULTURAL: 62
- SPORTS: 61
- HACKATHON: 54
- WEBINAR: 49
- ORIENTATION: 44
- PLACEMENT: 31
- NSS: 17
- SYMPOSIUM: 12
- NCC: 9
- TECH_FEST: 9
- STTP: 3

### Department occurrence counts (REPORTABLE only)

- Electronics and Communication Engineering: 160
- Electrical and Electronics Engineering: 125
- Computer Science and Engineering: 118
- Mechanical Engineering: 108
- Civil Engineering: 91
- Mechatronics: 61
- T'SEDA (Architecture, Design, Planning): 60
- General: 55
- Computer Science and Business Systems: 53
- Applied Mathematics and Computational Science: 52
- Information Technology: 47
- Artificial Intelligence: 27
- Chemistry: 25
- English: 16
- Computer Applications: 13

### Stakeholder occurrence counts (REPORTABLE only)

- Students: 1022
- Faculty: 554
- Industry: 283
- Community and Society: 264
- Alumni: 209
- Government and Agencies: 151
- Parents: 5
- Non-Teaching Staff: 3

## Dates

- dated: 845
- undated: 886
- ambiguous multi-year: 16
- Convention: academic_year assigned ONLY for single explicit dates; June 1 - May 31; no invented dates/years.

Academic-year distribution (reportable only):

- 2023-24: 10
- 2024-25: 261
- 2025-26: 328
- 2026-27: 118
- 2027-28: 1

Reportable activities by month (reliable dates only):

- 2023-08: 1
- 2024-04: 6
- 2024-05: 3
- 2024-06: 4
- 2024-07: 14
- 2024-08: 8
- 2024-09: 13
- 2024-10: 21
- 2024-11: 20
- 2024-12: 13
- 2025-01: 19
- 2025-02: 25
- 2025-03: 44
- 2025-04: 43
- 2025-05: 37
- 2025-06: 12
- 2025-07: 15
- 2025-08: 29
- 2025-09: 23
- 2025-10: 20
- 2025-11: 28
- 2025-12: 35
- 2026-01: 26
- 2026-02: 28
- 2026-03: 32
- 2026-04: 45
- 2026-05: 27
- 2026-06: 15
- 2026-07: 21
- 2026-08: 57
- 2026-09: 24
- 2026-10: 1
- 2027-12: 1

## Provenance

- URL-verified posts: 1012
- Link-less posts: 735
- URL coverage: 57.93%
- Source sheet distribution:
  - All posts: 203
  - April 2024 - June 2025: 532
  - Jan - Sep 2025: 293
  - June 2025-June 2026: 718
  - Sep to Dec 2025: 1
- Occurrences: single=1261 multi=486

## Integrity

- No duplicate final activity IDs: **True**
- No invalid categories: **True**
- No invalid departments: **True**
- No invalid stakeholders: **True**
- No impossible academic years: **True**
- All final records traceable to staging: **True**

## Counting semantics

- `unique total activities` = REPORTABLE rows (stable regardless of filters).
- category / department / stakeholder counts are OCCURRENCE counts;
  an activity carrying N categories counts once in each of those N buckets.
- The public dashboard total, filtered lists and every analytics endpoint are
  computed from this same dataset.
