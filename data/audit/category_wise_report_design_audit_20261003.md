# Category-Wise Report Design Audit
## TCE LinkedIn Reportable Dataset
**Audit Date:** 2026-10-03  |  **Data source:** `backend/database/linkedin_reportable.db` (read-only)  |  **Total records:** 1,747

---

## 1. DATASET OVERVIEW

| Metric | Count | % |
|--------|------:|--:|
| Total reportable activities | **1,747** | 100% |
| General activities | **958** | 54.8% |
| Departmental activities | **789** | 45.2% |
| Activities with a usable date | **845** | 48.4% |
| Activities without a date | **902** | 51.6% |
| Activities with Post URL | **1,012** | 57.9% |
| Activities without Post URL | **735** | 42.1% |

> **CRITICAL:** Only **15 of 1,747 records are APPROVED** (0.86%). The vast majority are UNREVIEWED.
> A clear approval policy must be established before public reports are finalised.

### Review Status

| Status | Count |
|--------|------:|
| UNREVIEWED | 1,495 |
| NEEDS_REVIEW | 237 |
| APPROVED | 15 |

### Academic Year Distribution

| Year | Activities |
|------|----------:|
| 2022-23 | 3 |
| 2023-24 | 11 |
| 2024-25 | 803 |
| 2025-26 | 725 |
| 2026-27 | 204 |
| 2027-28 | 1 |

### Top Departments by Activity Count

| Department | Departmental Activities |
|-----------|------------------------:|
| Electronics and Communication Engineering | 155 |
| Electrical and Electronics Engineering | 121 |
| Computer Science and Engineering | 113 |
| Mechanical Engineering | 107 |
| Civil Engineering | 88 |
| Mechatronics | 61 |
| T'SEDA (Architecture, Design, Planning) | 58 |
| Applied Mathematics and Computational Science | 52 |
| Computer Science and Business Systems | 52 |
| Information Technology | 46 |
| Mathematics | 37 |
| Physics | 31 |
| Artificial Intelligence | 26 |
| Chemistry | 25 |
| English | 15 |
| Computer Applications | 12 |

---

## 2. CATEGORY COUNTS AND VERDICTS

| Category | Total | General | Dept | Date% | Stk% | URL% | Verdict |
|----------|------:|--------:|-----:|------:|-----:|-----:|---------|
| WORKSHOP | 178 | 49 | 129 | 56% | 95% | 62% | ✅ (HIGH) |
| SEMINAR | 89 | 10 | 79 | 64% | 96% | 56% | ✅ (HIGH) |
| CONFERENCE | 61 | 31 | 30 | 64% | 79% | 75% | ✅ (HIGH) |
| SYMPOSIUM | 10 | 1 | 9 | 40% | 70% | 70% | ⚠️ MERGE → CONFERENCE |
| GUEST_LECTURE | 86 | 17 | 69 | 69% | 98% | 56% | ✅ (HIGH) |
| FDP | 63 | 11 | 52 | 62% | 100% | 52% | ✅ (HIGH) |
| STTP | 3 | 1 | 2 | 100% | 100% | 67% | ⚠️ MERGE → FDP |
| HACKATHON | 32 | 15 | 17 | 34% | 94% | 59% | ✅ (MEDIUM) |
| TECH_FEST | 2 | 1 | 1 | 0% | 100% | 50% | ❌ |
| CULTURAL | 30 | 20 | 10 | 50% | 83% | 63% | ✅ (LOW) |
| SPORTS | 56 | 49 | 7 | 45% | 77% | 54% | ✅ (MEDIUM) |
| NCC | 7 | 7 | 0 | 43% | 43% | 43% | ✅ (LOW) |
| NSS | 8 | 7 | 1 | 62% | 100% | 38% | ✅ (LOW) |
| CLUB | 87 | 46 | 41 | 54% | 90% | 60% | ✅ (MEDIUM) |
| OUTREACH | 46 | 23 | 23 | 59% | 96% | 48% | ✅ (MEDIUM) |
| INDUSTRY | 88 | 62 | 26 | 44% | 98% | 56% | ✅ (HIGH) |
| ACHIEVEMENT | 149 | 46 | 103 | 20% | 97% | 54% | ✅ (HIGH) |
| PLACEMENT | 21 | 7 | 14 | 48% | 95% | 48% | ✅ (LOW) |
| INTERNSHIP | 41 | 9 | 32 | 27% | 93% | 63% | ✅ (MEDIUM) |
| RESEARCH | 84 | 28 | 56 | 37% | 86% | 64% | ✅ (HIGH) |
| ALUMNI | 66 | 43 | 23 | 50% | 100% | 65% | ✅ (MEDIUM) |
| ORIENTATION | 42 | 17 | 25 | 83% | 90% | 50% | ✅ (MEDIUM) |
| CAMPUS | 69 | 54 | 15 | 65% | 86% | 54% | ✅ (MEDIUM) |
| WEBINAR | 34 | 9 | 25 | 79% | 94% | 59% | ✅ (MEDIUM) |

