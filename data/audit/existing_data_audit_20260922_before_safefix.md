# Existing Data Audit — TCE Activity Intelligence (read-only)

Generated: 2026-09-22T01:09:42

## 1. Overall

- Total activity records: **2320**
- With structured date: **471**
- Missing date: **1849**
- With public category: **2308**
- Missing public category: **12**
- Missing any category (no category rows): **4**
- Missing department field: **10**
- Missing stakeholder field: **10**
- Missing source: **0**
- Weak/empty descriptions (<20 chars): **103**

## 2. Academic-period audit (read-time resolution)

| Period | Activities |
| ------ | ----------:|
| 2021-22 | 167 |
| 2022-23 | 184 |
| 2023-24 | 444 |
| 2024-25 | 364 |
| 2025-26 | 351 |
| Before 2021 | 810 |

- Records presented as `Before 2021` with **no** date and **no** year evidence: `739`
- Stored `academic_year` missing: `833`
- Stored year outside the five public periods: `{}`

## 3. Category audit

### Public category counts (all scopes)

| Code | Public name | Activities |
| ---- | ----------- | ----------:|
| ACHIEVEMENT | Achievement and Awards | 776 |
| RESEARCH | Research and Consultancy | 596 |
| INDUSTRY | Industry Collaboration | 324 |
| SPORTS | Sports | 295 |
| WORKSHOP | Workshops | 97 |
| OUTREACH | Outreach and Extension | 80 |
| CLUB | Clubs and Chapters | 78 |
| NCC | NCC | 70 |
| NSS | NSS | 65 |
| CULTURAL | Cultural | 44 |
| PLACEMENT | Placement | 42 |
| INTERNSHIP | Internship | 33 |
| CAMPUS | Campus | 30 |
| CONFERENCE | Conference | 29 |
| SEMINAR | Seminar | 28 |
| WEBINAR | Webinar | 26 |
| FDP | FDP | 15 |
| HACKATHON | Hackathon | 13 |
| GUEST_LECTURE | Guest Lecture | 9 |
| ORIENTATION | Orientation | 8 |

- Legacy/non-public codes still stored: `{'ALUMNI': 28, 'STTP': 1, 'SYMPOSIUM': 2}`
- General-scope (institution-wide) activities: `813`

### General (institution-wide) category distribution

- Sports: 280
- Industry Collaboration: 155
- Achievement and Awards: 92
- Workshops: 82
- Research and Consultancy: 71
- NCC: 59
- NSS: 54
- Placement: 40
- Cultural: 38
- Outreach and Extension: 36
- Campus: 29
- Alumni: 28
- Clubs and Chapters: 28
- Conference: 27
- Internship: 27
- Webinar: 24
- Seminar: 21
- Hackathon: 13
- FDP: 10
- Orientation: 8
- Guest Lecture: 4
- STTP: 1
- SYMPOSIUM: 1

### General bucket analysis (advisory — why General is so large)

- **no_date_but_some_evidence**: 470
  - #11 `Institution Innovation Council (IIC) signed 29 MoUs with industries an`
  - #12 `Hosted MSME Hackathon 4.0, granting ₹15 lakh for student innovations.`
  - #13 `Centers like TSSCAR and CEEPT offer industrial training, prototyping, `
  - #14 `Regular collaboration with Thoughtworks, Amazon, BHEL, and IIT Bombay `
  - #15 `Achieved 1,595 WoS and 4,432 Scopus-indexed publications with 42 desig`
  - #16 `345 students`
- **institution_wide_markers**: 249
  - #2 `TEDx Thiagarajar College of Engineering`
  - #31 `This milestone reflects the strong academic foundation and industry-or`
  - #33 `Home > Student Welfare > Physical Education > Activities Activities 20`
  - #35 `Thiru Karumuttu Thiagarajar Chettiar Second Memorial State Level Inter`
  - #36 `Joseph’s • Runner: ACE • Second Runner: Kongunadu • Third Runner: TCE `
  - #37 `MENS DOUBLES RESULTS: 1st PrizeKathir, Hrithick Manikam (YRTV) 2nd Pri`
- **dated_no_clear_scope**: 58
  - #34 `OPEN TOURNAMENTS State level Men’s Hockey Tournament (Aug 28,29-2023) `
  - #40 `Hockey (M) Winners MADURAI HALF MARATHON`
  - #44 `20th April Badminton(M&W) , Handball (M&W) Table Tennis (M&W) & Hockey`
  - #45 `OPEN TOURNAMENTS`
  - #51 `Intra and Inter department Badminton tournament for men and women`
  - #54 `Inter Department Kabaddi Tournament, for men`
- **departmental_text_present**: 32
  - #1 `International Conference on AI in Construction and Sustainable Built E`
  - #3 `Five-Day Online FDP on “AI-Powered Pedagogy”`
  - #7 `International Conference On Contemporary Mathematics And Innovations (`
  - #8 `Integrating AI into Classroom Pedagogy: Tools and Practices`
  - #9 `CODE AI 3.0 – Step into the Future with AI!`
  - #125 `Shoba, NITTTR, Chennai One0day Pedagogy workshop on “Instructional met`
- **insufficient_info_title_only**: 4
  - #4 `Founder's Day 2026`
  - #5 `GSDP Certificate Course on "Waste Optimization Professional"`
  - #6 `25th Silver Jubilee Reunion of the 1997 - 2001 Batch`
  - #10 `Shakti Math 2026 A Six-Day Online Course for Young Students (5th to 8t`

> Advisory keyword/date classification. Dept-specific sporting or award text can still be institution-wide; inspection recommended.

### Category vs text inconsistency (advisory)

- Records whose text suggests a different specific category than stored: **129**
  - #135 `With a student-centric environment, TCE encourages participa` stored=['CLUB', 'CULTURAL', 'SPORTS'] text-suggests=['SYMPOSIUM']
  - #564 `institution emphasizes professional development through the ` stored=['FDP', 'SEMINAR', 'WORKSHOP'] text-suggests=['STTP']
  - #835 `Best Outgoing NCC Cadet (Girl) - SUBHASHINI M` stored=['ACHIEVEMENT', 'NSS'] text-suggests=['NCC']
  - #843 `Best Outgoing NCC Cadet (Girl) - BALA SOUNDARYA V` stored=['ACHIEVEMENT', 'NSS'] text-suggests=['NCC']
  - #850 `Best Outgoing NCC Cadet (Girl) - GOPIKA GS` stored=['ACHIEVEMENT', 'NSS'] text-suggests=['NCC']
  - #2230 `Awarded Third Place in ZEMCH 2021 UAEU Design Workshop` stored=['ACHIEVEMENT'] text-suggests=['WORKSHOP']
  - #2231 `Best paper award in national conference NITT – NIT Trichy` stored=['ACHIEVEMENT'] text-suggests=['CONFERENCE']
  - #2244 `Reviewer of Journals for Passive Low Energy Architecture Des` stored=['ACHIEVEMENT'] text-suggests=['CONFERENCE']
  - #2292 `Nexus' 25` stored=['CLUB'] text-suggests=['SYMPOSIUM']
  - #2312 `TC - Placement Cell, Interview and Seminar Hall` stored=['RESEARCH'] text-suggests=['SEMINAR']
  - #2321 `TCE Mech Seminar Hall Interior` stored=['RESEARCH'] text-suggests=['SEMINAR']
  - #2379 `Blood donor representing - NCC – Blood-donation camp conduct` stored=['ACHIEVEMENT'] text-suggests=['NCC']
  - #2383 `Lead NCC, student council students – Admission day Volunteer` stored=['ACHIEVEMENT'] text-suggests=['NCC']
  - #2385 `On-going – BEACON Cohort hackathon` stored=['ACHIEVEMENT'] text-suggests=['HACKATHON']
  - #2386 `On-going – ZeAI made in India hackathon` stored=['ACHIEVEMENT'] text-suggests=['HACKATHON']

