import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, buildQuery } from "../services/api";
import { useGlobalFilters } from "../context/GlobalFilters";
import { Card, DataTable } from "../components/ui";
import { periodLabel } from "../lib/periods";

function categoryLabel(categories) {
  return categories?.map((category) => category.name).filter(Boolean).join(", ") || "Not available";
}

export default function Activities() {
  const { filters } = useGlobalFilters();
  const [state, setState] = useState(null);
  const [page, setPage] = useState(1);
  const [error, setError] = useState(false);
  const filterKey = JSON.stringify([
    filters.period, filters.department, filters.category,
    filters.generalCategory, filters.departmentalCategory, filters.stakeholder, filters.order,
  ]);
  const filterKeyRef = useRef(filterKey);

  useEffect(() => {
    setState(null);
    setError(false);
    const filtersChanged = filterKeyRef.current !== filterKey;
    filterKeyRef.current = filterKey;
    if (filtersChanged && page !== 1) {
      setPage(1);
      return undefined;
    }
    let active = true;
    const query = buildQuery(filters);
    api.get(`/api/activities${query ? `${query}&` : "?"}page=${page}&page_size=20`)
      .then((response) => { if (active) setState(response); })
      .catch(() => { if (active) setError(true); });
    return () => { active = false; };
  }, [filterKey, page, filters]);

  if (error) return <p className="error state">Unable to load activities. Please try again.</p>;
  if (!state) return <p className="muted state">Loading activities...</p>;
  if (state.data?.length === 0) {
    return <p className="muted state">No activities found. Try adjusting your filters.</p>;
  }

  const columns = [
    {
      key: "title", label: "Activity",
      render: (row) => <Link to={`/activities/${row.id}`}>{row.title}</Link>,
    },
    { key: "categories", label: "Category", render: (row) => categoryLabel(row.categories) },
    { key: "academic_year", label: "Period", render: (row) => periodLabel(row.academic_year) },
    { key: "department", label: "Department", render: (row) => row.department || "General" },
    { key: "general_category", label: "General Category" },
    { key: "departmental_category", label: "Departmental Category" },
    { key: "stakeholder", label: "Stakeholder", render: (row) => row.stakeholder || "Students" },
    {
      key: "source_url", label: "Source",
      render: (row) => row.source_url ? (
        <a href={row.source_url} target="_blank" rel="noreferrer">Official TCE Source</a>
      ) : "Not available",
    },
  ];
  const pagination = state.pagination || {};
  const first = ((pagination.page || 1) - 1) * (pagination.page_size || 20) + 1;
  const last = Math.min(first + (state.data?.length || 0) - 1, state.total || 0);

  return (
    <div className="page">
      <h2>Activities</h2>
      <p className="muted">Browse institutional activities, events, achievements and initiatives across TCE.</p>
      <Card>
        <DataTable columns={columns} rows={state.data} />
        <div className="pager">
          <span>Showing {first}–{last} of {state.total} activities</span>
          <button className="ghost" disabled={(pagination.page || 1) <= 1} onClick={() => setPage((value) => value - 1)}>
            Previous
          </button>
          <span>{pagination.page || 1} / {Math.max(1, pagination.pages || 0)}</span>
          <button className="ghost" disabled={(pagination.page || 1) >= (pagination.pages || 0)} onClick={() => setPage((value) => value + 1)}>
            Next
          </button>
        </div>
      </Card>
    </div>
  );
}