---

## 3. DETAILED CATEGORY ANALYSIS

### WORKSHOP

| Metric | Value |
|--------|------:|
| Total | 178 |
| General | 49 |
| Departmental | 129 |
| Date coverage | 56%  |
| Stakeholder coverage | 95% |
| URL coverage | 62% |
| Avg description length | 881 chars |
| Approved | 2 |
| Unreviewed | 166 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Parents, Students

**Departments (16):** Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Civil Engineering, Computer Applications *(+11 more)*

**Sample titles:**
- 🎓 I-RISE OTP | Operator Training Program Thiagarajar College of Engineering, Madurai, hosts the I-RISE Operator Training…
- 🚀 HCL Tech Bee Training Program Begins!
- 📡✨ Joy of Learning: Signal Processing!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### SEMINAR

| Metric | Value |
|--------|------:|
| Total | 89 |
| General | 10 |
| Departmental | 79 |
| Date coverage | 64%  |
| Stakeholder coverage | 96% |
| URL coverage | 56% |
| Avg description length | 639 chars |
| Approved | 0 |
| Unreviewed | 86 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (15):** Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Civil Engineering, Computer Applications *(+10 more)*

**Sample titles:**
- 🎓✨ Student-Centered Learning: Empowering Better Education!
- ⚡🔬 Advancing Research in Power Quality!
- 🎓🚀 Career Roadmap for Future Success!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### CONFERENCE

| Metric | Value |
|--------|------:|
| Total | 61 |
| General | 31 |
| Departmental | 30 |
| Date coverage | 64%  |
| Stakeholder coverage | 79% |
| URL coverage | 75% |
| Avg description length | 923 chars |
| Approved | 1 |
| Unreviewed | 54 |

**Stakeholders:** Faculty, Government and Agencies, Industry, Students

**Departments (15):** Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Civil Engineering, Computer Applications *(+10 more)*

**Sample titles:**
- 🏗️🌍 **International Conference on AI in Construction & Sustainable Built Environment – ICAIC 2026** The **Department of…
- 🚀✨ Something extraordinary is coming to TCE!
- 🎤✨ TEDx TCE Registrations Open!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### SYMPOSIUM

| Metric | Value |
|--------|------:|
| Total | 10 |
| General | 1 |
| Departmental | 9 |
| Date coverage | 40%  |
| Stakeholder coverage | 70% |
| URL coverage | 70% |
| Avg description length | 962 chars |
| Approved | 0 |
| Unreviewed | 4 |

**Stakeholders:** Community and Society, Faculty, Industry, Students

**Departments (4):** Computer Science and Business Systems, Electronics and Communication Engineering, Mechanical Engineering, Mechatronics

**Sample titles:**
- 🚀 SYNERGICZ 3.0 – National Level Technical Symposium Department of Mechatronics Engineering 📅 April 2, 2026 💰 Prize Pool…
- 🚀 *MOBIUS 2K26 – TECHUTSAV* The *Mechanical Engineering Association* of *Thiagarajar College of Engineering* proudly pre…
- 🚀 ZENYTH 2026 – Where Ideas Rise to the Peak!

**Verdict:** ⚠️ MERGE **MERGE**
  - Merge into: **CONFERENCE**
  - Reason: Only 10 records; semantically identical to departmental technical conferences; already excluded from public taxonomy.

**Data quality flags:**
  - ⚠️ 40% date coverage
  - ⚠️ Only 10 records

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

> Merge into CONFERENCE for public reporting.

---

### GUEST_LECTURE

| Metric | Value |
|--------|------:|
| Total | 86 |
| General | 17 |
| Departmental | 69 |
| Date coverage | 69%  |
| Stakeholder coverage | 98% |
| URL coverage | 56% |
| Avg description length | 639 chars |
| Approved | 0 |
| Unreviewed | 80 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (14):** Applied Mathematics and Computational Science, Artificial Intelligence, Civil Engineering, Computer Applications, Computer Science and Business Systems *(+9 more)*

