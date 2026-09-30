export const STATUS_TONES = {
  REPORTABLE: "good",
  NON_ACTIVITY: "muted",
  REVIEW_REQUIRED: "warn",
  UNREVIEWED: "muted",
  NEEDS_REVIEW: "warn",
  APPROVED: "good",
  PENDING_REVIEW: "warn",
  AUTO_CLASSIFIED: "good",
  dated: "good",
  undated: "warn",
  ambiguous_multi_year: "bad",
};

export function statusTone(status) {
  return STATUS_TONES[status] || "muted";
}

export function confidenceInfo(evidenceScore) {
  if (evidenceScore == null) return null;
  if (evidenceScore <= 4) return { level: "low", label: "Low" };
  if (evidenceScore >= 8) return { level: "high", label: "High" };
  return { level: "medium", label: "Medium" };
}

export function categoryName(code, categories = []) {
  const found = categories.find((c) => c.code === code);
  return found ? found.name : code;
}

export function listNames(codes, names) {
  return (codes || []).map((code) => names[code]).filter(Boolean);
}

// ---------------------------------------------------------------------------
// Public-facing helpers (STEP 9).  The LinkedIn public API already returns
// human-readable names; these maps are centralised fallbacks so an internal
// code is never rendered raw when a name is missing.
// ---------------------------------------------------------------------------
export const PUBLIC_CATEGORY_FALLBACK = {
  ACHIEVEMENT: "Achievement",
  RESEARCH: "Research",
  INDUSTRY: "Industry Collaboration",
  CLUB: "Clubs and Chapters",
  OUTREACH: "Outreach and Extension",
  WORKSHOP: "Workshops",
  CONFERENCE: "Conference",
  SEMINAR: "Seminar",
  GUEST_LECTURE: "Guest Lecture",
  FDP: "FDP",
  HACKATHON: "Hackathon",
  CULTURAL: "Cultural",
  SPORTS: "Sports",
  NCC: "NCC",
  NSS: "NSS",
  PLACEMENT: "Placement",
  INTERNSHIP: "Internship",
  ORIENTATION: "Orientation",
  CAMPUS: "Campus",
  WEBINAR: "Webinar",
  ALUMNI: "Alumni",
  SYMPOSIUM: "Symposium",
  STTP: "STTP",
  TECH_FEST: "Technical Festival",
};

export function publicCategoryLabel(code, name) {
  if (name) return name;
  return PUBLIC_CATEGORY_FALLBACK[code] || code;
}

export const GENERAL_DEPARTMENT = "General";

export function publicDepartmentLabel(department) {
  if (!department) return GENERAL_DEPARTMENT;
  const d = String(department).trim();
  if (d === "MCA" || d.toLowerCase() === "mca" || d.toLowerCase() === "computer applications/mca" || d.toLowerCase() === "mca/computer applications") {
    return "Computer Applications";
  }
  return d;
}

export const PUBLIC_SOURCE_LABEL = "TCE LinkedIn";

export function publicSourceLabel(source) {
  return source || PUBLIC_SOURCE_LABEL;
}

const _MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export function formatPublicDate(iso) {
  if (!iso || !iso.includes("-")) return null;
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return null;
  return `${d} ${_MONTHS[m - 1]} ${y}`;
}

export const DATE_STATUS_LABELS = {
  dated: "Dated",
  undated: "Undated",
  ambiguous_multi_year: "Spans multiple years",
};

export function dateStatusSummary(dateStatus) {
  const dated = dateStatus?.dated || 0;
  const undated = dateStatus?.undated || 0;
  const ambiguous = dateStatus?.ambiguous_multi_year || 0;
  const total = dated + undated + ambiguous;
  const share = total ? Math.round((100 * dated) / total) : 0;
  return { dated, undated, ambiguous, total, share };
}