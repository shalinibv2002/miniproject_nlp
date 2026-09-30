# LinkedIn Rule Implementation Validation (RULE-01..12)

- Generated: 2026-09-23T20:46:45
- Scope: NON-PRODUCTION validation on the **200 reviewed sample posts** only.
- No candidate rows, staging candidate table, production database or merged-workbook.xlsx were written or changed.
- Rules implemented: RULE-01 (comm lock), RULE-02 (category context-only), RULE-03..07 (category gates, flag-first), RULE-08 (curated multi-label pairs), RULE-09 (dept explicit-organizer gate -> General), RULE-12 (unclear taxonomy).
- Rules unchanged: RULE-02b (embedded-event guard stays in review layer), RULE-10 (stakeholder no-change), RULE-11 (date preservation).

## 0. Production safety invariants (read-only verification)

| Metric | Expected | Actual | OK |
|---|---|---|---|
| institutional_activities | 2258 | 2258 | OK |
| linkedin_posts | 1544 | 1544 | OK |
| linkedin_post_occurrences | 2094 | 2094 | OK |
| linkedin_activity_candidates | 1544 | 1544 | OK |
| review_sample_pending | 200 | 200 | OK |
| proposals | 136 | 136 | OK |
| merged-workbook.xlsx sha256 | ca6a57ee907ec3fba45a7d5e02086d4253ecd3c371103b50d33f0f308a358cbc | ca6a57ee907ec3fba45a7d5e02086d4253ecd3c371103b50d33f0f308a358cbc | OK |

Baseline classifier output matches the 200 stored candidate rows: **True**

## A. Proposal addressment (136 proposals)

By rule (total -> addressed):

| Rule | Total | Addressed |
|---|---|---|
| comm_separation_confirmed | 27 | 27 |
| dept_generic_term | 26 | 26 |
| cat_over_tag:ACHIEVEMENT | 21 | 21 |
| comm_mention_context | 20 | 20 |
| multi_year_keep | 15 | 15 |
| cat_over_tag:RESEARCH | 11 | 11 |
| cat_over_tag:INDUSTRY | 4 | 4 |
| pre_2024_keep | 4 | 4 |
| cat_over_tag:ALUMNI | 3 | 3 |
| multi_label_overlap | 3 | 3 |
| cat_over_tag:INTERNSHIP | 2 | 2 |

Correction addressment details:

| Post | Field | Rule (confidence) | Addressed | Mechanism |
|---|---|---|---|---|
| 11 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 12 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 13 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 13 | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) |
| 15 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 17 | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 17 | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) |
| 18 | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 18 | category | cat_over_tag:INTERNSHIP (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 25 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 29 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 31 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 32 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 34 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 40 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 45 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 46 | category | cat_over_tag:INTERNSHIP (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 47 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 50 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 50 | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) |
| 57 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 61 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 61 | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 69 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 73 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 75 | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 89 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 90 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 92 | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 105 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 140 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 140 | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 149 | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 164 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 166 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 170 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 171 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 187 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 242 | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) |
| 253 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 260 | category | multi_label_overlap (low) | yes | curated same-event pair collapsed |
| 261 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 298 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 298 | category | multi_label_overlap (low) | yes | curated same-event pair collapsed |
| 394 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 394 | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 400 | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) |
| 426 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 426 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 486 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 486 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 486 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 486 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 567 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 567 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 567 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 567 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 586 | department | dept_generic_term (low) | yes | explicitly named in post; kept per review guideline 'unless the post names this department' |
| 586 | category | multi_label_overlap (low) | yes | curated same-event pair collapsed |
| 601 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 601 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 601 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 601 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 660 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 660 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 660 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 660 | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) |
| 747 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 1125 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |
| 1519 | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) |

Unaddressed corrections: **0**

## B. Before / after counts (200 posts)

### B.1 candidate_status

| Status | Before | After |
|---|---|---|
| ACTIVITY_CANDIDATE | 116 | 116 |
| NON_ACTIVITY | 27 | 27 |
| REVIEW_REQUIRED | 57 | 57 |

### B.2 category candidates

| Category | Before | After |
|---|---|---|
| ACHIEVEMENT | 53 | 53 |
| ALUMNI | 14 | 14 |
| CAMPUS | 10 | 10 |
| CLUB | 15 | 15 |
| CONFERENCE | 11 | 10 |
| CULTURAL | 10 | 10 |
| FDP | 5 | 5 |
| GUEST_LECTURE | 9 | 9 |
| HACKATHON | 11 | 11 |
| INDUSTRY | 8 | 8 |
| INTERNSHIP | 16 | 16 |
| NCC | 6 | 6 |
| NSS | 6 | 6 |
| ORIENTATION | 7 | 7 |
| OUTREACH | 7 | 7 |
| PLACEMENT | 7 | 7 |
| RESEARCH | 43 | 43 |
| SEMINAR | 11 | 11 |
| SPORTS | 7 | 7 |
| STTP | 2 | 2 |
| SYMPOSIUM | 7 | 7 |
| TECH_FEST | 6 | 5 |
| WEBINAR | 6 | 5 |
| WORKSHOP | 15 | 15 |

