import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, DataTable } from "../components/ui";

export default function Sources() {
  const [sources, setSources] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/years").catch(() => {});
    api
      .get("/api/activities?page=1&page_size=1")
      .then(() => {})
      .catch(() => {});
  }, []);

  useEffect(() => {
    api
      .get("/api/analytics/overview")
      .then((o) => setSources([{ source: "tce.edu/events", activities: o.total_activities }]))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;

  return (
    <div className="page">
      <h2>Data Sources</h2>
      <Card title="Source registry and collection summary">
        <DataTable
          columns={[
            { key: "source", label: "Source" },
            { key: "activities", label: "Activities loaded" },
          ]}
          rows={sources}
        />
        <p className="muted">
          Live URLs verified against <code>robots.txt</code> before collection.
          Raw pages stored under <code>data/raw/events/</code>. Trigger a fresh
          pipeline run via <code>POST /api/collection/run</code> or{" "}
          <code>python -m backend.collectors.tce_events_collector</code>.
        </p>
      </Card>
    </div>
  );
}