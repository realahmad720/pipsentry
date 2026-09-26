import { auth } from "@clerk/nextjs/server";

import { isClerkConfigured } from "./clerkConfig";

export * from "./types";

const API_BASE_URL = process.env.PIPSENTRY_API_URL ?? "http://localhost:8000";

async function getServerToken(): Promise<string | null> {
  // auth() throws if clerkMiddleware() never ran on this request, which is
  // exactly the case when Clerk isn't configured (see proxy.ts) — so this
  // function is the only thing allowed to call it.
  if (!isClerkConfigured) return null;
  const { getToken } = await auth();
  return getToken();
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getServerToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Pipsentry API ${path} failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