### B.3 department display (new; RULE-09)

- `(none)` -> 109 posts
- `Electronics and Communication Engineering` -> 12 posts
- `Electrical and Electronics Engineering` -> 10 posts
- `T'SEDA (Architecture, Design, Planning)` -> 10 posts
- `General` -> 8 posts
- `Information Technology` -> 7 posts
- `Computer Science and Engineering` -> 6 posts
- `Applied Mathematics and Computational Science` -> 5 posts
- `Mechanical Engineering` -> 5 posts
- `Civil Engineering` -> 4 posts
- `Civil Engineering, Mechanical Engineering, Computer Science and Engineering, Electronics and Communication Engineering` -> 4 posts
- `Mechatronics` -> 4 posts
- `Computer Science and Business Systems` -> 2 posts
- `Electrical and Electronics Engineering, Civil Engineering, Electronics and Communication Engineering, Information Technology, Mechanical Engineering, Mechatronics` -> 2 posts
- `Applied Mathematics and Computational Science, Computer Science and Business Systems, Computer Science and Engineering` -> 1 posts
- `Applied Mathematics and Computational Science, Computer Science and Engineering, Civil Engineering, Computer Applications, Computer Science and Business Systems, Electronics and Communication Engineering, Information Technology, Mechanical Engineering, Mechatronics, T'SEDA (Architecture, Design, Planning)` -> 1 posts
- `Chemistry` -> 1 posts
- `Civil Engineering, Mechanical Engineering, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering` -> 1 posts
- `Civil Engineering, Mechatronics, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering` -> 1 posts
- `Computer Science and Business Systems, Computer Science and Engineering` -> 1 posts
- `Computer Science and Business Systems, Computer Science and Engineering, Electronics and Communication Engineering` -> 1 posts
- `Computer Science and Engineering, Information Technology` -> 1 posts
- `Electrical and Electronics Engineering, Civil Engineering, Electronics and Communication Engineering` -> 1 posts
- `English` -> 1 posts
- `T'SEDA (Architecture, Design, Planning), Civil Engineering` -> 1 posts
- `T'SEDA (Architecture, Design, Planning), Computer Science and Engineering, Civil Engineering, Electronics and Communication Engineering` -> 1 posts

### B.4 unclear_reason (new; RULE-12)

- `(none)` -> 143 posts
- `link_less_weak` -> 1 posts
- `low_evidence_event_like` -> 38 posts
- `multi_year` -> 1 posts
- `non_latin_unmatched` -> 3 posts
- `text_is_url` -> 6 posts
- `title_only` -> 3 posts
- `url_only` -> 5 posts

### B.5 new flags added by the gates

| Flag | After |
|---|---|
| category_context_only | 20 |
| category_gate:ACHIEVEMENT | 21 |
| category_gate:ALUMNI | 3 |
| category_gate:INDUSTRY | 4 |
| category_gate:INTERNSHIP | 2 |
| category_gate:RESEARCH | 11 |
| dept_to_general | 8 |
| multi_label_collapsed:conference | 1 |
| multi_label_collapsed:tech_fest | 1 |
| multi_label_collapsed:webinar | 1 |
| unclear:link_less_weak | 1 |
| unclear:low_evidence_event_like | 38 |
| unclear:multi_year | 1 |
| unclear:non_latin_unmatched | 3 |
| unclear:text_is_url | 6 |
| unclear:title_only | 3 |
| unclear:url_only | 5 |

## C. Corrections match table (70 corrections)

Addressed: **70 / 70**

