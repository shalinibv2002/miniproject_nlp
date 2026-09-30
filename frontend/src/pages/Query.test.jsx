import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Query from "./Query";

vi.mock("recharts", () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  BarChart: ({ children, data = [] }) => (
    <div>{data.map((row) => <span key={row.name}>{row.name}</span>)}{children}</div>
  ),
  Bar: function Bar() { return <span data-testid="bar" />; },
  XAxis: () => null, YAxis: () => null, Tooltip: () => null, CartesianGrid: () => null,
}));

const result = {
  question: "What sports activities are available?", status: "answer", count: 1,
  answer: "Found 1 matching activity.", criteria: ["Sports"],
  activities: [{ id: 7, title: "TCE Sports Day", academic_year: "2021-22", activity_date: "2022-06-07",
    department: "General", stakeholder: "Students", categories: [{ code: "SPORTS", name: "Sports and Games" }],
    source_url: "https://www.tce.edu/sports" }],
};
const response = (body) => ({ ok: true, json: async () => body });

describe("Ask the Data", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(response(result)))));

  it("renders grounded public answers and activity links without internal details", async () => {
    render(<MemoryRouter><Query /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: "How many activities are there?" }));
    expect(await screen.findByText("Found 1 matching activity.")).toBeInTheDocument();
    expect(screen.getByText("TCE Sports Day")).toHaveAttribute("href", "/activities/7");
    expect(screen.getByText("Sports and Games")).toBeInTheDocument();
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.queryByText(/intent|filters used|sql|classifier|confidence/i)).not.toBeInTheDocument();
  });

  it("renders criteria chips alongside the answer", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      ...result, answer: "23 matching activities found.", criteria: ["Workshops", "2024-2025"],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: "How many workshops happened in 2024-2025?" }));
    expect(await screen.findByText("23 matching activities found.")).toBeInTheDocument();
    const chips = screen.getByLabelText("Query criteria");
    expect(chips).toHaveTextContent("Workshops");
    expect(chips).toHaveTextContent("2024-2025");
  });

  it("renders a chart and ranking rows for grouped answers", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      answer: "Achievement and awards by department: Information Technology (5); Civil Engineering (3).",
      status: "answer", count: null, criteria: ["Achievement and Awards"],
      rows: [
        { label: "Information Technology", value: 5 },
        { label: "Civil Engineering", value: 3 },
      ],
      chart: { data: [
        { label: "Information Technology", value: 5 },
        { label: "Civil Engineering", value: 3 },
      ] },
      comparison: [
        { department: "Information Technology", activity_count: 5 },
        { department: "Civil Engineering", activity_count: 3 },
      ],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: "Rank departments by number of achievements." }));
    expect(await screen.findByText("Result Breakdown")).toBeInTheDocument();
    expect(screen.getAllByText("Information Technology").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("Civil Engineering").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByTestId("bar").length).toBeGreaterThan(0);
    expect(screen.queryByText("Comparative View")).not.toBeInTheDocument();
  });

  it("renders a comparison table with full period labels", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      answer: "2024-2025 had the most workshops with 23 matching activities.",
      status: "answer", count: 23, criteria: ["Workshops"],
      rows: [{ label: "2024-2025", value: 23 }, { label: "2023-2024", value: 16 }],
      chart: { data: [{ label: "2024-2025", value: 23 }, { label: "2023-2024", value: 16 }] },
      comparison: [
        { academic_year: "2021-22", activity_count: 4 },
        { academic_year: "2022-23", activity_count: 7 },
        { academic_year: "2023-24", activity_count: 16 },
        { academic_year: "2024-25", activity_count: 23 },
        { academic_year: "2025-26", activity_count: 10 },
      ],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: "Which year had the most workshops?" }));
    expect(await screen.findByText("2024-2025 had the most workshops with 23 matching activities.")).toBeInTheDocument();
    expect(screen.getByText("Comparative View")).toBeInTheDocument();
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.getByText("2025-2026")).toBeInTheDocument();
  });

  it("renders a detail card for a named event", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      answer: "Here are the details for the Future Ready seminar (1 matching activity).",
      status: "answer", count: 1, criteria: ["Future Ready seminar"],
      activities: [], detail: {
        id: 30, title: "Future Ready Seminar on Industry 5.0", academic_year: "2024-25",
        activity_date: "2024-11-10", department: "Information Technology",
        stakeholder: "Students", description: "Industry 5.0 orientation.",
        categories: [{ code: "SEMINAR", name: "Seminar" }],
        source_url: "https://www.tce.edu/future-ready",
      },
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: "Which year had the most workshops?" }));
    expect(await screen.findByText("Future Ready Seminar on Industry 5.0")).toBeInTheDocument();
    expect(screen.getByText("Future Ready Seminar on Industry 5.0")).toHaveAttribute("href", "/activities/30");
    expect(screen.getByText("2024-2025")).toBeInTheDocument();
    expect(screen.getByText("Industry 5.0 orientation.")).toBeInTheDocument();
    expect(screen.getByText("Official TCE Source")).toHaveAttribute("href", "https://www.tce.edu/future-ready");
  });

  it("hides technical request errors", async () => {
    globalThis.fetch.mockRejectedValueOnce(new Error("database failure"));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(example);
    expect(await screen.findByText("Unable to answer this question. Please try again.")).toBeInTheDocument();
    expect(screen.queryByText(/database failure/)).not.toBeInTheDocument();
  });

  it("displays zero-result message cleanly", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      question: "How many conferences in 2021-2022?", status: "zero", count: 0,
      answer: "No matching activities were found for the selected criteria.", criteria: ["Conference", "2021-2022"],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many workshops happened in 2024-2025?" });
    fireEvent.click(example);
    expect(await screen.findByText("No matching activities were found for the selected criteria.")).toBeInTheDocument();
  });

  it("displays unsupported question message", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      question: "What is the weather?", status: "unsupported", count: 0,
      answer: "That information is not available in the TCE activity data.", criteria: [],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "Top 5 departments by research activities." });
    fireEvent.click(example);
    expect(await screen.findByText("That information is not available in the TCE activity data.")).toBeInTheDocument();
  });

  it("displays clarification question message", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      question: "How many activities in 2026-2027?", status: "clarification", count: 0,
      answer: "Do you mean academic year 2025-2026?", criteria: [],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "Which department had the fewest workshops?" });
    fireEvent.click(example);
    expect(await screen.findByText("Do you mean academic year 2025-2026?")).toBeInTheDocument();
  });

  it("displays full period format and never short backend format", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      ...result, activities: [{ ...result.activities[0], academic_year: "2024-25" }],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(example);
    expect(await screen.findByText("2024-2025")).toBeInTheDocument();
    expect(screen.queryByText("2024-25")).not.toBeInTheDocument();
  });

  it("falls back to Students for a missing stakeholder and hides the date", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      ...result, activities: [{
        id: 10, title: "Unknown Activity", academic_year: null,
        activity_date: null, department: null, stakeholder: null,
        categories: [], source_url: null,
      }],
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(example);
    expect(await screen.findByText("Unknown Activity")).toBeInTheDocument();
    expect(screen.getByText("Students")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.queryByText("10 Nov 2024")).not.toBeInTheDocument();
  });

  it("does not display SQL, intent, classifier, or confidence in the DOM", async () => {
    globalThis.fetch.mockResolvedValueOnce(response({
      ...result, intent: "count", filters: { category: "SPORTS" },
      classifier: "rule-based", confidence: 0.95, sql: "SELECT * FROM ...",
    }));
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(example);
    expect(await screen.findByText("Found 1 matching activity.")).toBeInTheDocument();
    expect(screen.queryByText(/SELECT/)).not.toBeInTheDocument();
    expect(screen.queryByText(/intent/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/classifier/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/0\.95/)).not.toBeInTheDocument();
    expect(screen.queryByText(/SPORTS/)).not.toBeInTheDocument();
  });

  it("renders all required activity fields with links", async () => {
    render(<MemoryRouter><Query /></MemoryRouter>);
    const example = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(example);
    expect(await screen.findByText("TCE Sports Day")).toBeInTheDocument();
    expect(screen.getByText("TCE Sports Day").closest("a")).toHaveAttribute("href", "/activities/7");
    expect(screen.getByText("Sports and Games")).toBeInTheDocument();
    expect(screen.getByText("2021-2022")).toBeInTheDocument();
    expect(screen.getAllByText("General").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Students")).toBeInTheDocument();
    expect(screen.queryByText("07 Jun 2022")).not.toBeInTheDocument();
    expect(screen.getByText("Official TCE Source")).toHaveAttribute("href", "https://www.tce.edu/sports");
  });

  it("deterministic: same response produces identical render", async () => {
    const { unmount } = render(<MemoryRouter><Query /></MemoryRouter>);
    const first = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(first);
    expect(await screen.findByText("Found 1 matching activity.")).toBeInTheDocument();
    unmount();

    render(<MemoryRouter><Query /></MemoryRouter>);
    const second = await screen.findByRole("button", { name: "How many activities are there?" });
    fireEvent.click(second);
    expect(await screen.findByText("Found 1 matching activity.")).toBeInTheDocument();
  });
});