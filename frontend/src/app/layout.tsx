import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { Shell } from "@/components/Shell";

export const metadata: Metadata = { title: "QueryPilot AI", description: "Ask questions about your data in plain English" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><body><AuthProvider><Shell>{children}</Shell></AuthProvider></body></html>
  );
}
