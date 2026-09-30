import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicActivityDetail from "./LinkedinPublicActivityDetail";
import { publicRecordBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

function renderDetail(activityId = "LI-00001") {
  return render(
    <MemoryRouter initialEntries={[`/activities/${activityId}`]}>
      <Routes>
        <Route path="activities/:activityId" element={<LinkedinPublicActivityDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("LinkedinPublicActivityDetail", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders public projection fields only", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /\/api\/linkedin\/activities\/LI-00001/, respond: () => jsonResponse(publicRecordBody) },
    ]));
    renderDetail();

    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    expect(screen.getAllByText("Workshops").length).toBeGreaterThan(0);
    expect(screen.getByText("Computer Science and Engineering")).toBeInTheDocument();
    expect(screen.getByText("Students")).toBeInTheDocument();
    expect(screen.getByText("15 Jan 2026")).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /View Original LinkedIn Post/ });
    expect(link.getAttribute("href")).toBe(publicRecordBody.post_url);

    const disclosure = screen.getAllByText(/TCE LinkedIn/i);
    expect(disclosure.length).toBeGreaterThan(0);
  });

  it("never shows internal validation fields", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /LI-00001/, respond: () => jsonResponse(publicRecordBody) },
    ]));
    renderDetail();
    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    for (const internal of ["Evidence", "Confidence", "Review Status", "Manual overrides",
      "Validation history", "Provenance", "staging_post_id", "evidence_score"]) {
      expect(screen.queryByText(internal)).not.toBeInTheDocument();
    }
  });

  it("shows the structured public summary, never the raw description", async () => {
    const summary = 'The Department of Computer Science and Engineering has conducted a workshop on the topic "Machine Learning" on 15 January 2026 for students.';
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /LI-00001/, respond: () => jsonResponse(publicRecordBody) },
    ]));
    renderDetail();
    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByText(summary)).toBeInTheDocument();
    expect(screen.queryByText(/^{?description/i)).not.toBeInTheDocument();
  });

  it("shows a graceful message for missing activities", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      {
        match: /LI-99999/,
        respond: () => Promise.resolve({ ok: false, status: 404, json: async () => ({}) }),
      },
    ]));
    renderDetail("LI-99999");
    await waitFor(() => expect(screen.getByText(/not available in the public dataset/i)).toBeInTheDocument());
  });

  it("does not fabricate a post link when absent", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /LI-00002/, respond: () => jsonResponse({ ...publicRecordBody, activity_id: "LI-00002", post_url: null }) },
    ]));
    renderDetail("LI-00002");
    await waitFor(() => expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument());
    expect(screen.queryByRole("link", { name: /View Original LinkedIn Post/ })).not.toBeInTheDocument();
  });
});