"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Advisory } from "@/lib/types";

const AGENT_LABELS = [
  { key: "macro_fundamental", title: "Agent 1 · Macro & News" },
  { key: "technical", title: "Agent 2 · Technical & Price Action" },
  { key: "strategy_match", title: "Agent 3 · Strategy & RAG Retriever" },
] as const;

export function AdvisoryDetail({ id }: { id: string }) {
  const { request } = useApi();
  const [advisory, setAdvisory] = useState<Advisory | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<Advisory>(`/advisories/${id}`)
      .then(setAdvisory)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load advisory"));
  }, [id, request]);

  if (error) return <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>;
  if (!advisory) return <p className="text-sm text-ink/50">Loading…</p>;

  const payload = advisory.payload_json;
  const zones = payload.execution_zones;

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">
          {advisory.symbol} · {advisory.timeframe}
        </h1>
        <span className={`rounded-full px-3 py-1 text-sm font-medium ${payload.bias === "BULLISH" ? "bg-bullish/10 text-bullish" : payload.bias === "BEARISH" ? "bg-bearish/10 text-bearish" : "bg-black/5 text-ink/60"}`}>
          {advisory.action} · {(advisory.confidence_score * 100).toFixed(0)}%
        </span>
      </div>

      {payload.conflict_status !== "NONE" && (
        <p className="rounded-md bg-accent/10 px-3 py-2 text-sm text-ink">
          Conflict status: {payload.conflict_status} — position size capped at{" "}
          {(payload.position_size_multiplier * 100).toFixed(0)}% of normal risk unit.
        </p>
      )}

      {zones && (
        <section className="rounded-lg border border-black/10 bg-panel p-5">
          <h2 className="mb-3 text-sm font-medium text-ink/70">Execution zones</h2>
          <div className="tabular grid grid-cols-2 gap-3 text-sm text-ink sm:grid-cols-5">
            <div>
              <div className="text-ink/50">Entry</div>
              {zones.suggested_entry}
            </div>
            <div>
              <div className="text-ink/50">Stop loss</div>
              {zones.stop_loss}
            </div>
            <div>
              <div className="text-ink/50">TP1</div>
              {zones.take_profit_1}
            </div>
            <div>
              <div className="text-ink/50">TP2</div>
              {zones.take_profit_2}
            </div>
            <div>
              <div className="text-ink/50">R:R</div>
              {zones.risk_reward_ratio}
            </div>
          </div>
        </section>
      )}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Reasoning trail</h2>
        <div className="flex flex-col gap-4">
          {AGENT_LABELS.map(({ key, title }) => (
            <div key={key}>
              <div className="text-xs font-medium text-ink/50">{title}</div>
              <p className="text-sm text-ink">{payload.rationale[key] || "—"}</p>
            </div>
          ))}
        </div>
      </section>

      {payload.warnings.length > 0 && (
        <section className="rounded-lg border border-black/10 bg-panel p-5">
          <h2 className="mb-3 text-sm font-medium text-ink/70">Warnings</h2>
          <ul className="flex flex-col gap-1 text-sm text-ink">
            {payload.warnings.map((w, i) => (
              <li key={i}>⚠ {w}</li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-xs text-ink/40">{payload.disclaimer}</p>
    </div>
  );
}
