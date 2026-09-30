export function BarList({ items, nameKey = "name" }) {
  const rows = Array.isArray(items) ? items : [];
  const total = rows.reduce((sum, row) => sum + (row.value || 0), 0);
  if (rows.length === 0) return <p className="muted">No data available.</p>;
  return (
    <ul className="admin-bar-list">
      {rows.map((row, i) => (
        <li key={row.key || row[nameKey] || i}>
          <div className="bar-row">
            <span className="bar-name">{row[nameKey]}</span>
            <span className="bar-value">{row.value}</span>
          </div>
          <div className="bar-track">
            <div className="bar-fill" style={{ width: total ? `${(row.value / total) * 100}%` : "0%" }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function LoadingState({ label }) {
  return <p className="muted state">{label || "Loading..."}</p>;
}

export function ErrorState({ label }) {
  return <p className="error state">{label || "Unable to load data."}</p>;
}

export function EmptyState({ label }) {
  return <p className="muted state">{label || "No data available."}</p>;
}

export function ClickableCountList({ items, hrefFor, nameKey = "name" }) {
  if (!items || items.length === 0) return <EmptyState label="No data available." />;
  const total = items.reduce((sum, row) => sum + (row.value || 0), 0);
  return (
    <ul className="clickable-count-list">
      {items.map((row, i) => {
        const label = row[nameKey];
        const count = row.value || 0;
        const pct = total ? Math.round((100 * count) / total) : 0;
        const href = hrefFor(row);
        const body = (
          <>
            <span className="bar-name">{label}</span>
            <span className="bar-value">{count} <em>({pct}%)</em></span>
            <span className="bar-track"><span className="bar-fill" style={{ width: `${pct}%` }} /></span>
          </>
        );
        return (
          <li key={row.key || label || i}>
            {href ? <a className="bar-row clickable" href={href}>{body}</a> : <div className="bar-row">{body}</div>}
          </li>
        );
      })}
    </ul>
  );
}