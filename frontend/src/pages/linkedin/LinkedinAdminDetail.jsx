import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import {
  DEPARTMENTAL, columnLabels, reportColumns,
} from "../../lib/reportSchema";
import { isoDate, joinDateRange, splitDateRange } from "../../lib/dates";

// Validator editor.  The fields on screen are GENERATED from the record's own
// category report schema (`reportColumns`), so the Admin sees exactly the
// columns the user-facing report shows for that category -- Chief Guest for a
// Conference, Speaker and Description for a Seminar, Signed MOU With and
// Purpose for an Industry activity, and so on.  Nothing here is hard-coded per
// category, so a schema change needs no Admin change.
//
// Every control maps to the one canonical PATCH endpoint against the single
// reportable database, so an edit is visible immediately on every user surface
// and never creates a second record.

// Which columns the Admin may type into, and the control each one gets.
// A column not listed here is derived from the row and shown read-only.
const EDITABLE_COLUMNS = {
  title: { control: "text", span: 2 },
  chief_guest: { control: "text" },
  speaker: { control: "text" },
  alumni_name: { control: "text" },
  alumni_department: { control: "text" },
  topic_theme: { control: "text" },
  stakeholder_name: { control: "text" },
  mou_with: { control: "text", span: 2 },
  location: { control: "text", span: 2 },
  duration: { control: "text" },
  event_description: { control: "textarea", span: 2 },
  purpose: { control: "textarea", span: 2 },
  // An Internship's "Date (From-To)" needs two real date inputs, not one
  // free-text box, so the From / To parts are edited separately.
  date_range: { control: "date-range", span: 2 },
  // The report's single Date column is the canonical activity date.
  report_date: { control: "date" },
  academic_year_display: { control: "academic-year" },
  // Curated vocabularies already on the record: kept as the existing + Add /
  // − Remove multi-value controls.
  department_display: { control: "departments" },
  stakeholder_display: { control: "stakeholders" },
  name: { control: "report-name", span: 2 },
  achievement_description: { control: "report-description", span: 2 },
  // Award Category follows the one primary category; the category picker below
  // is its editor.
  award_category: { control: "category" },
  // The LinkedIn URL is provenance: shown, never editable.
  post_url: { control: "readonly-url" },
};

//: Report columns whose value is a stored column of the record rather than a
//: derived one.  ``draft`` is where the input is bound, ``record`` is the key
//: the current value is read from, and ``payload`` is the key the canonical
//: PATCH accepts for it.
const DRAFT_KEYS = {
  title: { draft: "title", record: "title", payload: "title" },
  report_date: { draft: "activity_date", record: "activity_date", payload: "activity_date" },
  academic_year_display: { draft: "academic_year", record: "academic_year", payload: "academic_year" },
  name: { draft: "report_name", record: "name", payload: "report_name" },
  achievement_description: {
    draft: "report_description", record: "achievement_description", payload: "report_description",
  },
};

