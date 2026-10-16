"use client";
import dynamic from "next/dynamic";

const Monaco = dynamic(() => import("@monaco-editor/react"), {
  ssr: false, loading: () => <div className="h-40 animate-pulse rounded bg-slate-100" />,
});

export function SqlEditor({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="overflow-hidden rounded-md border border-slate-200" aria-label="SQL editor">
      <Monaco height="160px" language="sql" value={value} onChange={(v) => onChange(v ?? "")}
        options={{ minimap: { enabled: false }, fontSize: 13, scrollBeyondLastLine: false, wordWrap: "on" }} />
    </div>
  );
}