**Sample titles:**
- 🏠✨ Exploring Residential Building Services!
- 🇮🇳✨ Shaping India into a Product Nation!
- 🌿🏛️ Guest Lecture: Site Planning Process T’SEDA, Thiagarajar School of Environmental Design and Architecture, invites yo…

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### FDP

| Metric | Value |
|--------|------:|
| Total | 63 |
| General | 11 |
| Departmental | 52 |
| Date coverage | 62%  |
| Stakeholder coverage | 100% |
| URL coverage | 52% |
| Avg description length | 926 chars |
| Approved | 2 |
| Unreviewed | 58 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Parents, Students

**Departments (14):** Applied Mathematics and Computational Science, Chemistry, Civil Engineering, Computer Science and Business Systems, Computer Science and Engineering *(+9 more)*

**Sample titles:**
- 🌱⚡ Advancing Sustainable Energy & Environmental Stewardship!
- 🤖📚 AI-Powered Pedagogy | Faculty Development Programme 2026 🎓✨ Thiagarajar College of Engineering, under the Centre for…
- 🤖⚙️ Empower Engineering with AI & Digital Twins!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### STTP

| Metric | Value |
|--------|------:|
| Total | 3 |
| General | 1 |
| Departmental | 2 |
| Date coverage | 100%  |
| Stakeholder coverage | 100% |
| URL coverage | 67% |
| Avg description length | 1149 chars |
| Approved | 0 |
| Unreviewed | 1 |

**Stakeholders:** Alumni, Community and Society, Faculty, Industry, Students

**Departments (2):** Computer Science and Business Systems, Information Technology

**Sample titles:**
- 🚀📚 Master Computational Linguistics for the LLM Era!
- 🚀 One Week Online STTP on “Art of Coding Using AI Tools” (Inclusive of 3 hours contests ) The Department of Information…
- 🎯 5-Day Online Short Term Training Program (STTP) on “ Next Generation Tools and Techniques ” 📅 24 – 28 November 2025 🕒…

**Verdict:** ⚠️ MERGE **MERGE**
  - Merge into: **FDP**
  - Reason: Only 3 records; functionally a subtype of FDP; already excluded from public taxonomy.

**Data quality flags:**
  - ⚠️ Only 3 records — near-empty category

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

> Merge into FDP for public reporting.

---

### HACKATHON

| Metric | Value |
|--------|------:|
| Total | 32 |
| General | 15 |
| Departmental | 17 |
| Date coverage | 34% ⚠️ |
| Stakeholder coverage | 94% |
| URL coverage | 59% |
| Avg description length | 810 chars |
| Approved | 0 |
| Unreviewed | 27 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (9):** Applied Mathematics and Computational Science, Civil Engineering, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering *(+4 more)*

**Sample titles:**
- 🚀💡 SIH 2026: Innovate.
- 🚀 Industry Innovation Hackathon 2026 Thiagarajar College of Engineering, in association with the Institution's Innovatio…
- 🚀 *HACKRAX’26 – Industry Innovation Challenge* The Department of Computer Science and Engineering, Thiagarajar College o…

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**

**Data quality flags:**
  - ⚠️ 34% date coverage

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### TECH_FEST

| Metric | Value |
|--------|------:|
| Total | 2 |
| General | 1 |
| Departmental | 1 |
| Date coverage | 0% ⚠️ |
| Stakeholder coverage | 100% |
| URL coverage | 50% |
| Avg description length | 998 chars |
| Approved | 0 |
| Unreviewed | 1 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Students

**Departments (1):** Computer Science and Engineering

**Sample titles:**
- AICTE is organizing its first-ever Tech Fest – AICTE IDEA Lab Tech Fest 2025!
- 🎉 FS'tival '24 – Annual Free Software Festival 🎉 Hosted by the Department of Computer Science and Engineering, TCE Where…

**Verdict:** ❌ **REMOVE**
  - Reason: Only 2 records; 0% date coverage; already excluded from public taxonomy.

**Data quality flags:**
  - ⚠️ 0% date coverage
  - ⚠️ Only 2 records — effectively empty

> Remove from public reporting. 2 records, 0% date coverage.

---

### CULTURAL

| Metric | Value |
|--------|------:|
| Total | 30 |
| General | 20 |
| Departmental | 10 |
| Date coverage | 50%  |
| Stakeholder coverage | 83% |
| URL coverage | 63% |
| Avg description length | 563 chars |
| Approved | 0 |
| Unreviewed | 26 |

**Stakeholders:** Alumni, Community and Society, Faculty, Industry, Non-Teaching Staff, Students

