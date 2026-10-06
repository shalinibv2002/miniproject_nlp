import { describe, expect, it } from "vitest";
import { isoDate, joinDateRange, splitDateRange } from "./dates";

describe("isoDate", () => {
  it("passes a native date input's ISO value straight through", () => {
    // The value an <input type="date"> hands back on every change. If this is
    // not recognised, the picked date is wiped on the next render.
    expect(isoDate("2026-01-12")).toBe("2026-01-12");
    expect(isoDate("2026-12-31")).toBe("2026-12-31");
    expect(isoDate("  2026-01-12  ")).toBe("2026-01-12");
  });

  it("also understands the human formats a reported value can hold", () => {
    // The report writes dates as "%d %B %Y", so a full month name is the common
    // case, and it has to survive the same parse as the abbreviated form.
    expect(isoDate("12 Jan 2026")).toBe("2026-01-12");
    expect(isoDate("12 January 2026")).toBe("2026-01-12");
    expect(isoDate("15 January 2026")).toBe("2026-01-15");
    expect(isoDate("5 Jan 2026")).toBe("2026-01-05");
  });

  it("rejects anything that is not a real calendar date", () => {
    // A malformed value would be rejected by the browser and silently blank the
    // input, so it must resolve to "" instead.
    expect(isoDate("2026-02-30")).toBe("");
    expect(isoDate("2026-13-01")).toBe("");
    expect(isoDate("2026-00-10")).toBe("");
    expect(isoDate("31 Feb 2026")).toBe("");
    expect(isoDate("January 2026")).toBe("");
    expect(isoDate("not a date")).toBe("");
    expect(isoDate("")).toBe("");
    expect(isoDate(null)).toBe("");
    expect(isoDate(undefined)).toBe("");
  });
});

describe("splitDateRange", () => {
  it("reads back both the ISO and human From-To forms", () => {
    expect(splitDateRange("2026-01-12 – 2026-01-20")).toEqual(["2026-01-12", "2026-01-20"]);
    expect(splitDateRange("2026-01-12 - 2026-01-20")).toEqual(["2026-01-12", "2026-01-20"]);
    expect(splitDateRange("2026-01-12 to 2026-01-20")).toEqual(["2026-01-12", "2026-01-20"]);
    expect(splitDateRange("12 Jan 2026 – 20 Jan 2026")).toEqual(["2026-01-12", "2026-01-20"]);
    expect(splitDateRange("12 January 2026 – 20 January 2026"))
      .toEqual(["2026-01-12", "2026-01-20"]);
  });

  it("treats a lone date as the From end and leaves the other box empty", () => {
    expect(splitDateRange("2026-01-12")).toEqual(["2026-01-12", ""]);
    expect(splitDateRange("12 Jan 2026")).toEqual(["2026-01-12", ""]);
  });

  it("returns two blank boxes for a missing or unreadable value", () => {
    expect(splitDateRange("")).toEqual(["", ""]);
    expect(splitDateRange(null)).toEqual(["", ""]);
    expect(splitDateRange("sometime in March")).toEqual(["", ""]);
  });
});

describe("joinDateRange", () => {
  it("round trips a full range", () => {
    expect(joinDateRange("2026-01-12", "2026-01-20")).toBe("2026-01-12 – 2026-01-20");
    expect(splitDateRange(joinDateRange("2026-01-12", "2026-01-20")))
      .toEqual(["2026-01-12", "2026-01-20"]);
  });

  it("round trips a half-filled range without losing the set end", () => {
    expect(splitDateRange(joinDateRange("2026-01-12", ""))).toEqual(["2026-01-12", ""]);
  });

  it("is empty only when neither end is set", () => {
    expect(joinDateRange("", "")).toBe("");
    expect(joinDateRange(null, undefined)).toBe("");
  });
});