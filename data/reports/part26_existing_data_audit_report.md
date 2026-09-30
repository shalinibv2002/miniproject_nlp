# Phase 4 — Existing-Data Audit Report

_Read-only audit of the live TCE database. Generated 2026-09-22. Every number below is computed live by `scripts/audit_existing_data.py` and reconciled against the running API; nothing is hardcoded._

---

## A. What was done

- **Backup created** before touching anything: `data/backups/tce_activity_intelligence_20260921_235429.db` (6.7 MB), so nothing in this phase can be lost.
- **Read-only guarantee.** The audit connects with a read-only `get_connection()`; it does not call `init_db()`, deletes nothing, merges nothing, and does not mutate any metadata. No automatic data changes were applied.
- **Machine-readable output:** `data/audit/existing_data_audit_20260922.json`
- **Human-readable output:** `data/audit/existing_data_audit_20260922.md`
- **Verification method.** Counts reuse the same read-time resolvers as the public UI (`PeriodResolver`, `normalize_department`, public category masters), so the audit numbers reconcile with the live `/api/activities`, `/api/analytics`, and dashboard.
- Duplicate detection uses exact source-URL + exact normalized-title + rapidfuzz `token_sort_ratio` (≥97 LIKELY / ≥93 POSSIBLE) within the same academic period. These are advisory groups; **nothing was deduplicated**.

## B. Verdict up front (checkered flag)

**No.** The current dataset is **not clean enough to begin adding TCE LinkedIn data**. It is structurally solid (100% traced to public sources, all sanity anchors verifiable after explanation), but it has three problems that would corrupt any LinkedIn side-by-side analysis if added now:

1. **~370 records are near-certain true duplicates** (73 exact-title groups involving 158 activities + 240 fuzzy-LIKELY groups), inflation that would double-count activities against LinkedIn matches.
2. **813 (35%) of records sit in the `General`/institution-wide bucket**, and the advisory breakdown shows few have explicit institution-wide evidence — a substantial fraction need a human to confirm they genuinely belong to no specific department.
3. **Key fields are unreliable for matching:** dates are missing for 1,849/2,320 records (80%), ~33% of descriptions are trivial (empty / <20 chars / title echoes), and venue/organizer/resource-person are empty on every record.

Readiness verdict: **Data Quality = "In Progress" — do not start the LinkedIn integration yet.** Recommended order: (1) run the SAFE TO FIX batch (Section J) to remove the clearly-safe duplication/reclassification, (2) run the review queue to its end, (3) re-run `audit_existing_data.py` and only proceed to LinkedIn when the duplicate group count drops below ~20 and General-with-departmental-text drops below ~10. Expected effort: about one to two focused work sessions, not open-ended.

## C. Headline numbers

| Metric | Live value |
|---|---|
| Total activities | **2320** |
| With structured date | 471 (20%) |
| Missing date | **1849 (80%)** |
| With public category | 2308 (99.5%) |
| Missing any category | 4 |
| Missing department field | 10 |
| Missing stakeholder field | 10 |
| Weak/empty descriptions (<20 chars) | 103 |
| Activities with a traceable source | **2320 (100%)** |
| Distinct source URLs | 170 |
| Open review-queue flags | 10 |
| Period-recovery audit rows (from prior phases) | 1480 |

**Period split (resolved, read-time):** 2021-22 = 167 · 2022-23 = 184 · 2023-24 = 444 · 2024-25 = 364 · 2025-26 = 351 · Before 2021 = 810. Note 739 of the "Before 2021" records have **no date and no year evidence** — they are un-dated by nature (mostly seeded department listing pages), not mis-labelled.

## D. Sanity-constant reconciliation

| Check | Live DB | Expected | Result |
|---|---|---|---|
| WORKSHOP (all scopes) | 97 | 97 | ✅ match |
| General (institution-wide) | 813 | 813 | ✅ match |
| 2025-26 Workshops (all scopes) | 10 | 10 | ✅ match |
| 2025-26 IT Achievements | **29** | 50 | ❌ differs |
| 2024-25 T'SEDA | 47 | 47 | ✅ match |

**The IT Achievements difference is fully explained, not an error.** The DB was modified between the Phase-3 verification audits and this one:

- `data/backups/tce_activity_intelligence_pre_stabilization_20260921.db` (the exact DB state Phase-3 audited): **2341 activities, ACHIEVEMENT = 797, IT-2025-26 ACHIEVEMENT = 50**.
- Live DB (mtime 2026-09-21 23:49): **2320 activities, ACHIEVEMENT = 776, IT-2025-26 ACHIEVEMENT = 29**.
- The delta is **exactly 21 in all three** and the 21 removed IDs are all IT-2025-26 ACHIEVEMENT records with low-value titles — e.g. `3250 "22IT017"`, `3259 "22IT120"`, `3310 "14-03-2025"`, `3318 "4/10/2025"`. Nobody added anything (added count = 0).

Conclusion: between the two sessions the dataset shrank by 21 junk-titled IT Award records. The current constants (29) are correct for the live DB. Audit does not pass judgement on whether that deletion was intended; if the 50 was a required census number, those 21 rows are the ones to re-inspect in the backup.