**Departments (6):** Civil Engineering, Computer Science and Engineering, Electrical and Electronics Engineering, English, Mechanical Engineering *(+1 more)*

**Sample titles:**
- 🎉✨ TEACHERS’ DAY CELEBRATION 2026 ✨🎉 Celebrating the guiding lights of knowledge!
- 🎉 CULTURA NOVA ’26 – Connections Organised by TCE–Shrishti Cultural Association Inviting Faculty, Non-Teaching Staff & R…
- 🎬 Cinema Quiz @ TCE – Cultura Nova 2026 Organised by the TCE–Shrishti Cultural Association, this exciting Cinema Quiz in…

**Verdict:** ✅ **KEEP**
  - Priority: **LOW**
  - Note: Some non-reportable content (congratulatory posts) mixed in.

**Data quality flags:**
  - ⚠️ Non-reportable congratulatory posts mixed in

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Date` | `Academic Year` | `Post URL`

---

### SPORTS

| Metric | Value |
|--------|------:|
| Total | 56 |
| General | 49 |
| Departmental | 7 |
| Date coverage | 45%  |
| Stakeholder coverage | 77% |
| URL coverage | 54% |
| Avg description length | 713 chars |
| Approved | 0 |
| Unreviewed | 52 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Non-Teaching Staff, Students

**Departments (5):** Civil Engineering, Computer Science and Engineering, Electronics and Communication Engineering, Information Technology, Mathematics

**Sample titles:**
- 🏆⚽ SPORTS INAUGURATION 2026!
- 🏆🥇 Champions!
- 🏸🏆 CONGRATULATIONS TO OUR FACULTY CHAMPIONS!🏆🏸 A proud sporting achievement for Thiagarajar College of Engineering!

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**

**Data quality flags:**
  - ⚠️ 45% date coverage
  - ⚠️ Near-duplicate titles detected in sample

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Date` | `Academic Year` | `Post URL`

---

### NCC

| Metric | Value |
|--------|------:|
| Total | 7 |
| General | 7 |
| Departmental | 0 |
| Date coverage | 43%  |
| Stakeholder coverage | 43% |
| URL coverage | 43% |
| Avg description length | 644 chars |
| Approved | 0 |
| Unreviewed | 3 |

**Stakeholders:** Students

**Sample titles:**
- 4 (TN) ENGR COY NCC Thiagarajar College of Engineering Cordially invites you to celebrate The 77ᵗʰ Republic Day of India…
- 79th Independence Day Celebration @ TCE Thiagarajar College of Engineering, Madurai, cordially invites you to join us in…
- TCE | Thiagarajar College of Engineering | Madurai The 4 TN Engr COY NCC, TCE is organizing a Tree Plantation Drive at t…

**Verdict:** ✅ **KEEP**
  - Priority: **LOW**
  - Note: Only 7 records; weak coverage metrics; NAAC-required.

**Data quality flags:**
  - ⚠️ 43% stakeholder coverage — lowest of all categories
  - ⚠️ Only 7 records

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

---

### NSS

| Metric | Value |
|--------|------:|
| Total | 8 |
| General | 7 |
| Departmental | 1 |
| Date coverage | 62%  |
| Stakeholder coverage | 100% |
| URL coverage | 38% |
| Avg description length | 673 chars |
| Approved | 0 |
| Unreviewed | 6 |

**Stakeholders:** Community and Society, Faculty, Government and Agencies, Students

**Departments (1):** Electrical and Electronics Engineering

**Sample titles:**
- 🩸❤️ GIVE BLOOD.
- 📘 TCE NSS Newsletter – Volume 1 (2026) Released!
- 🎉 Congratulations to TCE NSS & YRC Units!

**Verdict:** ✅ **KEEP**
  - Priority: **LOW**
  - Note: Only 8 records; NAAC-required.

