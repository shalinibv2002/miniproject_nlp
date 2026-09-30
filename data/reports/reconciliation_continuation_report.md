# TCE Activity Intelligence - Reconciliation Continuation - Final Report

_Generated 2026-09-13 10:38 from the live database; every number below is queried, not hardcoded._

## 1. Scope of this continuation

- **Phase A** - NULL-year recovery for achievement/award rows already linked to the official dept award pages (142 candidates inspected, 55 applied, backup taken before mutation).
- **Phase B** - Resolution of the 4 audit rows where the same activity had 2+ plausible periods (2 activities resolved; CSBS multi-cycle 'Best Paper Award' decided earlier as two kept rows).
- **Phases C-L** - Rebuilt matrix, full test regression, department/category/API/frontend/dashboard/NLQ/provenance/security audits against the reconciled DB.

## 2. Global year matrix (final_activity_metadata)

| Academic year | Activities |
|---|---|
| 2021-22 | 166 |
| 2022-23 | 178 |
| 2023-24 | 446 |
| 2024-25 | 372 |
| 2025-26 | 349 |
| None | 830 |
| **Total rows** | **2341** |

- institutional_activities (all sources incl. non-promoted): 2351
- Yearly sums (public periods): 1511
- Rows with no public period (pre-scope/undated, displayed as 'Not available'): 830 (35.5%)

## 3. Phase A - NULL-year recovery (55 applied)

Action `NULL_YEAR_RECOVERY` in the audit trail. Distribution by assigned period:

| Period | Recovered |
|---|---|
| 2021-22 | 2 |
| 2022-23 | 0 |
| 2023-24 | 6 |
| 2024-25 | 9 |
| 2025-26 | 38 |

By department:

| Department | Recovered |
|---|---|
| Artificial Intelligence | 15 |
| Data Science | 11 |
| Applied Mathematics and Computational Science | 9 |
| Computer Science and Engineering | 8 |
| Mechanical Engineering | 5 |
| Information Technology | 4 |
| Chemistry | 2 |
| Electronics and Communication Engineering | 1 |

Remaining NULL rows by department (830):

| Department | NULL rows |
|---|---|
| General | 343 |
| Civil Engineering | 181 |
| Information Technology | 61 |
| Electronics and Communication Engineering | 40 |
| Electrical and Electronics Engineering | 33 |
| Physics | 31 |
| Mechanical Engineering | 30 |
| Chemistry | 24 |
| Computer Science and Engineering | 23 |
| Architecture | 21 |
| Computer Applications | 9 |
| Applied Mathematics and Computational Science | 6 |
| Data Science | 6 |
| Computer Science and Business System | 5 |
| Artificial Intelligence | 3 |
| English and Humanities | 3 |
| Mechatronics | 2 |
| Applied Mathematics and Computational Science; Computer Science and Engineering | 1 |
| Architecture; Computer Applications; Electronics and Communication Engineering; Electrical and Electronics Engineering; Mechatronics | 1 |
| Computer Applications; Mechatronics | 1 |
| Computer Science and Engineering; Computer Applications; Electrical and Electronics Engineering; Mechatronics | 1 |
| Computer Science and Engineering; Electronics and Communication Engineering; Electrical and Electronics Engineering | 1 |
| Electrical and Electronics Engineering; Mechanical Engineering | 1 |
| Electronics and Communication Engineering; Chemistry | 1 |
| Electronics and Communication Engineering; Electrical and Electronics Engineering | 1 |
| Electronics and Communication Engineering; Mechanical Engineering | 1 |

Rationale for the 87 non-recovered: explicit pre-scope years (2016-2020) map outside the public 2021-22..2025-26 taxonomy; tables without any year evidence (ECE 'Fellowship and Medals'); junk numeric-name rows.
Corrections made during page verification vs. raw recon periods: IT Code Tantra -> 2024-25 (recon had 2021-22), math Elite Hyperbolic Geometry -> 2023-24 (recon had 2024-25); 3 excluded (22IT005 junk, 2016 pre-scope, HCL 2018 pre-scope).

