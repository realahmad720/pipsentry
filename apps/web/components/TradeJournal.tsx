"use client";

import { useCallback, useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { TradeJournalEntry } from "@/lib/types";

export function TradeJournal() {
  const { request } = useApi();
  const [entries, setEntries] = useState<TradeJournalEntry[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [symbol, setSymbol] = useState("");
  const [direction, setDirection] = useState<"long" | "short">("long");
  const [entryPrice, setEntryPrice] = useState("");
  const [size, setSize] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setEntries(await request<TradeJournalEntry[]>("/trade-journal"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trade journal");
    } finally {
      setLoaded(true);
    }
  }, [request]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!symbol.trim() || !entryPrice || !size) return;
    setSubmitting(true);
    try {
      const created = await request<TradeJournalEntry>("/trade-journal", {
        method: "POST",
        body: JSON.stringify({
          symbol: symbol.trim().toUpperCase(),
          direction,
          entry_price: Number(entryPrice),
          size: Number(size),
        }),
      });
      setEntries((prev) => [created, ...prev]);
      setSymbol("");
      setEntryPrice("");
      setSize("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to log trade");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await request<void>(`/trade-journal/${id}`, { method: "DELETE" });
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete entry");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-medium text-ink">Trade journal</h1>
      <p className="text-sm text-ink/50">A manual log of trades you actually took — separate from AI advisories.</p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3 rounded-lg border border-black/10 bg-panel p-5">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Symbol</label>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Direction</label>
          <select value={direction} onChange={(e) => setDirection(e.target.value as "long" | "short")} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent">
            <option value="long">Long</option>
            <option value="short">Short</option>
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Entry price</label>
          <input type="number" step="any" value={entryPrice} onChange={(e) => setEntryPrice(e.target.value)} className="tabular rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Size (lots)</label>
          <input type="number" step="any" value={size} onChange={(e) => setSize(e.target.value)} className="tabular rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <button type="submit" disabled={submitting} className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40">
          Log trade
        </button>
      </form>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : entries.length === 0 ? (
          <p className="text-sm text-ink/50">No trades logged yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Symbol</th>
                <th className="pb-2 font-medium">Direction</th>
                <th className="tabular pb-2 font-medium">Entry</th>
                <th className="tabular pb-2 font-medium">Size</th>
                <th className="tabular pb-2 font-medium">P&amp;L</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((e) => (
                <tr key={e.id} className="border-t border-black/5 text-ink">
                  <td className="py-2">{e.symbol}</td>
                  <td className="py-2 text-ink/60">{e.direction}</td>
                  <td className="tabular py-2">{e.entry_price}</td>
                  <td className="tabular py-2">{e.size}</td>
                  <td className={`tabular py-2 ${e.pnl && e.pnl > 0 ? "text-bullish" : e.pnl && e.pnl < 0 ? "text-bearish" : "text-ink/40"}`}>
                    {e.pnl ?? "open"}
                  </td>
                  <td className="py-2 text-right">
                    <button onClick={() => handleDelete(e.id)} className="text-xs text-bearish hover:underline">
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
