# LinkedIn Candidate Manual Review Report (2026-09-23)

- Generated: 2026-09-23T16:57:03
- Sample: 200 posts, PENDING_REVIEW (staging/review layer only)
- Disclaimer: This is a review aid for a human evaluator. Proposed corrections and review decisions are recorded in the review layer only (linkedin_manual_review_proposals + this report); nothing is applied to linkedin_activity_candidates, the production database or merged-workbook.xlsx. Internal evidence spans are never public UI fields. No accuracy claim is made.

## 1. How to use this report

- Groups A-H are review-priority buckets; they are NOT the step-2 screening kinds A-J stored in linkedin_activity_candidates.kind.
- Every proposal is a PROPOSED correction/review decision recorded in the review layer only (linkedin_manual_review_proposals table + this report). Nothing is applied to linkedin_activity_candidates, the production database, or merged-workbook.xlsx.
- Evidence-first: confirm from the post text (and the URL when present) before accepting a proposal; reject any proposal the text does not support.
- Academic year uses EXPLICIT dates only, June 1 - May 31. Undated posts stay undated; ambiguous multi-year posts stay flagged; no date is invented from sheet names or surrounding posts.
- Department must come from explicit evidence in the post. Generic technical terminology is not department evidence; institution-wide activities should be marked General.
- Stakeholder is the intended audience/participants of the activity, not an isolated word inside an unrelated sentence or a profile/bio line.
- Multi-label categories are kept only when the post genuinely reports multiple distinct activity types; same-event synonyms should collapse to the dominant category.
- Communication separation: admission promos, job ads, greetings, congratulations, general announcements and thanks are NON_ACTIVITY; a genuine event embedded in such a post must be promoted (group F).
- Over-tag attention categories: ACHIEVEMENT, RESEARCH, ALUMNI, INTERNSHIP, PLACEMENT, INDUSTRY, CAMPUS - keyword mentions of these in promos/profiles do not make the post an instance of that activity.
- No accuracy claim is made; this report is a review aid for a human evaluator. The classifier must be scored against the human labels.

## 2. Summary counts

### 2.1 Review groups A-H (partition of the 200 sampled posts)

| Group | Label | Posts |
|---|---|---|
| A | Activity - likely correct | 61 |
| B | Activity - category correction proposed | 39 |
| C | Activity - department correction proposed | 9 |
| D | Activity - stakeholder correction proposed | 0 |
| E | Non-activity - likely correct | 27 |
| F | Non-activity - should be activity (embedded event) | 0 |
| G | Review / unclear | 57 |
| H | Activity - date / academic-year issue | 7 |

### 2.2 Proposed corrections by field

| Field | Corrections |
|---|---|
| category | 44 |
| department | 26 |

Total proposed corrections: 70 | review notes: 66 | proposals persisted: 136

### 2.3 Proposed corrections by rule

| Rule | Count |
|---|---|
| comm_separation_confirmed | 27 |
| dept_generic_term | 26 |
| cat_over_tag:ACHIEVEMENT | 21 |
| comm_mention_context | 20 |
| multi_year_keep | 15 |
| cat_over_tag:RESEARCH | 11 |
| cat_over_tag:INDUSTRY | 4 |
| pre_2024_keep | 4 |
| cat_over_tag:ALUMNI | 3 |
| multi_label_overlap | 3 |
| cat_over_tag:INTERNSHIP | 2 |

### 2.4 Over-tag attention (7 categories, group B subset)

| Category | Posts flagged |
|---|---|
| Achievement and Awards | 21 |
| Research and Consultancy | 11 |
| Alumni | 3 |
| Internship | 2 |
| Placement | 0 |
| Industry Collaboration | 4 |
| Campus | 0 |

### 2.5 Sample composition by candidate status

| Status | Posts |
|---|---|
| ACTIVITY_CANDIDATE | 116 |
| NON_ACTIVITY | 27 |
| REVIEW_REQUIRED | 57 |

## Group A - Activity - likely correct (61 posts)

> ACTIVITY_CANDIDATE with no field-level correction proposed. Confirm the activity type from the text and approve.

### Post #1

- Source: `June 2025-June 2026` row `1` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7470537980454109184
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 7 | multi_label: 0
- Proposals: none
- Text: 🌍📚 Research Beyond Borders! The latest issue of the Thiagarajar Journal of Engineering, Science, Design and Technology — *Vol. 2, No. 1 (May 2026)* has been successfully released, showcasing pioneering research on *Digital Transformation and Sustainable Innovation in Engineering and Science*. 📈 Growing Global Impact 👁️ 3.7K+ Website Views 👥 2.5K+ Active Users 🌐 Readers from across the world Top Co

### Post #3

- Source: `June 2025-June 2026` row `3` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7470462168434606081
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:FDP)
- Categories: FDP
- Departments: Electrical and Electronics Engineering
- Stakeholders: Faculty, Government and Agencies, Students
- Date: status `dated` | dates: 2026-05-18 | AY: `2025-26`
- Flags: - | evidence_score: 14 | multi_label: 0
- Proposals: none
- Text: 🎓✨ Thiagarajar College of Engineering, Madurai Successfully conducted the 5-Day AICTE Approved Faculty Development Programme on Universal Human Values – II on 18 May 2026. 👩‍🏫 Resource Person: Mrs. Nidhi Chirag Sachde, UHV Volunteer, Mumbai 👥 Participants: 75 Faculty Members Organized by the Departments of Mathematics and Electrical & Electronics Engineering under the Centre for Continuing Educati

### Post #6

- Source: `June 2025-June 2026` row `6` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7469957353912684545
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:CONFERENCE)
- Categories: CONFERENCE
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-08-28 | AY: `2026-27`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 🚀✨ Something extraordinary is coming to TCE! 🎤 **TEDx Thiagarajar College of Engineering** 🗓️ **August 28, 2026** 📍 Theme: **"We Are The System"** 🌟 Renowned Speakers 🌍 Diverse Domains 💡 Endless Inspiration Get ready to explore powerful ideas that educate, entertain, and empower! From Technology and Engineering to Leadership, Creativity, and Transformation—this is where ideas spark change. 🔥 🎯 Sta

### Post #8

- Source: `June 2025-June 2026` row `8` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468882973816414208
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Faculty, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 14 | multi_label: 0
- Proposals: none
- Text: 🎉 *NPTEL Achievements – EVEN Semester (AY 2025–26)* 🎉 We are delighted to celebrate the remarkable accomplishments of our faculty and students in the NPTEL certification examinations. 🏆 491 Total Certifications Earned 👨‍🎓 Students 🥇 Elite + Gold: 100 🥈 Elite + Silver: 129 ⭐ Elite: 115 ✅ Successfully Completed: 61 👩‍🏫 Faculty 🥇 Elite + Gold: 01 🥈 Elite + Silver: 32 ⭐ Elite: 38 ✅ Successfully Comple

### Post #9

- Source: `June 2025-June 2026` row `9` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468882865024311296
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Categories: ACHIEVEMENT
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Government and Agencies, Community and Society, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 0
- Proposals: none
- Text: 🎉 *Congratulations* to the M.Plan (Urban Planning) students of *T'SEDA (Thiagarajar School of Environmental Design and Architecture)* on their selection as *Project Associates* at the *All India Institute of Local Self-Government (AIILSG)*. 🌟 Mr. Aakash S 🌟 Mr. Subash K 🌟 Mr. Muthukumar K 📍 Tirupati | From June 2026 This achievement reflects their dedication and the industry-oriented learning expe

### Post #10

- Source: `June 2025-June 2026` row `10` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468551551423291392
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:CAMPUS)
- Categories: CAMPUS
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 8 | multi_label: 0
- Proposals: none
- Text: 🌍🌱 World Environment Day 2026 🌱🌍 TCE celebrates World Environment Day, reaffirming our commitment to SDG 7 – Affordable & Clean Energy and a sustainable future. ♻️ 2000+ Trees nurturing our Campus 🌿 3 Biogas Plants supporting hostel needs 💧 3.5 Lakh sq.ft Rainwater Harvesting coverage 🔄 167 kLD Sewage Treatment & Water Reuse capacity 🛣️ Pioneer in Plastic Tar Roads – Waste-to-Wealth Innovation 🚌⚡ 

### Post #16

- Source: `June 2025-June 2026` row `16` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468176999489060865
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WORKSHOP)
- Categories: WORKSHOP
- Departments: -
- Stakeholders: Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 🌟📚 Empowering Educators, Enriching Classrooms! 💡❤️ The Women Empowerment Cell (WEC), Thiagarajar College of Engineering, is organizing a *Two-Day Workshop on "Teaching with EQ & Building Emotionally Intelligent Classrooms" on *4th & 5th June 2026 at KK Auditorium, TCE, Madurai*. 🧠 Understand Emotions 🎯 Empower Learning 🤝 Build Stronger Connections 🌱 Create Classrooms with Empathy & Understanding T

### Post #23

- Source: `June 2025-June 2026` row `23` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7466283178341740544
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,ALUMNI)
- Categories: ACHIEVEMENT, ALUMNI
- Departments: Civil Engineering
- Stakeholders: Alumni, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 24 | multi_label: 1
- Proposals: none
- Text: 🌟 *#AlumniSpotlight* From TCE Civil Engineering to leading India’s landmark infrastructure projects! Congratulations to Mr. Arockia Heronimus Pandian S (B.E. Civil Engineering, 2001–2005) for his remarkable journey in Nuclear, Hydro & Infrastructure Project Planning and Management. 🏅 Anna University Gold Medalist & BOSE Awardee 🏗️ Expertise in Contract Administration & Claims Management 🌍 Worked o

### Post #28

- Source: `June 2025-June 2026` row `28` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7464262770788708352
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:GUEST_LECTURE)
- Categories: GUEST_LECTURE
- Departments: Electronics and Communication Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-05-27 | AY: `2025-26`
- Flags: - | evidence_score: 6 | multi_label: 0
- Proposals: none
- Text: 📡 Explore the future of RF-MEMS and next-generation communication technologies at the special lecture organized by the Department of Electronics and Communication Engineering, Thiagarajar College of Engineering in association with ISSS Madurai Chapter. 🎙️ Topic: Vertical Focus on RF-MEMS – From Technology Inception and Past-to-Present Market Analysis to Future Prospects for 6G and Future Networks 

### Post #38

- Source: `June 2025-June 2026` row `38` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7461457972540383232
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:FDP,SEMINAR)
- Categories: FDP, SEMINAR
- Departments: Electrical and Electronics Engineering
- Stakeholders: Faculty, Government and Agencies, Students
- Date: status `dated` | dates: 2026-05-18 | AY: `2025-26`
- Flags: - | evidence_score: 18 | multi_label: 1
- Proposals: none
- Text: Building better educators beyond classrooms! ✨ Thiagarajar College of Engineering inaugurates the AICTE Approved Five-Day Faculty Development Programme on Universal Human Values – II, a journey towards value-based education, self-exploration, and holistic growth. 📅 May 18, 2026 🕘 9:00 AM 📍 EEE Seminar Hall, TCE Madurai Join academicians, facilitators, and educators as they come together to explore

### Post #41

- Source: `June 2025-June 2026` row `41` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7461446278166654976
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:CAMPUS)
- Categories: CAMPUS
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: 🏁 Day 5 marked the grand finale of IDE Boot Camp 2026 at Thiagarajar College of Engineering! ✨ Participants showcased their innovative ideas through Panel Presentations, reflecting the creativity, collaboration, and entrepreneurial learning gained throughout the boot camp. 💡🚀 The 5-day journey concluded with a memorable Valedictory Ceremony, celebrating innovation, teamwork, and the spirit of futu

### Post #64

- Source: `June 2025-June 2026` row `64` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7458003462665158656
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:SEMINAR)
- Categories: SEMINAR
- Departments: Electrical and Electronics Engineering
- Stakeholders: Faculty, Students
- Date: status `dated` | dates: 2026-05-07 | AY: `2025-26`
- Flags: - | evidence_score: 7 | multi_label: 0
- Proposals: none
- Text: 🎓 Fifth TCE Faculty Conclave 2026 at Thiagarajar College of Engineering Organized by the Office of Academic Process, this conclave brings together TCE faculty members to share innovative teaching ideas and best practices for the evolving Gen Z learning environment. 📌 Theme: Beyond Chalk and Talk: Redefining Education for the Gen Z World 📅 May 7, 2026 | 09.30 AM - 01.00 PM 📍 EEE Seminar Hall 🏆 ₹200

### Post #70

- Source: `June 2025-June 2026` row `70` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7456639910603714560
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:FDP)
- Categories: FDP
- Departments: Electrical and Electronics Engineering
- Stakeholders: Faculty, Government and Agencies, Students
- Date: status `dated` | dates: 2026-05-05 | AY: `2025-26`
- Flags: - | evidence_score: 19 | multi_label: 0
- Proposals: none
- Text: 📢 Five-Day Faculty Development Programme (FDP) Universal Human Values – II (UHV-II) 🗓️ May 18–22, 2026 📍 Face-to-Face | No Registration Fee Organized by the Departments of Mathematics & Electrical and Electronics Engineering. ✨ This FDP focuses on self-exploration, inner harmony, professional ethics, and value-based education, helping educators nurture responsible and compassionate learners. 👩‍🏫 R

### Post #81

- Source: `June 2025-June 2026` row `81` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7454828095263535104
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,CLUB,SEMINAR)
- Categories: ACHIEVEMENT, CLUB, SEMINAR, CAMPUS
- Departments: Computer Science and Engineering
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 21 | multi_label: 1
- Proposals: none
- Text: 🎓 Valedictory Ceremony 2025–26 Department of Computer Science & Engineering, Thiagarajar College of Engineering Join us as we celebrate the successful completion of CSEA & Professional Societies (IEEE, IE, CSI) activities. 👤 Chief Guest: Mr. Ks. Karthikeswaran, Director R&D, Aptean, Madurai 📅 April 30 | ⏰ 3:00 PM 📍 CSE Seminar Hall Let’s honor achievements, memories, and milestones together! #TCE 

### Post #82

- Source: `June 2025-June 2026` row `82` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7454827287671361536
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:SPORTS)
- Categories: SPORTS
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-05-03 | AY: `2025-26`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: ♟️ 9th Radha Thiagarajan Memorial State Level Open & Children Chess Tournament – 2026 Thiagarajar College of Engineering | FIT INDIA Cordially invites you to participate in a prestigious state-level chess event 🏆 📅 Sunday, 03 May 2026 ⏰ 9:00 AM onwards 📍 TCE Open Auditorium, Madurai ♟️ Organized by: Department of Physical Education & Darshini Chess Academy (Affiliated to Madurai District Chess Ass

### Post #91

- Source: `June 2025-June 2026` row `91` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452376028582273025
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WEBINAR)
- Categories: WEBINAR
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Students, Community and Society
- Date: status `dated` | dates: 2026-04-22 | AY: `2025-26`
- Flags: - | evidence_score: 7 | multi_label: 0
- Proposals: none
- Text: 🏗️ Sustainable Building Design Strategies 🌱 Thiagarajar School of Environmental Design and Architecture (T’SEDA), TCE, invites you to an insightful online session on sustainable architecture. 👤 Speaker: Ar. Caleb G. Rohan 📅 Date: April 22, 2026 ⏰ Time: 11:00 AM – 12:30 PM 💻 Mode: Online 🎯 For: III & IV Year B.Arch Students 🔗 Join via Google Meet: https://lnkd.in/gME89HJV #SustainableDesign #GreenA

### Post #93

- Source: `June 2025-June 2026` row `93` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452369199332597760
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH,SEMINAR)
- Categories: RESEARCH, SEMINAR
- Departments: -
- Stakeholders: Students, Faculty
- Date: status `dated` | dates: 2026-04-22 | AY: `2025-26`
- Flags: - | evidence_score: 14 | multi_label: 1
- Proposals: none
- Text: 🎓 TCE Research Seminar Series #32 Organized by the Research & Development Cell, TCE Join us for an insightful session by Dr. S. Padmavathi, Professor, IT Department. 📌 Topic: The Engine of Generative AI: Understanding Transformer Dynamics 📅 Date: 22 April 2026 🕒 Time: 3:30 PM – 4:30 PM 📍 Venue: IT Seminar Hall All faculty, research scholars, and UG/PG students are cordially invited. #TCE #Research

### Post #94

- Source: `June 2025-June 2026` row `94` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452311403291398144
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CLUB,SEMINAR,WORKSHOP)
- Categories: CLUB, SEMINAR, WORKSHOP
- Departments: Civil Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-22 | AY: `2025-26`
- Flags: - | evidence_score: 14 | multi_label: 1
- Proposals: none
- Text: 🚀 Business Model Canvas Workshop @ TCE The Institute Innovation Council of Thiagarajar College of Engineering invites you to an insightful session on building impactful business models. 🗓 April 22, 2026 ⏰ 3:00 PM – 5:00 PM 📍 Civil Seminar Hall 🎤 Speaker: Mr. Vinoth Rajendran, CEO, TCE TBI Explore how to turn ideas into structured, scalable ventures using the Business Model Canvas framework. #TCE #

### Post #97

- Source: `June 2025-June 2026` row `97` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452223921317384192
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:SPORTS)
- Categories: SPORTS
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-05-17 | AY: `2025-26`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 🏸 3rd Thiru Karumuttu T. Kannan Memorial Open State-Level Badminton Tournament 2026 Organized by the Department of Physical Education, Thiagarajar College of Engineering, Madurai, this tournament invites passionate shuttlers to compete in a professionally organized state-level event. 📅 Date: May 17, 2026 (Sunday) ⏰ Reporting Time: 9:00 AM 📍 Venue: TCE Indoor Stadium (4 Wooden Courts) 🎯 Categories:

### Post #99

- Source: `June 2025-June 2026` row `99` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452149844116410368
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:OUTREACH,NSS)
- Categories: OUTREACH, NSS
- Departments: -
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-04-17 | AY: `2025-26`
- Flags: - | evidence_score: 15 | multi_label: 1
- Proposals: none
- Text: 📘 TCE NSS Newsletter – Volume 1 (2026) Released! We are delighted to announce the official release of the TCE NSS Newsletter – Volume 1 (2026) on April 17, 2026. This edition captures the spirit of service, dedication, and impactful initiatives carried out by the NSS volunteers of Thiagarajar College of Engineering. From community outreach to social awareness campaigns, the newsletter showcases th

### Post #100

- Source: `June 2025-June 2026` row `100` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7451877211525279744
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:CULTURAL)
- Categories: CULTURAL
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 📜 கவியரங்கம் – அழைப்பு தியாகராசர் பொறியியற் கல்லூரி, மதுரை சிருட்டிக்கலைக்குழுமம் & தமிழ் மன்றம் வழங்கும் 🎙️ கவியரங்கம் 👩‍🏫 சிறப்பு விருந்தினர்: முனைவர் லெ. அலமேலு 📅 சித்திரை 7 | ஏப்ரல் 20, 2026 🕜 நேரம்: பிற்பகல் 1.30 – 3.00 மணி 📍 இடம்: KS அரங்கம் ✨ தமிழ்த்தாய் வாழ்த்து முதல் நாட்டுப்பண் வரை – உரை, கவிதை, நாடகம், நடனம் மற்றும் பரிசளிப்பு விழா இணைந்த இலக்கிய நிகழ்வு! #TCE #TamilMandram #Kaviyaranga

### Post #104

