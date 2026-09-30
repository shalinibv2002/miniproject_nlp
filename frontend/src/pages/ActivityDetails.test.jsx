import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ActivityDetails from "./ActivityDetails";

const activity = {
  id: 12, title: "TCE Sports Day", description: "Students took part in the annual sports day.",
  activity_date: "2022-06-07", activity_date_text: "7 June 2022", academic_year: "2021-22",
  department: "General", general_category: "Sports", departmental_category: null,
  stakeholder: "Students", achievement_outcome: "Student teams received awards.",
  categories: [{ code: "SPORTS", name: "Sports and Games" }], source_url: "https://www.tce.edu/sports",
  official_sources: ["https://www.tce.edu/sports", "https://www.tce.edu/sports/day", "https://example.com/not-official"],
};

const response = (body, ok = true) => ({ ok, json: async () => body });
function renderDetails(id = "12") {
  return render(<MemoryRouter initialEntries={[`/activities/${id}`]}><Routes>
    <Route path="/activities/:id" element={<ActivityDetails />} />
  </Routes></MemoryRouter>);
}

describe("public Activity Details", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(response(activity)))));

  it("renders clean public fields, full Period, and official sources", async () => {
    renderDetails();
    expect(await screen.findByRole("heading", { name: "TCE Sports Day" })).toBeInTheDocument();
    expect(screen.getByText("Sports and Games")).toBeInTheDocument();
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.getAllByText("General").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Students")).toBeInTheDocument();
    expect(screen.getByText("Students took part in the annual sports day.")).toBeInTheDocument();
    expect(screen.getByText("Student teams received awards.")).toBeInTheDocument();
    expect(screen.getAllByText("Official TCE Source")).toHaveLength(2);
    expect(screen.queryByText("SPORTS")).not.toBeInTheDocument();
    expect(screen.queryByText(/confidence|verification|review|candidate/i)).not.toBeInTheDocument();
  });

  it("shows the public General/Departmental Category labels without internal scope codes", async () => {
    renderDetails();
    await screen.findByRole("heading", { name: "TCE Sports Day" });
    expect(screen.getByText("General Category")).toBeInTheDocument();
    expect(screen.getByText("Departmental Category")).toBeInTheDocument();
    expect(screen.queryByText("Scope")).not.toBeInTheDocument();
    expect(screen.queryByText(/institution_wide|single|multiple/u)).not.toBeInTheDocument();
  });

  it("uses Before 2021 for a missing period and hides an empty outcome", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({ ...activity, academic_year: null, activity_date: null,
      activity_date_text: null, achievement_outcome: "" }));
    renderDetails();
    expect(await screen.findByText("Before 2021")).toBeInTheDocument();
    expect(screen.queryByText("Achievement / Outcome")).not.toBeInTheDocument();
    expect(screen.queryByText("Date")).not.toBeInTheDocument();
  });

  it("shows loading, not found, and friendly error states", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch.mockReturnValueOnce(pending);
    const { unmount } = renderDetails();
    expect(screen.getByText("Loading activity...")).toBeInTheDocument();
    unmount();

    globalThis.fetch.mockResolvedValueOnce(response({ error: "activity not found" }, false));
    renderDetails("999");
    expect(await screen.findByText("Activity not found.")).toBeInTheDocument();
    expect(screen.getByText("← Back to Activities")).toHaveAttribute("href", "/activities");
  });

  it("does not expose technical errors", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    renderDetails();
    expect(await screen.findByText("Unable to load this activity. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });
});
