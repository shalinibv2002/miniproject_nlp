import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, buildQuery } from "../services/api";
import { useGlobalFilters } from "../context/GlobalFilters";
import { Card, DataTable } from "../components/ui";
import { periodLabel } from "../lib/periods";

function counts(items, label) {
  const values = new Map();
  items.forEach((item) => {
    const name = label(item) || "Students";
    values.set(name, (values.get(name) || 0) + 1);
  });
  return [...values.entries()].map(([name, activityCount]) => ({ name, activityCount }))
    .sort((a, b) => b.activityCount - a.activityCount || a.name.localeCompare(b.name));
}

/* Only the 7 departmental categories (derived public field) drive this page's drill. */
function categoryChoices(items) {
  const values = new Map();
  items.forEach((activity) => {
    String(activity.departmental_category || "").split("; ").filter(Boolean).forEach((name) => {
      const current = values.get(name) || { code: name, name, activityCount: 0 };
      current.activityCount += 1;
      values.set(name, current);
    });
  });
  return [...values.values()].sort((a, b) => b.activityCount - a.activityCount || a.name.localeCompare(b.name));
}

function ChoiceList({ title, choices, onSelect }) {
  return <Card title={title}><div className="choice-list">{choices.map((choice) => (
    <button key={choice.code || choice.name} className="ghost choice-card" onClick={() => onSelect(choice)}>
      {choice.name} — {choice.activityCount}
    </button>
  ))}</div></Card>;
}

export default function Departments() {
  const { filters, setFilters } = useGlobalFilters();
  const [departments, setDepartments] = useState(null);
  const [activities, setActivities] = useState(null);
  const [selectedStakeholder, setSelectedStakeholder] = useState("");
  const [error, setError] = useState(false);
  const selectedDepartment = filters.department;
  const selectedCategory = filters.category;
  const period = filters.period;

  useEffect(() => {
    const qs = period ? `?period=${encodeURIComponent(period)}` : "";
    api.get(`/api/departments${qs}`).then(setDepartments).catch(() => setError(true));
  }, [period]);

  useEffect(() => {
    if (!selectedDepartment) {
      setActivities(null);
      setSelectedStakeholder("");
      return undefined;
    }
    let active = true;
    setActivities(null);
    setSelectedStakeholder("");
    const query = buildQuery({ period, department: selectedDepartment, category: selectedCategory });
    api.get(`/api/activities${query ? `${query}&` : "?"}page=1&page_size=1000`)
      .then((result) => { if (active) setActivities(result.data || []); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [selectedDepartment, selectedCategory, period]);

  const categories = useMemo(() => categoryChoices(activities || []), [activities]);
  const activeCategory = useMemo(() => categories.find((category) =>
    category.code === selectedCategory || category.name.toLowerCase() === selectedCategory.toLowerCase(),
  ), [categories, selectedCategory]);
  const categoryActivities = useMemo(() => activeCategory
    ? (activities || []).filter((activity) => String(activity.departmental_category || "").includes(activeCategory.name))
    : [], [activities, activeCategory]);
  const stakeholders = useMemo(() => counts(categoryActivities, (activity) => activity.stakeholder), [categoryActivities]);
  const finalActivities = useMemo(() => selectedStakeholder
    ? categoryActivities.filter((activity) => (activity.stakeholder || "Students") === selectedStakeholder)
    : [], [categoryActivities, selectedStakeholder]);

  function selectDepartment(department) {
    setError(false);
    setFilters((current) => ({
      ...current, department: department.department, category: "",
      generalCategory: "", departmentalCategory: "", stakeholder: "",
    }));
  }
  function selectCategory(category) {
    setFilters((current) => ({ ...current, category: category.code, generalCategory: "", departmentalCategory: "" }));
  }
  function backToDepartments() {
    setFilters((current) => ({
      ...current, department: "", category: "",
      generalCategory: "", departmentalCategory: "", stakeholder: "",
    }));
  }
  function backToCategories() {
    setFilters((current) => ({ ...current, category: "", generalCategory: "", departmentalCategory: "" }));
  }

  if (error) return <p className="error state">Unable to load department data. Please try again.</p>;
  if (!departments) return <p className="muted state">Loading departments...</p>;
  if (!selectedDepartment) {
    return <div className="page">
      <h2>Departments</h2>
      <p className="muted">Explore TCE activities by department, category and stakeholder.</p>
      {departments.length === 0 ? <p className="muted state">No activities found.</p> : <div className="chart-grid">
        {departments.map((department) => <Card key={department.department} title={department.department}>
          <p>{department.activity_count} activities</p>
          <button className="primary" onClick={() => selectDepartment(department)}>Explore department</button>
        </Card>)}
      </div>}
    </div>;
  }
  if (!activities) return <p className="muted state">Loading activities...</p>;

  return <div className="page">
    <p className="back-row"><button className="ghost" onClick={backToDepartments}>← Departments</button></p>
    <h2>{selectedDepartment}</h2>
    <p className="muted">Explore {selectedDepartment} activities by category and stakeholder.</p>
    <p className="drill-path">Departments{period ? ` · ${periodLabel(period)}` : ""} → {selectedDepartment}{activeCategory && ` → ${activeCategory.name}`}{selectedStakeholder && ` → ${selectedStakeholder}`}</p>
    {activities.length === 0 ? <p className="muted state">No activities found.</p> : <>
      {!activeCategory && <ChoiceList title="Categories" choices={categories} onSelect={selectCategory} />}
      {activeCategory && !selectedStakeholder && <>
        <p className="back-row"><button className="ghost" onClick={backToCategories}>← Categories</button></p>
        <ChoiceList title="Stakeholders" choices={stakeholders} onSelect={(choice) => setSelectedStakeholder(choice.name)} />
      </>}
      {selectedStakeholder && <>
        <p className="back-row"><button className="ghost" onClick={() => setSelectedStakeholder("")}>← Stakeholders</button></p>
        <Card title="Activities"><DataTable rows={finalActivities} columns={[
          { key: "title", label: "Activity", render: (activity) => <Link to={`/activities/${activity.id}`}>{activity.title}</Link> },
          { key: "category", label: "Category", render: () => activeCategory.name },
          { key: "academic_year", label: "Period", render: (activity) => periodLabel(activity.academic_year) },
          { key: "department", label: "Department", render: (activity) => activity.department || "Not available" },
          { key: "stakeholder", label: "Stakeholder", render: (activity) => activity.stakeholder || "Students" },
          { key: "source_url", label: "Source", render: (activity) => activity.source_url ? <a href={activity.source_url} target="_blank" rel="noreferrer">Official TCE Source</a> : "Not available" },
        ]} /></Card>
      </>}
    </>}
  </div>;
}