import { useEffect, useMemo, useState } from "react";
import { api } from "../../services/api";
import { KpiCard, Card } from "../../components/ui";
import { BarList, LoadingState, ErrorState, EmptyState } from "../../components/linkedinPublic";
import { ActivityCardList } from "../../components/ActivityList";
import { publicCategoryLabel, publicDepartmentLabel } from "../../lib/linkedin";

const REPORT_TYPES = [
  ["all", "All Activities"],
  ["achievements", "Achievements"],
  ["research", "Research & Consultancy"],
  ["industry", "Industry Collaboration"],
  ["clubs", "Clubs & Chapters"],
  ["workshops", "Workshops"],
  ["conferences", "Conferences"],
  ["seminars", "Seminars"],
  ["guest_lectures", "Guest Lectures"],
  ["fdp", "FDPs"],
  ["hackathons", "Hackathons"],
  ["cultural", "Cultural"],
  ["sports", "Sports"],
  ["placements", "Placements"],
  ["internships", "Internships"],
  ["webinars", "Webinars"],
  ["campus", "Campus"],
];

const GENERAL_PRESETS = [
  "IA Annual Report",
  "IA Workshop Report",
  "IA Event Series",
];

function buildQuery(filters) {
  const parts = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) parts.set(key, value);
  });
  const qs = parts.toString();
  return qs ? `?${qs}` : "";
}

export default function LinkedinPublicReports() {
  const [options, setOptions] = useState(null);
  const [scope, setScope] = useState("general");
  const [reportType, setReportType] = useState("all");
  const [academicYear, setAcademicYear] = useState("");
  const [department, setDepartment] = useState("");
  const [stakeholder, setStakeholder] = useState("");
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState(false);

  const filters = useMemo(
    () => ({
      report_type: reportType,
      scope,
      academic_year: academicYear,
      department: scope === "departmental" ? department : "",
      stakeholder,
    }),
    [reportType, scope, academicYear, department, stakeholder],
  );

  useEffect(() => {
    let active = true;
    api.get("/api/linkedin/filters")
      .then((data) => { if (active) setOptions(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    setPreview(null);
    setError(false);
    let active = true;
    api.get(`/api/linkedin/reports/preview${buildQuery(filters)}`)
      .then((data) => { if (active) setPreview(data); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [filters]);

  const downloadUrl = useMemo(() => {
    const qs = buildQuery(filters);
    return (fmt) => `/api/linkedin/reports/export${qs}${qs ? "&" : "?"}format=${fmt}`;
  }, [filters]);

  if (error && !preview) return <ErrorState label="Unable to load reports." />;
  if (!options || (!preview && !error)) return <LoadingState label="Building report..." />;

  const breakdown = preview?.breakdown || {};
  const cats = breakdown.categories || [];
  const depts = breakdown.departments || [];
  const staks = breakdown.stakeholders || [];
  const records = preview?.records || [];

  function selectScope(next) {
    setScope(next);
    setPreview(null);
  }

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Report Generator</h2>
        <p className="muted">
          Generate an institutional activity report from the same reportable dataset shown everywhere else.
          Pick a General (institution-wide) or Department report, choose a report type, preview the result, then download it as Excel or PDF.
        </p>
      </section>

      <div className="module-grid">
        <button
          type="button"
          className={`module-card choice-card${scope === "general" ? " selected" : ""}`}
          onClick={() => selectScope("general")}
        >
          <h3 className="module-title">General Reports</h3>
          <p className="muted">
            Institution-wide reporting. Presets include {GENERAL_PRESETS.join(", ")}.
          </p>
          <span className="muted">Covers only General (institution-wide) activities.</span>
        </button>
        <button
          type="button"
          className={`module-card choice-card${scope === "departmental" ? " selected" : ""}`}
          onClick={() => selectScope("departmental")}
        >
          <h3 className="module-title">Department Reports</h3>
          <p className="muted">
            Department-specific reporting. Pick an organising department, then a report type.
          </p>
          <span className="muted">Covers only departmental activities.</span>
        </button>
      </div>

      <Card className="filter-card">
        <div className="filter-panel">
          {scope === "departmental" && (
            <label className="filter-field">
              <span className="filter-label">Department</span>
              <select aria-label="Department" value={department}
                onChange={(event) => setDepartment(event.target.value)}>
                <option value="">All departments</option>
                {departmentOptions(options).map((d) => (
                  <option key={d} value={d}>{publicDepartmentLabel(d)}</option>
                ))}
              </select>
            </label>
          )}
          <label className="filter-field">
            <span className="filter-label">Report type</span>
            <select
              aria-label="Report type"
              value={reportType}
              onChange={(event) => setReportType(event.target.value)}
            >
              {REPORT_TYPES.map(([code, label]) => (
                <option key={code} value={code}>{label}</option>
              ))}
            </select>
          </label>
          <label className="filter-field">
            <span className="filter-label">Academic year</span>
            <select aria-label="Academic year" value={academicYear}
              onChange={(event) => setAcademicYear(event.target.value)}>
              <option value="">All years</option>
              {(options.years || []).map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </label>
          <label className="filter-field">
            <span className="filter-label">Stakeholder</span>
            <select aria-label="Stakeholder" value={stakeholder}
              onChange={(event) => setStakeholder(event.target.value)}>
              <option value="">All stakeholders</option>
              {(options.stakeholders || []).map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </label>
        </div>
      </Card>

      {preview && (
        <>
          <div className="kpi-grid">
            <KpiCard label="Report" value={preview.report_label} />
            <KpiCard label="Scope" value={scope === "general" ? "General" : "Departmental"} />
            <KpiCard label="Total activities" value={preview.total} />
            <KpiCard label="Categories" value={cats.length} />
            <KpiCard label="Departments" value={depts.length} />
            <KpiCard label="Stakeholders" value={staks.length} />
          </div>

          <div className="row-actions" style={{ margin: "4px 0 16px" }}>
            <a className="btn primary" href={downloadUrl("xlsx")}>Download Excel</a>
            <a className="btn" href={downloadUrl("pdf")}>Download PDF</a>
          </div>

          {(cats.length > 0 || depts.length > 0 || staks.length > 0) && (
            <div className="chart-grid">
              {cats.length > 0 && (
                <Card title="By Category">
                  <BarList items={cats.map((c) => ({ key: c.category, name: publicCategoryLabel(c.category, c.name), value: c.activity_count })).sort((a, b) => b.value - a.value)} />
                </Card>
              )}
              {depts.length > 0 && (
                <Card title="By Department">
                  <BarList items={depts.map((d) => ({ key: d.department, name: publicDepartmentLabel(d.department), value: d.activity_count })).sort((a, b) => b.value - a.value)} />
                </Card>
              )}
              {staks.length > 0 && (
                <Card title="By Stakeholder">
                  <BarList items={staks.map((s) => ({ key: s.stakeholder, name: s.stakeholder, value: s.activity_count })).sort((a, b) => b.value - a.value)} />
                </Card>
              )}
            </div>
          )}

          <Card title="Report Preview">
            <p className="muted note">{preview.context}</p>
            {records.length === 0
              ? <EmptyState label="No activities match these filters." />
              : <ActivityCardList records={records.slice(0, 12)} showDepartment={scope === "departmental"} />}
          </Card>
        </>
      )}
    </div>
  );
}

function departmentOptions(options) {
  return (options.departments || []).filter((d) => d !== "General");
}