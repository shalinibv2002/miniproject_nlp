import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { adminApi } from "../services/api";
import { Card } from "../components/ui";
import { periodLabel } from "../lib/periods";

function Field({ label, value }) {
  return <div className="field"><span className="field-label">{label}</span><span>{value || "—"}</span></div>;
}

export default function AdminActivityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activity, setActivity] = useState(null);
  const [state, setState] = useState("loading");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    setState("loading");
    setActivity(null);
    adminApi.get(`/api/admin/activities/${id}`).then((item) => {
      if (active) { setActivity(item); setState("ready"); }
    }).catch(() => { if (active) setState("error"); });
    return () => { active = false; };
  }, [id]);

  async function deleteActivity() {
    if (busy) return;
    setBusy(true);
    try {
      await adminApi.del(`/api/admin/activities/${id}`);
      navigate("/admin/activities", { replace: true });
    } catch {
      setBusy(false);
      setState("error");
    }
  }

  if (state === "loading") return <p className="muted state">Loading activity...</p>;
  if (state === "error") return <p className="error state">Unable to load this activity.</p>;

  const category = activity.category
    ? (activity.general_category || activity.departmental_category || activity.category)
    : null;

  return (
    <div className="page">
      <p className="back-row"><Link to="/admin/activities">← Back to activities</Link></p>
      <div className="title-row">
        <h2>{activity.title}</h2>
        <div className="row-actions">
          <Link to={`/admin/activities/${id}/edit`} className="primary-link">Edit</Link>
          <button type="button" className="link danger" onClick={() => setConfirming(true)}>Delete</button>
        </div>
      </div>
      <div className="detail-grid">
        <Card title="Activity Information">
          <Field label="Academic Period" value={periodLabel(activity.academic_year)} />
          <Field label="Department" value={activity.department === "General" ? "General (Institution-wide)" : activity.department} />
          <Field label="Scope" value={activity.scope === "general" ? "General" : "Departmental"} />
          <Field label="Category" value={category} />
          <Field label="Stakeholder" value={activity.stakeholder || "Students"} />
          <Field label="Source URL" value={activity.source_url} />
        </Card>
        <Card title="Description">
          <p className="body-text">{activity.description || "No description available."}</p>
        </Card>
      </div>
      {activity.achievement_outcome && (
        <Card title="Achievement / Outcome"><p className="body-text">{activity.achievement_outcome}</p></Card>
      )}

      {confirming && (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Delete confirmation">
          <div className="modal">
            <h3>Delete this activity?</h3>
            <p className="body-text">Are you sure you want to delete <strong>{activity.title}</strong>?</p>
            <p className="muted">Related metadata will be removed. This cannot be undone.</p>
            <div className="modal-actions">
              <button type="button" className="ghost" onClick={() => setConfirming(false)} disabled={busy}>Cancel</button>
              <button type="button" className="primary danger" onClick={deleteActivity} disabled={busy}>
                {busy ? "Deleting..." : "Delete activity"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}