**Data quality flags:**
  - ⚠️ 38% URL coverage
  - ⚠️ Only 8 records

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Date` | `Academic Year` | `Post URL`

---

### CLUB

| Metric | Value |
|--------|------:|
| Total | 87 |
| General | 46 |
| Departmental | 41 |
| Date coverage | 54%  |
| Stakeholder coverage | 90% |
| URL coverage | 60% |
| Avg description length | 651 chars |
| Approved | 1 |
| Unreviewed | 81 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (11):** Artificial Intelligence, Chemistry, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering *(+6 more)*

**Sample titles:**
- 🧮✨ MATH CLUB INAUGURAL CEREMONY!
- 🎉✨ Inaugural Ceremony 2026!
- 🎓⚙️ Mechanical Engineering Association Inauguration!

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### OUTREACH

| Metric | Value |
|--------|------:|
| Total | 46 |
| General | 23 |
| Departmental | 23 |
| Date coverage | 59%  |
| Stakeholder coverage | 96% |
| URL coverage | 48% |
| Avg description length | 664 chars |
| Approved | 0 |
| Unreviewed | 42 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (7):** Artificial Intelligence, Civil Engineering, Computer Science and Engineering, Electronics and Communication Engineering, Information Technology *(+2 more)*

**Sample titles:**
- 🏗️✨ LEAN CONSTRUCTION | AWARENESS SESSION!
- 🎓🚀 GATE–JAM 2027 Outreach Programme!
- 🛡️🔐 Cyber Security Awareness!

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### INDUSTRY

| Metric | Value |
|--------|------:|
| Total | 88 |
| General | 62 |
| Departmental | 26 |
| Date coverage | 44%  |
| Stakeholder coverage | 98% |
| URL coverage | 56% |
| Avg description length | 794 chars |
| Approved | 1 |
| Unreviewed | 84 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (10):** Civil Engineering, Computer Science and Business Systems, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering *(+5 more)*

**Sample titles:**
- 🤝🚀 MoU SIGNED | BUILD • INCUBATE • IMPACT TCE, ITEL & TCE TBI signed an MoU to strengthen Build Club and co-incubation i…
- 🚀🧠 Poster Presentation Contest!
- 🧘‍♀️🌿 TCE YOGA CELEBRATION 2026 – Relax • Refresh • Rejuvenate!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**

**Data quality flags:**
  - ⚠️ Some records are institutional announcements rather than discrete activities

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### ACHIEVEMENT

| Metric | Value |
|--------|------:|
| Total | 149 |
| General | 46 |
| Departmental | 103 |
| Date coverage | 20% ⚠️ |
| Stakeholder coverage | 97% |
| URL coverage | 54% |
| Avg description length | 767 chars |
| Approved | 2 |
| Unreviewed | 136 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (15):** Applied Mathematics and Computational Science, Artificial Intelligence, Chemistry, Civil Engineering, Computer Science and Business Systems *(+10 more)*

**Sample titles:**
- Career Pathways in AI Product Management: From Technology to Business Impact!
- 🏆✨ **HEARTIEST CONGRATULATIONS!** 🇮🇳🚀 Thiagarajar College of Engineering proudly congratulates **Dr.
- 🏆✨ PROUD MOMENT FOR TCE IEEE STUDENT BRANCH ✨🏆 TCE IEEE Student Branch has been recognized as a *Winner* at the *IEEE Ma…

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**
  - Note: Only category where Name + Achievement Description are appropriate columns. 20% date coverage is a concern.

**Data quality flags:**
  - ⚠️ 20% date coverage — worst of any major category

**Recommended columns — General:** `S.No` | `Stakeholder` | `Name` | `Award Title` | `Achievement Description` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Stakeholder` | `Name` | `Department` | `Award Title` | `Achievement Description` | `Academic Year` | `Post URL`

> Only category where Name and Achievement Description columns are appropriate.

---

### PLACEMENT

| Metric | Value |
|--------|------:|
| Total | 21 |
| General | 7 |
| Departmental | 14 |
| Date coverage | 48%  |
| Stakeholder coverage | 95% |
| URL coverage | 48% |
| Avg description length | 752 chars |
| Approved | 0 |
| Unreviewed | 18 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (7):** Applied Mathematics and Computational Science, Computer Science and Business Systems, Computer Science and Engineering, Electronics and Communication Engineering, Mechanical Engineering *(+2 more)*

**Sample titles:**
- 🏆🎉 Congratulations to Dr.
- 🏆🚗 STEP Centre Triumph!
- 📡 Welcome to the World of ECE @ Thiagarajar College of Engineering Step into the exciting world of Electronics & Communi…

**Verdict:** ✅ **KEEP**
  - Priority: **LOW**
  - Note: 21 records; some miscategorisation detected.

**Data quality flags:**
  - ⚠️ Some records appear miscategorised (promotional/course posts)

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### INTERNSHIP

| Metric | Value |
|--------|------:|
| Total | 41 |
| General | 9 |
| Departmental | 32 |
| Date coverage | 27% ⚠️ |
| Stakeholder coverage | 93% |
| URL coverage | 63% |
| Avg description length | 826 chars |
| Approved | 2 |
| Unreviewed | 37 |

**Stakeholders:** Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (11):** Applied Mathematics and Computational Science, Artificial Intelligence, Civil Engineering, Computer Science and Business Systems, Computer Science and Engineering *(+6 more)*