> Text-vs-category advisory only; highlights likely mislabelled records for human review. Nothing is changed.

## 4. Department audit

- Institution-wide (General): **813**

| Department | Activities |
| ---------- | ----------:|
| Civil Engineering | 224 |
| Chemistry | 46 |
| Computer Science and Engineering | 111 |
| Computer Science and Business Systems | 61 |
| Computer Applications | 33 |
| Applied Mathematics and Computational Science | 101 |
| Artificial Intelligence | 41 |
| Electronics and Communication Engineering | 129 |
| Electrical and Electronics Engineering | 205 |
| English | 13 |
| Information Technology | 238 |
| Mechanical Engineering | 75 |
| Mechatronics | 47 |
| T'SEDA (Architecture, Design, Planning) | 165 |

- Multi-department records: **14** (counted in every applicable department; never duplicated)
  - #112 `Institute Innovation Council Members Faculty Representation in IIC Name of the M` → Electronics and Communication Engineering; Electrical and Electronics Engineering
  - #315 `T 2022 CSE TN18SWA 726077 NTRO (NationalTechnical Research Organisation), a cent` → Computer Science and Engineering; Mechanical Engineering
  - #345 `For further details on ISRO-START program, click the following annexure II For C` → Electronics and Communication Engineering; Chemistry
  - #348 `Balamurali, ASP/Mech M/s TVS Motor Company, Hosur Product Engineering Lab - Desi` → Electronics and Communication Engineering; Mechanical Engineering
  - #382 `Conference Room : 1 GD Rooms : 3 Interview Cabins : 8 Classrooms - Training : 2 ` → T'SEDA (Architecture, Design, Planning); Computer Applications
  - #605 `Salient features of curriculum @TCE: Curriculum` → Electrical and Electronics Engineering; Mechanical Engineering
  - #671 `Anitha, Associate Professor in the Department of Applied Mathematics & Computati` → Applied Mathematics and Computational Science; Computer Science and Engineering
  - #827 `EVENT MEDAL NAME Judo (M) Silver medal Arunkumar S, II year CSE Judo (M) Balakum` → Computer Science and Engineering; Electronics and Communication Engineering; Mechanical Engineering

- Values outside the 14-department master (kept, not relabelled): `{'Physics': 39}`

## 5. Stakeholder audit

| Stakeholder | Activities |
| ------------ | ----------:|
| Students | 1141 |
| Faculty | 589 |
| Industry | 259 |
| Faculty; Industry | 125 |
| Institution | 59 |
| External; Students | 42 |
| Students; Faculty | 23 |
| Students; Industry | 22 |
| (missing) | 10 |
| Students; Alumni | 8 |
| Alumni | 6 |
| Alumni; Industry | 5 |
| Students; Faculty; Industry | 5 |
| Students; Faculty; Staff | 5 |
| Staff | 3 |
| Students; External | 3 |
| Faculty; Staff | 3 |
| Students; Alumni; Industry | 3 |
| Alumni; External | 2 |
| Students; Faculty; Alumni; Industry | 2 |
| Students; Staff | 2 |
| Staff; Alumni | 1 |
| Faculty; External | 1 |
| Students; Faculty; Staff; Industry | 1 |

- Outside the supported set (incl. missing): `{'(missing)': 10}`

## 6. Duplicate audit

