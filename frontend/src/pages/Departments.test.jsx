import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Departments from "./Departments";
import { GlobalFiltersProvider } from "../context/GlobalFilters";

const activities = [
  { id: 1, title: "Student Workshop", academic_year: "2021-22", activity_date: "2022-06-07", department: "Mechanical Engineering", stakeholder: "Students", departmental_category: "Workshop", source_url: "https://www.tce.edu/workshop" },
  { id: 2, title: "Faculty Workshop", academic_year: null, activity_date: null, department: "Mechanical Engineering", stakeholder: "Students", departmental_category: "Workshop", source_url: null },
];
const response = (body) => ({ ok: true, json: async () => body });
const renderDepartments = () => render(<MemoryRouter><GlobalFiltersProvider><Departments /></GlobalFiltersProvider></MemoryRouter>);

describe("Departments drill-down", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn((url) => {
    if (url.endsWith("/api/departments")) {
      return Promise.resolve(response([{ department: "Mechanical Engineering", activity_count: 2 }]));
    }
    return Promise.resolve(response({ data: activities }));
  })));

  it("drills from a department through departmental category and stakeholder to public activities", async () => {
    renderDepartments();
    expect(await screen.findByText("Mechanical Engineering")).toBeInTheDocument();
    expect(screen.getByText("2 activities")).toBeInTheDocument();
    expect(screen.queryByText("General")).not.toBeInTheDocument();
    screen.getByRole("button", { name: "Explore department" }).click();
    expect(await screen.findByRole("button", { name: "Workshop — 2" })).toBeInTheDocument();
    expect(screen.queryByText("WORKSHOP")).not.toBeInTheDocument();
    screen.getByRole("button", { name: "Workshop — 2" }).click();
    expect(await screen.findByRole("button", { name: "Students — 2" })).toBeInTheDocument();
    screen.getByRole("button", { name: "Students — 2" }).click();
    expect(await screen.findByText("Student Workshop")).toHaveAttribute("href", "/activities/1");
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.getByText("Official TCE Source")).toHaveAttribute("href", "https://www.tce.edu/workshop");
    expect(screen.queryByText(/confidence|verification|classifier|review/i)).not.toBeInTheDocument();
  });

  it("shows public loading, empty, and error states", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch.mockReturnValueOnce(pending);
    const { unmount } = renderDepartments();
    expect(screen.getByText("Loading departments...")).toBeInTheDocument();
    unmount();
    globalThis.fetch.mockResolvedValueOnce(response([]));
    renderDepartments();
    expect(await screen.findByText("No activities found.")).toBeInTheDocument();
  });

  it("does not expose technical failures", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    renderDepartments();
    expect(await screen.findByText("Unable to load department data. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });

  it("shows clean public department names and never department codes or the General group", async () => {
    globalThis.fetch.mockImplementation((url) => {
      if (url.endsWith("/api/departments")) {
        return Promise.resolve(response([{ code: "MECH", department: "Mechanical Engineering", activity_count: 2 }]));
      }
      return Promise.resolve(response({ data: activities }));
    });
    renderDepartments();
    expect(await screen.findByText("Mechanical Engineering")).toBeInTheDocument();
    expect(screen.queryByText("MECH")).not.toBeInTheDocument();
    expect(screen.queryByText("General")).not.toBeInTheDocument();
    screen.getByRole("button", { name: "Explore department" }).click();
    expect(await screen.findByRole("button", { name: "Workshop — 2" })).toBeInTheDocument();
    expect(screen.queryByText("MECH")).not.toBeInTheDocument();
  });

  it("never lets stale general/departmental category filters leak into the drill query", async () => {
    globalThis.fetch = vi.fn((url) => {
      if (url.endsWith("/api/departments")) {
        return Promise.resolve(response([{ department: "Mechanical Engineering", activity_count: 2 }]));
      }
      return Promise.resolve(response({ data: activities }));
    });
    render(
      <MemoryRouter>
        <GlobalFiltersProvider initialFilters={{
          period: "", department: "", category: "",
          generalCategory: "ACHIEVEMENT", departmentalCategory: "INDUSTRY", stakeholder: "Faculty", order: "desc",
        }}>
          <Departments />
        </GlobalFiltersProvider>
      </MemoryRouter>,
    );
    expect(await screen.findByText("Mechanical Engineering")).toBeInTheDocument();
    screen.getByRole("button", { name: "Explore department" }).click();
    await waitFor(() => {
      const activityCall = globalThis.fetch.mock.calls.find(([url]) => String(url).includes("/api/activities"));
      expect(activityCall).toBeTruthy();
      expect(String(activityCall[0])).toBe("/api/activities?department=Mechanical+Engineering&page=1&page_size=1000");
    });
    expect(await screen.findByRole("button", { name: "Workshop — 2" })).toBeInTheDocument();
  });
});