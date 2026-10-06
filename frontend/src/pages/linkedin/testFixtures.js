export const optionsBody = {
  statuses: ["REPORTABLE", "NON_ACTIVITY", "REVIEW_REQUIRED"],
  review_statuses: ["UNREVIEWED", "NEEDS_REVIEW", "APPROVED"],
  date_statuses: ["dated", "undated", "ambiguous_multi_year"],
  categories: [
    { code: "FDP", name: "Workshop / FDP / STTP" },
    { code: "WORKSHOP", name: "Workshop" },
  ],
  departments: ["General", "Computer Science and Engineering"],
  stakeholders: ["Students", "Faculty"],
  academic_years: ["2025-26"],
  review_reasons: ["bare_text"],
  confidence_levels: ["low", "medium", "high"],
};

export const summaryBody = {
  total_raw_rows: 1544,
  total_canonical_posts: 1544,
  total_reportable_activities: 1280,
  total_non_activities: 102,
  total_review_required: 162,
  by_classification_status: { AUTO_CLASSIFIED: 1408, PENDING_REVIEW: 116 },
  by_review_status: { UNREVIEWED: 1400, NEEDS_REVIEW: 100, APPROVED: 44 },
  by_category: { WORKSHOP: 700, FDP: 400 },
  by_department: { General: 900, "Computer Science and Engineering": 300 },
  by_stakeholder: { Students: 1100, Faculty: 400 },
  dated_vs_undated: { dated: 699, undated: 829, ambiguous_multi_year: 16 },
  academic_year_availability: { "2025-26": 1280 },
  link_vs_linkless: { with_url: 1500, without_url: 44 },
  unresolved_or_flagged: 262,
  flagged_records: 100,
  manually_validated: 44,
  validation_stats: { sample_pending_review: 116, auto_classified: 1408, needs_review: 100, approved: 44 },
};

export const recordBody = {
  activity_id: "LI-00001",
  staging_post_id: 1,
  staging_candidate_id: "LSC-2026-01",
  reportable_status: "REPORTABLE",
  title: "Machine Learning Workshop",
  description: "A one-day workshop on Machine Learning for students.",
  post_url: "https://www.linkedin.com/posts/tcemadurai_x",
  activity_date: "2026-01-15",
  academic_year: "2025-26",
  categories: ["WORKSHOP"],
  departments: ["Computer Science and Engineering"],
  stakeholders: ["Students"],
  // formal report display fields (identical derivation to the public report)
  stakeholder_display: "students",
  name: "Machine Learning",
  report_department: "Computer Science and Engineering",
  award_category: "Workshop",
  achievement_description:
    'The Department of Computer Science and Engineering has conducted a workshop on the topic "Machine Learning" on 15 January 2026 for students.',
  report_date: "15 January 2026",
  academic_year_display: "2025\u201326",
  date_status: "dated",
  classification_status: "AUTO_CLASSIFIED",
  review_status: "UNREVIEWED",
  is_manually_validated: 0,
  category_candidates: [{ code: "WORKSHOP", name: "Workshop / FDP / STTP", score: 92 }],
  department_candidates: ["Computer Science and Engineering"],
  stakeholder_candidates: ["Students"],
  department_display: ["Computer Science and Engineering"],
  date_evidence: { primary_date: "2026-01-15", source: "post text", quote: "on 15 January 2026" },
  category_evidence: { matched: ["workshop"], weights: { workshop: 60 } },
  department_evidence: { matched: ["computer science"] },
  stakeholder_evidence: { students: 3 },
  communication_type: "post",
  communication_evidence: { has_url: true },
  evidence_score: 9,
  multi_label: 0,
  flags: [],
  unclear_reason: null,
  reason: "classification ok",
  kind: "primary",
  manual_overrides: {},
  validation_history: [
    { field: "review_status", old: "UNREVIEWED", new: "APPROVED", by: "shalini", at: "2026-09-23T12:00:00", note: "verified visually" },
  ],
  provenance: {
    source: "linkedin",
    source_workbook: "TCE LinkedIn Posts 2026.xlsx",
    source_sheet: "June 2025-June 2026",
    source_row: 12,
    occurrence_count: 3,
    source_occurrence_ids: [101, 102, 103],
    collected_at: "2026-09-20T09:30:00",
    resolved_via: "exact",
    activity_urn_id: "li_urn_1",
  },
};

// An institution-wide row: no department in the report columns, so the
// Validator falls back to "General".
export const generalRecordBody = {
  ...recordBody,
  activity_id: "LI-00002",
  staging_post_id: 2,
  title: "Five-Day FDP on Cloud Computing",
  description: "A five day Faculty Development Programme on Cloud Computing.",
  post_url: null,
  categories: ["FDP"],
  departments: [],
  stakeholders: ["Faculty"],
  stakeholder_display: "faculty",
  name: "",
  report_department: "",
  award_category: "FDP",
  achievement_description:
    "Thiagarajar College of Engineering has conducted a Faculty Development Programme for faculty.",
  report_date: "",
  academic_year_display: "",
};

export const recordsBody = {
  data: [recordBody],
  total: 1544,
  pagination: { page: 1, page_size: 25, total: 1544, pages: 62 },
};

export const queueBody = {
  data: [recordBody],
  total: 1,
};

export const jsonResponse = (body, ok = true) => Promise.resolve({
  ok,
  status: ok ? 200 : 400,
  json: async () => body,
});

export function routeFetch(handlers) {
  return (input, options = {}) => {
    const url = typeof input === "string" ? input : input.url;
    const route = handlers.find((h) => h.match.test(url));
    if (!route) return jsonResponse({ error: "not found" }, false);
    return route.respond(url, options);
  };
}

export function rule(match, body, ok = true) {
  return { match, respond: () => jsonResponse(body, ok) };
}