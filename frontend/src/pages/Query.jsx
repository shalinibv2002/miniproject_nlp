import { useState } from "react";
import { Link } from "react-router-dom";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { api } from "../services/api";
import { Card, DataTable } from "../components/ui";
import { periodLabel } from "../lib/periods";

const EXAMPLES = [
  "How many activities are there?",
  "How many workshops happened in 2024-2025?",
  "Which year had the most workshops?",
  "Which department had the highest achievements in 2024-2025?",
  "Rank departments by number of achievements.",
  "Top 5 departments by research activities.",
  "Which department had the fewest workshops?",
];

function tooltipProps() {
  return {
    cursor: { fill: "rgba(123,20,59,0.06)" },
    contentStyle: { borderRadius: 10, border: "1px solid #e3e8f0", boxShadow: "0 10px 28px rgba(16,24,40,0.12)", fontSize: 13 },
    labelStyle: { color: "#5b6775", fontWeight: 600 },
    itemStyle: { color: "#17202b" },
  };
}

function chartSeries(chart) {
  return (chart?.data || []).map((row) => ({ name: row.label, activities: row.value }));
}

function AnswerChart({ chart }) {
  const data = chartSeries(chart);
  if (data.length === 0) return null;
  return (
    <div className="answer-chart">
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 44)}>
        <BarChart data={data} layout="vertical" margin={{ left: 12, right: 16, top: 4, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8ecf2" />
          <XAxis type="number" allowDecimals={false}
            tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={{ stroke: "#d3dbe8" }} tickLine={false} />
          <YAxis type="category" dataKey="name" width={200}
            tick={{ fontSize: 12, fill: "#5b6775" }} axisLine={false} tickLine={false} />
          <Tooltip {...tooltipProps()} />
          <Bar dataKey="activities" fill="#7b143b" radius={[0, 6, 6, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

const columns = [
  { key: "title", label: "Activity", render: (activity) => <Link to={`/activities/${activity.id}`}>{activity.title}</Link> },
  { key: "categories", label: "Category", render: (activity) => activity.categories?.map((category) => category.name).join(", ") || "Not available" },
  { key: "academic_year", label: "Period", render: (activity) => periodLabel(activity.academic_year) },
  { key: "department", label: "Department", render: (activity) => activity.department || "General" },
  { key: "general_category", label: "General Category" },
  { key: "departmental_category", label: "Departmental Category" },
  { key: "stakeholder", label: "Stakeholder", render: (activity) => activity.stakeholder || "Students" },
  { key: "source_url", label: "Source", render: (activity) => activity.source_url ? <a href={activity.source_url} target="_blank" rel="noreferrer">Official TCE Source</a> : "Not available" },
];

const rankingColumns = [
  { key: "label", label: "Group", render: (row) => row.label },
  { key: "value", label: "Count" },
];

function comparisonColumns(rows) {
  const first = rows?.[0] || {};
  if (first.academic_year) return [{ key: "period", label: "Period" }, { key: "activities", label: "Activities" }];
  if (first.department) return [{ key: "department", label: "Department" }, { key: "activities", label: "Activities" }];
  if (first.entity) return [{ key: "entity", label: "Entity" }, { key: "activities", label: "Activities" }];
  return [{ key: "category", label: "Category" }, { key: "activities", label: "Activities" }];
}

function comparisonRows(comparison) {
  return (comparison || []).map((row) => {
    if (row.academic_year) return { period: periodLabel(row.academic_year), activities: row.activity_count };
    if (row.department) return { department: row.department, activities: row.activity_count };
    if (row.entity) return { entity: row.entity, activities: row.activity_count };
    if (row.category) return { category: row.category, activities: row.activity_count };
    return row;
  });
}

function DetailCard({ detail }) {
  const categories = detail.categories?.map((category) => category.name).join(", ") || "Not available";
  return (
    <div className="detail-card">
      <h3><Link to={`/activities/${detail.id}`}>{detail.title}</Link></h3>
      <dl className="detail-grid">
        <dt>Period</dt><dd>{detail.academic_year ? periodLabel(detail.academic_year) : "Not available"}</dd>
        <dt>Department</dt><dd>{detail.department || "General"}</dd>
        <dt>Stakeholder</dt><dd>{detail.stakeholder || "Students"}</dd>
        <dt>Categories</dt><dd>{categories}</dd>
        <dt>Description</dt><dd>{detail.description || "Not available"}</dd>
      </dl>
      {detail.source_url && <p><a href={detail.source_url} target="_blank" rel="noreferrer">Official TCE Source</a></p>}
    </div>
  );
}

export default function Query() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function ask(text) {
    if (!text.trim()) return;
    setBusy(true);
    setError(false);
    setResult(null);
    try {
      setResult(await api.post("/api/query", { question: text }));
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  const comparison = comparisonRows(result?.comparison);
  const comparisonLabel = (row) => row.period || row.department || row.entity || row.category;
  const sameAsRows = !!result?.rows && comparison.length === result.rows.length &&
    comparison.every((row, index) =>
      comparisonLabel(row) === result.rows[index].label && row.activities === result.rows[index].value);
  const showComparison = comparison.length > 0 && !sameAsRows;

  return <div className="page">
    <h2>Ask the Data</h2>
    <p className="muted">Ask questions about TCE activities, categories, departments, academic periods, achievements, workshops, and research.</p>
    <form onSubmit={(event) => { event.preventDefault(); ask(question); }}>
      <div className="query-bar">
        <input value={question} onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask about TCE activities" className="query-input" aria-label="Ask the Data" />
        <button type="submit" className="primary" disabled={busy || !question.trim()}>Ask</button>
      </div>
    </form>
    <div className="examples">{EXAMPLES.map((example) => (
      <button key={example} className="ghost" onClick={() => { setQuestion(example); ask(example); }}>{example}</button>
    ))}</div>
    {busy && <p className="muted">Searching activity data...</p>}
    {error && <p className="error state">Unable to answer this question. Please try again.</p>}
    {result && <Card title="Answer">
      <p className="answer-text">{result.answer}</p>
      {result.criteria?.length > 0 && (
        <div className="criteria-chips" aria-label="Query criteria">
          {result.criteria.map((criterion) => <span key={criterion} className="chip">{criterion}</span>)}
        </div>
      )}
      {result.detail && <DetailCard detail={result.detail} />}
      {result.chart?.data?.length > 0 && <AnswerChart chart={result.chart} />}
      {result.rows?.length > 0 && <>
        <h3>Result Breakdown</h3>
        <DataTable rows={result.rows} columns={rankingColumns} />
      </>}
      {showComparison && comparison.length > 0 && <>
        <h3>Comparative View</h3>
        <DataTable rows={comparison} columns={comparisonColumns(result.comparison)} />
      </>}
      {result.activities?.length > 0 && <>
        <h3>Matching Activities</h3>
        <DataTable rows={result.activities} columns={columns} />
      </>}
    </Card>}
    <p className="muted"><Link to="/activities">Browse all activities</Link></p>
  </div>;
}