| Post | Grp | Field | Rule (conf) | Addressed | Mechanism | old -> new (categories) |
|---|---|---|---|---|---|---|
| 11 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,ALUMNI,RESEARCH -> ACHIEVEMENT,ALUMNI,RESEARCH |
| 12 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,RESEARCH -> ACHIEVEMENT,RESEARCH |
| 13 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | INTERNSHIP,ACHIEVEMENT,RESEARCH -> INTERNSHIP,ACHIEVEMENT,RESEARCH |
| 13 | B | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) | INTERNSHIP,ACHIEVEMENT,RESEARCH -> INTERNSHIP,ACHIEVEMENT,RESEARCH |
| 15 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,RESEARCH -> ACHIEVEMENT,RESEARCH |
| 17 | B | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) | INDUSTRY,RESEARCH -> INDUSTRY,RESEARCH |
| 17 | B | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) | INDUSTRY,RESEARCH -> INDUSTRY,RESEARCH |
| 18 | B | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) | INTERNSHIP,RESEARCH,INDUSTRY,CONFERENCE,WORKSHOP -> INTERNSHIP,RESEARCH,INDUSTRY,CONFERENCE,WORKSHOP |
| 18 | B | category | cat_over_tag:INTERNSHIP (low) | yes | category_gate flag fired (kept for review, not dropped) | INTERNSHIP,RESEARCH,INDUSTRY,CONFERENCE,WORKSHOP -> INTERNSHIP,RESEARCH,INDUSTRY,CONFERENCE,WORKSHOP |
| 25 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,RESEARCH -> ACHIEVEMENT,RESEARCH |
| 29 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |
| 31 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,ALUMNI,HACKATHON,RESEARCH -> ACHIEVEMENT,ALUMNI,HACKATHON,RESEARCH |
| 32 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | CAMPUS,INTERNSHIP,ACHIEVEMENT -> CAMPUS,INTERNSHIP,ACHIEVEMENT |
| 34 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | CULTURAL,ACHIEVEMENT -> CULTURAL,ACHIEVEMENT |
| 40 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | WEBINAR,CAMPUS,INTERNSHIP,RESEARCH -> WEBINAR,CAMPUS,INTERNSHIP,RESEARCH |
| 45 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | FDP,RESEARCH,ACHIEVEMENT,WORKSHOP -> FDP,RESEARCH,ACHIEVEMENT,WORKSHOP |
| 46 | B | category | cat_over_tag:INTERNSHIP (low) | yes | category_gate flag fired (kept for review, not dropped) | RESEARCH,CONFERENCE,INTERNSHIP -> RESEARCH,CONFERENCE,INTERNSHIP |
| 47 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | INDUSTRY,WORKSHOP,ACHIEVEMENT -> INDUSTRY,WORKSHOP,ACHIEVEMENT |
| 50 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | WORKSHOP,ACHIEVEMENT -> WORKSHOP,ACHIEVEMENT |
| 50 | B | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) | WORKSHOP,ACHIEVEMENT -> WORKSHOP,ACHIEVEMENT |
| 57 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | INTERNSHIP,CLUB,ACHIEVEMENT -> INTERNSHIP,CLUB,ACHIEVEMENT |
| 61 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ALUMNI,FDP,ACHIEVEMENT -> ALUMNI,FDP,ACHIEVEMENT |
| 61 | B | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) | ALUMNI,FDP,ACHIEVEMENT -> ALUMNI,FDP,ACHIEVEMENT |
| 69 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | SEMINAR,RESEARCH -> SEMINAR,RESEARCH |
| 73 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | INTERNSHIP,RESEARCH -> INTERNSHIP,RESEARCH |
| 75 | B | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,INDUSTRY,CLUB -> HACKATHON,INDUSTRY,CLUB |
| 89 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | GUEST_LECTURE,OUTREACH,CLUB,RESEARCH -> GUEST_LECTURE,OUTREACH,CLUB,RESEARCH |
| 90 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,SPORTS -> ACHIEVEMENT,SPORTS |
| 92 | B | category | cat_over_tag:RESEARCH (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT,SEMINAR,CAMPUS,RESEARCH -> ACHIEVEMENT,SEMINAR,CAMPUS,RESEARCH |
| 105 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | ACHIEVEMENT,HACKATHON -> ACHIEVEMENT,HACKATHON |
| 140 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ALUMNI,ORIENTATION,ACHIEVEMENT -> ALUMNI,ORIENTATION,ACHIEVEMENT |
| 140 | B | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) | ALUMNI,ORIENTATION,ACHIEVEMENT -> ALUMNI,ORIENTATION,ACHIEVEMENT |
| 149 | B | category | cat_over_tag:ALUMNI (low) | yes | category_gate flag fired (kept for review, not dropped) | ALUMNI,ORIENTATION,ACHIEVEMENT -> ALUMNI,ORIENTATION,ACHIEVEMENT |
| 164 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,ACHIEVEMENT -> HACKATHON,ACHIEVEMENT |
| 166 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | SYMPOSIUM,TECH_FEST,WORKSHOP,ACHIEVEMENT,CONFERENCE -> SYMPOSIUM,TECH_FEST,WORKSHOP,ACHIEVEMENT,CONFERENCE |
| 170 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |
| 171 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |
| 187 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,SYMPOSIUM,WORKSHOP,ACHIEVEMENT -> HACKATHON,SYMPOSIUM,WORKSHOP,ACHIEVEMENT |
| 242 | C | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) | HACKATHON,TECH_FEST -> HACKATHON,TECH_FEST |
| 253 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,SYMPOSIUM,CLUB,CONFERENCE,ACHIEVEMENT -> HACKATHON,SYMPOSIUM,CLUB,CONFERENCE,ACHIEVEMENT |
| 260 | B | category | multi_label_overlap (low) | yes | curated same-event pair collapsed | CONFERENCE,INTERNSHIP,WEBINAR -> CONFERENCE,INTERNSHIP |
| 261 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | ACHIEVEMENT,RESEARCH,ORIENTATION -> ACHIEVEMENT,RESEARCH,ORIENTATION |
| 298 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | SYMPOSIUM,TECH_FEST,WORKSHOP,ACHIEVEMENT -> SYMPOSIUM,WORKSHOP,ACHIEVEMENT |
| 298 | B | category | multi_label_overlap (low) | yes | curated same-event pair collapsed | SYMPOSIUM,TECH_FEST,WORKSHOP,ACHIEVEMENT -> SYMPOSIUM,WORKSHOP,ACHIEVEMENT |
| 394 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,INDUSTRY,ACHIEVEMENT -> HACKATHON,INDUSTRY,ACHIEVEMENT |
| 394 | B | category | cat_over_tag:INDUSTRY (low) | yes | category_gate flag fired (kept for review, not dropped) | HACKATHON,INDUSTRY,ACHIEVEMENT -> HACKATHON,INDUSTRY,ACHIEVEMENT |
| 400 | C | department | dept_generic_term (low) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 426 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | STTP,RESEARCH -> STTP,RESEARCH |
| 426 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | STTP,RESEARCH -> STTP,RESEARCH |
| 486 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 486 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 486 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 486 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 567 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 567 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 567 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 567 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 586 | B | department | dept_generic_term (low) | yes | explicitly named in post; kept per review guideline 'unless the post names this department' | RESEARCH,CONFERENCE,GUEST_LECTURE,INTERNSHIP -> RESEARCH,GUEST_LECTURE,INTERNSHIP |
| 586 | B | category | multi_label_overlap (low) | yes | curated same-event pair collapsed | RESEARCH,CONFERENCE,GUEST_LECTURE,INTERNSHIP -> RESEARCH,GUEST_LECTURE,INTERNSHIP |
| 601 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 601 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 601 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 601 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 660 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 660 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 660 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 660 | C | department | dept_generic_term (medium) | yes | department removed from display (General or explicit depts) | RESEARCH -> RESEARCH |
| 747 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |
| 1125 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |
| 1519 | B | category | cat_over_tag:ACHIEVEMENT (low) | yes | category_gate flag fired (kept for review, not dropped) | ACHIEVEMENT -> ACHIEVEMENT |

