import { useEffect, useState } from "react";
import { api } from "../services/api";
import { Card, DataTable } from "../components/ui";

export default function ReferencePage({ title, endpoint, columns, extra }) {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(endpoint)
      .then(setRows)
      .catch((e) => setError(e.message));
  }, [endpoint]);

  if (error) return <p className="error">{error}</p>;

  return (
    <div className="page">
      <h2>{title}</h2>
      {extra}
      <Card>
        <DataTable columns={columns} rows={rows} />
      </Card>
    </div>
  );
}