import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { LoadingState, ErrorState, ClickableCountList } from "../../components/linkedinPublic";

export default function LinkedinPublicStakeholders() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/stakeholders")
      .then((data) => { if (active) setRows(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  if (error) return <ErrorState label="Unable to load stakeholders." />;
  if (!rows) return <LoadingState label="Loading stakeholders..." />;

  const items = rows
    .map((row) => ({
      key: row.stakeholder,
      name: row.stakeholder,
      value: row.activity_count,
      stakeholder: row.stakeholder,
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Stakeholders</h2>
        <p className="muted">Who the TCE LinkedIn activities were created for. Select a stakeholder group to browse related activities.</p>
      </section>
      <Card>
        <ClickableCountList items={items} hrefFor={(row) => `/activities?stakeholder=${encodeURIComponent(row.stakeholder)}`} />
      </Card>
    </div>
  );
}