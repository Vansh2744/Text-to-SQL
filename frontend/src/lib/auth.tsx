"use client";
import { ClerkProvider, SignIn, useAuth } from "@clerk/nextjs";
import { Loader2 } from "lucide-react";
import { configureAuth } from "./api";

const CLERK_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
export const clerkEnabled = Boolean(CLERK_KEY);

function ClerkGate({ children }: { children: React.ReactNode }) {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  configureAuth({ getToken: () => getToken() });
  if (!isLoaded) return <div className="grid h-screen place-items-center"><Loader2 className="animate-spin" /></div>;
  if (!isSignedIn) return <div className="grid h-screen place-items-center"><SignIn routing="hash" /></div>;
  return <>{children}</>;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  if (clerkEnabled) {
    return <ClerkProvider publishableKey={CLERK_KEY}><ClerkGate>{children}</ClerkGate></ClerkProvider>;
  }
  configureAuth({ devUser: process.env.NEXT_PUBLIC_DEV_USER ?? "dev-user" });
  return <>{children}</>;
}
