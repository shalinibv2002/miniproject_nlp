import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, KpiCard, DataTable } from "../components/ui";

const STATUS_COLORS = {
  Matched: "good",
  "Possible Match": "warn",
  "Not Found": "bad",
  "Not Checked": "muted",
};

export default function Linkedin() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/analytics/linkedin")
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p className="muted">Loading…</p>;

  const rows = Object.entries(data.by_status || {}).map(([status, count]) => ({
    status,
    count,
  }));
  const coverage = (data.coverage_ratio * 100).toFixed(1);
  return (
    <div className="page">
      <h2>LinkedIn Cross-Reference</h2>
      <div className="kpi-grid">
        <KpiCard label="Matched" value={data.matched} />
        <KpiCard label="Possible Match" value={data.possible} />
        <KpiCard label="Not Found (searched)" value={data.not_found_after_search} />
        <KpiCard label="Coverage" value={`${coverage}%`} />
      </div>
      <Card title="Match status breakdown">
        <DataTable
          columns={[
            {
              key: "status",
              label: "Status",
              render: (r) => (
                <span className={`pill ${STATUS_COLORS[r.status] || "muted"}`}>
                  {r.status}
                </span>
              ),
            },
            { key: "count", label: "Activities" },
          ]}
          rows={rows}
        />
        <p className="muted note">{data.note}</p>
      </Card>
      <p className="muted">
        Lookup queue exported to{" "}
        <code>data/linkedin_lookup_queue.csv</code> — fill it by searching the
        public TCE LinkedIn page and record results via{" "}
        <code>POST /api/review/:id/linkedin</code>.
      </p>
    </div>
  );
}