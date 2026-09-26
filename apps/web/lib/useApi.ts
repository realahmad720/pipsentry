"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

import { isClerkConfigured } from "./clerkConfig";

// Client components can't use the server-only `auth()` helper (lib/api.ts),
// so this hook re-fetches a fresh session token per call instead.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type UseApi = () => { request: <T>(path: string, init?: RequestInit) => Promise<T> };

function buildRequest(getToken: () => Promise<string | null>) {
  return async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const token = await getToken();
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...init?.headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    if (!response.ok) {
      const detail = await response.text().catch(() => "");
      throw new Error(`Pipsentry API ${path} failed: ${response.status} ${detail}`);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    return response.json() as Promise<T>;
  };
}

const useApiWithClerk: UseApi = () => {
  const { getToken } = useAuth();
  const request = useCallback(buildRequest(getToken), [getToken]);
  return { request };
};

// Only reachable when Clerk isn't configured (see lib/clerkConfig.ts) — sends
// every request with no bearer token, so the API will 401 on anything past
// /health. That's expected for local review before real auth is wired up.
const useApiNoAuth: UseApi = () => {
  const request = useCallback(buildRequest(async () => null), []);
  return { request };
};

// Chosen once, at module load — isClerkConfigured is a build-time constant
// (inlined NEXT_PUBLIC_* env var), not something that changes per render, so
// this doesn't violate the rules of hooks the way a per-render branch would.
export const useApi: UseApi = isClerkConfigured ? useApiWithClerk : useApiNoAuth;
