"use client";
import { Play, Trash2 } from "lucide-react";
import { useState } from "react";
import { AnalysisView } from "@/components/AnalysisView";
import { Button, Card, Empty, ErrorBox, PageHeader, Spinner } from "@/components/ui";
import { api, errorMessage } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { Analysis } from "@/types";

export default function SavedPage() {
  const { data, error, loading, reload } = useApi(api.saved);
  const [result, setResult] = useState<Analysis | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const run = async (id: string) => {
    setErr(null);
    try { setResult(await api.runSaved(id)); } catch (e) { setErr(errorMessage(e)); }
  };
  const remove = async (id: string) => {
    if (!confirm("Delete this saved query?")) return;
    try { await api.deleteSaved(id); reload(); } catch (e) { setErr(errorMessage(e)); }
  };
  return (
    <>
      <PageHeader title="Saved Queries" />
      {loading && <Spinner />}
      {(error || err) && <ErrorBox message={(error ?? err)!} />}
      {data && (data.length === 0 ? <Empty>Nothing saved yet. Save a query from the workspace.</Empty> : (
        <div className="space-y-3">{data.map((s) => (
          <Card key={s.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0"><p className="font-medium">{s.title}</p>
                {s.description && <p className="text-sm text-slate-600">{s.description}</p>}
                <p className="mt-1 truncate font-mono text-xs text-slate-500">{s.sql}</p></div>
              <div className="flex gap-2">
                <Button onClick={() => run(s.id)}><Play className="h-4 w-4" />Run</Button>
                <Button variant="danger" aria-label={`Delete ${s.title}`} onClick={() => remove(s.id)}><Trash2 className="h-4 w-4" /></Button>
              </div>
            </div>
          </Card>))}</div>))}
      {result && <div className="mt-6"><AnalysisView result={result} /></div>}
    </>
  );
}
