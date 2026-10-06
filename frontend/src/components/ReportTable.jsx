import { DataTable } from "./ui";
import {
  DEPARTMENTAL,
  normalizeCategory,
  normalizeScope,
  reportColumns as schemaColumns,
  reportColumnsForRecords,
} from "../lib/reportSchema";

// Institutional activity report.  The column set is category-specific and
// comes from `lib/reportSchema` (the UI mirror of the canonical backend
// definition), so the table, the report preview, the XLSX/PDF exports and
// Ask-the-Data always show the same columns for the same category.
//
// Invariants:
//   * one row per unique activity -- multiple stakeholder / department /
//     category values never multiply a row;
//   * one primary category per activity, never an achievement-shaped row for a
//     workshop or a club;
//   * the LinkedIn URL is a trailing, read-only reference for validation; it
//     never feeds counting, classification or any report derivation.
export function PostUrlLink({ url }) {
  if (!url) return <span className="muted">&mdash;</span>;
  return (
    <a href={url} target="_blank" rel="noopener noreferrer" title={url}>
      View Post
    </a>
  );
}

// `columns` (from the report preview API) wins when present so the screen and
// the download can never disagree.  Otherwise the schema is resolved locally
// from the selected category / the rows themselves.
// `extraColumns` lets the Validator append its own Action column on top of the
// exact same report columns.
export function reportColumns({
  category,
  records,
  showDepartment = false,
  scope,
  columns: provided,
  showPostUrl = true,
  extraColumns = [],
  departmentCell,
} = {}) {
  const resolvedScope = normalizeScope(scope || (showDepartment ? DEPARTMENTAL : undefined));
  let columns = provided;
  if (!columns || columns.length === 0) {
    const code = normalizeCategory(category);
    columns = code
      ? schemaColumns(code, resolvedScope)
      : reportColumnsForRecords(records, resolvedScope);
  }
  const cols = columns.map((column) => ({
    key: column.field || "sno",
    label: column.label,
    render: column.field === "post_url"
      ? (row) => <PostUrlLink url={row.post_url} />
      : undefined,
  }));
  if (departmentCell) {
    const department = cols.find((col) => col.label === "Department");
    if (department) department.render = departmentCell;
  }
  if (!showPostUrl) {
    return cols.filter((col) => col.label !== "LinkedIn URL").concat(extraColumns);
  }
  return cols.concat(extraColumns);
}

// S.No counts across the whole report, not the current page.
export function reportRows(records, page, pageSize) {
  const offset = Math.max(0, ((page || 1) - 1) * (pageSize || 0));
  return (records || []).map((record, i) => ({ ...record, sno: offset + i + 1 }));
}

export function ReportTable({
  records,
  category,
  scope,
  showDepartment,
  columns,
  page,
  pageSize,
  extraColumns,
  departmentCell,
}) {
  return (
    <DataTable
      columns={reportColumns({
        category,
        records,
        showDepartment,
        scope,
        columns,
        extraColumns,
        departmentCell,
      })}
      rows={reportRows(records, page, pageSize)}
    />
  );
}

export default ReportTable;