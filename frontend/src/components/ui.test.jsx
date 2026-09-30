import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { KpiCard, DataTable, Card } from "./ui";

describe("UI components", () => {
  it("renders a KPI card with label and value", () => {
    render(<KpiCard label="Total Activities" value="10" />);
    expect(screen.getByText("Total Activities")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("renders a Card with its title", () => {
    render(<Card title="Hello">
      <p>content</p>
    </Card>);
    expect(screen.getByText("Hello")).toBeInTheDocument();
  });

  it("shows an empty state for DataTable without rows", () => {
    render(<DataTable columns={[{ key: "a", label: "A" }]} rows={[]} />);
    expect(screen.getByText("No data available.")).toBeInTheDocument();
  });

  it("renders table rows with custom renderers", () => {
    render(
      <DataTable
        columns={[
          { key: "code", label: "Code" },
          { key: "status", label: "Status", render: (r) => `pill:${r.status}` },
        ]}
        rows={[{ code: "CSE", status: "verified" }]}
      />
    );
    expect(screen.getByText("CSE")).toBeInTheDocument();
    expect(screen.getByText("pill:verified")).toBeInTheDocument();
  });
});