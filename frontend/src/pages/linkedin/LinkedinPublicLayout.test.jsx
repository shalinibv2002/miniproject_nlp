import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import LinkedinPublicLayout from "../../components/LinkedinPublicLayout";

function renderLayout() {
  return render(
    <MemoryRouter>
      <LinkedinPublicLayout />
    </MemoryRouter>
  );
}

describe("public LinkedIn layout", () => {
  it("shows the public navigation and branding", () => {
    renderLayout();
    expect(screen.getByRole("heading", { name: "TCE Institutional Activity Intelligence" })).toBeInTheDocument();
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    const links = within(nav).getAllByRole("link");
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/", "/categories", "/reports", "/query",
    ]);
  });

  it("does not offer standalone Activities or Stakeholders modules in the menu", () => {
    renderLayout();
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    const hrefs = within(nav).getAllByRole("link").map((link) => link.getAttribute("href"));
    expect(hrefs).not.toContain("/activities");
    expect(hrefs).not.toContain("/stakeholders");
  });

  it("never exposes admin or internal entry points to public visitors", () => {
    renderLayout();
    expect(screen.queryByRole("link", { name: /admin/i })).not.toBeInTheDocument();
    for (const internal of ["Review Queue", "Validation Dashboard", "Data Sources", "Evidence", "Confidence"]) {
      expect(screen.queryByText(internal)).not.toBeInTheDocument();
    }
  });

  it("credits the data source honestly in the footer", () => {
    renderLayout();
    expect(screen.getByText(/Based on available TCE LinkedIn posts/i)).toBeInTheDocument();
    const login = screen.getByRole("link", { name: "Staff login" });
    expect(login.getAttribute("href")).toBe("/admin/login");
  });
});