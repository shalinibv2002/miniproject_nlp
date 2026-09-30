import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import LinkedinPublicQuery from "./LinkedinPublicQuery";
import { queryCountBody, queryCompareBody, queryZeroBody } from "./publicFixtures";
import { jsonResponse, routeFetch } from "./testFixtures";

function mockQuery() {
  global.fetch = vi.fn().mockImplementation(routeFetch([
    {
      match: /\/api\/linkedin\/query/,
      respond: (url, options) => {
        const text = JSON.parse(options.body || "{}").question || "";
        if (text.includes("naval")) return jsonResponse(queryZeroBody);
        if (/\bor\b/i.test(text)) return jsonResponse(queryCompareBody);
        if (/workshops/i.test(text)) return jsonResponse(queryCountBody);
        return jsonResponse(queryCountBody);
      },
    },
  ]));
}

function renderQuery() {
  return render(<MemoryRouter><LinkedinPublicQuery /></MemoryRouter>);
}

describe("LinkedinPublicQuery", () => {
  afterEach(() => vi.restoreAllMocks());

  it("answers a question and shows activities returned by the API", async () => {
    mockQuery();
    renderQuery();

    const input = screen.getByRole("textbox", { name: "Your question" });
    fireEvent.change(input, { target: { value: "How many workshops were conducted in 2025-26?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => expect(screen.getByText(/55 matching activities found/i)).toBeInTheDocument());
    expect(screen.getByText("Academic year: 2025-26")).toBeInTheDocument();
    expect(screen.getByText("Category: Workshops")).toBeInTheDocument();
    expect(screen.getByText("Machine Learning Workshop")).toBeInTheDocument();
  });

  it("renders comparison charts and tables for compare questions", async () => {
    mockQuery();
    renderQuery();

    fireEvent.change(screen.getByRole("textbox", { name: "Your question" }), { target: { value: "More workshops or seminars?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => expect(screen.getByText(/Workshops has more activities than Seminars/i)).toBeInTheDocument());
    expect(screen.getByRole("columnheader", { name: "Entity" })).toBeInTheDocument();
    expect(screen.getAllByText("Workshops").length).toBeGreaterThan(0);
    expect(screen.getAllByText("179").length).toBeGreaterThan(0);
    expect(screen.getAllByText("60").length).toBeGreaterThan(0);
  });

  it("shows an honest empty result for zero matches", async () => {
    mockQuery();
    renderQuery();

    fireEvent.change(screen.getByRole("textbox", { name: "Your question" }), { target: { value: "How many naval activities existed?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    await waitFor(() => expect(screen.getByText(/No matching activities were found/i)).toBeInTheDocument());
  });

  it("offers example questions as one-click prompts", async () => {
    mockQuery();
    renderQuery();
    expect(screen.getByRole("button", { name: "What categories are available?" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Show sports activities" })).toBeInTheDocument();
  });
});