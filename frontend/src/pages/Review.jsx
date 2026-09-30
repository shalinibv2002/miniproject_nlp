import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import { Card, DataTable } from "../components/ui";

export default function Review() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = () =>
    api
      .get("/api/review?status=open")
      .then((r) => setItems(r.items))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const act = async (id, action) => {
    setBusy(true);
    try {
      await api.post(`/api/review/${id}/${action}`, {
        reviewer: "dashboard-user",
        reason: "approved from dashboard",
      });
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  if (error) return <p className="error">{error}</p>;

  return (
    <div className="page">
      <h2>Review Queue</h2>
      <Card>
        <DataTable
          columns={[
            {
              key: "title",
              label: "Activity",
              render: (r) => <Link to={`/activities/${r.activity_id}`}>{r.title}</Link>,
            },
            { key: "reason", label: "Reason" },
            {
              key: "confidence",
              label: "Confidence",
              render: (r) => (r.overall_confidence ?? "—"),
            },
            {
              key: "actions",
              label: "Actions",
              render: (r) => (
                <div className="row-actions">
                  <button
                    className="primary"
                    disabled={busy}
                    onClick={() => act(r.activity_id, "approve")}
                  >
                    Approve
                  </button>
                  <button
                    className="danger"
                    disabled={busy}
                    onClick={() => act(r.activity_id, "reject")}
                  >
                    Reject
                  </button>
                </div>
              ),
            },
          ]}
          rows={items}
        />
      </Card>
    </div>
  );
}