## 4. Phase B - Year-conflict resolution (2 activities)

| Activity | Dept | Old | New | Evidence (official page) |
|---|---|---|---|---|
| #2681 | Computer Science and Business System | 2025-26 | 2024-25 | Official CSBS page 'Faculty Achievements 2024-25' (year cell 2025) lists GST Analytics Hackathon Mentor-Appreciation Pri |
| #3207 | Information Technology | 2022-23 | 2021-22 | Official IT page section [h4]2021-22 lists 'Best Paper Award - ICTIEE2022' (ICTIEE 2022); corrected from 2022-23 to 2021 |

CSBS 'Best Paper Award (IC3SEA)' multi-cycle case kept as two rows (#3638/2024-25, #3639/2023-24) per user decision; the GST mentor-appreciation row exists once (2024-25) so a single correction was applied.

## 5. Audit trail provenance

| Action | Count | Meaning |
|---|---|---|
| INSERT | 120 | Achievement/award rows inserted (phase-2) |
| INSERT_SKIP | 39 | Planned rows skipped (section markers, numeric names, no-period, pre-scope) |
| INSERT_SKIP_DUP | 7 | Planned inserts already present (norm title + year + dept) |
| NULL_YEAR_DB | 12 | DB rows flagged NULL-year for the follow-up pass |
| NULL_YEAR_RECOVERY | 55 | Phase A: NULL academic_year recovered from official page |
| PERIOD_CONFLICT_RESOLVED | 2 | Phase B: 2 resolved with official-page evidence |
| PERIOD_FIX | 53 | Phase-2 period correction on existing rows |
| PERIOD_SKIP | 4 | Ambiguous same-activity periods (-> Phase B) |
| STAKEHOLDER_FIX | 5 | Titled faculty rows flipped Students -> Faculty |

Provenance check: all 57 reconciled activity rows have non-empty evidence_text, a source_url, and updated_at; none remains NULL.

## 6. Test regression

| Suite | Result |
|---|---|
| Backend pytest (tests/) | 171 passed |
| Frontend vitest (frontend/) | 43 passed |
| End-to-end API smoke (16 checks) | 16 passed |

## 7. Audit findings (Phases E-L)

| Phase | Outcome |
|---|---|
| E Departments | All stored department_display values canonical or alias-covered; no DB change; multi-department rows normalise per part |
| F Categories | 20 General + 7 Departmental masters enforced at presentation (dimension_fields hides legacy codes); category catalog intentionally reports all 24 stored codes incl. ALUMNI/SYMPOSIUM/STTP/TECH_FEST (recorded as designed + test contract) |
| G API | '/api/departments' and '/api/analytics/departments' now count alias multi-department parts against the canonical master (T'SEDA 163 -> 165) keeping the institutional-activities base (General 815) |
| H Frontend | Pages use the reconciled endpoints; period/Not-available labels consistent; no defects found |
| I Dashboard | Charts read public analytics; yearly/category/dept bars match DB; consistent |
| J NLQ | Grounded parameterised templates; honest zero for out-of-scope years (2019->0); 5-period comparisons; verified live (2024-25->372, 2021->166) |
| K Provenance | 57 reconciled rows all carry evidence + source + updated_at; audit trail complete |
| L Security | No secrets committed; public read contracts whitelisted. **Finding:** '/api/review/*' and 'POST /api/collection/run' are unauthenticated mutating endpoints (CORS '*'). Not changed (tests codify anonymous access); recommended: production RBAC/token + restrict origins + disable debug serving |

## 8. Backups

| File | When |
|---|---|
| data/tce_activity_intelligence_backup_phaseA_before_20260913.db | before Phase A (55 recoveries) |
| data/tce_activity_intelligence_backup_phaseB_before_20260913.db | before Phase B (2 year fixes) |

## 9. Artifacts

- Global matrix: `C:\Users\mlwav\AppData\Local\Temp\opencode\global_achievement_matrix.json`
- Phase A decisions: `C:\Users\mlwav\AppData\Local\Temp\opencode\phaseA_decisions.json`
- Verify: `python -m pytest tests -q` and `frontend: npm test`