# LinkedIn Manual Review — Rule Improvement Analysis (ANALYSIS ONLY)

- Generated: 2026-09-23
- Input: 136 proposals in `linkedin_manual_review_proposals` (staging DB) + 200-record review file `data/audit/linkedin_manual_review_20260923.{md,json,csv}`
- Scope: analysis only. NO rules implemented. NO corrections applied. NO changes to production DB, the 1,544 candidate records, or merged-workbook.xlsx. No frontend/integration work.
- Disclaimer: counts are from the 200-post human-reviewed sample unless stated as "full table" (n=1,544 candidates). No accuracy claim.

---

## A. Summary of all 136 proposals

### A.1 By field and rule

| Rule | Field | Total | Corrections | Notes |
|---|---|---|---|---|
| comm_separation_confirmed | status | 27 | 0 | 27 |
| dept_generic_term | department | 26 | 26 | 0 |
| cat_over_tag:ACHIEVEMENT | category | 21 | 21 | 0 |
| comm_mention_context | category | 20 | 0 | 20 |
| multi_year_keep | date | 15 | 0 | 15 |
| cat_over_tag:RESEARCH | category | 11 | 11 | 0 |
| cat_over_tag:INDUSTRY | category | 4 | 4 | 0 |
| pre_2024_keep | date | 4 | 0 | 4 |
| cat_over_tag:ALUMNI | category | 3 | 3 | 0 |
| multi_label_overlap | category | 3 | 3 | 0 |
| cat_over_tag:INTERNSHIP | category | 2 | 2 | 0 |
| **Total** | | **136** | **70** | **66** |

By field: category 64 · status 27 · department 26 · date 19.
By confidence: high 66 · medium 20 · low 50.
Corrections by field: category 44 (41 over-tag + 3 multi-label) · department 26 · status 0 · date 0.

### A.2 Interpretation

- 66/136 (49%) are CONFIRMATIONS (notes): the existing logic was correct and should be locked in as hard rules (communication separation, date preservation).
- 70/136 (51%) are CORRECTIONS: concentrated in category over-tagging (41) and department over-inference (26).
- Stakeholder: **0 proposals** → no evidence of a problem; leave logic unchanged.

---

## B. Proposed reusable rule improvements

> Each rule below is a RECOMMENDATION for the next classifier iteration. None are implemented at this stage.

### RULE-01 — `comm_separation_lock` (communication → NON_ACTIVITY)

| | |
|---|---|
| Problem | Admission promos, job ads, greetings, thanks must never be classified as activities, even when they contain activity-like words. |
| Evidence | 27/27 sample NON_ACTIVITY posts confirmed correct (14 admission_promo, 8 job_ad, 4 greeting, 1 thanks in sample); group F (embedded event) = 0. Full table: 102 NON_ACTIVITY (41 admission_promo, 31 job_ad, 21 greeting, 9 thanks). |
| Example post IDs | 4, 5, 7, 20, 21, 26, 27, 35, 36, 37 (admissions); 20, 21 (job ads); 26, 60, 169 (greetings) |
| Current behavior | communication_type + `communication_only` flag set; status NON_ACTIVITY; categories may still be attached (see RULE-02). |
| Proposed behavior | Hard rule: communication_type ∈ {admission_promo, job_ad, greeting, thanks, announcement} ⇒ NON_ACTIVITY with no exception path except explicit embedded-event promotion (RULE-02b). |
| Safe to generalize? | **Yes** — 27/27 confirmed, 0 false positives in sample. |
| Risk | FP risk ≈ 0. FN risk: a genuine event hidden inside a promo (group F found 0/27, but keep the promotion check as a guard, do not remove it). |

### RULE-02 — `comm_context_category_suppression`

