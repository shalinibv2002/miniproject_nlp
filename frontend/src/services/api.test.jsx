import { describe, expect, it } from "vitest";
import { buildQuery } from "./api";

describe("buildQuery", () => {
  it("maps public filters to supported activity parameters", () => {
    expect(buildQuery({
      period: "2021-22",
      department: "General",
      category: "SPORTS",
      generalCategory: "ACHIEVEMENT",
      departmentalCategory: "INDUSTRY",
      order: "asc",
    })).toBe("?academic_year=2021-22&department=General&category=SPORTS&general_category=ACHIEVEMENT&departmental_category=INDUSTRY&order=asc");
  });

  it("maps the public stakeholder filter to the supported activity parameter", () => {
    expect(buildQuery({
      search: "marathon", dateFrom: "2022-01-01", dateTo: "2022-12-31", sort: "title",
      scope: "Departmental", stakeholder: "Students", verified: "true",
    })).toBe("?stakeholder=Students");
  });

  it("does not send removed legacy public filters", () => {
    expect(buildQuery({
      search: "marathon", dateFrom: "2022-01-01", dateTo: "2022-12-31", sort: "title",
      scope: "Departmental", verified: "true",
    })).toBe("");
  });
});