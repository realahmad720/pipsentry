"use client";

import { useEffect, useMemo, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Advisory } from "@/lib/types";

// Matches the ATR multiples app/backtest/strategy.py and app/delivery/forward_test.py
// use for TP1/TP2, so advisory outcomes translate to the same R-multiple unit
// the Backtest page reports in.
const OUTCOME_R: Record<string, number> = { tp1: 2.0, tp2: 3.0, sl: -1.0 };

export function PerformanceAnalytics() {
  const { request } = useApi();
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<Advisory[]>("/advisories")
      .then(setAdvisories)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load advisory history"))
      .finally(() => setLoaded(true));
  }, [request]);

  const stats = useMemo(() => {
    const resolved = advisories.filter((a) => a.outcome !== "open").slice().reverse();
    const rMultiples = resolved.map((a) => OUTCOME_R[a.outcome] ?? 0);
    const wins = rMultiples.filter((r) => r > 0).length;

    let equity = 0;
    let peak = 0;
    let maxDrawdown = 0;
    const curve: number[] = [];
    for (const r of rMultiples) {
      equity += r;
      peak = Math.max(peak, equity);
      maxDrawdown = Math.max(maxDrawdown, peak - equity);
      curve.push(equity);
    }

    const bySymbol = new Map<string, { count: number; totalR: number }>();
    resolved.forEach((a, i) => {
      const entry = bySymbol.get(a.symbol) ?? { count: 0, totalR: 0 };
      entry.count += 1;
      entry.totalR += rMultiples[i];
      bySymbol.set(a.symbol, entry);
    });

    return {
      resolvedCount: resolved.length,
      winRate: resolved.length ? wins / resolved.length : 0,
      avgR: resolved.length ? rMultiples.reduce((a, b) => a + b, 0) / resolved.length : 0,
      maxDrawdown,
      curve,
      bySymbol: Array.from(bySymbol.entries()),
    };
  }, [advisories]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Performance analytics</h1>
      <p className="text-sm text-ink/50">Computed from your resolved advisory outcomes (Section 19 page 17).</p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      {!loaded ? (
        <p className="text-sm text-ink/50">Loading…</p>
      ) : stats.resolvedCount === 0 ? (
        <p className="text-sm text-ink/50">No resolved advisories yet.</p>
      ) : (
        <>
          <section className="tabular grid grid-cols-2 gap-4 rounded-lg border border-black/10 bg-panel p-5 text-sm sm:grid-cols-4">
            <div><div className="text-ink/50">Resolved advisories</div>{stats.resolvedCount}</div>
            <div><div className="text-ink/50">Win rate</div>{(stats.winRate * 100).toFixed(0)}%</div>
            <div><div className="text-ink/50">Avg R-multiple</div>{stats.avgR.toFixed(2)}R</div>
            <div><div className="text-ink/50">Max drawdown</div>{stats.maxDrawdown.toFixed(2)}R</div>
          </section>

          <section className="rounded-lg border border-black/10 bg-panel p-5">
            <h2 className="mb-3 text-sm font-medium text-ink/70">Equity curve (cumulative R)</h2>
            <svg viewBox="0 0 600 160" className="w-full" preserveAspectRatio="none">
              {(() => {
                const max = Math.max(1, ...stats.curve.map(Math.abs));
                const points = stats.curve.map((v, i) => {
                  const x = (i / Math.max(1, stats.curve.length - 1)) * 600;
                  const y = 80 - (v / max) * 70;
                  return `${x},${y}`;
                });
                return (
                  <>
                    <line x1={0} x2={600} y1={80} y2={80} stroke="#10131C" strokeOpacity={0.1} />
                    <polyline points={points.join(" ")} fill="none" stroke="#00F5D4" strokeWidth={2} />
                  </>
                );
              })()}
            </svg>
          </section>

          <section className="rounded-lg border border-black/10 bg-panel p-5">
            <h2 className="mb-3 text-sm font-medium text-ink/70">By symbol</h2>
            <table className="tabular w-full text-sm">
              <thead>
                <tr className="text-left text-ink/50">
                  <th className="pb-2 font-medium">Symbol</th>
                  <th className="pb-2 font-medium">Trades</th>
                  <th className="pb-2 font-medium">Total R</th>
                </tr>
              </thead>
              <tbody>
                {stats.bySymbol.map(([symbol, s]) => (
                  <tr key={symbol} className="border-t border-black/5 text-ink">
                    <td className="py-2">{symbol}</td>
                    <td className="py-2">{s.count}</td>
                    <td className={`py-2 ${s.totalR >= 0 ? "text-bullish" : "text-bearish"}`}>{s.totalR.toFixed(2)}R</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  );
}
