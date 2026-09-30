import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicReports from "./LinkedinPublicReports";
import { filtersBody, publicRecordBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

const previewBody = {
  report_type: "all",
  report_label: "All Activities",
  context: "General (institution-wide) activities",
  filters: { status: "REPORTABLE", scope: "general" },
  total: 300,
  records: [publicRecordBody],
  breakdown: {
    categories: [{ category: "WORKSHOP", name: "Workshops", activity_count: 200 }],
    departments: [],
    stakeholders: [{ stakeholder: "Students", activity_count: 150 }],
  },
};

function mockApi(track = []) {
  global.fetch = vi.fn().mockImplementation(routeFetch([
    { match: /\/api\/linkedin\/filters/, respond: () => jsonResponse(filtersBody) },
    {
      match: /\/api\/linkedin\/reports\/preview/,
      respond: (url) => {
        track.push(url);
        if (url.includes("scope=departmental&department=")) {
          return jsonResponse({ ...previewBody, total: 700, context: "Departmental activities" });
        }
        return jsonResponse(previewBody);
      },
    },
  ]));
  return track;
}

describe("LinkedinPublicReports (report generator)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("offers General and Department report scopes and previews the general report", async () => {
    mockApi();
    render(<MemoryRouter><LinkedinPublicReports /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText("Report Generator")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /General Reports/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Department Reports/ })).toBeInTheDocument();

    await waitFor(() => expect(screen.getAllByText("300").length).toBeGreaterThan(0));
    expect(screen.getAllByText("All Activities").length).toBeGreaterThan(0);
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("150")).toBeInTheDocument();

    const excel = screen.getByRole("link", { name: "Download Excel" });
    expect(excel.getAttribute("href")).toContain("/api/linkedin/reports/export");
    expect(excel.getAttribute("href")).toContain("scope=general");
    const pdf = screen.getByRole("link", { name: "Download PDF" });
    expect(pdf.getAttribute("href")).toContain("format=pdf");
  });

  it("switches to a department report with a department filter and refreshes", async () => {
    const calls = mockApi();
    render(<MemoryRouter><LinkedinPublicReports /></MemoryRouter>);
    await waitFor(() => expect(screen.getAllByText("300").length).toBeGreaterThan(0));

    fireEvent.click(screen.getByRole("button", { name: /Department Reports/ }));
    await waitFor(() => {
      expect(calls.some((url) => url.includes("scope=departmental"))).toBe(true);
    });

    fireEvent.change(screen.getByRole("combobox", { name: "Department" }), {
      target: { value: "Information Technology" },
    });
    await waitFor(() => {
      expect(calls.some((url) => url.includes("department=Information+Technology"))).toBe(true);
    });
    await waitFor(() => expect(screen.getAllByText("700").length).toBeGreaterThan(0));
  });

  it("uses only public records in the dataset (no internal fields render)", async () => {
    mockApi();
    render(<MemoryRouter><LinkedinPublicReports /></MemoryRouter>);
    await waitFor(() => expect(screen.getByText("Report Generator")).toBeInTheDocument());
    await waitFor(() => expect(screen.getAllByText("300").length).toBeGreaterThan(0));
    for (const internal of ["Evidence", "Confidence", "Review Status", "Manual overrides", "Validation History"]) {
      expect(screen.queryByText(internal)).not.toBeInTheDocument();
    }
  });
});