"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

// Client components can't use the server-only `auth()` helper (lib/api.ts),
// so this hook re-fetches a fresh session token per call instead.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useApi() {
  const { getToken } = useAuth();

  const request = useCallback(
    async <T>(path: string, init?: RequestInit): Promise<T> => {
      const token = await getToken();
      const response = await fetch(`${API_BASE_URL}${path}`, {
        ...init,
        headers: {
          ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
          ...init?.headers,
          Authorization: `Bearer ${token}`,
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
    },
    [getToken],
  );

  return { request };
}
