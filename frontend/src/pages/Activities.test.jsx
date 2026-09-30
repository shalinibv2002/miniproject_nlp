import { useEffect } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Activities from "./Activities";
import { GlobalFiltersProvider, useGlobalFilters } from "../context/GlobalFilters";

const activity = {
  id: 12, title: "TCE Sports Day", activity_date: "2022-06-07", activity_date_text: "7 June 2022",
  academic_year: "2021-22", department: "General", general_category: "Sports",
  departmental_category: null, stakeholder: "Students",
  categories: [{ code: "SPORTS", name: "Sports and Games" }], source_url: "https://www.tce.edu/sports",
};
const response = (data, pagination = { page: 1, page_size: 20, pages: 2 }) => ({
  ok: true, json: async () => ({ data, total: 21, pagination }),
});

function renderActivities() {
  return render(<MemoryRouter><GlobalFiltersProvider><Activities /></GlobalFiltersProvider></MemoryRouter>);
}

function ApplyFilters() {
  const { setFilters } = useGlobalFilters();
  useEffect(() => setFilters((filters) => ({ ...filters, generalCategory: "ACHIEVEMENT", period: "2021-22", order: "asc" })), [setFilters]);
  return <Activities />;
}

function FilterChanger() {
  const { setFilters } = useGlobalFilters();
  return (
    <button onClick={() => setFilters((filters) => ({ ...filters, period: "2023-24", category: "SPORTS" }))}>
      Set filters
    </button>
  );
}

describe("public Activities", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn((url) => Promise.resolve(
    response([activity], url.includes("page=2") ? { page: 2, page_size: 20, pages: 2 } : undefined),
  ))));

  it("renders clean public activity fields and a source link", async () => {
    renderActivities();
    expect(await screen.findByText("TCE Sports Day")).toHaveAttribute("href", "/activities/12");
    expect(screen.getByText("Sports and Games")).toBeInTheDocument();
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.getAllByText("General").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Sports")).toBeInTheDocument();
    expect(screen.getByText("General Category")).toBeInTheDocument();
    expect(screen.getByText("Departmental Category")).toBeInTheDocument();
    expect(screen.queryByText("Scope")).not.toBeInTheDocument();
    expect(screen.getByText("Official TCE Source")).toHaveAttribute("href", "https://www.tce.edu/sports");
    expect(screen.getByText("Showing 1–1 of 21 activities")).toBeInTheDocument();
    expect(screen.queryByText("Confidence")).not.toBeInTheDocument();
    expect(screen.queryByText("Verification")).not.toBeInTheDocument();
  });

  it("sends supported public period, general category, and ordering parameters", async () => {
    render(<MemoryRouter><GlobalFiltersProvider><ApplyFilters /></GlobalFiltersProvider></MemoryRouter>);
    await screen.findByText("TCE Sports Day");
    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      "/api/activities?academic_year=2021-22&general_category=ACHIEVEMENT&order=asc&page=1&page_size=20",
      expect.any(Object),
    );
  });

  it("uses Before 2021 for an activity without a stored public period and hides the date", async () => {
    globalThis.fetch.mockResolvedValueOnce(response([{ ...activity, activity_date: null, academic_year: null }]));
    renderActivities();
    expect(await screen.findByText("Before 2021")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.queryByText("Date")).not.toBeInTheDocument();
  });

  it("paginates through the server-side result", async () => {
    renderActivities();
    await screen.findByText("TCE Sports Day");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(await screen.findByText("Showing 21–21 of 21 activities")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      "/api/activities?order=desc&page=2&page_size=20", expect.any(Object),
    );
  });

  it("resets to page 1 when filters change while on a later page", async () => {
    render(<MemoryRouter><GlobalFiltersProvider><Activities /><FilterChanger /></GlobalFiltersProvider></MemoryRouter>);
    await screen.findByText("TCE Sports Day");
    fireEvent.click(screen.getByRole("button", { name: "Next" }));
    await screen.findByText("Showing 21–21 of 21 activities");
    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      "/api/activities?order=desc&page=2&page_size=20", expect.any(Object),
    );

    fireEvent.click(screen.getByRole("button", { name: "Set filters" }));
    expect(await screen.findByText("TCE Sports Day")).toBeInTheDocument();
    expect(globalThis.fetch).toHaveBeenLastCalledWith(
      "/api/activities?academic_year=2023-24&category=SPORTS&order=desc&page=1&page_size=20",
      expect.any(Object),
    );
    expect(globalThis.fetch.mock.calls.some(([url]) =>
      String(url).includes("page=2") && String(url).includes("academic_year=2023-24"))).toBe(false);
  });

  it("shows friendly loading, empty, and error states", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch.mockReturnValueOnce(pending);
    const { unmount } = renderActivities();
    expect(screen.getByText("Loading activities...")).toBeInTheDocument();
    unmount();

    globalThis.fetch.mockResolvedValueOnce(response([], { page: 1, page_size: 20, pages: 0 }));
    renderActivities();
    expect(await screen.findByText(/No activities found/)).toBeInTheDocument();
  });

  it("hides technical errors from public users", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    renderActivities();
    expect(await screen.findByText("Unable to load activities. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });
});
