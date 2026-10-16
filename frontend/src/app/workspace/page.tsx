"use client";
import { Bookmark, Copy, Play, Send } from "lucide-react";
import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AnalysisView } from "@/components/AnalysisView";
import { SqlEditor } from "@/components/SqlEditor";
import {
  Button,
  Card,
  Empty,
  ErrorBox,
  PageHeader,
  Spinner,
} from "@/components/ui";
import { api, errorMessage } from "@/lib/api";
import { suggestQuestions } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import type { Analysis, Column } from "@/types";
import { SaveQueryDialog } from "@/components/SaveQueryDialog";

function Workspace() {
  const params = useSearchParams();
  const router = useRouter();
  const datasets = useApi(api.datasets);
  const ready = (datasets.data ?? []).filter((d) => d.status === "ready");
  const datasetId = params.get("dataset") ?? "";
  const schema = useApi(
    () => (datasetId ? api.schema(datasetId) : Promise.resolve(null)),
    [datasetId],
  );

  const [question, setQuestion] = useState("");
  const [sql, setSql] = useState("");
  const [result, setResult] = useState<Analysis | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [busy, setBusy] = useState<"" | "ask" | "run">("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saveOpen, setSaveOpen] = useState(false);

  useEffect(() => {
    setResult(null);
    setSql("");
    setConversationId(null);
    setError(null);
  }, [datasetId]);

  const ask = async (q = question) => {
    if (!q.trim() || !datasetId) return;
    setBusy("ask");
    setError(null);
    setNotice(null);
    try {
      let cid = conversationId;
      if (!cid) {
        cid = (await api.createConversation(datasetId)).id;
        setConversationId(cid);
      }
      const r = await api.analyze(datasetId, q.trim(), cid);
      setResult(r);
      setSql(r.sql);
      setQuestion("");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy("");
    }
  };

  const runSql = async () => {
    setBusy("run");
    setError(null);
    setNotice(null);
    try {
      const r = await api.execute(datasetId, sql);
      setResult(r);
      setSql(r.sql);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy("");
    }
  };

  const save = async (title: string, description: string) => {
    await api.saveQuery({
      dataset_id: datasetId,
      title,
      description: description || undefined,
      sql,
    });
    setSaveOpen(false);
    setNotice("Saved.");
  };

  const cols: Column[] = schema.data?.columns ?? [];
  return (
    <>
      <PageHeader title="Query Workspace">
        <select
          aria-label="Dataset"
          value={datasetId}
          onChange={(e) => router.push(`/workspace?dataset=${e.target.value}`)}
          className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
        >
          <option value="">Select a dataset…</option>
          {ready.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </PageHeader>
      {datasets.loading ? (
        <Spinner />
      ) : !datasetId ? (
        <Empty>
          {ready.length === 0
            ? "Upload a dataset first, then come back to ask questions."
            : "Choose a dataset to start."}
        </Empty>
      ) : (
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card title="Schema" className="h-fit">
            {schema.loading ? (
              <Spinner />
            ) : (
              <ul className="space-y-1 text-sm">
                {cols.map((c) => (
                  <li key={c.name} className="flex justify-between gap-2">
                    <span className="truncate font-medium">{c.name}</span>
                    <span className="text-xs text-slate-500">{c.type}</span>
                  </li>
                ))}
              </ul>
            )}
          </Card>
          <div className="min-w-0 space-y-4">
            <Card>
              <label htmlFor="q" className="mb-1 block text-sm font-medium">
                Ask a question
              </label>
              <div className="flex gap-2">
                <input
                  id="q"
                  value={question}
                  maxLength={1000}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && ask()}
                  placeholder="Which product generated the most revenue?"
                  className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
                />
                <Button
                  onClick={() => ask()}
                  disabled={busy !== "" || !question.trim()}
                >
                  <Send className="h-4 w-4" />
                  Ask
                </Button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {suggestQuestions(cols).map((s) => (
                  <button
                    key={s}
                    onClick={() => ask(s)}
                    disabled={busy !== ""}
                    className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700 hover:bg-slate-200 disabled:opacity-50"
                  >
                    {s}
                  </button>
                ))}
              </div>
              {conversationId && (
                <button
                  onClick={() => {
                    setConversationId(null);
                    setResult(null);
                    setSql("");
                  }}
                  className="mt-3 text-xs text-indigo-700 hover:underline"
                >
                  Start a new conversation
                </button>
              )}
            </Card>
            {busy === "ask" && <Spinner label="Generating and running SQL" />}
            {error && <ErrorBox message={error} />}
            {notice && (
              <p role="status" className="text-sm text-emerald-700">
                {notice}
              </p>
            )}
            {(sql || result) && (
              <Card
                title="SQL"
                actions={
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => navigator.clipboard.writeText(sql)}
                    >
                      <Copy className="h-4 w-4" />
                      Copy
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setSaveOpen(true)}
                      disabled={!sql}
                    >
                      <Bookmark className="h-4 w-4" />
                      Save
                    </Button>
                    <Button
                      onClick={runSql}
                      disabled={busy !== "" || !sql.trim()}
                    >
                      <Play className="h-4 w-4" />
                      {busy === "run" ? "Running…" : "Run SQL"}
                    </Button>
                  </div>
                }
              >
                <SqlEditor value={sql} onChange={setSql} />
                <p className="mt-2 text-xs text-slate-500">
                  The server re-validates all SQL. Only a single read-only
                  SELECT on this dataset&apos;s table <code>data</code> is
                  allowed.
                </p>
              </Card>
            )}
            {result && <AnalysisView result={result} />}
          </div>
        </div>
      )}
      <SaveQueryDialog
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        onSave={save}
      />
    </>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<Spinner />}>
      <Workspace />
    </Suspense>
  );
}
