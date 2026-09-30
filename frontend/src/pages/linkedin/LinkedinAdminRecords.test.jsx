import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminRecords from "./LinkedinAdminRecords";
import { recordsBody, optionsBody, jsonResponse } from "./testFixtures";

function makeFetch(listBody = recordsBody) {
  const calls = [];
  const fn = vi.fn((url) => {
    calls.push(String(url));
    if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
    return jsonResponse(listBody);
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

describe("LinkedIn Admin Records", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("renders record rows with mapped category names and confidence", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Machine Learning Workshop")).toBeInTheDocument();
    const row = screen.getByRole("row", { name: /Machine Learning Workshop/ });
    expect(within(row).getByText("Workshop")).toBeInTheDocument();
    expect(within(row).queryByText("WORKSHOP")).not.toBeInTheDocument();
    expect(within(row).getByText("REPORTABLE")).toBeInTheDocument();
    expect(screen.getByText("High (9)")).toBeInTheDocument();
    expect(screen.getByText("1544 records found")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Machine Learning Workshop" })).toHaveAttribute(
      "href", "/admin/linkedin/records/LI-00001");
    expect(fn.mock.calls.some(([url]) => /\/api\/admin\/linkedin\/activities$/.test(String(url)))).toBe(true);
  });

  it("paginates through the server with the Next button", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByText("Machine Learning Workshop");
    fireEvent.click(screen.getByRole("button", { name: "Next →" }));
    await waitFor(() =>
      expect(calls.some((url) => url.includes("activities?page=2"))).toBe(true));
  });

  it("applies a status filter through the API", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByText("Machine Learning Workshop");
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "NON_ACTIVITY" } });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("status=NON_ACTIVITY"))).toBe(true));
  });

  it("sorts by a column header", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByText("Machine Learning Workshop");
    fireEvent.click(screen.getByRole("button", { name: "Activity" }));
    await waitFor(() =>
      expect(calls.some((url) => url.includes("sort=title&order=asc"))).toBe(true));
  });

  it("shows the empty state when no records match", async () => {
    const { fn } = makeFetch({ data: [], total: 0, pagination: { page: 1, page_size: 25, total_pages: 0 } });
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