import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../services/api";
import { Card } from "./ui";
import { LoadingState, ErrorState, EmptyState } from "./linkedinPublic";
import { ActivityCardList } from "./ActivityList";
import { publicCategoryLabel } from "../lib/linkedin";

const ORDER = ["period", "category", "stakeholder"];
const PAGE_SIZE = 12;

function qs(base, extra = {}) {
  const p = new URLSearchParams(base);
  Object.entries(extra).forEach(([k, v]) => { if (v) p.set(k, v); });
  const s = p.toString();
  return s ? `?${s}` : "";
}

function buildSummary({ total, scope, department, categoryLabel, stakeholder, period }) {
  if (!total) return null;
  const noun = total === 1 ? "activity" : "activities";
  const head = [total];
  if (scope === "general") head.push("General");
  if (department) head.push(department);
  if (categoryLabel) head.push(categoryLabel);
  head.push(noun);
  let sentence = head.join(" ");
  if (stakeholder) sentence += ` involving ${stakeholder}`;
  if (period) sentence += ` during ${period}`;
  return `${sentence}.`;
}

export default function DrillFlow({ scope, department, title, intro, backTo, backLabel }) {
  const [params, setParams] = useSearchParams();
  const period = params.get("period") || "";
  const category = params.get("category") || "";
  const stakeholder = params.get("stakeholder") || "";
  const view = params.get("view") || "";

  const [rows, setRows] = useState(null);
  const [list, setList] = useState(null);
  const [error, setError] = useState(false);
  const [page, setPage] = useState(1);

  const base = {};
  if (scope) base.scope = scope;
  if (department) base.department = department;

  const allSet = period && category && stakeholder;
  const showList = view === "activities" || Boolean(allSet);
  const stepKey = showList ? null
    : !period ? "period"
    : !category ? "category"
    : "stakeholder";

  useEffect(() => {
    let active = true;
    setRows(null);
    setError(false);
    setPage(1);
    const fetchRows = () => {
      if (stepKey === "period") return api.get(`/api/linkedin/years${qs(base)}`);
      if (stepKey === "category") return api.get(`/api/linkedin/categories${qs(base, { academic_year: period })}`);
      if (stepKey === "stakeholder") return api.get(`/api/linkedin/stakeholders${qs(base, { academic_year: period, category })}`);
      return null;
    };
    if (!fetchRows()) { setRows([]); return () => { active = false; }; }
    fetchRows()
      .then((data) => { if (active) setRows(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stepKey, period, category, scope, department]);

  useEffect(() => {
    if (!showList) { setList(null); return undefined; }
    let active = true;
    setList(null);
    setError(false);
    api.get(`/api/linkedin/activities${qs({ ...base, academic_year: period, category, stakeholder }, { page, page_size: PAGE_SIZE })}`)
      .then((data) => { if (active) setList(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showList, period, category, stakeholder, scope, department, page]);

  function select(key, value) {
    setPage(1);
    setParams((prev) => {
      const p = new URLSearchParams(prev);
      if (value) p.set(key, value); else p.delete(key);
      const idx = ORDER.indexOf(key);
      ORDER.slice(idx + 1).forEach((k) => p.delete(k));
      p.delete("view");
      return p;
    });
  }

  function showActivities() {
    setPage(1);
    setParams((prev) => {
      const p = new URLSearchParams(prev);
      p.set("view", "activities");
      return p;
    });
  }

  function goBack() {
    setPage(1);
    setParams((prev) => {
      const p = new URLSearchParams(prev);
      if (p.get("stakeholder")) p.delete("stakeholder");
      else if (p.get("category")) p.delete("category");
      else if (p.get("period")) p.delete("period");
      p.delete("view");
      return p;
    });
  }

  const chips = [
    ["period", period],
    ["category", category && publicCategoryLabel(category)],
    ["stakeholder", stakeholder],
  ].filter(([, value]) => value);

  if (error && !rows && !list) return <ErrorState label="Unable to load this flow." />;

  const { data = [], total = 0, pagination = {} } = list || {};
  const categoryLabel = category ? publicCategoryLabel(category) : "";

  return (
    <div className="page">
      <section className="page-intro">
        <h2>{title}</h2>
        <p className="muted">{intro}</p>
      </section>

      <div className="back-row">
        <Link to={backTo} className="ghost btn">&larr; {backLabel}</Link>
      </div>

      <p className="drill-path">
        {chips.length === 0
          ? "Step: choose a period"
          : chips.map(([key, value], i) => (
            <span key={key}>
              {i > 0 && " › "}
              <button type="button" className="ghost" onClick={() => select(key, "")}>{value} ✕</button>
            </span>
          ))}
        {chips.length > 0 && !showList && <span> › {stepKey}</span>}
      </p>

      {!showList && (
        <Card title={`Choose a ${stepKey}`}>
          {!rows && !error && <LoadingState label={`Loading ${stepKey}...`} />}
          {rows && rows.length === 0 && <EmptyState label={`No ${stepKey} available.`} />}
          {rows && rows.length > 0 && (
            <div className="choice-list">
              {rows.map((row) => {
                const key = stepKey === "period" ? row.academic_year
                  : stepKey === "category" ? row.category : row.stakeholder;
                const name = stepKey === "category" ? publicCategoryLabel(row.category, row.name) : key;
                return (
                  <button
                    key={key}
                    type="button"
                    className="choice-card"
                    onClick={() => select(stepKey, key)}
                  >
                    <span>{name}</span>
                    <span className="muted">{row.activity_count}</span>
                  </button>
                );
              })}
            </div>
          )}
          <div className="filter-actions" style={{ marginTop: 12 }}>
            <button type="button" className="ghost" onClick={showActivities}>View all matching activities</button>
          </div>
        </Card>
      )}

      {showList && (
        <>
          <div className="back-row">
            <button type="button" className="ghost" onClick={goBack}>&larr; Back to filters</button>
          </div>

          {!list && !error && <LoadingState label="Loading activities..." />}
          {error && !list && <ErrorState label="Unable to load activities." />}

          {list && (
            <>
              <p className="answer-line">
                {buildSummary({ total, scope, department, categoryLabel, stakeholder, period })
                  || "No matching activities for the selected filters."}
              </p>
              {data.length === 0 && <EmptyState label="No activities match the selected filters." />}
              {data.length > 0 && (
                <>
                  <ActivityCardList records={data} showDepartment={Boolean(department)} />
                  <div className="pager">
                    <span>
                      Showing {(pagination.page || 1) - 1 < 0 ? 1 : (pagination.page - 1) * pagination.page_size + 1}–
                      {Math.min(pagination.page * pagination.page_size, total)} of {total}
                    </span>
                    <div className="row-actions">
                      <button type="button" className="ghost" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>&larr; Prev</button>
                      <span>Page {page} of {Math.max(1, pagination.pages || 0)}</span>
                      <button type="button" className="ghost" disabled={page >= (pagination.pages || 1)} onClick={() => setPage((p) => p + 1)}>Next &rarr;</button>
                    </div>
                  </div>
                </>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