- Source: `June 2025-June 2026` row `104` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7451459155032244224
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:GUEST_LECTURE)
- Categories: GUEST_LECTURE
- Departments: -
- Stakeholders: Faculty, Students
- Date: status `dated` | dates: 2026-04-20 | AY: `2025-26`
- Flags: - | evidence_score: 6 | multi_label: 0
- Proposals: none
- Text: Thiagarajar College of Engineering, Madurai, cordially invites you to the Inaugural Ceremony of *UMAY Assistive Technology Studio* — a step towards empowering children through technology-driven therapy solutions that enhance focus, coordination, and independence. 🎓 Founder: Dr. Uma Kannan 🎖 Chief Guest: Mr. S. Govindaraj 🎤 Keynote Speaker: Prof. Dr. Sunil K Narayan Date: April 20, 2026 🕙 Time: 10:

### Post #113

- Source: `June 2025-June 2026` row `113` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450416825508474880
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:OUTREACH)
- Categories: OUTREACH
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 📢 Election Awareness Camp – Selfie Point 🗳️ To create awareness among students, step in, snap a selfie, and show your commitment to democracy! 📍 Venue: Open Air Auditorium 👥 Organized by YRC Let your voice be heard—Vote for a better tomorrow! #ElectionAwareness #StudentAwareness #VoteResponsibly #YouthForDemocracy #YRC #CampusInitiative

### Post #114

- Source: `June 2025-June 2026` row `114` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450132376468238336
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:OUTREACH,NSS)
- Categories: OUTREACH, NSS
- Departments: -
- Stakeholders: Community and Society
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 17 | multi_label: 1
- Proposals: none
- Text: 🌿 Thiagarajar College of Engineering NSS – Adopted Villages Initiative From Vilachery, Thanakkankulam, Sambakulam, Surakulam to Thangalacheri, TCE NSS continues to create impact through meaningful rural engagement. ✨ Key Activities: Plantation drives • Medical camps • BLS training • Plastic awareness rallies • Village cleaning • Election awareness • Surveys & field visits • Health & education sess

### Post #115

- Source: `June 2025-June 2026` row `115` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450131257080070144
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:ALUMNI,CULTURAL)
- Categories: ALUMNI, CULTURAL
- Departments: -
- Stakeholders: Alumni
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 15 | multi_label: 1
- Proposals: none
- Text: ✨ TCE USA Alumni Meet 2026 🇺🇸 Reconnect, reminisce, and rejoice with your TCE family at the Atlanta & Michigan Chapters Meet! We are honored to have Mr. K. Hari Thiagarajan, Chairman & Correspondent, TCE, grace the occasion. 📅 June 27 & 28, 2026 🤝 Networking | 🎤 Interactive Sessions | 🎉 Cultural Activities Join us for a memorable gathering filled with warmth and lasting connections! 🔗 Register: ht

### Post #118

- Source: `June 2025-June 2026` row `118` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450069588500996096
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ALUMNI,ACHIEVEMENT)
- Communication type: `greeting`
- Categories: ALUMNI, ACHIEVEMENT
- Departments: Electronics and Communication Engineering
- Stakeholders: Alumni, Community and Society
- Date: status `dated` | dates: 2026-04-01 | AY: `2025-26`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals: none
- Text: 🎉 Hearty Congratulations! 🎉 Thiagarajar College of Engineering proudly congratulates Mr. V. Prasanna (ECE – 2003 Batch) on assuming charge as Additional Divisional Railway Manager (ADRM) of the Madurai Division on 01 April 2026 🚆 Your remarkable achievement is a testament to your dedication, leadership, and commitment to excellence. You continue to inspire the TCE community with your success and s

### Post #123

- Source: `June 2025-June 2026` row `123` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7449641086987280384
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,SPORTS)
- Categories: ACHIEVEMENT, SPORTS
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-17 | AY: `2025-26`
- Flags: - | evidence_score: 9 | multi_label: 1
- Proposals: none
- Text: 🏆 THIDALSAM 2026 – State Level Kho-Kho Tournament 🏃‍♂️ proudly presents Thiru Karumuttu Thiagarajar Chettiar 12th Memorial State Level Inter-Engineering Men’s Kho-Kho Tournament 2026 📅 April 18 & 19, 2026 📍 TCE Campus 🔥 Open to all regular B.E./B.Tech/B.Arch students 👥 Team Size: 15 Players 🏆 Prizes: 🥇 ₹6000 + Rolling Trophy 🥈 ₹4000 + Trophy 🥉 ₹3000 | 🏅 ₹2000 📌 No Entry Fee | Accommodation Provide

### Post #124

- Source: `June 2025-June 2026` row `124` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7449640591933726720
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:GUEST_LECTURE,ACHIEVEMENT,SEMINAR)
- Categories: GUEST_LECTURE, ACHIEVEMENT, SEMINAR, CAMPUS, CLUB
- Departments: -
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-04-15 | AY: `2025-26`
- Flags: - | evidence_score: 21 | multi_label: 1
- Proposals: none
- Text: 🚀 *TCE Coders Club – Valedictory ’26* Join us as we celebrate innovation, achievements, and the spirit of coding at Thiagarajar College of Engineering ✨ 📅 April 15, 2026 (Wednesday) ⏰ 4:15 PM 📍 Seminar Hall, Dept. of IT 🎙 Chief Guest: Celsia, Hardware Engineer, Savemom Pvt. Ltd., Madurai 🎉 Highlights: • Annual Report • Principal’s Address • Chief Guest Talk • Prize Distribution Let’s wrap up the y

### Post #128

- Source: `June 2025-June 2026` row `128` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7448957327631646720
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:CAMPUS,CULTURAL)
- Categories: CAMPUS, CULTURAL
- Departments: -
- Stakeholders: Students, Community and Society, Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 12 | multi_label: 1
- Proposals: none
- Text: 🎨 Gangs of Kodambakkam – Second Edition Presented by Shrishti Cultural Association – Visual Arts, Thiagarajar College of Engineering (Since 1957) 📅 April 15 & 16 🕞 3:30 PM – 5:00 PM | BHalls 🎉 Valedictory: April 17 🕞 3:30 PM – 5:00 PM ✨ A vibrant celebration of creativity, expression, and visual storytelling awaits! 👨‍🎓 Student Coordinators: Vishnu Varthan BK, Shreeharan MS 👩‍🏫 Faculty Coordinator

### Post #131

- Source: `June 2025-June 2026` row `131` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7447562625313374208
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:CULTURAL,RESEARCH,SEMINAR)
- Categories: CULTURAL, RESEARCH, SEMINAR
- Departments: Mechanical Engineering
- Stakeholders: Faculty, Non-Teaching Staff, Community and Society, Students
- Date: status `dated` | dates: 2026-04-08 | AY: `2025-26`
- Flags: - | evidence_score: 26 | multi_label: 1
- Proposals: none
- Text: 🎉 CULTURA NOVA ’26 – Connections Organised by TCE–Shrishti Cultural Association Inviting Faculty, Non-Teaching Staff & Research Scholars to join an engaging session of connection and culture! 📅 08 April 2026 📍 Mechanical Seminar Hall, TCE 🕒 3:30 PM onwards 🎟️ Register & be part of the experience! #CulturaNova26 #TCE #Shrishti #CampusLife #FacultyEngagement #ResearchScholars #TCEEvents #CulturalCon

### Post #133

- Source: `June 2025-June 2026` row `133` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7447183410885910528
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NSS,OUTREACH)
- Categories: NSS, OUTREACH
- Departments: -
- Stakeholders: Students, Government and Agencies
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 12 | multi_label: 1
- Proposals: none
- Text: 🩸 *BLOOD DONATION CAMP - 26* 🩸 🏥 *Organized by*: NSS & YRC 🤝 *In association with*: Govt. Rajaji Hospital - Madurai 📍 *Venue*: Open Auditorium 🕘 *Time*: 9:00 AM - 4:00 PM 📅 *Date*: 8th April 2026 - Wednesday ✨ *A small act, a big impact!!* ✨ 🩸 *GIVE BLOOD, GIVE HOPE* Every drop of blood you donate carries life and hope to someone in need.Step forward and make a difference. 🍀Every heartbeat saved i

### Post #136

- Source: `June 2025-June 2026` row `136` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7446936304405131265
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WORKSHOP,CULTURAL)
- Categories: WORKSHOP, CULTURAL
- Departments: -
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-05-15 | AY: `2025-26`
- Flags: - | evidence_score: 9 | multi_label: 1
- Proposals: none
- Text: 🎓 DECODE IT – 2026 Engineering Exploration Week for School Students 📍 Thiagarajar College of Engineering, Madurai 📅 May 18–22, 2026 | ⏰ 10:00 AM – 4:00 PM 💡 Explore the world of IT through: * Coding (Scratch) * Website Creation * Mobile App Development * AI Basics & Cyber Safety * Mini Project & Quiz 🚀 Learn by doing, build real projects & boost future-ready skills 💰 Registration Fee: ₹826 (incl. 

### Post #142

- Source: `June 2025-June 2026` row `142` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7446008752555847680
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,RESEARCH)
- Communication type: `greeting`
- Categories: ACHIEVEMENT, RESEARCH
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 18 | multi_label: 1
- Proposals: none
- Text: 🎉 Congratulations! 🎉 Thiagarajar College of Engineering proudly celebrates our six Ph.D. Scholars for being awarded the prestigious IndiaAI Fellowship (2025–26) 👏 This remarkable achievement reflects their dedication to research, innovation, and excellence in AI and emerging technologies 🚀 💡 Fellowship Highlights: * ₹70,000/month (1st & 2nd year) * ₹75,000/month (3rd year) * ₹80,000/month (4th & 5

### Post #153

- Source: `June 2025-June 2026` row `153` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7443142184616312833
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:ORIENTATION)
- Categories: ORIENTATION
- Departments: Applied Mathematics and Computational Science, Computer Science and Engineering, Civil Engineering, Computer Applications, Computer Science and Business Systems, Electronics and Communication Engineering, Information Technology, Mechanical Engineering, Mechatronics, T'SEDA (Architecture, Design, Planning)
- Stakeholders: Faculty, Students
- Date: status `dated` | dates: 2026-03-27, 2026-03-30, 2026-04-02, 2026-04-10 | AY: `2025-26`
- Flags: - | evidence_score: 16 | multi_label: 0
- Proposals: none
- Text: 🎓 FAREWELL 2026 Department-Wise Send-Off 💙 📅 Farewell Schedule 🗓️ March 27, 2026 Applied Mathematics And Computational Science | Computer Science And Engineering | Computer Science And Business Systems | Mechatronics 🗓️ March 30, 2026 Computer Applications | Civil Engineering | Electronics and Communication Engineering | Mechanical Engineering 🗓️ April 02, 2026 Information Technology 🗓️ April 10, 

### Post #156

- Source: `June 2025-June 2026` row `156` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7443140611429261312
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:OUTREACH)
- Categories: OUTREACH
- Departments: Electronics and Communication Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-03-29 | AY: `2025-26`
- Flags: - | evidence_score: 10 | multi_label: 0
- Proposals: none
- Text: 🎓 Thiagarajar College of Engineering, Madurai 📡 Department of Electronics & Communication Engineering 🛡️ Cyber Security Awareness Programme 📢 Outreach under Sanchar Mitra Scheme by DoT in association with TRAI 🗓️ March 29, 2026 ⏰ 9:00 AM 📍 Thiagarajar College, Teppakulam, Madurai 💡 Learn about digital safety, cyber threats & secure communication practices! #TCE #ThiagarajarCollege #CyberSecurityAw

### Post #157

- Source: `June 2025-June 2026` row `157` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7442818716590907392
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:GUEST_LECTURE)
- Categories: GUEST_LECTURE
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Faculty, Community and Society, Students
- Date: status `dated` | dates: 2026-03-26 | AY: `2025-26`
- Flags: - | evidence_score: 10 | multi_label: 0
- Proposals: none
- Text: 📢 Technical Talk on Urban Planning The Faculty of Planning, T’SEDA, Thiagarajar College of Engineering, is organizing a Technical Talk on Urban Planning on March 26, 2026 | 10:30 AM to 02:00 PM 🎙️ Dr. Abdul Razak Mohamed, Retired Professor, Department of Planning, School of Planning and Architecture, Vijayawada, will deliver the session. This session offers valuable insights and expert perspective

### Post #161

- Source: `June 2025-June 2026` row `161` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7441099984789209088
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CLUB,CONFERENCE)
- Categories: CLUB, CONFERENCE
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-07 | AY: `2025-26`
- Flags: - | evidence_score: 7 | multi_label: 1
- Proposals: none
- Text: 📄 *Paper Presentation – Math Club Activity* The Math Club, Department of Mathematics, invites students to participate in a Paper Presentation on the theme “Mathematics and Its Applications.” Showcase your ideas and explore how mathematics connects with real-world applications. April 7, 2026 ⏰ Time: 3:20 PM 👨‍🏫 Coordinator: Dr. L. Muthusubramanian 📌 Guidelines * Individual participation * Presentat

### Post #162

- Source: `June 2025-June 2026` row `162` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7441099339235680256
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CONFERENCE,CLUB)
- Categories: CONFERENCE, CLUB
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-08 | AY: `2025-26`
- Flags: - | evidence_score: 8 | multi_label: 1
- Proposals: none
- Text: 🎯 *Think²–Create | Math Club Activity* Unleash your creativity and connect mathematics with real-world ideas through Think²–Create, organized by the Math Club, Department of Mathematics. Date: April 8, 2026 👥 Team: Individual or 2 Students per team 🔗 Register: https://lnkd.in/gtBEtuDy 🌐 Themes: * Mathematics in My Domain * Mathematics in AI * Mathematics in Nature 🎨 Event Categories (Choose any on

### Post #176

- Source: `June 2025-June 2026` row `176` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7439134424920850432
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-03-24 | AY: `2025-26`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: ✨ The Management, Principal, Staff and Students cordially invite your esteemed presence 🎓 68th College Day Function Thiagarajar College of Engineering, Madurai 📅 Tuesday, 24 March 2026 | 04:35 PM 📍 Karumuttu Kannan Auditorium, TCE Chief Guest Mr. Rajesh Mittal President & Managing Director, Isuzu Motors India Pvt. Ltd. President, Isuzu Engineering Business Centre India Presided by Mr. K. Hari Thia

### Post #178

- Source: `June 2025-June 2026` row `178` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7439133379062607872
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:STTP,CLUB)
- Categories: STTP, CLUB
- Departments: Information Technology
- Stakeholders: Students, Community and Society
- Date: status `dated` | dates: 2026-04-03, 2026-04-04 | AY: `2025-26`
- Flags: - | evidence_score: 17 | multi_label: 1
- Proposals: none
- Text: 🚀 One Week Online STTP on “Art of Coding Using AI Tools” (Inclusive of 3 hours contests ) The Department of Information Technology, Thiagarajar College of Engineering, in association with IEEE Computational Intelligence Society & ACM, organizes a One Week Online Short Term Training Program. 📅 30 Mar – 03 Apr 2026 ⏰ 6:30 PM – 8:00 PM (Online) 💡 Topics Covered Git & GitHub • Firebase • LLM APIs • Hu

### Post #183

- Source: `June 2025-June 2026` row `183` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7438418942496468992
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-03-24 | AY: `2025-26`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: ✨ The Management, Principal, Staff and Students cordially invite your esteemed presence 🎓 68th College Day Function Thiagarajar College of Engineering, Madurai 📅 Tuesday, 24 March 2026 | 04:35 PM 📍 Karumuttu Kannan Auditorium, TCE Chief Guest Mr. Rajesh Mittal President & Managing Director, Isuzu Motors India Pvt. Ltd. President, Isuzu Engineering Business Centre India Presided by Mr. K. Hari Thia

### Post #185

- Source: `June 2025-June 2026` row `185` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7437867633514987521
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:HACKATHON)
- Categories: HACKATHON
- Departments: Computer Science and Engineering
- Stakeholders: Industry, Students
- Date: status `dated` | dates: 2026-03-17, 2026-03-27 | AY: `2025-26`
- Flags: - | evidence_score: 8 | multi_label: 0
- Proposals: none
- Text: 🚀 *HACKRAX’26 – Industry Innovation Challenge* The Department of Computer Science and Engineering, Thiagarajar College of Engineering, Madurai, presents HACKRAX '26 – a platform to transform innovative ideas into real-world solutions. 💡 From Vision to Reality Submit your Ideation PPT by March 17, 2026, and compete in an intense 8-hour offline prototyping challenge. 🏆 Prize Pool: ₹10,000 📅 Event Da

### Post #206

- Source: `June 2025-June 2026` row `206` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7434820924614504448
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WEBINAR)
- Categories: WEBINAR
- Departments: Applied Mathematics and Computational Science
- Stakeholders: Students
- Date: status `dated` | dates: 2026-03-04 | AY: `2025-26`
- Flags: - | evidence_score: 7 | multi_label: 0
- Proposals: none
- Text: 📢 Webinar on Design Thinking for AI & Data Innovation The Department of Applied Mathematics & Computational Science, jointly with E-Cell, is organizing an insightful webinar for M.Sc. Data Science students. 🗓 Date: 04 March 2026 ⏰ Time: 11.00 AM 💻 Mode: Online 🎙 Guest Speaker: Mr. V. Sreevatsan CEO & Co-Founder, Guest Guru, Trichy An engaging session exploring innovation-driven thinking in AI and 

### Post #226

- Source: `June 2025-June 2026` row `226` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7431549960011251714
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CONFERENCE,GUEST_LECTURE,INTERNSHIP)
- Communication type: `thanks`
- Categories: CONFERENCE, GUEST_LECTURE, INTERNSHIP
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-02-23 | AY: `2025-26`
- Flags: - | evidence_score: 13 | multi_label: 1
- Proposals: none
- Text: 🌍 Centre for International Affairs – International Conference Talk Series (Online) 🎓 Inauguration Ceremony Chief Guest & Keynote Speaker: Dr. Pao-Ann Hsuing Dean, College of Engineering National Chung Cheng University, Taiwan 🗓 February 23, 2026 (Monday) ⏰ 10:00 AM Agenda Highlights: 🔹 Welcome Address – Dr. S. Karthikeyan 🔹 Presidential Address – Dr. L. Ashok Kumar, Principal 🔹 Keynote Address – D

### Post #232

- Source: `June 2025-June 2026` row `232` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7430470962602749952
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:GUEST_LECTURE,WEBINAR)
- Categories: GUEST_LECTURE, WEBINAR
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 12 | multi_label: 1
- Proposals: none
- Text: 🎓 Guest Lecture on Campus Planning in Indian Context Thiagarajar School of Environmental Design and Architecture (T’SEDA) 🗓 February 23 ⏰ 2:15 – 4:15 PM 📍 Online Session 🎙 Guest Speaker: Ar. Sanjay Mohe Principal Architect – Mindspace Architects An insightful session exploring campus planning strategies within the Indian context. #TCE #TSEDA #GuestLecture #CampusPlanning #ArchitectureEducation #In

### Post #275

- Source: `June 2025-June 2026` row `275` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7422560779750625280
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NCC,NSS)
- Communication type: `thanks`
- Categories: NCC, NSS
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals: none
- Text: 🇮🇳 77th Republic Day Celebrations | TCE 📍 Main Ground | 🗓️ 26.01.2026 | ⏰ Morning A proud morning of patriotism and discipline 🇮🇳 ✨ Chief Guest arrival & warm welcome 🚩 Flag Hoisting & Balloon Release 🤝 National Pledge 💃 Graceful Bharatanatyam by NCC Cadets 🎖️ Power-packed Special NCC Drill 📝 Thought-provoking Tamil Kavithai by NSS 🎤 Inspiring Republic Day Address 🙏 Vote of Thanks 🇮🇳 Saluting the 

### Post #278