## D. Regression checks

### D.1 Status flips (activity <-> non-activity)

| Post | review group | old -> new | human_activity |
|---|---|---|---|

False communication suppressions (human said ACTIVITY, classifier flipped to NON_ACTIVITY): **0**

### D.2 Department -> General flips

| Post | review group | raw departments | display | review dept proposals |
|---|---|---|---|---|
| 13 | B | Applied Mathematics and Computational Science | General | cat_over_tag:RESEARCH,dept_generic_term |
| 17 | B | Electrical and Electronics Engineering | General | cat_over_tag:INDUSTRY,dept_generic_term |
| 50 | B | Chemistry | General | cat_over_tag:ACHIEVEMENT,dept_generic_term |
| 63 | E | T'SEDA (Architecture, Design, Planning) | General | comm_mention_context,comm_separation_confirmed |
| 87 | E | Chemistry | General | comm_mention_context,comm_separation_confirmed |
| 242 | C | T'SEDA (Architecture, Design, Planning) | General | dept_generic_term |
| 370 | G | Chemistry | General | - |
| 400 | C | Electrical and Electronics Engineering | General | dept_generic_term,pre_2024_keep |

Department -> General WITHOUT a review dept_generic proposal: **0** on activity rows (must be 0); **1** including group-G (unclear) rows, which are informational only because the review layer never proposes department corrections for REVIEW_REQUIRED rows.

### D.3 Category gate flags fired without a human over-tag proposal

Gates are flag-first (nothing dropped); these are watch items, not changes.

| Post | review group | category |
|---|---|---|

Count: **0**

### D.4 Multi-label changes

| Post | old multi | new multi | old cats -> new cats |
|---|---|---|---|

Unwanted multi-label changes (outside the 3 curated posts 260/298/586): **0**

### D.5 Invariant checks

- Stakeholder candidates changed on any of the 200: **0** (must be 0)
- Date status / academic_year changed on any of the 200: **0** (must be 0)

## E. Rollback recommendation

No rollback needed: every implemented rule is additive (flags / display-level values) and the 200 reviewed rows in the staging DB are byte-for-byte unchanged (baseline == stored = True). Before turning category/context suppression into automatic display or statistics, score the gates against the 200 human labels and re-run this validation.

## F. Full test-suite result

`python -m pytest tests -q` -> **315 passed** in 48.1s, all green (pre-existing suite + RULE-01..12 rule tests).
