import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { Pager } from "../../components/detail";
import { ReportTable } from "../../components/ReportTable";

// The validator works from four questions only: is it approved, which year,
// which category and which audience.  Everything else the API can filter on
// stays out of this screen on purpose.
const FILTER_KEYS = ["approval", "category", "stakeholder", "academic_year",
  "sort", "order", "page", "pageSize"];

export default function LinkedinAdminRecords() {
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
  const [options, setOptions] = useState({ categories: [], departments: [], stakeholders: [], academic_years: [] });

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/linkedin/options").then((body) => {
      if (active) setOptions(body);
    }).catch(() => { /* filters still usable, vocabulary falls back */ });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    const params = new URLSearchParams();
    for (const key of FILTER_KEYS) {
      const value = filters[key];
      if (value) params.set(key, value);
    }
    setSearchParams(params, { replace: true });
    const qs = params.toString();
    setError(false);
    adminApi.get(`/api/admin/linkedin/activities${qs ? `?${qs}` : ""}`)
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
  // S.No and the pager follow the server's own page/page_size so the serial
  // numbers stay continuous even when the requested page size is clamped.
  const metaPage = Number((pagination && pagination.page) || page);
  const metaPageSize = Number((pagination && pagination.page_size) || pageSize);

  const setFilter = (key, value) => setFilters((current) => (
  { ...current, [key]: value, ...(key === "page" || key === "pageSize" ? {} : { page: "" }) }
));

  const reset = () => {
    setFilters({ pageSize: String(pageSize) });
  };

  // Delete is immediate: no confirmation dialog, the row disappears and the
  // table is reloaded from the server straight away.
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
          <Link to={`/admin/linkedin/records/${row.activity_id}`}>Edit</Link>
          <button type="button" className="ghost danger"
            disabled={Boolean(deleting)}
            onClick={() => removeRecord(row.activity_id)}>
            {deleting === row.activity_id ? "Deleting..." : "Delete"}
          </button>
        </span>
      ),
    },
  ];

  const errorTitle = error ? "Unable to load LinkedIn records." : null;
  const emptyText = items && items.length === 0
    ? "No records match your filters."
    : "Loading LinkedIn records...";

  return (
    <div className="page">
      <h2>All LinkedIn Records</h2>
      <p className="muted">All LinkedIn activities in the final reportable dataset. Use filters to narrow by status, year, category or stakeholder.</p>

      <Card className="admin-filters">
        <div className="filter-grid">
          <label className="filter">
            <span>Status</span>
            <select value={filters.approval || ""} onChange={(e) => setFilter("approval", e.target.value)}>
              <option value="">Approved / Not Approved</option>
              <option value="APPROVED">Approved</option>
              <option value="NOT_APPROVED">Not Approved</option>
            </select>
          </label>
          <label className="filter">
            <span>Academic Year</span>
            <select value={filters.academic_year || ""} onChange={(e) => setFilter("academic_year", e.target.value)}>
              <option value="">All years</option>
              {(options.academic_years || []).map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Category</span>
            <select value={filters.category || ""} onChange={(e) => setFilter("category", e.target.value)}>
              <option value="">All categories</option>
              {(options.categories || []).map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Stakeholder</span>
            <select value={filters.stakeholder || ""} onChange={(e) => setFilter("stakeholder", e.target.value)}>
              <option value="">All stakeholders</option>
              {(options.stakeholders || []).map((s) => <option key={s} value={s}>{s}</option>)}
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
            page={metaPage}
            pageSize={metaPageSize}
            departmentCell={(row) => row.report_department || "General"}
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