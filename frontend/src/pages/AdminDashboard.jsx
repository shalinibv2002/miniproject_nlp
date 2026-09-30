import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../services/api";
import { KpiCard, Card, DataTable } from "../components/ui";
import { periodLabel } from "../lib/periods";

function PeriodList({ rows }) {
  const shown = rows.slice(0, 12);
  const total = shown.reduce((sum, row) => sum + (row.activities || 0), 0);
  if (shown.length === 0) return <p className="muted">No dated records yet.</p>;
  return (
    <ul className="admin-bar-list">
      {shown.map((row) => (
        <li key={row.label}>
          <div className="bar-row">
            <span className="bar-name">{row.label}</span>
            <span className="bar-value">{row.activities}</span>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: total ? `${((row.activities || 0) / total) * 100}%` : "0%" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function CategoryList({ items }) {
  const shown = [...items].sort((a, b) => b.activity_count - a.activity_count).slice(0, 12);
  const total = shown.reduce((sum, row) => sum + row.activity_count, 0);
  return (
    <ul className="admin-bar-list">
      {shown.map((row) => (
        <li key={row.code || row.name}>
          <div className="bar-row">
            <span className="bar-name">{row.name}</span>
            <span className="bar-value">{row.activity_count}</span>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: total ? `${(row.activity_count / total) * 100}%` : "0%" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    adminApi.get("/api/admin/overview")
      .then((body) => { if (active) setData(body); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  if (error) return <p className="error state">Unable to load admin overview.</p>;
  if (!data) return <p className="muted state">Loading admin dashboard...</p>;

  const periodRows = data.period_breakdown.map((row) => ({
    label: periodLabel(row.academic_year),
    activities: row.activity_count,
  }));

  return (
    <div className="page">
      <h2>Admin Dashboard</h2>
      <p className="muted">Manage the institution&apos;s activity database.</p>

      <div className="kpi-grid">
        <KpiCard label="Total Activities" value={data.total_activities} />
        <KpiCard label="General Activities" value={data.general_activities} />
        <KpiCard label="Departmental Activities" value={data.departmental_activities} />
        <KpiCard label="Records Requiring Attention" value={data.records_requiring_attention} />
      </div>

      <Card title="Activities by Academic Period" className="wide">
        <PeriodList rows={periodRows} />
      </Card>

      <div className="chart-grid">
        <Card title="Activities by Category">
          <CategoryList items={data.category_totals} />
        </Card>
        <Card title="Activities by Department">
          <CategoryList items={data.department_totals} />
        </Card>
      </div>

      <Card title="Recent Activity Records">
        <DataTable
          rows={data.recent_activities}
          columns={[
            { key: "title", label: "Activity", render: (row) => (
              <Link to={`/admin/activities/${row.id}`}>{row.title}</Link>
            ) },
            { key: "activity_date", label: "Activity Date", render: (row) => row.activity_date || "—" },
            { key: "source_url", label: "Source", render: (row) => row.source_url ? (
              <a href={row.source_url} target="_blank" rel="noreferrer">Official TCE Source</a>
            ) : "—" },
          ]}
        />
        <p className="back-row"><Link to="/admin/activities">Manage all activities →</Link></p>
      </Card>
    </div>
  );
}