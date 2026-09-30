import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import Layout from "./Layout";
import { GlobalFiltersProvider } from "../context/GlobalFilters";
import { AuthProvider } from "../context/Auth";

function renderLayout() {
  return render(
    <MemoryRouter>
      <GlobalFiltersProvider>
        <AuthProvider><Layout /></AuthProvider>
      </GlobalFiltersProvider>
    </MemoryRouter>
  );
}

describe("public layout", () => {
  it("shows only the public navigation items and no admin or internal routes", async () => {
    renderLayout();

    const nav = await screen.findByRole("navigation", { name: "Main navigation" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/", "/categories", "/departments", "/query",
    ]);

    const labels = links.map((link) => link.textContent);
    expect(labels).toEqual([
      "Dashboard", "Categories", "Departments", "Ask the Data",
    ]);
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument();

    for (const internal of ["Stakeholders", "LinkedIn", "Review Queue", "Reports", "Data Sources", "Review", "Activities"]) {
      expect(within(nav).queryByText(internal)).not.toBeInTheDocument();
    }
    for (const path of ["/admin", "/activities", "/stakeholders", "/linkedin", "/review", "/reports", "/sources", "/department-profiles", "/category-profiles"]) {
      expect(within(nav).getAllByRole("link").some((link) => link.getAttribute("href") === path)).toBe(false);
    }
  });

  it("does not expose an Admin console entry in the user navigation", async () => {
    renderLayout();

    await screen.findByRole("navigation", { name: "Main navigation" });
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument();
    expect(screen.queryByText(/manage activities|add activity/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/review queue|verification status/i)).not.toBeInTheDocument();
  });

  it("no longer exposes a global filter toolbar in the shared layout", async () => {
    renderLayout();

    await screen.findByRole("navigation", { name: "Main navigation" });
    for (const removed of ["Period", "Department", "General Category", "Departmental Category", "Sort Order", "Reset"]) {
      expect(screen.queryByRole("combobox", { name: removed })).not.toBeInTheDocument();
      expect(screen.queryByText(removed)).not.toBeInTheDocument();
    }
    for (const internal of ["Verification", "Confidence", "Review Status", "Candidate"]) {
      expect(screen.queryByText(internal)).not.toBeInTheDocument();
    }
  });
});