**Sample titles:**
- 🤖🔥 Ready to Build the Future with Robotics?
- 🚀 TCE AI CONSORTIUM presents SUMMER INTERNSHIP 2026 🤖 AI-Powered Predictive Analytics & Decision Support Systems 🎯 Who c…
- 🚀 TCE AI CONSORTIUM presents SUMMER INTERNSHIP 2026 🤖 AI-Powered Predictive Analytics & Decision Support Systems 🎯 Who c…

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**
  - Note: 27% date coverage; possible near-duplicate records.

**Data quality flags:**
  - ⚠️ 27% date coverage
  - ⚠️ Possible near-duplicate records (same programme posted multiple times)

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### RESEARCH

| Metric | Value |
|--------|------:|
| Total | 84 |
| General | 28 |
| Departmental | 56 |
| Date coverage | 37% ⚠️ |
| Stakeholder coverage | 86% |
| URL coverage | 64% |
| Avg description length | 761 chars |
| Approved | 4 |
| Unreviewed | 73 |

**Stakeholders:** Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (13):** Applied Mathematics and Computational Science, Artificial Intelligence, Civil Engineering, Computer Science and Business Systems, Computer Science and Engineering *(+8 more)*

**Sample titles:**
- 📢📝 Call for Papers | Thiagarajar Journal of Engineering, Science, Design & Technology (TJESDT) 🚀📚 Thiagarajar College of…
- 🎉✨ T’CODE Takes Flight!
- 🎉🏆 Utility Patent Granted | Another Milestone for TCE Innovation!

**Verdict:** ✅ **KEEP**
  - Priority: **HIGH**
  - Note: 37% date coverage; possible near-duplicate patent posts.

**Data quality flags:**
  - ⚠️ 37% date coverage
  - ⚠️ Possible near-duplicate patent announcement posts

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### ALUMNI

| Metric | Value |
|--------|------:|
| Total | 66 |
| General | 43 |
| Departmental | 23 |
| Date coverage | 50%  |
| Stakeholder coverage | 100% |
| URL coverage | 65% |
| Avg description length | 644 chars |
| Approved | 0 |
| Unreviewed | 65 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (9):** Applied Mathematics and Computational Science, Civil Engineering, Computer Applications, Computer Science and Business Systems, Computer Science and Engineering *(+4 more)*

**Sample titles:**
- 🇦🇺🤝 Australia–Brisbane Alumni Meet 2026 | Reconnect, Network & Celebrate!
- 🎉💎 Jalabula Gems | Silver Jubilee Reunion 2026 💜🎓 The TCE 1997–2001 Batch warmly invites its beloved teachers to celebra…
- 🎓🌟 Alumni Connect 2026 | Inspiring the Next Generation 🚀 Join Alumni Connect 2026 – 2001 Batch Alumni Interaction Series…

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**
  - Note: Currently excluded from public taxonomy but 66 coherent records. Recommend reconsidering exclusion.

**Data quality flags:**
  - ⚠️ Currently excluded from public taxonomy despite 66 coherent reportable records

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Date` | `Academic Year` | `Post URL`

---

### ORIENTATION

| Metric | Value |
|--------|------:|
| Total | 42 |
| General | 17 |
| Departmental | 25 |
| Date coverage | 83%  |
| Stakeholder coverage | 90% |
| URL coverage | 50% |
| Avg description length | 651 chars |
| Approved | 0 |
| Unreviewed | 37 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Parents, Students

**Departments (11):** Applied Mathematics and Computational Science, Civil Engineering, Computer Applications, Computer Science and Business Systems, Computer Science and Engineering *(+6 more)*

**Sample titles:**
- 🎓✨ A New Beginning for Future Tech Leaders!
- 🚀🎓 MCA First-Year Orientation Program!
- 🎓 Welcoming the Batch of 2031!

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**
  - Note: Best date coverage of any category (83%).

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

### CAMPUS

| Metric | Value |
|--------|------:|
| Total | 69 |
| General | 54 |
| Departmental | 15 |
| Date coverage | 65%  |
| Stakeholder coverage | 86% |
| URL coverage | 54% |
| Avg description length | 686 chars |
| Approved | 0 |
| Unreviewed | 65 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (10):** Artificial Intelligence, Chemistry, Computer Science and Engineering, Electrical and Electronics Engineering, Electronics and Communication Engineering *(+5 more)*

**Sample titles:**
- 🏆✨ Celebrating Excellence at TCE!
- 🌸🎓 Founder’s Day 2026 | Honouring the Vision of Kalaithanthai Karumuttu Thiagarajan Chettiar 🙏✨ Thiagarajar College of E…
- 🏆💡 National Technology Day 2026 | Hackathon Prize Distribution Ceremony 🎉🚀 Thiagarajar College of Engineering cordially…

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**
  - Note: Catch-all category; boundary with CULTURAL/ACHIEVEMENT/OUTREACH is fuzzy.

**Data quality flags:**
  - ⚠️ Fuzzy category boundary with CULTURAL, ACHIEVEMENT, OUTREACH

**Recommended columns — General:** `S.No` | `Title` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Date` | `Academic Year` | `Post URL`

