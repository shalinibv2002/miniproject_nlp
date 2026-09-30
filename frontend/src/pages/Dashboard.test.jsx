import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "./Dashboard";
import { GlobalFiltersProvider } from "../context/GlobalFilters";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  BarChart: ({ children, data = [] }) => <div>{data.map((row) => <span key={row.name}>{row.name}</span>)}{children}</div>,
  Bar: function Bar() { return <span data-testid="bar" />; },
  XAxis: () => null, YAxis: () => null, Tooltip: () => null, CartesianGrid: () => null,
}));

const generalPayload = {
  total_activities: 879,
  periods_covered: ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"],
  period_breakdown: [
    { academic_year: "2021-22", activity_count: 46 }, { academic_year: "2022-23", activity_count: 56 },
    { academic_year: "2023-24", activity_count: 105 }, { academic_year: "2024-25", activity_count: 99 },
    { academic_year: "2025-26", activity_count: 6 },
  ],
  general_categories: [
    { code: "SPORTS", name: "Sports and Games", activity_count: 293 },
    { code: "ACHIEVEMENT", name: "Achievement and Awards", activity_count: 5 },
  ],
  year_category_breakdown: [
    { academic_year: "2021-22", category: "Sports and Games", activity_count: 10 },
  ],
};

const departmentsPayload = [
  { department: "Information Technology", activity_count: 5 },
  { department: "Civil Engineering", activity_count: 3 },
];

const departmentOverview = {
  total_activities: 8,
  periods_covered: ["2021-22"],
  period_breakdown: [{ academic_year: "2021-22", activity_count: 8 }],
  departments: departmentsPayload,
  departmental_categories: [{ code: "ACHIEVEMENT", name: "Achievement and Awards", activity_count: 5 }],
};

const departmentDetail = {
  department: "Information Technology",
  total_activities: 5,
  periods_covered: ["2021-22"],
  period_breakdown: [{ academic_year: "2021-22", activity_count: 5 }],
  departmental_categories: [{ code: "ACHIEVEMENT", name: "Achievement and Awards", activity_count: 5 }],
  year_category_breakdown: [{ academic_year: "2021-22", category: "Achievement and Awards", activity_count: 5 }],
};

const fixtureFetch = vi.fn((url) => {
  const json = (body) => ({ ok: true, json: async () => body });
  if (url.endsWith("/api/departments")) return Promise.resolve(json(departmentsPayload));
  if (url.endsWith("/api/analytics/general")) return Promise.resolve(json(generalPayload));
  if (url.includes("/api/analytics/department?department=")) return Promise.resolve(json(departmentDetail));
  if (url.endsWith("/api/analytics/department")) return Promise.resolve(json(departmentOverview));
  return Promise.resolve(json([]));
});

const renderDashboard = () => render(<MemoryRouter><GlobalFiltersProvider><Dashboard /></GlobalFiltersProvider></MemoryRouter>);

describe("public Dashboard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", fixtureFetch);
  });

  it("renders the General Activities tab with public KPIs and charts", async () => {
    renderDashboard();
    expect(await screen.findByText("Institutional Activity Dashboard")).toBeInTheDocument();
    expect(await screen.findByText("879")).toBeInTheDocument();
    expect(screen.getByText("Total General Activities")).toBeInTheDocument();
    expect(screen.getByText("Periods Covered")).toBeInTheDocument();
    expect(screen.getByText("General Categories")).toBeInTheDocument();
    expect(screen.getByText("Institution-wide Activities by Period")).toBeInTheDocument();
    expect(screen.getByText("General Category Analytics")).toBeInTheDocument();
    expect(screen.getAllByText("2025-2026").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("2021-2022").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("Department Activity Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("Activities by Scope")).not.toBeInTheDocument();
    expect(screen.queryByText("Verified")).not.toBeInTheDocument();
    expect(screen.queryByText("Needs Review")).not.toBeInTheDocument();
    expect(screen.queryByText("Open Review Tasks")).not.toBeInTheDocument();
  });

  it("shows only public analytics and no internal classification/review metrics", async () => {
    renderDashboard();
    await screen.findByText("879");
    expect(screen.getByText("Total General Activities")).toBeInTheDocument();
    for (const metric of ["Total Activities", "Activities by Department",
      "Confidence", "Candidate", "Classifier", "Extraction", "Verification",
      "Candidate Count", "Classification Metrics", "Review Count", "Matching"]) {
      expect(screen.queryByText(metric)).not.toBeInTheDocument();
    }
  });

  it("shows a public error message without technical details", async () => {
    vi.stubGlobal("fetch", vi.fn((url) => {
      const json = (body) => ({ ok: true, json: async () => body });
      if (url.endsWith("/api/analytics/general")) return Promise.reject(new Error("database failed"));
      return Promise.resolve(json({}));
    }));
    renderDashboard();
    expect(await screen.findByText("Unable to load dashboard data. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failed/)).not.toBeInTheDocument();
  });

  it("shows the loading state", () => {
    vi.stubGlobal("fetch", () => new Promise(() => {}));
    renderDashboard();
    expect(screen.getByText("Loading dashboard...")).toBeInTheDocument();
  });

  it("switches to the Department Activities tab and drills from overview to department detail", async () => {
    renderDashboard();
    await screen.findByText("879");
    fireEvent.click(screen.getByRole("tab", { name: "Department Activities" }));

    expect(await screen.findByText("Total Department Activities")).toBeInTheDocument();
    expect(screen.getByText("Activities by Department")).toBeInTheDocument();
    expect(screen.getAllByText("Information Technology").length).toBeGreaterThanOrEqual(1);
    expect(screen.queryByText("General")).not.toBeInTheDocument();

    const deptSelect = screen.getByRole("combobox", { name: "Department" });
    const deptOptions = deptSelect.querySelectorAll("option");
    expect([...deptOptions].map((option) => option.textContent)).toEqual([
      "All Departments", "Information Technology", "Civil Engineering",
    ]);
    fireEvent.change(deptSelect, { target: { value: "Information Technology" } });

    expect(await screen.findByText("Total Activities")).toBeInTheDocument();
    expect(screen.getAllByText("Information Technology").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.queryByText("8")).not.toBeInTheDocument();
  });

  it("keeps legacy category names and codes out of the dashboard", async () => {
    renderDashboard();
    await screen.findByText("879");
    for (const term of ["SYMPOSIUM", "STTP", "TECH_FEST", "Symposium", "STTP", "Technical Festival"]) {
      expect(screen.queryByText(term)).not.toBeInTheDocument();
    }
  });
});