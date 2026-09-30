import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { Pager } from "../../components/detail";
import { categoryName, confidenceInfo, statusTone } from "../../lib/linkedin";

const FILTER_KEYS = ["status", "category", "department", "stakeholder",
  "academic_year", "review_status", "confidence", "date_status",
  "sort", "order", "page", "pageSize"];

function SortTh({ label, sortKey, sort, order, onSort }) {
  const active = sort === sortKey;
  return (
    <button type="button"
      className={`sort-th${active ? " active" : ""}`}
      onClick={() => onSort(sortKey, active && order === "asc" ? "desc" : "asc")}>
      {label}
      {active && <span className="sort-arrow">{order === "asc" ? " ▲" : " ▼"}</span>}
    </button>
  );
}

function Pill({ value, title }) {
  return (
    <span className={`pill ${statusTone(value)}`} title={title}>{value || "—"}</span>
  );
}

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
  const [searchInput, setSearchInput] = useState(filters.search || "");
  const [items, setItems] = useState(null);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState(false);
  const [options, setOptions] = useState({ categories: [], departments: [], stakeholders: [], academic_years: [] });

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/linkedin/options").then((body) => {
      if (active) setOptions(body);
    }).catch(() => { /* filters still usable, vocabulary falls back */ });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters((current) => {
        const search = searchInput.trim();
        if ((current.search || "") === search) return current;
        return { ...current, search, page: "" };
      });
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

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
      })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [filters, setSearchParams]);

  const page = Number(filters.page || 1);
  const pageSize = Number(filters.pageSize || 25);
  const sort = filters.sort || "activity_id";
  const order = filters.order || "asc";

  const setFilter = (key, value) => setFilters((current) => (
  { ...current, [key]: value, ...(key === "page" || key === "pageSize" ? {} : { page: "" }) }
));

  const onSort = (nextSort, nextOrder) => {
    setFilters((current) => ({ ...current, sort: nextSort, order: nextOrder, page: "" }));
  };

  const reset = () => {
    setSearchInput("");
    setFilters({ pageSize: String(pageSize) });
  };

  const columns = useMemo(() => [
    {
      key: "activity_id", label: "ID",
      render: (row) => <Link to={`/admin/linkedin/records/${row.activity_id}`} className="mono">{row.activity_id}</Link>,
    },
    {
      key: "title", label: "Activity",
      render: (row) => <Link to={`/admin/linkedin/records/${row.activity_id}`}>{row.title}</Link>,
    },
    {
      key: "reportable_status", label: "Status",
      render: (row) => <Pill value={row.reportable_status} />,
    },
    {
      key: "category", label: "Category",
      render: (row) => (row.categories || []).map((c) => categoryName(c, options.categories)).join(", ") || "—",
    },
    { key: "department", label: "Department", render: (row) => (row.departments || []).join(", ") || "—" },
    { key: "stakeholder", label: "Stakeholder", render: (row) => (row.stakeholders || []).join(", ") || "—" },
    { key: "activity_date", label: "Activity Date", render: (row) => row.activity_date || "—" },
    { key: "academic_year", label: "Academic Year", render: (row) => row.academic_year || "—" },
    {
      key: "evidence_score", label: "Confidence",
      render: (row) => {
        const info = confidenceInfo(row.evidence_score);
        return <Pill value={info ? `${info.label} (${row.evidence_score})` : "—"} title={row.evidence_score == null ? "" : `Evidence score: ${row.evidence_score}`} />;
      },
    },
    { key: "review_status", label: "Review", render: (row) => <Pill value={row.review_status || "UNREVIEWED"} /> },
  ], [options.categories]);

  const errorTitle = error ? "Unable to load LinkedIn records." : null;
  const emptyText = items && items.length === 0
    ? "No records match your filters."
    : "Loading LinkedIn records...";

  return (
    <div className="page">
      <h2>All LinkedIn Records</h2>
      <p className="muted">Every final reportable row, with admin-only evidence available on each record.</p>

      <Card className="admin-filters">
        <div className="filter-grid">
          <label className="filter">
            <span>Status</span>
            <select value={filters.status || ""} onChange={(e) => setFilter("status", e.target.value)}>
              <option value="">All statuses</option>
              {(options.statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
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
            <span>Department</span>
            <select value={filters.department || ""} onChange={(e) => setFilter("department", e.target.value)}>
              <option value="">All departments</option>
              {(options.departments || []).map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Stakeholder</span>
            <select value={filters.stakeholder || ""} onChange={(e) => setFilter("stakeholder", e.target.value)}>
              <option value="">All stakeholders</option>
              {(options.stakeholders || []).map((s) => <option key={s} value={s}>{s}</option>)}
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
            <span>Review Status</span>
            <select value={filters.review_status || ""} onChange={(e) => setFilter("review_status", e.target.value)}>
              <option value="">All</option>
              {(options.review_statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Confidence</span>
            <select value={filters.confidence || ""} onChange={(e) => setFilter("confidence", e.target.value)}>
              <option value="">All</option>
              {(options.confidence_levels || []).map((level) => (
                <option key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</option>
              ))}
            </select>
          </label>
          <label className="filter">
            <span>Date Status</span>
            <select value={filters.date_status || ""} onChange={(e) => setFilter("date_status", e.target.value)}>
              <option value="">All</option>
              {(options.date_statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Date From</span>
            <input type="date" value={filters.date_from || ""} onChange={(e) => setFilter("date_from", e.target.value)} />
          </label>
          <label className="filter">
            <span>Date To</span>
            <input type="date" value={filters.date_to || ""} onChange={(e) => setFilter("date_to", e.target.value)} />
          </label>
          <label className="filter filter-search">
            <span>Search</span>
            <input type="text" value={searchInput} placeholder="Search title or description"
              onChange={(e) => setSearchInput(e.target.value)} />
          </label>
          <div className="filter form-actions">
            <button type="button" className="ghost" onClick={reset}>Reset filters</button>
          </div>
        </div>
      </Card>

      {errorTitle && <p className="error state">{errorTitle}</p>}
      {!error && !items && <p className="muted state">{emptyText}</p>}
      {!error && items && items.length === 0 && <p className="muted state">{emptyText}</p>}
      {!error && items && items.length > 0 && (
        <Card>
          <div className="table-actions">
            <span className="muted">{total} record{total === 1 ? "" : "s"} found</span>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th><SortTh label="Activity" sortKey="title" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Status" sortKey="reportable_status" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Category" sortKey="category" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Department" sortKey="department" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Stakeholder" sortKey="stakeholder" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Activity Date" sortKey="activity_date" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Academic Year" sortKey="academic_year" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Confidence" sortKey="evidence_score" sort={sort} order={order} onSort={onSort} /></th>
                  <th><SortTh label="Review" sortKey="review_status" sort={sort} order={order} onSort={onSort} /></th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.activity_id}>
                    {columns.map((c) => (
                      <td key={c.key}>{c.render(row)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={page} pageSize={pageSize} total={total}
            onPage={(next) => setFilter("page", String(next))}
            onPageSize={(size) => setFilter("pageSize", String(size))} />
        </Card>
      )}
      <p className="back-row"><Link to="/admin/linkedin">← Back to overview</Link></p>
    </div>
  );
}