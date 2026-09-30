import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../../services/api";
import { Card } from "../../components/ui";
import { Pager } from "../../components/detail";
import { categoryName, confidenceInfo, statusTone } from "../../lib/linkedin";

function Pill({ value }) {
  return <span className={`pill ${statusTone(value)}`}>{value || "—"}</span>;
}

export default function LinkedinAdminQueue() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState(false);
  const [options, setOptions] = useState({ categories: [], statuses: [], date_statuses: [], review_reasons: [] });
  const [filters, setFilters] = useState({ reason: "", status: "", category: "", department: "", date: "", confidence: "" });
  const [localPage, setLocalPage] = useState(1);
  const [localSize, setLocalSize] = useState(25);

  const load = () => {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value) params.set(key, value);
    }
    const qs = params.toString();
    setError(false);
    adminApi.get(`/api/admin/linkedin/review-queue${qs ? `?${qs}` : ""}`)
      .then((body) => { setItems(body.data || []); setLocalPage(1); })
      .catch(() => setError(true));
  };

  useEffect(() => { load(); }, [filters]);

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/linkedin/options").then((body) => {
      if (active) setOptions(body);
    }).catch(() => {});
    return () => { active = false; };
  }, []);

  const setFilter = (name, value) => setFilters((current) => ({ ...current, [name]: value }));

  const start = (localPage - 1) * localSize;
  const pageItems = items ? items.slice(start, start + localSize) : [];

  return (
    <div className="page">
      <div className="title-row">
        <h2>LinkedIn Review Queue</h2>
        <div className="row-actions">
          <button type="button" className="ghost" onClick={load}>Refresh</button>
        </div>
      </div>
      <p className="muted">Records that need a human decision — open each one to inspect evidence and make a correction.</p>

      <Card className="admin-filters">
        <div className="filter-grid">
          <label className="filter">
            <span>Reason</span>
            <select value={filters.reason} onChange={(e) => setFilter("reason", e.target.value)}>
              <option value="">All reasons</option>
              {(options.review_reasons || []).map((reason) => <option key={reason} value={reason}>{reason}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Status</span>
            <select value={filters.status} onChange={(e) => setFilter("status", e.target.value)}>
              <option value="">All statuses</option>
              {(options.statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Category</span>
            <select value={filters.category} onChange={(e) => setFilter("category", e.target.value)}>
              <option value="">All categories</option>
              {(options.categories || []).map((c) => <option key={c.code} value={c.code}>{c.name}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Department</span>
            <select value={filters.department} onChange={(e) => setFilter("department", e.target.value)}>
              <option value="">All departments</option>
              {(options.departments || []).map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Date Status</span>
            <select value={filters.date} onChange={(e) => setFilter("date", e.target.value)}>
              <option value="">All</option>
              {(options.date_statuses || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
          <label className="filter">
            <span>Confidence</span>
            <select value={filters.confidence} onChange={(e) => setFilter("confidence", e.target.value)}>
              <option value="">All</option>
              {(options.confidence_levels || []).map((level) => (
                <option key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</option>
              ))}
            </select>
          </label>
          <div className="filter form-actions">
            <button type="button" className="ghost" onClick={() => setFilters({
              reason: "", status: "", category: "", department: "", date: "", confidence: "",
            })}>Reset filters</button>
          </div>
        </div>
      </Card>

      {error && <p className="error state">Unable to load the review queue.</p>}
      {!error && !items && <p className="muted state">Loading review queue...</p>}
      {!error && items && items.length === 0 && <p className="muted state">Nothing needs review under these filters.</p>}
      {!error && items && items.length > 0 && (
        <Card>
          <div className="table-actions">
            <span className="muted">{items.length} record{items.length === 1 ? "" : "s"} {items.length === 1 ? "needs" : "need"} attention</span>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Activity</th>
                  <th>Status</th>
                  <th>Category</th>
                  <th>Reason</th>
                  <th>Classification</th>
                  <th>Review</th>
                  <th>Confidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {pageItems.map((row) => (
                  <tr key={row.activity_id}>
                    <td className="mono">{row.activity_id}</td>
                    <td><Link to={`/admin/linkedin/records/${row.activity_id}`}>{row.title}</Link></td>
                    <td><Pill value={row.reportable_status} /></td>
                    <td>{(row.categories || []).map((c) => categoryName(c, options.categories)).join(", ") || "—"}</td>
                    <td>{row.unclear_reason || row.reason || "—"}</td>
                    <td><Pill value={row.classification_status} /></td>
                    <td><Pill value={row.review_status || "UNREVIEWED"} /></td>
                    <td>
                      {confidenceInfo(row.evidence_score)
                        ? `${confidenceInfo(row.evidence_score).label} (${row.evidence_score})`
                        : "—"}
                    </td>
                    <td><Link to={`/admin/linkedin/records/${row.activity_id}`}>Review →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager page={localPage} pageSize={localSize} total={items.length}
            onPage={setLocalPage} onPageSize={setLocalSize} />
        </Card>
      )}
      <p className="back-row"><Link to="/admin/linkedin">← Back to overview</Link></p>
    </div>
  );
}