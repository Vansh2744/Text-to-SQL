"use client";
import { Card, PageHeader } from "@/components/ui";
import { clerkEnabled } from "@/lib/auth";

export default function SettingsPage() {
  return (
    <>
      <PageHeader title="Settings" />
      <Card title="Connection">
        <dl className="space-y-2 text-sm">
          <div><dt className="text-slate-500">API URL</dt><dd>{process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}</dd></div>
          <div><dt className="text-slate-500">Authentication</dt>
            <dd>{clerkEnabled ? "Clerk" : "Local dev mode (no real authentication). Do not use in production."}</dd></div>
        </dl>
      </Card>
    </>
  );
}
