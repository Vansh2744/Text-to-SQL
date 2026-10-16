"use client";
import Link from "next/link";
import {
  Badge,
  Card,
  Empty,
  ErrorBox,
  PageHeader,
  Spinner,
} from "@/components/ui";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useApi } from "@/lib/useApi";

export default function DashboardPage() {
  const { data, error, loading } = useApi(api.dashboard);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox message={error ?? "Failed to load."} />;
  const link =
    "rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700";
  return (
    <>
      <PageHeader title="Dashboard">
        <div className="flex flex-wrap gap-2">
          <Link href="/datasets" className={link}>
            Upload dataset
          </Link>
          <Link href="/workspace" className={link}>
            Start a query
          </Link>
        </div>
      </PageHeader>
      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <Card>
          <p className="text-sm text-slate-500">Datasets</p>
          <p className="text-3xl font-semibold">{data.dataset_count}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Queries executed</p>
          <p className="text-3xl font-semibold">{data.query_count}</p>
        </Card>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card title="Recent queries">
          {data.recent_queries.length === 0 ? (
            <Empty>No queries yet.</Empty>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.recent_queries.map((q) => (
                <li
                  key={q.id}
                  className="flex items-start justify-between gap-2"
                >
                  <span
                    className="min-w-0 flex-1 truncate"
                    title={q.question ?? q.sql ?? ""}
                  >
                    {q.question ?? q.sql}
                  </span>
                  <Badge>{q.status}</Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Recent datasets">
          {data.recent_datasets.length === 0 ? (
            <Empty>No datasets yet.</Empty>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.recent_datasets.map((d) => (
                <li key={d.id} className="min-w-0">
                  <Link
                    className="block truncate text-indigo-700 hover:underline"
                    href={`/workspace?dataset=${d.id}`}
                    title={d.name}
                  >
                    {d.name}
                  </Link>
                  <span className="text-xs text-slate-500">
                    {formatDate(d.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card title="Saved queries" className="md:col-span-2 xl:col-span-1">
          {data.recent_saved_queries.length === 0 ? (
            <Empty>Nothing saved yet.</Empty>
          ) : (
            <ul className="space-y-3 text-sm">
              {data.recent_saved_queries.map((s) => (
                <li key={s.id} className="truncate" title={s.title}>
                  {s.title}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </>
  );
}
