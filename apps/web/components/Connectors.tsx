"use client";

import { useCallback, useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Connector } from "@/lib/types";

const STATUS_STYLE: Record<Connector["status"], string> = {
  unverified: "bg-black/5 text-ink/50",
  healthy: "bg-bullish/10 text-bullish",
  unreachable: "bg-bearish/10 text-bearish",
  unauthorized: "bg-bearish/10 text-bearish",
};

export function Connectors() {
  const { request } = useApi();
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [endpointUrl, setEndpointUrl] = useState("");
  const [category, setCategory] = useState<Connector["category"]>("custom");
  const [credentials, setCredentials] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setConnectors(await request<Connector[]>("/connectors"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load connectors");
    } finally {
      setLoaded(true);
    }
  }, [request]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !endpointUrl.trim()) return;
    setSubmitting(true);
    try {
      const created = await request<Connector>("/connectors", {
        method: "POST",
        body: JSON.stringify({ name, endpoint_url: endpointUrl, category, credentials: credentials || undefined }),
      });
      setConnectors((prev) => [created, ...prev]);
      setName("");
      setEndpointUrl("");
      setCredentials("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to register connector");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleHealthCheck(id: string) {
    try {
      const updated = await request<Connector>(`/connectors/${id}/health-check`, { method: "POST" });
      setConnectors((prev) => prev.map((c) => (c.id === id ? updated : c)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Health check failed");
    }
  }

  async function handleDelete(id: string) {
    try {
      await request<void>(`/connectors/${id}`, { method: "DELETE" });
      setConnectors((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete connector");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-medium text-ink">Connectors</h1>
      <p className="text-sm text-ink/50">
        Register any MCP server; on registration we call its tool-discovery endpoint and record what
        it exposes (Section 20). Actually feeding a discovered tool&apos;s output into Agent 1/2&apos;s
        reasoning pass isn&apos;t wired in yet — see the API&apos;s connectors/mcp_bridge.py.
      </p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3 rounded-lg border border-black/10 bg-panel p-5">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-1 min-w-64 flex-col gap-1">
          <label className="text-xs text-ink/50">Endpoint URL</label>
          <input value={endpointUrl} onChange={(e) => setEndpointUrl(e.target.value)} placeholder="https://example.com/mcp" className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Category</label>
          <select value={category} onChange={(e) => setCategory(e.target.value as Connector["category"])} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent">
            <option value="market_data">Market data</option>
            <option value="broker_readonly">Broker (read-only)</option>
            <option value="news">News</option>
            <option value="custom">Custom</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Auth header (optional)</label>
          <input value={credentials} onChange={(e) => setCredentials(e.target.value)} placeholder="Bearer ..." className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <button type="submit" disabled={submitting} className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40">
          Register
        </button>
      </form>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : connectors.length === 0 ? (
          <p className="text-sm text-ink/50">No connectors registered yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Category</th>
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium">Tools</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {connectors.map((c) => (
                <tr key={c.id} className="border-t border-black/5 text-ink">
                  <td className="py-2">{c.name}</td>
                  <td className="py-2 text-ink/60">{c.category}</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[c.status]}`}>{c.status}</span>
                  </td>
                  <td className="py-2 text-ink/60">{c.discovered_tools.map((t) => t.name).join(", ") || "—"}</td>
                  <td className="py-2 text-right">
                    <button onClick={() => handleHealthCheck(c.id)} className="mr-3 text-xs text-ink/60 hover:text-ink hover:underline">
                      Recheck
                    </button>
                    <button onClick={() => handleDelete(c.id)} className="text-xs text-bearish hover:underline">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
