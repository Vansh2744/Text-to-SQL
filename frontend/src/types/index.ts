export interface Column { name: string; type: string }

export interface Dataset {
  id: string; name: string; original_filename: string; file_format: string; file_size: number;
  status: "processing" | "ready" | "failed"; error: string | null;
  row_count: number | null; column_count: number | null; created_at: string; updated_at: string;
}

export interface Visualization { type: ChartType; x: string; y: string[]; title?: string }
export type ChartType = "bar" | "line" | "pie" | "area" | "scatter";

export interface Analysis {
  query_id: string; question: string | null; sql: string; columns: Column[]; rows: unknown[][];
  row_count: number; truncated: boolean; duration_ms: number; visualization: Visualization | null;
  explanation: string | null; attempts: number; conversation_id: string | null;
}

export interface HistoryItem {
  id: string; dataset_id: string; conversation_id: string | null; question: string | null;
  sql: string | null; status: string; error_category: string | null; duration_ms: number | null;
  row_count: number | null; created_at: string;
}

export interface SavedQuery {
  id: string; dataset_id: string; title: string; description: string | null; sql: string;
  created_at: string; updated_at: string;
}

export interface Conversation { id: string; dataset_id: string; title: string }

export interface ProfileColumn extends Column {
  null_count: number; distinct_count: number; min?: number; max?: number; avg?: number;
}

export interface Dashboard {
  dataset_count: number; query_count: number; recent_queries: HistoryItem[];
  recent_datasets: Dataset[]; recent_saved_queries: SavedQuery[];
}
