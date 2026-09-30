import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, DataTable } from "../components/ui";

export default function Reports() {
  const [quality, setQuality] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/analytics/data-quality")
      .then(setQuality)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!quality) return <p className="muted">Loading…</p>;

  const fieldRows = Object.entries(quality.field_completeness).map(
    ([field, v]) => ({
      field,
      filled: v.filled,
      ratio: `${(v.ratio * 100).toFixed(1)}%`,
    })
  );

  return (
    <div className="page">
      <h2>Reports</h2>
      <div className="chart-grid">
        <Card title="Field completeness (data quality)">
          <DataTable
            columns={[
              { key: "field", label: "Field" },
              { key: "filled", label: "Filled" },
              { key: "ratio", label: "Ratio" },
            ]}
            rows={fieldRows}
          />
        </Card>
        <Card title="Pipeline health">
          <DataTable
            columns={[
              { key: "label", label: "Metric" },
              { key: "value", label: "Value" },
            ]}
            rows={[
              { label: "Total activities", value: quality.total_activities },
              { label: "LinkedIn unchecked", value: quality.linkedin_unchecked },
              { label: "Review backlog", value: quality.review_backlog },
            ]}
          />
        </Card>
      </div>
      <p className="muted">
        Formal PDF/institutional reports are produced by the Python reporting
        module (Phase 14) and export to <code>data/exports/</code>.
      </p>
    </div>
  );
}