import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { Pager } from "../../components/detail";
import { ReportTable } from "../../components/ReportTable";

// Departmental Activities validator view.  Reads from the same canonical
// linkedin_reportable.db via the existing admin API — just adds scope=departmental
// so only department-attributed records are shown.  No separate DB or duplicate
// records.  Edits here propagate to the public Dashboard, Reports, Analytics,
// Ask the Data and Exports immediately.
const FILTER_KEYS = [
  "approval", "academic_year", "department", "category", "stakeholder",
  "sort", "order", "page", "pageSize",
];

export default function LinkedinAdminDepartmental() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState(() => {
    const next = {};
    for (const key of FILTER_KEYS) {
      const value = searchParams.get(key);
      if (value) next[key] = value;
    }
    return next;
  });
  const [items, setItems] = useState(null);
  const [total, setTotal] = useState(0);
  const [pagination, setPagination] = useState(null);
  const [error, setError] = useState(false);
  const [actionError, setActionError] = useState("");
  const [deleting, setDeleting] = useState(null);
  const [reload, setReload] = useState(0);
  const [options, setOptions] = useState({
    categories: [], departments: [], stakeholders: [], academic_years: [],
  });

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/linkedin/options").then((body) => {
      if (active) setOptions(body);
    }).catch(() => { /* filters still usable */ });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams();
    // Always request departmental scope from the API.
    params.set("scope", "departmental");
    for (const key of FILTER_KEYS) {
      const value = filters[key];
      if (value) params.set(key, value);
    }
    setSearchParams(
      // Don't write scope= into the visible URL — it's implicit for this page.
      (() => {
        const visible = new URLSearchParams();
        for (const key of FILTER_KEYS) {
          if (filters[key]) visible.set(key, filters[key]);
        }
        return visible;
      })(),
      { replace: true },
    );
    const qs = params.toString();
    setError(false);
    adminApi.get(`/api/admin/linkedin/activities?${qs}`)
      .then((body) => {
        if (!active) return;
        setItems(body.data || []);
        setTotal(body.total || 0);
        setPagination(body.pagination || null);
      })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [filters, setSearchParams, reload]);

  const page = Number(filters.page || 1);
  const pageSize = Number(filters.pageSize || 25);
  const metaPage = Number((pagination && pagination.page) || page);
  const metaPageSize = Number((pagination && pagination.page_size) || pageSize);

  const setFilter = (key, value) => setFilters((current) => (
    { ...current, [key]: value, ...(key === "page" || key === "pageSize" ? {} : { page: "" }) }
  ));

  const reset = () => setFilters({ pageSize: String(pageSize) });

  // Delete is immediate: no confirmation dialog.
  async function removeRecord(activityId) {
    if (deleting) return;
    setDeleting(activityId);
    setActionError("");
    try {
      await adminApi.del(`/api/admin/linkedin/activities/${activityId}`);
      setItems((current) => (current || []).filter((row) => row.activity_id !== activityId));
      setTotal((current) => Math.max(0, current - 1));
      setReload((n) => n + 1);
    } catch (err) {
      setActionError(err.message || "Unable to delete this activity.");
    } finally {
      setDeleting(null);
    }
  }

  const extraColumns = [
    {
      key: "action",
      label: "Action",
      render: (row) => (
        <span className="row-actions">
          <Link to={`/admin/linkedin/departmental/${row.activity_id}`}>Edit</Link>
          <button type="button" className="ghost danger"
            disabled={Boolean(deleting)}
            onClick={() => removeRecord(row.activity_id)}>
            {deleting === row.activity_id ? "Deleting..." : "Delete"}
          </button>
        </span>
      ),
    },
  ];

  // Filter departments shown in the dropdown to real departments
  // (exclude "General" which is the institution-wide sentinel).
  const deptOptions = (options.departments || []).filter((d) => d !== "General");

  const errorTitle = error ? "Unable to load departmental records." : null;
  const emptyText = items && items.length === 0
    ? "No records match your filters."
    : "Loading departmental records...";

  return (
    <div className="page">
      <h2>Departmental Activities</h2>
      <p className="muted">
        LinkedIn activities attributed to a specific department. Edits here are reflected
        immediately in the User Dashboard, Reports, Analytics, Ask the Data and Exports.
      </p>

      <Card className="admin-filters">
        <div className="filter-grid">
          <label className="filter">
            <span>Status</span>
            <select
              value={filters.approval || ""}
              onChange={(e) => setFilter("approval", e.target.value)}
              aria-label="Status">
              <option value="">Approved / Not Approved</option>
              <option value="APPROVED">Approved</option>
              <option value="NOT_APPROVED">Not Approved</option>
            </select>
          </label>
          <label className="filter">
            <span>Academic Year</span>
            <select
              value={filters.academic_year || ""}
              onChange={(e) => setFilter("academic_year", e.target.value)}
              aria-label="Academic Year">
              <option value="">All years</option>
              {(options.academic_years || []).map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Department</span>
            <select
              value={filters.department || ""}
              onChange={(e) => setFilter("department", e.target.value)}
              aria-label="Department">
              <option value="">All departments</option>
              {deptOptions.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Departmental Category</span>
            <select
              value={filters.category || ""}
              onChange={(e) => setFilter("category", e.target.value)}
              aria-label="Departmental Category">
              <option value="">All categories</option>
              {(options.categories || []).map((c) => (
                <option key={c.code} value={c.code}>{c.name}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Stakeholder</span>
            <select
              value={filters.stakeholder || ""}
              onChange={(e) => setFilter("stakeholder", e.target.value)}
              aria-label="Stakeholder">
              <option value="">All stakeholders</option>
              {(options.stakeholders || []).map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
          <div className="filter form-actions">
            <button type="button" className="ghost" onClick={reset}>Reset filters</button>
          </div>
        </div>
      </Card>

      {actionError && <p className="error state" role="alert">{actionError}</p>}
      {errorTitle && <p className="error state">{errorTitle}</p>}
      {!error && !items && <p className="muted state">{emptyText}</p>}
      {!error && items && items.length === 0 && <p className="muted state">{emptyText}</p>}
      {!error && items && items.length > 0 && (
        <Card>
          <div className="table-actions">
            <span className="muted">{total} record{total === 1 ? "" : "s"} found</span>
          </div>
          <ReportTable
            records={items}
            showDepartment
            scope="departmental"
            category={filters.category || ""}
            page={metaPage}
            pageSize={metaPageSize}
            departmentCell={(row) => row.report_department || "—"}
            extraColumns={extraColumns}
          />
          <Pager page={metaPage} pageSize={metaPageSize} total={total}
            onPage={(next) => setFilter("page", String(next))}
            onPageSize={(size) => setFilter("pageSize", String(size))} />
        </Card>
      )}
      <p className="back-row"><Link to="/admin/linkedin">← Back to overview</Link></p>
    </div>
  );
}
