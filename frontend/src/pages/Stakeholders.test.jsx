import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Stakeholders from "./Stakeholders";
import { GlobalFiltersProvider, useGlobalFilters } from "../context/GlobalFilters";

const rows = [
  { stakeholder: "Students", activity_count: 1162 },
  { stakeholder: "Faculty", activity_count: 589 },
];
const response = (body) => ({ ok: true, json: async () => body });

function Probe() {
  const { filters } = useGlobalFilters();
  return <p data-testid="probe">{filters.stakeholder || "none"} | {filters.period || "none"}</p>;
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/stakeholders"]}>
      <GlobalFiltersProvider>
        <Routes>
          <Route path="/stakeholders" element={<Stakeholders />} />
          <Route path="/activities" element={<Probe />} />
        </Routes>
      </GlobalFiltersProvider>
    </MemoryRouter>
  );
}

describe("Stakeholders drill-down", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn((url) => {
    if (url.startsWith("/api/stakeholders")) return Promise.resolve(response(rows));
    return Promise.resolve(response({ data: [], total: 0, pagination: { page: 1, page_size: 20, pages: 0 } }));
  })));

  it("lists public stakeholders and drills into the activities list with the stakeholder filter", async () => {
    renderPage();
    expect(await screen.findByText("Students")).toBeInTheDocument();
    expect(screen.getByText("Faculty")).toBeInTheDocument();
    expect(screen.getByText("1162 activities")).toBeInTheDocument();
    expect(screen.queryByText("Code")).not.toBeInTheDocument();
    expect(screen.queryByText("Name")).not.toBeInTheDocument();

    screen.getAllByRole("button", { name: "Explore activities" })[0].click();
    expect(await screen.findByTestId("probe")).toHaveTextContent("Students | none");
  });

  it("applies the selected period to the stakeholder metrics", async () => {
    renderPage();
    await screen.findByText("Students");
    const periodSelect = screen.getByRole("combobox", { name: "Academic Period" });
    fireEvent.change(periodSelect, { target: { value: "2025-26" } });
    await waitFor(() => {
      const call = globalThis.fetch.mock.calls.find(([url]) =>
        String(url).includes("/api/stakeholders") && String(url).includes("period=2025-26"));
      expect(call).toBeTruthy();
    });
  });

  it("shows public loading, empty, and error states", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch.mockReturnValueOnce(pending);
    const { unmount } = renderPage();
    expect(screen.getByText("Loading stakeholders...")).toBeInTheDocument();
    unmount();

    globalThis.fetch.mockResolvedValueOnce(response([]));
    renderPage();
    expect(await screen.findByText(/No stakeholder activities found/)).toBeInTheDocument();
  });

  it("does not expose technical failures", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    renderPage();
    expect(await screen.findByText("Unable to load stakeholder data. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });
});