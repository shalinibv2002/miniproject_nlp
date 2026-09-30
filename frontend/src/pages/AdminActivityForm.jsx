import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { adminApi } from "../services/api";
import { Card } from "../components/ui";
import { BEFORE_2021, PERIOD_LABELS } from "../lib/periods";

const PERIOD_OPTIONS = [
  { value: "", label: "Select academic period" },
  ...Object.entries(PERIOD_LABELS).map(([value, label]) => ({ value, label })),
  { value: BEFORE_2021, label: BEFORE_2021 },
];

const STAKEHOLDER_OPTIONS = [
  "Students", "Faculty", "Non-Teaching Staff", "Alumni", "Industry",
  "Parents", "Government and Agencies", "Community and Society",
];

export default function AdminActivityForm() {
  const { id } = useParams();
  const editing = Boolean(id);
  const navigate = useNavigate();

  const [departments, setDepartments] = useState([]);
  const [generalCategories, setGeneralCategories] = useState([]);
  const [departmentalCategories, setDepartmentalCategories] = useState([]);
  const [loading, setLoading] = useState(editing);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    title: "", description: "", activity_date: "", academic_year: "", scope: "general",
    department: "", category: "", stakeholder: "Students",
    achievement_outcome: "", student_name: "", register_number: "", source_url: "",
  });

  useEffect(() => {
    adminApi.get("/api/departments").then(setDepartments).catch(() => setDepartments([]));
    adminApi.get("/api/general-categories").then(setGeneralCategories).catch(() => setGeneralCategories([]));
  }, []);

  useEffect(() => {
    if (!editing) return undefined;
    let active = true;
    setLoading(true);
    adminApi.get(`/api/admin/activities/${id}`)
      .then((item) => {
        if (!active) return;
        setForm({
          title: item.title || "", description: item.description || "",
          activity_date: item.activity_date || "", academic_year: item.academic_year || "",
          scope: item.scope || (item.department === "General" ? "general" : "departmental"),
          department: item.department === "General" ? "" : (item.department || ""),
          category: item.category || "",
          stakeholder: item.stakeholder || "Students",
          achievement_outcome: item.achievement_outcome || "",
          student_name: "", register_number: "", source_url: item.source_url || "",
        });
        setLoading(false);
      })
      .catch((err) => { if (active) { setError(err.message || "Unable to load activity."); setLoading(false); } });
    return () => { active = false; };
  }, [id, editing]);

  useEffect(() => {
    if (form.scope !== "departmental") {
      setDepartmentalCategories([]);
      return undefined;
    }
    const suffix = form.department ? `?department=${encodeURIComponent(form.department)}` : "";
    adminApi.get(`/api/departmental-categories${suffix}`)
      .then(setDepartmentalCategories)
      .catch(() => setDepartmentalCategories([]));
  }, [form.scope, form.department]);

  const categoryOptions = useMemo(() => {
    if (form.scope === "general") return generalCategories;
    return departmentalCategories;
  }, [form.scope, generalCategories, departmentalCategories]);

  const categoryLabel = useMemo(() => {
    const map = {};
    [...generalCategories, ...departmentalCategories].forEach((category) => {
      map[category.code] = category.name;
    });
    return map;
  }, [generalCategories, departmentalCategories]);

  function change(name, value) {
    setForm((current) => {
      const next = { ...current, [name]: value };
      if (name === "scope") next.category = "";
      if (name === "department") next.category = "";
      return next;
    });
  }

  const isValid = Boolean(form.title.trim()) && Boolean(form.category) &&
    (form.scope !== "departmental" || Boolean(form.department)) &&
    (form.activity_date === "" || /^\d{4}-\d{2}-\d{2}$/.test(form.activity_date));

  async function onSubmit(event) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    const payload = {
      title: form.title, description: form.description,
      activity_date: form.activity_date || null, academic_year: form.academic_year || null,
      scope: form.scope,
      department: form.scope === "departmental" ? form.department : "",
      category: form.category,
      stakeholder: form.stakeholder, achievement_outcome: form.achievement_outcome,
      student_name: form.student_name, register_number: form.register_number,
      source_url: form.source_url,
    };
    try {
      if (editing) {
        await adminApi.put(`/api/admin/activities/${id}`, payload);
        navigate(`/admin/activities/${id}`, { replace: true });
      } else {
        const body = await adminApi.post("/api/admin/activities", payload);
        navigate(`/admin/activities/${body.activity_id}`, { replace: true });
      }
    } catch (err) {
      setError(err.message || "Unable to save the activity.");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <p className="muted state">Loading activity...</p>;

  return (
    <div className="page">
      <p className="back-row"><Link to={editing ? `/admin/activities/${id}` : "/admin/activities"}>← Back to activities</Link></p>
      <h2>{editing ? "Edit Activity" : "Add Activity"}</h2>
      <p className="muted">Record a new institutional activity or update an existing one.</p>

      <Card>
        <form onSubmit={onSubmit} className="admin-form form-grid">
          <label className="field span-2">
            <span className="field-label">Activity title *</span>
            <input value={form.title} onChange={(event) => change("title", event.target.value)} required />
          </label>
          <label className="field span-2">
            <span className="field-label">Description / details</span>
            <textarea rows={4} value={form.description} onChange={(event) => change("description", event.target.value)} placeholder="What happened in this activity?" />
          </label>

          <label className="field">
            <span className="field-label">Academic period</span>
            <select value={form.academic_year} onChange={(event) => change("academic_year", event.target.value)}>
              {PERIOD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field-label">Activity date</span>
            <input type="date" value={form.activity_date} onChange={(event) => change("activity_date", event.target.value)} />
          </label>

          <label className="field">
            <span className="field-label">Activity scope</span>
            <select value={form.scope} onChange={(event) => change("scope", event.target.value)}>
              <option value="general">General (Institution-wide)</option>
              <option value="departmental">Departmental</option>
            </select>
          </label>

          {form.scope === "departmental" ? (
            <>
              <label className="field">
                <span className="field-label">Department *</span>
                <select value={form.department} onChange={(event) => change("department", event.target.value)} required>
                  <option value="">Select department</option>
                  {departments.map((d) => (
                    <option key={d.department} value={d.department}>{d.department}</option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span className="field-label">Departmental Category *</span>
                <select value={form.category} onChange={(event) => change("category", event.target.value)} required>
                  <option value="">Select category</option>
                  {categoryOptions.map((category) => (
                    <option key={category.code} value={category.code}>{category.name}</option>
                  ))}
                </select>
              </label>
            </>
          ) : (
            <label className="field">
              <span className="field-label">General Category *</span>
              <select value={form.category} onChange={(event) => change("category", event.target.value)} required>
                <option value="">Select category</option>
                {generalCategories.map((category) => (
                  <option key={category.code} value={category.code}>{category.name}</option>
                ))}
              </select>
            </label>
          )}

          <label className="field">
            <span className="field-label">Stakeholder</span>
            <select value={form.stakeholder} onChange={(event) => change("stakeholder", event.target.value)}>
              {STAKEHOLDER_OPTIONS.map((name) => (
                <option key={name} value={name}>{name}</option>
              ))}
            </select>
          </label>

          {categoryLabel[form.category] && (
            <p className="muted span-2">Category: {categoryLabel[form.category]}</p>
          )}

          <label className="field span-2">
            <span className="field-label">Achievement / outcome details</span>
            <textarea rows={3} value={form.achievement_outcome} onChange={(event) => change("achievement_outcome", event.target.value)}
              placeholder="Award won, rank, recognition, or other outcome." />
          </label>
          <label className="field">
            <span className="field-label">Student name</span>
            <input value={form.student_name} onChange={(event) => change("student_name", event.target.value)} placeholder="Only if relevant" />
          </label>
          <label className="field">
            <span className="field-label">Register number</span>
            <input value={form.register_number} onChange={(event) => change("register_number", event.target.value)} placeholder="Only if relevant" />
          </label>
          <label className="field span-2">
            <span className="field-label">Source URL</span>
            <input type="url" value={form.source_url} onChange={(event) => change("source_url", event.target.value)} placeholder="https://www.tce.edu/..." />
          </label>

          {error && <p className="error state span-2" role="alert">{error}</p>}
          <p className="muted span-2">* Required fields. Leave optional fields empty when they do not apply.</p>
          <div className="form-actions span-2">
            <button type="submit" className="primary" disabled={busy || !isValid}>
              {busy ? "Saving..." : (editing ? "Save changes" : "Add activity")}
            </button>
            <Link className="ghost" to={editing ? `/admin/activities/${id}` : "/admin/activities"}>Cancel</Link>
          </div>
        </form>
      </Card>
    </div>
  );
}