## E. Duplicate audit

These are advisory group detections only — **nothing was deleted or merged.**

- **Exact source-URL groups: 147.** Most are *one page → many distinct activities* (e.g. `tce.edu/campuslife/sports` → ~160 ids, department `achievements` pages → dozens). These are NOT duplicates by themselves; they merely warn that a single listing was split into many records. Only review the fuzzy/exact-title pairs below.
- **Exact normalized-title groups: 73 groups / 158 activities** — e.g. `2nd Place – 4*100m relay` (ids 2754 & 3656), `Finalist – Code feast` (2381 & 3606), `Winner – Hackrax’26` (2775 & 3651). These are genuine duplicates: same title, same period.
- **Fuzzy LIKELY (≥97, same period): 240 groups** — many with 100.0 ratio, e.g. `Two days workshop on "Arduino Unleashed..."` (444 & 458), `Communication, Critical thinking, Collaboration, Creativity` (702 & 711 and 714 & 718), `Leadership Qualities for School Children` (3154 & 3155).
- **Fuzzy POSSIBLE (≥93): 76 groups.**
- **Estimated true-duplicate load:** ~370 records (158 exact + ~240 LIKELY), i.e. **roughly 1 in 6 records currently has a sibling.** This is the single biggest data-quality cost to fix before any LinkedIn reconciliation.
- Schema note: the existing `duplicate_candidates` table (85 rows) has NULL `activity_id_a/b`, so it is not usable to drive Cleanup — new pair generation is required (Section J).

## F. Non-activities / junk records

- Heuristic flags: **26**, e.g. `#1 International Conference on AI in Construction...`, `#2 TEDx Thiagarajar College of Engineering`, `#4 Founder's Day 2026`, `#6 25th Silver Jubilee Reunion...` — marked "no description and no evidence text" (11 of them also carry open `validation-flag: missing-description` review flags, ids 1–10).
- Candidate quality reviews marked NON_ACTIVITY: **0** (the internal review pipeline found 133 NON_ACTIVITY at the *candidate* level during extraction, but none currently flagged at the activity level — that 133 is the better source to mine, see Section J).
- These are advisory. Recommend human review of the 26; the 10 with open review flags are the natural next candidates to quarantine.

## G. Category health (misclassification risk)

- Public category assigned to **2308/2320** records; only 4 have no category rows at all; 12 lack a *public* category.
- **Legacy/non-public codes still stored:** ALUMNI=28, STTP=1, SYMPOSIUM=2. These render without a public label and should be mapped to public categories (or intentionally hidden).
- **Category-vs-text advisory: 129 records** whose text implies a different *specific* category than stored, e.g. `#835 "Best Outgoing NCC Cadet (Girl)"` stored [ACHIEVEMENT,NSS] text-suggests NCC; `#2231 "Best paper award in national conference NITT"` stored ACHIEVEMENT text-suggests CONFERENCE; `#2385 "On-going – BEACON Cohort hackathon"` stored ACHIEVEMENT. Advisory only — each needs a human glance, but the count is significant.
- Multi-category records: 290 (10% carry more than one code; mostly ACHIEVEMENT+secondary). Reasonable for the domain, but LinkedIn matching should rely on a single *primary* category — currently defined as the highest-confidence code.

**Note on the 6-vs-10 Workshops scope question (carried decision):** the all-scope `category` dimension yields 10 for 2025-26 Workshops (matches Reports / Ask-the-Data / `category` filter); the General-scope dashboard card yields 6 (institution-wide Workshops). Both are correct for their scope; this audit confirms both numbers and recommends documenting "all scopes vs General-scope" in the UI help text rather than changing semantics.

## H. The General (institution-wide) bucket — why is it so large?

Total General = **813** (35% of the dataset). Advisory breakdown by evidence:

| Bucket | Count | Reading |
|---|---|---|
| no date but some evidence | 470 | plausibly institutional event text, no date to confirm |
| institution-wide markers (TCE / college-wide / sports day / NCC/NSS…) | 249 | genuinely institution-wide or college-level |
| dated, no clear scope | 58 | has a date, could be either |
| **departmental text present** | **32** | specific dept words in text — *likely should be departmental, currently General* |
| insufficient info (title only) | 4 | cannot classify at all |

The headline: **only 249 of 813 have explicit institution-wide evidence.** Sports (280), Industry (155), Achievement (92), Workshops (82) and Research (71) dominate the bucket. Since these come overwhelmingly from college-level listing pages (annual sports day, IIC, NCC/NSS, placement), many are legitimately institution-wide — but the 32 "departmental text present" records plus a share of the 470 undated ones need human confirmation. Recommendation: review the 32 first (Section J) — they are the cheapest, safest wins.

## I. Dates, descriptions, sources

