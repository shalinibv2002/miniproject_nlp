import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminOverview from "./LinkedinAdminOverview";
import { routeFetch, rule, summaryBody, optionsBody } from "./testFixtures";

function renderPage() {
  return render(<MemoryRouter><LinkedinAdminOverview /></MemoryRouter>);
}

describe("LinkedIn Admin Overview", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("renders summary KPIs and charts from the admin API", async () => {
    globalThis.fetch = vi.fn(routeFetch([
      rule(/\/api\/admin\/linkedin\/summary$/, summaryBody),
      rule(/\/api\/admin\/linkedin\/options$/, optionsBody),
    ]));
    renderPage();
    expect(await screen.findByText("LinkedIn Validation Dashboard")).toBeInTheDocument();
    expect(screen.getAllByText("1280").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("162").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Raw Rows Collected")).toBeInTheDocument();
    expect(screen.getByText("Dated")).toBeInTheDocument();
    expect(screen.getByText("1500")).toBeInTheDocument();
    expect(screen.getByText("With source link")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Browse all records →" })).toHaveAttribute("href", "/admin/linkedin/records");
    expect(screen.getByRole("link", { name: "Open the review queue →" })).toHaveAttribute("href", "/admin/linkedin/review");
  });

  it("shows a loading state then an error when summary fails", async () => {
    const pending = new Promise(() => {});
    globalThis.fetch = vi.fn((url) => {
      if (/options/.test(url)) return Promise.resolve({ ok: true, json: async () => optionsBody });
      return pending;
    });
    const { unmount } = renderPage();
    expect(screen.getByText("Loading LinkedIn validation overview...")).toBeInTheDocument();
    unmount();
    globalThis.fetch = vi.fn(routeFetch([
      rule(/\/api\/admin\/linkedin\/summary$/, { error: "boom" }, false),
      rule(/\/api\/admin\/linkedin\/options$/, optionsBody),
    ]));
    renderPage();
    expect(await screen.findByText("Unable to load the LinkedIn validation overview.")).toBeInTheDocument();
  });
});