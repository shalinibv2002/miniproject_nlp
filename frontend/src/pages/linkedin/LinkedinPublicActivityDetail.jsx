import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { Tags } from "../../components/detail";
import { LoadingState, ErrorState } from "../../components/linkedinPublic";
import { publicCategoryLabel, publicDepartmentLabel, publicSourceLabel, formatPublicDate } from "../../lib/linkedin";

export default function LinkedinPublicActivityDetail() {
  const { activityId } = useParams();
  const [record, setRecord] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    setRecord(null);
    setNotFound(false);
    setError(false);
    let active = true;
    api.get(`/api/linkedin/activities/${activityId}`)
      .then((data) => { if (active) setRecord(data); })
      .catch((err) => {
        if (!active) return;
        if (String(err.message).includes("404")) setNotFound(true);
        else setError(true);
      });
    return () => { active = false; };
  }, [activityId]);

  if (notFound) return <p className="muted state">This activity is not available in the public dataset.</p>;
  if (error) return <ErrorState label="Unable to load this activity." />;
  if (!record) return <LoadingState label="Loading activity..." />;

  const dateText = formatPublicDate(record.activity_date);

  return (
    <div className="page">
      <p className="muted">
        <Link to="/categories">← Browse by category</Link>
        <span aria-hidden="true"> · </span>
        <Link to="/reports">Report generator</Link>
      </p>
      <article className="detail-card">
        <h2>{record.title}</h2>
        {record.summary && (
          <div className="detail-summary">
            <h3>Summary</h3>
            <p className="detail-description">{record.summary}</p>
          </div>
        )}
        <Card>
          <dl className="kv-list">
            {dateText ? (
              <div className="kv-row"><dt>Date</dt><dd>{dateText}</dd></div>
            ) : (
              <div className="kv-row"><dt>Date</dt><dd className="muted">Not specified</dd></div>
            )}
            <div className="kv-row"><dt>Academic Year</dt><dd>{record.academic_year || "Not specified"}</dd></div>
            <div className="kv-row"><dt>Category</dt><dd>{publicCategoryLabel(null, record.category) || "Not specified"}</dd></div>
            <div className="kv-row"><dt>Categories</dt><dd><Tags items={(record.categories || []).map((c) => publicCategoryLabel(c.code, c.name))} /></dd></div>
            <div className="kv-row"><dt>Department</dt><dd>{publicDepartmentLabel(record.department)}</dd></div>
            <div className="kv-row"><dt>Stakeholder</dt><dd>{record.stakeholder || "Not specified"}</dd></div>
            <div className="kv-row"><dt>Source</dt><dd>{publicSourceLabel(record.source)}</dd></div>
          </dl>
          {record.post_url ? (
            <p className="detail-link">
              <a href={record.post_url} target="_blank" rel="noreferrer">View Original LinkedIn Post →</a>
            </p>
          ) : (
            <p className="muted note">No public LinkedIn link is available for this activity.</p>
          )}
        </Card>
      </article>
    </div>
  );
}