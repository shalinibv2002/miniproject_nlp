import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../services/api";
import { Card } from "../../components/ui";
import { BarList, LoadingState, ErrorState } from "../../components/linkedinPublic";
import { publicCategoryLabel, publicDepartmentLabel, publicSourceLabel, formatPublicDate } from "../../lib/linkedin";

const EXAMPLES = [
  "How many workshops were conducted in 2025-26?",
  "Which department had the most activities last year?",
  "Show sports activities",
  "What categories are available?",
  "More workshops or seminars?",
  "How many activities involved students?",
];

export default function LinkedinPublicQuery() {
  const [input, setInput] = useState("");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function ask(text) {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;
    setInput(trimmed);
    setQuestion(trimmed);
    setResult(null);
    setError(false);
    setLoading(true);
    try {
      const data = await api.post("/api/linkedin/query", { question: trimmed });
      setResult(data);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <section className="page-intro">
        <h2>Ask the Data</h2>
        <p className="muted">
          Ask a plain-English question about activities on the TCE LinkedIn channel. Answers are computed live
          from the same reportable dataset as the dashboard, activities and reports.
        </p>
      </section>

      <Card>
        <form className="query-form" onSubmit={(event) => { event.preventDefault(); ask(); }}>
          <label className="query-input">
            <span className="sr-only">Your question</span>
            <input
              type="text"
              aria-label="Your question"
              placeholder="e.g. How many seminars were conducted in 2024-25?"
              value={input}
              onChange={(event) => setInput(event.target.value)}
            />
          </label>
          <button type="submit" className="primary" disabled={loading}>{loading ? "Asking..." : "Ask"}</button>
        </form>
        <div className="example-queries">
          <span className="muted">Try:</span>
          {EXAMPLES.map((ex) => (
            <button key={ex} type="button" className="ghost" onClick={() => ask(ex)}>{ex}</button>
          ))}
        </div>
      </Card>

      {error && <ErrorState label="Unable to answer that question. Please try again." />}
      {loading && <LoadingState label="Thinking..." />}

      {result && !loading && (
        <ResultPanel result={result} question={question} />
      )}
    </div>
  );
}

function ResultPanel({ result, question }) {
  const criteria = result.criteria || [];
  const status = result.status;
  const activities = result.activities || [];
  const chart = result.chart;
  const rows = result.rows || [];
  const comparison = result.comparison || [];
  const exportQ = encodeURIComponent(question);
  const canExport = Boolean(result.count || result.activities?.length || result.rows?.length || result.comparison?.length);

  return (
    <Card>
      <p className="muted">Q: {question}</p>
      {criteria.length > 0 && (
        <p className="criteria-line">
          {criteria.map((label) => <span key={label} className="tag">{label}</span>)}
        </p>
      )}
      {canExport && (
        <div className="row-actions" style={{ margin: "0 0 10px" }}>
          <a className="btn primary" href={`/api/linkedin/query/export?q=${exportQ}&format=xlsx`}>Download Excel</a>
          <a className="btn" href={`/api/linkedin/query/export?q=${exportQ}&format=pdf`}>Download PDF</a>
        </div>
      )}

      <p className={status === "zero" || status === "unsupported" ? "muted answer-line" : "answer-line"}>
        {result.answer}
      </p>

      {activities.length > 0 && (
        <div className="activity-grid">
          {activities.map((record) => {
            const dateText = formatPublicDate(record.activity_date);
            return (
              <Link key={record.activity_id} className="activity-card" to={`/activities/${record.activity_id}`}>
                <h4 className="activity-card-title">{record.title}</h4>
                {dateText && <p className="muted">{dateText}</p>}
                <span className="activity-card-source">
                  {publicCategoryLabel(null, record.category)}
                  {" · "}{publicDepartmentLabel(record.department)}
                  {" · "}{publicSourceLabel(record.source)}
                </span>
              </Link>
            );
          })}
        </div>
      )}

      {(rows.length > 0 || chart?.data?.length > 0) && (
        <BarList items={(rows.length ? rows : chart.data).map((r) => ({ key: r.label, name: r.label, value: r.value }))} />
      )}

      {comparison.length > 0 && (
        <table className="data-table">
          <thead>
            <tr><th>Entity</th><th>Activities</th></tr>
          </thead>
          <tbody>
            {comparison.map((row) => (
              <tr key={row.entity}>
                <td>{row.entity}</td>
                <td>{row.activity_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Card>
  );
}