import type {
  Analysis, Column, Conversation, Dashboard, Dataset, HistoryItem, ProfileColumn, SavedQuery,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PREFIX = `${BASE}/api/v1`;

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}

let getToken: (() => Promise<string | null>) | null = null;
let devUser: string | null = null;

export function configureAuth(opts: { getToken?: () => Promise<string | null>; devUser?: string }) {
  getToken = opts.getToken ?? null;
  devUser = opts.devUser ?? null;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData) && init.body) headers.set("Content-Type", "application/json");
  if (getToken) {
    const t = await getToken();
    if (t) headers.set("Authorization", `Bearer ${t}`);
  } else if (devUser) headers.set("X-Dev-User", devUser);

  let res: Response;
  try {
    res = await fetch(`${PREFIX}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network", "Cannot reach the server. Is the backend running?");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.error?.code ?? "error", body?.error?.message ?? res.statusText);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const json = (method: string, body: unknown): RequestInit => ({ method, body: JSON.stringify(body) });

const FRIENDLY: Record<string, string> = {
  unsupported_file_type: "Unsupported file type. Use CSV, XLSX or Parquet.",
  invalid_file: "That file looks invalid or corrupted.",
  file_too_large: "File is too large.",
  unauthorized: "Your session expired. Please sign in again.",
  not_found: "That item no longer exists or you don't have access.",
  llm_unavailable: "The AI provider is unavailable right now. Try again in a moment.",
  llm_not_configured: "The AI provider is not configured on the server.",
  rate_limited: "Too many requests. Please slow down.",
  sql_validation_failed: "That SQL isn't allowed: ",
  query_timeout: "The query timed out. Try a simpler question.",
  dataset_not_ready: "This dataset isn't ready yet.",
  dataset_files_missing: "This dataset's data is no longer on the server. Delete it and upload the file again.",
};

export function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    const base = FRIENDLY[e.code];
    if (!base) return e.message;
    return e.code === "sql_validation_failed" ? base + e.message : base;
  }
  return "Something went wrong.";
}

export const api = {
  dashboard: () => request<Dashboard>("/dashboard"),
  datasets: () => request<Dataset[]>("/datasets"),
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return request<Dataset>("/datasets/upload", { method: "POST", body: fd });
  },
  schema: (id: string) => request<{ table: string; columns: Column[] }>(`/datasets/${id}/schema`),
  preview: (id: string) => request<{ columns: Column[]; rows: unknown[][] }>(`/datasets/${id}/preview?rows=10`),
  profile: (id: string) => request<{ columns: ProfileColumn[] }>(`/datasets/${id}/profile`),
  renameDataset: (id: string, name: string) => request<Dataset>(`/datasets/${id}`, json("PATCH", { name })),
  deleteDataset: (id: string) => request<void>(`/datasets/${id}`, { method: "DELETE" }),
  analyze: (dataset_id: string, question: string, conversation_id?: string) =>
    request<Analysis>("/queries/analyze", json("POST", { dataset_id, question, conversation_id })),
  execute: (dataset_id: string, sql: string) =>
    request<Analysis>("/queries/execute", json("POST", { dataset_id, sql })),
  history: () => request<HistoryItem[]>("/queries/history?limit=100"),
  rerun: (id: string) => request<Analysis>(`/queries/${id}/rerun`, { method: "POST" }),
  createConversation: (dataset_id: string) =>
    request<Conversation>("/conversations", json("POST", { dataset_id })),
  saved: () => request<SavedQuery[]>("/saved-queries"),
  saveQuery: (b: { dataset_id: string; title: string; description?: string; sql: string }) =>
    request<SavedQuery>("/saved-queries", json("POST", b)),
  runSaved: (id: string) => request<Analysis>(`/saved-queries/${id}/run`, { method: "POST" }),
  deleteSaved: (id: string) => request<void>(`/saved-queries/${id}`, { method: "DELETE" }),
};