| | |
|---|---|
| Problem | Communication posts carry category keywords (RESEARCH, INTERNSHIP, ALUMNI…) as *program features*, making them look like activities downstream. |
| Evidence | 20 sample notes (`comm_mention_context`). Full table: 52/102 NON_ACTIVITY posts carry ≥1 category; RESEARCH on 43 NA, ACHIEVEMENT on 25 NA, INTERNSHIP 10, PLACEMENT 10, ALUMNI 8, INDUSTRY 7, CAMPUS 2. |
| Example post IDs | 4 (admissions listing RESEARCH/INTERNSHIP/ALUMNI/INDUSTRY/PLACEMENT), 5, 7, 20, 21 (job ad → RESEARCH), 27, 35, 36, 42, 51 |
| Current behavior | `communication_override:<type>` noted, but category strings remain stored/visible on the candidate row. |
| Proposed behavior | For NON_ACTIVITY rows: suppress categories from display/export (store as `category_context` or clear them); never count them toward activity statistics. |
| Safe to generalize? | **Yes** — display/statistics-level suppression is safe; keep raw values in an internal column for audit. |
| Risk | FP risk low. Guard: if a post is later promoted to activity (RULE-02b), categories must be re-evaluated from text, not restored blindly. |

### RULE-02b — `embedded_event_promotion_guard` (keep alive, do not generalize away)

| | |
|---|---|
| Problem | A genuine event embedded in a communication post must still be promotable to activity. |
| Evidence | Group F = 0/27 in sample — rule never fired, but absence of fires ≠ absence of need. |
| Current behavior | Promotion logic exists (group F). |
| Proposed behavior | Keep; require strong event term + explicit date before promotion. |
| Safe to generalize? | **Keep as guard only** — do not auto-promote; the sample found 0 cases, insufficient evidence to tune thresholds. |
| Risk | Removing it → FN on future embedded events. Auto-enabling it → FP on promos. |

### RULE-03 — `achievement_evidence_gate`

