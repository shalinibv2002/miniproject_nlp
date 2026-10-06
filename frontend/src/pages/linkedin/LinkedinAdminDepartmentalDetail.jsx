import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { ACHIEVEMENT, columnLabels, reportColumns } from "../../lib/reportSchema";
import { isoDate } from "../../lib/dates";

// Edit screen for a Departmental Activity.  Uses the same canonical
// PATCH /api/admin/linkedin/activities/:id endpoint as the General Records
// editor, so any save is immediately reflected in the public report surfaces.
// Stakeholder, Department and Award Category support multiple values via the
// MultiDropdown component (same pattern as LinkedinAdminDetail).
//
// The report fields are category-specific: an ACHIEVEMENT reports Name and
// Achievement Description, every other category reports a Title.  This
// departmental editor always uses the departmental column set.

// ---------------------------------------------------------------------------
// MultiDropdown — identical helper used in LinkedinAdminDetail.
// ---------------------------------------------------------------------------
function MultiDropdown({ values, rawOptions, onChange, fieldLabel, emptyLabel = "None" }) {
  const opts = rawOptions.map((o) =>
    typeof o === "string" ? { code: o, name: o } : o,
  );

  const selectedSet = new Set(values.filter(Boolean));

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
        <div key={i} className="multi-row">
          <select
            value={val}
            onChange={(e) => changeRow(i, e.target.value)}
            aria-label={i === 0 ? fieldLabel : `${fieldLabel} ${i + 1}`}>
            <option value="">{emptyLabel}</option>
            {opts.map((o) => (
              <option
                key={o.code}
                value={o.code}
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

function arraysEqual(a, b) {
  const sa = [...a].filter(Boolean).sort();
  const sb = [...b].filter(Boolean).sort();
  return JSON.stringify(sa) === JSON.stringify(sb);
}

export default function LinkedinAdminDepartmentalDetail() {
  const { id } = useParams();
  const [record, setRecord] = useState(null);
  const [options, setOptions] = useState({
    categories: [], departments: [], stakeholders: [], academic_years: [],
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
    const rawStatus = rec.review_status || rec.approval || "UNREVIEWED";
    return {
      categories:   (rec.categories  || []).filter(Boolean),
      departments:  (rec.departments || []).filter(Boolean),
      stakeholders: (rec.stakeholders || []).filter(Boolean),
      title: rec.title || "",
      activity_date: rec.activity_date || "",
      academic_year: rec.academic_year || "",
      report_name:   rec.name || rec.report_name || "",
      report_description:
        rec.achievement_description || rec.report_description || "",
      review_status: rawStatus === "APPROVED" ? "APPROVED" : "NEEDS_REVIEW",
    };
  }

  // One activity has exactly one primary category, so the category-specific
  // report fields follow the first selected category.
  const categoryCode = (draft?.categories || []).filter(Boolean)[0] || "";
  const isAchievement = categoryCode === ACHIEVEMENT;
  const reportColumnLabels = columnLabels(reportColumns(categoryCode, "departmental"));

  function onField(name, value) {
    setDraft((current) => ({ ...current, [name]: value }));
  }

  function validateDraft() {
    if (draft.academic_year && !/^\d{4}-\d{2}$/.test(draft.academic_year)) {
      return "Academic year must look like 2025-26.";
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

    if ((draft.activity_date || "") !== (record.activity_date || "")) {
      payload.activity_date = draft.activity_date || null;
    }
    if ((draft.academic_year || "") !== (record.academic_year || "")) {
      payload.academic_year = draft.academic_year || null;
    }
    if (isAchievement) {
      const currentName = record.name || record.report_name || "";
      if ((draft.report_name || "") !== currentName) {
        payload.report_name = draft.report_name || "";
      }
      const currentDesc = record.achievement_description || record.report_description || "";
      if ((draft.report_description || "") !== currentDesc) {
        payload.report_description = draft.report_description || "";
      }
    } else {
      // The report Title of a non-achievement activity.
      if ((draft.title || "") !== (record.title || "")) {
        payload.title = draft.title || "";
      }
    }
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
      <p className="back-row"><Link to="/admin/linkedin/departmental">← Back to Departmental Activities</Link></p>
    </div>
  );
  if (state === "error") return (
    <div className="page">
      <p className="error state">Unable to load this record.</p>
      <p className="back-row"><Link to="/admin/linkedin/departmental">← Back to Departmental Activities</Link></p>
    </div>
  );

  // Exclude "General" from department options in the departmental editor.
  const deptOptions = (options.departments || []).filter((d) => d !== "General");

  return (
    <div className="page">
      <p className="back-row">
        <Link to="/admin/linkedin/departmental">← Back to Departmental Activities</Link>
      </p>
      <div className="title-row">
        <h2 className="record-title">
          {record.title || record.name || record.achievement_description}
        </h2>
      </div>
      {formError && <p className="error state" role="alert">{formError}</p>}
      {feedback && feedback.kind === "ok" && (
        <p className="ok state" role="status">{feedback.text}</p>
      )}

      <Card title="Edit Departmental Activity">
        {draft && (
          <form className="admin-form" onSubmit={(e) => { e.preventDefault(); save(); }}>
            <p className="muted note">
              Report columns for {categoryCode || "this activity"}:{" "}
              {reportColumnLabels.join(" | ")}
            </p>
            <div className="form-grid">

              {/* Stakeholder — multi-value */}
              <label className="field">
                <span className="field-label">Stakeholder</span>
                <MultiDropdown
                  values={draft.stakeholders}
                  rawOptions={options.stakeholders || []}
                  onChange={(vals) => onField("stakeholders", vals)}
                  fieldLabel="Stakeholder"
                />
              </label>

              {/* Department — multi-value (no General) */}
              <label className="field">
                <span className="field-label">Department</span>
                <MultiDropdown
                  values={draft.departments}
                  rawOptions={deptOptions}
                  onChange={(vals) => onField("departments", vals)}
                  fieldLabel="Department"
                />
              </label>

              {/* Award Category — multi-value (one primary category per activity) */}
              <label className="field">
                <span className="field-label">Award Category</span>
                <MultiDropdown
                  values={draft.categories}
                  rawOptions={options.categories || []}
                  onChange={(vals) => onField("categories", vals)}
                  fieldLabel="Award Category"
                />
              </label>

              {/* Category-specific report fields */}
              {isAchievement ? (
                <>
                  <label className="field span-2">
                    <span className="field-label">Name</span>
                    <input
                      type="text"
                      value={draft.report_name}
                      onChange={(e) => onField("report_name", e.target.value)}
                      aria-label="Name" />
                  </label>
                  <label className="field span-2">
                    <span className="field-label">Achievement Description</span>
                    <textarea
                      value={draft.report_description}
                      rows={4}
                      onChange={(e) => onField("report_description", e.target.value)}
                      aria-label="Achievement Description" />
                  </label>
                </>
              ) : (
                <label className="field span-2">
                  <span className="field-label">Title</span>
                  <input
                    type="text"
                    value={draft.title}
                    onChange={(e) => onField("title", e.target.value)}
                    aria-label="Title" />
                </label>
              )}

              {/* Date */}
              <label className="field">
                <span className="field-label">Date</span>
                {/* Shown parsed, because a date input only ever renders a full
                    ISO date and would blank a reported "15 January 2026". */}
                <input
                  type="date"
                  value={isoDate(draft.activity_date)}
                  onChange={(e) => onField("activity_date", e.target.value)}
                  aria-label="Date" />
              </label>

              {/* Academic Year */}
              <label className="field">
                <span className="field-label">Academic Year</span>
                <select
                  value={draft.academic_year}
                  onChange={(e) => onField("academic_year", e.target.value)}
                  aria-label="Academic Year">
                  <option value="">Not assigned</option>
                  {(options.academic_years || []).map((y) => (
                    <option key={y} value={y}>{y}</option>
                  ))}
                </select>
              </label>

              {/* Status */}
              <label className="field">
                <span className="field-label">Status</span>
                {/* UI shows only Approved / Not Approved; NOT_APPROVED maps to NEEDS_REVIEW internally */}
                <select
                  value={draft.review_status === "APPROVED" ? "APPROVED" : "NOT_APPROVED"}
                  onChange={(e) => onField("review_status", e.target.value === "APPROVED" ? "APPROVED" : "NEEDS_REVIEW")}
                  aria-label="Status">
                  <option value="APPROVED">Approved</option>
                  <option value="NOT_APPROVED">Not Approved</option>
                </select>
              </label>

              {/* LinkedIn URL — immutable provenance: shown as a read-only link, never editable */}
              <div className="field span-2">
                <span className="field-label">LinkedIn URL</span>
                {record.post_url ? (
                  <a className="link" href={record.post_url} target="_blank" rel="noreferrer">
                    {record.post_url}
                  </a>
                ) : (
                  <p className="value-static">Not linked</p>
                )}
              </div>

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
