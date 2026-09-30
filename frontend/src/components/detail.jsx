export function Field({ label, value }) {
  return (
    <div className="field">
      <span className="field-label">{label}</span>
      <span>{value || "—"}</span>
    </div>
  );
}

export function Tags({ items }) {
  const values = Array.isArray(items) ? items : items ? [items] : [];
  if (values.length === 0) return <span className="muted">—</span>;
  return (
    <span className="keywords">
      {values.map((item, i) => (
        <span key={i} className="tag">{String(item)}</span>
      ))}
    </span>
  );
}

/** Renders an arbitrary JSON value (string | number | list | object). */
export function JsonValue({ value }) {
  if (value == null) return <span className="muted">—</span>;
  if (typeof value === "object") {
    if (Array.isArray(value)) {
      if (value.length === 0) return <span className="muted">Unavailable</span>;
      return <Tags items={value.map((item) => String(item))} />;
    }
    const entries = Object.entries(value);
    if (entries.length === 0) return <span className="muted">No details</span>;
    return (
      <dl className="kv-list">
        {entries.map(([key, val]) => (
          <div key={key} className="kv-row">
            <dt>{key}</dt>
            <dd><JsonValue value={val} /></dd>
          </div>
        ))}
      </dl>
    );
  }
  return <span>{String(value)}</span>;
}

export function Pager({ page, pageSize, total, onPage, onPageSize, sizes = [25, 50, 100] }) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  const label = total === 0
    ? "No records"
    : `Showing ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}`;
  return (
    <div className="pager">
      <span>{label}</span>
      <div className="row-actions">
        {sizes.map((size) => (
          <button key={size} type="button"
            className={size === pageSize ? "primary" : "ghost"}
            onClick={() => onPageSize && onPageSize(size)}>
            {size}
          </button>
        ))}
      </div>
      <div className="row-actions">
        <button type="button" className="ghost" disabled={page <= 1}
          onClick={() => onPage && onPage(page - 1)}>← Prev</button>
        <span>Page {page} of {pages}</span>
        <button type="button" className="ghost" disabled={page >= pages}
          onClick={() => onPage && onPage(page + 1)}>Next →</button>
      </div>
    </div>
  );
}