---

### WEBINAR

| Metric | Value |
|--------|------:|
| Total | 34 |
| General | 9 |
| Departmental | 25 |
| Date coverage | 79%  |
| Stakeholder coverage | 94% |
| URL coverage | 59% |
| Avg description length | 704 chars |
| Approved | 0 |
| Unreviewed | 33 |

**Stakeholders:** Alumni, Community and Society, Faculty, Government and Agencies, Industry, Students

**Departments (12):** Applied Mathematics and Computational Science, Chemistry, Civil Engineering, Computer Science and Engineering, Electrical and Electronics Engineering *(+7 more)*

**Sample titles:**
- 🌿🏢 GREEN BUILDING AWARENESS!
- 🏗️✨ From Span to Space!
- 🚀🎓 Roadmap to a Master’s in Space Science & Technology!

**Verdict:** ✅ **KEEP**
  - Priority: **MEDIUM**

**Recommended columns — General:** `S.No` | `Title` | `Date` | `Academic Year` | `Post URL`

**Recommended columns — Departmental:** `S.No` | `Title` | `Department` | `Stakeholder` | `Date` | `Academic Year` | `Post URL`

---

## 4. PROPOSED COLUMN DESIGN (ALL CATEGORIES)

### General Activities

| Category | Recommended Columns |
|----------|---------------------|
| WORKSHOP | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| SEMINAR | S.No \| Title \| Date \| Academic Year \| Post URL |
| CONFERENCE | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| SYMPOSIUM | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| GUEST_LECTURE | S.No \| Title \| Date \| Academic Year \| Post URL |
| FDP | S.No \| Title \| Date \| Academic Year \| Post URL |
| STTP | S.No \| Title \| Date \| Academic Year \| Post URL |
| HACKATHON | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| TECH_FEST | *(excluded from public reports)* |
| CULTURAL | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| SPORTS | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| NCC | S.No \| Title \| Date \| Academic Year \| Post URL |
| NSS | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| CLUB | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| OUTREACH | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| INDUSTRY | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| ACHIEVEMENT | S.No \| Stakeholder \| Name \| Award Title \| Achievement Description \| Academic Year \| Post URL |
| PLACEMENT | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| INTERNSHIP | S.No \| Title \| Date \| Academic Year \| Post URL |
| RESEARCH | S.No \| Title \| Date \| Academic Year \| Post URL |
| ALUMNI | S.No \| Title \| Date \| Academic Year \| Post URL |
| ORIENTATION | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| CAMPUS | S.No \| Title \| Stakeholder \| Date \| Academic Year \| Post URL |
| WEBINAR | S.No \| Title \| Date \| Academic Year \| Post URL |

### Departmental Activities

| Category | Recommended Columns |
|----------|---------------------|
| WORKSHOP | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| SEMINAR | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| CONFERENCE | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| SYMPOSIUM | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| GUEST_LECTURE | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| FDP | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| STTP | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| HACKATHON | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| TECH_FEST | *(none / excluded)* |
| CULTURAL | S.No \| Title \| Department \| Date \| Academic Year \| Post URL |
| SPORTS | S.No \| Title \| Department \| Date \| Academic Year \| Post URL |
| NCC | *(none / excluded)* |
| NSS | S.No \| Title \| Department \| Date \| Academic Year \| Post URL |
| CLUB | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| OUTREACH | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| INDUSTRY | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| ACHIEVEMENT | S.No \| Stakeholder \| Name \| Department \| Award Title \| Achievement Description \| Academic Year \| Post URL |
| PLACEMENT | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| INTERNSHIP | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| RESEARCH | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| ALUMNI | S.No \| Title \| Department \| Date \| Academic Year \| Post URL |
| ORIENTATION | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |
| CAMPUS | S.No \| Title \| Department \| Date \| Academic Year \| Post URL |
| WEBINAR | S.No \| Title \| Department \| Stakeholder \| Date \| Academic Year \| Post URL |