**Dates**
- Structured dates: only 471/2320 (20%). **1,849 records have no structured date.**
- Invalid structured date: 0. Future date: 1 (2026-12-17, an upcoming event — fine).
- 138 records have "year only" in text; 156 mention multiple years in one record (usually multi-event listing pages).
- No structured date conflicts with a stored academic year (0) — because stored years were set from the same resolve logic.
- **Finding:** period counts rest on the recovery tables (1480 recovery rows, only 112 via ROW_DATE/rows with real dates). 833 records have no stored `academic_year` at all. For LinkedIn, the "as-of year" of a LinkedIn post will rarely match a record that has no real calendar date — expect a large fraction of records to be LinkedIn-untimeable until dates are backfilled where recoverable.

**Descriptions**
- Empty: 10 · short <20 chars: 93 · **description equals/repeats title: 669**.
- Rich fields: achievement_outcome populated on 1,008 (43%); venue 0; organizer 0; resource_person 0 (never extracted/populated). Description quality is the second-biggest fix: ~772 records (~33%) have trivial or no prose.

**Sources/provenance**
- 100% of activities have an `activity_sources` row and a primary `source_url`; 0 untraceable.
- 170 distinct source URLs; 10 registry entries, all active. Top types: TCE Events, TCE Academics, TCE Departments, TCE Sports, TCE NCC, TCE NSS, TCE Clubs, TCE Achievements, TCE Outreach, TCE Newsletter.
- Source pages are TCE's own public site. For LinkedIn this is ideal: each record already has a truthful URL to cite; none are fabricated.

## J. Recommended corrections (categorised)

### SAFE TO FIX (batchable, low-risk, reversible via the backup)
1. **Build a real duplicate-pair table.** The old `duplicate_candidates` rows have NULL activity ids and cannot drive cleanup. Regenerate pairs using exact-title + fuzzy ≥97 within period (est. ~370 records), store as `(activity_a, activity_b, method, score, status=pending)`; start by auto-merging only exact-title pairs within the same period and same category (est. dozens), leaving fuzzy pairs as pending review.
2. **Map the 3 legacy codes** (ALUMNI 28, STTP 1, SYMPOSIUM 2) to public categories (ALUMNI→CLUB or a new public code; STTP→FDP; SYMPOSIUM→CONFERENCE) — with user sign-off on the mapping.
3. **Reclassify the 32 General records with departmental text** from General to their department (target: General drops toward ~781 and those 32 land where their text says).
4. **Backfill dates where recoverable.** 138 records have an unambiguous year in text; set `activity_date` from it (year only) so they become period-verifiable and LinkedIn-aspected. Leave no-date cases alone.
5. **Fill 10 missing department + 10 missing stakeholder fields** from the source candidates when unambiguous.
6. **Quarantine/park the 26 heuristic non-activities and the 10 `validation-flag: missing-description` records** into a "review" status (not deletion) so they stay auditable.

### NEEDS REVIEW (human decision, small FTE)
7. The **129 category-vs-text advisory flags** — each is a 5-second eyeball; batch into the review queue.
8. The **~240 fuzzy-LIKELY duplicate pairs** — confirm before merge (title similarity is high but not always identical).
9. The **58 dated General records with no clear scope** — department or institution-wide? Human answer.
10. Whether the **21 removed IT Award records** (Section D) were intended; if the 50-census is normative, restore from the pre-stabilization backup.

### DO NOT CHANGE
11. **Semantics of the 6-vs-10 Workshops scope** (documented, not changed).
12. **Period buckets** — 739 un-dated "Before 2021" records are honest (they carry no date information); do not invent years.
13. **Auto-merge without a pending pair table** — with ~370 suspects, blind fuzzy-merge is dangerous.
14. **Nothing from the audit** is auto-applied: any cleanup must go through the regular review pipeline so every mutation keeps an audit trail.

## K. Readiness for the LinkedIn integration (full answer)

| Readiness dimension | Status |
|---|---|
| Provenance / trustworthiness | ✅ All 2320 records traced to verified public TCE pages |
| Analysis/runtime reconciliation | ✅ Audit counts match the live API and dashboards 1:1 |
| Sanity anchors | ✅ 4/5 match; 5th explained (21 low-value records removed since census) |
| Review backlog | 🟡 10 open flags + 133 candidate-stage NON_ACTIVITY available to mine |
| Duplicate cleanliness | ❌ ~370 suspected duplicates (1 in 6 records) |
| General/scope accuracy | 🟡 813 General; only 249 show institution-wide evidence; 32 look departmental |
| Surface fields for LinkedIn matching | ❌ 80% missing dates; 33% trivial descriptions; venue/organizer/resource always empty |
| Existing classification confidence | 🟡 129 probable mislabels + 290 multi-category needing a stable primary |

**Bottom line:** the project is **"not yet ready"** to start pulling TCE LinkedIn data. The recommendation is to spend one to two focused sessions on Section J's SAFE TO FIX items (reduces duplicates from ~370 toward ~tens, clears the 32 General/departmental drift, backfills ~138 recoverable dates, parks the junk), then re-run `scripts/audit_existing_data.py`. The checkered flag turns from 🟡 to ✅ when the next audit shows (a) fuzzy+exact duplicate groups < ~20, (b) General-with-departmental-text < ~10, and (c) the review queue is empty. Only then do the analytics accuracy and LinkedIn-workflow build justify the extra source.