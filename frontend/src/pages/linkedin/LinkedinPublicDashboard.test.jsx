import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicDashboard from "./LinkedinPublicDashboard";
import { overviewBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

describe("LinkedinPublicDashboard", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders six KPIs and the general/departmental breakdowns from the API", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /\/api\/linkedin\/analytics\/overview/, respond: () => jsonResponse(overviewBody) },
    ]));

    render(<MemoryRouter><LinkedinPublicDashboard /></MemoryRouter>);

    await waitFor(() => expect(screen.getAllByText("1280").length).toBeGreaterThan(0));
    expect(screen.getByText("Total Activities")).toBeInTheDocument();
    expect(screen.getByText("General Activities")).toBeInTheDocument();
    expect(screen.getByText("Departmental Activities")).toBeInTheDocument();
    expect(screen.getByText("Departments Covered")).toBeInTheDocument();
    expect(screen.getByText("Stakeholders Covered")).toBeInTheDocument();
    expect(screen.getByText("Categories")).toBeInTheDocument();
    expect(screen.getByText("Activities by Academic Year")).toBeInTheDocument();
    expect(screen.getByText("General vs Departmental")).toBeInTheDocument();
    expect(screen.getByText("Top General Categories")).toBeInTheDocument();
    expect(screen.getByText("Top Departmental Categories")).toBeInTheDocument();
    expect(screen.getByText("Top Departments")).toBeInTheDocument();

    // BarList/Chart sections render real API values.
    expect(screen.getByText("Computer Science and Engineering")).toBeInTheDocument();
    expect(screen.getAllByText("300").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Students").length).toBeGreaterThan(0);
    expect(screen.getByText("1100")).toBeInTheDocument();
  });

  it("keeps General and Departmental activity worlds separate", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /overview/, respond: () => jsonResponse(overviewBody) },
    ]));

    render(<MemoryRouter><LinkedinPublicDashboard /></MemoryRouter>);

    await waitFor(() => expect(screen.getAllByText("300").length).toBeGreaterThan(0));
    expect(screen.getAllByText("980").length).toBeGreaterThan(0);
    expect(screen.getByText("General (institution-wide)")).toBeInTheDocument();
    expect(screen.getByText("Department-specific")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /browse general categories/i }).length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: /drill into departments/i })).toBeInTheDocument();
  });

  it("labels the date limitation honestly", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /overview/, respond: () => jsonResponse(overviewBody) },
    ]));

    render(<MemoryRouter><LinkedinPublicDashboard /></MemoryRouter>);

    await waitFor(() => expect(screen.getByText("Total Activities")).toBeInTheDocument());
    expect(screen.getByText(/include only reliably dated records/)).toBeInTheDocument();
    expect(screen.getByText(/Undated records are counted in totals but excluded from date-based charts/)).toBeInTheDocument();
  });
});