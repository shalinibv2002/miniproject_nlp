// Category-specific report columns for the on-screen report tables.
//
// This is the UI mirror of `backend/database/category_report_schema.py`, which
// is the single source of truth (also used by the report preview, the XLSX/PDF
// exports and Ask-the-Data).  Both sides are transcribed from the same revised
// per-category column contract:
//   * backend  -> backend/database/category_report_schema.py
//   * frontend -> frontend/src/lib/reportSchema.js
// A backend test and a frontend test pin both sides to the same rules, so the
// two cannot drift silently.
//
// Rules:
//   * Department is a departmental-only column -- except Alumni Meet, where it
//     names the alumnus' own course and batch and is part of the row's identity.
//   * Name / Award Category / Achievement Description belong to ACHIEVEMENT
//     alone -- they are never forced onto a workshop, club or sports record.
//   * LinkedIn URL is always last: a read-only reference for validation.
//   * PLACEMENT is retired from the active taxonomy; historical rows fall back
//     to the plain activity layout so they still render.

export const GENERAL = "general";
export const DEPARTMENTAL = "departmental";
export const ACHIEVEMENT = "ACHIEVEMENT";

const SNO = { label: "S.No", field: null };
const TITLE = { label: "Title", field: "title" };
const STAKEHOLDER = { label: "Stakeholder", field: "stakeholder_display" };
const NAME = { label: "Name", field: "name" };
const DEPARTMENT = { label: "Department", field: "department_display" };
const AWARD_CATEGORY = { label: "Award Category", field: "award_category" };
const DESCRIPTION = { label: "Achievement Description", field: "achievement_description" };
const DATE = { label: "Date", field: "report_date" };
const ACADEMIC_YEAR = { label: "Academic Year", field: "academic_year_display" };
const LINKEDIN_URL = { label: "LinkedIn URL", field: "post_url" };

// --- Columns of the revised per-category contracts -----------------------
// Every one of these is DERIVED from the one canonical row on the backend
// (backend/database/report_fields.py); none is stored, and a value the post
// does not state arrives blank.
const ALUMNI_NAME = { label: "Alumni Name", field: "alumni_name" };
const ALUMNI_DEPARTMENT = { label: "Department", field: "alumni_department" };
const TOPIC_THEME = { label: "Topic/Theme", field: "topic_theme" };
const CHIEF_GUEST = { label: "Chief Guest", field: "chief_guest" };
const TOPIC = { label: "Topic", field: "title" };
const SPEAKER = { label: "Speaker", field: "speaker" };
const EVENT_NAME = { label: "Event Name", field: "title" };
const EVENT_DESCRIPTION = { label: "Event Description", field: "event_description" };
const PLAIN_DESCRIPTION = { label: "Description", field: "event_description" };
const THEME_DESCRIPTION = { label: "Theme/Description", field: "event_description" };
const MOU_WITH = { label: "Signed MOU With", field: "mou_with" };
const PURPOSE = { label: "Purpose", field: "purpose" };
const DURATION = { label: "Duration", field: "duration" };
const DATE_RANGE = { label: "Date (From-To)", field: "date_range" };
const LOCATION = { label: "Location", field: "location" };
const RESEARCH_TOPIC = { label: "Research Topic", field: "title" };
const STAKEHOLDER_NAME = { label: "Stakeholder Name", field: "stakeholder_name" };
const SEMINAR_TITLE = { label: "Seminar Title", field: "title" };

function activity({ stakeholder = false, department = false } = {}) {
  const columns = [SNO, TITLE];
  if (department) columns.push(DEPARTMENT);
  if (stakeholder) columns.push(STAKEHOLDER);
  columns.push(DATE, ACADEMIC_YEAR, LINKEDIN_URL);
  return columns;
}

function achievement({ department = false } = {}) {
  const columns = [SNO, STAKEHOLDER, NAME];
  if (department) columns.push(DEPARTMENT);
  columns.push(AWARD_CATEGORY, DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL);
  return columns;
}

// Fallback for a category the audit did not customise and for a result set
// that mixes categories.
export const DEFAULT_GENERAL = activity();
export const DEFAULT_DEPARTMENTAL = activity({ department: true });

const GENERAL_ACTIVITY = activity();
const GENERAL_ACTIVITY_WITH_STAKEHOLDER = activity({ stakeholder: true });
const DEPARTMENTAL_ACTIVITY = activity({ department: true });
const DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER = activity({ department: true, stakeholder: true });

// Codes retired from the active reporting taxonomy.  Their rows still render,
// through the plain activity fallback.
export const RETIRED_CATEGORY_CODES = ["PLACEMENT"];

