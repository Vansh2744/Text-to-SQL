"use client";
import { Clock } from "lucide-react";
import type { Analysis } from "@/types";
import { Card } from "./ui";
import { ResultChart } from "./ResultChart";
import { ResultsTable } from "./ResultsTable";

export function AnalysisView({ result }: { result: Analysis }) {
  return (
    <div className="space-y-4">
      {result.explanation && <Card title="Explanation"><p className="text-sm leading-relaxed">{result.explanation}</p></Card>}
      <p className="flex items-center gap-3 text-xs text-slate-500">
        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{result.duration_ms} ms</span>
        <span>{result.row_count.toLocaleString()} rows{result.truncated && " (truncated)"}</span>
        {result.attempts > 1 && <span>{result.attempts} attempts</span>}
      </p>
      {result.visualization && <Card><ResultChart viz={result.visualization} columns={result.columns} rows={result.rows} /></Card>}
      <Card title="Results"><ResultsTable columns={result.columns} rows={result.rows} truncated={result.truncated} /></Card>
    </div>
  );
}
