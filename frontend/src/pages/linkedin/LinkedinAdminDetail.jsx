import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { Field, JsonValue, Tags } from "../../components/detail";
import { categoryName, confidenceInfo, statusTone } from "../../lib/linkedin";

function Pill({ value }) {
  return <span className={`pill ${statusTone(value)}`}>{value || "—"}</span>;
}

function yesNo(value) {
  return value ? "Yes" : value === 0 ? "No" : "—";
}

function HistoryTable({ history }) {
  if (!history || history.length === 0) {
    return <p className="muted">No manual corrections recorded yet.</p>;
  }
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th>Field</th><th>Before</th><th>After</th><th>By</th><th>When</th><th>Note</th>
          </tr>
        </thead>
        <tbody>
          {history.map((entry, i) => (
            <tr key={i}>
              <td><code>{entry.field}</code></td>
              <td className="history-old">{String(entry.old ?? "—")}</td>
              <td className="history-new">{String(entry.new ?? "—")}</td>
              <td>{entry.by}</td>
              <td>{entry.at}</td>
              <td>{entry.note || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function LinkedinAdminDetail() {
  const { id } = useParams();
  const [record, setRecord] = useState(null);
  const [options, setOptions] = useState({ categories: [], departments: [], stakeholders: [], academic_years: [], statuses: [], review_statuses: [] });
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
    return {
      title: rec.title || "",
      description: rec.description || "",
      activity_date: rec.activity_date || "",
      academic_year: rec.academic_year || "",
      categories: (rec.categories || [])[0] || "",
      departments: (rec.departments || [])[0] || "",
      stakeholders: (rec.stakeholders || [])[0] || "",
      reportable_status: rec.reportable_status || "",
      review_status: rec.review_status || "",
      note: "",
    };
  }

  function onField(name, value) {
    setDraft((current) => ({ ...current, [name]: value }));
  }

  function validateDraft() {
    if (draft.reportable_status === "REPORTABLE" && !draft.title.trim()) {
      return "A reportable activity needs a title.";
    }
    if (draft.academic_year && !/^\d{4}-\d{2}$/.test(draft.academic_year)) {
      return "Academic year must look like 2025-26.";
    }
    if (draft.reportable_status === "REPORTABLE" && record && record.reportable_status !== "REPORTABLE") {
      return "Use 'Save & Publish' to make this record publicly REPORTABLE.";
    }
    return "";
  }

  async function save() {
    if (busy || !draft) return;
    const problem = validateDraft();
    if (problem) { setFormError(problem); return; }
    setBusy(true);
    setFormError("");
    setFeedback(null);
    const payload = {
      title: draft.title,
      description: draft.description,
      activity_date: draft.activity_date || null,
      academic_year: draft.academic_year || null,
      categories: draft.categories ? [draft.categories] : [],
      departments: draft.departments ? [draft.departments] : [],
      stakeholders: draft.stakeholders ? [draft.stakeholders] : [],
      reportable_status: draft.reportable_status,
      review_status: draft.review_status,
      _note: draft.note.trim() || "admin manual correction",
    };
    try {
      const updated = await adminApi.patch(`/api/admin/linkedin/activities/${id}`, payload);
      const last = (updated.validation_history || []).slice(-1)[0];
      setRecord(updated);
      setDraft(buildDraft(updated));
      setFeedback(last
        ? { kind: "ok", text: `Saved — ${last.field}: “${String(last.old ?? "—")}” → “${String(last.new ?? "—")}”` }
        : { kind: "ok", text: "Saved. No field values changed." });
    } catch (err) {
      setFormError(err.message || "Unable to save changes.");
    } finally {
      setBusy(false);
    }
  }

  async function publish() {
    if (busy || !draft) return;
    const problem = validateDraft();
    if (problem) { setFormError(problem); return; }
    setBusy(true);
    setFormError("");
    setFeedback(null);
    const payload = {
      title: draft.title,
      description: draft.description,
      activity_date: draft.activity_date || null,
      academic_year: draft.academic_year || null,
      categories: draft.categories ? [draft.categories] : [],
      departments: draft.departments ? [draft.departments] : [],
      stakeholders: draft.stakeholders ? [draft.stakeholders] : [],
      _note: draft.note.trim() || "admin save & publish",
    };
    try {
      const updated = await adminApi.post(`/api/admin/linkedin/activities/${id}/publish`, payload);
      const last = [...(updated.validation_history || [])].reverse()
        .find((entry) => entry.field === "reportable_status");
      setRecord(updated);
      setDraft(buildDraft(updated));
      setFeedback(last
        ? { kind: "ok", text: `Published — ${updated.activity_id} is now PUBLIC REPORTABLE (“${String(last.old ?? "—")}” → “${String(last.new ?? "—")}”).` }
        : { kind: "ok", text: `Saved — ${updated.activity_id} is already published and publicly visible.` });
    } catch (err) {
      setFormError(err.message || "Unable to publish this record.");
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

  const confidence = confidenceInfo(record.evidence_score);

  return (
    <div className="page">
      <p className="back-row"><Link to="/admin/linkedin/records">← Back to records</Link></p>
      <div className="title-row">
        <h2 className="record-title">{record.title}</h2>
        <div className="row-actions">
          <Pill value={record.reportable_status} />
          <Pill value={record.review_status || "UNREVIEWED"} />
          {Boolean(record.is_manually_validated) && <span className="pill good">Manually validated</span>}
        </div>
      </div>
      <p className="muted">{record.activity_id} &middot; {record.category_evidence ? "evidence attached" : "no evidence"}</p>

      {formError && <p className="error state" role="alert">{formError}</p>}
      {feedback && feedback.kind === "ok" && <p className="ok state" role="status">{feedback.text}</p>}

      <div className="detail-grid">
        <Card title="Source & Provenance">
          <Field label="Source" value={record.post_url ? <a href={record.post_url} target="_blank" rel="noreferrer">Open LinkedIn post</a> : "No source link"} />
          <Field label="Source Type" value={record.provenance.source} />
          <Field label="Workbook" value={record.provenance.source_workbook} />
          <Field label="Sheet" value={record.provenance.source_sheet} />
          <Field label="Row" value={record.provenance.source_row} />
          <Field label="Occurrences" value={record.provenance.occurrence_count} />
          <Field label="Occurrence IDs" value={record.provenance.source_occurrence_ids && JSON.stringify(record.provenance.source_occurrence_ids)} />
          <Field label="Collected At" value={record.provenance.collected_at} />
          <Field label="Resolved Via" value={record.provenance.resolved_via} />
          <Field label="LinkedIn URN" value={record.provenance.activity_urn_id} />
          <Field label="Staging Post ID" value={record.staging_post_id} />
          <Field label="Staging Candidate ID" value={record.staging_candidate_id} />
        </Card>

        <Card title="Classification Decisions">
          <Field label="Reportable Status" value={<Pill value={record.reportable_status} />} />
          <Field label="Classification Status" value={<Pill value={record.classification_status} />} />
          <Field label="Review Status" value={<Pill value={record.review_status || "UNREVIEWED"} />} />
          <Field label="Decision Reason" value={record.reason} />
          <Field label="Unclear Reason" value={record.unclear_reason} />
          <Field label="Kind" value={record.kind} />
          <Field label="Multi-label" value={yesNo(record.multi_label)} />
          <Field label="Flags" value={<Tags items={record.flags} />} />
          <Field label="Manually Validated" value={yesNo(record.is_manually_validated)} />
        </Card>
      </div>

      <div className="chart-grid">
        <Card title="Category">
          <Field label="Assigned Categories" value={<Tags items={record.categories.map((c) => categoryName(c, options.categories))} />} />
          <Field label="Candidate Categories" value={<Tags items={record.category_candidates} />} />
          <h3>Category Evidence</h3>
          <JsonValue value={record.category_evidence} />
        </Card>
        <Card title="Department">
          <Field label="Assigned Departments" value={<Tags items={record.departments} />} />
          <Field label="Public Display" value={<Tags items={record.department_display} />} />
          <Field label="Candidate Departments" value={<Tags items={record.department_candidates} />} />
          <h3>Department Evidence</h3>
          <JsonValue value={record.department_evidence} />
        </Card>
        <Card title="Stakeholder">
          <Field label="Assigned Stakeholders" value={<Tags items={record.stakeholders} />} />
          <Field label="Candidate Stakeholders" value={<Tags items={record.stakeholder_candidates} />} />
          <h3>Stakeholder Evidence</h3>
          <JsonValue value={record.stakeholder_evidence} />
        </Card>
      </div>

      <div className="detail-grid">
        <Card title="Date & Academic Year">
          <Field label="Activity Date" value={record.activity_date} />
          <Field label="Date Status" value={<Pill value={record.date_status} />} />
          <Field label="Academic Year" value={record.academic_year} />
          <h3>Date Evidence</h3>
          <JsonValue value={record.date_evidence} />
        </Card>
        <Card title="Confidence & Communication">
          <Field label="Evidence Score" value={confidence ? `${confidence.label} (${record.evidence_score}/10)` : "—"} />
          <Field label="Communication Type" value={record.communication_type} />
          <h3>Communication Evidence</h3>
          <JsonValue value={record.communication_evidence} />
        </Card>
        <Card title="Description">
          <p className="body-text">{record.description || "No description available."}</p>
        </Card>
      </div>

      <Card title="Edit Record">
        {draft && (
          <form className="admin-form" onSubmit={(e) => { e.preventDefault(); save(); }}>
            <div className="form-grid">
              <label className="field span-2">
                <span className="field-label">Title</span>
                <input type="text" value={draft.title} onChange={(e) => onField("title", e.target.value)} aria-label="Title" />
              </label>
              <label className="field span-2">
                <span className="field-label">Description</span>
                <textarea value={draft.description} rows={4}
                  onChange={(e) => onField("description", e.target.value)} aria-label="Description" />
              </label>
              <label className="field">
                <span className="field-label">Reportable Status</span>
                <select value={draft.reportable_status} onChange={(e) => onField("reportable_status", e.target.value)} aria-label="Reportable status">
                  {(options.statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Review Status</span>
                <select value={draft.review_status} onChange={(e) => onField("review_status", e.target.value)} aria-label="Review status">
                  {(options.review_statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Category</span>
                <select value={draft.categories} onChange={(e) => onField("categories", e.target.value)} aria-label="Category">
                  <option value="">None</option>
                  {(options.categories || []).map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Department</span>
                <select value={draft.departments} onChange={(e) => onField("departments", e.target.value)} aria-label="Department">
                  <option value="">None</option>
                  {(options.departments || []).map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Stakeholder</span>
                <select value={draft.stakeholders} onChange={(e) => onField("stakeholders", e.target.value)} aria-label="Stakeholder">
                  <option value="">None</option>
                  {(options.stakeholders || []).map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Activity Date</span>
                <input type="date" value={draft.activity_date || ""} onChange={(e) => onField("activity_date", e.target.value)} aria-label="Activity date" />
              </label>
              <label className="field">
                <span className="field-label">Academic Year</span>
                <select value={draft.academic_year} onChange={(e) => onField("academic_year", e.target.value)} aria-label="Academic year">
                  <option value="">Not assigned</option>
                  {(options.academic_years || []).map((y) => <option key={y} value={y}>{y}</option>)}
                </select>
              </label>
              <label className="field span-2">
                <span className="field-label">Reviewer Note</span>
                <input type="text" value={draft.note} placeholder="Optional note recorded in validation history"
                  onChange={(e) => onField("note", e.target.value)} aria-label="Reviewer note" />
              </label>
            </div>
            <div className="form-actions">
              <button type="button" className="ghost" disabled={busy}
                onClick={() => setDraft(buildDraft(record))}>Discard changes</button>
              <button type="submit" className="ghost" disabled={busy}>
                {busy ? "Saving..." : "Save changes"}
              </button>
              <button type="button" className="primary" disabled={busy} onClick={publish}>
                {busy ? "Publishing..." : "Save & Publish"}
              </button>
            </div>
          </form>
        )}
      </Card>

      <Card title="Validation History">
        <HistoryTable history={(record.validation_history || []).slice().reverse()} />
      </Card>
    </div>
  );
}