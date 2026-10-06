import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { LoadingState, ErrorState, EmptyState } from "../../components/linkedinPublic";
import { publicCategoryLabel, publicDepartmentLabel, formatPublicDate } from "../../lib/linkedin";

const PAGE_SIZE = 12;

function paramFilters(params) {
  const academic_year = params.get("academic_year") || "";
  const category = params.get("category") || "";
  const department = params.get("department") || "";
  const stakeholder = params.get("stakeholder") || "";
  const search = params.get("search") || "";
  return { academic_year, category, department, stakeholder, search };
}

function buildQuery(filters) {
  const parts = new URLSearchParams();
  if (filters.academic_year) parts.set("academic_year", filters.academic_year);
  if (filters.category) parts.set("category", filters.category);
  if (filters.department) parts.set("department", filters.department);
  if (filters.stakeholder) parts.set("stakeholder", filters.stakeholder);
  if (filters.search) parts.set("search", filters.search);
  const qs = parts.toString();
  return qs ? `&${qs}` : "";
}

export default function LinkedinPublicActivities() {
  const [params, setParams] = useSearchParams();
  const initial = useMemo(() => paramFilters(params), []);
  const [options, setOptions] = useState(null);
  const [filters, setFilters] = useState(initial);
  const [draft, setDraft] = useState(initial);
  const [page, setPage] = useState(1);
  const [state, setState] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/filters")
      .then((data) => { if (active) setOptions(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    setState(null);
    setError(false);
    let active = true;
    api.get(`/api/linkedin/activities?page=${page}&page_size=${PAGE_SIZE}${buildQuery(filters)}`)
      .then((data) => { if (active) setState(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [page, filters]);

  function apply() {
    setFilters(draft);
    setPage(1);
    setParams((next) => {
      Object.keys(draft).forEach((key) => {
        if (draft[key]) next.set(key, draft[key]);
        else next.delete(key);
      });
      return next;
    }, { replace: true });
  }

  function reset() {
    const cleared = { academic_year: "", category: "", department: "", stakeholder: "", search: "" };
    setDraft(cleared);
    setFilters(cleared);
    setPage(1);
    setParams({}, { replace: true });
  }

  if (error && !options) return <ErrorState label="Unable to load filter options." />;
  if (!options) return <LoadingState label="Loading activities..." />;

  const years = options.years || [];
  const categories = options.categories || [];
  const departments = options.departments || [];
  const stakeholders = options.stakeholders || [];
  const { data = [], total = 0, pagination = {} } = state || {};
  const hasActiveFilters = Object.values(filters).some(Boolean);

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Activities</h2>
        <p className="muted">
          Browse {total} activities published on the TCE LinkedIn channel. Filters combine — pick a year, category,
          department or stakeholder to narrow the list.
        </p>
      </section>

      <Card className="filter-card" >
        <div className="filter-panel">
          <label className="filter-field filter-search">
            <span className="filter-label">Search</span>
            <input
              type="search"
              aria-label="Search activities"
              placeholder="Search titles and keywords..."
              value={draft.search}
              onChange={(event) => setDraft((prev) => ({ ...prev, search: event.target.value }))}
            />
          </label>
          <label className="filter-field">
            <span className="filter-label">Academic Year</span>
            <select
              aria-label="Academic year"
              value={draft.academic_year}
              onChange={(event) => setDraft((prev) => ({ ...prev, academic_year: event.target.value }))}
            >
              <option value="">All years</option>
              {years.map((year) => <option key={year} value={year}>{year}</option>)}
            </select>
          </label>
          <label className="filter-field">
            <span className="filter-label">Category</span>
            <select
              aria-label="Category"
              value={draft.category}
              onChange={(event) => setDraft((prev) => ({ ...prev, category: event.target.value }))}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c.code} value={c.code}>{publicCategoryLabel(c.code, c.name)}</option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span className="filter-label">Department</span>
            <select
              aria-label="Department"
              value={draft.department}
              onChange={(event) => setDraft((prev) => ({ ...prev, department: event.target.value }))}
            >
              <option value="">All departments</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>{publicDepartmentLabel(dept)}</option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span className="filter-label">Stakeholder</span>
            <select
              aria-label="Stakeholder"
              value={draft.stakeholder}
              onChange={(event) => setDraft((prev) => ({ ...prev, stakeholder: event.target.value }))}
            >
              <option value="">All stakeholders</option>
              {stakeholders.map((stak) => <option key={stak} value={stak}>{stak}</option>)}
            </select>
          </label>
          <div className="filter-actions">
            <button type="button" className="primary" onClick={apply}>Apply filters</button>
            <button type="button" className="ghost" onClick={reset}>Reset</button>
          </div>
        </div>
      </Card>

      {error && <ErrorState label="Unable to load activities. Please try again." />}
      {!state && !error && <LoadingState label="Loading activities..." />}
      {state && data.length === 0 && (
        <EmptyState label={hasActiveFilters ? "No activities match the selected filters." : "No activities available."} />
      )}

      {state && data.length > 0 && (
        <>
          <div className="activity-grid">
            {data.map((record) => {
              const dateText = formatPublicDate(record.activity_date);
              const category = publicCategoryLabel(null, record.category);
              return (
                <Link key={record.activity_id} className="activity-card" to={`/activities/${record.activity_id}`}>
                  <h3 className="activity-card-title">{record.title}</h3>
                  {record.summary && <p className="activity-card-desc">{record.summary}</p>}
                  <dl className="activity-meta">
                    {dateText ? (
                      <div className="kv-row"><dt>Date</dt><dd>{dateText}</dd></div>
                    ) : (
                      <div className="kv-row"><dt>Date</dt><dd className="muted">Not specified</dd></div>
                    )}
                    {record.academic_year && (
                      <div className="kv-row"><dt>Year</dt><dd>{record.academic_year}</dd></div>
                    )}
                    <div className="kv-row"><dt>Category</dt><dd>{category || "Not specified"}</dd></div>
                    <div className="kv-row"><dt>Department</dt><dd>{publicDepartmentLabel(record.department)}</dd></div>
                    <div className="kv-row"><dt>Stakeholder</dt><dd>{record.stakeholder || "Not specified"}</dd></div>
                  </dl>
                  </Link>
              );
            })}
          </div>
          <div className="pager">
            <span>
              Showing {(pagination.page || 1) - 1 < 0 ? 1 : (pagination.page - 1) * pagination.page_size + 1}–
              {Math.min(pagination.page * pagination.page_size, total)} of {total}
            </span>
            <div className="row-actions">
              <button type="button" className="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>← Prev</button>
              <span>Page {page} of {Math.max(1, pagination.pages || 0)}</span>
              <button type="button" className="ghost" disabled={page >= (pagination.pages || 1)} onClick={() => setPage((p) => p + 1)}>Next →</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}