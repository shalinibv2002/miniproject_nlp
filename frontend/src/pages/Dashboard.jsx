import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { api } from "../services/api";
import { useGlobalFilters } from "../context/GlobalFilters";
import { KpiCard, Card } from "../components/ui";
import { ALL_PERIODS, periodLabel } from "../lib/periods";

const GENERAL_COLORS = [
  "#7b143b", "#c9a227", "#a03252", "#40846b", "#8c4317", "#5e7dab",
  "#b4566e", "#6b5b2f", "#7a3a63", "#3f5b3a", "#c2769b", "#4a6b52",
  "#9c6b3f", "#4d4f9c", "#b0413e", "#2f7d8c", "#8a3a2f", "#5a3a6b",
  "#a26a2f", "#5b6775",
];
const DEPT_CATEGORY_COLORS = ["#7b143b", "#a03252", "#c9a227", "#b4566e", "#8c5b2f", "#d98b6c", "#5e1227"];
const PERIOD_ORDER = Object.fromEntries(ALL_PERIODS.map((period, index) => [period, index]));

/* Series of the six periods in canonical presentation order. */
function periodSeries(breakdown) {
  const counts = new Map((breakdown || []).map((row) => [row.academic_year, row.activity_count]));
  return ALL_PERIODS.map((period) => ({ name: periodLabel(period), activities: counts.get(period) || 0 }));
}

/* Turn a resolved year x category list into a stacked chart series. */
function stackedSeries(rows) {
  const map = new Map();
  rows.forEach((row) => {
    const entry = map.get(row.academic_year) || { name: periodLabel(row.academic_year), order: PERIOD_ORDER[row.academic_year] };
    entry[row.category] = (entry[row.category] || 0) + row.activity_count;
    map.set(row.academic_year, entry);
  });
  return [...map.values()].sort((a, b) => a.order - b.order);
}

/* Category series names present in the trend data, ordered for the legend. */
function trendCategories(rows, palette) {
  const names = [];
  rows.forEach((row) => {
    if (!names.includes(row.category)) names.push(row.category);
  });
  names.sort((a, b) => a.localeCompare(b));
  return names.map((name, index) => ({ name, color: palette[index % palette.length] }));
}

function tooltipProps() {
  return {
    cursor: { fill: "rgba(123,20,59,0.06)" },
    contentStyle: { borderRadius: 10, border: "1px solid #e3e8f0", boxShadow: "0 10px 28px rgba(16,24,40,0.12)", fontSize: 13 },
    labelStyle: { color: "#5b6775", fontWeight: 600 },
    itemStyle: { color: "#17202b" },
  };
}

function VerticalCategoryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={320}>
      <BarChart data={data} layout="vertical" margin={{ left: 12, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecf2" />
        <XAxis type="number" allowDecimals={false}
          tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={{ stroke: "#d3dbe8" }} tickLine={false} />
        <YAxis type="category" dataKey="name" width={180}
          tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={false} tickLine={false} />
        <Tooltip {...tooltipProps()} />
        <Bar dataKey="activities" fill="#7b143b" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function PeriodChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecf2" />
        <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={{ stroke: "#d3dbe8" }} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={false} tickLine={false} width={40} />
        <Tooltip {...tooltipProps()} />
        <Bar dataKey="activities" fill="#a03252" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ChartLegend({ items }) {
  if (!items.length) return null;
  return (
    <ul className="chart-legend" aria-label="Category colours">
      {items.map((item) => (
        <li key={item.name}>
          <span className="legend-swatch" style={{ backgroundColor: item.color }} aria-hidden="true" />
          {item.name}
        </li>
      ))}
    </ul>
  );
}

function StackedCategoryChart({ data, categories }) {
  return (
    <>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={data} layout="vertical" margin={{ left: 12, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecf2" />
          <XAxis type="number" allowDecimals={false}
            tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={{ stroke: "#d3dbe8" }} tickLine={false} />
          <YAxis type="category" dataKey="name" width={168}
            tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={false} tickLine={false} />
          <Tooltip {...tooltipProps()} />
          {categories.map((category, index) => (
            <Bar key={category.name} dataKey={category.name} stackId="a" fill={category.color}
              radius={index === categories.length - 1 ? [4, 4, 0, 0] : [0, 0, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
      <ChartLegend items={categories} />
    </>
  );
}

function GeneralView({ data, categoryOptions, category, onCategoryChange }) {
  if (!data) return <p className="muted state">Loading dashboard...</p>;
  const categories = data.general_categories || [];
  const breakdown = data.year_category_breakdown || [];
  const trends = stackedSeries(breakdown);
  const legendItems = trendCategories(breakdown, GENERAL_COLORS);
  return (
    <>
      <div className="toolbar inline-toolbar">
        <label className="filter">
          <span>General Category</span>
          <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
            <option value="">All General Categories</option>
            {categoryOptions.map((row) => (
              <option key={row.code} value={row.code}>{row.name}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="kpi-grid">
        <KpiCard label="Total General Activities" value={data.total_activities} />
        <KpiCard label="Periods Covered" value={data.periods_covered.length}
          sub={data.periods_covered.map(periodLabel).join(", ")} />
        <KpiCard label="General Categories" value={categories.length} />
      </div>
      <Card title="Institution-wide Activities by Period" className="wide">
        <PeriodChart data={periodSeries(data.period_breakdown)} />
      </Card>
      <div className="chart-grid">
        <Card title="General Category Analytics">
          <VerticalCategoryChart data={categories.map((row) => ({ name: row.name, activities: row.activity_count }))} />
        </Card>
        {trends.length > 0 && (
          <Card title="Category Trends by Period">
            <StackedCategoryChart data={trends} categories={legendItems} />
          </Card>
        )}
      </div>
    </>
  );
}

function DepartmentView({ options, overview, detail, selected, onSelectDepartment, categoryOptions, category, onCategoryChange }) {
  if (!overview && !detail) return <p className="muted state">Loading dashboard...</p>;
  return (
    <>
      <div className="toolbar inline-toolbar">
        <label className="filter">
          <span>Department</span>
          <select value={selected || ""} onChange={(e) => onSelectDepartment(e.target.value)}>
            <option value="">All Departments</option>
            {options.map((row) => (
              <option key={row.department} value={row.department}>{row.department}</option>
            ))}
          </select>
        </label>
        <label className="filter">
          <span>Departmental Category</span>
          <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
            <option value="">All Departmental Categories</option>
            {categoryOptions.map((row) => (
              <option key={row.code} value={row.code}>{row.name}</option>
            ))}
          </select>
        </label>
      </div>
      {detail ? <DepartmentDetail data={detail} /> : <DepartmentOverview data={overview} />}
    </>
  );
}

function DepartmentOverview({ data }) {
  const departments = data.departments || [];
  const categories = data.departmental_categories || [];
  return (
    <>
      <div className="kpi-grid">
        <KpiCard label="Departments" value={departments.length} />
        <KpiCard label="Total Department Activities" value={data.total_activities} />
        <KpiCard label="Departmental Categories" value={categories.length} />
      </div>
      <Card title="Department Activities by Period" className="wide">
        <PeriodChart data={periodSeries(data.period_breakdown)} />
      </Card>
      <div className="chart-grid">
        <Card title="Activities by Department">
          <VerticalCategoryChart data={departments.map((row) => ({ name: row.department, activities: row.activity_count }))} />
        </Card>
        <Card title="Departmental Category Analytics">
          <VerticalCategoryChart data={categories.map((row) => ({ name: row.name, activities: row.activity_count }))} />
        </Card>
      </div>
    </>
  );
}

function DepartmentDetail({ data }) {
  const categories = data.departmental_categories || [];
  const breakdown = data.year_category_breakdown || [];
  const trends = stackedSeries(breakdown);
  const legendItems = trendCategories(breakdown, DEPT_CATEGORY_COLORS);
  return (
    <>
      <div className="kpi-grid">
        <KpiCard label="Total Activities" value={data.total_activities} sub={data.department} />
        <KpiCard label="Periods Covered" value={data.periods_covered.length}
          sub={data.periods_covered.map(periodLabel).join(", ")} />
        <KpiCard label="Departmental Categories" value={categories.length} />
      </div>
      <Card title={`${data.department} Activities by Period`} className="wide">
        <PeriodChart data={periodSeries(data.period_breakdown)} />
      </Card>
      <div className="chart-grid">
        <Card title="Departmental Category Analytics">
          <VerticalCategoryChart data={categories.map((row) => ({ name: row.name, activities: row.activity_count }))} />
        </Card>
        {trends.length > 0 && (
          <Card title="Category Trends by Period">
            <StackedCategoryChart data={trends} categories={legendItems} />
          </Card>
        )}
      </div>
    </>
  );
}

export default function Dashboard() {
  const { filters, setFilters } = useGlobalFilters();
  const [view, setView] = useState("general");
  const [general, setGeneral] = useState(null);
  const [generalCategory, setGeneralCategory] = useState("");
  const [generalCategoryOptions, setGeneralCategoryOptions] = useState([]);
  const [overview, setOverview] = useState(null);
  const [detail, setDetail] = useState(null);
  const [options, setOptions] = useState([]);
  const [deptCategoryOptions, setDeptCategoryOptions] = useState([]);
  const [deptCategory, setDeptCategory] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [error, setError] = useState(false);
  const period = filters.period;

  useEffect(() => {
    setFilters((current) => ({
      ...current, department: "", category: "",
      generalCategory: "", departmentalCategory: "", stakeholder: "",
    }));
  }, [setFilters]);

  useEffect(() => {
    const qs = period ? `?period=${encodeURIComponent(period)}` : "";
    api.get(`/api/general-categories${qs}`)
      .then(setGeneralCategoryOptions)
      .catch(() => setGeneralCategoryOptions([]));
    api.get(`/api/departments${qs}`)
      .then(setOptions)
      .catch(() => setOptions([]));
  }, [period]);

  useEffect(() => {
    let active = true;
    setError(false);
    const params = new URLSearchParams();
    if (generalCategory) params.set("general_category", generalCategory);
    if (period) params.set("academic_year", period);
    const query = params.toString() ? `?${params.toString()}` : "";
    api.get(`/api/analytics/general${query}`)
      .then((result) => { if (active) setGeneral(result); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [generalCategory, period]);

  useEffect(() => {
    const params = new URLSearchParams();
    if (selectedDepartment) params.set("department", selectedDepartment);
    if (period) params.set("academic_year", period);
    const query = params.toString() ? `?${params.toString()}` : "";
    api.get(`/api/departmental-categories${query}`)
      .then(setDeptCategoryOptions)
      .catch(() => setDeptCategoryOptions([]));
  }, [selectedDepartment, period]);

  useEffect(() => {
    let active = true;
    setError(false);
    setDetail(null);
    setOverview(null);
    const params = new URLSearchParams();
    if (selectedDepartment) params.set("department", selectedDepartment);
    if (deptCategory) params.set("departmental_category", deptCategory);
    if (period) params.set("academic_year", period);
    const query = params.toString() ? `?${params.toString()}` : "";
    api.get(`/api/analytics/department${query}`)
      .then((result) => {
        if (active) {
          if (selectedDepartment) setDetail(result);
          else setOverview(result);
        }
      })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [selectedDepartment, deptCategory, period]);

  function selectDepartment(value) {
    setSelectedDepartment(value);
    setDeptCategory("");
  }

  return (
    <div className="page">
      <h2>Institutional Activity Dashboard</h2>
      <p className="muted">Explore institution-wide initiatives and department activities across TCE.</p>
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
      <div className="view-tabs" role="tablist" aria-label="Dashboard views">
        <button type="button" role="tab" aria-selected={view === "general"}
          className={`tab-button${view === "general" ? " active" : ""}`}
          onClick={() => setView("general")}>General Activities</button>
        <button type="button" role="tab" aria-selected={view === "departments"}
          className={`tab-button${view === "departments" ? " active" : ""}`}
          onClick={() => setView("departments")}>Department Activities</button>
      </div>
      {error && <p className="error state">Unable to load dashboard data. Please try again.</p>}
      {view === "general" ? (
        <GeneralView data={general} categoryOptions={generalCategoryOptions}
          category={generalCategory} onCategoryChange={setGeneralCategory} />
      ) : (
        <DepartmentView options={options} overview={overview} detail={detail}
          selected={selectedDepartment} onSelectDepartment={selectDepartment}
          categoryOptions={deptCategoryOptions} category={deptCategory} onCategoryChange={setDeptCategory} />
      )}
      <p className="muted"><Link to="/activities">Browse all activities</Link></p>
    </div>
  );
}