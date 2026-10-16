"use client";
import { Trash2, Upload } from "lucide-react";
import Link from "next/link";
import { useRef, useState } from "react";
import { Badge, Button, Card, Empty, ErrorBox, PageHeader, Spinner } from "@/components/ui";
import { ResultsTable } from "@/components/ResultsTable";
import { api, errorMessage } from "@/lib/api";
import { formatBytes, formatDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import type { Dataset } from "@/types";

function Details({ id }: { id: string }) {
  const profile = useApi(() => api.profile(id), [id]);
  const preview = useApi(() => api.preview(id), [id]);
  if (profile.loading || preview.loading) return <Spinner />;
  if (profile.error || preview.error || !profile.data || !preview.data) return <ErrorBox message={profile.error ?? preview.error ?? "Failed"} />;
  return (
    <div className="space-y-4">
      <div className="overflow-x-auto"><table className="min-w-full text-left text-xs">
        <thead><tr className="text-slate-500"><th className="px-2 py-1">Column</th><th className="px-2">Type</th><th className="px-2">Nulls</th><th className="px-2">Distinct</th><th className="px-2">Min</th><th className="px-2">Max</th><th className="px-2">Avg</th></tr></thead>
        <tbody>{profile.data.columns.map((c) => (
          <tr key={c.name} className="border-t border-slate-100"><td className="px-2 py-1 font-medium">{c.name}</td><td className="px-2">{c.type}</td>
            <td className="px-2">{c.null_count}</td><td className="px-2">{c.distinct_count}</td>
            <td className="px-2">{c.min ?? ""}</td><td className="px-2">{c.max ?? ""}</td><td className="px-2">{c.avg !== undefined ? Number(c.avg).toFixed(2) : ""}</td></tr>))}</tbody>
      </table></div>
      <ResultsTable columns={preview.data.columns} rows={preview.data.rows} />
    </div>
  );
}

function Row({ ds, onChange }: { ds: Dataset; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState(ds.name);
  const [err, setErr] = useState<string | null>(null);
  const rename = async () => {
    if (name.trim() && name !== ds.name) {
      try { await api.renameDataset(ds.id, name.trim()); onChange(); } catch (e) { setErr(errorMessage(e)); }
    }
  };
  const remove = async () => {
    if (!confirm(`Delete "${ds.name}" and its queries, conversations and saved queries? This cannot be undone.`)) return;
    try { await api.deleteDataset(ds.id); onChange(); } catch (e) { setErr(errorMessage(e)); }
  };
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <input aria-label="Dataset name" value={name} onChange={(e) => setName(e.target.value)} onBlur={rename}
            className="w-64 max-w-full rounded border border-transparent px-1 font-medium hover:border-slate-300" />
          <p className="px-1 text-xs text-slate-500">{ds.original_filename} · {formatBytes(ds.file_size)} · {formatDate(ds.created_at)}
            {ds.row_count !== null && ` · ${ds.row_count.toLocaleString()} rows × ${ds.column_count} cols`}</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge>{ds.status}</Badge>
          {ds.status === "ready" && <>
            <Button variant="secondary" onClick={() => setOpen(!open)}>{open ? "Hide" : "Inspect"}</Button>
            <Link href={`/workspace?dataset=${ds.id}`} className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700">Query</Link></>}
          <Button variant="danger" aria-label={`Delete ${ds.name}`} onClick={remove}><Trash2 className="h-4 w-4" /></Button>
        </div>
      </div>
      {ds.error && <p className="mt-2 text-sm text-red-700">{ds.error}</p>}
      {err && <div className="mt-2"><ErrorBox message={err} /></div>}
      {open && <div className="mt-4"><Details id={ds.id} /></div>}
    </Card>
  );
}

export default function DatasetsPage() {
  const { data, error, loading, reload } = useApi(api.datasets);
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);

  const upload = async (file: File | undefined) => {
    if (!file) return;
    setUploading(true); setUploadErr(null);
    try { await api.upload(file); reload(); } catch (e) { setUploadErr(errorMessage(e)); reload(); }
    finally { setUploading(false); if (input.current) input.current.value = ""; }
  };

  return (
    <>
      <PageHeader title="Datasets">
        <Button onClick={() => input.current?.click()} disabled={uploading}><Upload className="h-4 w-4" />{uploading ? "Uploading…" : "Upload file"}</Button>
      </PageHeader>
      <input ref={input} type="file" accept=".csv,.xlsx,.parquet" className="sr-only" aria-label="Upload dataset file" onChange={(e) => upload(e.target.files?.[0])} />
      <div onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); upload(e.dataTransfer.files[0]); }}
        className="mb-6 rounded-lg border-2 border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
        {uploading ? <Spinner label="Uploading and ingesting" /> : "Drop a CSV, XLSX or Parquet file here"}
      </div>
      {uploadErr && <div className="mb-4"><ErrorBox message={uploadErr} /></div>}
      {loading && <Spinner />}
      {error && <ErrorBox message={error} />}
      {data && (data.length === 0 ? <Empty>No datasets yet. Upload one to get started.</Empty> :
        <div className="space-y-3">{data.map((d) => <Row key={d.id} ds={d} onChange={reload} />)}</div>)}
    </>
  );
}