- Source: `June 2025-June 2026` row `278` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7421212560802209792
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NCC)
- Categories: NCC
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-01-26 | AY: `2025-26`
- Flags: - | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: 4 (TN) ENGR COY NCC Thiagarajar College of Engineering Cordially invites you to celebrate The 77ᵗʰ Republic Day of India 🇮🇳 Dr. L. Ashok Kumar Principal, TCE will graciously preside over the function 📅 26 January 2026 ⏰ 7.45 AM 📍 Main Ground, TCE Join us as we honor the spirit of the Republic. #77thRepublicDay #RepublicDay2026 #JanaGanaMana #ProudToBeIndian #NationFirst #UnityInDiversity #IndianRe

### Post #288

- Source: `June 2025-June 2026` row `288` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7419601456556716032
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WEBINAR,CLUB,SEMINAR)
- Categories: WEBINAR, CLUB, SEMINAR
- Departments: Electronics and Communication Engineering
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-01-22 | AY: `2025-26`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals: none
- Text: 📡 Inauguration Ceremony & Webinar on 5G Mobile Communications IEEE Broadcast Technology Society (BTS) in collaboration with TCE IEEE Student Branch & Dept. of ECE 🎙 Chief Guest & Speaker Shri S. Sudhakar, ITS Additional Director General (Telecom) – TN & Puducherry Department of Telecommunications 📅 22 January 2026 ⏰ 3:30 PM – 5:00 PM 📍 ECE Seminar Hall #IEEEBTS #IEEEBroadcastTechnologySociety #IEE

### Post #425

- Source: `June 2025-June 2026` row `425` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394584633985785856
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NSS)
- Categories: NSS
- Departments: -
- Stakeholders: Government and Agencies, Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 8 | multi_label: 0
- Proposals: none
- Text: A Two-Day 🎓 Career Guidance Exposure Visit 2025 Inspiring Young Minds Towards Higher Education Thiagarajar College of Engineering, Madurai, warmly welcomes Class 12 students from Government Schools for the Career Guidance Exposure Visit, a Government initiative aimed at enhancing the Gross Enrollment Ratio (GER) in higher education. 📅 Date: November 12 & 13, 2025 📍 Venue: Thiagarajar College of En

### Post #434

- Source: `June 2025-June 2026` row `434` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394233289097719808
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NSS)
- Categories: NSS
- Departments: -
- Stakeholders: Government and Agencies, Community and Society, Students
- Date: status `dated` | dates: 2025-11-12 | AY: `2025-26`
- Flags: - | evidence_score: 8 | multi_label: 0
- Proposals: none
- Text: 🎓 Career Guidance Exposure Visit 2025 Inspiring Young Minds Towards Higher Education Thiagarajar College of Engineering, Madurai, warmly welcomes Class 12 students from Government Schools for the Career Guidance Exposure Visit, a Government initiative aimed at enhancing the Gross Enrollment Ratio (GER) in higher education. 📅 Date: November 12, 2025 📍 Venue: Thiagarajar College of Engineering, Madu

### Post #451

- Source: `June 2025-June 2026` row `451` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7389951409409949696
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,NCC,CULTURAL)
- Categories: ACHIEVEMENT, NCC, CULTURAL
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2025-10-01 | AY: `2025-26`
- Flags: - | evidence_score: 18 | multi_label: 1
- Proposals: none
- Text: 🎯 TCE at AP Trekking Camp II – Araku Valley, Andhra Pradesh 🏞️ Sep 24 – Oct 1, 2025 Proud moment for our NCC Cadets! 💪 🥇 CSM Sangamesh S (III Yr) – Culturals Winner 🥈 LCPL Sudhakar S (IV Yr) – Culturals Winner & Debate Runner-up #TCE #ThiagarajarCollegeOfEngineering #TCEMadurai #NCC #APTrekkingCamp #ArakuValley #StudentAchievement #ProudMoment #NCCIndia #YouthEmpowerment #TCEPride #QualityAndEthic

### Post #509

- Source: `June 2025-June 2026` row `509` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7377148723254104064
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NCC,SEMINAR)
- Categories: NCC, SEMINAR
- Departments: Computer Science and Engineering
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals: none
- Text: 🎖️ Special Invited Lecture 🎖️ Career in the Indian Armed Forces 📅 Date: 26th Sept 2025 ⏰ Time: 3:15 PM - 04.15 PM 📍 Venue: CSE Seminar Hall, TCE 👨‍✈️ Resource Person Capt. Venkatesh Kumar S (CSE - 2005) Commanding Officer, Indian Naval Air Squadron, Goa Organized by TCE NCC Coordinators: Lieut. Dr. S. Saravanakumar & Capt. Dr. T. Chandrakumar #TCE #NCC #IndianArmedForces #CareerInForces #TCEMadura

### Post #511

- Source: `June 2025-June 2026` row `511` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7377147846225031169
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:ORIENTATION,OUTREACH)
- Categories: ORIENTATION, OUTREACH
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Students, Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals: none
- Text: 🌟 COA & MSME Sponsored Programme @ TCE 🌟 🎓 Entrepreneur Awareness Programme (EAP) Exploring Horizons: Avenues After Graduation in Architecture 📅 8th October 2025 🕘 9:30 AM – 5:00 PM 📍 KS Auditorium, TCE 👩‍🎓 For: Architecture Students & Young Professionals 🎙️ Sessions by Experts: Ar. Sridhar Kandal – Principal Architect, Abstract Reality Pvt. Ltd., Bangalore Ar. Kavitha Mohan – Founder & Creative H

### Post #548

- Source: `June 2025-June 2026` row `548` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7371550788055269376
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CULTURAL,ORIENTATION)
- Categories: CULTURAL, ORIENTATION
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 9 | multi_label: 1
- Proposals: none
- Text: 🎉 Fresher’s Fest 2025-26 🎉 Organized by Shrishti Cultural Association Thiagarajar College of Engineering 📅 11.09.2025 (Thursday) 🕑 2:00 PM – 5:00 PM 📍 Open Auditorium ✨ An evening of Dance | Drama | Music | DJ Showcasing the vibrant talents of our first-year students along with special performances by Nadanalaya, Andhadhi & AFD. Join us to celebrate creativity, energy, and passion! 💃🎶🎭 #TCE #Fresh

### Post #592

- Source: `June 2025-June 2026` row `592` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7363970859784355840
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:SYMPOSIUM,CLUB,GUEST_LECTURE)
- Categories: SYMPOSIUM, CLUB, GUEST_LECTURE
- Departments: Computer Science and Business Systems
- Stakeholders: Students, Community and Society
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals: none
- Text: 🌟 One-Day Non-Technical Symposium – RE-INVENT 🌟 “Igniting Innovation & Impact in the Age of Ideas” 📅 12.09.2025 (Friday) 🏛️ Organized by IEEE CIS TCE Student Chapter & Dept. of CSBS, TCE 🤝 Sponsored by IEEE SPAx ✨ Highlights: 🔹 Keynote: Innovation as the New Intelligence 🔹 Session: Rebranding You – Campus to Global 🔹 Competitions: Pitcher Perfect, Leader’s Maze 🎯 Eligibility: UG/PG students (Engin

### Post #606

- Source: `June 2025-June 2026` row `606` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7361639604149522433
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NCC)
- Categories: NCC
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2025-08-15 | AY: `2025-26`
- Flags: - | evidence_score: 6 | multi_label: 0
- Proposals: none
- Text: 79th Independence Day Celebration @ TCE Thiagarajar College of Engineering, Madurai, cordially invites you to join us in commemorating the 79th Independence Day. Let us come together to honour our nation’s spirit of freedom, unity, and progress. 📅 Date: Friday, 15 August 2025 🕖 Time: 7:45 AM – Flag Hoisting 📍 Venue: Main Ground, TCE 🎖 Presided by: Dr. L. Ashok Kumar, Principal, TCE Agenda Highligh

### Post #893

- Source: `Jan - Sep 2025` row `394` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7307791658975145984
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `A`, reason: activity_evidence:SYMPOSIUM,CONFERENCE,CULTURAL)
- Categories: SYMPOSIUM, CONFERENCE, CULTURAL
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 13 | multi_label: 1
- Proposals: none
- Text: TCE | Department of Physics organizes 🔬✨ National Science Day 2025 - One-Day National-Level Symposium ✨🔬 🧪 Theme: Empowering Indian Youth for Global Leadership in Science & Innovation for Viksit Bharat 📅 Date: 19th March 2025 | ⏰ Time: 9:00 AM - 4:00 PM 📍 Venue: Thiagarajar College of Engineering, Madurai 🔥 Exciting Events: 🚀 Working Models (Individual & Group) 🎨 Poster Presentation (Individual) 🧠

### Post #897

- Source: `Jan - Sep 2025` row `398` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7307788591810625537
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:TECH_FEST,WORKSHOP)
- Categories: TECH_FEST, WORKSHOP
- Departments: Computer Science and Engineering
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals: none
- Text: 🎉 Get Ready for TECHUTSAV 25 - PANORAMA! 🚀 📅 Date: March 20th 🏢 Organized by: Department of Computer Science & Engineering 💡 Exciting Events: 🔎 Tech Heist 🏗️ Bid & Build 🔌 Wired Connect 💰 Win Cash Prizes 🎟️ Registration Fee: ₹500 (Includes Workshop Events) 📲 For More Details: Vineesha U: +91 89779 37889 Hariesh RP: +91 93605 81547 🖱️ Scan the QR Code to Register! Be a part of the celebration and s

### Post #915

- Source: `Jan - Sep 2025` row `416` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7304043142050127872
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:HACKATHON,SYMPOSIUM,TECH_FEST)
- Categories: HACKATHON, SYMPOSIUM, TECH_FEST, WORKSHOP
- Departments: Mechatronics
- Stakeholders: Students, Industry
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 22 | multi_label: 1
- Proposals: none
- Text: 🚀 SYNERGICZ 2.0 – TECHUTSAV’ 25🔥 Visit our page: https://synergicz.in The Mechatronics Engineering Department of Thiagarajar College of Engineering is back with SYNERGICZ 2.0 – TECHUTSAV' 25 , a National Level Technical Symposium designed to challenge your engineering skills, creativity, and innovation! 📅 Date:21st & 22nd March 📍 Venue: Thiagarajar College of Engineering Prize Pool: ₹50,000 🔹 TECH

### Post #924

- Source: `Jan - Sep 2025` row `425` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7302273911377776640
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:TECH_FEST,WORKSHOP)
- Categories: TECH_FEST, WORKSHOP
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals: none
- Text: AICTE is organizing its first-ever Tech Fest – AICTE IDEA Lab Tech Fest 2025! 🔹 Date: 7th March 2025 🔹 Venue: AICTE HQ, New Delhi Get ready to witness 70+ innovative stalls, live demonstrations, workshops, and interactive exhibits showcasing cutting-edge technology and creativity! 💡 Experience Innovation Like Never Before! Join us in this grand celebration of technology and creativity. Don't miss 

### Post #1133

- Source: `April 2024 - June 2025` row `121` | URL: none (link-less)
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:NCC)
- Categories: NCC
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2024-09-19 | AY: `2024-25`
- Flags: link_less | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: TCE | Thiagarajar College of Engineering | Madurai The 4 TN Engr COY NCC, TCE is organizing a Tree Plantation Drive at the college campus on September 19, 2024, at 4:30 PM. Our respected Principal, Dr. L. Ashok Kumar, will preside over the event. Join us in contributing to a greener and more sustainable environment! Together, let’s work towards building a greener tomorrow! 🌿 #GreenTCE #EcoFriendly

## Group B - Activity - category correction proposed (39 posts)

> ACTIVITY_CANDIDATE where a category looks over-tagged or overlapping. Special attention: ACHIEVEMENT, RESEARCH, ALUMNI, INTERNSHIP, PLACEMENT, INDUSTRY, CAMPUS.

### Post #11

- Source: `June 2025-June 2026` row `11` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468550020540137472
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,ALUMNI,RESEARCH)
- Categories: ACHIEVEMENT, ALUMNI, RESEARCH
- Departments: Electronics and Communication Engineering
- Stakeholders: Alumni, Community and Society, Government and Agencies, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 31 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🌟 **#AlumniSpotlight** Proud to celebrate **Mr. Madhan M**, B.E. ECE (2002–2006), an accomplished **Lead Agile Coach, Six Sigma Black Belt & Quality Leader at Honeywell, Madurai**. 🏆 19+ years of industry excellence 🏅 Outstanding Achiever Award Recipient 🥇 6 Honeywell Bronze Awards (2018–2026) 📜 Certified Scrum Master & Quality Auditor 💡 Recognized by DRDO for research contributions Your achieveme

### Post #12

- Source: `June 2025-June 2026` row `12` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468495454515699712
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,RESEARCH)
- Communication type: `thanks`
- Categories: ACHIEVEMENT, RESEARCH
- Departments: -
- Stakeholders: Community and Society, Faculty, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 22 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🌿🏆 Proud Moment! Celebrating 'Platinum' Excellence in Sustainability at TCE! 🏆🌿 We are absolutely delighted to announce that Thiagarajar College of Engineering has been recognized as a Platinum Sustainable Campus Partner at the prestigious Bharat Environment Program 2026. This prestigious award acknowledges our institution's unwavering dedication to excellence in: 🌱 Environmental Stewardship 🌍 Cre

### Post #13

- Source: `June 2025-June 2026` row `13` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468494693970923520
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:INTERNSHIP,ACHIEVEMENT,RESEARCH)
- Categories: INTERNSHIP, ACHIEVEMENT, RESEARCH
- Departments: Applied Mathematics and Computational Science
- Stakeholders: Students, Faculty, Industry
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 22 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence.
- Text: 🎉 Internship Achievement! Congratulations to six 3rd Year M.Sc. Data Science students of TCE Madurai for securing a 6-month Full-Time Physical Internship (June–Nov 2026) at the Advanced Geometric Computing Lab, IIT Madras under the guidance of Dr. M. Ramanathan. 🌟 Aparna J | Niranjana G | Thayumanavan S | Pradeep S S | Ragul Raj T | Senthur Aswin S 💰 Performance-Based Stipend 👏 Faculty Coordinator

### Post #15

- Source: `June 2025-June 2026` row `15` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468178193208950784
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,RESEARCH)
- Categories: ACHIEVEMENT, RESEARCH
- Departments: -
- Stakeholders: Faculty, Government and Agencies, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 21 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🎉 *Proud Moment for TCE!*🎉 🏛️ Thiagarajar College of Engineering, Madurai, has been officially recognized as a Scientific and Industrial Research Organisation (SIRO) by the Department of Scientific and Industrial Research (DSIR), Government of India. 🔬 This prestigious recognition reflects TCE's unwavering commitment to fostering a strong research culture, driving innovation, and advancing impactf

### Post #17

- Source: `June 2025-June 2026` row `17` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7467805797281062913
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:INDUSTRY,RESEARCH)
- Categories: INDUSTRY, RESEARCH
- Departments: Electrical and Electronics Engineering
- Stakeholders: Industry, Faculty, Government and Agencies, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 23 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:INDUSTRY` · confidence=low · current: INDUSTRY → proposed: verify over-tag: remove Industry Collaboration unless the text is clearly about it
    - rationale: INDUSTRY qualified via mention-style keyword(s) only (mou, industry collaboration); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electric'; generic terminology is a topic, not department evidence.
- Text: 🤝⚡ MoU Signed Between TCE Madurai & NIT Calicut Thiagarajar College of Engineering (TCE), Madurai, and National Institute of Technology (NIT) Calicut have partnered for Collaborative Research & Innovation under a MeitY–MHI funded project on next-generation Electric Vehicle technologies. 🚗🔋 Project Value: ₹319.50 Lakhs | Duration: 3 Years 🔬 Focus Areas: ✅ Battery Management Systems (BMS) ✅ EV Telem

### Post #18

- Source: `June 2025-June 2026` row `18` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7467805304127406080
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:INTERNSHIP,RESEARCH,INDUSTRY)
- Categories: INTERNSHIP, RESEARCH, INDUSTRY, CONFERENCE, WORKSHOP
- Departments: -
- Stakeholders: Industry, Faculty, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 33 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:INTERNSHIP` · confidence=low · current: INTERNSHIP → proposed: verify over-tag: remove Internship unless the text is clearly about it
    - rationale: INTERNSHIP qualified via mention-style keyword(s) only (internship, intern); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` category · rule=`cat_over_tag:INDUSTRY` · confidence=low · current: INDUSTRY → proposed: verify over-tag: remove Industry Collaboration unless the text is clearly about it
    - rationale: INDUSTRY qualified via mention-style keyword(s) only (mou); a keyword mention does not make the post an instance of this activity.
- Text: 🤝✨ Strengthening Academic Excellence Through Collaboration! Thiagarajar College of Engineering (TCE), Madurai, is proud to announce the signing of a Memorandum of Understanding (MoU) with the Indian Institute of Technology (IIT) Palakkad for Academic, Research & Innovation Collaboration. 🎓 This partnership aims to foster: 🔬 Joint Research & Development 📚 Academic & Technical Knowledge Exchange 💡 I

### Post #25

- Source: `June 2025-June 2026` row `25` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7465931080789938176
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,RESEARCH)
- Communication type: `greeting`
- Categories: ACHIEVEMENT, RESEARCH
- Departments: Computer Science and Business Systems, Computer Science and Engineering
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🎉 *Proud Moment for Thiagarajar College of Engineering* 🎉 Congratulations to our students for receiving the prestigious India AI Fellowship Scheme (Phase 1) funding of ₹50,000 for the academic year 2025–26. 👏✨ 🏆 Awardees: 🔹 Sam Rakshana – CSBS (UG) Supervisor: Ms. Priya Thiagarajan 🔹 Joline Melina A – CSE (PG) Supervisor: Dr. S. Mercy Shalinie 🔹 Keziah Kerona J – CSE (PG) Supervisor: Mr. D. Nagend

### Post #29

- Source: `June 2025-June 2026` row `29` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7463763416457908224
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2023-05-23 | AY: `2022-23`
- Flags: pre_2024_ambiguous | evidence_score: 3 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (milestone); a keyword mention does not make the post an instance of this activity.
  - `note` date · rule=`pre_2024_keep` · confidence=high · current: pre-2024 evidence (2023-05-23) → proposed: keep flagged; confirm the post belongs to the dataset before any publication
    - rationale: earliest explicit date is before 2024 and the sheet period may not cover it; never silently re-date.
- Text: 🪷 In Reverential Remembrance On the third anniversary of his passing, We remember with deep respect and gratitude *Thiru Karumuttu T. Kannan* — former Chairman & Correspondent of *Thiagarajar College of Engineering, Madurai*. 🌿 A visionary leader who nurtured institutions with wisdom, integrity, and purpose. ✨ His compassionate leadership and unwavering belief in education continue to inspire gene

### Post #31

- Source: `June 2025-June 2026` row `31` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7463573156968960000
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,ALUMNI,HACKATHON)
- Categories: ACHIEVEMENT, ALUMNI, HACKATHON, RESEARCH
- Departments: -
- Stakeholders: Government and Agencies, Alumni, Community and Society, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 30 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (publication); a keyword mention does not make the post an instance of this activity.
- Text: ✨ #AlumniSpotlight Proud to celebrate Vijay Sankar, Full Stack Gen AI Consultant at Deloitte, for his impactful journey in AI and technology innovation. 🔹 4+ years of industry experience 🔹 7+ projects | 4+ publications 🔹 10+ awards | 15+ certifications 🔹 Industry-supported Generative AI mentor for TCE students 🔹 SIH 2022 Evaluator – Ministry of Education Innovation Cell & AICTE Your achievements c

### Post #32

- Source: `June 2025-June 2026` row `32` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7463098364243431424
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:CAMPUS,INTERNSHIP,ACHIEVEMENT)
- Communication type: `greeting`
- Categories: CAMPUS, INTERNSHIP, ACHIEVEMENT
- Departments: -
- Stakeholders: Students, Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 14 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 📸🌍 My City My Nature – Nationwide Biodiversity Campaign 2026 Greetings from TCE EIACP PC RP, Thiagarajar College of Engineering, Madurai 🌿 On the occasion of International Biodiversity Day & World Environment Day 2026, we invite you to become part of a nationwide movement to document and celebrate India’s rich biodiversity. 🌱 Take just 1 nature photo near you and put your city on India’s Biodivers

### Post #34

- Source: `June 2025-June 2026` row `34` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7463094924465385472
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:CULTURAL,ACHIEVEMENT)
- Categories: CULTURAL, ACHIEVEMENT
- Departments: English
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 9 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 CAMPUS TO CAREER 2026 ✨ Confidence Creates Careers! Step into the professional world with confidence through the 5-Day Online Employability Program organized by the Department of English & Centre of Excellence in British Council at Thiagarajar College of Engineering. 📅 Date: 5th June – 9th June 2026 💻 Mode: Online (Google Meet / Zoom) ⏰ 2 Hours Per Day 💰 Registration Fee: ₹500 (Inclusive of GST)

### Post #40

- Source: `June 2025-June 2026` row `40` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7461446946612842496
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:WEBINAR,CAMPUS,INTERNSHIP)
- Categories: WEBINAR, CAMPUS, INTERNSHIP, RESEARCH
- Departments: -
- Stakeholders: Government and Agencies, Students, Faculty
- Date: status `dated` | dates: 2026-05-22 | AY: `2025-26`
- Flags: - | evidence_score: 19 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🌿 Celebrate International Day for Biological Diversity 2026 with us! 🌍 TCE EIACP PC-RP, Thiagarajar College of Engineering, under the Ministry of Environment, Forest and Climate Change, Government of India, cordially invites you to a special webinar in celebration of *Biodiversity Day 2026* themed *“Acting Locally for Global Impact.”* 🎙️ *Topic:* Biodiversity and Climate Change 👨‍🏫 *Speaker:* Dr. 

### Post #45

- Source: `June 2025-June 2026` row `45` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460926021366620160
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:FDP,RESEARCH,ACHIEVEMENT)
- Categories: FDP, RESEARCH, ACHIEVEMENT, WORKSHOP
- Departments: Information Technology
- Stakeholders: Students, Faculty, Community and Society
- Date: status `dated` | dates: 2026-05-25, 2026-05-30 | AY: `2025-26`
- Flags: - | evidence_score: 28 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 Join the Six-Day Online Faculty Development Program (FDP) on “Integrating AI into Classroom Pedagogy: Tools and Practices” 🤖📚 Organized by the Department of Information Technology, Thiagarajar College of Engineering, Madurai. 📅 Date: 25 May 2026 – 30 May 2026 💻 Mode: Virtual 💰 Registration Fee: ₹500 🎓 E-Certificate will be provided to all participants ✨ Program Highlights: ✔️ AI Tools for Teachi

### Post #46

- Source: `June 2025-June 2026` row `46` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460922049205673984
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH,CONFERENCE,INTERNSHIP)
- Categories: RESEARCH, CONFERENCE, INTERNSHIP
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 31 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:INTERNSHIP` · confidence=low · current: INTERNSHIP → proposed: verify over-tag: remove Internship unless the text is clearly about it
    - rationale: INTERNSHIP qualified via mention-style keyword(s) only (intern); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 Empowering Research. Inspiring Innovation. Thiagarajar College of Engineering proudly introduces the 🎓 *Thiagarajar Research Fellowship – Integrated Ph.D. (TRF-IP) Scheme* A prestigious initiative to support aspiring full-time research scholars pursuing 📘 Integrated Ph.D. (M.S. By Research + Ph.D.) under Anna University, Chennai. ✨ Fellowship Highlights: 💰 ₹12,500/month – First 2 Years 💰 ₹25,000

