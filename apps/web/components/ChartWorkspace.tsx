"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Advisory, Candle } from "@/lib/types";

const AGENT_STEPS = ["Macro & News", "Technical & Price Action", "Strategy & RAG Retriever", "Risk & Synthesis Auditor"];

function Candlesticks({ candles }: { candles: Candle[] }) {
  if (candles.length === 0) return null;
  const width = 900;
  const height = 320;
  const padding = 20;
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const range = max - min || 1;
  const slot = (width - padding * 2) / candles.length;

  const y = (price: number) => padding + (1 - (price - min) / range) * (height - padding * 2);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full" preserveAspectRatio="none">
      {candles.map((c, i) => {
        const x = padding + i * slot + slot / 2;
        const bullish = c.close >= c.open;
        const bodyTop = y(Math.max(c.open, c.close));
        const bodyBottom = y(Math.min(c.open, c.close));
        return (
          <g key={c.time}>
            <line x1={x} x2={x} y1={y(c.high)} y2={y(c.low)} stroke={bullish ? "#0F9B8E" : "#FF3B5C"} strokeWidth={1} />
            <rect
              x={x - slot * 0.3}
              y={bodyTop}
              width={slot * 0.6}
              height={Math.max(bodyBottom - bodyTop, 1)}
              fill={bullish ? "#0F9B8E" : "#FF3B5C"}
            />
          </g>
        );
      })}
    </svg>
  );
}

export function ChartWorkspace() {
  const { request } = useApi();
  const router = useRouter();
  const searchParams = useSearchParams();
  const symbol = (searchParams.get("symbol") || "EURUSD").toUpperCase();
  const timeframe = searchParams.get("timeframe") || "1h";

  const [candles, setCandles] = useState<Candle[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [evaluating, setEvaluating] = useState(false);
  const [activeStep, setActiveStep] = useState(-1);

  useEffect(() => {
    setError(null);
    request<Candle[]>(`/market/candles?symbol=${symbol}&interval=${timeframe}&outputsize=150`)
      .then(setCandles)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load candles"));
  }, [symbol, timeframe, request]);

  async function handleEvaluate() {
    setEvaluating(true);
    setError(null);
    setActiveStep(0);
    const stepTimer = setInterval(() => setActiveStep((s) => Math.min(s + 1, AGENT_STEPS.length - 1)), 1500);
    try {
      const advisory = await request<Advisory>("/advisories/evaluate", {
        method: "POST",
        body: JSON.stringify({ symbol, timeframe }),
      });
      router.push(`/advisories/${advisory.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      clearInterval(stepTimer);
      setEvaluating(false);
      setActiveStep(-1);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">
          {symbol} · {timeframe}
        </h1>
        <button
          onClick={handleEvaluate}
          disabled={evaluating}
          className="rounded-md bg-ink px-4 py-2 text-sm font-medium text-base disabled:opacity-40"
        >
          {evaluating ? "Evaluating…" : "Evaluate setup"}
        </button>
      </div>

      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      {evaluating && (
        <div className="flex gap-3 rounded-lg border border-black/10 bg-panel p-4 text-sm">
          {AGENT_STEPS.map((step, i) => (
            <span
              key={step}
              className={`rounded-full px-3 py-1 transition-colors ${
                i <= activeStep ? "bg-accent/20 text-ink shadow-[0_0_12px_rgba(0,245,212,0.5)]" : "text-ink/40"
              }`}
            >
              {step}
            </span>
          ))}
        </div>
      )}

      <div className="rounded-lg border border-black/10 bg-panel p-5">
        {candles.length === 0 && !error ? (
          <p className="text-sm text-ink/50">
            Loading price data — set TWELVEDATA_API_KEY on the API if this stays empty.
          </p>
        ) : (
          <Candlesticks candles={candles} />
        )}
      </div>
    </div>
  );
}
