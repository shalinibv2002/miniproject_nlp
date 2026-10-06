import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminRecords from "./LinkedinAdminRecords";
import {
  recordBody, generalRecordBody, recordsBody, optionsBody, jsonResponse,
} from "./testFixtures";

function makeFetch(listBody = recordsBody) {
  const calls = [];
  const deleted = new Set();
  const fn = vi.fn((url, options = {}) => {
    calls.push(String(url));
    const method = (options.method || "GET").toUpperCase();
    if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
    if (method === "DELETE") {
      const activityId = String(url).split("/").pop();
      deleted.add(activityId);
      return jsonResponse({ activity_id: activityId, deleted: true, by: "admin" });
    }
    const remaining = {
      ...listBody,
      data: (listBody.data || []).filter((row) => !deleted.has(row.activity_id)),
      total: Math.max(0, (listBody.total || 0) - deleted.size),
    };
    return jsonResponse(remaining);
  });
  return { calls, fn };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/admin/linkedin/records"]}>
      <LinkedinAdminRecords />
    </MemoryRouter>,
  );
}

function tableHeaders() {
  return within(screen.getByRole("table"))
    .getAllByRole("columnheader")
    .map((th) => th.textContent);
}

describe("LinkedIn Admin Records", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("uses the same clean report table as the public report", async () => {
    // Fixture record is WORKSHOP with a real department.
    // WORKSHOP departmental schema: Title | Duration | Department | Date | Academic Year | LinkedIn URL
    // Admin page appends an Action column.
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    expect(tableHeaders()).toEqual([
      "S.No", "Title", "Duration", "Department", "Date", "Academic Year", "LinkedIn URL", "Action",
    ]);
    // Must NOT contain old universal columns.
    expect(tableHeaders()).not.toContain("Award Category");
    expect(tableHeaders()).not.toContain("Achievement Description");
  });

  it("renders the report display values for an activity", async () => {
    // WORKSHOP departmental: S.No | Title | Duration | Department | Date | Academic Year | LinkedIn URL
    // title="Machine Learning Workshop", department="CSE", duration from the post
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    const row = screen.getByRole("row", { name: /Machine Learning Workshop/ });
    expect(within(row).getByText("1")).toBeInTheDocument();
    expect(within(row).getByText("Machine Learning Workshop")).toBeInTheDocument();
    expect(within(row).getByText("Computer Science and Engineering")).toBeInTheDocument();
    // WORKSHOP no longer reports a Stakeholder column.
    expect(within(row).queryByText("students")).toBeNull();
    expect(within(row).getByText("15 January 2026")).toBeInTheDocument();
    expect(within(row).getByText("2025\u201326")).toBeInTheDocument();
    expect(within(row).getByRole("link", { name: "View Post" })).toHaveAttribute(
      "href", recordBody.post_url);
    // Award Category and Achievement Description are NOT shown for WORKSHOP.
    expect(within(row).queryByText("Workshop")).toBeNull();
    expect(within(row).queryByText(/has conducted a workshop/)).toBeNull();
  });

  it("never shows the raw post body or internal evidence columns", async () => {
    // The curated title IS now a column (Title-based schema).
    // The raw description text (full LinkedIn post body) must NOT appear.
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    // title IS shown as a report column in WORKSHOP schema — that is correct.
    expect(screen.getByText(recordBody.title)).toBeInTheDocument();
    // The raw post body/description must not appear as a table cell.
    expect(screen.queryByText(recordBody.description)).toBeNull();
    // Internal admin fields must not appear as columns.
    expect(tableHeaders()).not.toContain("Evidence Score");
    expect(tableHeaders()).not.toContain("Confidence");
    expect(tableHeaders()).not.toContain("Review Status");
  });

  it("shows General for institution-wide rows with no department", async () => {
    // generalRecordBody: FDP, no real department.
    // FDP departmental schema (admin always shows dept): S.No | Title | Department | Stakeholder | ...
    // Department cell shows "General" as fallback for institution-wide activities.
    const { fn } = makeFetch({
      ...recordsBody,
      data: [generalRecordBody],
      total: 1,
      pagination: { page: 1, page_size: 25, total: 1, pages: 1 },
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    // Row is found by the activity title (FDP records use Title column).
    const row = screen.getByRole("row", { name: /Five-Day FDP on Cloud Computing/ });
    expect(within(row).getByText("General")).toBeInTheDocument();
    expect(within(row).queryByRole("link", { name: "View Post" })).toBeNull();
  });

  it("numbers serial numbers across pages using the server pagination", async () => {
    const { fn } = makeFetch({
      ...recordsBody,
      pagination: { page: 3, page_size: 20, total: 1544, pages: 78 },
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    expect(within(screen.getByRole("row", { name: /Machine Learning/ }))
      .getByText("41")).toBeInTheDocument();
  });

  it("keeps the existing filters above the table", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    for (const label of ["Academic Year", "Category", "Stakeholder", "Status"]) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "WORKSHOP" } });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("category=WORKSHOP"))).toBe(true));
  });

  it("filters by Approved and Not Approved status", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "NOT_APPROVED" } });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("approval=NOT_APPROVED"))).toBe(true));
  });

  it("links Edit to the existing record editor", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href", "/admin/linkedin/records/LI-00001");
  });

  it("deletes immediately with no confirmation and refreshes the table", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    const confirmSpy = vi.spyOn(window, "confirm");
    renderPage();
    await screen.findByRole("table");

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() =>
      expect(fn.mock.calls.some(([, options]) => (options && options.method) === "DELETE")).toBe(true));
    expect(confirmSpy).not.toHaveBeenCalled();
    expect(calls.some((url) => url.includes("/activities/LI-00001"))).toBe(true);
    await waitFor(() => expect(screen.queryByRole("table")).toBeNull());
    expect(screen.getByText("No records match your filters.")).toBeInTheDocument();
    // the list is re-fetched from the server straight away
    const listCalls = calls.filter((url) => /\/activities(\?|$)/.test(url));
    expect(listCalls.length).toBeGreaterThanOrEqual(2);
  });

  it("keeps the row and reports the failure when a delete is rejected", async () => {
    const { fn } = makeFetch();
    fn.mockImplementation((url, options = {}) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      if ((options.method || "").toUpperCase() === "DELETE") {
        return jsonResponse({ error: "delete blocked" }, false);
      }
      return jsonResponse(recordsBody);
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(await screen.findByText("delete blocked")).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });

  it("shows the empty state when no records match", async () => {
    const { fn } = makeFetch({ data: [], total: 0, pagination: { page: 1, page_size: 25, total: 0, pages: 0 } });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("No records match your filters.")).toBeInTheDocument();
  });

  it("shows an error state when the list request fails", async () => {
    const { fn } = makeFetch();
    fn.mockImplementation((url) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      return jsonResponse({ error: "boom" }, false);
    });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Unable to load LinkedIn records.")).toBeInTheDocument();
  });
});