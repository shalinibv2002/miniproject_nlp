import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LinkedinAdminDepartmentalDetail from "./LinkedinAdminDepartmentalDetail";

const options = {
  categories: [
    { code: "WORKSHOP", name: "Workshop" },
    { code: "FDP", name: "FDP" },
  ],
  departments: ["General", "Computer Science and Engineering", "Information Technology"],
  stakeholders: ["Students", "Faculty"],
  academic_years: ["2025-26", "2024-25"],
};

const baseRecord = {
  activity_id: "LI-00001",
  title: "Machine Learning Workshop",
  description: "A workshop on ML for CSE students.",
  post_url: "https://www.linkedin.com/posts/tcemadurai_x",
  activity_date: "2026-01-15",
  academic_year: "2025-26",
  categories: ["WORKSHOP"],
  departments: ["Computer Science and Engineering"],
  stakeholders: ["Students"],
  reportable_status: "REPORTABLE",
  review_status: "UNREVIEWED",
  name: "Machine Learning Workshop",
  achievement_description: "CSE has conducted a workshop on Machine Learning for students.",
  report_date: "15 January 2026",
  academic_year_display: "2025\u201326",
  stakeholder_display: "students",
  report_department: "Computer Science and Engineering",
  award_category: "Workshop",
  validation_history: [],
};

