import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { adminApi } from "../services/api";
import { Card, DataTable } from "../components/ui";
import { BEFORE_2021, PERIOD_LABELS, periodLabel } from "../lib/periods";

const PERIOD_OPTIONS = [
  ...Object.entries(PERIOD_LABELS).map(([value, label]) => ({ value, label })),
  { value: BEFORE_2021, label: BEFORE_2021 },
];

export default function AdminActivityList() {
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(false);
  const [departments, setDepartments] = useState([]);
  const [generalCategories, setGeneralCategories] = useState([]);
  const [departmentalCategories, setDepartmentalCategories] = useState([]);
  const [filters, setFilters] = useState({
    period: "", department: "", generalCategory: "", departmentalCategory: "",
    stakeholder: "", q: "",
  });
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    adminApi.get("/api/departments").then(setDepartments).catch(() => setDepartments([]));
    adminApi.get("/api/general-categories").then(setGeneralCategories).catch(() => setGeneralCategories([]));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.period) params.set("period", filters.period);
    if (filters.department) params.set("department", filters.department);
    if (filters.generalCategory) params.set("general_category", filters.generalCategory);
    if (filters.departmentalCategory) params.set("departmental_category", filters.departmentalCategory);
    if (filters.stakeholder) params.set("stakeholder", filters.stakeholder);
    if (filters.q) params.set("q", filters.q);
    const qs = params.toString();
    let active = true;
    setError(false);
    adminApi.get(`/api/admin/activities${qs ? `?${qs}` : ""}`)
      .then((body) => { if (active) setRows(body.data || []); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [filters]);

  useEffect(() => {
    const suffix = filters.department ? `?department=${encodeURIComponent(filters.department)}` : "";
    adminApi.get(`/api/departmental-categories${suffix}`)
      .then(setDepartmentalCategories)
      .catch(() => setDepartmentalCategories([]));
  }, [filters.department]);

  function updateFilter(name, value) {
    setFilters((current) => {
      const next = { ...current, [name]: value };
      if (name === "department") next.departmentalCategory = "";
      return next;
    });
  }

  const shownRows = useMemo(() => (rows || []).map((row) => ({
    ...row,
    department: row.department || "General",
  })), [rows]);

  async function confirmDeleteRow(row) {
    if (busy) return;
    setBusy(true);
    try {
      await adminApi.del(`/api/admin/activities/${row.id}`);
      setConfirmDelete(null);
      setRows((current) => (current || []).filter((item) => item.id !== row.id));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  const columns = [
    {
      key: "title", label: "Activity",
      render: (row) => <Link to={`/admin/activities/${row.id}`}>{row.title}</Link>,
    },
    { key: "academic_year", label: "Period", render: (row) => periodLabel(row.academic_year) },
    { key: "department", label: "Department" },
    {
      key: "category", label: "Category",
      render: (row) => row.general_category || row.departmental_category || "—",
    },
    { key: "stakeholder", label: "Stakeholder", render: (row) => row.stakeholder || "Students" },
    {
      key: "actions", label: "Actions",
      render: (row) => (
        <div className="row-actions">
          <Link to={`/admin/activities/${row.id}`}>View</Link>
          <Link to={`/admin/activities/${row.id}/edit`}>Edit</Link>
          <button type="button" className="link danger" onClick={() => setConfirmDelete(row)}>Delete</button>
        </div>
      ),
    },
  ];

  return (
    <div className="page">
      <h2>Manage Activities</h2>
      <p className="muted">Search, filter and manage the activity database.</p>

      <Card className="admin-filters">
        <div className="filter-grid">
          <label className="filter">
            <span>Period</span>
            <select value={filters.period} onChange={(e) => updateFilter("period", e.target.value)}>
              <option value="">All periods</option>
              {PERIOD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Department</span>
            <select value={filters.department} onChange={(e) => updateFilter("department", e.target.value)}>
              <option value="">All Departments</option>
              {departments.map((d) => (
                <option key={d.department} value={d.department}>{d.department}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>General Category</span>
            <select value={filters.generalCategory} onChange={(e) => updateFilter("generalCategory", e.target.value)}>
              <option value="">All</option>
              {generalCategories.map((category) => (
                <option key={category.code} value={category.code}>{category.name}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Departmental Category</span>
            <select value={filters.departmentalCategory} onChange={(e) => updateFilter("departmentalCategory", e.target.value)}>
              <option value="">All</option>
              {departmentalCategories.map((category) => (
                <option key={category.code} value={category.code}>{category.name}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Stakeholder</span>
            <input
              type="text"
              value={filters.stakeholder}
              placeholder="e.g. Students"
              onChange={(e) => updateFilter("stakeholder", e.target.value)}
            />
          </label>
          <label className="filter filter-search">
            <span>Search</span>
            <input
              type="text"
              value={filters.q}
              placeholder="Search activity title or description"
              onChange={(e) => updateFilter("q", e.target.value)}
            />
          </label>
        </div>
      </Card>

      {error && <p className="error state">Unable to load activities.</p>}
      {!rows && !error && <p className="muted state">Loading activities...</p>}
      {rows && shownRows.length === 0 && <p className="muted state">No activities match your filters.</p>}
      {rows && shownRows.length > 0 && (
        <Card>
          <DataTable columns={columns} rows={shownRows} />
          <p className="muted">{shownRows.length} activity{shownRows.length === 1 ? "" : "ies"} shown.</p>
        </Card>
      )}

      {confirmDelete && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Delete confirmation">
          <div className="modal">
            <h3>Delete this activity?</h3>
            <p className="body-text">Are you sure you want to delete <strong>{confirmDelete.title}</strong>?</p>
            <p className="muted">This will remove the activity and its related metadata. This action cannot be undone.</p>
            <div className="modal-actions">
              <button type="button" className="ghost" onClick={() => setConfirmDelete(null)} disabled={busy}>Cancel</button>
              <button type="button" className="primary danger" onClick={() => confirmDeleteRow(confirmDelete)} disabled={busy}>
                {busy ? "Deleting..." : "Delete activity"}
              </button>
            </div>
          </div>
        </div>
      )}
      <p className="back-row"><button type="button" className="ghost" onClick={() => navigate("/admin")}>← Admin Dashboard</button></p>
    </div>
  );
}