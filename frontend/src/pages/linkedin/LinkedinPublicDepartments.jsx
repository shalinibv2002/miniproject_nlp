import { useEffect, useState } from "react";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { LoadingState, ErrorState, ClickableCountList } from "../../components/linkedinPublic";
import { publicDepartmentLabel } from "../../lib/linkedin";

export default function LinkedinPublicDepartments() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/departments")
      .then((data) => { if (active) setRows(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  if (error) return <ErrorState label="Unable to load departments." />;
  if (!rows) return <LoadingState label="Loading departments..." />;

  const items = rows
    .filter((row) => row.department !== "General")
    .map((row) => ({
      key: row.department,
      name: publicDepartmentLabel(row.department),
      value: row.activity_count,
      department: row.department,
    }))
    .sort((a, b) => b.value - a.value);

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Departments</h2>
        <p className="muted">
          Activities by organising department. Select a department to drill into its
          academic periods, categories and stakeholders.
        </p>
      </section>
      <Card>
        <ClickableCountList items={items} hrefFor={(row) => `/departments/${encodeURIComponent(row.department)}`} />
      </Card>
    </div>
  );
}