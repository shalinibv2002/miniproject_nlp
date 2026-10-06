import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import LinkedinAdminDetail from "./LinkedinAdminDetail";

const options = {
  categories: [
    { code: "WORKSHOP", name: "Workshop" },
    { code: "FDP", name: "FDP" },
    { code: "SEMINAR", name: "Seminar" },
    { code: "CONFERENCE", name: "Conference" },
    { code: "INDUSTRY", name: "Industry" },
    { code: "INTERNSHIP", name: "Internship" },
    { code: "ALUMNI", name: "Alumni Meet" },
    { code: "ACHIEVEMENT", name: "Achievement" },
  ],
  departments: ["Computer Science and Engineering", "Information Technology"],
  stakeholders: ["Students", "Faculty"],
  academic_years: ["2025-26", "2024-25"],
  statuses: ["REPORTABLE", "NON_ACTIVITY", "REVIEW_REQUIRED"],
  review_statuses: ["UNREVIEWED", "APPROVED", "REJECTED", "NEEDS_REVIEW"],
};

const baseRecord = {
  activity_id: "LI-00001",
  title: "Machine Learning Workshop",
  description: "A workshop on ML.",
  post_url: "https://www.linkedin.com/posts/example",
  activity_date: "2026-01-15",
  academic_year: "2025-26",
  categories: ["WORKSHOP"],
  departments: ["Computer Science and Engineering"],
  stakeholders: ["Students"],
  reportable_status: "REPORTABLE",
  review_status: "UNREVIEWED",
  classification_status: "AUTO_CLASSIFIED",
  reason: "activity_evidence:WORKSHOP",
  unclear_reason: null,
  kind: "D",
  multi_label: 0,
  flags: ["link_less"],
  is_manually_validated: 0,
  provenance: {
    source: "LinkedIn",
    source_workbook: "merged.xlsx",
    source_sheet: "June",
    source_row: 1,
    occurrence_count: 1,
    source_occurrence_ids: [100],
    collected_at: "2026-10-03T04:09:07",
    resolved_via: null,
    activity_urn_id: "urn:li:activity:123",
  },
  staging_post_id: 1,
  staging_candidate_id: 1,
  evidence_score: 7,
  category_evidence: { WORKSHOP: { workshop: ["workshop"] } },
  department_evidence: {},
  stakeholder_evidence: {},
  date_evidence: {},
  communication_type: null,
  communication_evidence: {},
  name: "Machine Learning Workshop",
  achievement_description: "A workshop on ML.",
  report_date: "15 January 2026",
  academic_year_display: "2025\u201326",
  stakeholder_display: "students",
  department_display: "Computer Science and Engineering",
  award_category: "Workshop",
  validation_history: [],
};

