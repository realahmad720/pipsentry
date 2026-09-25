"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { CotPositioning } from "@/lib/types";

export function CotPositioningView() {
  const { request } = useApi();
  const [currencies, setCurrencies] = useState<string[]>([]);
  const [currency, setCurrency] = useState("EUR");
  const [data, setData] = useState<CotPositioning | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<string[]>("/market/cot/supported-currencies").then(setCurrencies).catch(() => {});
  }, [request]);

  useEffect(() => {
    setError(null);
    setData(null);
    request<CotPositioning>(`/market/cot?currency=${currency}`)
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load COT data"));
  }, [currency, request]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">COT positioning</h1>
        <select
          value={currency}
          onChange={(e) => setCurrency(e.target.value)}
          className="rounded-md border border-black/10 bg-base px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
        >
          {(currencies.length ? currencies : ["EUR", "GBP", "JPY", "AUD", "CAD", "CHF"]).map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <p className="text-sm text-ink/50">Weekly CFTC Commitment of Traders report, non-commercial (speculative) net positioning.</p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!data ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : (
          <div className="tabular grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            <div>
              <div className="text-ink/50">Report date</div>
              {data.report_date}
            </div>
            <div>
              <div className="text-ink/50">Non-commercial net</div>
              <span className={data.noncommercial_net >= 0 ? "text-bullish" : "text-bearish"}>
                {data.noncommercial_net.toLocaleString()}
              </span>
            </div>
            <div>
              <div className="text-ink/50">Non-commercial long / short</div>
              {data.noncommercial_long.toLocaleString()} / {data.noncommercial_short.toLocaleString()}
            </div>
            <div>
              <div className="text-ink/50">Open interest</div>
              {data.open_interest.toLocaleString()}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
