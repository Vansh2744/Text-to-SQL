import { describe, expect, it } from "vitest";
import { formatCell, suggestQuestions, toCsv } from "@/lib/format";
import { ApiError, errorMessage } from "@/lib/api";
import { allowedTypes } from "@/components/ResultChart";

describe("toCsv", () => {
  it("escapes quotes/commas and neutralises formula injection", () => {
    const csv = toCsv(["a", "b"], [['he said "hi", ok', "=HYPERLINK(\"x\")"], [null, 5]]);
    expect(csv.split("\n")[1]).toBe('"he said ""hi"", ok","\'=HYPERLINK(""x"")"');
    expect(csv.split("\n")[2]).toBe(",5");
  });
  it("does not prefix negative numbers", () => {
    expect(toCsv(["n"], [[-3]]).split("\n")[1]).toBe("-3");
  });
});

describe("formatCell", () => {
  it("renders null and numbers sensibly", () => {
    expect(formatCell(null)).toBe("null");
    expect(formatCell(1234)).toBe((1234).toLocaleString());
    expect(formatCell("x")).toBe("x");
  });
});

describe("suggestQuestions", () => {
  it("uses real column names", () => {
    const q = suggestQuestions([{ name: "region", type: "VARCHAR" }, { name: "revenue", type: "DOUBLE" }]);
    expect(q.some((s) => s.includes("revenue") && s.includes("region"))).toBe(true);
  });
});

describe("errorMessage", () => {
  it("maps known codes and passes through validation detail", () => {
    expect(errorMessage(new ApiError(504, "query_timeout", "x"))).toMatch(/timed out/);
    expect(errorMessage(new ApiError(422, "sql_validation_failed", "Unknown table 'x'."))).toContain("Unknown table");
    expect(errorMessage(new Error("boom"))).toBe("Something went wrong.");
  });
});

describe("allowedTypes", () => {
  const cols = [{ name: "c", type: "VARCHAR" }, { name: "v", type: "BIGINT" }];
  it("offers pie only for one measure and few rows; scatter only for numeric x", () => {
    const viz = { type: "bar" as const, x: "c", y: ["v"] };
    expect(allowedTypes(viz, cols, 5)).toContain("pie");
    expect(allowedTypes(viz, cols, 50)).not.toContain("pie");
    expect(allowedTypes(viz, cols, 5)).not.toContain("scatter");
    expect(allowedTypes({ ...viz, x: "v" }, cols, 5)).toContain("scatter");
  });
});