function jsonResponse(body) {
  return Promise.resolve({
    ok: true,
    json: () => Promise.resolve(body),
  });
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={["/admin/linkedin/records/LI-00001"]}>
      <Routes>
        <Route path="/admin/linkedin/records/:id" element={<LinkedinAdminDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("LinkedIn Admin Record Detail", () => {
  let fetchMock;

  beforeEach(() => {
    fetchMock = vi.fn();
    globalThis.fetch = fetchMock;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("loads the minimal editor and exposes only the category-appropriate fields", async () => {
    // baseRecord is WORKSHOP → editor shows Title (not Name / Achievement Description).
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();

    await screen.findByText("Machine Learning Workshop");

    // Always-present editable fields (any category).
    expect(screen.getByLabelText("Stakeholder")).toBeInTheDocument();
    expect(screen.getByLabelText("Department")).toBeInTheDocument();
    expect(screen.getByLabelText("Award Category")).toBeInTheDocument();
    expect(screen.getByLabelText("Date")).toBeInTheDocument();
    expect(screen.getByLabelText("Academic Year")).toBeInTheDocument();
    expect(screen.getByLabelText("Status")).toBeInTheDocument();

    // WORKSHOP is not ACHIEVEMENT: Title is shown; Name and Achievement Description are absent.
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.queryByLabelText("Name")).toBeNull();
    expect(screen.queryByLabelText("Achievement Description")).toBeNull();

    // Internal / raw fields must never appear.
    expect(screen.queryByLabelText("Description")).toBeNull();
    expect(screen.queryByLabelText("Reportable status")).toBeNull();
    expect(screen.queryByLabelText("Review status")).toBeNull();
    expect(screen.queryByLabelText("Reviewer note")).toBeNull();
    expect(screen.queryByText("Source & Provenance")).toBeNull();
    expect(screen.queryByText("Classification Decisions")).toBeNull();
    expect(screen.queryByText("Validation History")).toBeNull();
  });

  it("patches only the changed Title field when saving a WORKSHOP record", async () => {
    // WORKSHOP records edit Title (not Name/Achievement Description).
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        expect(init.method).toBe("PATCH");
        expect(url).toMatch(/\/activities\/LI-00001$/);
        const body = JSON.parse(init.body || "{}");
        expect(body).toEqual({
          title: "Machine Learning Workshop — Updated",
          _note: "admin manual correction",
        });
        return jsonResponse({
          ...baseRecord,
          title: "Machine Learning Workshop — Updated",
          validation_history: [
            {
              field: "title",
              old: "Machine Learning Workshop",
              new: "Machine Learning Workshop — Updated",
              by: "admin",
              at: "2026-10-03T10:00:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Title");

    fireEvent.change(screen.getByLabelText("Title"), {
      target: { value: "Machine Learning Workshop — Updated" },
    });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("maps approval changes to NOT_APPROVED and keeps display fields trimmed", async () => {
    // Start from APPROVED then flip to Not Approved — the only transition that
    // produces a real status change in payload (NEEDS_REVIEW).
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
              at: "2026-10-03T10:01:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Status");

    fireEvent.change(screen.getByLabelText("Status"), {
      target: { value: "NOT_APPROVED" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("shows 'No changes to save' when nothing changed", async () => {
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

  it("surfaces server error messages", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce(() => Promise.reject(new Error("invalid department name: Not Real")));

    renderPage();
    await screen.findByLabelText("Department");

    // First row of the multi-value field keeps aria-label="Department".
    fireEvent.change(screen.getByLabelText("Department"), {
      target: { value: "Not Real" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("invalid department name: Not Real")).toBeInTheDocument();
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
        // Sorted comparison to be order-agnostic.
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
              at: "2026-10-03T11:00:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Stakeholder");

    // Click the "+ Add" button for Stakeholder.
    fireEvent.click(screen.getByRole("button", { name: "Add Stakeholder" }));

    // A second row should appear with aria-label="Stakeholder 2".
    const secondRow = await screen.findByLabelText("Stakeholder 2");
    fireEvent.change(secondRow, { target: { value: "Faculty" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  it("removes an existing department value and sends the empty array in the PATCH payload", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect(body.departments).toEqual([]);
        return jsonResponse({
          ...baseRecord,
          departments: [],
          validation_history: [
            {
              field: "departments",
              old: ["Computer Science and Engineering"],
              new: [],
              by: "admin",
              at: "2026-10-03T11:01:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Department");

    // Remove the first (and only) department row.
    fireEvent.click(screen.getByRole("button", { name: "Remove Department 1" }));

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  it("adds a second Award Category and sends both in the PATCH payload", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect([...body.categories].sort()).toEqual(["FDP", "WORKSHOP"]);
        return jsonResponse({
          ...baseRecord,
          categories: ["WORKSHOP", "FDP"],
          validation_history: [
            {
              field: "categories",
              old: ["WORKSHOP"],
              new: ["WORKSHOP", "FDP"],
              by: "admin",
              at: "2026-10-03T11:02:00",
              note: "admin manual correction",
            },
          ],
        });
      });

    renderPage();
    await screen.findByLabelText("Award Category");

    fireEvent.click(screen.getByRole("button", { name: "Add Award Category" }));

    const secondCat = await screen.findByLabelText("Award Category 2");
    fireEvent.change(secondCat, { target: { value: "FDP" } });

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await screen.findByText(/Saved/)).toBeInTheDocument();
  });

  // -------------------------------------------------------------------------
  // Category-specific report fields
  // -------------------------------------------------------------------------

  function withCategory(code, extra = {}) {
    return {
      ...baseRecord,
      categories: [code],
      award_category: code,
      ...extra,
    };
  }

  it("shows exactly the CONFERENCE report columns and PATCHes the Chief Guest", async () => {
    const record = withCategory("CONFERENCE", {
      departments: [], // general scope -> no Department column
      chief_guest: "",
    });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect(body).toEqual({
          chief_guest: "Dr A. Sharma",
          _note: "admin manual correction",
        });
        return jsonResponse({
          ...record,
          chief_guest: "Dr A. Sharma",
          validation_history: [
            { field: "chief_guest", old: "", new: "Dr A. Sharma", by: "admin", at: "2026-10-03T12:00:00", note: "admin manual correction" },
          ],
        });
      });

    renderPage();
    // CONFERENCE reports a Chief Guest; a Speaker or an MOU is not its field.
    await screen.findByLabelText("Chief Guest");
    expect(screen.queryByLabelText("Speaker")).toBeNull();
    expect(screen.queryByLabelText("Signed MOU With")).toBeNull();

    fireEvent.change(screen.getByLabelText("Chief Guest"), {
      target: { value: "Dr A. Sharma" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("shows both INDUSTRY columns and PATCHes the MOU and the Purpose together", async () => {
    const record = withCategory("INDUSTRY", { departments: [], mou_with: "", purpose: "" });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        expect(body).toEqual({
          mou_with: "Infosys Ltd",
          purpose: "Industry academia tie-up.",
          _note: "admin manual correction",
        });
        return jsonResponse({ ...record, mou_with: "Infosys Ltd", purpose: "Industry academia tie-up." });
      });

    renderPage();
    await screen.findByLabelText("Signed MOU With");
    expect(screen.getByLabelText("Purpose")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Signed MOU With"), { target: { value: "Infosys Ltd" } });
    fireEvent.change(screen.getByLabelText("Purpose"), { target: { value: "Industry academia tie-up." } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  // -------------------------------------------------------------------------
  // Date editing.
  //
  // These assert the PATCH body from the test body rather than from inside the
  // fetch mock: an expectation thrown in there only rejects the request, which
  // the page swallows into its error banner, so a wrong payload would still
  // leave the test green.
  // -------------------------------------------------------------------------

  it("applies a picked date to the field and saves both ends of the INTERNSHIP range", async () => {
    const record = withCategory("INTERNSHIP", { departments: [], date_range: "" });
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
    const from = await screen.findByLabelText("Date (From-To) from");
    expect(screen.getByLabelText("Date (From-To) to")).toBeInTheDocument();

    // Picking From must leave it on screen: a picked date that vanishes on the
    // next render is the whole symptom being guarded against.
    fireEvent.change(from, { target: { value: "2026-01-12" } });
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-01-12");

    fireEvent.change(screen.getByLabelText("Date (From-To) to"), { target: { value: "2026-01-20" } });
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-01-12");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");

    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0]).toEqual({
      date_range: "2026-01-12 – 2026-01-20",
      _note: "admin manual correction",
    });
    // The saved range stays on screen after the round trip too.
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-01-12");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");
  });

  it("shows the saved INTERNSHIP range again when the record is reopened", async () => {
    const record = withCategory("INTERNSHIP", { departments: [], date_range: "" });
    const saved = { ...record, date_range: "2026-01-12 – 2026-01-20" };
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        patchBodies.push(JSON.parse(init.body || "{}"));
        return jsonResponse(saved);
      });

    renderPage();
    await screen.findByLabelText("Date (From-To) from");
    fireEvent.change(screen.getByLabelText("Date (From-To) from"), { target: { value: "2026-01-12" } });
    fireEvent.change(screen.getByLabelText("Date (From-To) to"), { target: { value: "2026-01-20" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));

    // Reopen the record, as a validator does after navigating away and back.
    cleanup();
    fetchMock.mockReset();
    fetchMock
      .mockImplementationOnce(() => jsonResponse(saved))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    expect((await screen.findByLabelText("Date (From-To) from")).value).toBe("2026-01-12");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");
  });

  it("preloads the two date inputs from a reported From-To value", async () => {
    // The report writes dates as "%d %B %Y", so a full month name is the form a
    // derived range actually arrives in.
    const record = withCategory("INTERNSHIP", { departments: [], date_range: "12 January 2026 – 20 January 2026" });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    expect((await screen.findByLabelText("Date (From-To) from")).value).toBe("2026-01-12");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");
  });

  it("saves a From date on its own and keeps it in the From box when reloaded", async () => {
    const record = withCategory("INTERNSHIP", { departments: [], date_range: "" });
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
    await screen.findByLabelText("Date (From-To) from");
    fireEvent.change(screen.getByLabelText("Date (From-To) from"), { target: { value: "2026-03-02" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].date_range).toBe("2026-03-02");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-03-02");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("");
  });

  it("replaces an existing range when the admin re-picks both ends", async () => {
    const record = withCategory("INTERNSHIP", {
      departments: [], date_range: "12 Jan 2026 – 20 Jan 2026",
    });
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
    expect((await screen.findByLabelText("Date (From-To) from")).value).toBe("2026-01-12");

    fireEvent.change(screen.getByLabelText("Date (From-To) from"), { target: { value: "2026-05-04" } });
    fireEvent.change(screen.getByLabelText("Date (From-To) to"), { target: { value: "2026-05-18" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].date_range).toBe("2026-05-04 – 2026-05-18");
  });

  it("clears both date inputs when the admin empties the range, and saves that", async () => {
    const record = withCategory("INTERNSHIP", {
      departments: [], date_range: "12 Jan 2026 – 20 Jan 2026",
    });
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
    await screen.findByLabelText("Date (From-To) from");

    // Clearing one end must leave the other end exactly where it was.
    fireEvent.change(screen.getByLabelText("Date (From-To) from"), { target: { value: "" } });
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");

    fireEvent.change(screen.getByLabelText("Date (From-To) to"), { target: { value: "" } });
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    // Blank drops the pin and hands the column back to the post text.
    expect(patchBodies[0].date_range).toBe("");
  });

  it("refuses to save an INTERNSHIP range whose From date is after its To date", async () => {
    const record = withCategory("INTERNSHIP", { departments: [], date_range: "" });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Date (From-To) from");
    fireEvent.change(screen.getByLabelText("Date (From-To) to"), { target: { value: "2026-01-12" } });
    fireEvent.change(screen.getByLabelText("Date (From-To) from"), { target: { value: "2026-01-20" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText(/cannot be after/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("PATCHes a newly picked single Date for a WORKSHOP record", async () => {
    // Every other category reports one Date column instead of a From-To range.
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        patchBodies.push(body);
        return jsonResponse({ ...baseRecord, ...body });
      });

    renderPage();
    const date = await screen.findByLabelText("Date");
    expect(date.value).toBe("2026-01-15");

    fireEvent.change(date, { target: { value: "2026-02-20" } });
    expect(screen.getByLabelText("Date").value).toBe("2026-02-20");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0]).toEqual({
      activity_date: "2026-02-20",
      _note: "admin manual correction",
    });
    expect(screen.getByLabelText("Date").value).toBe("2026-02-20");
  });

  it("shows a stored human-readable activity date instead of an empty box", async () => {
    // A date input only renders a full ISO date, so a reported "15 January 2026"
    // must still be shown -- and must not be rewritten by an unrelated save.
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

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Renamed Workshop" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0]).toEqual({
      title: "Renamed Workshop",
      _note: "admin manual correction",
    });
  });

  it("clears a pinned derived column when the admin empties it", async () => {
    const record = withCategory("CONFERENCE", { departments: [], chief_guest: "Wrong Name" });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        // An empty value is sent so the pin is dropped and the report falls back
        // to whatever the post text derives.
        expect(JSON.parse(init.body || "{}").chief_guest).toBe("");
        return jsonResponse({ ...record, chief_guest: "" });
      });

    renderPage();
    await screen.findByLabelText("Chief Guest");

    fireEvent.change(screen.getByLabelText("Chief Guest"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it("adds the Department column for a departmental CONFERENCE record", async () => {
    const record = withCategory("CONFERENCE", {
      departments: ["Computer Science and Engineering"],
      chief_guest: "",
    });
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Chief Guest");
    // The same curated vocabulary, still a + Add / − Remove multi-value editor.
    expect(screen.getByRole("button", { name: "Add Department" })).toBeInTheDocument();
  });

  it("never offers 'General' as a department value", async () => {
    // "General" is the general layout's placeholder, not a real department: a
    // departmental report must never be able to select it.
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    const department = await screen.findByLabelText("Department");
    expect(
      Array.from(department.options).map((option) => option.value),
    ).not.toContain("General");
  });

  it("drops the Department column and reports the record as general once it has no department", async () => {
    // A record with no department is legitimately reported under the general
    // layout, so removing the last department is allowed -- it just switches the
    // columns the report shows.
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Title");

    // baseRecord has one department, so it is reported department-wise.
    expect(screen.getByText(/department-wise/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Remove Department 1" }));

    // With no department left the same record reports under the general layout.
    await waitFor(() => expect(screen.getByText(/\(general\)/i)).toBeInTheDocument());
    expect(screen.queryByText(/department-wise/i)).toBeNull();
  });

  it("shows the LinkedIn URL as a link and never as an editable field", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Title");

    const link = screen.getByRole("link", { name: baseRecord.post_url });
    expect(link).toHaveAttribute("href", baseRecord.post_url);
    expect(screen.queryByLabelText("LinkedIn URL")).toBeNull();
  });

  it("discard resets multi-value fields to original record values", async () => {
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    await screen.findByLabelText("Stakeholder");

    // Add a second stakeholder row.
    fireEvent.click(screen.getByRole("button", { name: "Add Stakeholder" }));
    expect(await screen.findByLabelText("Stakeholder 2")).toBeInTheDocument();

    // Discard — second row should disappear.
    fireEvent.click(screen.getByRole("button", { name: "Discard changes" }));
    await waitFor(() => expect(screen.queryByLabelText("Stakeholder 2")).toBeNull());
    // Still only 2 fetch calls (record + options).
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  // -------------------------------------------------------------------------
  // Date pickers are genuinely usable.
  //
  // `pickDate` reproduces what the browser sends for BOTH ways of setting a date:
  // choosing it in the native calendar, and typing it into the segments. Either
  // way the control reports a complete ISO date, or "" while it is incomplete.
  // -------------------------------------------------------------------------

  function pickDate(input, value) {
    fireEvent.change(input, { target: { value } });
  }

  function internshipRecord(extra = {}) {
    return withCategory("INTERNSHIP", { departments: [], date_range: "", ...extra });
  }

  function mountWithPatches(record) {
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        const body = JSON.parse(init.body || "{}");
        patchBodies.push(body);
        return jsonResponse({ ...record, ...body });
      });
    return patchBodies;
  }

  it("check 1: a single-date field takes a picked date, keeps it, and saves it", async () => {
    const patchBodies = mountWithPatches(baseRecord);

    renderPage();
    const date = await screen.findByLabelText("Date");
    // A real native date control: not readOnly, not disabled, not blocked.
    expect(date).toHaveAttribute("type", "date");
    expect(date).not.toHaveAttribute("readonly");
    expect(date).not.toBeDisabled();

    pickDate(date, "2026-02-20");
    // Appears immediately...
    expect(screen.getByLabelText("Date").value).toBe("2026-02-20");
    // ...and survives an unrelated re-render of the whole form.
    pickDate(screen.getByLabelText("Title"), "Renamed Workshop");
    expect(screen.getByLabelText("Date").value).toBe("2026-02-20");

    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].activity_date).toBe("2026-02-20");
  });

  it("check 2: the Internship From Date works on its own", async () => {
    const patchBodies = mountWithPatches(internshipRecord());

    renderPage();
    const from = await screen.findByLabelText("Date (From-To) from");
    expect(from).toHaveAttribute("type", "date");
    expect(from).not.toHaveAttribute("readonly");
    expect(from).not.toBeDisabled();

    pickDate(from, "2026-01-12");

    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-01-12");
    // Setting From must not invent a To.
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("");

    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].date_range).toBe("2026-01-12");
  });

  it("check 3: the Internship To Date works independently of the From Date", async () => {
    const patchBodies = mountWithPatches(internshipRecord());

    renderPage();
    await screen.findByLabelText("Date (From-To) from");
    const to = screen.getByLabelText("Date (From-To) to");
    expect(to).toHaveAttribute("type", "date");
    expect(to).not.toHaveAttribute("readonly");
    expect(to).not.toBeDisabled();

    pickDate(to, "2026-01-20");

    // The picked To stays in the To box and From is left genuinely empty.
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("");

    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].date_range).toBe("2026-01-20");
  });

  it("check 4: a calendar-chosen date appears at once and stays after re-render", async () => {
    mountWithPatches(internshipRecord());

    renderPage();
    await screen.findByLabelText("Date (From-To) from");

    // The browser sends a complete ISO date when the day is clicked in the picker.
    pickDate(screen.getByLabelText("Date (From-To) from"), "2026-04-07");
    pickDate(screen.getByLabelText("Date (From-To) to"), "2026-04-25");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-04-07");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-04-25");

    // Force several unrelated re-renders; neither date may drift or reset.
    pickDate(screen.getByLabelText("Title"), "Renamed Internship");
    pickDate(screen.getByLabelText("Duration"), "2 weeks");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-04-07");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-04-25");
  });

  it("check 4b: a typed date clears the field until it is complete, then applies", async () => {
    // Manual entry: the browser reports "" while the segments are half-filled.
    mountWithPatches(internshipRecord());

    renderPage();
    await screen.findByLabelText("Date (From-To) from");

    pickDate(screen.getByLabelText("Date (From-To) from"), "2026-06-0");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("");
    pickDate(screen.getByLabelText("Date (From-To) from"), "2026-06-09");
    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-06-09");
  });

  it("check 4c: both ends survive when React batches the two changes together", async () => {
    // The other end must be read from the latest draft, not from the render
    // closure, or a batched pair of edits would lose one of the two dates.
    mountWithPatches(internshipRecord());

    renderPage();
    await screen.findByLabelText("Date (From-To) from");
    const from = screen.getByLabelText("Date (From-To) from");
    const to = screen.getByLabelText("Date (From-To) to");

    act(() => {
      from.value = "2026-07-01";
      from.dispatchEvent(new Event("input", { bubbles: true }));
      to.value = "2026-07-31";
      to.dispatchEvent(new Event("input", { bubbles: true }));
    });

    expect(screen.getByLabelText("Date (From-To) from").value).toBe("2026-07-01");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-07-31");
  });

  it("check 5: a saved range is still shown when the record is reopened", async () => {
    const record = internshipRecord();
    const saved = { ...record, date_range: "2026-01-12 – 2026-01-20" };
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(record))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        patchBodies.push(JSON.parse(init.body || "{}"));
        return jsonResponse(saved);
      });

    renderPage();
    await screen.findByLabelText("Date (From-To) from");
    pickDate(screen.getByLabelText("Date (From-To) from"), "2026-01-12");
    pickDate(screen.getByLabelText("Date (From-To) to"), "2026-01-20");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));
    expect(patchBodies[0].date_range).toBe("2026-01-12 – 2026-01-20");

    // Reopen: the range is still in both boxes.
    cleanup();
    fetchMock.mockReset();
    fetchMock
      .mockImplementationOnce(() => jsonResponse(saved))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    expect((await screen.findByLabelText("Date (From-To) from")).value).toBe("2026-01-12");
    expect(screen.getByLabelText("Date (From-To) to").value).toBe("2026-01-20");
  });

  it("check 5b: a saved single date is still shown when the record is reopened", async () => {
    const saved = { ...baseRecord, activity_date: "2026-02-20" };
    const patchBodies = [];
    fetchMock
      .mockImplementationOnce(() => jsonResponse(baseRecord))
      .mockImplementationOnce(() => jsonResponse(options))
      .mockImplementationOnce((url, init = {}) => {
        patchBodies.push(JSON.parse(init.body || "{}"));
        return jsonResponse(saved);
      });

    renderPage();
    await screen.findByLabelText("Date");
    pickDate(screen.getByLabelText("Date"), "2026-02-20");
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(patchBodies).toHaveLength(1));

    cleanup();
    fetchMock.mockReset();
    fetchMock
      .mockImplementationOnce(() => jsonResponse(saved))
      .mockImplementationOnce(() => jsonResponse(options));

    renderPage();
    expect((await screen.findByLabelText("Date")).value).toBe("2026-02-20");
  });
});
