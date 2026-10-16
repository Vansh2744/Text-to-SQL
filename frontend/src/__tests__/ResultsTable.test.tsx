import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { ResultsTable } from "@/components/ResultsTable";

const cols = [{ name: "region", type: "VARCHAR" }, { name: "revenue", type: "DOUBLE" }];

describe("ResultsTable", () => {
  it("renders nulls, row count and truncation warning", () => {
    render(<ResultsTable columns={cols} rows={[["N", 10], [null, null]]} truncated />);
    expect(screen.getAllByText("null")).toHaveLength(2);
    expect(screen.getByText(/2 rows/)).toBeInTheDocument();
    expect(screen.getByText(/not the full result/)).toBeInTheDocument();
  });

  it("sorts when a header is clicked and filters rows", async () => {
    const user = userEvent.setup();
    render(<ResultsTable columns={cols} rows={[["b", 1], ["a", 2], ["c", 3]]} />);
    await user.click(screen.getByRole("button", { name: "region" }));
    const firstCell = () => screen.getAllByRole("row")[1]!.querySelector("td")!.textContent;
    expect(firstCell()).toBe("a");
    await user.type(screen.getByLabelText("Filter rows"), "c");
    expect(screen.getByText(/1 of 3 rows/)).toBeInTheDocument();
  });

  it("shows an empty state", () => {
    render(<ResultsTable columns={cols} rows={[]} />);
    expect(screen.getByText("No rows returned.")).toBeInTheDocument();
  });
});
