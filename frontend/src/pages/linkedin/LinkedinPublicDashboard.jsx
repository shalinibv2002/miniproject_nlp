import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { KpiCard, Card } from "../../components/ui";
import { BarList, LoadingState, ErrorState } from "../../components/linkedinPublic";
import { dateStatusSummary } from "../../lib/linkedin";
import { useSyncNotification, SyncNotificationBanner } from "../../lib/useSyncNotification.jsx";

const PUBLIC_HINT = "reportable activities from available posts";

export default function LinkedinPublicDashboard() {
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState(false);
  const { notification, dismiss } = useSyncNotification();

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/analytics/overview")
      .then((data) => { if (active) setOverview(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  if (error) return <ErrorState label="Unable to load the institutional activity dashboard." />;
  if (!overview) return <LoadingState label="Loading the institutional activity dashboard..." />;

  const total = overview.total_reportable_activities;
  const years = (overview.activities_by_academic_year || [])
    .sort((a, b) => b.activity_count - a.activity_count);
  const depts = (overview.activities_by_department || [])
    .filter((row) => row.department !== "General")
    .sort((a, b) => b.activity_count - a.activity_count);
  const staks = (overview.activities_by_stakeholder || [])
    .sort((a, b) => b.activity_count - a.activity_count);
  const split = overview.general_departmental || {};
  const generalTotal = split.general || 0;
  const departmentalTotal = split.departmental || 0;
  const generalCats = (overview.general_categories || [])
    .sort((a, b) => b.activity_count - a.activity_count);
  const departmentalCats = (overview.departmental_categories || [])
    .sort((a, b) => b.activity_count - a.activity_count);
  const date = dateStatusSummary(overview.date_status || {});

  const departmentRows = depts
    .map((d) => ({ key: d.department, name: d.department, value: d.activity_count }));
  const stakeholderRows = staks
    .map((s) => ({ key: s.stakeholder, name: s.stakeholder, value: s.activity_count }));
  const yearRows = years
    .map((y) => ({ key: y.academic_year, name: y.academic_year, value: y.activity_count }));
  const generalCatRows = generalCats
    .map((c) => ({ key: c.category, name: c.name, value: c.activity_count }));
  const departmentalCatRows = departmentalCats
    .map((c) => ({ key: c.category, name: c.name, value: c.activity_count }));

  return (
    <div className="page">
      {/* Non-blocking sync notification — shown only when a new sync has run */}
      <SyncNotificationBanner notification={notification} onDismiss={dismiss} />

      <section className="page-intro">
        <h2>Institutional Activity Dashboard</h2>
        <p className="muted">
          Public summary of {total} activities shared on the official TCE LinkedIn channel.
          All figures are computed from the reportable dataset and update automatically — nothing is hard-coded.
        </p>
      </section>

      <div className="kpi-grid">
        <KpiCard label="Total Activities" value={total} sub={PUBLIC_HINT} />
        <KpiCard label="General Activities" value={generalTotal} sub={<Link to="/categories/general">institution-wide</Link>} />
        <KpiCard label="Departmental Activities" value={departmentalTotal} sub={<Link to="/departments">by department</Link>} />
        <KpiCard label="Departments Covered" value={overview.departments_covered || 0} sub="organising departments" />
        <KpiCard label="Stakeholders Covered" value={overview.stakeholders_covered || 0} sub="audience groups" />
        <KpiCard label="Categories" value={overview.categories_covered || 0} sub="activity types" />
      </div>

      <div className="chart-grid">
        <Card title="Activities by Academic Year">
          {yearRows.length > 0
            ? <BarList items={yearRows} />
            : <p className="muted">No dated reportable activities.</p>}
          <p className="muted note">
            Date-based figures include only reliably dated records ({date.dated} of {date.total} records, {date.share}%).
          </p>
        </Card>
        <Card title="General vs Departmental">
          <BarList items={[
            { key: "general", name: "General (institution-wide)", value: generalTotal },
            { key: "departmental", name: "Department-specific", value: departmentalTotal },
          ]} />
          <p className="muted note">
            Two separate worlds: <Link to="/categories/general">browse general categories</Link> or{" "}
            <Link to="/departments">drill into departments</Link>.
          </p>
        </Card>
      </div>

      <div className="chart-grid">
        <Card title="Top General Categories">
          {generalCatRows.length > 0
            ? <BarList items={generalCatRows} />
            : <p className="muted">No institution-wide category breakdowns.</p>}
          <p className="muted note"><Link to="/categories/general">Browse General Categories</Link></p>
        </Card>
        <Card title="Top Departmental Categories">
          {departmentalCatRows.length > 0
            ? <BarList items={departmentalCatRows} />
            : <p className="muted">No departmental category breakdowns.</p>}
          <p className="muted note"><Link to="/departments">Browse Departments</Link></p>
        </Card>
      </div>

      <div className="chart-grid">
        <Card title="Top Departments">
          {departmentRows.length > 0
            ? <BarList items={departmentRows} />
            : <p className="muted">No departmental activities in the dataset.</p>}
          <p className="muted note"><Link to="/departments">All departments</Link></p>
        </Card>
        <Card title="Stakeholders">
          <BarList items={stakeholderRows} />
        </Card>
      </div>
    </div>
  );
}