import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../../services/api";
import { KpiCard, Card } from "../../components/ui";
import { categoryName } from "../../lib/linkedin";
import ApifySyncStatus from "./ApifySyncStatus";

function BarList({ items }) {
  const total = items.reduce((sum, row) => sum + row.value, 0);
  if (items.length === 0) return <p className="muted">No data available.</p>;
  return (
    <ul className="admin-bar-list">
      {items.map((row) => (
        <li key={row.key || row.name}>
          <div className="bar-row">
            <span className="bar-name">{row.name}</span>
            <span className="bar-value">{row.value}</span>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: total ? `${(row.value / total) * 100}%` : "0%" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

const DATE_STATUS_LABELS = {
  dated: "Dated",
  undated: "Undated",
  ambiguous_multi_year: "Ambiguous (multi-year)",
};

export default function LinkedinAdminOverview() {
  const [data, setData] = useState(null);
  const [options, setOptions] = useState({ categories: [] });
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      adminApi.get("/api/admin/linkedin/summary"),
      adminApi.get("/api/admin/linkedin/options"),
    ]).then(([summary, opts]) => {
      if (!active) return;
      if (summary.status === "fulfilled") setData(summary.value);
      else setError(true);
      if (opts.status === "fulfilled") setOptions(opts.value);
    });
    return () => { active = false; };
  }, []);

  if (error) return <p className="error state">Unable to load the LinkedIn validation overview.</p>;
  if (!data) return <p className="muted state">Loading LinkedIn validation overview...</p>;

  const statusRows = [
    { key: "REPORTABLE", name: "Reportable", value: data.total_reportable_activities },
    { key: "NON_ACTIVITY", name: "Non-Activity", value: data.total_non_activities },
    { key: "REVIEW_REQUIRED", name: "Review Required", value: data.total_review_required },
  ];

  const categoryRows = Object.entries(data.by_category || {})
    .map(([code, count]) => ({ key: code, name: categoryName(code, options.categories), value: count }))
    .sort((a, b) => b.value - a.value).slice(0, 12);
  const deptRows = Object.entries(data.by_department || {})
    .map(([dept, count]) => ({ key: dept, name: dept === "General" ? "General (Institution-wide)" : dept, value: count }))
    .sort((a, b) => b.value - a.value).slice(0, 12);
  const stakeholderRows = Object.entries(data.by_stakeholder || {})
    .map(([name, count]) => ({ key: name, name, value: count }))
    .sort((a, b) => b.value - a.value).slice(0, 10);
  const yearRows = Object.entries(data.academic_year_availability || {})
    .map(([year, count]) => ({ key: year, name: year, value: count }));
  const dateRows = Object.entries(data.dated_vs_undated || {})
    .map(([status, count]) => ({ key: status, name: DATE_STATUS_LABELS[status] || status, value: count }));
  const linkRows = Object.entries(data.link_vs_linkless || {})
    .map(([key, count]) => ({ key, name: key === "with_url" ? "With source link" : "Without source link", value: count }));
  const reviewRows = Object.entries(data.by_review_status || {})
    .map(([status, count]) => ({ key: status, name: status, value: count }));
  const classificationRows = Object.entries(data.by_classification_status || {})
    .map(([status, count]) => ({ key: status, name: status, value: count }));

  return (
    <div className="page">
      <h2>LinkedIn Validation Dashboard</h2>
      <p className="muted">
        Final reportable dataset built from LinkedIn posts. Evidence and provenance are visible here only.
      </p>

      {/* Apify Sync Status — Monday 09:00 IST, manual trigger, checkpoint/resume */}
      <ApifySyncStatus />

      <div className="kpi-grid">
        <KpiCard label="Raw Rows Collected" value={data.total_raw_rows} sub="reported across all posts" />
        <KpiCard label="Canonical Posts" value={data.total_canonical_posts} />
        <KpiCard label="Reportable Activities" value={data.total_reportable_activities} sub="published publicly" />
        <KpiCard label="Review Required" value={data.total_review_required} sub="need manual triage" />
        <KpiCard label="Non-Activities" value={data.total_non_activities} />
        <KpiCard label="Unresolved / Flagged" value={data.unresolved_or_flagged} sub={`${data.flagged_records} flagged records`} />
      </div>

      <Card title="Classification Status">
        <BarList items={statusRows} />
        <p className="muted note">
          <Link to="/admin/linkedin/records">Browse all records →</Link> &middot;{" "}
          <Link to="/admin/linkedin/review">Open the review queue →</Link>
        </p>
      </Card>

      <div className="chart-grid">
        <Card title="Top Categories">
          <BarList items={categoryRows} />
        </Card>
        <Card title="Top Departments">
          <BarList items={deptRows} />
        </Card>
      </div>

      <div className="chart-grid">
        <Card title="Academic Years (Reportable)">
          {yearRows.length > 0
            ? <BarList items={yearRows} />
            : <p className="muted">No dated reportable activities.</p>}
        </Card>
        <Card title="Date Coverage">
          <BarList items={dateRows} />
        </Card>
      </div>

      <div className="chart-grid">
        <Card title="Stakeholders">
          <BarList items={stakeholderRows} />
        </Card>
        <Card title="Review Pipeline">
          <BarList items={reviewRows} />
          <p className="muted note">
            Classification pipeline: <BarList items={classificationRows} />
          </p>
        </Card>
        <Card title="Source Link Quality">
          <BarList items={linkRows} />
          <p className="muted note">
            {data.manually_validated} records manually validated ({Math.round((data.manually_validated / Math.max(1, data.total_canonical_posts)) * 100)}% of all records).
          </p>
        </Card>
      </div>
    </div>
  );
}