"use client";
import { RotateCw } from "lucide-react";
import { useState } from "react";
import { AnalysisView } from "@/components/AnalysisView";
import { Badge, Button, Card, Empty, ErrorBox, PageHeader, Spinner } from "@/components/ui";
import { api, errorMessage } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import type { Analysis } from "@/types";

export default function HistoryPage() {
  const { data, error, loading } = useApi(api.history);
  const [result, setResult] = useState<Analysis | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState("");

  const rerun = async (id: string) => {
    setBusy(id); setErr(null);
    try { setResult(await api.rerun(id)); } catch (e) { setErr(errorMessage(e)); } finally { setBusy(""); }
  };
  return (
    <>
      <PageHeader title="Query History" />
      {loading && <Spinner />}
      {(error || err) && <ErrorBox message={(error ?? err)!} />}
      {data && (data.length === 0 ? <Empty>No queries yet.</Empty> : (
        <Card><ul className="divide-y divide-slate-100">{data.map((h) => (
          <li key={h.id} className="flex flex-wrap items-start justify-between gap-3 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{h.question ?? "(edited SQL)"}</p>
              <p className="truncate font-mono text-xs text-slate-500">{h.sql}</p>
              <p className="text-xs text-slate-500">{formatDate(h.created_at)}{h.duration_ms !== null && ` · ${h.duration_ms} ms`}{h.row_count !== null && ` · ${h.row_count} rows`}</p>
            </div>
            <div className="flex items-center gap-2">
              <Badge>{h.status}</Badge>
              {h.sql && <Button variant="secondary" onClick={() => rerun(h.id)} disabled={busy !== ""}><RotateCw className="h-4 w-4" />{busy === h.id ? "Running…" : "Rerun"}</Button>}
            </div>
          </li>))}</ul></Card>))}
      {result && <div className="mt-6"><AnalysisView result={result} /></div>}
    </>
  );
}
