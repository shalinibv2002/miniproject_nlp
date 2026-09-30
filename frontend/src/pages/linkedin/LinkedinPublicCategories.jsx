import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { LoadingState, ErrorState } from "../../components/linkedinPublic";

export default function LinkedinPublicCategories() {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/categories")
      .then((data) => { if (active) setRows(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  if (error) return <ErrorState label="Unable to load categories." />;
  if (!rows) return <LoadingState label="Loading categories..." />;

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Categories</h2>
        <p className="muted">
          Explore activities in two completely separate worlds: institution-wide
          General activities, or activities that belong to a specific department.
        </p>
      </section>

      <div className="module-grid">
        <Card className="module-card">
          <h3 className="module-title">General Categories</h3>
          <p className="muted">
            Institution-wide activities only. Browse by academic period, category and stakeholder.
          </p>
          <Link to="/categories/general" className="btn primary">Browse General →</Link>
        </Card>
        <Card className="module-card">
          <h3 className="module-title">Departments</h3>
          <p className="muted">
            Department-specific activities only. Choose a department, then drill into period, category and stakeholder.
          </p>
          <Link to="/departments" className="btn primary">Browse Departments →</Link>
        </Card>
      </div>
    </div>
  );
}