| | |
|---|---|
| Problem | ACHIEVEMENT is the top over-tag: attached to promos, ceremonies, announcements and remembrance posts where nothing was actually achieved/won. |
| Evidence | 21/21 flagged posts are corrections (18% of the 116 activity sample posts; 21/39 group-B posts). Full table: 491/1,280 activity candidates carry ACHIEVEMENT (highest-leverage category). |
| Example post IDs | 29, 747, 1519 (remembrance of founder — not an achievement); 34, 164 (employability/data-science *program promos*); 45, 47, 50, 57, 61 (FDP/course/workshop announcements); 90 (tournament announcement, no result yet); 170, 171 (institutional NBA accreditation news — institutional status, not an activity instance) |
| Current behavior | Keyword-driven (e.g., "proud", "celebrate", "congratulations", "excellence") ⇒ ACHIEVEMENT added, often multi-label. |
| Proposed behavior | Require an *achievement instance*: an award won, a result declared, a person/team recognised, a certification count published. Announcement-of-event, promo, remembrance and pure institutional-status posts do not qualify. |
| Safe to generalize? | **Yes as a review flag / score penalty**; **not as unconditional auto-drop** (sample shows real achievements like #8 NPTEL results, #9 placement selection must keep it). |
| Risk | FP (wrongly dropping real achievements) if auto-applied; FN low if used only as a flag. Confidence on these proposals was mixed — treat as "verify" until scored against human labels. |

### RULE-04 — `research_evidence_gate`

| | |
|---|---|
| Problem | RESEARCH over-tagged on alumni-spotlight, fellowship-award, recognition and greeting posts where "research" only appears in a profile line or institutional title. |
| Evidence | 11/11 flagged = corrections. Full table: 351/1,280 activity candidates carry RESEARCH. |
| Example post IDs | 11, 31 (alumni spotlight profiles mentioning research careers); 12, 15, 25 (award/recognition posts); 13 (internship achievement); 73 (Workers' Day greeting); 40, 73 (day-of observance posts) |
| Current behavior | Keyword presence of research/R&D/fellowship/scholar ⇒ RESEARCH added. |
| Proposed behavior | Require a research *activity instance*: seminar/conclave/paper/journal/funding event or published result. Profile mentions, institutional titles (e.g., SIRO recognition), and fellowship announcements to individuals are not research activities by themselves. |
| Safe to generalize? | **Yes as gate/flag** (posts 69, 89, 92 correctly keep RESEARCH via R&D Cell/Research Council event evidence). |
| Risk | FP if auto-drop: a "congratulations for research grant" post may legitimately be RESEARCH. Use organizer/event evidence first, drop only when none exists. |

### RULE-05 — `industry_partnership_gate`

| | |
|---|---|
| Problem | INDUSTRY added from (a) MoUs with *academic* institutes, (b) the word "Industry" in a hackathon title. |
| Evidence | 4/4 flagged = corrections. Full table: 69 activity candidates carry INDUSTRY. |
| Example post IDs | 17 (MoU with NIT Calicut — academic collaboration, not industry); 18 (academic collaboration announcement); 75 ("Industry Innovation Hackathon" title, partner is the internal IIC); 394 ("AI Fusion" title words) |
| Current behavior | Keyword `industry`, `MoU`, `collaboration` ⇒ INDUSTRY. |
| Proposed behavior | Require an *industry actor*: company name, corporate partner, "in association with <industry body>", sponsored-by-industry. Academic MoUs and title adjectives do not qualify. |
| Safe to generalize? | **Yes** — 4/4 unanimous; clear semantic boundary. |
| Risk | FN if industry actor naming is informal; FP near-zero when actor-name requirement enforced. |

### RULE-06 — `alumni_audience_gate`

| | |
|---|---|
| Problem | ALUMNI added to graduation/training posts where alumni are not the audience/subject. |
| Evidence | 3/3 flagged = corrections. Full table: 179 activity candidates carry ALUMNI (base rate high — gate must be conservative). |
| Example post IDs | 61 (BIM training programme for professionals — not alumni); 140, 149 (Graduation Ceremony 2025 — audience is graduating students, not the alumni body) |
| Current behavior | Keywords "batch", "alumni", "graduation" ⇒ ALUMNI. |
| Proposed behavior | ALUMNI only for: alumni meet/chapter events, alumni spotlight features, alumni-authored or alumni-audience activities. Graduation/farewell = ORIENTATION (or existing kind), not ALUMNI. |
| Safe to generalize? | **Yes** — and note legitimate uses (#115 TCE USA Alumni Meet, #118 alumni congratulation) must survive. |
| Risk | FP moderate if the gate is keyword-only again; require audience semantics (meet/spotlight/chapter). |

### RULE-07 — `internship_event_gate`

| | |
|---|---|
| Problem | INTERNSHIP attached because the word appears as a program feature or résumé line. |
| Evidence | 2/2 flagged = corrections. Full table: 167 activity candidates carry INTERNSHIP (high base rate; sample only flagged 2, so rule must be narrow). |
| Example post IDs | 18 (collaboration announcement listing program features); 46 (research fellowship intro) |
| Current behavior | Keyword `intern`/`internship` ⇒ INTERNSHIP. |
| Proposed behavior | INTERNSHIP only when the post is *about* an internship: posting, completion report, drive, or internship-related event — not a feature bullet inside another activity. |
| Safe to generalize? | **Yes narrowly** — small evidence base (2), so apply as feature-bullet exclusion first, not a broad rewrite. |
| Risk | FN risk if internship-achievement posts (#13-style) are over-pruned; keep when the achievement subject *is* the internship. |

### RULE-08 — `multi_label_same_event_collapse`

| | |
|---|---|
| Problem | One event gets two categories that are format/venue synonyms of each other. |
| Evidence | 3/3 flagged = corrections. Full table: 767/1,280 activity candidates are multi-label (498 with exactly 2) — but only 3 were judged overlapping, so broad collapsing is NOT supported. |
| Example post IDs | 260 (CONFERENCE + WEBINAR — same talk series; keep CONFERENCE); 298 (SYMPOSIUM + TECH_FEST — keep SYMPOSIUM); 586 (CONFERENCE + GUEST_LECTURE — keep GUEST_LECTURE as proposed) |
| Current behavior | Independent keyword labels accumulate. |
| Proposed behavior | Collapse **only within a curated synonym-pair list** (CONFERENCE↔WEBINAR, SYMPOSIUM↔TECH_FEST, CONFERENCE↔GUEST_LECTURE when it is one event) to the dominant format. Distinct event types in one post stay multi-label. |
| Safe to generalize? | **Only for the curated pairs** — 3 instances do not justify a generic overlap merger. |
| Risk | Generic collapsing → high FN (would wrongly flatten legitimate multi-distinct activities, e.g., FDP+SEMINAR). |

### RULE-09 — `department_explicit_evidence_gate` (→ display General)

| | |
|---|---|
| Problem | Department inferred from topic/technology/course names instead of organizer/host evidence. |
| Evidence | 26 department corrections across 14 sample posts (largest non-category finding). Trigger terms: Chemistry 7 · Applied Mathematics & Computational Science 6 · Electrical & Electronics Engineering 6 · Artificial Intelligence 6 · T'SEDA 1. Full table: AC/RR rows carrying these depts — AMCS 88, AI 69, Chemistry 38, EEE 131 (high leverage). |
| Example post IDs | 13 (M.Sc. Data Science topic → AMCS); 50 (materials/chemistry *topic*, organizer is Physics → Chemistry wrongly added); 105, 261 (topic/tech → AI/Chemistry); 17, 400 (MoU/patent topic → EEE); 426 (organizer is CSBS but AMCS+AI inferred); 486, 567, 601, 660 (journal Call-for-Papers fan-out assigns 4 departments each — pure topic match); 586, 242 (scope/topic match) |
| Current behavior | Topic/technology/course keywords mapped to departments; no organizer requirement. |
| Proposed behavior | Department requires **explicit participation evidence**: "Department of X", "organized/hosted by X", "X department invites", department association/club names, or department faculty named as coordinator. Otherwise set department = **General** (display value), keeping raw inference in an internal column for audit. |
| Safe to generalize? | **Yes** — 26/26 unanimous; matches the stated policy (generic technical terminology is not department evidence). |
| Risk | FN when organizer phrasing is unusual ("team from ECE", initials like "Dept. of ECE") — mitigate with alias/initials matcher. FP ≈ 0 because the rule only *removes* unsupported claims. |

### RULE-10 — `stakeholder_no_change`

| | |
|---|---|
| Problem | None observed. |
| Evidence | Group D = 0; 0 stakeholder proposals in 136. |
| Current behavior | Stakeholders inferred from audience/participant phrases. |
| Proposed behavior | **No change.** Re-evaluate only after classifier scored against these human labels. |
| Safe to generalize? | N/A — verification-only. |
| Risk | Changing now would be unevidenced; do nothing. |

### RULE-11 — `date_explicit_only_lock` (multi_year_keep + pre_2024_keep)

| | |
|---|---|
| Problem | Pressure to "resolve" ambiguous multi-year dates, invent dates for undated posts, or infer AY from sheet names. |
| Evidence | 19 date notes (15 `multi_year_keep`, 4 `pre_2024_keep`), all "keep as-is". Full table: 16 multi_year, 4 pre_2024_ambiguous, 829 undated / 699 dated / 16 ambiguous. |
| Example post IDs | multi_year: 333, 392, 393, 394, 395, 414, 415, 419, 486, 533, 567, 586, 601, 660, 1125 · pre_2024: 29, 400, 747, 1519 |
| Current behavior | Explicit dates only (June 1–May 31 AY); ambiguous_multi_year flagged; undated stays undated; pre-2024 flagged. |
| Proposed behavior | Lock current behavior as invariant rules: (1) never assign a date without explicit text evidence; (2) never collapse multi-year posts to one AY; (3) undated ⇒ undated; (4) never infer AY from workbook sheet names/sheet period; (5) pre-2024 stays flagged for scope confirmation, not deleted. |
| Safe to generalize? | **Yes — as preservation constraints (negative rules).** |
| Risk | Any relaxation introduces fabricated dates (high severity). Collapsing multi-year loses real ambiguity (e.g., posts 415/419 spanning Nov 2025–Mar 2026 events). |

### RULE-12 — `weak_evidence_unclear_routing` (recommendation from group G, see section G)

| | |
|---|---|
| Problem | 57 posts sit in REVIEW_REQUIRED with heterogeneous causes; downstream cannot tell *why* they are unclear. |
| Evidence | Group G = 57: 19 weak_text, 6 text_is_url, 5 url_only (empty text), 4 link_less, 1 multi_year, 37 unflagged-but-low-score (0–4). Evidence score: 19×0, 30×1–3, 8×4–7. |
| Example post IDs | url_only/empty: 744, 773, 802, 818, 862 · text-as-URL: 346, 482, 483, 1028, 1090, 1091 · title-only: 789, 821, 822, 830, 860, 884, 931, 1424 · link-less weak: 1424 |
| Current behavior | Single REVIEW_REQUIRED status; flags exist but taxonomy is coarse and 37 posts have no flag at all. |
| Proposed behavior | Attach a machine-readable `unclear_reason`: `url_only` \| `text_is_url` \| `title_only` \| `link_less_weak` \| `low_evidence_event_like` \| `non_latin_unmatched` \| `multi_year`; route url_only/text_is_url to URL-resolve queue, title_only/low_evidence to human queue. |
| Safe to generalize? | **Yes** — routing/metadata only, no classification change. |
| Risk | Low; mis-binned reason codes only affect queue prioritisation. |

---

## C. Category-specific findings

1. **ACHIEVEMENT is the dominant precision problem** — 21 corrections, all four families present: (a) remembrance/memorial posts (29, 747, 1519), (b) program promos (34, 164), (c) event announcements without results (45, 47, 50, 57, 61, 90), (d) institutional status news (170, 171, 1125). Proposal: evidence gate (RULE-03), flag-first.
2. **RESEARCH second** — 11 corrections, driven by profile/recognition/greeting mentions (11, 12, 13, 15, 25, 31, 73) rather than research events. Legitimate uses remain (69 R&D Cell seminar, 89, 92).
3. **INDUSTRY — semantic confusion with academic collaboration** (17, 18) and title adjectives (75, 394). Small but clear-cut: require industry actor (RULE-05).
4. **ALUMNI — audience confusion with graduation/training** (61, 140, 149). High base rate (179) → gate must be audience-semantic (RULE-06).
5. **INTERNSHIP — feature-bullet leakage** (18, 46). Narrow rule (RULE-07).
6. **PLACEMENT / CAMPUS — 0 over-tag flags in sample**; no change proposed beyond the shared attention-category monitoring list.
7. **Multi-label overlap is rare** (3/767 multi-label rows judged overlapping) → collapse only curated synonym pairs (RULE-08). Multi-label itself is NOT a problem to remove: 767/1,280 activity candidates are multi-label and most were accepted (group A contains many multi-label posts: 23, 38, 93, 99…).
8. **Ordering matters**: communication suppression (RULE-02) must run *before* category gates, otherwise NA posts pollute category statistics (52/102 NA posts carry categories).

---

## D. Department-specific findings

1. **26 corrections / 14 posts — zero dissent** (all `dept_generic_term`, all corrections, all high-salience).
2. **Trigger patterns** (what the classifier actually used as "evidence"):
   - *Subject/topic → department*: Data Science → AMCS (13); materials/chemistry words → Chemistry (50, 261, 586); AI/HVAC/robotics words → AI (105); electrical/patent/MoU topic → EEE (17, 400).
   - *Course/program name → department*: STTP "Next Gen Tools" → AMCS+AI although organizer is CSBS (426).
   - *Journal Call-for-Papers fan-out*: one journal CFP assigns Chemistry + AMCS + AI + EEE simultaneously (486, 567, 601, 660 — 16 of the 26 corrections come from just 4 posts × 4 inferred departments).
   - *Festival scope → department*: "7+ Departments" tech fest → T'SEDA (242).
3. **Policy conclusion** (matches review guideline): department must come from explicit organize/host/participate evidence; otherwise the **display value must be General**. Raw inference kept internally.
4. **Also note counter-example**: post 50 *does* name "Department of Physics" explicitly — the correct behavior is keep Physics (or named dept) and drop the inferred Chemistry.
5. **Leverage**: full table carries AMCS 88, AI 69, Chemistry 38, EEE 131 among AC/RR rows — a large share of these are likely topic-inferred and would flip to General under RULE-09. Requires alias/initials matcher to avoid FN ("Dept. of ECE", "T'SEDA", "Mech" etc.).
6. **Display rule**: multi-department lists inferred purely from scope statements (institution-wide events) → General, per review guidelines.

---

## E. Communication / non-activity findings

1. **Communication separation is working**: 27/27 confirmations, 0 corrections, group F = 0. Sample NA composition: admission_promo 14, job_ad 8, greeting 4, thanks 1. Full table NA: 102 (41/31/21/9).
2. **But categories leak into NA rows**: 52/102 NA posts carry ≥1 category label (RESEARCH 43, ACHIEVEMENT 25, INTERNSHIP 10, PLACEMENT 10, ALUMNI 8, INDUSTRY 7, CAMPUS 2). The 20 `comm_mention_context` notes confirm these are program-feature/profile mentions, not activity types → suppress at display (RULE-02).
3. **Worst offenders**: admission promos listing 4–6 categories (post 4: RESEARCH, INTERNSHIP, ALUMNI, INDUSTRY, PLACEMENT, WORKSHOP); job ads tagged RESEARCH/ACHIEVEMENT (20, 21).
4. **Congratulation/thanks posts are split**: as *communications* they are NA (confirmed), but the same wording inside an activity post correctly keeps ACHIEVEMENT (e.g., #118). Context gate must key on post-level communication_type, not sentence-level keywords.
5. **Keep the embedded-event promotion path** (RULE-02b) — unfired in this sample, so do not tune or remove it.
6. **Greeting festival posts in Tamil** (74, 126, 269) currently fell into unclear (kind I) instead of greeting — see section G: greeting lexicon is English-biased.

---

## F. Date / academic-year findings

1. **All 19 date proposals are "keep" notes** — no date corrections proposed; current explicit-date logic validated.
2. **multi_year (15 notes)**: posts with explicit dates in >1 AY (e.g., 392: Dec 27 2025 + Jan 21 2026; 415/419: five dates Nov 2025–Mar 2026; 486/567/601/660: journal issue windows spanning Sep 2025–Jan 2026). Correct action = keep `ambiguous_multi_year`, never collapse to one AY.
3. **pre_2024 (4 notes)**: posts 29, 400, 747, 1519 carry 2023 dates → keep flagged for scope confirmation; do not delete, do not reassign AY.
4. **Undated stays undated** — 829/1,544 full table; no proposals asked to date them (good).
5. **No sheet-name inference** observed anywhere in proposals — preserve the ban (workbook sheet = "June 2025-June 2026" etc. must never assign AY).
6. **Invariants to lock** (RULE-11): explicit-text-dates only; multi-year flagged not collapsed; undated preserved; pre-2024 flagged; sheet-period never used as date evidence.

---

## G. Rules that should NOT be generalized

1. **Do NOT auto-drop over-tagged categories without scoring against human labels.** All 41 over-tag proposals are phrased "verify/remove unless…"; 50 of 136 proposals are low-confidence. Auto-removal now risks false drops of true positives (real achievements/research events coexist in the same keywords).
2. **Do NOT build a generic multi-label overlap merger** — only 3 instances, all within curated synonym pairs (RULE-08 limited form only).
3. **Do NOT touch stakeholder logic** — 0/136 proposals; no evidence either way.
4. **Do NOT auto-promote or auto-demote communication posts** — group F = 0 gives no calibration data; keep promotion as a guarded path only.
5. **Do NOT "fix" ambiguous multi-year or pre-2024 dates** — preservation only (RULE-11); inventing/collapsing dates is prohibited.
6. **Do NOT infer department from scope statements or journal CFP topic lists** — and do not blanket-remove departments when explicit organizer evidence exists (post 50 counter-example).
7. **Do NOT treat review groups A–H as screening kinds A–J** — they are different taxonomies (documented in the review report); any rule must reference `kind` values from `linkedin_activity_candidates`, not review-group letters.
8. **Do NOT delete or rewrite the 1,544 candidate rows based on this analysis** — this stage produces recommendations only; application requires an explicit next-stage approval.

---

## H. Recommended changes for the next classifier iteration

*(analysis-only backlog; not implemented)*

1. **Pipeline order**: communication detection → category gates → department gate → date rules → unclear routing.
2. **Category layer**
   - Add evidence gates RULE-03..07 for ACHIEVEMENT, RESEARCH, INDUSTRY, ALUMNI, INTERNSHIP (flag/score-penalty first; auto-drop only after evaluation against these 200 human labels).
   - Suppress categories on NON_ACTIVITY rows at display (RULE-02); store context categories separately.
   - Add curated synonym-pair collapse list (RULE-08): CONFERENCE↔WEBINAR, SYMPOSIUM↔TECH_FEST, CONFERENCE↔GUEST_LECTURE (single-event only).
   - Keep PLACEMENT/CAMPUS on the watch list (0 sample flags, but base rates 27/58).
3. **Department layer**
   - Implement organizer-evidence requirement with alias matcher ("Department of X", "Dept.", initials ECE/EEE/CSE/MECH/CIVIL, association names, "organized by", coordinator lines).
   - Fallback display value = **General**; raw inference retained in internal column.
   - Special-case: journal CFP posts (scope lists) ⇒ General; institution-wide events ⇒ General.
4. **Stakeholder layer**: no change (RULE-10).
5. **Date layer**: encode RULE-11 as invariant assertions + regression tests (multi-year flag preserved, undated preserved, no sheet-name date source, pre-2024 flagged).
6. **Unclear layer**
   - Adopt `unclear_reason` taxonomy (RULE-12) and split the 57 into queues: URL-resolve (14: url_only/text_is_url/link_less), human-title queue (title-only ~8), low-evidence event-like queue (37 unflagged).
   - Extend greeting lexicon to Tamil festival posts (74, 126, 269) → route to greeting/NON_ACTIVITY instead of REVIEW_REQUIRED.
   - Investigate kind-I cluster of event-like posts (IDE Boot Camp recaps 44/49/53/54/55, inaugurations 108/429, contests 230, series 141/396): these are likely activities missed by the event-term lexicon → candidate additions: "inaugurat*", "boot camp", "contest", "lecture series", "day N".
7. **Evaluation precondition**: score the classifier against the 200 human labels first (groups A–H + the 70 accepted corrections) to measure each rule's precision/recall before any rule is turned on automatically.
8. **Explicit non-goals for this stage**: no DB writes, no candidate edits, no Excel edits, no frontend/integration.

---

## Verification (read-only counts after analysis)

| Metric | Expected | Actual |
|---|---|---|
| institutional_activities | 2,258 | 2,258 ✅ |
| LinkedIn canonical posts | 1,544 | 1,544 ✅ |
| raw occurrences | 2,094 | 2,094 ✅ |
| candidate rows | 1,544 | 1,544 ✅ |
| review sample | 200 | 200 ✅ |

No production table, candidate row, or merged-workbook.xlsx was modified. Analysis stage complete — STOP here.
