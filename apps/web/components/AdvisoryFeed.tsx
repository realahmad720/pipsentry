"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Advisory } from "@/lib/types";

const OUTCOME_STYLE: Record<Advisory["outcome"], string> = {
  open: "bg-accent/15 text-ink/70",
  tp1: "bg-bullish/10 text-bullish",
  tp2: "bg-bullish/10 text-bullish",
  sl: "bg-bearish/10 text-bearish",
  expired: "bg-black/5 text-ink/40",
};

export function AdvisoryFeed() {
  const { request } = useApi();
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symbolFilter, setSymbolFilter] = useState("");

  const refresh = useCallback(async () => {
    try {
      setAdvisories(await request<Advisory[]>("/advisories"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load advisories");
    } finally {
      setLoaded(true);
    }
  }, [request]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const filtered = symbolFilter
    ? advisories.filter((a) => a.symbol.includes(symbolFilter.toUpperCase()))
    : advisories;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">Advisory feed</h1>
        <input
          value={symbolFilter}
          onChange={(e) => setSymbolFilter(e.target.value)}
          placeholder="Filter by symbol"
          className="rounded-md border border-black/10 bg-base px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
        />
      </div>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : filtered.length === 0 ? (
          <p className="text-sm text-ink/50">No advisories yet — evaluate a setup from the Chart Workspace.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Symbol</th>
                <th className="pb-2 font-medium">Timeframe</th>
                <th className="pb-2 font-medium">Action</th>
                <th className="tabular pb-2 font-medium">Confidence</th>
                <th className="pb-2 font-medium">Outcome</th>
                <th className="pb-2 font-medium">Delivered</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id} className="border-t border-black/5 text-ink">
                  <td className="py-2">
                    <Link href={`/advisories/${a.id}`} className="hover:underline">
                      {a.symbol}
                    </Link>
                  </td>
                  <td className="py-2 text-ink/60">{a.timeframe}</td>
                  <td className={`py-2 ${a.action.includes("SELL") ? "text-bearish" : a.action.includes("BUY") ? "text-bullish" : "text-ink/60"}`}>
                    {a.action}
                  </td>
                  <td className="tabular py-2">{(a.confidence_score * 100).toFixed(0)}%</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${OUTCOME_STYLE[a.outcome]}`}>
                      {a.outcome}
                    </span>
                  </td>
                  <td className="tabular py-2 text-ink/50">{new Date(a.delivered_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
