"use client";
import { useMemo, useState } from "react";
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart,
  ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import { isNumericType } from "@/lib/format";
import type { ChartType, Column, Visualization } from "@/types";

const COLORS = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#14b8a6", "#f97316"];
const MAX_POINTS = 200;

export function allowedTypes(viz: Visualization, columns: Column[], nRows: number): ChartType[] {
  const xNumeric = isNumericType(columns.find((c) => c.name === viz.x)?.type ?? "");
  const t: ChartType[] = ["bar", "line", "area"];
  if (viz.y.length === 1 && nRows <= 12) t.push("pie");
  if (xNumeric) t.push("scatter");
  return t;
}

export function ResultChart({ viz, columns, rows }: { viz: Visualization; columns: Column[]; rows: unknown[][] }) {
  const [type, setType] = useState<ChartType>(viz.type);
  const xi = columns.findIndex((c) => c.name === viz.x);
  const yis = viz.y.map((n) => columns.findIndex((c) => c.name === n));
  const valid = xi >= 0 && yis.every((i) => i >= 0) && rows.length > 0 && rows.length <= MAX_POINTS;

  const data = useMemo(() => rows.map((r) => {
    const o: Record<string, unknown> = { [viz.x]: r[xi] };
    viz.y.forEach((n, k) => { o[n] = Number(r[yis[k] ?? 0]); });
    return o;
  }), [rows, viz]);

  if (!valid) return <p className="text-sm text-slate-500">This result can&apos;t be charted (too many points or missing fields).</p>;
  const types = allowedTypes(viz, columns, rows.length);
  const axes = <><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey={viz.x} /><YAxis /><Tooltip /><Legend /></>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">{viz.title ?? `${viz.y.join(", ")} by ${viz.x}`}</h3>
        <div role="group" aria-label="Chart type" className="flex gap-1">
          {types.map((t) => (
            <button key={t} aria-pressed={t === type} onClick={() => setType(t)}
              className={`rounded px-2 py-1 text-xs capitalize ${t === type ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-700"}`}>{t}</button>
          ))}
        </div>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer>
          {type === "bar" ? (
            <BarChart data={data}>{axes}{viz.y.map((n, i) => <Bar key={n} dataKey={n} fill={COLORS[i % COLORS.length]} />)}</BarChart>
          ) : type === "line" ? (
            <LineChart data={data}>{axes}{viz.y.map((n, i) => <Line key={n} dataKey={n} stroke={COLORS[i % COLORS.length]} dot={false} />)}</LineChart>
          ) : type === "area" ? (
            <AreaChart data={data}>{axes}{viz.y.map((n, i) => <Area key={n} dataKey={n} stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]} fillOpacity={0.2} />)}</AreaChart>
          ) : type === "pie" ? (
            <PieChart><Tooltip /><Legend /><Pie data={data} dataKey={viz.y[0] ?? ""} nameKey={viz.x} outerRadius={100}>{data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie></PieChart>
          ) : (
            <ScatterChart><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey={viz.x} type="number" name={viz.x} /><YAxis dataKey={viz.y[0]} type="number" name={viz.y[0]} /><Tooltip /><Scatter data={data} fill={COLORS[0]} /></ScatterChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
