import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, buildQuery } from "../services/api";
import { useGlobalFilters } from "../context/GlobalFilters";
import { Card, DataTable } from "../components/ui";
import { ALL_PERIODS, periodLabel } from "../lib/periods";

function counts(items, label) {
  const result = new Map();
  items.forEach((item) => {
    const value = label(item) || "Students";
    result.set(value, (result.get(value) || 0) + 1);
  });
  return [...result.entries()].map(([name, activityCount]) => ({ name, activityCount }))
    .sort((a, b) => b.activityCount - a.activityCount || a.name.localeCompare(b.name));
}

function ChoiceList({ title, choices, onSelect }) {
  return (
    <Card title={title}>
      <div className="choice-list">
        {choices.map((choice) => (
          <button key={choice.name} className="ghost choice-card" onClick={() => onSelect(choice.name)}>
            {choice.name} — {choice.activityCount}
          </button>
        ))}
      </div>
    </Card>
  );
}

function CategoryGrid({ categories, mode, onSelect }) {
  if (categories.length === 0) return <p className="muted state">No categories with activities found.</p>;
  return (
    <div className="chart-grid">
      {categories.map((category) => (
        <Card key={category.code} title={category.name}>
          <p>{category.activity_count} activities</p>
          <button className="primary" onClick={() => onSelect({ kind: mode, category })}>Explore category</button>
        </Card>
      ))}
    </div>
  );
}

export default function Categories() {
  const { filters, setFilters } = useGlobalFilters();
  const [generalCategories, setGeneralCategories] = useState(null);
  const [departmentalCategories, setDepartmentalCategories] = useState(null);
  const [drill, setDrill] = useState(null);
  const [activities, setActivities] = useState(null);
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [selectedStakeholder, setSelectedStakeholder] = useState("");
  const [error, setError] = useState(false);
  const period = filters.period;

  useEffect(() => {
    setError(false);
    const qs = period ? `?period=${encodeURIComponent(period)}` : "";
    Promise.all([
      api.get(`/api/general-categories${qs}`),
      api.get(`/api/departmental-categories${qs}`),
    ])
      .then(([general, departmental]) => { setGeneralCategories(general); setDepartmentalCategories(departmental); })
      .catch(() => setError(true));
  }, [period]);

  useEffect(() => {
    if (!drill) {
      setActivities(null);
      setSelectedDepartment("");
      setSelectedStakeholder("");
      return undefined;
    }
    let active = true;
    setActivities(null);
    setSelectedDepartment("");
    setSelectedStakeholder("");
    const query = drill.kind === "general"
      ? buildQuery({ period, generalCategory: drill.category.code })
      : buildQuery({ period, departmentalCategory: drill.category.code });
    api.get(`/api/activities${query ? `${query}&` : "?"}page=1&page_size=1000`)
      .then((result) => { if (active) setActivities(result.data || []); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [drill, period]);

  const departmentLabel = (activity) => activity.department || (drill && drill.kind === "general" ? "General" : "Not available");
  const departments = useMemo(() => counts(activities || [], departmentLabel), [activities, drill]);
  const departmentActivities = useMemo(() => selectedDepartment
    ? (activities || []).filter((activity) => departmentLabel(activity) === selectedDepartment)
    : [], [activities, selectedDepartment, drill]);
  const stakeholders = useMemo(() => counts(departmentActivities, (activity) => activity.stakeholder), [departmentActivities]);
  const finalActivities = useMemo(() => selectedStakeholder
    ? departmentActivities.filter((activity) => (activity.stakeholder || "Students") === selectedStakeholder)
    : [], [departmentActivities, selectedStakeholder]);

  if (error) return <p className="error state">Unable to load category data. Please try again.</p>;
  if (!generalCategories || !departmentalCategories) return <p className="muted state">Loading categories...</p>;

  if (!drill) {
    return (
      <div className="page">
        <h2>Categories</h2>
        <p className="muted">Explore TCE activities by general and departmental category.</p>
        <div className="toolbar inline-toolbar">
          <label className="filter">
            <span>Academic Period</span>
            <select value={period} onChange={(event) => setFilters((current) => ({ ...current, period: event.target.value }))}>
              <option value="">All Periods</option>
              {ALL_PERIODS.map((p) => (
                <option key={p} value={p}>{periodLabel(p)}</option>
              ))}
            </select>
          </label>
        </div>
        {generalCategories.length + departmentalCategories.length === 0
          ? <p className="muted state">No categories with activities found for the selected period.</p> : (
            <>
              <h3 className="section-title">General Categories</h3>
              <p className="muted">Institution-wide activities that engage the TCE community.</p>
              <CategoryGrid categories={generalCategories} mode="general" onSelect={setDrill} />
              <h3 className="section-title">Departmental Categories</h3>
              <p className="muted">Activities organised by the 14 academic departments.</p>
              <CategoryGrid categories={departmentalCategories} mode="departmental" onSelect={setDrill} />
            </>
          )}
      </div>
    );
  }

  if (!activities) return <p className="muted state">Loading activities...</p>;
  const kindLabel = drill.kind === "general" ? "General Categories" : "Departmental Categories";
  return (
    <div className="page">
      <p className="back-row"><button className="ghost" onClick={() => setDrill(null)}>← Categories</button></p>
      <h2>{drill.category.name}</h2>
      <p className="muted">Explore {drill.category.name} activities by department and stakeholder.</p>
      <p className="drill-path">{kindLabel}{period ? ` · ${periodLabel(period)}` : ""} → {drill.category.name}{selectedDepartment && ` → ${selectedDepartment}`}{selectedStakeholder && ` → ${selectedStakeholder}`}</p>
      {activities.length === 0 ? <p className="muted state">No activities found.</p> : (
        <>
          {!selectedDepartment && <ChoiceList title="Departments" choices={departments} onSelect={setSelectedDepartment} />}
          {selectedDepartment && !selectedStakeholder && (
            <>
              <p className="back-row"><button className="ghost" onClick={() => setSelectedDepartment("")}>← Departments</button></p>
              <ChoiceList title="Stakeholders" choices={stakeholders} onSelect={setSelectedStakeholder} />
            </>
          )}
          {selectedStakeholder && (
            <>
              <p className="back-row"><button className="ghost" onClick={() => setSelectedStakeholder("")}>← Stakeholders</button></p>
              <Card title="Activities">
                <DataTable
                  rows={finalActivities}
                  columns={[
                    { key: "title", label: "Activity", render: (activity) => <Link to={`/activities/${activity.id}`}>{activity.title}</Link> },
                    { key: "category", label: "Category", render: () => drill.category.name },
                    { key: "academic_year", label: "Period", render: (activity) => periodLabel(activity.academic_year) },
                    { key: "department", label: "Department", render: (activity) => departmentLabel(activity) },
                    { key: "stakeholder", label: "Stakeholder", render: (activity) => activity.stakeholder || "Students" },
                    { key: "source_url", label: "Source", render: (activity) => activity.source_url ? <a href={activity.source_url} target="_blank" rel="noreferrer">Official TCE Source</a> : "Not available" },
                  ]}
                />
              </Card>
            </>
          )}
        </>
      )}
    </div>
  );
}