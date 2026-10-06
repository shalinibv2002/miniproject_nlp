import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ReportTable, reportRows } from "./ReportTable";
import { activitiesBody } from "../pages/linkedin/publicFixtures";

// ── helpers ─────────────────────────────────────────────────────────────────

function headers() {
  return within(screen.getByRole("table"))
    .getAllByRole("columnheader")
    .map((th) => th.textContent);
}

function bodyRows() {
  return within(screen.getByRole("table"))
    .getAllByRole("row")
    .slice(1)
    .map((tr) => within(tr).getAllByRole("cell").map((td) => td.textContent));
}

// activitiesBody.data[0] is a WORKSHOP record (general scope when showDepartment=false).
// WORKSHOP general schema: S.No | Title | Duration | Date | Academic Year | LinkedIn URL
// activitiesBody.data[1] is an FDP record.  Mixed set → DEFAULT_GENERAL:
//   S.No | Title | Date | Academic Year | LinkedIn URL

describe("ReportTable", () => {
  it("shows WORKSHOP general columns (Title + Duration, no Stakeholder, no Achievement Description)", () => {
    render(<ReportTable records={[activitiesBody.data[0]]} category="WORKSHOP" showDepartment={false} />);
    expect(headers()).toEqual([
      "S.No", "Title", "Duration", "Date", "Academic Year", "LinkedIn URL",
    ]);
  });

  it("adds Department column for departmental WORKSHOP reports", () => {
    render(<ReportTable records={[activitiesBody.data[0]]} category="WORKSHOP" showDepartment />);
    expect(headers()).toEqual([
      "S.No", "Title", "Duration", "Department", "Date", "Academic Year", "LinkedIn URL",
    ]);
  });

  it("shows ACHIEVEMENT general columns (Stakeholder | Name | Award Category | Achievement Description)", () => {
    render(
      <ReportTable
        records={[{ ...activitiesBody.data[0], categories: [{ code: "ACHIEVEMENT" }] }]}
        category="ACHIEVEMENT"
        showDepartment={false}
      />
    );
    expect(headers()).toEqual([
      "S.No", "Stakeholder", "Name", "Award Category",
      "Achievement Description", "Date", "Academic Year", "LinkedIn URL",
    ]);
  });

  it("shows ACHIEVEMENT departmental columns (includes Department between Name and Award Category)", () => {
    render(
      <ReportTable
        records={[{ ...activitiesBody.data[0], categories: [{ code: "ACHIEVEMENT" }] }]}
        category="ACHIEVEMENT"
        showDepartment
      />
    );
    expect(headers()).toEqual([
      "S.No", "Stakeholder", "Name", "Department", "Award Category",
      "Achievement Description", "Date", "Academic Year", "LinkedIn URL",
    ]);
  });

  it("renders one row per activity with a sequential serial number", () => {
    render(<ReportTable records={activitiesBody.data} showDepartment={false} />);
    const rows = bodyRows();
    expect(rows).toHaveLength(2);
    expect(rows.map((r) => r[0])).toEqual(["1", "2"]);
  });

  it("numbers rows across the whole report, not per page", () => {
    expect(reportRows([{}, {}], 3, 12).map((r) => r.sno)).toEqual([25, 26]);
    expect(reportRows([{}], 1, 12).map((r) => r.sno)).toEqual([1]);
  });

  it("shows the en dash academic year (index 3) and a blank date (index 2) for DEFAULT_GENERAL mixed set", () => {
    // Mixed WORKSHOP+FDP records → DEFAULT_GENERAL = [S.No, Title, Date, Academic Year, LinkedIn URL]
    render(<ReportTable records={activitiesBody.data} showDepartment={false} />);
    const rows = bodyRows();
    // row[0]: record with academic_year_display "2025–26" at col index 3
    expect(rows[0][3]).toBe("2025\u201326");
    // row[1]: FDP record with no date — blank at col index 2
    expect(rows[1][2]).toBe("");
  });

  it("never renders the raw LinkedIn post summary in report columns", () => {
    // The summary/description (full post body) must not appear in any report column.
    render(<ReportTable records={activitiesBody.data} showDepartment={false} />);
    // These are the raw description strings from publicFixtures — not a column field.
    expect(screen.queryByText(/has conducted a workshop on the topic/)).toBeNull();
    expect(screen.queryByText(/Faculty Development Programme for faculty/)).toBeNull();
  });

  it("links the post URL and opens the LinkedIn post in a new tab", () => {
    render(<ReportTable records={activitiesBody.data} showDepartment={false} />);
    const link = screen.getByRole("link", { name: "View Post" });
    expect(link).toHaveAttribute("href", activitiesBody.data[0].post_url);
    expect(link).toHaveAttribute("target", "_blank");
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("shows a dash instead of a link when no post URL is known", () => {
    // Mixed DEFAULT_GENERAL: [S.No, Title, Date, Academic Year, LinkedIn URL] → URL at index 4
    render(<ReportTable records={activitiesBody.data} showDepartment={false} />);
    expect(screen.getAllByRole("link", { name: "View Post" })).toHaveLength(1);
    const rows = bodyRows();
    expect(rows[1][4]).toBe("—");
  });
});