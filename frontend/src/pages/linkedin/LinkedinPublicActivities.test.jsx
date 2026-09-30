import { render, screen, waitFor, within, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicActivities from "./LinkedinPublicActivities";
import { filtersBody, activitiesBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

function mockApi(url) {
  const calls = [];
  global.fetch = vi.fn().mockImplementation(routeFetch([
    {
      match: /\/api\/linkedin\/filters/,
      respond: () => jsonResponse(filtersBody),
    },
    {
      match: /\/api\/linkedin\/activities/,
      respond: (requestUrl) => {
        calls.push(requestUrl);
        if (requestUrl.includes("category=WORKSHOP")) {
          return jsonResponse({
            data: [activitiesBody.data[0]],
            total: 1,
            pagination: { page: 1, page_size: 12, total: 1, pages: 1 },
          });
        }
        return jsonResponse(activitiesBody);
      },
    },
  ]));
  return calls;
}

function renderPage(initialPath = "/activities") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <LinkedinPublicActivities />
    </MemoryRouter>
  );
}

describe("LinkedinPublicActivities", () => {
  afterEach(() => vi.restoreAllMocks());

  it("loads filter options and lists activity cards", async () => {
    mockApi("/");
    renderPage();

    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    expect(screen.getAllByText(/TCE LinkedIn/i).length).toBeGreaterThan(0);
    expect(screen.getByRole("combobox", { name: "Academic year" })).toBeInTheDocument();
    expect(within(screen.getByRole("combobox", { name: "Category" })).getAllByRole("option").length).toBe(5);
  });

  it("applies filters and refreshes the server-side list", async () => {
    const calls = mockApi("/");
    renderPage();

    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    fireEvent.change(screen.getByRole("combobox", { name: "Category" }), { target: { value: "WORKSHOP" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));

    await waitFor(() => {
      expect(calls.some((url) => url.includes("category=WORKSHOP"))).toBe(true);
    });
    expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument();
    expect(screen.queryByText("Five-Day FDP on Cloud Computing")).not.toBeInTheDocument();
  });

  it("honours deep links with query parameters", async () => {
    mockApi("/");
    renderPage("/activities?category=WORKSHOP&academic_year=2025-26");

    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
  });

  it("shows an empty state when nothing matches", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /filters/, respond: () => jsonResponse(filtersBody) },
      { match: /activities/, respond: () => jsonResponse({ data: [], total: 0, pagination: { page: 1, page_size: 12, total: 0, pages: 0 } }) },
    ]));
    renderPage();
    await waitFor(() => expect(screen.getByText(/No activities (available|match)/i)).toBeInTheDocument());
  });
});