> **KEY RULE:** `ACHIEVEMENT` is the **only** category where `Name` and `Achievement Description` are
> appropriate columns. Every other category uses the activity `Title` as the primary descriptor.

---

## 5. CATEGORIES RECOMMENDED FOR REMOVAL OR MERGING

| Category | Action | Records | Factual Reason |
|----------|--------|--------:|----------------|
| SYMPOSIUM | MERGE → CONFERENCE | 10 | Only 10 records; semantically identical to departmental technical conferences; already excluded from public taxonomy. |
| STTP | MERGE → FDP | 3 | Only 3 records; functionally a subtype of FDP; already excluded from public taxonomy. |
| TECH_FEST | REMOVE | 2 | Only 2 records; 0% date coverage; already excluded from public taxonomy. |

---

## 6. CATEGORIES WITH WEAK DATA

| Category | Total | Key Weakness |
|----------|------:|--------------|
| TECH_FEST | 2 | 2 records; 0% date coverage |
| STTP | 3 | 3 records; near-empty category |
| NCC | 7 | 7 records; 43% date/stakeholder/URL coverage |
| NSS | 8 | 8 records; 38% URL coverage |
| SYMPOSIUM | 10 | 10 records; 40% date coverage |
| ACHIEVEMENT | 149 | 149 records but 20% date coverage — worst of any major category |
| INTERNSHIP | 41 | 41 records; 27% date coverage; possible near-duplicates |
| HACKATHON | 32 | 32 records; 34% date coverage |
| RESEARCH | 84 | 84 records; 37% date coverage; possible duplicate patent posts |
| PLACEMENT | 21 | 21 records; some miscategorisation |

---

## 7. MAJOR DATA QUALITY PROBLEMS

### 7.1 Approval Status — Critical
> Only **15 of 1,747** records are APPROVED (0.86%).
> Any public report gated on approval will be nearly empty.
> A clear policy decision is required: include UNREVIEWED records or not?

### 7.2 Date Coverage — Systemic
> **48.4% of all records lack a usable date.** Per-category worst offenders:
> ACHIEVEMENT 20% · INTERNSHIP 27% · HACKATHON 34% · RESEARCH 37%
> Dates must be added manually via the admin editor for high-value records.

### 7.3 Near-Duplicate Records
> Detected in: SPORTS, INTERNSHIP, RESEARCH
> Examples: same internship programme posted 2x; same patent announced in multiple posts;
> same Sports event title appearing twice in the top-6 sample.

### 7.4 Non-Reportable Content in Categories
> The following categories contain congratulatory posts, invitations, or promotional content
> that is not a discrete reportable activity:
> - CULTURAL: *'Congratulations to our Chairman'*
> - ACHIEVEMENT: *'Hearty Congratulations!'*, *'68th College Day Function (invitation)'*
> - PLACEMENT: *'Welcome to the World of ECE'* (dept promo)
> - INDUSTRY: *'Yoga Celebration'* (misclassified)

### 7.5 ALUMNI Excluded from Public Taxonomy
> ALUMNI has 66 coherent, high-quality records (alumni meets, reunions) but is excluded
> from the public taxonomy as a 'stakeholder grouping'. The records describe concrete
> reportable activities. Recommend reconsidering this exclusion.

---

## 8. FINAL IMPLEMENTATION PLAN (DO NOT IMPLEMENT YET)

> **This is a planning document only. No code, database, or UI changes should be made
> until this plan is reviewed and approved by the institution.**

### Phase 1: Data cleanup
Admin review — APPROVE high-confidence records; delete/reclassify non-reportable posts; add dates for ACHIEVEMENT/INTERNSHIP/RESEARCH; de-duplicate SPORTS/INTERNSHIP/RESEARCH

### Phase 2: Category taxonomy update
Reclassify SYMPOSIUM→CONFERENCE and STTP→FDP (update stored codes); flag TECH_FEST as excluded; reconsider adding ALUMNI to public taxonomy

### Phase 3: Report column redesign
Implement per-category column definitions per Section 4 of audit; ACHIEVEMENT is the only category with Name + Description columns

### Phase 4: Category boundary definition
Clarify CAMPUS vs CULTURAL vs ACHIEVEMENT vs OUTREACH boundaries with admin tagging rules

### Phase 5: Reporting gate policy
Decide whether public reports include UNREVIEWED records or only APPROVED; if APPROVED-only, initiate mass admin review

---

*Audit generated: 2026-10-03*  
*Read-only analysis — no records altered, no schema changed, no application modified.*