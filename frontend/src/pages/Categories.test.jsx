import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Categories from "./Categories";
import { GlobalFiltersProvider } from "../context/GlobalFilters";

const generalActivities = [
  { id: 1, title: "Student Achievement", academic_year: "2021-22", activity_date: "2022-06-07", department: "General", stakeholder: "Students", source_url: "https://www.tce.edu/a" },
  { id: 2, title: "Faculty Achievement", academic_year: "Not available", activity_date: null, department: "General", stakeholder: "Students", source_url: null },
];
const departmentActivities = [
  { id: 3, title: "IT Innovation Camp", academic_year: "2021-22", activity_date: "2022-06-07", department: "Information Technology", stakeholder: "Students", source_url: "https://www.tce.edu/it" },
];
const response = (body) => ({ ok: true, json: async () => body });

function makeCategoriesFetch() {
  return vi.fn((url) => {
    if (url.startsWith("/api/general-categories")) {
      return Promise.resolve(response([{ code: "ACHIEVEMENT", name: "Achievement and Awards", activity_count: 2 }]));
    }
    if (url.startsWith("/api/departmental-categories")) {
      return Promise.resolve(response([{ code: "WORKSHOP", name: "Workshops", activity_count: 1 }]));
    }
    if (url.includes("general_category=ACHIEVEMENT")) return Promise.resolve(response({ data: generalActivities }));
    if (url.includes("departmental_category=WORKSHOP")) return Promise.resolve(response({ data: departmentActivities }));
    return Promise.resolve(response({ data: [] }));
  });
}

function renderCategories() {
  return render(<MemoryRouter><GlobalFiltersProvider><Categories /></GlobalFiltersProvider></MemoryRouter>);
}

describe("Categories drill-down", () => {
  beforeEach(() => vi.stubGlobal("fetch", makeCategoriesFetch()));

  it("shows General and Departmental category sections and drills a General category to activities", async () => {
    renderCategories();
    expect(await screen.findByText("General Categories")).toBeInTheDocument();
    expect(screen.getByText("Departmental Categories")).toBeInTheDocument();
    expect(screen.getByText("Achievement and Awards")).toBeInTheDocument();
    expect(screen.getByText("2 activities")).toBeInTheDocument();
    expect(screen.getByText("Workshops")).toBeInTheDocument();
    expect(screen.getByText("1 activities")).toBeInTheDocument();
    expect(screen.queryByText("ACHIEVEMENT")).not.toBeInTheDocument();

    const exploreButtons = screen.getAllByRole("button", { name: "Explore category" });
    exploreButtons[0].click();

    expect(await screen.findByRole("button", { name: "General — 2" })).toBeInTheDocument();
    screen.getByRole("button", { name: "General — 2" }).click();
    expect(await screen.findByRole("button", { name: "Students — 2" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Students — 2" }).click();
    expect(await screen.findByText("Student Achievement")).toHaveAttribute("href", "/activities/1");
    expect(screen.getByText("Faculty Achievement")).toHaveAttribute("href", "/activities/2");
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.getByText("Official TCE Source")).toHaveAttribute("href", "https://www.tce.edu/a");
    expect(screen.getAllByText("Achievement and Awards").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText(/confidence|verification|classifier|review/i)).not.toBeInTheDocument();
    for (const code of ["ACHIEVEMENT", "SPORTS", "WORKSHOP", "TECH_FEST", "STTP", "SYMPOSIUM"]) {
      expect(screen.queryByText(code)).not.toBeInTheDocument();
    }
  });

  it("drills a Departmental category through department and stakeholder", async () => {
    renderCategories();
    const exploreButtons = await screen.findAllByRole("button", { name: "Explore category" });
    exploreButtons[1].click();

    expect(await screen.findByRole("button", { name: "Information Technology — 1" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Information Technology — 1" }).click();
    expect(await screen.findByRole("button", { name: "Students — 1" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Students — 1" }).click();
    expect(await screen.findByText("IT Innovation Camp")).toHaveAttribute("href", "/activities/3");
    expect(screen.getByText("Information Technology")).toBeInTheDocument();
    expect(screen.queryByText("General Categories")).not.toBeInTheDocument();
  });

  it("shows loading, empty, and friendly error states", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch.mockReturnValueOnce(pending);
    const { unmount } = renderCategories();
    expect(screen.getByText("Loading categories...")).toBeInTheDocument();
    unmount();

    globalThis.fetch.mockImplementation((url) => {
      if (url.endsWith("/api/general-categories")) return Promise.resolve(response([]));
      if (url.endsWith("/api/departmental-categories")) return Promise.resolve(response([]));
      return Promise.resolve(response({ data: [] }));
    });
    renderCategories();
    expect(await screen.findByText(/No categories with activities found/)).toBeInTheDocument();
  });

  it("does not expose technical failures", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    renderCategories();
    expect(await screen.findByText("Unable to load category data. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });

  it("persists the selected period into the category metrics and the drill data", async () => {
    renderCategories();

    expect(await screen.findByText("Achievement and Awards")).toBeInTheDocument();
    const periodSelect = screen.getByRole("combobox", { name: "Academic Period" });
    fireEvent.change(periodSelect, { target: { value: "2024-25" } });

    await waitFor(() => {
      const generalCall = globalThis.fetch.mock.calls.find(([url]) => String(url).includes("/api/general-categories") && String(url).includes("period=2024-25"));
      expect(generalCall).toBeTruthy();
    });

    screen.getAllByRole("button", { name: "Explore category" })[0].click();

    await waitFor(() => {
      const activityCall = globalThis.fetch.mock.calls.find(([url]) => String(url).includes("/api/activities") && String(url).includes("academic_year=2024-25"));
      expect(activityCall).toBeTruthy();
    });
    expect(await screen.findByRole("button", { name: "General — 2" })).toBeInTheDocument();
    expect(screen.getByText(/General Categories · 2024-2025 → Achievement and Awards/)).toBeInTheDocument();
  });

  it("keeps stale global filters out of the drill query", async () => {
    render(
      <MemoryRouter>
        <GlobalFiltersProvider initialFilters={{
          period: "", department: "Information Technology", category: "CONFERENCE",
          generalCategory: "", departmentalCategory: "", stakeholder: "Faculty", order: "desc",
        }}>
          <Categories />
        </GlobalFiltersProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText("Achievement and Awards")).toBeInTheDocument();

    screen.getAllByRole("button", { name: "Explore category" })[0].click();

    await waitFor(() => {
      const activityCall = globalThis.fetch.mock.calls.find(([url]) => String(url).includes("/api/activities"));
      expect(activityCall).toBeTruthy();
      expect(String(activityCall[0])).toBe("/api/activities?general_category=ACHIEVEMENT&page=1&page_size=1000");
    });
    expect(await screen.findByRole("button", { name: "General — 2" })).toBeInTheDocument();
  });
});