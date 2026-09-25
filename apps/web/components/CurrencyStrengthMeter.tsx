"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { CurrencyStrength } from "@/lib/types";

export function CurrencyStrengthMeter() {
  const { request } = useApi();
  const [strength, setStrength] = useState<CurrencyStrength>({});
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<CurrencyStrength>("/market/currency-strength")
      .then(setStrength)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load currency strength"))
      .finally(() => setLoaded(true));
  }, [request]);

  const sorted = Object.entries(strength).sort((a, b) => b[1] - a[1]);
  const maxAbs = Math.max(0.01, ...sorted.map(([, v]) => Math.abs(v)));

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Currency strength</h1>
      <p className="text-sm text-ink/50">Daily % move of each major currency, averaged across every pair it trades in.</p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="flex flex-col gap-3 rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : (
          sorted.map(([currency, value]) => (
            <div key={currency} className="flex items-center gap-3">
              <span className="w-10 text-sm text-ink/70">{currency}</span>
              <div className="relative h-3 flex-1 rounded-full bg-black/5">
                <div
                  className={`absolute top-0 h-3 rounded-full ${value >= 0 ? "bg-bullish" : "bg-bearish"}`}
                  style={{
                    left: value >= 0 ? "50%" : `${50 - (Math.abs(value) / maxAbs) * 50}%`,
                    width: `${(Math.abs(value) / maxAbs) * 50}%`,
                  }}
                />
                <div className="absolute left-1/2 top-0 h-3 w-px bg-black/20" />
              </div>
              <span className="tabular w-16 text-right text-sm text-ink/70">{value.toFixed(2)}%</span>
            </div>
          ))
        )}
      </section>
    </div>
  );
}
