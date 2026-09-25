"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Watchlist as WatchlistEntry } from "@/lib/types";

const FORWARD_TEST_LABEL: Record<WatchlistEntry["forward_test_status"], string> = {
  not_started: "Not started",
  running: "Running",
  passed: "Passed",
  failed: "Failed",
};

export function Watchlist() {
  const { request } = useApi();
  const [entries, setEntries] = useState<WatchlistEntry[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("1h");
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setEntries(await request<WatchlistEntry[]>("/watchlists"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load watchlist");
    } finally {
      setLoaded(true);
    }
  }, [request]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim()) return;
    setSubmitting(true);
    try {
      const created = await request<WatchlistEntry>("/watchlists", {
        method: "POST",
        body: JSON.stringify({ symbol: symbol.trim().toUpperCase(), timeframe }),
      });
      setEntries((prev) => [created, ...prev]);
      setSymbol("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add symbol");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await request<void>(`/watchlists/${id}`, { method: "DELETE" });
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove symbol");
    }
  }

  async function handleStartForwardTest(id: string) {
    try {
      const updated = await request<WatchlistEntry>(`/watchlists/${id}/forward-test/start`, { method: "POST" });
      setEntries((prev) => prev.map((e) => (e.id === id ? updated : e)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start forward test");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-medium text-ink">Watchlist</h1>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="text-sm font-medium text-ink/70">Track a symbol</h2>
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col gap-1">
            <label className="text-xs text-ink/50">Symbol</label>
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              placeholder="EURUSD"
              className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-ink/50">Timeframe</label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent"
            >
              {["15min", "1h", "4h", "1day"].map((tf) => (
                <option key={tf} value={tf}>
                  {tf}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={submitting || !symbol.trim()}
            className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40"
          >
            Add
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Tracked symbols</h2>
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-ink/50">No symbols tracked yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Symbol</th>
                <th className="pb-2 font-medium">Timeframe</th>
                <th className="pb-2 font-medium">Forward test</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-t border-black/5 text-ink">
                  <td className="tabular py-2">
                    <Link href={`/chart?symbol=${entry.symbol}&timeframe=${entry.timeframe}`} className="hover:underline">
                      {entry.symbol}
                    </Link>
                  </td>
                  <td className="py-2 text-ink/60">{entry.timeframe}</td>
                  <td className="py-2 text-ink/60">{FORWARD_TEST_LABEL[entry.forward_test_status]}</td>
                  <td className="py-2 text-right">
                    {entry.forward_test_status === "not_started" && (
                      <button
                        onClick={() => handleStartForwardTest(entry.id)}
                        className="mr-3 text-xs text-ink/60 hover:text-ink hover:underline"
                      >
                        Start forward test
                      </button>
                    )}
                    <button onClick={() => handleDelete(entry.id)} className="text-xs text-bearish hover:underline">
                      Remove
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
