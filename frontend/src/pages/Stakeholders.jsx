import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { useGlobalFilters } from "../context/GlobalFilters";
import { Card } from "../components/ui";
import { ALL_PERIODS, periodLabel } from "../lib/periods";

export default function Stakeholders() {
  const { filters, setFilters } = useGlobalFilters();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(false);
  const navigate = useNavigate();
  const period = filters.period;

  useEffect(() => {
    let active = true;
    setError(false);
    setRows(null);
    const qs = period ? `?period=${encodeURIComponent(period)}` : "";
    api.get(`/api/stakeholders${qs}`)
      .then((result) => { if (active) setRows(result); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [period]);

  function explore(stakeholder) {
    setFilters((current) => ({
      ...current, stakeholder,
      department: "", category: "", generalCategory: "", departmentalCategory: "",
    }));
    navigate("/activities");
  }

  if (error) return <p className="error state">Unable to load stakeholder data. Please try again.</p>;
  if (!rows) return <p className="muted state">Loading stakeholders...</p>;

  return (
    <div className="page">
      <h2>Stakeholders</h2>
      <p className="muted">Explore TCE activities by the audiences they engage.</p>
      <div className="toolbar inline-toolbar">
        <label className="filter">
          <span>Academic Period</span>
          <select value={period} onChange={(event) => setFilters((current) => ({ ...current, period: event.target.value }))}>
            <option value="">All Periods</option>
            {ALL_PERIODS.map((p) => (
              <option key={p} value={p}>{periodLabel(p)}</option>
            ))}
          </select>
        </label>
      </div>
      {rows.length === 0 ? (
        <p className="muted state">No stakeholder activities found for the selected period.</p>
      ) : (
        <div className="chart-grid">
          {rows.map((row) => (
            <Card key={row.stakeholder} title={row.stakeholder}>
              <p>{row.activity_count} activities</p>
              <button className="primary" onClick={() => explore(row.stakeholder)}>Explore activities</button>
            </Card>
          ))}
        </div>
      )}
      <p className="muted"><Link to="/activities">Browse all activities</Link></p>
    </div>
  );
}