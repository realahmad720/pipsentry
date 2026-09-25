"use client";

import { useState } from "react";

import { useApi } from "@/lib/useApi";
import type { BacktestResult } from "@/lib/types";

function defaultDates(): { start: string; end: string } {
  const end = new Date();
  const start = new Date();
  start.setMonth(start.getMonth() - 6);
  return { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) };
}

export function BacktestRunner() {
  const { request } = useApi();
  const { start, end } = defaultDates();
  const [symbol, setSymbol] = useState("EURUSD");
  const [timeframe, setTimeframe] = useState("1h");
  const [startDate, setStartDate] = useState(start);
  const [endDate, setEndDate] = useState(end);
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);
    try {
      const data = await request<BacktestResult>("/backtest/run", {
        method: "POST",
        body: JSON.stringify({ symbol: symbol.toUpperCase(), timeframe, start_date: startDate, end_date: endDate }),
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Backtest failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Backtest & validation</h1>
      <p className="text-sm text-ink/50">
        Replays a deterministic SMA-cross/ATR reference strategy candle-by-candle over the window below —
        not the full four-agent LLM pipeline, which would mean thousands of paid LLM calls per run.
        See the API&apos;s backtest/strategy.py for why.
      </p>

      <form onSubmit={handleRun} className="flex flex-wrap items-end gap-3 rounded-lg border border-black/10 bg-panel p-5">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Symbol</label>
          <input value={symbol} onChange={(e) => setSymbol(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Timeframe</label>
          <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent">
            {["15min", "1h", "4h", "1day"].map((tf) => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">Start date</label>
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-ink/50">End date</label>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="rounded-md border border-black/10 bg-base px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
        </div>
        <button type="submit" disabled={running} className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40">
          {running ? "Running…" : "Run backtest"}
        </button>
      </form>

      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      {result && (
        <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
          <div className={`rounded-md px-3 py-2 text-sm ${result.passes_gate ? "bg-bullish/10 text-bullish" : "bg-bearish/10 text-bearish"}`}>
            {result.gate_message}
          </div>
          <div className="tabular grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div><div className="text-ink/50">Trades</div>{result.trades.length}</div>
            <div><div className="text-ink/50">Win rate</div>{(result.win_rate * 100).toFixed(0)}%</div>
            <div><div className="text-ink/50">Avg R-multiple</div>{result.avg_r_multiple.toFixed(2)}R</div>
            <div><div className="text-ink/50">Max drawdown</div>{result.max_drawdown_r.toFixed(2)}R</div>
          </div>
        </section>
      )}
    </div>
  );
}