### Post #47

- Source: `June 2025-June 2026` row `47` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460627386535956480
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:INDUSTRY,WORKSHOP,ACHIEVEMENT)
- Categories: INDUSTRY, WORKSHOP, ACHIEVEMENT
- Departments: Electrical and Electronics Engineering
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 15 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: ⚡ PLAY WITH POWER ⚡ A One-Week Hands-on Certification Course for XI & XII Students by the Department of EEE at Thiagarajar College of Engineering 📅 May 25–29, 2026 📍 Power Electronics Lab, TCE 🎯 Offline Mode | Limited to 30 Students 💰 ₹1000/- (Inclusive of GST) 🔋 Explore the exciting world of Electrical & Electronics Engineering through: ✔️ Hands-on Experiments ✔️ EV & Renewable Energy Concepts ✔️

### Post #50

- Source: `June 2025-June 2026` row `50` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460132638276759552
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:WORKSHOP,ACHIEVEMENT)
- Categories: WORKSHOP, ACHIEVEMENT
- Departments: Chemistry
- Stakeholders: Students, Faculty, Industry
- Date: status `dated` | dates: 2026-05-24 | AY: `2025-26`
- Flags: - | evidence_score: 14 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence.
- Text: 🔬 Department of Physics, Thiagarajar College of Engineering, Madurai, in association with COEMRES, organizes an Offline Hands-on Workshop on 📘 “Materials Insight: From Structural Refinement to Quantum Modeling Devices” 📅 May 25–29, 2026 🕙 10:00 AM – 4:00 PM 📍 BE Lab, B-Block (1st Floor), TCE ✨ Explore hands-on training in: ✔️ FullProf Refinement ✔️ Quantum ESPRESSO ✔️ VASP ✔️ BIOVIA Materials Stud

### Post #57

- Source: `June 2025-June 2026` row `57` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459767634386001920
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:INTERNSHIP,CLUB,ACHIEVEMENT)
- Categories: INTERNSHIP, CLUB, ACHIEVEMENT
- Departments: Mechatronics
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-06-19 | AY: `2026-27`
- Flags: - | evidence_score: 19 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🤖🔥 Ready to Build the Future with Robotics? Join the Robotics Summer Internship 2026 organized by the Institution’s Innovation Council and the Centre of Excellence in Robotics, Department of Mechatronics Engineering at Thiagarajar College of Engineering. 📅 15 –19 June 2026 📍 Offline Mode 🎯 For Engineering, Polytechnic & School Students ✨ Learn Industrial & Mobile Robotics ✨ Robot Programming using

### Post #61

- Source: `June 2025-June 2026` row `61` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459103368184086529
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ALUMNI,FDP,ACHIEVEMENT)
- Categories: ALUMNI, FDP, ACHIEVEMENT
- Departments: Civil Engineering
- Stakeholders: Students, Alumni, Faculty, Industry
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 18 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ALUMNI` · confidence=low · current: ALUMNI → proposed: verify over-tag: remove Alumni unless the text is clearly about it
    - rationale: ALUMNI qualified via mention-style keyword(s) only (alumni); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 📢 Five-Day Online Training Programme 🎯 Digital Project Planning & Monitoring with BIM 📅 May 18 – 22, 2026 💻 Mode: Virtual Organized by 🏛️ Department of Civil Engineering, Thiagarajar College of Engineering (TCE), Madurai 🤝 In association with Bentley Education & TechApps ✨ Why Join? ✔️ Learn Primavera + BIM (4D & 5D) ✔️ Hands-on exposure to project planning & scheduling ✔️ Industry-oriented traini

### Post #69

- Source: `June 2025-June 2026` row `69` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7457736680696041472
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:SEMINAR,RESEARCH)
- Categories: SEMINAR, RESEARCH
- Departments: Electronics and Communication Engineering
- Stakeholders: Faculty
- Date: status `dated` | dates: 2026-05-06 | AY: `2025-26`
- Flags: - | evidence_score: 9 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🔐 The Research and Development Cell, Thiagarajar College of Engineering, cordially invites you to an insightful seminar on: “Secure by Design: Hardware Implementations of Public Key Cryptography for Resilient Systems” 🎙️ Speaker: Dr. V. R. Venkata Subramani Associate Professor, Dept. of ECE 📅 May 6, 2026 ⏰ 03:30 PM – 04:30 PM 📍 ECE Seminar Hall 🌐 www.tce.edu #ThiagarajarCollegeOfEngineering #TCEMa

### Post #73

- Source: `June 2025-June 2026` row `73` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7455806722524254208
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:INTERNSHIP,RESEARCH)
- Communication type: `greeting`
- Categories: INTERNSHIP, RESEARCH
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 7 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🎓 TCE wishes you a meaningful International Workers’ Day | May 1 Celebrating the dedication and intellectual effort 💡 that drive academic excellence, research, and innovation 🔬📚 Together, we build knowledge 📖 Together, we shape the future 🚀 #InternationalWorkersDay #LabourDay2026 #May1 #TCE #ThiagarajarCollegeOfEngineering #AcademicExcellence #Research #Innovation #HigherEducation #EngineeringEduc

### Post #75

- Source: `June 2025-June 2026` row `75` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7455571639385083905
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:HACKATHON,INDUSTRY,CLUB)
- Categories: HACKATHON, INDUSTRY, CLUB
- Departments: -
- Stakeholders: Industry, Students
- Date: status `dated` | dates: 2026-05-02 | AY: `2025-26`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:INDUSTRY` · confidence=low · current: INDUSTRY → proposed: verify over-tag: remove Industry Collaboration unless the text is clearly about it
    - rationale: INDUSTRY qualified via mention-style keyword(s) only (industry collaboration); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 Industry Innovation Hackathon 2026 Thiagarajar College of Engineering, in association with the Institution's Innovation Council, presents a dynamic innovation platform! 🗓️ May 2, 2026 📍 Open Auditorium, TCE 🎯 Theme: National Technology Day 2026 💡 25 Teams | 75 Students | 25 Mentors 🤝 Industry collaboration with JK Fenner, EY India, Edge Matrix, Harvio Tech & Aargee Equipments #TCE #Innovation #H

### Post #89

- Source: `June 2025-June 2026` row `89` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452886837200691202
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:GUEST_LECTURE,OUTREACH,CLUB)
- Categories: GUEST_LECTURE, OUTREACH, CLUB, RESEARCH
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `dated` | dates: 2026-04-25 | AY: `2025-26`
- Flags: - | evidence_score: 17 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 Distinguished Guest Lecture @ TCE Thiagarajar College of Engineering presents a special session on April 25, 2026 | 10:30 AM to 12 PM | KS Auditorium Theme: Reach the unreach- Indian Space Technology 👨‍🚀 Mr. D. Gokul Senior Scientist, Indian Space Research Organisation, Chennai ✨ Session Highlights: •⁠ ⁠Address to TCE Space Club & Engineers Without Borders (EWB) •⁠ ⁠Insights on Indian Space Tech

### Post #90

- Source: `June 2025-June 2026` row `90` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452569473758150656
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,SPORTS)
- Categories: ACHIEVEMENT, SPORTS
- Departments: -
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-05-01, 2026-05-03 | AY: `2025-26`
- Flags: - | evidence_score: 8 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: ♟️ 9th Radha Thiagarajan Memorial State-Level Open & Children’s Chess Tournament 2026–27 Organized by Thiagarajar College of Engineering, Madurai, in association with Darshini Chess Academy & Madurai District Chess Association. 📅 May 3, 2026 (Sunday) 🕘 Reporting: 8:00 AM | Round 1: 9:00 AM 📍 Open Auditorium, TCE 💰 Total Cash Prize: ₹42,100 🏆 Open Category (Top 20 Cash Prizes) 👦👧 Children Categorie

### Post #92

- Source: `June 2025-June 2026` row `92` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452370817511858176
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,SEMINAR,CAMPUS)
- Categories: ACHIEVEMENT, SEMINAR, CAMPUS, RESEARCH
- Departments: Electronics and Communication Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-22 | AY: `2025-26`
- Flags: - | evidence_score: 16 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:RESEARCH` · confidence=low · current: RESEARCH → proposed: verify over-tag: remove Research and Consultancy unless the text is clearly about it
    - rationale: RESEARCH qualified via mention-style keyword(s) only (research); a keyword mention does not make the post an instance of this activity.
- Text: 🎓 Celebrating Innovation, Research & Achievements! The Student Research Council (SRC), Thiagarajar College of Engineering cordially invites you to the Valedictory Ceremony 2025–26. Join us as we reflect on a year of impactful research, recognize excellence, and celebrate the spirit of innovation. 📅 April 22, 2026 🕒 3:30 PM – 5:00 PM 📍 ECE Seminar Hall We are honored to host Mr. Kalyanasundaram G, 

### Post #140

- Source: `June 2025-June 2026` row `140` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7446035257776107520
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ALUMNI,ORIENTATION,ACHIEVEMENT)
- Categories: ALUMNI, ORIENTATION, ACHIEVEMENT
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-04-04 | AY: `2025-26`
- Flags: - | evidence_score: 13 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ALUMNI` · confidence=low · current: ALUMNI → proposed: verify over-tag: remove Alumni unless the text is clearly about it
    - rationale: ALUMNI qualified via mention-style keyword(s) only (batch, batch of); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (milestone); a keyword mention does not make the post an instance of this activity.
- Text: 🎓 Graduation Ceremony – Batch of 2025 📺 Watch Live 🔗 https://lnkd.in/gQrqtdhZ 📅 April 4, 2026 | ⏰ 10:35 AM Celebrate the journey. Witness the pride. 🌟 #TCEGraduation #LiveNow #GraduationCeremony #ClassOf2025 #EngineeringLife #CampusCelebration #MilestoneMoment #AcademicSuccess #FutureEngineers #DreamBigAchieveBig #ProudGraduates

### Post #149

- Source: `June 2025-June 2026` row `149` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7443840323128102912
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ALUMNI,ORIENTATION,ACHIEVEMENT)
- Categories: ALUMNI, ORIENTATION, ACHIEVEMENT
- Departments: Mechanical Engineering
- Stakeholders: Alumni, Students
- Date: status `dated` | dates: 2026-04-04 | AY: `2025-26`
- Flags: - | evidence_score: 31 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ALUMNI` · confidence=low · current: ALUMNI → proposed: verify over-tag: remove Alumni unless the text is clearly about it
    - rationale: ALUMNI qualified via mention-style keyword(s) only (alumni, alumnus, batch); a keyword mention does not make the post an instance of this activity.
- Text: 🎓 Graduation Ceremony – Batch 2025 🎓 The Management, Principal, Staff, and Students cordially invite you to the Graduation Ceremony 2025. 📅 April 4, 2026 (Saturday) ⏰ 10:35 AM 📍 Karumuttu Kannan Auditorium ✨ Chief Guest Ashutosh Gupta – Managing Director, Coursera ✨ Guest of Honor V. Saravana Kumar IAS– Divisional Commissioner, Jaipur | Mechanical Engineering Alumnus (1994 Batch) 🎓 Join us as we c

### Post #164

- Source: `June 2025-June 2026` row `164` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7441097337277657088
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:HACKATHON,ACHIEVEMENT)
- Categories: HACKATHON, ACHIEVEMENT
- Departments: Applied Mathematics and Computational Science
- Stakeholders: Community and Society, Students
- Date: status `dated` | dates: 2026-05-08 | AY: `2025-26`
- Flags: - | evidence_score: 11 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 📊 *Becoming a Data Scientist – One Week Immersive Program!* 📅 May 11–15, 2026 ⏰ 10:00 AM – 4:00 PM 👨‍🎓 For School Students (12th Grade) ✨ Program Highlights: * Explore the World of Data 🔍 * Understand Data & Visualization 📈 * Introduction to AI 🤖 * Real-world Data Science Applications * Mini Hackathon Experience 🏆 💡 Why Join? ✔ Hands-on AI & Data Science Projects ✔ Certificate of Completion ✔ Expe

### Post #166

- Source: `June 2025-June 2026` row `166` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7440952130213126144
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:SYMPOSIUM,TECH_FEST,WORKSHOP)
- Categories: SYMPOSIUM, TECH_FEST, WORKSHOP, ACHIEVEMENT, CONFERENCE
- Departments: Mechatronics
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-02 | AY: `2025-26`
- Flags: - | evidence_score: 22 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 SYNERGICZ 3.0 – National Level Technical Symposium Department of Mechatronics Engineering 📅 April 2, 2026 💰 Prize Pool: ₹20,000 ✨ Explore innovation through: 🔹 Technical Workshops 🔹 Paper Presentation 🔹 Quantumania Shield Trials 🔹 Ultron Protocol (ROS Platform) 🔹 Escape Room | CineQuest 🔹 Online Idea Pitch & Photography 🎟 Pass Details: 🔸 Pass 1: Workshop + Tech + Non-Tech – ₹354 🔸 Pass 2: Paper 

### Post #170

- Source: `June 2025-June 2026` row `170` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7440416847042301953
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: Mechanical Engineering
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 10 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (accreditation, milestone); a keyword mention does not make the post an instance of this activity.
- Text: 🎉 NBA ACCREDITATION (TIER-I) Thiagarajar College of Engineering, Madurai, proudly announces 🏆 3 YEARS ACCREDITATION 🗓️ 2026 – 2028 for UG Engineering Programme: 🔹 Mechanical Engineering ✨ A proud milestone of quality, excellence, & outcome-based education 🙏 Deep gratitude to all stakeholders #NBAAccreditation #3YearsAccreditation #TCE #Tier1 #EngineeringExcellence #QualityEducation #OutcomeBasedEd

### Post #171

- Source: `June 2025-June 2026` row `171` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7440415957921099776
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: Electrical and Electronics Engineering, Civil Engineering, Electronics and Communication Engineering
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 12 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (accreditation, milestone); a keyword mention does not make the post an instance of this activity.
- Text: 🎉 NBA ACCREDITATION (TIER-I) Thiagarajar College of Engineering, Madurai, proudly announces 🏆 6 YEARS ACCREDITATION 🗓️ 2026 – 2031 for UG Engineering Programmes: 🔹 Civil Engineering 🔹 Electrical & Electronics Engineering 🔹 Electronics & Communication Engineering ✨ A proud milestone of quality, excellence & outcome-based education 🙏 Deep gratitude to all stakeholders #NBAAccreditation #6YearsAccred

### Post #187

- Source: `June 2025-June 2026` row `187` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7437535773513609216
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:HACKATHON,SYMPOSIUM,WORKSHOP)
- Categories: HACKATHON, SYMPOSIUM, WORKSHOP, ACHIEVEMENT
- Departments: Mechanical Engineering
- Stakeholders: -
- Date: status `dated` | dates: 2026-04-02 | AY: `2025-26`
- Flags: - | evidence_score: 18 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 *MOBIUS 2K26 – TECHUTSAV* The *Mechanical Engineering Association* of *Thiagarajar College of Engineering* proudly presents **MOBIUS 2K26**, a **National Level Technical Symposium**! 🔧⚙️ 📅 *Date:* April 02 , 2026 (Thursday) 🏫 *Venue:* Thiagarajar College of Engineering 💰 *Prize Pool:* ₹20,000 🍽️ *Perks:* Kit, Lunch, Refreshments & Certificate for all participants ⚡ *Open to all departments!* ✨ *

### Post #253

- Source: `June 2025-June 2026` row `253` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7426594353860714497
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:HACKATHON,SYMPOSIUM,CLUB)
- Categories: HACKATHON, SYMPOSIUM, CLUB, CONFERENCE, ACHIEVEMENT
- Departments: Electronics and Communication Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-03-14 | AY: `2025-26`
- Flags: - | evidence_score: 23 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
- Text: 🚀 ZENYTH 2026 – Where Ideas Rise to the Peak! TCE IEEE Student Branch, in association with the Department of Electronics and Communication Engineering, Thiagarajar College of Engineering brings you a 🔥 NATIONAL LEVEL TECHNICAL SYMPOSIUM 🔥 📅 March 14, 2026 🎯 MORNING TRACK Logicent – Programming Contest Circuit Debug Sprint Satellite War 💡 AFTERNOON TRACK InnoX for SDGs – Poster Presentation Line Fo

### Post #260

- Source: `June 2025-June 2026` row `260` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7425224477539758080
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:CONFERENCE,INTERNSHIP,WEBINAR)
- Categories: CONFERENCE, INTERNSHIP, WEBINAR
- Departments: -
- Stakeholders: Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 14 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`multi_label_overlap` · confidence=low · current: CONFERENCE + WEBINAR → proposed: verify multi-label: if both describe the SAME event, keep only the dominant category (CONFERENCE)
    - rationale: CONFERENCE and WEBINAR matched within the same region of the text (gap <= 30 chars); same-event synonyms should not be kept as separate activity types.
- Text: 🌐 *International Conference | Online Talk Series 📅 February 23–27, 2026* Organised by the Centre for International Affairs, Thiagarajar College of Engineering 🎙️ 5 Days | Global Experts | Future-Ready Topics: AI & Smart Cities • Ethical Leadership & HRM 4.0 • Quantum Computing • Trustworthy & Medical AI • Renewable Energy • Sustainability • Industry-Ready Engineering Education 🌍 International spea

### Post #298

- Source: `June 2025-June 2026` row `298` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7417516008531447808
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:SYMPOSIUM,TECH_FEST,WORKSHOP)
- Categories: SYMPOSIUM, TECH_FEST, WORKSHOP, ACHIEVEMENT
- Departments: Electronics and Communication Engineering
- Stakeholders: Faculty, Students
- Date: status `dated` | dates: 2026-02-07 | AY: `2025-26`
- Flags: - | evidence_score: 20 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` category · rule=`multi_label_overlap` · confidence=low · current: SYMPOSIUM + TECH_FEST → proposed: verify multi-label: if both describe the SAME event, keep only the dominant category (SYMPOSIUM)
    - rationale: SYMPOSIUM and TECH_FEST matched within the same region of the text (gap <= 30 chars); same-event synonyms should not be kept as separate activity types.
