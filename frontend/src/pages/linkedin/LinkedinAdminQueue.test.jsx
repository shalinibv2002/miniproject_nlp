import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminQueue from "./LinkedinAdminQueue";
import { queueBody, optionsBody, jsonResponse } from "./testFixtures";

function makeFetch(queue = queueBody) {
  const calls = [];
  const fn = vi.fn((url) => {
    calls.push(String(url));
    if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
    return jsonResponse(queue);
  });
  return { calls, fn };
}

function renderPage() {
  return render(<MemoryRouter><LinkedinAdminQueue /></MemoryRouter>);
}

describe("LinkedIn Admin Review Queue", () => {
  beforeEach(() => { vi.restoreAllMocks(); });

  it("renders queued records with reasons and a review link", async () => {
    const { fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Machine Learning Workshop")).toBeInTheDocument();
    expect(screen.getByText("1 record needs attention")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Review →" })).toHaveAttribute(
      "href", "/admin/linkedin/records/LI-00001");
    expect(fn.mock.calls.some(([url]) => /review-queue$/.test(String(url)))).toBe(true);
  });

  it("passes a reason filter to the API", async () => {
    const { calls, fn } = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByText("Machine Learning Workshop");
    fireEvent.change(screen.getByLabelText("Reason"), { target: { value: "bare_text" } });
    await waitFor(() =>
      expect(calls.some((url) => url.includes("reason=bare_text"))).toBe(true));
  });

  it("shows the empty state when nothing needs review", async () => {
    const { fn } = makeFetch({ data: [], total: 0 });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Nothing needs review under these filters.")).toBeInTheDocument();
  });

  it("shows an error state when the queue fails", async () => {
    const { fn } = makeFetch();
    fn.mockImplementation((url) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      return jsonResponse({ error: "boom" }, false);
    });
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByText("Unable to load the review queue.")).toBeInTheDocument();
  });
});