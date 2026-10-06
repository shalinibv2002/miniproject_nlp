import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminDepartmental from "./LinkedinAdminDepartmental";
import {
  recordBody, recordsBody, optionsBody, jsonResponse,
} from "./testFixtures";

// A departmental record: has a real department (not General).
const deptRecord = {
  ...recordBody,
  departments: ["Computer Science and Engineering"],
  report_department: "Computer Science and Engineering",
};
const deptRecordsBody = {
  ...recordsBody,
  data: [deptRecord],
};

function makeFetch(listBody = deptRecordsBody) {
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
    <MemoryRouter initialEntries={["/admin/linkedin/departmental"]}>
      <LinkedinAdminDepartmental />
    </MemoryRouter>,
  );
}

describe("LinkedIn Admin Departmental", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("always sends scope=departmental in the API request", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    const listCalls = calls.filter((url) => /\/activities/.test(url) && !/\/options/.test(url));
    expect(listCalls.some((url) => url.includes("scope=departmental"))).toBe(true);
  });

  it("uses the category-specific report table columns (WORKSHOP departmental)", async () => {
    // Fixture record is WORKSHOP with a real department.
    // WORKSHOP departmental schema: Title | Duration | Department | Date | Academic Year | LinkedIn URL
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    const headers = within(screen.getByRole("table"))
      .getAllByRole("columnheader")
      .map((th) => th.textContent);
    expect(headers).toEqual([
      "S.No", "Title", "Duration", "Department", "Date", "Academic Year", "LinkedIn URL", "Action",
    ]);
    expect(headers).not.toContain("Award Category");
    expect(headers).not.toContain("Achievement Description");
    expect(headers).not.toContain("Name");
  });

  it("shows the five departmental filters", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    for (const label of ["Status", "Academic Year", "Department", "Departmental Category", "Stakeholder"]) {
      expect(screen.getByLabelText(label)).toBeInTheDocument();
    }
  });

  it("excludes General from the department filter options", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    const deptSelect = screen.getByLabelText("Department");
    const optionTexts = Array.from(deptSelect.querySelectorAll("option")).map((o) => o.textContent);
    expect(optionTexts).not.toContain("General");
    expect(optionTexts).toContain("Computer Science and Engineering");
  });

  it("filters by approval status and passes it to the API", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "APPROVED" } });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("approval=APPROVED"))).toBe(true));
  });

  it("filters by department and passes it to the API", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    fireEvent.change(screen.getByLabelText("Department"), {
      target: { value: "Computer Science and Engineering" },
    });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("department=Computer"))).toBe(true));
  });

  it("links Edit to the departmental editor route", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("table");
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute(
      "href", "/admin/linkedin/departmental/LI-00001",
    );
  });

  it("deletes immediately with no confirmation and removes the row", async () => {
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
  });

  it("shows an error state when the list request fails", async () => {
    const { fn } = makeFetch();
    fn.mockImplementation((url) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      return jsonResponse({ error: "boom" }, false);
    });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Unable to load departmental records.")).toBeInTheDocument();
  });

  it("shows the empty state when no records match", async () => {
    const { fn } = makeFetch({
      data: [], total: 0,
      pagination: { page: 1, page_size: 25, total: 0, pages: 0 },
    });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("No records match your filters.")).toBeInTheDocument();
  });
});
