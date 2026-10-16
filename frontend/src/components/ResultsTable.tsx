"use client";
import {
  ColumnDef, flexRender, getCoreRowModel, getFilteredRowModel, getPaginationRowModel,
  getSortedRowModel, SortingState, useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, Download } from "lucide-react";
import { useMemo, useState } from "react";
import { formatCell, toCsv } from "@/lib/format";
import type { Column } from "@/types";
import { Button } from "./ui";

export function ResultsTable({ columns, rows, truncated = false }:
  { columns: Column[]; rows: unknown[][]; truncated?: boolean }) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [filter, setFilter] = useState("");

  const defs = useMemo<ColumnDef<unknown[]>[]>(() => columns.map((c, i) => ({
    id: c.name, header: c.name, accessorFn: (r) => r[i],
    cell: (ctx) => {
      const v = ctx.getValue();
      return v === null || v === undefined
        ? <span className="italic text-slate-400">null</span>
        : <span className={typeof v === "number" ? "tabular-nums" : ""}>{formatCell(v)}</span>;
    },
    sortingFn: "alphanumeric",
  })), [columns]);

  const table = useReactTable({
    data: rows, columns: defs, state: { sorting, globalFilter: filter },
    onSortingChange: setSorting, onGlobalFilterChange: setFilter,
    getCoreRowModel: getCoreRowModel(), getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(), getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: 25 } },
  });

  const download = () => {
    const blob = new Blob([toCsv(columns.map((c) => c.name), rows)], { type: "text/csv" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "results.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  };

  if (rows.length === 0) return <p className="py-6 text-center text-sm text-slate-500">No rows returned.</p>;
  const filtered = table.getFilteredRowModel().rows.length;
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <input aria-label="Filter rows" placeholder="Filter rows…" value={filter} onChange={(e) => setFilter(e.target.value)}
          className="w-56 rounded-md border border-slate-300 px-3 py-1.5 text-sm" />
        <Button variant="secondary" onClick={download}><Download className="h-4 w-4" />Export CSV</Button>
      </div>
      <div className="overflow-x-auto rounded-md border border-slate-200">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-50">
            {table.getHeaderGroups().map((hg) => (
              <tr key={hg.id}>{hg.headers.map((h) => {
                const dir = h.column.getIsSorted();
                return (
                  <th key={h.id} scope="col" aria-sort={dir === "asc" ? "ascending" : dir === "desc" ? "descending" : "none"} className="whitespace-nowrap px-3 py-2 font-medium text-slate-700">
                    <button className="flex items-center gap-1" onClick={h.column.getToggleSortingHandler()}>
                      {flexRender(h.column.columnDef.header, h.getContext())}
                      {dir === "asc" && <ArrowUp className="h-3 w-3" />}{dir === "desc" && <ArrowDown className="h-3 w-3" />}
                    </button>
                  </th>
                );
              })}</tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-100">
                {r.getVisibleCells().map((c) => <td key={c.id} className="whitespace-nowrap px-3 py-2">{flexRender(c.column.columnDef.cell, c.getContext())}</td>)}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-slate-600">
        <span>
          {filtered === rows.length ? `${rows.length.toLocaleString()} rows` : `${filtered.toLocaleString()} of ${rows.length.toLocaleString()} rows`}
          {truncated && " — results were limited by the server; this is not the full result"}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="secondary" disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>Previous</Button>
          <span>Page {table.getState().pagination.pageIndex + 1} / {Math.max(table.getPageCount(), 1)}</span>
          <Button variant="secondary" disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>Next</Button>
        </div>
      </div>
    </div>
  );
}
