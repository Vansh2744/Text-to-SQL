"use client";
import { UserButton } from "@clerk/nextjs";
import {
  BarChart3,
  Bookmark,
  Database,
  History,
  LayoutDashboard,
  Menu,
  Terminal,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { clerkEnabled } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/workspace", label: "Query Workspace", icon: Terminal },
  { href: "/history", label: "Query History", icon: History },
  { href: "/saved", label: "Saved Queries", icon: Bookmark },
];

function Brand() {
  return (
    <div className="flex items-center gap-2 font-semibold">
      <BarChart3 className="h-5 w-5 text-indigo-600" />
      QueryPilot AI
    </div>
  );
}

function NavLinks({
  path,
  onNavigate,
}: {
  path: string;
  onNavigate?: () => void;
}) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-1 px-2">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-2 whitespace-nowrap rounded-md px-3 py-2 text-sm ${
              active
                ? "bg-indigo-50 font-medium text-indigo-700"
                : "text-slate-600 hover:bg-slate-100"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [path]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [open]);

  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <aside className="hidden border-r border-slate-200 bg-white md:block md:w-56">
        <div className="px-4 py-4">
          <Brand />
        </div>
        <NavLinks path={path} />
        {clerkEnabled && (
          <div className="px-4 py-4">
            <UserButton />
          </div>
        )}
      </aside>

      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <Brand />
        <div className="flex items-center gap-3">
          {clerkEnabled && <UserButton />}
          <button
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            aria-expanded={open}
            aria-controls="mobile-nav"
            className="rounded-md p-2 text-slate-700 hover:bg-slate-100"
          >
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div
        className={`fixed inset-0 z-40 md:hidden ${open ? "" : "pointer-events-none"}`}
        aria-hidden={!open}
      >
        <div
          onClick={() => setOpen(false)}
          className={`absolute inset-0 bg-slate-900/40 transition-opacity ${open ? "opacity-100" : "opacity-0"}`}
        />
        <div
          id="mobile-nav"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation menu"
          className={`absolute left-0 top-0 h-full w-64 max-w-[80%] overflow-y-auto bg-white shadow-xl transition-transform duration-200 ${
            open ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="flex items-center justify-between px-4 py-4">
            <Brand />
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close menu"
              className="rounded-md p-1 text-slate-500 hover:bg-slate-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <NavLinks path={path} onNavigate={() => setOpen(false)} />
        </div>
      </div>

      <main className="min-w-0 flex-1 p-4 md:p-8">{children}</main>
    </div>
  );
}
