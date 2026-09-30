import { Link } from "react-router-dom";
import { publicCategoryLabel, publicDepartmentLabel, publicSourceLabel, formatPublicDate } from "../lib/linkedin";

export function ActivityCardList({ records, showDepartment = true }) {
  if (!records || records.length === 0) return null;
  return (
    <div className="activity-grid">
      {records.map((record) => {
        const dateText = formatPublicDate(record.activity_date);
        const category = publicCategoryLabel(null, record.category);
        return (
          <Link key={record.activity_id} className="activity-card" to={`/activities/${record.activity_id}`}>
            <h3 className="activity-card-title">{record.title}</h3>
            {record.summary && <p className="activity-card-desc">{record.summary}</p>}
            <dl className="activity-meta">
              {dateText ? (
                <div className="kv-row"><dt>Date</dt><dd>{dateText}</dd></div>
              ) : (
                <div className="kv-row"><dt>Date</dt><dd className="muted">Not specified</dd></div>
              )}
              {record.academic_year && (
                <div className="kv-row"><dt>Year</dt><dd>{record.academic_year}</dd></div>
              )}
              <div className="kv-row"><dt>Category</dt><dd>{category || "Not specified"}</dd></div>
              {showDepartment && (
                <div className="kv-row"><dt>Department</dt><dd>{publicDepartmentLabel(record.department)}</dd></div>
              )}
              <div className="kv-row"><dt>Stakeholder</dt><dd>{record.stakeholder || "Not specified"}</dd></div>
            </dl>
            <span className="activity-card-source">{publicSourceLabel(record.source)}</span>
            <span className="activity-card-view">View details &rarr;</span>
          </Link>
        );
      })}
    </div>
  );
}