export const CATEGORY_SCHEMAS = {
  // --- revised contracts --------------------------------------------------
  ALUMNI: [
    [SNO, ALUMNI_NAME, ALUMNI_DEPARTMENT, TOPIC_THEME, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, ALUMNI_NAME, ALUMNI_DEPARTMENT, TOPIC_THEME, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  CONFERENCE: [
    [SNO, CHIEF_GUEST, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, CHIEF_GUEST, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  GUEST_LECTURE: [
    [SNO, TOPIC, SPEAKER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, TOPIC, SPEAKER, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  HACKATHON: [
    [SNO, TITLE, EVENT_DESCRIPTION, STAKEHOLDER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, TITLE, EVENT_DESCRIPTION, DEPARTMENT, STAKEHOLDER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  INDUSTRY: [
    [SNO, MOU_WITH, PURPOSE, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, DEPARTMENT, MOU_WITH, PURPOSE, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  INTERNSHIP: [
    [SNO, TITLE, DURATION, DATE_RANGE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, TITLE, DURATION, DEPARTMENT, DATE_RANGE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  NCC: [
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  NSS: [
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  ORIENTATION: [
    [SNO, EVENT_NAME, CHIEF_GUEST, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, EVENT_NAME, CHIEF_GUEST, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  OUTREACH: [
    [SNO, TITLE, THEME_DESCRIPTION, LOCATION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, TITLE, THEME_DESCRIPTION, DEPARTMENT, LOCATION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  RESEARCH: [
    [SNO, RESEARCH_TOPIC, STAKEHOLDER, STAKEHOLDER_NAME, PLAIN_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, RESEARCH_TOPIC, STAKEHOLDER, STAKEHOLDER_NAME, DEPARTMENT, PLAIN_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  SEMINAR: [
    [SNO, SEMINAR_TITLE, PLAIN_DESCRIPTION, SPEAKER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, SEMINAR_TITLE, PLAIN_DESCRIPTION, SPEAKER, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  SPORTS: [
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, EVENT_NAME, EVENT_DESCRIPTION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  SYMPOSIUM: [
    [SNO, EVENT_NAME, PLAIN_DESCRIPTION, STAKEHOLDER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, EVENT_NAME, PLAIN_DESCRIPTION, DEPARTMENT, STAKEHOLDER, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  WORKSHOP: [
    [SNO, TITLE, DURATION, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
    [SNO, TITLE, DURATION, DEPARTMENT, DATE, ACADEMIC_YEAR, LINKEDIN_URL],
  ],
  // --- unchanged audit layouts -------------------------------------------
  FDP: [GENERAL_ACTIVITY, DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER],
  STTP: [GENERAL_ACTIVITY, DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER],
  TECH_FEST: [DEFAULT_GENERAL, DEFAULT_DEPARTMENTAL],
  CULTURAL: [GENERAL_ACTIVITY_WITH_STAKEHOLDER, DEPARTMENTAL_ACTIVITY],
  CLUB: [GENERAL_ACTIVITY_WITH_STAKEHOLDER, DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER],
  CAMPUS: [GENERAL_ACTIVITY_WITH_STAKEHOLDER, DEPARTMENTAL_ACTIVITY],
  WEBINAR: [GENERAL_ACTIVITY, DEPARTMENTAL_ACTIVITY_WITH_STAKEHOLDER],
  ACHIEVEMENT: [achievement(), achievement({ department: true })],
};

export function normalizeScope(scope) {
  return scope === DEPARTMENTAL ? DEPARTMENTAL : GENERAL;
}

export function normalizeCategory(category) {
  return String(category || "").trim().toUpperCase() || null;
}

// The single primary category of one projected record.
export function categoryOfRecord(record) {
  if (!record) return null;
  const categories = record.categories || [];
  if (categories.length > 0) {
    const first = categories[0];
    return normalizeCategory(typeof first === "string" ? first : first.code);
  }
  return normalizeCategory(record.category_code);
}

export function reportColumns(category, scope) {
  const schema = CATEGORY_SCHEMAS[normalizeCategory(category)];
  if (!schema) return scope === DEPARTMENTAL ? DEFAULT_DEPARTMENTAL : DEFAULT_GENERAL;
  return schema[scope === DEPARTMENTAL ? 1 : 0];
}

// One table has one column set: a category-filtered report uses that
// category's schema, a mixed result set uses the plain activity layout.  Rows
// are never duplicated or dropped because of the column choice.
export function reportColumnsForRecords(records, scope) {
  const codes = new Set((records || []).map(categoryOfRecord).filter(Boolean));
  if (codes.size === 1) return reportColumns([...codes][0], scope);
  return reportColumns(null, scope);
}

export function columnLabels(columns) {
  return columns.map((column) => column.label);
}