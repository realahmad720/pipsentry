"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { SessionClock } from "@/lib/types";

export function SessionClockView() {
  const { request } = useApi();
  const [data, setData] = useState<SessionClock | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = () => request<SessionClock>("/market/session-clock").then(setData).catch((err) => setError(err instanceof Error ? err.message : "Failed to load session clock"));
    load();
    const interval = setInterval(load, 60000);
    return () => clearInterval(interval);
  }, [request]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Session clock</h1>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!data ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : (
          <div className="flex flex-col gap-4">
            <p className="tabular text-sm text-ink/60">UTC {new Date(data.utc_time).toUTCString()}</p>
            <div className="flex gap-3">
              {data.sessions.map((s) => (
                <div
                  key={s.name}
                  className={`flex-1 rounded-md border p-3 text-sm ${
                    data.open_sessions.includes(s.name) ? "border-accent bg-accent/10 text-ink" : "border-black/10 text-ink/40"
                  }`}
                >
                  <div className="font-medium">{s.name}</div>
                  <div className="tabular text-xs">
                    {s.open_hour_utc}:00 – {s.close_hour_utc}:00 UTC
                  </div>
                </div>
              ))}
            </div>
            {data.overlaps.length > 0 && (
              <p className="text-sm text-ink">Overlap right now: {data.overlaps.join(", ")}</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
