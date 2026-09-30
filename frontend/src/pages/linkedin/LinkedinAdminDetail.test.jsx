import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LinkedinAdminDetail from "./LinkedinAdminDetail";
import { recordBody, optionsBody, jsonResponse } from "./testFixtures";
import { setAuthSession, clearAuthSession } from "../../services/api";

const updatedBody = {
  ...recordBody,
  title: "Machine Learning Workshop (revised)",
  validation_history: [
    ...recordBody.validation_history,
    { field: "title", old: "Machine Learning Workshop", new: "Machine Learning Workshop (revised)", by: "shalini", at: "2026-09-23T13:00:00", note: "admin manual correction" },
  ],
};

function makeFetch(updated = null) {
  return vi.fn((url, options = {}) => {
    const u = String(url);
    if (/\/options$/.test(u)) return jsonResponse(optionsBody);
    if (options.method === "PATCH") return jsonResponse(updated || recordBody);
    return jsonResponse(recordBody);
  });
}

function renderPage(id = "LI-00001") {
  return render(
    <MemoryRouter initialEntries={[`/admin/linkedin/records/${id}`]}>
      <Routes>
        <Route path="/admin/linkedin/records/:id" element={<LinkedinAdminDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LinkedIn Admin Record Detail", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    setAuthSession("test-token", "shalini", "admin");
  });
  afterEach(() => clearAuthSession());

  it("renders provenance, evidence, description, and validation history", async () => {
    const fn = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    expect(await screen.findByRole("heading", { name: "Machine Learning Workshop" })).toBeInTheDocument();
    expect(screen.getByText("Open LinkedIn post")).toHaveAttribute(
      "href", "https://www.linkedin.com/posts/tcemadurai_x");
    expect(screen.getByText("TCE LinkedIn Posts 2026.xlsx")).toBeInTheDocument();
    expect(screen.getAllByText("matched").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("workshop").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("A one-day workshop on Machine Learning for students.").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("APPROVED").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("review_status")).toBeInTheDocument();
    expect(screen.getByText("verified visually")).toBeInTheDocument();
  });

  it("shows not-found when the record does not exist", async () => {
    const fn = vi.fn((url) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      return jsonResponse({ error: "activity not found" }, false);
    });
    globalThis.fetch = fn;
    renderPage("LI-99999");
    expect(await screen.findByText("Record not found.")).toBeInTheDocument();
  });

  it("submits an editable-field PATCH with auth and shows the before/after result", async () => {
    const fn = makeFetch(updatedBody);
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("heading", { name: "Machine Learning Workshop" });

    const title = screen.getByLabelText("Title");
    fireEvent.change(title, { target: { value: "Machine Learning Workshop (revised)" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByText(/Saved — title:/)).toBeInTheDocument();
    const patchCall = fn.mock.calls.find(([, o]) => o && o.method === "PATCH");
    expect(patchCall).toBeTruthy();
    const payload = JSON.parse(patchCall[1].body);
    expect(payload.title).toBe("Machine Learning Workshop (revised)");
    expect(patchCall[1].headers.Authorization).toBe("Bearer test-token");
    expect(payload.categories).toEqual(["WORKSHOP"]);
    expect(payload.review_status).toBe("UNREVIEWED");
  });

  it("blocks saving when a reportable activity has no title", async () => {
    const fn = makeFetch();
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("heading", { name: "Machine Learning Workshop" });
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Reportable status"), { target: { value: "REPORTABLE" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("A reportable activity needs a title.")).toBeInTheDocument();
    expect(fn.mock.calls.some(([, o]) => o && o.method === "PATCH")).toBe(false);
  });

  it("blocks plain saving when promoting to REPORTABLE — publish must be explicit", async () => {
    const pendingBody = { ...recordBody, reportable_status: "NON_ACTIVITY" };
    const fn = vi.fn((url, options = {}) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      return jsonResponse(pendingBody);
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("heading", { name: "Machine Learning Workshop" });
    fireEvent.change(screen.getByLabelText("Reportable status"), { target: { value: "REPORTABLE" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Use 'Save & Publish' to make this record publicly REPORTABLE.")).toBeInTheDocument();
    expect(fn.mock.calls.some(([, o]) => o && o.method === "PATCH")).toBe(false);
  });

  it("publishes through Save & Publish and reports the transition", async () => {
    const pendingBody = { ...recordBody, reportable_status: "NON_ACTIVITY", review_status: "NEEDS_REVIEW" };
    const publishedBody = {
      ...recordBody,
      reportable_status: "REPORTABLE",
      review_status: "APPROVED",
      is_manually_validated: 1,
      validation_history: [
        ...recordBody.validation_history,
        { field: "reportable_status", old: "NON_ACTIVITY", new: "REPORTABLE", by: "shalini", at: "2026-09-25T10:00:00", note: "admin save & publish" },
      ],
    };
    const fn = vi.fn((url, _options = {}) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      if (String(url).endsWith("/publish")) return jsonResponse(publishedBody);
      return jsonResponse(pendingBody);
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("heading", { name: "Machine Learning Workshop" });

    fireEvent.click(screen.getByRole("button", { name: "Save & Publish" }));
    expect(await screen.findByText(/Published — LI-00001 is now PUBLIC REPORTABLE/)).toBeInTheDocument();

    const publishCall = fn.mock.calls.find(([u, o]) => o && o.method === "POST" && /\/publish$/.test(String(u)));
    expect(publishCall).toBeTruthy();
    const payload = JSON.parse(publishCall[1].body);
    expect(payload.title).toBe("Machine Learning Workshop");
    expect(payload.reportable_status).toBeUndefined();
    expect(publishCall[1].headers.Authorization).toBe("Bearer test-token");
  });

  it("surfaces a server error when the patch is rejected", async () => {
    const fn = vi.fn((url, options = {}) => {
      if (/\/options$/.test(String(url))) return jsonResponse(optionsBody);
      if (options.method === "PATCH") return jsonResponse({ error: "invalid department name: Not Real" }, false);
      return jsonResponse(recordBody);
    });
    globalThis.fetch = fn;
    renderPage();
    await screen.findByRole("heading", { name: "Machine Learning Workshop" });
    fireEvent.change(screen.getByLabelText("Department"), { target: { value: "Computer Science and Engineering" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("invalid department name: Not Real")).toBeInTheDocument();
  });
});