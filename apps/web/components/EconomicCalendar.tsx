"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { CalendarEvent } from "@/lib/types";

const IMPACT_STYLE: Record<CalendarEvent["impact"], string> = {
  High: "bg-bearish/10 text-bearish",
  Medium: "bg-accent/15 text-ink/70",
  Low: "bg-black/5 text-ink/50",
  Holiday: "bg-black/5 text-ink/40",
};

export function EconomicCalendar() {
  const { request } = useApi();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [hoursAhead, setHoursAhead] = useState(48);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(false);
    request<CalendarEvent[]>(`/market/calendar?hours_ahead=${hoursAhead}`)
      .then((data) => {
        setEvents(data);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load calendar"))
      .finally(() => setLoaded(true));
  }, [hoursAhead, request]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">Economic calendar</h1>
        <select
          value={hoursAhead}
          onChange={(e) => setHoursAhead(Number(e.target.value))}
          className="rounded-md border border-black/10 bg-base px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
        >
          {[24, 48, 72, 168].map((h) => (
            <option key={h} value={h}>
              Next {h}h
            </option>
          ))}
        </select>
      </div>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        {!loaded ? (
          <p className="text-sm text-ink/50">Loading…</p>
        ) : events.length === 0 ? (
          <p className="text-sm text-ink/50">No high-impact events in this window.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-ink/50">
                <th className="pb-2 font-medium">Event</th>
                <th className="pb-2 font-medium">Currency</th>
                <th className="pb-2 font-medium">Impact</th>
                <th className="tabular pb-2 font-medium">When</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e, i) => (
                <tr key={i} className="border-t border-black/5 text-ink">
                  <td className="py-2">{e.title}</td>
                  <td className="py-2 text-ink/60">{e.country}</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${IMPACT_STYLE[e.impact]}`}>
                      {e.impact}
                    </span>
                  </td>
                  <td className="tabular py-2 text-ink/50">{new Date(e.event_time).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
