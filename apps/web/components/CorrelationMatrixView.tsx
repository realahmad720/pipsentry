"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { CorrelationMatrix } from "@/lib/types";

function cellColor(value: number): string {
  if (value >= 0.5) return "bg-bullish/20 text-bullish";
  if (value <= -0.5) return "bg-bearish/20 text-bearish";
  return "bg-black/5 text-ink/60";
}

export function CorrelationMatrixView() {
  const { request } = useApi();
  const [data, setData] = useState<CorrelationMatrix | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<CorrelationMatrix>("/market/correlation")
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load correlation matrix"));
  }, [request]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Correlation matrix</h1>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="overflow-x-auto rounded-lg border border-black/10 bg-panel p-5">
        {!data ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : (
          <table className="tabular text-sm">
            <thead>
              <tr>
                <th className="p-1"></th>
                {data.pairs.map((p) => (
                  <th key={p} className="p-1 text-xs font-medium text-ink/50">
                    {p}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.pairs.map((row) => (
                <tr key={row}>
                  <td className="p-1 text-xs font-medium text-ink/50">{row}</td>
                  {data.pairs.map((col) => (
                    <td key={col} className={`p-1 text-center ${cellColor(data.matrix[row][col])}`}>
                      {data.matrix[row][col].toFixed(2)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