- Exact source-URL groups: **147**
  - `tce.edu/events` → ids [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  - `tce.edu` → ids [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
  - `tce.edu/index.php/student/physical-education/activities` → ids [33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69]
  - `tce.edu/student/ncc` → ids [70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86]
  - `tce.edu/campuslife/nss` → ids [87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110]
  - `tce.edu/industry/iic` → ids [111, 112, 113]
  - `tce.edu/about/statutory-committees` → ids [114, 115]
  - `tce.edu/about/about-the-college` → ids [116, 117, 118]
  - `tce.edu/about/administration` → ids [119, 120, 121]
  - `tce.edu/academics/tlp-tce` → ids [122, 123, 124, 125, 126, 127, 128, 129, 130, 131]
  - `tce.edu/research/sponsored-research` → ids [132, 133, 134]
  - `tce.edu/campuslife` → ids [135, 136, 137]
  - `tce.edu/campuslife/sports` → ids [138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290]
  - `tce.edu/campuslife/skill-rack` → ids [291, 292]
  - `tce.edu/campuslife/capacity-development-and-skill-enhancement` → ids [293, 294]
  - `tce.edu/campuslife/ncc` → ids [295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323]
  - `tce.edu/campuslife/yrc` → ids [324, 325, 326]
  - `tce.edu/industry/ecell` → ids [327, 328, 329, 330]
  - `tce.edu/industry/ten` → ids [331, 332, 333]
  - `tce.edu/nodal-centre/tss-car` → ids [334, 335]
  - `tce.edu/nodal-centre/isro-iirs-outreach-programmes` → ids [336, 337, 338, 339, 340, 341, 342, 343, 344, 345]
  - `tce.edu/nodal-centre/centres-excellence` → ids [346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369]
  - `tce.edu/events/icaic-2026` → ids [370, 371, 372]
  - `tce.edu/sites/default/files/pdf/tce-newsletter-2026-final-corrected-version.pdf` → ids [373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393]
  - `tce.edu/mqubit2026phy` → ids [395, 396, 397]
  - `tce.edu/index.php` → ids [398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420]
  - `tce.edu/academics/departments/computer-applications` → ids [424, 425]
  - `tce.edu/academics/departments/data-science` → ids [426, 427, 428]
  - `tce.edu/academics/departments/electronics-and-communication-engineering` → ids [429, 430, 431, 432, 433, 434, 435]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering` → ids [436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460, 461, 462, 463, 464, 465, 466, 467]
  - `tce.edu/academics/departments/information-technology` → ids [469, 470, 471, 472, 473]
  - `tce.edu/academics/departments/physics` → ids [474, 475]
  - `tce.edu/academics/departments/architecture` → ids [476, 477, 478, 479, 480]
  - `tce.edu/sites/default/files/pdf/nirf-2026-innovations.pdf` → ids [482, 483]
  - `tce.edu/sites/default/files/pdf/nirf-2026-sdg-institutions.pdf` → ids [484, 485, 486, 487, 488]
  - `tce.edu/sites/default/files/pdf/nirf-2025-innovation.pdf` → ids [489, 490, 491, 492]
  - `tce.edu/sites/default/files/pdf/tce-nirf-2023-overall.pdf` → ids [493, 494, 495]
  - `tce.edu/sites/default/files/pdf/tce-nirf-2022-overall.pdf` → ids [496, 497, 498]
  - `tce.edu/sites/default/files/pdf/nirf/nirf-2021-overall.pdf` → ids [499, 500, 501]
  - `tce.edu/sites/default/files/naac/ssr-cycle-ii-approved.pdf` → ids [502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 526, 527, 528, 529, 530, 531, 532, 533, 534, 535, 536, 537, 538, 539, 540, 541, 542, 543, 544, 545, 546, 547, 548, 549, 550, 551, 552, 553, 554, 555, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 575, 576, 577, 578, 579, 580, 581, 582, 583, 584, 585, 586, 587, 588, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599]
  - `tce.edu/sites/default/files/naac/final-ssr-report.pdf` → ids [600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625, 626, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636]
  - `tce.edu/sites/default/files/pdf/amendment-relativegradingsystem-2021.pdf` → ids [637, 639, 640, 641, 642, 643, 644, 645, 646]
  - `tce.edu/sites/default/files/pdf/amendment-researchpaper-internship.pdf` → ids [647, 648, 649, 650, 651, 652, 653, 654, 655, 656, 657, 658, 659]
  - `tce.edu/academics/academic-achievements` → ids [660, 661, 662, 663, 664, 665]
  - `tce.edu/sites/default/files/pdf/life-tce-report-2025-july31.pdf` → ids [666, 667, 668, 669, 670, 671, 672, 673, 674, 675, 676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695]
  - `tce.edu/sites/default/files/pdf/tce-faculty_conclave_2025-short-report.pdf` → ids [696, 697, 698, 699, 700, 701]
  - `tce.edu/sites/default/files/pdf/student-satisfaction-survey-2021-22.pdf` → ids [702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712]
  - `tce.edu/sites/default/files/pdf/student-satisfaction-survey-2020-21.pdf` → ids [714, 715, 716, 717, 718]
  - `tce.edu/sites/default/files/pdf/student-satisfaction-survey-2019-20.pdf` → ids [719, 720, 721, 722, 723, 724]
  - `tce.edu/sites/default/files/pdf/student-satisfaction-survey-2018-19.pdf` → ids [725, 726, 727]
  - `tce.edu/sites/default/files/pdf/aca-res-process-flow-2022.pdf` → ids [729, 730]
  - `tce.edu/sites/default/files/pdf/sr-formats-2025-updated.pdf` → ids [731, 732]
  - `tce.edu/sites/default/files/ipr-cell/activity/2022-2023/activity-3.pdf` → ids [733, 734, 735, 736]
  - `tce.edu/sites/default/files/ipr-cell/activity/2021-2022/activity-2.pdf` → ids [737, 738, 739]
  - `tce.edu/sites/default/files/ipr-cell/activity/2021-2022/activity-4.pdf` → ids [740, 741]
  - `tce.edu/sites/default/files/ipr-cell/activity/2021-2022/activity-7.pdf` → ids [742, 743, 744, 745, 746]
  - `tce.edu/sites/default/files/ipr-cell/activity/2020-2021/activity-4.pdf` → ids [748, 749]
  - `tce.edu/sites/default/files/ipr-cell/activity/2019-2020/activity-3.pdf` → ids [750, 751]
  - `tce.edu/sites/default/files/ipr-cell/activity/2018-2019/activity-1.pdf` → ids [753, 754]
  - `tce.edu/sites/default/files/pdf/tce-ip-policy.pdf` → ids [758, 759, 760, 761]
  - `tce.edu/sites/default/files/pdf/tce-sms-formats.pdf` → ids [762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773]
  - `tce.edu/campuslife/sports/organised-tce` → ids [774, 775, 776, 777, 778, 779, 780, 781, 782, 783, 784, 785]
  - `tce.edu/campuslife/sports/annual-sports-day` → ids [786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825, 826, 827, 828, 829, 830, 831, 832]
  - `tce.edu/campuslife/bos/college-day-awards-2026` → ids [833, 834, 835, 836, 837, 838]
  - `tce.edu/campuslife/bos/college-day-awards-2024` → ids [840, 841, 842, 843, 844, 845, 846]
  - `tce.edu/campuslife/bos/college-day-awards-2023` → ids [847, 848, 849, 850, 851, 852, 853]
  - `tce.edu/campuslife/bos/college-day-awards-2022` → ids [854, 855]
  - `tce.edu/campuslife/bos/college-day-awards-2020` → ids [857, 858, 859]
  - `tce.edu/campuslife/bos/college-day-awards-2019` → ids [860, 861, 862]
  - `tce.edu/student/bos/college-day-awards-2018` → ids [863, 864, 865, 866, 867, 868, 869, 870, 871, 872, 873, 874, 875, 876, 877]
  - `tce.edu/student/bos/college-day-awards-2017` → ids [878, 879]
  - `tce.edu/academics/departments/architecture/achievements` → ids [2230, 2231, 2232, 2233, 2234, 2235, 2236, 2237, 2238, 2239, 2240, 2241, 2242, 2243, 2244, 2245, 2246, 2247, 2248, 2249, 2250, 2251, 2252, 2253, 2254, 2255, 2256, 2257, 2258, 2259, 2260, 2261, 2262, 3582, 3583, 3584, 3585, 3586, 3587, 3588, 3589, 3590, 3591, 3592, 3593, 3594, 3595, 3596, 3597, 3598, 3599, 3600, 3601, 3602, 3603, 3604]
  - `tce.edu/academics/departments/architecture/associations` → ids [2263, 2264, 2265, 2266, 2267, 2268, 2269, 2270, 2271, 2272, 2273, 2274, 2275, 2276, 2277, 2278, 2279, 2280, 2281, 2282, 2283, 2284, 2285, 2286, 2287, 2288, 2289, 2290, 2291, 2292]
  - `tce.edu/academics/departments/architecture/consultancy-projects` → ids [2293, 2294, 2295, 2296, 2297, 2298, 2299, 2300, 2301, 2302, 2303, 2304, 2305, 2306, 2307, 2308, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320, 2321, 2322, 2323, 2324, 2325, 2326, 2327, 2328, 2329, 2330, 2331, 2332, 2333]
  - `tce.edu/academics/departments/architecture/mou` → ids [2334, 2335, 2336, 2337, 2338, 2339, 2340, 2341, 2342, 2343, 2344]
  - `tce.edu/academics/departments/architecture/outreach-activities` → ids [2345, 2346, 2347, 2348, 2349, 2350, 2351, 2352, 2353, 2354, 2355, 2356, 2357, 2358, 2359, 2360, 2361, 2362, 2363, 2364, 2365]
  - `tce.edu/academics/departments/architecture/sponsored-research` → ids [2366, 2367, 2368]
  - `tce.edu/academics/departments/artificial-intelligence/achievements` → ids [2369, 2370, 2371, 2372, 2373, 2374, 2375, 2376, 2377, 2378, 2379, 2380, 2381, 2382, 2383, 2384, 2385, 2386, 2387, 2388, 2389, 2390, 2391, 2392, 2393, 2394, 2395, 2396, 2397, 2398, 2399, 3605, 3606]
  - `tce.edu/academics/departments/artificial-intelligence/patents` → ids [2400, 2401, 2402, 2403, 2404, 2405]
  - `tce.edu/academics/departments/artificial-intelligence/sponsored-research` → ids [2406, 2407]
  - `tce.edu/academics/departments/chemistry/achievements` → ids [2408, 2409, 2410, 2411, 2412, 2413, 2414, 2415, 2416, 2417, 2418, 2419, 2420, 2421, 2422, 3607, 3608]
  - `tce.edu/academics/departments/chemistry/consultancy-projects` → ids [2423, 2424, 2425, 2426, 2427, 2428, 2429, 2430, 2431, 2432]
  - `tce.edu/academics/departments/chemistry/mou` → ids [2433, 2434, 2435, 2436, 2437, 2438, 2439]
  - `tce.edu/academics/departments/chemistry/patents` → ids [2441, 2442, 2443, 2444, 2445, 2446, 2447]
  - `tce.edu/academics/departments/chemistry/sponsored-research` → ids [2448, 2449, 2450]
  - `tce.edu/academics/departments/civil-engineering/achievements` → ids [2451, 2452, 2453, 2454, 2455, 2456, 2457, 2458, 2459, 3609, 3610, 3611, 3612, 3613, 3614, 3615, 3616, 3617, 3618, 3619, 3620]
  - `tce.edu/academics/departments/civil-engineering/associations` → ids [2461, 2462, 2465]
  - `tce.edu/academics/departments/civil-engineering/consultancy-projects` → ids [2469, 2470, 2471, 2472, 2473, 2474, 2475, 2476, 2477, 2478, 2479, 2480, 2481, 2482, 2483, 2484, 2485, 2486, 2487, 2488, 2489, 2490, 2491, 2492, 2493, 2494, 2495, 2496, 2497, 2498, 2499, 2500, 2501, 2502, 2503, 2504, 2505, 2506, 2507, 2508, 2509, 2510, 2511, 2512, 2513, 2514, 2515, 2516, 2517, 2518, 2519, 2520, 2521, 2522, 2523, 2524, 2525, 2526, 2527, 2528, 2529, 2530, 2531, 2532, 2533, 2534, 2535, 2536, 2537, 2538, 2539, 2540, 2541, 2542, 2543, 2544, 2545, 2546, 2547, 2548, 2549, 2550, 2551, 2552, 2553, 2554, 2555, 2556, 2557, 2558, 2559, 2560, 2561, 2562, 2563, 2564, 2565, 2566, 2567, 2568, 2569, 2570, 2571, 2572, 2573, 2574, 2575, 2576, 2577, 2578, 2579, 2580, 2581, 2582, 2583, 2584, 2585, 2586, 2587, 2588, 2589, 2590, 2591, 2592, 2593, 2594, 2595, 2596, 2597, 2598, 2599, 2600, 2601, 2602, 2603, 2604, 2605, 2606, 2607, 2608, 2609, 2610, 2611, 2612, 2613, 2614, 2615, 2616, 2617, 2618, 2619, 2620, 2621, 2622, 2623, 2624, 2625, 2626, 2627, 2628, 2629, 2630, 2631, 2632, 2633, 2634, 2635]
  - `tce.edu/academics/departments/civil-engineering/mou` → ids [2636, 2637, 2638, 2639, 2640]
  - `tce.edu/academics/departments/civil-engineering/patents` → ids [2641, 2642, 2643, 2644, 2645, 2646]
  - `tce.edu/academics/departments/civil-engineering/sponsored-research` → ids [2647, 2648, 2649, 2650, 2651, 2652, 2653, 2654, 2655, 2656, 2657, 2658]
  - `tce.edu/academics/departments/civil-engineering/upcoming-events` → ids [2659, 2660, 2661, 2662, 2663, 2664, 2666, 2667]
  - `tce.edu/academics/departments/computer-applications/achievements` → ids [2668, 2669, 3621, 3622, 3623, 3624, 3625, 3626, 3627, 3628, 3629, 3630, 3631, 3632, 3633, 3634, 3635, 3636]
  - `tce.edu/academics/departments/computer-applications/sponsored-research` → ids [2672, 2673, 2674, 2675, 2676, 2677, 2678]
  - `tce.edu/academics/departments/computer-science-and-business-system/awards-recognitions` → ids [2679, 2680, 2681, 2682, 2683, 2684, 2685, 2686, 2687, 2688, 2689, 2690, 2691, 2692, 2693, 2694, 2695, 2696, 2697, 2698, 2699, 2700, 2701, 2702, 2703, 2704, 2705, 2706, 2707, 2708, 2709, 3637, 3638, 3639, 3640, 3641, 3642, 3643, 3644, 3645, 3646, 3647, 3648]
  - `tce.edu/academics/departments/computer-science-and-business-system/mou` → ids [2710, 2711, 2712]
  - `tce.edu/academics/departments/computer-science-and-business-system/outreach-activities` → ids [2713, 2714, 2715, 2716, 2717]
  - `tce.edu/academics/departments/computer-science-and-business-system/patents` → ids [2718, 2719, 2720, 2721, 2722, 2723, 2724, 2725]
  - `tce.edu/academics/departments/computer-science-engineering/achievements` → ids [2728, 2729, 2730, 2731, 2732, 2733, 2734, 2735, 2736, 2737, 2738, 2739, 2740, 2741, 2742, 2743, 2744, 2745, 2746, 2747, 2748, 2749, 2750, 2751, 2752, 2753, 2754, 2755, 2756, 2757, 2758, 2759, 2760, 2761, 2762, 2763, 2764, 2765, 2766, 2767, 2768, 2769, 2770, 2771, 2772, 2773, 2774, 2775, 2776, 2777, 2778, 2779, 2780, 3649, 3650, 3651, 3652, 3653, 3654, 3655, 3656, 3657, 3658]
  - `tce.edu/academics/departments/computer-science-engineering/industry-interface` → ids [2781, 2782, 2783, 2784]
  - `tce.edu/academics/departments/computer-science-engineering/mou` → ids [2785, 2786, 2787, 2788, 2789, 2790, 2791, 2792, 2793, 2794, 2795, 2796, 2797, 2798, 2799, 2800, 2801]
  - `tce.edu/academics/departments/computer-science-engineering/outreach-activities` → ids [2802, 2803]
  - `tce.edu/academics/departments/computer-science-engineering/patents` → ids [2804, 2805, 2806, 2807, 2808, 2809]
  - `tce.edu/academics/departments/computer-science-engineering/sponsored-research` → ids [2810, 2811, 2812, 2813, 2814, 2815, 2816]
  - `tce.edu/academics/departments/data-science/achievements` → ids [2817, 2818, 2819, 2820, 2821, 2822, 2823, 2824, 2825, 2826, 2827, 2828, 2829, 2830, 2831, 2832, 2833, 2834, 2835, 2836, 2837, 2838, 2839, 2840, 2841, 2842, 2843, 2844, 2845, 2846, 2847, 2848, 2849, 3659, 3660, 3661, 3662, 3663, 3664, 3665, 3666, 3667, 3668, 3669, 3670, 3671, 3672, 3673, 3674, 3675, 3676]
  - `tce.edu/academics/departments/data-science/associations` → ids [2850, 2851, 2852, 2853, 2854]
  - `tce.edu/academics/departments/data-science/consultancy-projects` → ids [2855, 2856, 2857]
  - `tce.edu/academics/departments/data-science/mou` → ids [2858, 2859, 2860]
  - `tce.edu/academics/departments/data-science/outreach-activities` → ids [2861, 2862]
  - `tce.edu/academics/departments/data-science/patent` → ids [2863, 2864]
  - `tce.edu/academics/departments/data-science/sponsored-research` → ids [2865, 2866, 2867]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/awards-recognitions` → ids [2868, 2869, 2870, 2871, 2872, 2873, 2874, 2875, 2876, 2877, 2878, 2879, 2880, 2881, 2882, 2883, 2884, 2885, 2886, 2887, 2888, 3677, 3678, 3679, 3680, 3681, 3682, 3683, 3684, 3685]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/industry-interface` → ids [2889, 2890, 2891, 2892, 2893, 2894, 2895, 2896, 2897, 2898, 2899, 2900, 2901, 2902, 2903, 2904, 2905, 2906, 2907, 2908, 2909, 2910, 2911, 2912, 2913, 2914, 2915, 2916, 2917, 2918, 2919, 2920, 2921, 2922, 2923, 2924, 2925, 2926]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/mou` → ids [2927, 2928, 2929, 2930, 2931, 2932]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/outreach-activities` → ids [2933, 2934]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/patent` → ids [2935, 2936, 2937, 2938, 2939, 2940, 2941, 2942, 2943, 2944, 2945, 2946, 2947, 2948, 2949, 2950, 2951, 2952, 2953, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 2961, 2962, 2963, 2964, 2965, 2966, 2967, 2968, 2969, 2970, 2971, 2972, 2973, 2974, 2975, 2976, 2977, 2978, 2979, 2980, 2981, 2982, 2983, 2984, 2985, 2986, 2987, 2988, 2989, 2990, 2991, 2992, 2993, 2994, 2995, 2996, 2997, 2998, 2999, 3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010, 3011, 3012, 3013, 3014, 3015, 3016, 3017, 3018, 3019, 3020, 3021, 3022]
  - `tce.edu/academics/departments/electrical-and-electronics-engineering/sponsored-research` → ids [3023, 3024, 3025, 3026, 3027, 3028, 3029, 3030, 3031, 3032, 3033, 3034, 3035, 3036, 3037, 3038, 3039]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/achievements` → ids [3040, 3041, 3042, 3043, 3044, 3045, 3046, 3047, 3048, 3049, 3050, 3051, 3052, 3053, 3054, 3055, 3056, 3057, 3058, 3059, 3060, 3061, 3062, 3063, 3064, 3065, 3066, 3686, 3687, 3688, 3689, 3690]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/associations` → ids [3067, 3068, 3069, 3070, 3071, 3072, 3073]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/industry-interface` → ids [3074, 3075, 3076, 3077, 3078, 3079, 3080, 3081, 3082, 3083, 3084, 3085, 3086, 3087, 3088, 3089, 3090, 3091, 3092]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/mou` → ids [3093, 3094, 3095, 3096, 3097, 3098, 3099, 3100, 3101]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/patents` → ids [3102, 3103, 3104, 3105, 3106, 3107, 3108, 3109, 3110, 3111, 3112, 3113, 3114, 3115, 3116, 3117, 3118, 3119, 3120, 3121, 3122, 3123, 3124, 3125]
  - `tce.edu/academics/departments/electronics-and-communication-engineering/sponsored-research` → ids [3126, 3127, 3128, 3129, 3130, 3131, 3132, 3133, 3134, 3135, 3136, 3137, 3138, 3139, 3140, 3141, 3142, 3143, 3144]
  - `tce.edu/academics/departments/english/awards-recognitions` → ids [3145, 3146, 3147, 3148, 3149, 3691]
  - `tce.edu/academics/departments/english/mou` → ids [3150, 3151]
  - `tce.edu/academics/departments/english/outreach-activities` → ids [3152, 3153, 3154, 3155]
  - `tce.edu/academics/departments/information-technology/awards-recognitions` → ids [3157, 3158, 3159, 3160, 3161, 3162, 3163, 3164, 3165, 3166, 3167, 3168, 3169, 3170, 3171, 3172, 3173, 3174, 3175, 3176, 3177, 3178, 3179, 3180, 3181, 3182, 3183, 3184, 3185, 3186, 3187, 3188, 3189, 3190, 3191, 3192, 3193, 3194, 3195, 3196, 3197, 3198, 3199, 3200, 3201, 3202, 3203, 3204, 3205, 3206, 3207, 3208, 3209, 3210, 3211, 3212, 3213, 3214, 3215, 3216, 3217, 3218, 3219, 3220, 3221, 3222, 3223, 3224, 3225, 3226, 3227, 3228, 3229, 3230, 3231, 3232, 3233, 3234, 3235, 3236, 3237, 3238, 3239, 3240, 3241, 3242, 3243, 3244, 3245, 3246, 3247, 3248, 3268, 3269, 3270, 3271, 3272, 3273, 3274, 3275, 3276, 3277, 3278, 3279, 3280, 3281, 3282, 3283, 3284, 3285, 3286, 3287, 3288, 3289, 3290, 3291, 3292, 3293, 3294, 3295, 3296, 3297, 3298, 3299, 3300, 3301, 3302, 3303, 3304, 3305, 3306, 3307, 3308, 3309, 3311, 3312, 3313, 3314, 3315, 3316, 3317, 3319, 3320, 3321, 3322, 3323, 3324, 3325, 3326, 3327, 3328, 3329, 3330, 3331, 3332, 3333, 3334, 3335, 3336, 3337, 3338, 3339, 3340, 3341, 3342, 3343, 3692, 3693, 3694, 3695, 3696, 3697, 3698, 3699]
  - `tce.edu/academics/departments/information-technology/industry-interface` → ids [3344, 3345, 3346, 3347, 3348]
  - `tce.edu/academics/departments/information-technology/mou` → ids [3349, 3350, 3351, 3352, 3353, 3354, 3355, 3356]
  - `tce.edu/academics/departments/information-technology/patents` → ids [3358, 3359, 3360, 3361]
  - `tce.edu/academics/departments/information-technology/professional-societies` → ids [3362, 3363, 3364, 3365, 3366, 3367, 3368, 3369, 3370, 3371, 3372, 3373, 3374, 3375, 3376, 3377, 3378, 3379, 3380, 3381, 3382, 3383, 3384, 3385, 3386, 3387, 3388, 3389, 3390, 3391, 3392, 3393]
  - `tce.edu/academics/departments/information-technology/sponsored-research` → ids [3394, 3395, 3396, 3397, 3398, 3399, 3400, 3401, 3402, 3403, 3404, 3405, 3406, 3407]
  - `tce.edu/academics/departments/mathematics/awards-and-recognitions` → ids [3408, 3409, 3410, 3411, 3412, 3413, 3414, 3415, 3416, 3417, 3418, 3419, 3420, 3421, 3422, 3423, 3424, 3700]
  - `tce.edu/academics/departments/mathematics/past-events` → ids [3425, 3426, 3427, 3428, 3429]
  - `tce.edu/academics/departments/mathematics/patents` → ids [3430, 3431, 3432, 3433, 3434]
  - `tce.edu/academics/departments/mechanical-engineering/awards-recognitions` → ids [3436, 3437, 3438, 3439, 3440, 3441, 3442, 3443, 3444, 3445, 3446, 3447, 3448, 3449, 3450, 3451, 3452, 3453, 3454, 3455, 3456, 3457, 3458, 3459, 3460, 3461, 3462, 3463, 3464, 3465, 3466, 3467, 3468, 3469, 3470, 3471]
  - `tce.edu/academics/departments/mechanical-engineering/mou` → ids [3472, 3473, 3474]
  - `tce.edu/academics/departments/mechanical-engineering/patents` → ids [3475, 3476, 3477, 3478, 3479, 3480, 3481, 3482, 3483, 3484, 3485]
  - `tce.edu/academics/departments/mechanical-engineering/sponsored-research` → ids [3486, 3487, 3488, 3489, 3490, 3491, 3492, 3493, 3494, 3495, 3496, 3497, 3498, 3499, 3500, 3501, 3503]
  - `tce.edu/academics/departments/mechatronics/awards-recognitions` → ids [3504, 3505, 3506, 3507, 3508, 3509, 3510, 3511, 3512, 3513, 3514, 3515, 3516, 3517, 3518, 3519, 3520, 3521, 3522, 3701]
  - `tce.edu/academics/departments/mechatronics/industry-interface` → ids [3523, 3524, 3525, 3526, 3527, 3528, 3529, 3530]
  - `tce.edu/academics/departments/mechatronics/mou` → ids [3531, 3532, 3533, 3534, 3535, 3536]
  - `tce.edu/academics/departments/mechatronics/patent` → ids [3538, 3539, 3540, 3541, 3542]
  - `tce.edu/academics/departments/mechatronics/sponsored-research` → ids [3543, 3544]
  - `tce.edu/academics/departments/physics/achievements` → ids [3545, 3546, 3547, 3548, 3549, 3550, 3551, 3552, 3553, 3554, 3555, 3556, 3557, 3558, 3559, 3560, 3561, 3562, 3563, 3564, 3565]
  - `tce.edu/academics/departments/physics/outreach-activities` → ids [3566, 3567]
  - `tce.edu/academics/departments/physics/sponsored-research` → ids [3568, 3569, 3570, 3571, 3572, 3573, 3574, 3575, 3576, 3577, 3578, 3579, 3580, 3581]
- Exact normalized-title groups: **73** (activities involved: 158)
- Fuzzy LIKELY groups (token-sort ratio ≥97, same period): **240**
  - 100.0: ids [2381, 3606] `Finalist – Code feast` | `Finalist – Code feast`
  - 100.0: ids [2754, 3656] `2nd Place – 4*100m relay` | `2nd Place – 4*100m relay`
  - 100.0: ids [2757, 3657] `3rd Place – CM Trophy(Chess)` | `3rd Place – CM Trophy(Chess)`
  - 100.0: ids [2758, 3655] `3rd place – TT Alumni Meet Tournament` | `3rd place – TT Alumni Meet Tournament`
  - 100.0: ids [2775, 3651] `Winner – Hackrax’26` | `Winner – Hackrax’26`
  - 100.0: ids [2776, 3653] `Winner – HPE Think-A-Thon` | `Winner – HPE Think-A-Thon`
  - 100.0: ids [2778, 3652] `Winner – Quantumurd Hackathon` | `Winner – Quantumurd Hackathon`
  - 97.8: ids [2808, 3109] `Quantum Safe Smart Submarine Monitoring System` | `Quantum-Safe Smart Submarine Monitoring System`
  - 100.0: ids [3019, 3103] `System and Method for Visual Fault Classification in Solar P` | `System and Method for Visual Fault Classification in Solar P`
  - 99.7: ids [3127, 3143] `Archival, Classification of Madurai's Chithiral Festival Att` | `Archival, Classification of Madurais Chithiral Festival Atti`
  - 100.0: ids [11, 398] `Institution Innovation Council (IIC) signed 29 MoUs with ind` | `Institution Innovation Council (IIC) signed 29 MoUs with ind`
  - 100.0: ids [12, 399] `Hosted MSME Hackathon 4.0, granting ₹15 lakh for student inn` | `Hosted MSME Hackathon 4.0, granting ₹15 lakh for student inn`
  - 100.0: ids [13, 400] `Centers like TSSCAR and CEEPT offer industrial training, pro` | `Centers like TSSCAR and CEEPT offer industrial training, pro`
  - 100.0: ids [14, 401] `Regular collaboration with Thoughtworks, Amazon, BHEL, and I` | `Regular collaboration with Thoughtworks, Amazon, BHEL, and I`
  - 100.0: ids [15, 403] `Achieved 1,595 WoS and 4,432 Scopus-indexed publications wit` | `Achieved 1,595 WoS and 4,432 Scopus-indexed publications wit`
  - 100.0: ids [16, 404] `345 students` | `345 students`
  - 100.0: ids [17, 405] `I am thrilled to share that I` | `I am thrilled to share that I`
  - 100.0: ids [18, 406] `Graduating in 2025 with good performance` | `Graduating in 2025 with good performance`
  - 100.0: ids [19, 407] `I am proud to tell that I` | `I am proud to tell that I`
  - 100.0: ids [20, 408] `rigorous training programs, practice interviews, and persona` | `rigorous training programs, practice interviews, and persona`
  - 100.0: ids [23, 411] `regular training sessions, mock interviews, and career guida` | `regular training sessions, mock interviews, and career guida`
  - 100.0: ids [21, 409] `Graduating as a rank holder in 2023` | `Graduating as a rank holder in 2023`
  - 100.0: ids [22, 410] `management's focus on providing state-of-the-art facilities,` | `management's focus on providing state-of-the-art facilities,`
  - 100.0: ids [24, 412] `Being a member of the NSS provided me with a unique opportun` | `Being a member of the NSS provided me with a unique opportun`
  - 100.0: ids [25, 413] `college’s placement training` | `college’s placement training`
  - 100.0: ids [26, 414] `This, along with the placement coaching, encouragement, and ` | `This, along with the placement coaching, encouragement, and `
  - 100.0: ids [27, 415] `department provided great opportunities for growth through t` | `department provided great opportunities for growth through t`
  - 100.0: ids [28, 416] `Placement training sessions played a key role in preparing m` | `Placement training sessions played a key role in preparing m`
  - 100.0: ids [29, 417] `placement training programs, sessions with alumni placed in ` | `placement training programs, sessions with alumni placed in `
  - 100.0: ids [30, 418] `Their guidance, training, and support throughout the placeme` | `Their guidance, training, and support throughout the placeme`
  - 100.0: ids [31, 419] `This milestone reflects the strong academic foundation and i` | `This milestone reflects the strong academic foundation and i`
  - 100.0: ids [32, 420] `From placement training sessions to continuous mentoring, th` | `From placement training sessions to continuous mentoring, th`
  - 98.4: ids [444, 458] `Two days workshop on “Arduino Unleashed: A Beginner’s Guide ` | `Two days workshop on “Arduino Unleashed: A Beginner’s Guide `
  - 98.3: ids [448, 461] `Coordinated IAEMP Sponsored Two-Day Seminar on Energy Auditi` | `Coordinated IAEMP Sponsored Two-Day Seminar on Energy Auditi`
  - 99.5: ids [763, 770] `List of Publications from this Project(including title, auth` | `List of Publications from this Project(including title, auth`
  - 99.2: ids [766, 772] `Achievement of Objectives a) List of approved project object` | `Achievement of Objectives a) List of approved project object`
  - 100.0: ids [768, 773] `Conclusion and Suggestions a) Overall remarks on the success` | `Conclusion and Suggestions a) Overall remarks on the success`
  - 100.0: ids [3154, 3155] `Leadership Qualities for School Children` | `Leadership Qualities for School Children`
  - 98.0: ids [3628, 3636] `1st Prize – TCE Visual Arts Club - Frames & Fames` | `1st Price – TCE Visual Arts Club - Frames & Fames`
  - 97.6: ids [143, 221] `3 Shooting Tanish Milind Salunkhe RepresentedAnna University` | `11 Shooting(M) Tanish Milind Salunkhe RepresentedAnna Univer`
  - 97.5: ids [446, 459] `One day Workshop on “ Hands-on IoT: Getting started with Ard` | `One day Workshop on “ Hands-on IoT: Getting started with Ard`
  - 98.5: ids [449, 462] `Coordinated workshop on "RECENT TRENDS IN IT DOMAIN" in asso` | `Coordinated workshop on "RECENT TRENDS IN IT DOMAIN" in asso`
  - 98.2: ids [451, 464] `Coordinated one day Workshop on National "e seva App store &` | `Coordinated one day Workshop on National "e seva App store &`
  - 98.3: ids [452, 465] `Co-Coordinated "Madurai Hackathon 2023" in association with ` | `Co-Coordinated "Madurai Hackathon 2023" in association with `
  - 97.9: ids [775, 776] `Served as Selection Committee Member for Badminton (Men), Zo` | `Served as Selection Committee Member for Badminton (Women), `
  - 97.4: ids [3483, 3542] `Hysterisis Loop Framed Electric Bicycle` | `Hysteresis Loop Framed Electric Bicycle`
  - 98.8: ids [453, 466] `Coordinated "NEN Faculty Orientation Programme (FoP)" in col` | `Coordinated "NEN Faculty Orientation Programme (FoP)" in col`
  - 99.0: ids [455, 467] `Coordinated "StartupTN Devhack 2023 Hackathon"in association` | `Coordinated "StartupTN Devhack 2023 Hackathon"in association`
  - 100.0: ids [702, 711] `Communication, Critical thinking, Collaboration, Creativity` | `Communication, Critical thinking, Collaboration, Creativity`
  - 97.6: ids [275, 283] `10 BasketBall Men’s team Represented Anna University Sports ` | `24 BasketBall Men’s team Represented Anna University Sports `
  - 97.5: ids [276, 284] `11 Football Men’s team Represented Anna University Sports Bo` | `25 Football Men’s team Represented Anna University Sports Bo`
  - 98.8: ids [277, 285] `12 Aquatics Men’s team Represented Anna University Sports Bo` | `26 Aquatics Men’s team Represented Anna University Sports Bo`
  - 97.5: ids [279, 287] `14 Fencing Men’s team Represented Anna University Sports Boa` | `28 Fencing Men’s team Represented Anna University Sports Boa`
  - 97.7: ids [280, 288] `15 Ball Badminton Men’s team Represented Anna University Spo` | `29 Ball Badminton Men’s team Represented Anna University Spo`
  - 97.6: ids [281, 289] `16 Best Physique Men’s team Represented Anna University Spor` | `30 Best Physique Men’s team Represented Anna University Spor`
  - 98.8: ids [282, 290] `17 Taekwondo Men’s team Represented Anna University Sports B` | `31 Taekwondo Men’s team Represented Anna University Sports B`
  - 98.0: ids [303, 322] `Weapon Training by NCC cadets during CATC Camp At NTA -Idaya` | `Weapon Training by NCC cadets during CATC Camp At NTA -Idaya`
  - 98.1: ids [304, 323] `Cultural Performance by NCC cadets during CATC Camp At NTA -` | `Cultural Performance by NCC cadets during CATC Camp At NTA -`
  - 98.4: ids [447, 460] `Adjunct faculty webinar series on “Bridging the gap between ` | `Adjunct faculty webinar series on “Bridging the gap between `
  - 100.0: ids [714, 718] `Communication, Critical thinking, Collaboration, Creativity` | `Communication, Critical thinking, Collaboration, Creativity`
- Fuzzy POSSIBLE groups (ratio ≥93): **76**

## 7. Non-activity audit (advisory)

- Heuristic flags: **26**
Examples:
  - #1 `International Conference on AI in Construction and Sustainable Built E` — no description and no evidence text
  - #2 `TEDx Thiagarajar College of Engineering` — no description and no evidence text
  - #3 `Five-Day Online FDP on “AI-Powered Pedagogy”` — no description and no evidence text
  - #4 `Founder's Day 2026` — no description and no evidence text
  - #5 `GSDP Certificate Course on "Waste Optimization Professional"` — no description and no evidence text
  - #6 `25th Silver Jubilee Reunion of the 1997 - 2001 Batch` — no description and no evidence text
  - #7 `International Conference On Contemporary Mathematics And Innovations (` — no description and no evidence text
  - #8 `Integrating AI into Classroom Pedagogy: Tools and Practices` — no description and no evidence text

- Candidate quality reviews marked NON_ACTIVITY: **0**

## 8. Source / provenance audit

- Activities with `activity_sources` rows: **2320**
- Activities with a primary `source_url`: **2320**
- Activities with **no traceable source**: **0**
- Distinct source URLs: **170**

| Source registry | Type | Active | URL |
| --------------- | ---- | ------ | --- |
| TCE Events | events | 1 | https://www.tce.edu/events |
| TCE Academics | academics | 1 | https://www.tce.edu/academics/programmes |
| TCE Departments | departments | 1 | https://www.tce.edu/academics/departments |
| TCE Sports | sports | 1 | https://www.tce.edu/campuslife/sports |
| TCE NCC | ncc | 1 | https://www.tce.edu/campuslife/ncc |
| TCE NSS | nss | 1 | https://www.tce.edu/campuslife/nss |
| TCE Clubs | clubs | 1 | https://clubs.tceapps.in/tce/student |
| TCE Achievements | achievements | 1 | https://www.tce.edu/ranking-recognition |
| TCE Outreach | outreach | 1 | https://www.tce.edu/campuslife/nss |
| TCE Newsletter | newsletter | 1 | https://www.tce.edu/sites/default/files/PDF/TCE-Newsletter-2026-Final-Corrected-Version.pdf |

## 9. Date audit

- Invalid structured date: **0**
- Future date: **1**
- Date inconsistent with stored academic year: **0**
- Only year available in source text: **138**
- Multiple years mentioned in source text: **156**
- Date range: `{'min': datetime.date(2021, 9, 21), 'max': datetime.date(2026, 12, 17)}`

## 10. Description-quality audit

- Empty descriptions: **10**
- Short (<20 chars): **93**
- Description equals title: **669**
- Rich fields: outcome 1008, venue 0, organizer 0, resource person 0

## 11. Five-year coverage

| Academic Year | Activities | Categories | Departments | Stakeholders |
| ------------- | ----------:| ----------:| -----------:| ------------:|
| 2021-22 | 167 | 13 | 12 | 6 |
| 2022-23 | 184 | 16 | 13 | 6 |
| 2023-24 | 444 | 16 | 15 | 7 |
| 2024-25 | 364 | 19 | 15 | 7 |
| 2025-26 | 351 | 15 | 15 | 5 |
| Before 2021 | 810 | 20 | 15 | 7 |

### Category × academic year (resolved periods)

| Category | 2021-22 | 2022-23 | 2023-24 | 2024-25 | 2025-26 | Before 2021 |
|----------|-------:|-------:|-------:|-------:|-------:|-----------:|
| Achievement and Awards | 82 | 62 | 125 | 152 | 193 | 162 |
| Campus | 0 | 4 | 10 | 1 | 0 | 15 |
| Clubs and Chapters | 1 | 6 | 25 | 16 | 8 | 22 |
| Conference | 0 | 1 | 3 | 8 | 5 | 12 |
| Cultural | 3 | 0 | 2 | 18 | 0 | 21 |
| FDP | 0 | 0 | 1 | 3 | 6 | 5 |
| Guest Lecture | 0 | 0 | 4 | 1 | 2 | 2 |
| Hackathon | 0 | 2 | 2 | 5 | 0 | 4 |
| Industry Collaboration | 20 | 32 | 27 | 63 | 36 | 146 |
| Internship | 2 | 2 | 0 | 8 | 4 | 17 |
| NCC | 6 | 3 | 6 | 1 | 4 | 50 |
| NSS | 1 | 5 | 5 | 2 | 2 | 50 |
| Orientation | 0 | 2 | 0 | 1 | 0 | 5 |
| Outreach and Extension | 3 | 3 | 10 | 28 | 9 | 27 |
| Placement | 0 | 4 | 0 | 25 | 0 | 13 |
| Research and Consultancy | 24 | 35 | 62 | 68 | 77 | 330 |
| Seminar | 3 | 2 | 0 | 9 | 1 | 13 |
| Sports | 19 | 44 | 178 | 3 | 2 | 49 |
| Webinar | 9 | 0 | 2 | 0 | 6 | 9 |
| Workshops | 4 | 7 | 16 | 23 | 10 | 37 |

## 12. Sanity checks (live DB)

| Check | Live DB | Expected (user constants) |
| ----- | ------: | -------------------------: |
| WORKSHOP (all scopes) | 97 | 97 |
| General (institution-wide) | 813 | 813 |
| 2025-26 Workshops (all scopes) | 10 | 10 |
| 2025-26 IT Achievements | 29 | 50 |
| 2024-25 T'SEDA | 47 | 47 |

## 13. Existing internal flags

- Open review-queue flags: `10`
  - activity #1 — validation-flag: missing-description
  - activity #2 — validation-flag: missing-description
  - activity #3 — validation-flag: missing-description
  - activity #4 — validation-flag: missing-description
  - activity #5 — validation-flag: missing-description
  - activity #6 — validation-flag: missing-description
  - activity #7 — validation-flag: missing-description
  - activity #8 — validation-flag: missing-description
  - activity #9 — validation-flag: missing-description
  - activity #10 — validation-flag: missing-description
- Period-recovery audit rows: `1480` ([{'recovery_method': 'UNRESOLVED', 'c': 408}, {'recovery_method': 'OUT_OF_SCOPE', 'c': 300}, {'recovery_method': 'ROW_YEAR', 'c': 190}, {'recovery_method': 'REPORT_DOC', 'c': 171}, {'recovery_method': 'SECTION_HEADING', 'c': 134}, {'recovery_method': 'EXPLICIT_YEAR', 'c': 116}, {'recovery_method': 'ROW_DATE', 'c': 112}, {'recovery_method': 'URL_YEAR', 'c': 18}, {'recovery_method': 'ROW_ACADEMIC_YEAR', 'c': 11}, {'recovery_method': 'URL_ACADEMIC_YEAR', 'c': 10}, {'recovery_method': 'RUNNING_HEADER', 'c': 6}, {'recovery_method': 'TITLE_DATE', 'c': 2}, {'recovery_method': 'EVENT_DOC_YEAR', 'c': 2}])
