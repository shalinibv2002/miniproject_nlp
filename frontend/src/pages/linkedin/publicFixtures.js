export const filtersBody = {
  years: ["2024-25", "2025-26"],
  categories: [
    { code: "WORKSHOP", name: "Workshops" },
    { code: "FDP", name: "FDP" },
    { code: "SPORTS", name: "Sports" },
    { code: "TECH_FEST", name: "Technical Festival" },
  ],
  departments: ["General", "Computer Science and Engineering", "Information Technology"],
  stakeholders: ["Students", "Faculty", "Institution"],
  date_range: { earliest: "2024-04-01", latest: "2026-06-30" },
};

export const publicRecordBody = {
  activity_id: "LI-00001",
  title: "Machine Learning Workshop",
  summary: 'The Department of Computer Science and Engineering has conducted a workshop on the topic "Machine Learning" on 15 January 2026 for students.',
  post_url: "https://www.linkedin.com/posts/tcemadurai_1",
  activity_date: "2026-01-15",
  academic_year: "2025-26",
  category: "Workshops",
  categories: [{ code: "WORKSHOP", name: "Workshops" }],
  department: "Computer Science and Engineering",
  departments: ["Computer Science and Engineering"],
  stakeholder: "Students",
  stakeholders: ["Students"],
  source: "TCE LinkedIn",
  stakeholder_display: "students",
  name: "Machine Learning",
  department_display: "Computer Science and Engineering",
  award_category: "Workshops",
  achievement_description: 'The Department of Computer Science and Engineering has conducted a workshop on the topic "Machine Learning" on 15 January 2026 for students.',
  report_date: "15 January 2026",
  academic_year_display: "2025\u201326",
};

export const publicRecordBody2 = {
  activity_id: "LI-00002",
  title: "Five-Day FDP on Cloud Computing",
  summary: "Thiagarajar College of Engineering has conducted a Faculty Development Programme for faculty.",
  post_url: null,
  activity_date: null,
  academic_year: null,
  category: "FDP",
  categories: [{ code: "FDP", name: "FDP" }],
  department: "General",
  departments: [],
  stakeholder: "Faculty",
  stakeholders: ["Faculty"],
  source: "TCE LinkedIn",
  stakeholder_display: "faculty",
  name: "",
  department_display: "",
  award_category: "FDP",
  achievement_description: "Thiagarajar College of Engineering has conducted a Faculty Development Programme for faculty.",
  report_date: "",
  academic_year_display: "",
};

export const activitiesBody = {
  data: [publicRecordBody, publicRecordBody2],
  total: 2,
  pagination: { page: 1, page_size: 12, total: 2, pages: 1 },
};

export const overviewBody = {
  total_reportable_activities: 1280,
  activities_by_academic_year: [
    { academic_year: "2024-25", activity_count: 410 },
    { academic_year: "2025-26", activity_count: 870 },
  ],
  activities_by_category: [
    { category: "WORKSHOP", name: "Workshops", activity_count: 700 },
    { category: "FDP", name: "FDP", activity_count: 400 },
    { category: "SPORTS", name: "Sports", activity_count: 180 },
  ],
  activities_by_department: [
    { department: "General", activity_count: 900 },
    { department: "Computer Science and Engineering", activity_count: 300 },
  ],
  activities_by_stakeholder: [
    { stakeholder: "Students", activity_count: 1100 },
    { stakeholder: "Faculty", activity_count: 400 },
  ],
  activities_by_month: [
    { month: "2025-01", activity_count: 40 },
    { month: "2025-02", activity_count: 35 },
  ],
  date_status: { dated: 699, undated: 829, ambiguous_multi_year: 16 },
  source_coverage: {
    source: "TCE LinkedIn",
    with_url: 1180,
    without_url: 100,
    url_coverage_pct: 92.19,
  },
  general_departmental: { general: 300, departmental: 980 },
  general_categories: [
    { category: "WORKSHOP", name: "Workshops", activity_count: 200 },
    { category: "FDP", name: "FDP", activity_count: 100 },
  ],
  departmental_categories: [
    { category: "WORKSHOP", name: "Workshops", activity_count: 500 },
    { category: "FDP", name: "FDP", activity_count: 300 },
  ],
  departments_covered: 2,
  stakeholders_covered: 2,
  categories_covered: 3,
};

export const queryCountBody = {
  question: "How many workshops were conducted in 2025-26?",
  status: "answer",
  answer: "55 matching activities found.",
  count: 55,
  activities: [publicRecordBody],
  criteria: ["Academic year: 2025-26", "Category: Workshops"],
};

export const queryCompareBody = {
  question: "More workshops or seminars?",
  status: "answer",
  answer: "Workshops has more activities than Seminars (179 vs 60).",
  count: 179,
  activities: [],
  rows: [
    { label: "Workshops", value: 179 },
    { label: "Seminars", value: 60 },
  ],
  chart: {
    data: [
      { label: "Workshops", value: 179 },
      { label: "Seminars", value: 60 },
    ],
  },
  comparison: [
    { entity: "Workshops", activity_count: 179 },
    { entity: "Seminars", activity_count: 60 },
  ],
  criteria: ["Workshops", "Seminars"],
};

export const queryZeroBody = {
  question: "How many naval activities existed?",
  status: "zero",
  answer: "No matching activities were found for the selected criteria.",
  count: 0,
  activities: [],
  criteria: [],
};