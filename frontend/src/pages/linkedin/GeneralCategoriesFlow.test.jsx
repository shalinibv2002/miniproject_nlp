import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import GeneralCategoriesFlow from "./GeneralCategoriesFlow";
import { activitiesBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

// URL selects category=WORKSHOP — general WORKSHOP schema:
// S.No | Title | Stakeholder | Date | Academic Year | LinkedIn URL
const REPORTED = "/categories/general?period=2025-26&category=WORKSHOP&stakeholder=Students";

function mockApi() {
  global.fetch = vi.fn().mockImplementation(routeFetch([
    {
      match: /\/api\/linkedin\/activities/,
      respond: () => jsonResponse(activitiesBody),
    },
    {
      match: /\/api\/linkedin\/(years|categories|stakeholders)/,
      respond: () => jsonResponse([]),
    },
  ]));
}

function renderGeneral() {
  return render(
    <MemoryRouter initialEntries={[REPORTED]}>
      <GeneralCategoriesFlow />
    </MemoryRouter>
  );
}

describe("GeneralCategoriesFlow report results", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders the report table with WORKSHOP general columns (no Award Category / Achievement Description)", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());

    const hdrs = within(screen.getByRole("table"))
      .getAllByRole("columnheader")
      .map((th) => th.textContent);
    // WORKSHOP general: S.No | Title | Duration | Date | Academic Year | LinkedIn URL
    expect(hdrs).toEqual([
      "S.No", "Title", "Duration", "Date", "Academic Year", "LinkedIn URL",
    ]);
    // Must NOT contain old universal columns.
    expect(hdrs).not.toContain("Award Category");
    expect(hdrs).not.toContain("Achievement Description");
    expect(hdrs).not.toContain("Name");
  });

  it("has no Department column in the general report", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());
    const hdrs = within(screen.getByRole("table"))
      .getAllByRole("columnheader")
      .map((th) => th.textContent);
    expect(hdrs).not.toContain("Department");
  });

  it("shows the report count matching the filtered dataset", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());
    expect(screen.getByText(/2 General Workshops activities/i)).toBeInTheDocument();
    expect(screen.getByText(/Showing 1\u20132 of 2/)).toBeInTheDocument();
  });

  it("does not show the raw LinkedIn post body (summary/description) in the table", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());
    // The raw LinkedIn post summary text must not appear — only curated fields.
    expect(screen.queryByText(/has conducted a workshop on the topic/)).toBeNull();
  });

  it("links the Post URL in a new tab for validation", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());
    const link = within(screen.getByRole("table")).getByRole("link", { name: "View Post" });
    expect(link).toHaveAttribute("target", "_blank");
  });

  it("displays the academic year with an en dash", async () => {
    mockApi();
    renderGeneral();
    await waitFor(() => expect(screen.getByRole("table")).toBeInTheDocument());
    expect(screen.getByText("2025\u201326")).toBeInTheDocument();
  });
});