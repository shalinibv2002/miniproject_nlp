import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicCategories from "./LinkedinPublicCategories";
import LinkedinPublicDepartments from "./LinkedinPublicDepartments";
import LinkedinPublicStakeholders from "./LinkedinPublicStakeholders";
import { jsonResponse, routeFetch } from "./testFixtures";

function renderPage(Component) {
  return render(<MemoryRouter><Component /></MemoryRouter>);
}

describe("LinkedinPublicCategories", () => {
  afterEach(() => vi.restoreAllMocks());

  it("acts as the landing page for the two separate activity worlds", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /\/api\/linkedin\/categories/, respond: () => jsonResponse([]) },
    ]));
    renderPage(LinkedinPublicCategories);
    await waitFor(() => expect(screen.getByText("General Categories")).toBeInTheDocument());
    expect(screen.getByText("Departments")).toBeInTheDocument();

    const general = screen.getByRole("link", { name: /Browse General/ });
    expect(general.getAttribute("href")).toBe("/categories/general");
    const depts = screen.getByRole("link", { name: /Browse Departments/ });
    expect(depts.getAttribute("href")).toBe("/departments");
  });
});

describe("LinkedinPublicDepartments", () => {
  afterEach(() => vi.restoreAllMocks());

  it("lists organising departments without the institution-wide General bucket", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /\/api\/linkedin\/departments/, respond: () => jsonResponse([
        { department: "General", activity_count: 900 },
        { department: "Computer Science and Engineering", activity_count: 300 },
      ]) },
    ]));
    renderPage(LinkedinPublicDepartments);
    await waitFor(() => expect(screen.getByText("Computer Science and Engineering")).toBeInTheDocument());
    expect(screen.queryByRole("link", { name: /^General/ })).not.toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();

    const link = screen.getByRole("link", { name: /Computer Science and Engineering/ });
    expect(link.getAttribute("href")).toBe("/departments/Computer%20Science%20and%20Engineering");
  });
});

describe("LinkedinPublicStakeholders", () => {
  afterEach(() => vi.restoreAllMocks());

  it("renders stakeholder counts and drill links", async () => {
    global.fetch = vi.fn().mockImplementation(routeFetch([
      { match: /\/api\/linkedin\/stakeholders/, respond: () => jsonResponse([
        { stakeholder: "Students", activity_count: 1100 },
        { stakeholder: "Institution", activity_count: 250 },
      ]) },
    ]));
    renderPage(LinkedinPublicStakeholders);
    await waitFor(() => expect(screen.getByText("Students")).toBeInTheDocument());
    expect(screen.getByText("Institution")).toBeInTheDocument();
    expect(screen.getByText("1100")).toBeInTheDocument();

    const students = screen.getByRole("link", { name: /Students/ });
    expect(students.getAttribute("href")).toBe("/activities?stakeholder=Students");
  });
});