- Text: 🚀 TECHVISTA ’26 | National Level Technical Symposium Organised by the Department of Electronics & Communication Engineering, TCE in association with IEI & IETE Student Chapters 📅 7 February 2026 🎯 Events: Tech Events | Workshop | Ideathon | Project Expo | Surprise Event 🏆 Prize Pool: ₹9,000 💳 Registration Fee: ₹350 ✅ Includes certificates, lunch, refreshments & symposium kit 👩‍🏫 Faculty Coordinato

### Post #394

- Source: `June 2025-June 2026` row `394` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7400144281459486721
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:HACKATHON,INDUSTRY,ACHIEVEMENT)
- Categories: HACKATHON, INDUSTRY, ACHIEVEMENT
- Departments: -
- Stakeholders: Community and Society, Industry, Students
- Date: status `ambiguous_multi_year` | dates: 2025-12-27, 2026-01-21 | AY: `2025-26`
- Flags: multi_year | evidence_score: 16 | multi_label: 1
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:INDUSTRY` · confidence=low · current: INDUSTRY → proposed: verify over-tag: remove Industry Collaboration unless the text is clearly about it
    - rationale: INDUSTRY qualified via mention-style keyword(s) only (industry partners); a keyword mention does not make the post an instance of this activity.
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-27, 2026-01-21) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🎯 TCE AI CONSORTIUM presents – AI FUSION 2025 🤖 AI OLYMPIAD & AI HACKATHON 💡 Where Innovation Meets Intelligence! 📅 Dec 27, 2025 – Jan 21, 2026 🏫 AI Olympiad: Grade 6–12 💻 AI Hackathon: Engineering, Arts & Polytechnic Students 🧩 2 Rounds – Online & Offline (Jan 21, 2026) 🏆 Trophies & Certificates for Winners! 💰 Registration: 🎓 School – ₹300 | 🎓 College – ₹500 📌 Problem statements formulated by Ind

### Post #586

- Source: `June 2025-June 2026` row `586` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7364682051544887297
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH,CONFERENCE,GUEST_LECTURE)
- Categories: RESEARCH, CONFERENCE, GUEST_LECTURE, INTERNSHIP
- Departments: Chemistry
- Stakeholders: Students, Faculty, Government and Agencies, Industry
- Date: status `ambiguous_multi_year` | dates: 2025-12-15, 2026-01-15, 2026-01-31 | AY: `2025-26`
- Flags: multi_year | evidence_score: 33 | multi_label: 1
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence.
  - `CORRECTION` category · rule=`multi_label_overlap` · confidence=low · current: CONFERENCE + GUEST_LECTURE → proposed: verify multi-label: if both describe the SAME event, keep only the dominant category (GUEST_LECTURE)
    - rationale: CONFERENCE and GUEST_LECTURE matched within the same region of the text (gap <= 30 chars); same-event synonyms should not be kept as separate activity types.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-15, 2026-01-15, 2026-01-31) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🌍✨ ICISTEEH-26 ✨🌍 International Conference on Innovations in Sustainable Technologies for Energy, Environment & Healthcare 📅 Feb 13 & 14, 2026 📍 Thiagarajar College of Engineering, Madurai Organized by: 🔬 Department of Chemistry, TCE 🌱 TCE EIACP PC-RP (MoEF&CC, Govt. of India) 💡 About the Conference ICISTEEH-26 is a global forum bringing together leading experts, researchers, industry practitioner

### Post #747

- Source: `Jan - Sep 2025` row `248` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7331548597143949312
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2023-05-23 | AY: `2022-23`
- Flags: pre_2024_ambiguous | evidence_score: 3 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (milestone); a keyword mention does not make the post an instance of this activity.
  - `note` date · rule=`pre_2024_keep` · confidence=high · current: pre-2024 evidence (2023-05-23) → proposed: keep flagged; confirm the post belongs to the dataset before any publication
    - rationale: earliest explicit date is before 2024 and the sheet period may not cover it; never silently re-date.
- Text: *Remembering a Visionary Leader* On the second anniversary of our former beloved Chairman and Correspondent, Thiru. Karumuttu T. Kannan, we reflect with deep gratitude on his enduring vision and commitment to education. His legacy is etched in every milestone the institution achieved under his inspiring leadership. He led not with authority but with purpose, grace, and an unwavering belief in acad

### Post #1125

- Source: `April 2024 - June 2025` row `113` | URL: none (link-less)
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `ambiguous_multi_year` | dates: 2024-09-06, 2026-09-05 | AY: `2024-25`
- Flags: link_less, multi_year | evidence_score: 5 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (certificat); a keyword mention does not make the post an instance of this activity.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2024-09-06, 2026-09-05) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🚀 TCE is now an EAT RIGHT Campus, says FSSAI! 🚀 🎓 Thiagarajar College of Engineering has been officially certified as an Eat Right CAMPUS by the Ministry of Health and Family Welfare! 🌿🍽 This prestigious certification, granted by the Food Safety and Standards Authority of India (FSSAI), is valid from September 6, 2024, to September 5, 2026. 🗓 We’re committed to ensuring safe, healthy, and sustaina

### Post #1519

- Source: `April 2024 - June 2025` row `543` | URL: none (link-less)
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Communication type: `thanks`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2023-05-23 | AY: `2022-23`
- Flags: link_less, pre_2024_ambiguous | evidence_score: 3 | multi_label: 0
- Proposals:
  - `CORRECTION` category · rule=`cat_over_tag:ACHIEVEMENT` · confidence=low · current: ACHIEVEMENT → proposed: verify over-tag: remove Achievement and Awards unless the text is clearly about it
    - rationale: ACHIEVEMENT qualified via mention-style keyword(s) only (milestone); a keyword mention does not make the post an instance of this activity.
  - `note` date · rule=`pre_2024_keep` · confidence=high · current: pre-2024 evidence (2023-05-23) → proposed: keep flagged; confirm the post belongs to the dataset before any publication
    - rationale: earliest explicit date is before 2024 and the sheet period may not cover it; never silently re-date.
- Text: Remembering a Visionary Leader On the second anniversary of our former beloved Chairman and Correspondent, Thiru. Karumuttu T. Kannan, we reflect with deep gratitude on his enduring vision and commitment to education. His legacy is etched in every milestone the institution achieved under his inspiring leadership. He led not with authority but with purpose, grace, and an unwavering belief in academ

## Group C - Activity - department correction proposed (9 posts)

> ACTIVITY_CANDIDATE where the department was inferred from generic technical terminology rather than an explicit department statement. Institution-wide activities should be marked General.

### Post #105

- Source: `June 2025-June 2026` row `105` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7451458831596883968
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT,HACKATHON)
- Categories: ACHIEVEMENT, HACKATHON
- Departments: Mechatronics, Artificial Intelligence
- Stakeholders: Faculty, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 17 | multi_label: 1
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'ai-ml'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
- Text: 🎉 *Proud Moment for TCE!* Thiagarajar College of Engineering team secures 🥉 3rd Place at the National-Level ISHRAE HVACR Hackathon 2025–26! 👨‍🔬 Team (2027 Batch – Mechatronics): Dharun S | Hariharasudhan B | Harish J H | Jayasridhar V 💡 Project: AI-ML & renewable energy integration for efficient cold storage supply chains 🏆 Prize: ₹50,000 👏 Mentor: Dr. G. Kumaraguruparan 👏 Faculty Advisor: Mr. S. 

### Post #242

- Source: `June 2025-June 2026` row `242` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7428930441895694336
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:HACKATHON,TECH_FEST)
- Categories: HACKATHON, TECH_FEST
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 12 | multi_label: 1
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: T'SEDA (Architecture, Design, Planning) → proposed: verify department: drop 'T'SEDA (Architecture, Design, Planning)' (route to General or the explicitly named department) unless the post names this department
    - rationale: T'SEDA (Architecture, Design, Planning) matched only via generic technical term(s) 'architecture'; generic terminology is a topic, not department evidence.
- Text: 🚀 TECHUTSAV 2026 | Feb 27 – Mar 6 Thiagarajar College of Engineering 🏆 ₹2.7+ Lakh Prize Pool ⚡ 7+ Departments. 70+ Events. One Massive Arena. From AI & Industrial IoT to Robotics, Hackathons, CAD Battles, Ideathons & Design Challenges — this is where ideas turn into impact. 🔥 Not Just A Fest — A Battlefield For Brains. 📍 Open To All Engineering & Architecture Disciplines 🎟 Limited Slots Per Event 

### Post #261

- Source: `June 2025-June 2026` row `261` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7424410072987885569
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:ACHIEVEMENT,RESEARCH,ORIENTATION)
- Categories: ACHIEVEMENT, RESEARCH, ORIENTATION
- Departments: Chemistry, Electrical and Electronics Engineering
- Stakeholders: Faculty, Government and Agencies
- Date: status `dated` | dates: 2025-07-18, 2025-12-17 | AY: `2025-26`
- Flags: - | evidence_score: 28 | multi_label: 1
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
- Text: 🎉 Congratulations! 🎉 A proud moment for Thiagarajar College of Engineering as it secures Design Registration for the 🔬 INDUCTION-ASSISTED SOLVENT DEPOSITION REACTOR 🆔 Design No.: 466182-001 📅 Registered on: 18/07/2025 📘 Journal Date: 17/12/2025 👨‍🔬 Inventors * Dr. P. Ram Kumar – Asst. Professor, Chemistry * Dr. A. Ramalinga Chandra Sekar – Asst. Professor, Chemistry * Dr. M. Kottaisamy – Professor

### Post #400

- Source: `June 2025-June 2026` row `400` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7399725330472738816
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: Electrical and Electronics Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2023-08-16 | AY: `2023-24`
- Flags: pre_2024_ambiguous | evidence_score: 7 | multi_label: 0
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=low · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electric'; generic terminology is a topic, not department evidence.
  - `note` date · rule=`pre_2024_keep` · confidence=high · current: pre-2024 evidence (2023-08-16) → proposed: keep flagged; confirm the post belongs to the dataset before any publication
    - rationale: earliest explicit date is before 2024 and the sheet period may not cover it; never silently re-date.
- Text: Congratulations to Our Innovators! 🏅 Utility Patent Granted HYSTERESIS LOOP FRAMED ELECTRIC BICYCLE Patent No.: 202341054997 | Dated: Aug 16, 2023 Inventors: Dr. S. Julius Fusic • Dr. M. Balamurali • Dr. C. Vignesh An innovative electric bicycle featuring a hysteresis loop frame, brushless DC motor, and mono suspension system that reduces vibration by 80%, delivering a smooth, efficient, and stabl

### Post #426

- Source: `June 2025-June 2026` row `426` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394583420905037824
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:STTP,RESEARCH)
- Categories: STTP, RESEARCH
- Departments: Computer Science and Business Systems, Applied Mathematics and Computational Science, Artificial Intelligence
- Stakeholders: Students, Faculty, Industry
- Date: status `dated` | dates: 2025-11-28 | AY: `2025-26`
- Flags: - | evidence_score: 24 | multi_label: 1
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'machine learning'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
- Text: 🎯 5-Day Online Short Term Training Program (STTP) on “ Next Generation Tools and Techniques ” 📅 24 – 28 November 2025 🕒 Mode: Online Organized by the Department of Computer Science and Business Systems, Thiagarajar College of Engineering, Madurai 💡 Explore cutting-edge domains: AI • Machine Learning • Data Science • Cloud Computing • Cybersecurity • IoT • Quantum Computing 🎙 Expert Speakers from C

### Post #486

- Source: `June 2025-June 2026` row `486` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7381323674123038720
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: Civil Engineering, Mechanical Engineering, Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: Industry
- Date: status `ambiguous_multi_year` | dates: 2025-10-20, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20 | AY: `2025-26`
- Flags: multi_year | evidence_score: 20 | multi_label: 0
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'ai & ml'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electrical'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-10-20, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🚀 Call for Papers – 2025 Edition (Second Issue) 📚 🎓 Thiagarajar Journal of Engineering, Science, Design and Technology invites innovative research contributions from across India! 📌 Scope of Topics: 🔹 Engineering: Civil, Mechanical, Electrical, ECE, CSE, Environmental, Industrial & Manufacturing, Materials & Nano, Robotics 🔹 Applied Science: Physics, Chemistry, Mathematics, Data Science, Green Tec

### Post #567

- Source: `June 2025-June 2026` row `567` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7367107429655867392
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: Civil Engineering, Mechanical Engineering, Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: Industry
- Date: status `ambiguous_multi_year` | dates: 2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20 | AY: `2025-26`
- Flags: multi_year | evidence_score: 20 | multi_label: 0
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'ai & ml'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electrical'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🚀 Call for Papers – Second Issue – 2025 Edition 📚 🎓 Thiagarajar Journal of Engineering, Science, Design and Technology invites innovative research contributions from across India! 📌 Scope of Topics: 🔹 🛠️ Engineering Civil, Mechanical, Electrical | ECE | CSE | Environmental | Industrial & Manufacturing Materials & Nano | Structural | Robotics 🔹 🔬 Applied Science Physics | Chemistry | Math Modeling 

### Post #601

- Source: `June 2025-June 2026` row `601` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7362855902837669888
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: Civil Engineering, Mechanical Engineering, Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: Industry
- Date: status `ambiguous_multi_year` | dates: 2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20 | AY: `2025-26`
- Flags: multi_year | evidence_score: 20 | multi_label: 0
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'ai & ml'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electrical'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🚀 Call for Papers – Second Issue – 2025 Edition 📚 🎓 Thiagarajar Journal of Engineering, Science, Design and Technology invites innovative research contributions from across India! 📌 Scope of Topics: 🔹 🛠️ Engineering Civil, Mechanical, Electrical | ECE | CSE | Environmental | Industrial & Manufacturing Materials & Nano | Structural | Robotics 🔹 🔬 Applied Science Physics | Chemistry | Math Modeling 

### Post #660

- Source: `June 2025-June 2026` row `660` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7353000704925421568
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: Civil Engineering, Mechanical Engineering, Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: Industry
- Date: status `ambiguous_multi_year` | dates: 2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20 | AY: `2025-26`
- Flags: multi_year | evidence_score: 20 | multi_label: 0
- Proposals:
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Applied Mathematics and Computational Science → proposed: verify department: drop 'Applied Mathematics and Computational Science' (route to General or the explicitly named department) unless the post names this department
    - rationale: Applied Mathematics and Computational Science matched only via generic technical term(s) 'data science'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Artificial Intelligence → proposed: verify department: drop 'Artificial Intelligence' (route to General or the explicitly named department) unless the post names this department
    - rationale: Artificial Intelligence matched only via generic technical term(s) 'ai & ml'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Chemistry → proposed: verify department: drop 'Chemistry' (route to General or the explicitly named department) unless the post names this department
    - rationale: Chemistry matched only via generic technical term(s) 'chemistry'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `CORRECTION` department · rule=`dept_generic_term` · confidence=medium · current: Electrical and Electronics Engineering → proposed: verify department: drop 'Electrical and Electronics Engineering' (route to General or the explicitly named department) unless the post names this department
    - rationale: Electrical and Electronics Engineering matched only via generic technical term(s) 'electrical'; generic terminology is a topic, not department evidence. Another department is named explicitly in the post.
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-09-30, 2025-10-31, 2025-11-30, 2025-12-20, 2026-01-20) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🚀 Call for Papers – Second Issue – 2025 Edition 📚 🎓 Thiagarajar Journal of Engineering, Science, Design and Technology invites innovative research contributions from across India! 📌 Scope of Topics: 🔹 🛠️ Engineering Civil, Mechanical, Electrical | ECE | CSE | Environmental | Industrial & Manufacturing Materials & Nano | Structural | Robotics 🔹 🔬 Applied Science Physics | Chemistry | Math Modeling 

## Group D - Activity - stakeholder correction proposed (0 posts)

> ACTIVITY_CANDIDATE where the stakeholder may have been inferred from an isolated word instead of an intended audience/participant.

_No posts in this group._

## Group E - Non-activity - likely correct (27 posts)

> NON_ACTIVITY (admission promo / job ad / greeting / announcement / thanks) with no embedded event detected. Confirm the communication separation and that no real event is hidden in the text.

### Post #4

- Source: `June 2025-June 2026` row `4` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7470040597769306113
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: RESEARCH, INTERNSHIP, ALUMNI, INDUSTRY, PLACEMENT, WORKSHOP
- Departments: Electronics and Communication Engineering
- Stakeholders: Industry, Alumni, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 42 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH, INTERNSHIP, ALUMNI, INDUSTRY, PLACEMENT, WORKSHOP → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 📡🎓 PG Admissions 2026–27 Open at TCE! 🚀 M.E. Communication Systems Power the Future of a Smart & Connected World with expertise in: 🔷 RF and Microwave Engineering 🔷 VLSI Design and Technology 🔷 Digital and Image processing 🔷 Wireless Networks and Security 🔷 Remote Sensing and GIS ✨ Why Choose TCE? 🔹 Advanced Communication Laboratories 🔹 Industry-Oriented Curriculum & Hands-on Training 🔹 Research, 

### Post #5

- Source: `June 2025-June 2026` row `5` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7470022537813381120
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: ALUMNI
- Departments: Civil Engineering
- Stakeholders: Alumni, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 9 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: ALUMNI → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🏗️ M.E. Construction Engineering & Management @ TCE 🎓 PG Admissions 2026–27 Open ✅ BIM ✅ Lean Construction ✅ Project Management Studio ✅ Data Analytics ✅ Sustainable & Green Building Practices 💻 Bentley | Primavera P6 | Power BI 🏆 ₹54 LPA Highest Package 🏢 100+ Recruiters 🌍 100,000+ Alumni Network ⏳ Limited Seats Available! 🌐 www.tce.edu 📞 +91 452 2482240 #TCE #CEM #CivilEngineering #BIM #Construc

### Post #7

- Source: `June 2025-June 2026` row `7` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468884972427190274
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: INTERNSHIP, RESEARCH, ALUMNI
- Departments: Electrical and Electronics Engineering, Artificial Intelligence
- Stakeholders: Industry, Students, Alumni
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 26 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: INTERNSHIP, RESEARCH, ALUMNI → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓🚀 *PG Admissions 2026–27 Open at TCE!* 📢 Spot Admissions Open for ⚡ M.E. Embedded System Technologies Explore cutting-edge domains: 🤖 AI & ML 🌐 IoT ⚙️ Cyber Physical Systems 🔋 Electric Vehicles ⚡ Smart Grids 🏭 Industrial Automation 💻 Edge Computing 🏆 TCE Advantage 💰 ₹54 LPA Highest Package 🏢 100+ Recruiters 📚 5000+ Scopus Publications 🌍 100,000+ Alumni Network 🔬 Paid Internships & R&D Opportuniti

### Post #20

- Source: `June 2025-June 2026` row `20` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7467446002317217794
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: RESEARCH
- Departments: Computer Science and Engineering, Information Technology
- Stakeholders: Faculty, Students, Community and Society, Industry
- Date: status `dated` | dates: 2026-06-16 | AY: `2026-27`
- Flags: communication_only | evidence_score: 11 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🚨 *We're Hiring!* Join the academic community at Thiagarajar College of Engineering (TCE), Madurai. Applications are invited for *Assistant Professor* positions in: 💻 Computer Science & Engineering (CSE) 🌐 Information Technology (IT) ✅ M.E./M.Tech. with strong academic background ✅ Ph.D. desirable ✅ Industry professionals encouraged to apply Last Date: June 16, 2026 📧 Send your resume to: recruitm

### Post #21

- Source: `June 2025-June 2026` row `21` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7467443860412080128
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 3 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: *WE'RE HIRING* *FIRE SAFETY OFFICER* *Thiagarajar Mills & Thiagarajar Institutions* *Eligibility* ✔ Diploma / Advanced Diploma in Fire & Safety, Industrial Safety, or related discipline ✔ NEBOSH Fire Safety Certification preferred ✔ 1–3 years of relevant experience in fire safety, industrial safety, or risk management *Key Skills* 🔥 Fire Prevention & Protection 🛡 Risk Assessment & Safety Complianc

### Post #26

- Source: `June 2025-June 2026` row `26` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7465599750722170880
- Decision: **NON_ACTIVITY** / non-activity (kind `H`, reason: communication_only:greeting)
- Communication type: `greeting`
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 0 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (greeting) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: 🌙✨ Eid Mubarak from Thiagarajar College of Engineering ✨🌙 Wishing you happiness, peace, and prosperity this Eid. May this special occasion fill every heart with joy, kindness, and togetherness. 🤍 Let us celebrate the spirit of compassion, gratitude, and unity that brings communities closer. #EidMubarak #TCE #ThiagarajarCollegeOfEngineering #FestivalOfJoy #PeaceAndProsperity #Togetherness #Celebrat

### Post #27

- Source: `June 2025-June 2026` row `27` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7464362081459482624
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: INTERNSHIP, RESEARCH, ALUMNI
- Departments: T'SEDA (Architecture, Design, Planning), Computer Science and Engineering, Civil Engineering, Electronics and Communication Engineering
- Stakeholders: Students, Alumni, Industry
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 28 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: INTERNSHIP, RESEARCH, ALUMNI → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 *PG Admissions 2026–2027 Open* at Thiagarajar College of Engineering 📚 PG Programmes Offered 🏗️ Civil Engineering ▪️ M.E. Structural Engineering ▪️ M.E. Construction Engineering & Management 💻 Computer Science & Engineering ▪️ M.E. Computer Science & Engineering 📡 Electronics & Communication Engineering ▪️ M.E. Communication Systems ▪️ M.E. Embedded System Technologies 🏙️ Architecture & Planning

### Post #35

- Source: `June 2025-June 2026` row `35` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7462008474625814528
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: ACHIEVEMENT
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 6 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: ✨ Admissions Open 2026–27 ✨ Step into the world of creativity, innovation, and spatial design with the B.Des (Interior Design) programme at Thiagarajar College of Engineering under Thiagarajar School of Environmental Design and Architecture. 🏛️ Design Spaces. Shape Experiences. 📍 4-Year UG Programme 🎓 TNEA Counselling Code: 5008 🌟 NIRF All India Rank – 33 Build your future in: ✨ Interior Design ✨ 

### Post #36

- Source: `June 2025-June 2026` row `36` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7461462224600064000
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: ACHIEVEMENT
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 6 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 Admissions Open 2026–27 Begin your creative journey with Thiagarajar School of Environmental Design and Architecture, Thiagarajar College of Engineering ✨ 📚 Courses Offered 🏛️ B.Arch 🛋️ B.Des (Interior Design) 🌆 M.Plan (Urban Planning) 💡 Your Future Begins Here 🌟 Become a Part of Excellence 🌐 [Apply Now – TCE Official Website: https://lnkd.in/gHtZtig3 📍 T’SEDA, Thirupparankundram, Madurai – 625 

### Post #37

- Source: `June 2025-June 2026` row `37` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7461461548587470848
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_only:admission_promo)
- Communication type: `admission_promo`
- Categories: -
- Departments: T'SEDA (Architecture, Design, Planning), Civil Engineering
- Stakeholders: Community and Society, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 4 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: 🎓 Admissions Open | M.Plan Urban Planning 2026–2028 🏙️ Shape the future of cities with the M.Plan Urban Planning Programme at Thiagarajar School of Environmental Design and Architecture, Thiagarajar College of Engineering. 🚆 Career opportunities in DTCP, CMDA/CUMTA, Metro Rail, Municipal Corporations, NIUA, State Planning Commission & more. 📘 Eligibility: B.Arch. / B.Plan. / Civil Engineering / Ge

### Post #42

- Source: `June 2025-June 2026` row `42` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460994742256848897
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: INTERNSHIP, INDUSTRY, PLACEMENT, RESEARCH
- Departments: Applied Mathematics and Computational Science, Computer Science and Engineering
- Stakeholders: Industry, Students, Faculty, Government and Agencies
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 27 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: INTERNSHIP, INDUSTRY, PLACEMENT, RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: *Admissions Open 2026!* 🚀 Integrated M.Sc (Data Science) [5 Years] at Thiagarajar College of Engineering (TCE), Madurai *for HSC Students* Integrated M.Sc (Data Science) – 5 Years at Thiagarajar College of Engineering (TCE), Madurai 📘 Dept. of Applied Mathematics & Computational Science 📊 Interdisciplinary curriculum blending Mathematics, Statistics & Computer Science ✨ Highlights: Industry collab

### Post #51

- Source: `June 2025-June 2026` row `51` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459927837899165696
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: RESEARCH
- Departments: Computer Science and Business Systems, Computer Science and Engineering, Electronics and Communication Engineering
- Stakeholders: Faculty, Government and Agencies, Industry, Students
- Date: status `dated` | dates: 2026-05-15 | AY: `2025-26`
- Flags: communication_only | evidence_score: 10 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🚀 Recruitment 2026 @ Thiagarajar College of Engineering Applications are invited for Assistant Professor positions under the Self Financing Scheme in: 📘 ECE | CSE | IT | CSBS | Physics ✨ Attractive Salary 🎓 Qualification & Salary: As per AICTE Norms 📅 Last Date to Apply: May 15, 2026 Why join TCE? ✅ Legacy of excellence since 1957 ✅ Strong research & innovation ecosystem ✅ Industry-driven academic

### Post #52

- Source: `June 2025-June 2026` row `52` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459909558786740225
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: RESEARCH, ACHIEVEMENT
- Departments: Electrical and Electronics Engineering, Civil Engineering, Electronics and Communication Engineering, Information Technology, Mechanical Engineering, Mechatronics, Chemistry, Computer Science and Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-05-15 | AY: `2025-26`
- Flags: communication_only | evidence_score: 34 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH, ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 Admissions Open 2026–27 | QIP @ TCE – Apply Now! Advance your research journey at Thiagarajar College of Engineering (TCE), a recognized Minor QIP Centre. 🔬 Why TCE? * 500+ PhD Scholars Awarded * 5000+ Scopus Publications | 67K+ Citations | h-index: 111 * 45+ Crores Research Funding * 26 Centres of Excellence * 100+ Research Supervisors 🎓 Programmes Offered 📘 Ph.D. Departments: * Civil Engineeri

### Post #60

- Source: `June 2025-June 2026` row `60` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459103527534141440
- Decision: **NON_ACTIVITY** / non-activity (kind `H`, reason: communication_only:greeting)
- Communication type: `greeting`
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 1 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (greeting) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: Greetings from TCE EIACP PC-RP, TCE EIACP PC-RP On the occasion of World Migratory Bird Day 2026, we warmly invite you to participate in our digital awareness initiative and support bird conservation efforts. Every bird counts, and your small participation can create a meaningful impact toward environmental awareness and biodiversity protection. 📌 Participate in the event by: * Sharing your basic 

### Post #62

- Source: `June 2025-June 2026` row `62` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459095475015720960
- Decision: **NON_ACTIVITY** / non-activity (kind `E`, reason: communication_only:thanks)
- Communication type: `thanks`
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-05-11 | AY: `2025-26`
- Flags: communication_only | evidence_score: 0 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (thanks) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: *Happy Mother’s Day | 11 May 2026* 🌸 To every guiding mother — thank you for being the strength, support, and inspiration behind every learner’s journey in higher education and beyond. Thiagarajar College of Engineering extends heartfelt wishes to all mothers in our TCE family. 💙 #HappyMothersDay #MothersDay2026 #TCE #ThiagarajarCollegeOfEngineering #HigherEducation #GuidingMothers #WomenOfStrengt

### Post #63

- Source: `June 2025-June 2026` row `63` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7458366429730463744
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: INTERNSHIP, ACHIEVEMENT, CAMPUS, PLACEMENT, SPORTS, CLUB, RESEARCH
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Government and Agencies, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 41 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: INTERNSHIP, ACHIEVEMENT, CAMPUS, PLACEMENT, SPORTS, CLUB, RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: Admissions Open 2026–2027 at Thiagarajar College of Engineering ✨ Government Aided Autonomous Institution 🏆 NAAC A++ | NBA Accredited Courses | NIRF Ranked 🎓 100% Tuition Fee Waiver for Government Aided Courses (Counselling Seats) 📍 TNEA Counselling Code: 5008 Why Choose TCE? ✔️ 90% Placement Consistency ✔️ ₹1.1 Lakh/month Highest Internship Stipend ✔️ Strong Industry Connect & 74+ MoUs ✔️ 26 Cent

### Post #65

- Source: `June 2025-June 2026` row `65` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7457829977397575682
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: CAMPUS, ALUMNI, PLACEMENT, ACHIEVEMENT
- Departments: Civil Engineering, Mechanical Engineering, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: Alumni, Government and Agencies, Industry
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 26 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: CAMPUS, ALUMNI, PLACEMENT, ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 Admissions Open 2026–27 | Thiagarajar College of Engineering, Madurai Begin your engineering journey at one of Tamil Nadu’s premier institutions with a legacy of excellence since 1957. ✅ Govt. Aided Autonomous Institution 📍 TNEA Code: 5008 💯 Tuition Fee Waiver for Eligible Aided Counselling Seats 🏆 NAAC A++ (3.56/4.00) | NIRF 2024 Rank Band: 101–150 💼 90% Placement Consistency | ₹54 LPA Highest 

### Post #66

- Source: `June 2025-June 2026` row `66` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7457828239043080192
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: INTERNSHIP, INDUSTRY, PLACEMENT, RESEARCH
- Departments: Applied Mathematics and Computational Science, Computer Science and Engineering
- Stakeholders: Industry, Students, Faculty, Government and Agencies
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 27 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: INTERNSHIP, INDUSTRY, PLACEMENT, RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: Admissions Open 2026! 🚀 Integrated M.Sc (Data Science) [5 Years] at Thiagarajar College of Engineering (TCE), Madurai for HSC Students Integrated M.Sc (Data Science) – 5 Years at Thiagarajar College of Engineering (TCE), Madurai 📘 Dept. of Applied Mathematics & Computational Science 📊 Interdisciplinary curriculum blending Mathematics, Statistics & Computer Science ✨ Highlights: Industry collaborat

### Post #87

- Source: `June 2025-June 2026` row `87` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7453329417784754176
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: RESEARCH, ACHIEVEMENT
- Departments: Chemistry
- Stakeholders: Faculty, Government and Agencies, Industry
- Date: status `dated` | dates: 2026-05-15 | AY: `2025-26`
- Flags: communication_only | evidence_score: 17 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH, ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🚨 Recruitment 2026 – Thiagarajar College of Engineering, Madurai Join a legacy of excellence at Thiagarajar College of Engineering (Since 1957) — where quality and ethics matter. ✨ Open Positions: Professor – Chemistry, Mathematics, English 🎓 Eligibility: Ph.D. | 15+ years experience | As per AICTE norms 💰 Attractive Salary 📅 Last Date to Apply: 15 May 2026 💡 Why TCE? * NAAC A++ Accredited * Stron

### Post #95

- Source: `June 2025-June 2026` row `95` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452236587314151424
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: RESEARCH, ACHIEVEMENT
- Departments: Electrical and Electronics Engineering, Civil Engineering, Electronics and Communication Engineering, Information Technology, Mechanical Engineering, Mechatronics, Chemistry, Computer Science and Engineering
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-30 | AY: `2025-26`
- Flags: communication_only | evidence_score: 34 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH, ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 Admissions Open 2026–27 | QIP @ TCE – Apply Now! Advance your research journey at Thiagarajar College of Engineering (TCE), a recognized Minor QIP Centre. 🔬 Why TCE? * 500+ PhD Scholars Awarded * 5000+ Scopus Publications | 67K+ Citations | h-index: 111 * 45+ Crores Research Funding * 26 Centres of Excellence * 100+ Research Supervisors 🎓 Programmes Offered 📘 Ph.D. Departments: * Civil Engineeri

### Post #127

- Source: `June 2025-June 2026` row `127` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7448957674089529344
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: RESEARCH, ACHIEVEMENT
- Departments: Electronics and Communication Engineering
- Stakeholders: Government and Agencies, Students
- Date: status `dated` | dates: 2026-04-30 | AY: `2025-26`
- Flags: communication_only | evidence_score: 15 | multi_label: 1
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH, ACHIEVEMENT → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🚨 We’re Hiring – Research Opportunity! Join Thiagarajar College of Engineering for a CAIR-DRDO funded project in the Department of ECE. 🔹 Position: Project Associate (1 Post) 💰 Salary: ₹21,500/month (Consolidated) 📅 Duration: 18 Months 🎓 Eligibility: * B.E./B.Tech in ECE (First Class) * From AICTE/UGC recognized institutions 📡 Specialization: Signal Processing & Wireless Communication 📩 Apply: pgs

### Post #169

- Source: `June 2025-June 2026` row `169` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7440950054665789440
- Decision: **NON_ACTIVITY** / non-activity (kind `H`, reason: communication_only:greeting)
- Communication type: `greeting`
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 0 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (greeting) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: 🌙✨ Eid Mubarak! ✨🌙 Thiagarajar College of Engineering extends warm wishes to you and your loved ones on this joyous occasion of Eid. 🤝💫 May this special day bring peace 🕊️, happiness 😊, and prosperity 🌟 to all. Let us celebrate the spirit of togetherness, compassion, and gratitude. 🌙💛 #EidMubarak #TCE #ThiagarajarCollegeOfEngineering #FestiveGreetings #EidWishes #SpreadJoy #PeaceAndProsperity #Tog

### Post #195

- Source: `June 2025-June 2026` row `195` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7437052216152203265
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_only:job_ad)
- Communication type: `job_ad`
- Categories: -
- Departments: Information Technology
- Stakeholders: Government and Agencies, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 3 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: 🚨 *Job Opportunities at TCE!* Under the Environmental Information, Awareness, Capacity Building and Livelihood Programme (EIACP) scheme of the Ministry of Environment, Forest and Climate Change, applications are invited for the following positions: 🔹 Program Officer 🔹 Information Technology Officer 🌱 About TCE EIACP: A specialized resource partner at TCE focusing on Plastic Waste Management, contr

### Post #198

- Source: `June 2025-June 2026` row `198` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7436373407010811904
- Decision: **NON_ACTIVITY** / non-activity (kind `H`, reason: communication_only:greeting)
- Communication type: `greeting`
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-03-08 | AY: `2025-26`
- Flags: communication_only | evidence_score: 0 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (greeting) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
- Text: 🌸 Happy Women’s Day March 8, 2026 TCE wishes everyone a Happy Women’s Day. As we celebrate the spirit of “Give to Gain,” we honor the strength, leadership, and inspiring contributions of women who shape a better and sustainable future. #WomensDay2026 #GiveToGain #SDG5 #GenderEquality #TCE #ThiagarajarCollegeOfEngineering #EmpowerWomen #SustainableFuture

### Post #247

- Source: `June 2025-June 2026` row `247` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7427682900646748160
- Decision: **NON_ACTIVITY** / non-activity (kind `G`, reason: communication_override:admission_promo (category keywords are program-feature mentions))
- Communication type: `admission_promo`
- Categories: RESEARCH
- Departments: Civil Engineering, Mechatronics, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering
- Stakeholders: -
- Date: status `dated` | dates: 2026-03-10 | AY: `2025-26`
- Flags: communication_only | evidence_score: 23 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (admission_promo) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:admission_promo (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🎓 Thiagarajar Post Doctoral Fellowship (TPDF) 2026 🚀 Admissions Open 🔹 Offering Departments: EEE | Civil | ECE | CSE | IT | CSBS | Mechatronics 🔹 Eligibility: ✔ Ph.D. Degree / Completed Viva-Voce in Thrust Areas / Frontier Technologies ✔ Minimum 3 SCImago Q1 Journal Publications ✔ Age below 40 years ⏳ Duration: 24 Months 💰 Fellowship: ₹45,000/month 💎 Total Stipend: ₹10,80,000 🗓 Last Date to Apply:

### Post #258

- Source: `June 2025-June 2026` row `258` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7426116373627723777
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: ALUMNI
- Departments: -
- Stakeholders: Students, Alumni, Community and Society, Faculty, Parents
- Date: status `undated` | dates: none | AY: `undated`
- Flags: communication_only | evidence_score: 10 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: ALUMNI → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🗣️ LET’S TALK! MEET YOUR PAL Have a conversation with Dr. L. Ashok Kumar Principal ✨ An open and friendly space for students, parents, alumni, faculty, and staff 💬 Share your ideas, concerns, and feedback — openly and without hesitation 🤝 Let’s connect, collaborate, and grow together as the TCE community 🚶 You’re welcome anytime Walk in. Talk freely. 📞 +91 98432 81115 📧 askurpal.tce@gmail.com #Let

### Post #265

- Source: `June 2025-June 2026` row `265` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7424303834551836672
- Decision: **NON_ACTIVITY** / non-activity (kind `F`, reason: communication_override:job_ad (category keywords are program-feature mentions))
- Communication type: `job_ad`
- Categories: RESEARCH
- Departments: Computer Science and Engineering, Electrical and Electronics Engineering
- Stakeholders: Students, Government and Agencies
- Date: status `dated` | dates: 2026-02-13 | AY: `2025-26`
- Flags: communication_only | evidence_score: 17 | multi_label: 0
- Proposals:
  - `note` status · rule=`comm_separation_confirmed` · confidence=high · current: NON_ACTIVITY (job_ad) → proposed: keep NON_ACTIVITY after reading the text
    - rationale: communication posts (admission promo, job ad, greeting, congratulation, announcement, thanks) are separated from activities; verify the text is genuinely a communication.
  - `note` category · rule=`comm_mention_context` · confidence=high · current: RESEARCH → proposed: context only: do NOT count as the post's activity type
    - rationale: category keywords are program-feature mentions inside a communication post (reason: communication_override:job_ad (category keywords are program-feature mentions)); they are kept as evidence, not as a classification.
- Text: 🚨 JRF Recruitment | MeitY–MHI EVSS Project | TCE, Madurai Thiagarajar College of Engineering invites applications from Indian Nationals for Junior Research Fellow (JRF) – 1 Post 🔋 Project: State-of-the-Art Indigenous Development of Battery Systems and Telematics for Next-Generation Electric Vehicles. 💰 ₹37,000/month + HRA 🎓 M.E./M.Tech (Power Electronics / Power Systems / Energy / CSE or related) 

## Group F - Non-activity - should be activity (embedded event) (0 posts)

> NON_ACTIVITY that appears to contain a genuine embedded event (strong event term + explicit date). Proposes promoting the post to ACTIVITY_CANDIDATE.

_No posts in this group._

## Group G - Review / unclear (57 posts)

> REVIEW_REQUIRED: the classifier could not decide (weak/url-only text or insufficient evidence). Human decides from the text and URL.

### Post #14

- Source: `June 2025-June 2026` row `14` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7468272640743395328
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Industry
- Date: status `dated` | dates: 2026-06-04 | AY: `2026-27`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🤝 *Meeting with the Hon'ble Chief Minister of Tamil Nadu* On *4 June 2026, Mr. K. Hari Thiagarajan, Chairman and Correspondent of Thiagarajar College of Engineering, Madurai, had an interaction with the Hon'ble Chief Minister of Tamil Nadu, **Thiru. C. Joseph Vijay*. The meeting reflected a shared commitment towards the progress of Tamil Nadu and the advancement of education, industry, and innovat

### Post #44

- Source: `June 2025-June 2026` row `44` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460927468476997634
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🚀 Day 4 at IDE Boot Camp 2026 sparked creativity, strategy, and innovation-driven thinking among participants! ✨ Sessions focused on: 🎨 Design to Delight 🖥️ Design & Present Working Session 💰 Financial Literacy 📈 Innovation & Funding A dynamic day of learning where students explored user-centric design, presentation skills, financial planning, and startup funding essentials. 🌟 #TCE #IDEBootCamp #I

### Post #49

- Source: `June 2025-June 2026` row `49` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7460590337359601664
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🚀 From Ideas to Impact — Day 3 at IDE Boot Camp 2026! TCE campus buzzed with creativity and entrepreneurial energy as participants explored the journey of building real-world startup solutions. 💡 ✨ Day 3 Highlights: 🎤 Crafting compelling Pitch Canvases 📈 Understanding sustainable Revenue Models 🚀 Transforming Prototypes into MVPs 🏢 Experiencing the startup ecosystem through an Incubator Visit The 

### Post #53

- Source: `June 2025-June 2026` row `53` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459820064435900416
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Government and Agencies, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: ✨ Day 2 of the IDE Bootcamp 2026 at Thiagarajar College of Engineering featured an inspiring Entrepreneur Talk Session with industry experts sharing insights on innovation, startups, and emerging technologies. Organized under the initiatives of the Ministry of Education, Government of India, AICTE, Wadhwani Foundation, and SBI Foundation – Service Beyond Banking, the session encouraged students to

### Post #54

- Source: `June 2025-June 2026` row `54` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459819120469995520
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `dated` | dates: 2026-05-11 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🚀 TCE IDE Boot Camp Phase III inaugurated at KS Auditorium, TCE, on May 11, 2026. ✨ 200+ students across Tamil Nadu ✨ Innovation | Entrepreneurship | Design Thinking ✨ Organized with AICTE Innovation Centre Chief Guest: Mr. A. S. Sakti Balan, AGM, NABARD, Chennai Guest of Honour: Mr. R. Anandasivaraj, AICTE Innovation Centre, Chennai A 5-day journey of ideas, innovation, validation, and startup le

### Post #55

- Source: `June 2025-June 2026` row `55` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459816627883151361
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Computer Science and Engineering
- Stakeholders: Faculty, Government and Agencies, Students
- Date: status `dated` | dates: 2026-05-11 | AY: `2025-26`
- Flags: - | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: 🚀 TCE IDE Boot Camp Phase III was inaugurated on May 11, 2026, at KS Auditorium, Thiagarajar College of Engineering, Madurai. Organized in association with the AICTE Innovation Centre, the 5-day boot camp brings together 200+ students from various colleges across Tamil Nadu to nurture innovation, entrepreneurship, and design thinking. The inaugural session was graced by: ✨ Chief Guest – Mr. A. S. 

### Post #58

- Source: `June 2025-June 2026` row `58` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7459105011864739840
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Applied Mathematics and Computational Science
- Stakeholders: Students
- Date: status `dated` | dates: 2026-05-11 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🌱🤖 Join us at Thiagarajar College of Engineering for the ISTE-BNY Sponsored One Week Knowledge Enhancement Programme 2026 on “Synergistic AI for Sustainable Innovation in Agriculture and Healthcare” 📅 May 11, 2026 | Monday 🕤 9:30 AM – 11:00 AM Chief Guest: Dr. S. Basil Gnanappa Organized by the Department of Applied Mathematics and Computational Science. #TCE #ThiagarajarCollegeOfEngineering #ISTE

### Post #74

- Source: `June 2025-June 2026` row `74` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7455804998778757120
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-05-01 | AY: `2025-26`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🌸 *சித்திரை திருவிழா நல்வாழ்த்துகள்* 🌸 May 1, 2026 மதுரை நகரின் ஆன்மிக பெருவிழாவான சித்திரை திருவிழா சிறப்பு தருணத்தில் ✨ அழகர் ஆற்றில் இறங்கும் திருநிகழ்வை முன்னிட்டு ✨ 🙏 இந்த புனித நிகழ்வில் கலந்து கொள்கிற அனைத்து பக்தர்களுக்கும் தியாகராசர் பொறியியற் கல்லூரி சார்பில் மனமார்ந்த வாழ்த்துக்கள்! 🌼 அழகர் அருள் உங்கள் வாழ்க்கையில் அமைதி • வளம் • ஆனந்தம் நிரப்பட்டும் 🌿 பக்தியும் பாரம்பரியமும் இணையும் இ

### Post #76

- Source: `June 2025-June 2026` row `76` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7455414101528461312
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students, Government and Agencies
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🚀 TCE Students, This is Your Moment! Join the IDE Bootcamp (Phase III) and turn your ideas into real-world impact. 💡 Innovate. Design. Build. Pitch. 📅 May 11 – 15, 2026 🎯 Open to all UG & PG students of Thiagarajar College of Engineering 🔥 Learn from experts | Build innovation skills | Collaborate & win recognition ⏳ Limited seats – Register now! 🔗 https://lnkd.in/gSguw9r4 #IDEBootcamp #TCE #Innov

### Post #78

- Source: `June 2025-June 2026` row `78` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7455136953131487232
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🎉 Celebrating 23 Years of Excellence with Cisco Networking Academy! Thiagarajar College of Engineering proudly marks 23+ years of impactful collaboration with Cisco Networking Academy — empowering students with industry-relevant networking and digital skills. From 10 years of active participation (2011) to 15 years of dedicated service (2023), this journey reflects a strong commitment to quality e

### Post #88

- Source: `June 2025-June 2026` row `88` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452908101273403394
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-23 | AY: `2025-26`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🇮🇳 Your Vote. Your Future. Thiagarajar College of Engineering (TCE), Madurai, encourages every responsible citizen to make their voice count. 🗳️ Voting Date: 23 April 2026 Be the change. Shape the nation. Let’s stand together for a stronger democracy. #TCE #ThiagarajarCollegeOfEngineering #Vote2026 #YourVoteYourVoice #ResponsibleCitizen #IndiaVotes #YouthForChange #DemocracyInAction #VoteForFuture

### Post #98

- Source: `June 2025-June 2026` row `98` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7452220352799117312
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Mechanical Engineering
- Stakeholders: Faculty, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: 🎓 Thiagarajar College of Engineering presents ⚙️ Mechanical Engineering & Robotics Bootcamp 2026 🔍 Hands-on learning with Robotics, CNC, IC Engines & Manufacturing 🌱 Explore Solar Tech, Cold Storage & Engineering Practices 👨‍🏫 Interact with expert faculty 📅 May 5–8, 2026 ⏳ Apply before May 1 💰 ₹850 + GST 👥 For XI, XII & Diploma Students 📲 Register now: www.tce.edu #TCE #EngineeringExploration #Rob

### Post #108

- Source: `June 2025-June 2026` row `108` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450772001536868352
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Industry, Students
- Date: status `dated` | dates: 2026-04-22 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🚀 Bajaj STEP Centre Inauguration at TCE Thiagarajar College of Engineering invites you to the inauguration of the Bajaj Service Training Excellence Program (STEP) Centre 🤝 A collaborative initiative by Bajaj Auto CSR (Bajaj STEP), TCE, and GTT Foundation. 22 April 2026 🕘 9:30 AM 📍 Opposite to Guest House, TCE, Madurai 🎖 Chief Guest: Ms. Ligi George, MD – Madras Suspensions Pvt. Ltd. 🎗 Guest of Hon

### Post #117

- Source: `June 2025-June 2026` row `117` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7450070506751311872
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Faculty
- Date: status `dated` | dates: 2025-04-08 | AY: `2024-25`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: ✨ Release of TCE Newsletter 2025 ✨ 📘 The Newsletter 2025 of Thiagarajar College of Engineering was formally released by our respected Chairman on April 8, 2025, in the presence of the Principal, Dean, and faculty members. #TCE #TCEMadurai #Newsletter2025 #EventHighlights #AcademicExcellence #ProudToBeTCE

### Post #126

- Source: `June 2025-June 2026` row `126` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7449639014954979328
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🌸 தமிழ் புத்தாண்டு நல்வாழ்த்துக்கள்! 🌸 தியாகராசர் பொறியியற் கல்லூரியின் சார்பாக அனைவருக்கும் இனிய பராபவ ஆண்டு தமிழ் புத்தாண்டு நல்வாழ்த்துக்கள்! 📅 ஏப்ரல் 14, 2026 இந்த புத்தாண்டு உங்கள் வாழ்வில் புதிய தொடக்கங்கள், அறிவு, ஆரோக்கியம் மற்றும் வளம் நிரப்பட்டும். கல்வி, ஆய்வு மற்றும் சாதனைகளில் சிறந்து விளங்க மனமார்ந்த வாழ்த்துகள். #TamilNewYear #PuthanduVazhthukal #TCE #ThiagarajarCollege #NewBeginnin

### Post #141

- Source: `June 2025-June 2026` row `141` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7446009296611442688
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-04-06 | AY: `2025-26`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🎓 College Connect Series @ TCE, TC, Madurai Explore the world of data careers! 🚀 “Data Analyst vs Data Engineer vs Data Scientist” 📅 6 April 2026 ⏰ 3:30 – 4:30 PM IST 🔗 Register: https://lnkd.in/g5xYKAqK ▶️ Past Sessions: https://lnkd.in/dCpV4jhb 📱 Follow TCS iON Instagram: https://lnkd.in/gp4ADaQW LinkedIn: https://lnkd.in/gqiRVSv6 Facebook: https://lnkd.in/gsuH99Nt #TCE #TCEMadurai #ThiagarajarC

### Post #204

- Source: `June 2025-June 2026` row `204` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7435149888822259715
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: T'SEDA (Architecture, Design, Planning), Chemistry
- Stakeholders: -
- Date: status `dated` | dates: 2026-03-06 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🌿 Panel Discussion on The Sustainability Outlook Investment, Impact & Interdisciplinary Action Thiagarajar College of Engineering – T'SEDA presents an engaging panel discussion featuring experts from architecture, engineering, chemistry, HVAC, and project management. 🗓 March 6, 2026 🕞 3:30 PM 📍 Multipurpose Hall, T'SEDA, TCE Join us for insightful conversations on shaping a sustainable built envir

### Post #212

- Source: `June 2025-June 2026` row `212` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7433018372193255424
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🌍 World Sustainable Energy Day – February 27 TCE celebrates World Sustainable Energy Day, reaffirming our commitment to SDG 7—Affordable & Clean Energy. 🌱 TCE’s Sustainable Energy Practices 🔋 3 Biogas Plants powering hostel needs 🌧 3.5 Lakh sq.ft Rainwater Harvesting coverage 🌳 2000+ Trees nurturing our Campus Forest ♻ 167 kLD Sewage Treatment & Water Reuse capacity 🛣 Pioneer in Plastic Tar Roads 

### Post #213

- Source: `June 2025-June 2026` row `213` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7432831315701288961
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Applied Mathematics and Computational Science, Computer Applications, Computer Science and Business Systems, Computer Science and Engineering
- Stakeholders: -
- Date: status `dated` | dates: 2026-02-27 | AY: `2025-26`
- Flags: - | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: 🎉 TECHUTSAV PARADIGM ’26 – Inaugural Ceremony The Departments of CSE, IT, CSBS, AMCS & MCA cordially invite you to the Inaugural Ceremony of TECHUTSAV PARADIGM ’26 🎙 Chief Guest: R. Ramanathan Principal Process Engineer, Kapitus, Chennai 📅 February 27, 2026 ⏰ 09:30 AM 📍 KK Auditorium Join us as we kickstart a celebration of innovation, technology, and talent! #TCE #Techutsav2026 #Paradigm26 #Innov

### Post #230

- Source: `June 2025-June 2026` row `230` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7431092539660697601
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `dated` | dates: 2026-02-27, 2026-03-21 | AY: `2025-26`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: ✨ JUSTICE BYTES–2026 A Social Impact Multimedia Contest Thiagarajar College of Engineering (TCE ADC), in collaboration with the Justice Shivraj Patil Foundation, presents a unique contest on the occasion of World Day of Social Justice. 🎯 Theme: Life journey & landmark judgments of Justice Shivraj V. Patil 🎬 Create AI-based multimedia storytelling reflecting social justice, constitutional values & 

### Post #234

- Source: `June 2025-June 2026` row `234` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7430217788398456832
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: 🌟 *TCE Team Leadership Programme* February 20 & 21 Venue: Kodaikanal Thiagarajar College of Engineering is organizing a focused leadership development programme for *Heads, Deans & Registrar* . The programme is designed to strengthen strategic thinking, decision-making, team building, communication, and emotional intelligence through interactive sessions and experiential activities. Participants w

### Post #254

- Source: `June 2025-June 2026` row `254` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7426593231230091264
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Students, Community and Society
- Date: status `dated` | dates: 2026-02-24, 2026-02-27 | AY: `2025-26`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: 🎨 WORLD SUSTAINABLE ENERGY WEEK 2026 | POSTER DESIGN COMPETITION 🌍 T’SEDA – Thiagarajar College of Engineering (Since 1957) Where quality and ethics matter 🗓 24–27 Feb 2026 💡 Be the Spark. Drive the Change! Theme: Sustainable Development Goals (SDGs) Categories 👧 School Students: SDG 6, 7, 12 🎓 College Students: SDG 11, 12, 13 ⏰ Last date for online submission: 24 Feb 2026 📩 Contact: drnarch@tce.e

### Post #255

- Source: `June 2025-June 2026` row `255` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7426592752898920448
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: T'SEDA (Architecture, Design, Planning)
- Stakeholders: Students, Community and Society
- Date: status `dated` | dates: 2026-02-24, 2026-02-27 | AY: `2025-26`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: 🎬 LIGHTS. CAMERA. SUSTAINABLE ACTION! 🌍 T’SEDA – Thiagarajar School of Environmental Design & Architecture presents SHORT FILM COMPETITION on SDGs as part of World Sustainable Energy Week 2026 📅 24–27 Feb 2026 ⏰ Last date for submission: 24 Feb 2026 🎞️ Theme: Sustainable Development Goals (SDGs) 👥 Open to: School & College Students 👨‍👩‍👧‍👦 Team size: Up to 5 🗣️ Language: Tamil / English ⏱️ Duratio

### Post #267

- Source: `June 2025-June 2026` row `267` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7424302333964017664
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Faculty, Industry
- Date: status `dated` | dates: 2026-02-03 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🎙️ TCE at Science, Technology & Startup Innovation Fest 2026 Dr. L. Ashok Kumar, Principal, Thiagarajar College of Engineering, Madurai, will deliver a Science Talk on “Catalyzing Collaboration between Industry & Academia” 📍 MSP Auditorium, Dindigul 🕒 3.00 – 4.00 PM 📅 Jan 28 – Feb 3, 2026 🎟️ Entry Free Organised by Dindigul District Administration & Prof. S. S. Nagarajan Science Foundation ✨ Advan

### Post #269

- Source: `June 2025-June 2026` row `269` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7424247183954268161
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🕉️ ஸ்ரீ கலைமஹா கணபதி ஆலய வருடாபிஷேகம் 🕉️ நமது கல்லூரியின் ஸ்ரீ கலைமஹா கணபதி ஆலயத்தில் வருடாபிஷேகம் சிறப்பாக நடைபெற உள்ளது. 📅 நாள் : 03.02.2026 (செவ்வாய்க்கிழமை) ⏰ காலை 8.30 மணி முதல் நிகழ்ச்சி விவரங்கள் : * விக்னேஷ்வர பூஜை * புண்யாஹவாசனம் * மஹாகணபதி மூல மந்திர ஹோமம் * ⏰ காலை 9.30 மணி – பூர்ணாஹுதி, த்ரவ்யாபிஷேகம், கலசாபிஷேகம் * தீபாராதனை * ⏰ காலை 10.45 மணி – ப்ரசாதம் வழங்குதல் ஹோமம் மற்றும் பூஜையில

### Post #282

- Source: `June 2025-June 2026` row `282` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7420371603135586304
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2026-01-23 | AY: `2025-26`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🔐 Cyber Security Essentials 🔐 Understanding Modern Threats & Practical Defense 🗣 Expert Speaker Mr. Sankarraj Subramanian Founder & CEO, Prompt Infotech, Coimbatore 📅 Jan 23, 2026 ⏰ 1:45 PM – 3:30 PM 📍 K.S. Auditorium 🔗 Scan & Register Now #CyberSecurity #ExpertLecture #ITDepartment #CyberThreats #TCE #TechTalk #EthicalEngineering

### Post #310

- Source: `June 2025-June 2026` row `310` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7415982659241156608
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🏎️ Kudos to Team Prometheans E83 from Thiagarajar College of Engineering! 🎉 💥 Competing in the eBAJA SAEINDIA 2026 Endurance Race! 💥 🔥 4 Hours of Grit, Speed, and Teamwork 🔥 📅 11th Jan 2026| 🕗 9 AM 🏁 Among 90 Competitive Teams, our team is pushing boundaries on the track! 📺 Watch the live streaming and cheer for Team Prometheans! 👉 Join the race live here!: https://lnkd.in/gdcVKcPK Congratulations

### Post #333

- Source: `June 2025-June 2026` row `333` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7410055784660926464
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Government and Agencies, Faculty, Students
- Date: status `ambiguous_multi_year` | dates: 2025-12-29, 2026-01-01 | AY: `2025-26`
- Flags: multi_year | evidence_score: 3 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-29, 2026-01-01) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 📘 AICTE-Sponsored Academic Meet | TCE, Madurai Theme: Preparing Glossary of Engineering in தமிழ் Language 🗓 29 Dec 2025 – 1 Jan 2026 Organised by: Govt. of India – Commission for Scientific & Technical Terminology, Ministry of Education Organising Committee Chief Patron Mr. K. Hari Thiagarajan, Chairman & Correspondent Organizing Secretary Dr. L. Ashok Kumar, Principal Coordinator: Dr. M. Mahendra

### Post #346

- Source: `June 2025-June 2026` row `346` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7408058293182488576
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text, text_is_url | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: https://lnkd.in/g3h959qb

### Post #369

- Source: `June 2025-June 2026` row `369` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7403767539987689472
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Electrical and Electronics Engineering
- Stakeholders: Industry, Faculty, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: 🌞 Congratulations! 🌞 Thiagarajar College of Engineering, Madurai, congratulates the project team for receiving sanction to carry out the project titled “Real-Time Solar Energy Forecasting Using Hybrid Deep Learning for Smart Grid Energy Trading Applications – SolartradeX.” This sanctioned project aims to advance renewable energy efficiency and smart grid energy trading through AI-powered forecasti

### Post #370

- Source: `June 2025-June 2026` row `370` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7403767089481580545
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Chemistry
- Stakeholders: Industry, Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: ✨ Congratulations ✨ TCE proudly congratulates the project team for the sanction of the project titled Digicell in Sight: A Data-Driven Framework for Comparative Analysis, Predictive Modeling, and Life cycle Health estimation of Multi-Chemistry, Multi-Brand Li-Ion Cells 🔋 Congratulations! 🔋 Thiagarajar College of Engineering, Madurai, proudly congratulates the project team for developing a data-dri

### Post #371

- Source: `June 2025-June 2026` row `371` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7403766626149720071
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Electrical and Electronics Engineering
- Stakeholders: Industry, Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: 🎉 Congratulations! 🎉 Thiagarajar College of Engineering, Madurai, proudly congratulates the project team on the sanctioned project titled “Indigenous Intelligent Battery Management System for Enhanced EV Battery Subsystems and Accurate SOC Estimation.” The project aims to advance EV battery technologies, improve SOC estimation accuracy, and foster indigenous hardware development for high-voltage a

### Post #396

- Source: `June 2025-June 2026` row `396` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7399838812782243840
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2025-11-28 | AY: `2025-26`
- Flags: - | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 🎓 Kanitamil Forum Inauguration & 7th Lecture Series @ TCE 📅 28 Nov 2025 | 🕛 12:00 PM 📍 K.K. Auditorium, TCE ✨ Chief Guest: Dr. Palanivel Thiaga Rajan , Hon’ble Minister for IT & Digital Services, TN 🎙️ Speaker: Mr. Neechalkaran Rajaraman , Developer of Vaani Spell Checker 💡 Topic: Large Language Models in Tamil – Opportunities & Challenges 🤝 Organized by TCE in collaboration with Tamil Virtual Aca

### Post #397

- Source: `June 2025-June 2026` row `397` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7399837940786393088
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Information Technology
- Stakeholders: Students
- Date: status `dated` | dates: 2025-11-28 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: Thiagarajar College of Engineering, Madurai in collaboration with Tamil Virtual Academy (TVA) cordially invites you to the Inauguration of the Kanitamil Forum and the 7th Kanitamil Lecture Series 📅 Date: 28 November 2025 | 🕛 Time: 12:00 PM 📍 Venue: K.K. Auditorium, TCE 🌟 Chief Guest: Dr. Palanivel Thiagarajan Hon’ble Minister for Information Technology and Digital Services, Tamil Nadu 🎓 Presided b

### Post #409

- Source: `June 2025-June 2026` row `409` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7398992042741334016
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Information Technology
- Stakeholders: Students
- Date: status `dated` | dates: 2025-11-30 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🎯 Skill Development Training Programme “Livelihood through Computers: Crafting Income from Home” Organized by the Centre for Continuing Education & Department of Information Technology, Thiagarajar College of Engineering, Madurai 🏛️ 💻 For Home Makers & Student Job Seekers ✨ Topics include: Creative Graphic Design using Canva 🎨 Website & UI Design 🌐 IoT for Education 📲 Video Creation & Editing 🎥 On

### Post #416

- Source: `June 2025-June 2026` row `416` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7396580054115311616
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `dated` | dates: 2025-11-28 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🚍 TCE hosts Deloitte–IIT Madras Training Program E-Bus Operational Planning and Advanced Technology Integration TCE, Madurai, is hosting Batch IV of the Training & Capacity Building Program for TNSTC Madurai & Tirunelveli officials, supported by the Transport Dept., Govt. of TN. 📅 19–28 Nov 2025 📍 TCE Campus Modules include: ✔ E-Bus & E-Mobility ✔ ICT & Telematics ✔ AFC Systems ✔ Depot Mgmt & ERP 

### Post #427

- Source: `June 2025-June 2026` row `427` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394582933698801664
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: -
- Stakeholders: Faculty, Industry, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 3 | multi_label: 0
- Proposals: none
- Text: 🎥 Call for Creative Videographers and Editors! Thiagarajar College of Engineering, Madurai, is inviting professional videographers with strong editing skills to collaborate with our official branding team. We’re looking for visual storytellers who can capture TCE’s spirit — academic excellence, vibrant campus life, and student innovation — through impactful cinematography. 📌 Scope: Event reels | C

### Post #429

- Source: `June 2025-June 2026` row `429` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394580873519673344
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Electrical and Electronics Engineering
- Stakeholders: Industry
- Date: status `dated` | dates: 2025-11-14 | AY: `2025-26`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🎉 Inauguration Invitation Thiagarajar College of Engineering, Madurai cordially invites you to the inauguration of the Fuji Electric Centre of Excellence – Innovation Hub for Automation and Drives 🗓️ November 14, 2025 (Friday) 🕤 09:30 AM – 10:30 AM 📍 Department of EEE, First Floor Chief Guest: Mr. Palanisamy Lakshmanan Chief Business Officer, Fuji Electric India Pvt. Ltd. Guests of Honour: Mr. Lou

### Post #431

- Source: `June 2025-June 2026` row `431` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7394327759264804864
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: insufficient_evidence)
- Categories: -
- Departments: Information Technology
- Stakeholders: Faculty
- Date: status `undated` | dates: none | AY: `undated`
- Flags: - | evidence_score: 2 | multi_label: 0
- Proposals: none
- Text: 🚀 Faculty Bootcamp on Drone Technology The Department of Information Technology, Thiagarajar College of Engineering, Madurai, in collaboration with Marlion Technologies, proudly presents a Faculty Bootcamp on Drone Technology under the spirit of innovation and continuous learning. 📅 Nov 12 & 14, 2025 🕓 4:00 PM – 6:00 PM 📍 TCE Main Grounds #TCE #DroneTechnology #FacultyBootcamp #TCEIT #MarlionTechn

### Post #482

- Source: `June 2025-June 2026` row `482` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7381652737727488001
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text, text_is_url | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: https://lnkd.in/gyZPtbgY

### Post #483

- Source: `June 2025-June 2026` row `483` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7381652462161715200
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text, text_is_url | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: https://lnkd.in/g9SAGv3C

### Post #744

- Source: `Jan - Sep 2025` row `245` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7332699196585582592
- Decision: **REVIEW_REQUIRED** / undecided (kind `J`, reason: url_only_no_text)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: url_only, weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 

### Post #773

- Source: `Jan - Sep 2025` row `274` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7326210061456855040
- Decision: **REVIEW_REQUIRED** / undecided (kind `J`, reason: url_only_no_text)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: url_only, weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 

### Post #789

- Source: `Jan - Sep 2025` row `290` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7324051804013367298
- Decision: **REVIEW_REQUIRED** / activity (kind `B`, reason: weak_text_requires_review)
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Government and Agencies, Students
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: AICTE QIP PG CERTIFICATION PROGRAMME in Emerging Areas 2025-26

### Post #802

- Source: `Jan - Sep 2025` row `303` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7322470919707250688
- Decision: **REVIEW_REQUIRED** / undecided (kind `J`, reason: url_only_no_text)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: url_only, weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 

### Post #818

- Source: `Jan - Sep 2025` row `319` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7318836255415324673
- Decision: **REVIEW_REQUIRED** / undecided (kind `J`, reason: url_only_no_text)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: url_only, weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 

### Post #821

- Source: `Jan - Sep 2025` row `322` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7317956622557802496
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: Celebrating Excellence | 67th College Day at TCE

### Post #822

- Source: `Jan - Sep 2025` row `323` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7317955422483542016
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: Sangamithra’25 – An Evening of Joy and Inspiration@ TCE Ladies Hostel

### Post #830

- Source: `Jan - Sep 2025` row `331` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7316300175247908864
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: Beats & Treats at TCE Men's Hostel! 🎶🍽️ An evening to remember with music, food & fun!

### Post #860

- Source: `Jan - Sep 2025` row `361` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7311994754207006720
- Decision: **REVIEW_REQUIRED** / activity (kind `D`, reason: weak_text_requires_review)
- Categories: ORIENTATION
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: Graduation Ceremony

### Post #862

- Source: `Jan - Sep 2025` row `363` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7311356524742774784
- Decision: **REVIEW_REQUIRED** / undecided (kind `J`, reason: url_only_no_text)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: url_only, weak_text | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: 

### Post #884

- Source: `Jan - Sep 2025` row `385` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7308770008002613249
- Decision: **REVIEW_REQUIRED** / activity (kind `A`, reason: weak_text_requires_review)
- Categories: CULTURAL
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: weak_text | evidence_score: 5 | multi_label: 0
- Proposals: none
- Text: Cultura Nova'25

### Post #931

- Source: `Jan - Sep 2025` row `432` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7300537077853564929
- Decision: **REVIEW_REQUIRED** / activity (kind `A`, reason: weak_text_requires_review)
- Categories: SPORTS
- Departments: -
- Stakeholders: -
- Date: status `dated` | dates: 2025-02-15 | AY: `2024-25`
- Flags: weak_text | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: TCE MINI MARATHON FEBRUARY 15, 2025

### Post #1028

- Source: `April 2024 - June 2025` row `16` | URL: none (link-less)
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: link_less, weak_text, text_is_url | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: https://www.facebook.com/100064550328054/posts/828180799343590/?mibextid=AQBXeECoIFSgMqhe

### Post #1090

- Source: `April 2024 - June 2025` row `78` | URL: none (link-less)
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: link_less, weak_text, text_is_url | evidence_score: 0 | multi_label: 0
- Proposals: none
- Text: https://www.lotustimes.org/.../how-to-bring-artificial.../

### Post #1091

- Source: `April 2024 - June 2025` row `79` | URL: none (link-less)
- Decision: **REVIEW_REQUIRED** / undecided (kind `I`, reason: weak_text_requires_review)
- Categories: -
- Departments: Electronics and Communication Engineering
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: link_less, weak_text, text_is_url | evidence_score: 1 | multi_label: 0
- Proposals: none
- Text: https://www.thehindu.com/.../artifici.../article68461116.ece

### Post #1424

- Source: `April 2024 - June 2025` row `432` | URL: none (link-less)
- Decision: **REVIEW_REQUIRED** / activity (kind `A`, reason: weak_text_requires_review)
- Categories: SPORTS
- Departments: -
- Stakeholders: -
- Date: status `undated` | dates: none | AY: `undated`
- Flags: link_less, weak_text | evidence_score: 4 | multi_label: 0
- Proposals: none
- Text: TCE - 61st ANNUAL SPORTS MEET

## Group H - Activity - date / academic-year issue (7 posts)

> ACTIVITY_CANDIDATE with a date/academic-year issue: multi-year ambiguity, pre-2024 evidence, or academic-year mismatch. Keep ambiguous/undated as flagged; never invent a date.

### Post #392

- Source: `June 2025-June 2026` row `392` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7400145510982041600
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `B`, reason: activity_evidence:ACHIEVEMENT)
- Categories: ACHIEVEMENT
- Departments: -
- Stakeholders: Community and Society, Students
- Date: status `ambiguous_multi_year` | dates: 2025-12-27, 2026-01-21 | AY: `2025-26`
- Flags: multi_year | evidence_score: 9 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-27, 2026-01-21) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🤖 TCE AI Consortium presents AI OLYMPIAD 2025–26: Unleash Your Future Genius! For School Students (Grades 6–12) 🗓️ Round 1 (Online): Dec 27, 2025 🏆 Final Round (Offline): Jan 21, 2026 💰 Fee: ₹300 | Rewards: Trophy + Certificates 📘 Scan to Register | Access Rulebook & Syllabus 📞 Queries: Dr. K. V. Uma – 93617 31131 Mrs. A. Indirani – 99949 85459 #TCE #AIOlympiad #AIConsortium #TCEMadurai #FutureGen

### Post #393

- Source: `June 2025-June 2026` row `393` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7400144446048256000
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: -
- Stakeholders: Faculty, Industry, Students
- Date: status `ambiguous_multi_year` | dates: 2025-11-30, 2026-01-05, 2026-01-09 | AY: `2025-26`
- Flags: multi_year | evidence_score: 25 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-11-30, 2026-01-05, 2026-01-09) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🎓 2nd National Research Conclave @ TCE, Madurai 📅 March 26–27, 2026 🔍 Theme: Digital Transformation & Sustainable Innovation in Engineering and Science 💡 Theme Areas: Quantum Information Science | Digital Twin Technology | Computational Sustainability | Industry 5.0 | Smart Vehicles | Cyber-Physical Systems | Blockchain | AI for Renewable Energy | VR/AR | Digital Transformation in STEM 🗓️ Importan

### Post #395

- Source: `June 2025-June 2026` row `395` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7400142786039070720
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:HACKATHON)
- Categories: HACKATHON
- Departments: -
- Stakeholders: Industry
- Date: status `ambiguous_multi_year` | dates: 2025-12-27, 2026-01-21 | AY: `2025-26`
- Flags: multi_year | evidence_score: 6 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-27, 2026-01-21) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 💡 TCE AI Consortium Hackathon Challenge 2025 🗓️ Dec 27, 2025 – Jan 21, 2026 ⚙️ Hybrid Mode | Registration Fee: ₹500/- 💥 Show Your Skills, Win Cool Prizes! 🚀 Problem statements by industry experts 👉 tinyurl.com/3ty592uw 📞 For Queries: Dr. K.V. Uma – 93617 31131 Mrs. A. Indirani – 99949 85459 🔗 Register now! #TCEAIConsortium #TCEHackathon2025 #InnovationChallenge #AIforFuture #TechForGood #Hackathon

### Post #414

- Source: `June 2025-June 2026` row `414` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7397186144225906688
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:WORKSHOP)
- Categories: WORKSHOP
- Departments: Information Technology
- Stakeholders: Students, Industry
- Date: status `ambiguous_multi_year` | dates: 2025-12-20, 2026-01-31, 2026-02-28 | AY: `2025-26`
- Flags: multi_year | evidence_score: 6 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-12-20, 2026-01-31, 2026-02-28) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🌥️ Skill Development Training Programme on AWS Cloud Foundations Centre for Continuing Education Centre of Excellence for Amazon Web Services Organized by the Department of Information Technology, TCE 🚀 *Build Your Cloud Career with AWS* Join our 30-hour hands-on training programme designed to equip students with essential AWS Cloud skills and industry-ready knowledge. 🗓 Training Schedule 31 Jan 2

### Post #415

- Source: `June 2025-June 2026` row `415` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7396595849616711680
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:PLACEMENT,CLUB)
- Categories: PLACEMENT, CLUB
- Departments: -
- Stakeholders: Students
- Date: status `ambiguous_multi_year` | dates: 2025-11-19, 2026-01-22, 2026-02-11, 2026-03-04, 2026-03-11 | AY: `2025-26`
- Flags: multi_year | evidence_score: 8 | multi_label: 1
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-11-19, 2026-01-22, 2026-02-11, 2026-03-04, 2026-03-11) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🎓 TCE Math Olympiad 2025–26 TCE MATH Club is launching the Math Olympiad to boost Olympiad-style problem-solving with engineering applications—ideal for GATE, placements & higher studies. 📘 Syllabus (Highlights) I Year: Algebra, Matrices, Vector Calculus, Geometry, Trigonometry, Probability, Aptitude II Year: Calculus, Linear Algebra, ODEs, Aptitude & Reasoning III Year: * Batch 1: Calculus, Linea

### Post #419

- Source: `June 2025-June 2026` row `419` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7396218234196185088
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `D`, reason: activity_evidence:PLACEMENT,CLUB)
- Categories: PLACEMENT, CLUB
- Departments: -
- Stakeholders: Students
- Date: status `ambiguous_multi_year` | dates: 2025-11-19, 2026-01-22, 2026-02-11, 2026-03-04, 2026-03-11 | AY: `2025-26`
- Flags: multi_year | evidence_score: 8 | multi_label: 1
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-11-19, 2026-01-22, 2026-02-11, 2026-03-04, 2026-03-11) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🎓 TCE Math Olympiad 2025–26 TCE MATH Club is launching the Math Olympiad to boost Olympiad-style problem-solving with engineering applications—ideal for GATE, placements & higher studies. 📘 Syllabus (Highlights) I Year: Algebra, Matrices, Vector Calculus, Geometry, Trigonometry, Probability, Aptitude II Year: Calculus, Linear Algebra, ODEs, Aptitude & Reasoning III Year: * Batch 1: Calculus, Linea

### Post #533

- Source: `June 2025-June 2026` row `533` | URL: https://www.linkedin.com/feed/update/urn:li:activity:7373396553648041984
- Decision: **ACTIVITY_CANDIDATE** / activity (kind `C`, reason: activity_evidence:RESEARCH)
- Categories: RESEARCH
- Departments: -
- Stakeholders: Students, Faculty, Industry
- Date: status `ambiguous_multi_year` | dates: 2025-10-14, 2025-11-30, 2026-01-09 | AY: `2025-26`
- Flags: multi_year | evidence_score: 20 | multi_label: 0
- Proposals:
  - `note` date · rule=`multi_year_keep` · confidence=high · current: ambiguous_multi_year (2025-10-14, 2025-11-30, 2026-01-09) → proposed: keep ambiguous_multi_year; do NOT collapse to one AY
    - rationale: the post carries explicit dates in more than one academic year; the ambiguity must stay flagged.
- Text: 🎓 TCE organizes 2nd National Level Research Conclave on Digital Transformation and Sustainable Innovation in Engineering and Science 🗓️ March 26 – 27, 2026 📍 Thiagarajar College of Engineering, Madurai 🔹 Theme Highlights: Quantum Science | Digital Twin | Computational Sustainability | Industry 5.0 | Climate Resilience | Smart Vehicles | Cyber-Physical Systems | Renewable Energy & AI | Blockchain |

## Integrity notes

- The 200 sampled posts are READ from linkedin_activity_candidates; their candidate_status, categories and review_status are unchanged.
- Proposed corrections/review decisions live ONLY in `linkedin_manual_review_proposals` (staging DB) and this report.
- Canonical posts remain 1,544; raw occurrences remain 2,094; the production database (2,258 website activities) and merged-workbook.xlsx were not touched.
- No accuracy claim: the human labels from this report are needed before any evaluation statement.
