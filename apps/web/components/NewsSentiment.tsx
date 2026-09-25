"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { SentimentScore } from "@/lib/types";

const MAJORS = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"];

export function NewsSentiment() {
  const { request } = useApi();
  const [scores, setScores] = useState<SentimentScore[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all(MAJORS.map((c) => request<SentimentScore>(`/market/sentiment?currency=${c}`)))
      .then(setScores)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load sentiment"))
      .finally(() => setLoaded(true));
  }, [request]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">News & sentiment</h1>
      <p className="text-sm text-ink/50">
        Surprise-based heuristic from released economic prints, not headline NLP — see the API's
        marketdata/sentiment.py for what this does and doesn&apos;t do.
      </p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {scores.map((s) => (
              <div key={s.currency} className="flex flex-col gap-1 rounded-md border border-black/5 p-3">
                <span className="text-xs text-ink/50">{s.currency}</span>
                <span className={`tabular text-lg font-medium ${s.score > 0 ? "text-bullish" : s.score < 0 ? "text-bearish" : "text-ink/60"}`}>
                  {s.score > 0 ? "+" : ""}
                  {s.score.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