function jsonResponse(body, ok = true) {
  return Promise.resolve({ ok, status: ok ? 200 : 400, json: async () => body });
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/admin/linkedin/departmental/LI-00001"]}>
      <Routes>
        <Route
          path="/admin/linkedin/departmental/:id"
          element={<LinkedinAdminDepartmentalDetail />}
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LinkedIn Admin Departmental Detail", () => {
  let fetchMock;
  beforeEach(() => { fetchMock = vi.fn(); globalThis.fetch = fetchMock; });
  afterEach(() => { vi.restoreAllMocks(); });

  it("shows only the category-appropriate editable fields and no internal fields", async () => {
    // baseRecord is WORKSHOP → departmental editor shows Title (not Name / Achievement Description).
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByText("Machine Learning Workshop");

    // Always-present fields.
    expect(screen.getByLabelText("Stakeholder")).toBeInTheDocument();
    expect(screen.getByLabelText("Department")).toBeInTheDocument();
    expect(screen.getByLabelText("Award Category")).toBeInTheDocument();
    expect(screen.getByLabelText("Date")).toBeInTheDocument();
    expect(screen.getByLabelText("Academic Year")).toBeInTheDocument();
    expect(screen.getByLabelText("Status")).toBeInTheDocument();

    // WORKSHOP is not ACHIEVEMENT: Title shown, Name and Achievement Description absent.
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.queryByLabelText("Name")).toBeNull();
    expect(screen.queryByLabelText("Achievement Description")).toBeNull();

    // No internal fields must appear.
    expect(screen.queryByLabelText("Description")).toBeNull();
    expect(screen.queryByText("Source & Provenance")).toBeNull();
    expect(screen.queryByText("Classification Decisions")).toBeNull();
    expect(screen.queryByText("Validation History")).toBeNull();
    expect(screen.queryByText("Confidence")).toBeNull();
  });

  it("shows a stored activity date and PATCHes a newly picked one", async () => {
    // The single Date column of every non-Internship category: a date input only
    // renders a full ISO date, so a reported "15 January 2026" must still show.
    const record = { ...baseRecord, activity_date: "15 January 2026" };
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        patchBodies.push(body);
        return jsonResponse({ ...record, ...body });
      });

    renderPage();
    expect((await screen.findByLabelText("Date")).value).toBe("2026-01-15");

    fireEvent.change(screen.getByLabelText("Date"), { target: { value: "2026-02-20" } });
    expect(screen.getByLabelText("Date").value).toBe("2026-02-20");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0]).toEqual({
      activity_date: "2026-02-20",
      _note: "admin manual correction",
    });
  });

  it("excludes General from the Department dropdown options", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Department");

    // The first row uses aria-label="Department" (i === 0).
    const deptSelect = screen.getByLabelText("Department");
    const optionTexts = Array.from(deptSelect.querySelectorAll("option")).map((o) => o.textContent);
    expect(optionTexts).not.toContain("General");
    expect(optionTexts).toContain("Computer Science and Engineering");
    expect(optionTexts).toContain("Information Technology");
  });

  it("patches only the changed Title field via the same canonical PATCH endpoint", async () => {
    // WORKSHOP departmental records use Title (not Achievement Description).
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        expect(init.method).toBe("PATCH");
        expect(url).toMatch(/\/api\/admin\/linkedin\/activities\/LI-00001$/);
        const body = JSON.parse(init.body || "{}");
        expect(body).toEqual({
          title: "ML Workshop for CSE — Updated",
          _note: "admin manual correction",
        });
        return jsonResponse({
          ...baseRecord,
          title: "ML Workshop for CSE — Updated",
          validation_history: [
            {
              field: "title",
              old: "Machine Learning Workshop",
              new: "ML Workshop for CSE — Updated",
              by: "admin",
              at: "2026-10-03T11:00:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Title");

    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "ML Workshop for CSE — Updated" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  it("shows 'No changes to save' when nothing was changed", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    // WORKSHOP shows Title field (not Name).
    await screen.findByLabelText("Title");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText(/no changes/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("flips APPROVED to NOT_APPROVED (NEEDS_REVIEW) via the same PATCH endpoint", async () => {
    const approvedRecord = { ...baseRecord, review_status: "APPROVED" };
    fetchMock
      .mockImplementationOnce(() => jsonResponse(approvedRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect(body.review_status).toBe("NEEDS_REVIEW");
        return jsonResponse({
          ...approvedRecord,
          review_status: "NEEDS_REVIEW",
          validation_history: [
            {
              field: "review_status",
              old: "APPROVED",
              new: "NEEDS_REVIEW",
              by: "admin",
              at: "2026-10-03T11:01:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Status");
    fireEvent.change(screen.getByLabelText("Status"), { target: { value: "NOT_APPROVED" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("surfaces server validation errors", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce(() => Promise.reject(new Error("invalid department name: Fake Dept")));

    renderPage();
    await screen.findByLabelText("Department");
    fireEvent.change(screen.getByLabelText("Department"), { target: { value: "Fake Dept" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByText("invalid department name: Fake Dept")).toBeInTheDocument();
  });

  it("shows a not-found error for an unknown id", async () => {
    fetchMock.mockImplementationOnce(() =>
      Promise.reject(new Error("activity not found")));

    renderPage();
    expect(await screen.findByText("Record not found.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to Departmental/ })).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Multi-value tests
  // -------------------------------------------------------------------------

  it("adds a second stakeholder and sends both in the PATCH payload", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect([...body.stakeholders].sort()).toEqual(["Faculty", "Students"]);
        return jsonResponse({
          ...baseRecord,
          stakeholders: ["Students", "Faculty"],
          validation_history: [
            {
              field: "stakeholders",
              old: ["Students"],
              new: ["Students", "Faculty"],
              by: "admin",
              at: "2026-10-03T11:10:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Stakeholder");

    fireEvent.click(screen.getByRole("button", { name: "Add Stakeholder" }));
    const secondRow = await screen.findByLabelText("Stakeholder 2");
    fireEvent.change(secondRow, { target: { value: "Faculty" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  it("adds a second department (non-General) and sends both in the PATCH payload", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect([...body.departments].sort()).toEqual([
          "Computer Science and Engineering",
          "Information Technology",
        ]);
        // Confirm General is NOT sent.
        expect(body.departments).not.toContain("General");
        return jsonResponse({
          ...baseRecord,
          departments: ["Computer Science and Engineering", "Information Technology"],
          validation_history: [
            {
              field: "departments",
              old: ["Computer Science and Engineering"],
              new: ["Computer Science and Engineering", "Information Technology"],
              by: "admin",
              at: "2026-10-03T11:11:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Department");

    // The "Add Department" button appears below the first row.
    fireEvent.click(screen.getByRole("button", { name: "Add Department" }));
    const secondDept = await screen.findByLabelText("Department 2");
    fireEvent.change(secondDept, { target: { value: "Information Technology" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  it("discard after adding a row resets to original values", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Award Category");

    // Add a second category row.
    fireEvent.click(screen.getByRole("button", { name: "Add Award Category" }));
    expect(await screen.findByLabelText("Award Category 2")).toBeInTheDocument();

    // Discard should remove the extra row.
    fireEvent.click(screen.getByRole("button", { name: "Discard changes" }));
    await waitFor(() => expect(screen.queryByLabelText("Award Category 2")).toBeNull());
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