// ---------------------------------------------------------------------------
// MultiDropdown — one or more dropdown rows with + Add / − Remove controls.
// `values`     : string[] of currently selected codes (may be empty).
// `rawOptions` : Array<{code, name}> | string[] — the vocabulary to pick from.
// `onChange`   : (newValues: string[]) => void
// `fieldLabel` : accessible label for the first row (aria-label on <select>).
// ---------------------------------------------------------------------------
function MultiDropdown({ values, rawOptions, onChange, fieldLabel, emptyLabel = "None", filterOptions }) {
  // Normalise: accept both {code,name}[] and string[] from the options endpoint.
  const opts = rawOptions.map((o) =>
    typeof o === "string" ? { code: o, name: o } : o,
  );

  const selectedSet = new Set(values.filter(Boolean));

  // Keep a value that is already stored selectable even when it is not in the
  // current vocabulary, so opening the form never silently drops one.
  const visible = filterOptions ? opts.filter(filterOptions) : opts;

  const addRow = () => onChange([...values, ""]);

  const removeRow = (idx) => onChange(values.filter((_, i) => i !== idx));

  const changeRow = (idx, val) => {
    const next = [...values];
    next[idx] = val;
    onChange(next);
  };

  return (
    <div className="multi-field">
      {values.map((val, i) => (
        // key on index is safe here: we never reorder rows, only append/remove.
        <div key={i} className="multi-row">
          <select
            value={val}
            onChange={(e) => changeRow(i, e.target.value)}
            aria-label={i === 0 ? fieldLabel : `${fieldLabel} ${i + 1}`}>
            <option value="">{emptyLabel}</option>
            {visible.map((o) => (
              <option
                key={o.code}
                value={o.code}
                // Disable options already chosen in another row to prevent duplicates.
                disabled={selectedSet.has(o.code) && o.code !== val}>
                {o.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            className="ghost danger multi-remove"
            onClick={() => removeRow(i)}
            aria-label={`Remove ${fieldLabel} ${i + 1}`}>
            −
          </button>
        </div>
      ))}
      <button
        type="button"
        className="ghost multi-add"
        onClick={addRow}
        aria-label={`Add ${fieldLabel}`}>
        + Add
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Helpers for comparing array fields without caring about order.
// ---------------------------------------------------------------------------
function arraysEqual(a, b) {
  const sa = [...a].filter(Boolean).sort();
  const sb = [...b].filter(Boolean).sort();
  return JSON.stringify(sa) === JSON.stringify(sb);
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function LinkedinAdminDetail() {
  const { id } = useParams();
  const [record, setRecord] = useState(null);
  const [options, setOptions] = useState({
    categories: [], departments: [], stakeholders: [], academic_years: [],
    statuses: [], review_statuses: [],
  });
  const [draft, setDraft] = useState(null);
  const [state, setState] = useState("loading");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [formError, setFormError] = useState("");

  const load = () => {
    setState("loading");
    setRecord(null);
    setDraft(null);
    setFeedback(null);
    adminApi.get(`/api/admin/linkedin/activities/${id}`)
      .then((body) => {
        setRecord(body);
        setDraft(buildDraft(body));
        setState("ready");
      })
      .catch((err) => {
        setState(err && /not found/i.test(String(err.message)) ? "notfound" : "error");
      });
  };

  useEffect(() => { load(); }, [id]);

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/linkedin/options").then((body) => {
      if (active) setOptions(body);
    }).catch(() => {});
    return () => { active = false; };
  }, []);

  function buildDraft(rec) {
    // Normalize: any non-APPROVED status is treated as NOT_APPROVED in the UI
    // so the editor only ever shows these two options.
    const rawStatus = rec.review_status || rec.approval || "UNREVIEWED";
    return {
      // Keep full arrays so the multi-value UI can show all existing values.
      categories:  (rec.categories  || []).filter(Boolean),
      departments: (rec.departments || []).filter(Boolean),
      stakeholders: (rec.stakeholders || []).filter(Boolean),
      title: rec.title || "",
      activity_date: rec.activity_date || "",
      academic_year: rec.academic_year || "",
      report_name: rec.name || rec.report_name || "",
      report_description:
        rec.achievement_description || rec.report_description || "",
      // Derived report columns carry no draft state until the admin types: an
      // untouched input shows, and does not overwrite, the reported value.
      fields: {},
      // Store as APPROVED or NEEDS_REVIEW (NOT_APPROVED maps to NEEDS_REVIEW)
      review_status: rawStatus === "APPROVED" ? "APPROVED" : "NEEDS_REVIEW",
    };
  }

  // One activity has exactly one primary category, so the category-specific
  // report fields follow the first selected category.
  const categoryCode = (draft?.categories || []).filter(Boolean)[0] || "";
  
  function isRealDepartment(option) {
    return Boolean(option && option.code) && option.code !== "General";
  }

  function isDepartmental(departments) {
    return (departments || []).some((d) => d && d !== "General");
  }

  // The scope shown is the one the draft would report under right now, while the
  // scope the record is currently stored under is what validation protects: a
  // record already reported department-wise may not lose its last department.
  const scope = draft && isDepartmental(draft.departments) ? DEPARTMENTAL : "general";
  
  const reportColumnsForRecord = reportColumns(categoryCode, scope);
  const reportColumnLabels = columnLabels(reportColumnsForRecord);
  // The columns this category actually reports, minus the curated vocabularies
  // and the category itself, which the validation group above already edits.
  const editableColumns = useMemo(
    () => reportColumnsForRecord.filter(
      (column) => column.field
        && column.field !== "department_display"
        && column.field !== "stakeholder_display"
        && column.field !== "award_category",
    ),
    [reportColumnsForRecord],
  );

  function currentFieldValue(field) {
    // A From-To range is held as two slots instead of one string. A lone string
    // cannot say which end is set, so filling or clearing one box would quietly
    // move the other end's value into it. The joined string is derived only
    // where the value is really consumed: validation and the PATCH payload.
    if (field === "date_range" && draft.date_range) {
      return joinDateRange(draft.date_range.from, draft.date_range.to);
    }
    // Show the value the report shows today, so an edit corrects what the admin
    // can actually see rather than a hidden raw value.
    if (draft.fields && draft.fields[field] !== undefined) {
      return draft.fields[field];
    }
    return (record && record[field]) || "";
  }

  function onField(name, value) {
    setDraft((current) => ({ ...current, [name]: value }));
  }

  function onFieldList(name, values) {
    setDraft((current) => ({ ...current, [name]: values }));
  }

  // One end of the From-To range moved. The other end is read from the LATEST
  // draft inside the updater rather than from this render's closure, so picking
  // From can never overwrite To (or the reverse) even when React batches two
  // edits together.
  function onDateRange(end, value, shown) {
    setDraft((current) => {
      const previous = current.date_range || shown;
      return {
        ...current,
        date_range: end === "from"
          ? { from: value, to: previous.to }
          : { from: previous.from, to: value },
      };
    });
  }

  // A derived report column has no slot on the record, so an edit to one is held
  // apart until save; an untouched column keeps showing the reported value.
  function onDerivedField(field, value) {
    setDraft((current) => ({
      ...current,
      fields: { ...current.fields, [field]: value },
    }));
  }

  // Render one report column with the control its kind calls for.  The whole
  // form is built from this, so a new category column appears automatically.
  function renderColumn(column) {
    const field = column.field;
    const spec = EDITABLE_COLUMNS[field] || { control: "readonly" };
    const span = spec.span === 2 ? " span-2" : "";
    const label = (
      <span className="field-label">{column.label}</span>
    );

    if (spec.control === "departments") {
      return (
        <label key={field} className={`field${span}`}>
          {label}
          <MultiDropdown
            values={draft.departments}
            rawOptions={options.departments || []}
            onChange={(vals) => onFieldList("departments", vals)}
            fieldLabel={column.label}
            filterOptions={isRealDepartment}
          />
        </label>
      );
    }
    if (spec.control === "stakeholders") {
      return (
        <label key={field} className={`field${span}`}>
          {label}
          <MultiDropdown
            values={draft.stakeholders}
            rawOptions={options.stakeholders || []}
            onChange={(vals) => onFieldList("stakeholders", vals)}
            fieldLabel={column.label}
          />
        </label>
      );
    }
    if (spec.control === "category") {
      return (
        <div key={field} className={`field${span}`}>
          {label}
          <p className="value-static">{record.award_category || "—"}</p>
        </div>
      );
    }
    if (spec.control === "date") {
      return (
        <label key={field} className={`field${span}`}>
          {label}
          {/* Shown parsed, because a date input only ever renders a full ISO
              date and would blank a reported "15 January 2026". The draft keeps
              the raw stored value until the admin actually picks, so an untouched
              date is never rewritten by an unrelated save. */}
          <input
            type="date"
            value={isoDate(draft.activity_date)}
            onChange={(e) => onField("activity_date", e.target.value)}
            aria-label={column.label} />
        </label>
      );
    }
    if (spec.control === "academic-year") {
      return (
        <label key={field} className={`field${span}`}>
          {label}
          <select
            value={draft.academic_year || ""}
            onChange={(e) => onField("academic_year", e.target.value)}
            aria-label={column.label}>
            <option value="">Not assigned</option>
            {(options.academic_years || []).map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>
      );
    }
    if (spec.control === "date-range") {
      // Untouched until the admin picks an end: show what the report shows.
      const [shownFrom, shownTo] = splitDateRange(currentFieldValue(field));
      const shown = { from: shownFrom, to: shownTo };
      const { from, to } = draft.date_range || shown;
      return (
        <div key={field} className={`field${span}`}>
          {label}
          <div className="date-range">
            <input
              type="date"
              value={from}
              onChange={(e) => onDateRange("from", e.target.value, shown)}
              aria-label={`${column.label} from`} />
            <span className="date-range-sep">to</span>
            <input
              type="date"
              value={to}
              onChange={(e) => onDateRange("to", e.target.value, shown)}
              aria-label={`${column.label} to`} />
          </div>
        </div>
      );
    }
    if (spec.control === "textarea") {
      const stored = DRAFT_KEYS[field];
      const set = stored
        ? (value) => onField(stored.draft, value)
        : (value) => onDerivedField(field, value);
      return (
        <label key={field} className={`field${span}`}>
          {label}
          <textarea
            rows={4}
            value={stored ? (draft[stored.draft] || "") : currentFieldValue(field)}
            onChange={(e) => set(e.target.value)}
            aria-label={column.label} />
        </label>
      );
    }
    if (spec.control === "report-name" || spec.control === "report-description") {
      const draftKey = DRAFT_KEYS[field].draft;
      const long = spec.control === "report-description";
      return (
        <label key={field} className={`field${span}`}>
          {label}
          {long ? (
            <textarea
              rows={4}
              value={draft[draftKey] || ""}
              onChange={(e) => onField(draftKey, e.target.value)}
              aria-label={column.label} />
          ) : (
            <input
              type="text"
              value={draft[draftKey] || ""}
              onChange={(e) => onField(draftKey, e.target.value)}
              aria-label={column.label} />
          )}
        </label>
      );
    }
    if (spec.control === "readonly-url") {
      return (
        <div key={field} className={`field${span}`}>
          {label}
          {record.post_url ? (
            <a className="link" href={record.post_url} target="_blank" rel="noreferrer">
              {record.post_url}
            </a>
          ) : (
            <p className="value-static">Not linked</p>
          )}
        </div>
      );
    }
    if (spec.control === "text") {
      // A single-line report value: a stored column where one exists, otherwise
      // a derived column the admin is pinning.
      const stored = DRAFT_KEYS[field];
      const set = stored
        ? (value) => onField(stored.draft, value)
        : (value) => onDerivedField(field, value);
      return (
        <label key={field} className={`field${span}`}>
          {label}
          <input
            type="text"
            value={stored ? (draft[stored.draft] || "") : currentFieldValue(field)}
            onChange={(e) => set(e.target.value)}
            aria-label={column.label} />
        </label>
      );
    }
    // A derived column with no editor yet: shown, never silently editable.
    return (
      <div key={field} className={`field${span}`}>
        {label}
        <p className="value-static">{record[field] || "—"}</p>
      </div>
    );
  }

  function validateDraft() {
    if (draft.academic_year && !/^\d{4}-\d{2}$/.test(draft.academic_year)) {
      return "Academic year must look like 2025-26.";
    }
    // "General" is the general layout's placeholder for "no department", never a
    // department an admin may assign: it would put an invalid value in a
    // departmental report.  Leaving the list empty is fine and simply reports
    // the activity under the general layout.
    const [fromPart, toPart] = splitDateRange(currentFieldValue("date_range"));
    if (fromPart && toPart && fromPart > toPart) {
      return "The Date (From) value cannot be after Date (To).";
    }
    return "";
  }

  async function save() {
    if (busy || !draft || !record) return;
    const problem = validateDraft();
    if (problem) { setFormError(problem); return; }
    setBusy(true);
    setFormError("");
    setFeedback(null);
    const payload = {};

    // --- array fields: compare sorted, send clean array ---
    const draftCats = draft.categories.filter(Boolean);
    if (!arraysEqual(draftCats, record.categories || [])) {
      payload.categories = draftCats;
    }
    const draftDepts = draft.departments.filter(Boolean);
    if (!arraysEqual(draftDepts, record.departments || [])) {
      payload.departments = draftDepts;
    }
    const draftStakeholders = draft.stakeholders.filter(Boolean);
    if (!arraysEqual(draftStakeholders, record.stakeholders || [])) {
      payload.stakeholders = draftStakeholders;
    }

    // --- one entry per column the category's report actually shows ---
    editableColumns.forEach((column) => {
      const field = column.field;
      // The LinkedIn URL is immutable provenance: shown, never sent.
      if (field === "post_url") return;

      const stored = DRAFT_KEYS[field];
      if (stored) {
        const edited = draft[stored.draft] || "";
        const shown = record[stored.record] || "";
        if (edited !== shown) {
          payload[stored.payload] = edited;
        }
        return;
      }

      // A derived column: pinned only when the admin changed what the report
      // currently shows, and cleared by saving an empty value.
      const shown = record[field] || "";
      const edited = currentFieldValue(field);
      if (edited !== shown) {
        payload[field] = edited || "";
      }
    });

    // Compare normalized statuses: draft is always APPROVED or NEEDS_REVIEW
    const currentApproval = record.review_status === "APPROVED" ? "APPROVED" : "NEEDS_REVIEW";
    if (draft.review_status !== currentApproval) {
      payload.review_status = draft.review_status;
    }

    if (Object.keys(payload).length === 0) {
      setFeedback({ kind: "ok", text: "No changes to save." });
      setBusy(false);
      return;
    }
    payload._note = "admin manual correction";
    try {
      const updated = await adminApi.patch(`/api/admin/linkedin/activities/${id}`, payload);
      const last = (updated.validation_history || []).slice(-1)[0];
      setRecord(updated);
      setDraft(buildDraft(updated));
      setFeedback(last
        ? { kind: "ok", text: `Saved — ${last.field}: "${String(last.old ?? "—")}" → "${String(last.new ?? "—")}"` }
        : { kind: "ok", text: "Saved. No field values changed." });
    } catch (err) {
      setFormError(err.message || "Unable to save changes.");
    } finally {
      setBusy(false);
    }
  }

  if (state === "loading") return <p className="muted state">Loading record...</p>;
  if (state === "notfound") return (
    <div className="page">
      <p className="error state">Record not found.</p>
      <p className="back-row"><Link to="/admin/linkedin/records">← Back to records</Link></p>
    </div>
  );
  if (state === "error") return (
    <div className="page">
      <p className="error state">Unable to load this record.</p>
      <p className="back-row"><Link to="/admin/linkedin/records">← Back to records</Link></p>
    </div>
  );

  return (
    <div className="page">
      <p className="back-row"><Link to="/admin/linkedin/records">← Back to records</Link></p>
      <div className="title-row">
        <h2 className="record-title">{record.title || record.name || record.achievement_description}</h2>
      </div>
      {formError && <p className="error state" role="alert">{formError}</p>}
      {feedback && feedback.kind === "ok" && <p className="ok state" role="status">{feedback.text}</p>}

      <Card title="Edit Record">
        {draft && (
          <form className="admin-form" onSubmit={(e) => { e.preventDefault(); save(); }} noValidate>
            <p className="muted note">
              This record is reported as{" "}
              <strong>{categoryCode || "an uncategorised activity"}</strong> ({scope === DEPARTMENTAL ? "department-wise" : "general"}).
              The report shows these columns: {reportColumnLabels.join(" | ")}
            </p>

            {/* Classification and the curated vocabularies.  These decide which
                report columns below apply and are shared by every category, so
                they are edited once here rather than per category. */}
            <p className="field-label section-label">Category and validation</p>
            <div className="form-grid">
              <label className="field">
                <span className="field-label">Award Category</span>
                <MultiDropdown
                  values={draft.categories}
                  rawOptions={options.categories || []}
                  onChange={(vals) => onFieldList("categories", vals)}
                  fieldLabel="Award Category"
                />
              </label>

              <label className="field">
                <span className="field-label">Department</span>
                <MultiDropdown
                  values={draft.departments}
                  rawOptions={options.departments || []}
                  onChange={(vals) => onFieldList("departments", vals)}
                  fieldLabel="Department"
                  filterOptions={isRealDepartment}
                />
              </label>

              <label className="field">
                <span className="field-label">Stakeholder</span>
                <MultiDropdown
                  values={draft.stakeholders}
                  rawOptions={options.stakeholders || []}
                  onChange={(vals) => onFieldList("stakeholders", vals)}
                  fieldLabel="Stakeholder"
                />
              </label>

              <label className="field">
                <span className="field-label">Status</span>
                {/* UI shows only Approved / Not Approved; internally NOT_APPROVED maps to NEEDS_REVIEW */}
                <select
                  value={draft.review_status === "APPROVED" ? "APPROVED" : "NOT_APPROVED"}
                  onChange={(e) => onField("review_status", e.target.value === "APPROVED" ? "APPROVED" : "NEEDS_REVIEW")}
                  aria-label="Status">
                  <option value="APPROVED">Approved</option>
                  <option value="NOT_APPROVED">Not Approved</option>
                </select>
              </label>
            </div>

            {/* The category's own report columns, generated from its schema. */}
            <p className="field-label section-label">
              Report fields — {categoryCode || "uncategorised"}
            </p>
            <div className="form-grid">
              {editableColumns.map(renderColumn)}
            </div>

            <div className="form-actions">
              <button type="button" className="ghost" disabled={busy}
                onClick={() => setDraft(buildDraft(record))}>
                Discard changes
              </button>
              <button type="submit" className="primary" disabled={busy}>
                {busy ? "Saving..." : "Save"}
              </button>
            </div>
          </form>
        )}
      </Card>
    </div>
  );
}