import { auth } from "@clerk/nextjs/server";

export * from "./types";

const API_BASE_URL = process.env.PIPSENTRY_API_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const { getToken } = await auth();
  const token = await getToken();

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...init?.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Pipsentry API ${path} failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
