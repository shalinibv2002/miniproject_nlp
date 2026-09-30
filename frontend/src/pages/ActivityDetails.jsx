import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../services/api";
import { Card } from "../components/ui";
import { periodLabel } from "../lib/periods";

function Field({ label, value }) {
  return <div className="field"><span className="field-label">{label}</span><span>{value || "Not available"}</span></div>;
}

function isOfficialTceUrl(value) {
  try {
    const hostname = new URL(value).hostname.toLowerCase();
    return hostname === "tce.edu" || hostname.endsWith(".tce.edu");
  } catch {
    return false;
  }
}

function officialSources(activity) {
  return [...new Set([...(activity.official_sources || []), activity.source_url].filter(isOfficialTceUrl))];
}

export default function ActivityDetails() {
  const { id } = useParams();
  const [activity, setActivity] = useState(null);
  const [state, setState] = useState("loading");

  useEffect(() => {
    let active = true;
    setState("loading");
    setActivity(null);
    api.get(`/api/activities/${id}`).then((result) => {
      if (active) {
        setActivity(result);
        setState("ready");
      }
    }).catch((error) => {
      if (active) setState(error.message.toLowerCase().includes("not found") ? "not-found" : "error");
    });
    return () => { active = false; };
  }, [id]);

  if (state === "loading") return <p className="muted state">Loading activity...</p>;
  if (state === "not-found") {
    return <div className="page"><p className="muted state">Activity not found.</p><Link to="/activities">← Back to Activities</Link></div>;
  }
  if (state === "error") return <p className="error state">Unable to load this activity. Please try again.</p>;

  const categories = activity.categories?.map((category) => category.name).filter(Boolean).join(", ") || "Not available";
  const sources = officialSources(activity);
  return (
    <div className="page">
      <p className="back-row"><Link to="/activities">← Back to Activities</Link></p>
      <h2>Activity Details</h2>
      <h1>{activity.title}</h1>
      <div className="detail-grid">
        <Card title="Activity Information">
          <Field label="Category" value={categories} />
          <Field label="Period" value={periodLabel(activity.academic_year)} />
          <Field label="Department" value={activity.department || "General"} />
          <Field label="General Category" value={activity.general_category} />
          <Field label="Departmental Category" value={activity.departmental_category} />
          <Field label="Stakeholder" value={activity.stakeholder || "Students"} />
        </Card>
        <Card title="Description">
          <p className="body-text">{activity.description || "No description available."}</p>
        </Card>
      </div>
      {activity.achievement_outcome?.trim() && (
        <Card title="Achievement / Outcome"><p className="body-text">{activity.achievement_outcome}</p></Card>
      )}
      <Card title={sources.length > 1 ? "Official TCE Sources" : "Official TCE Source"}>
        {sources.length ? (
          <ul className="source-list">
            {sources.map((source, index) => (
              <li key={source}>
                <a href={source} target="_blank" rel="noreferrer" aria-label={`Official TCE Source ${index + 1} (opens in a new tab)`}>
                  Official TCE Source
                </a>
              </li>
            ))}
          </ul>
        ) : <p className="muted">Not available</p>}
      </Card>
    </div>
  );
}
