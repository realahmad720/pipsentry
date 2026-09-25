"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Account, Connector, IngestedSource, Watchlist } from "@/lib/types";

export function OnboardingWizard() {
  const { request } = useApi();
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [sources, setSources] = useState<IngestedSource[]>([]);
  const [watchlist, setWatchlist] = useState<Watchlist[]>([]);
  const [account, setAccount] = useState<Account | null>(null);

  useEffect(() => {
    request<Connector[]>("/connectors").then(setConnectors).catch(() => {});
    request<IngestedSource[]>("/knowledge/sources").then(setSources).catch(() => {});
    request<Watchlist[]>("/watchlists").then(setWatchlist).catch(() => {});
    request<Account>("/account").then(setAccount).catch(() => {});
  }, [request]);

  const steps = [
    { label: "Connect a data feed", done: connectors.length > 0, href: "/connectors" },
    { label: "Ingest a first knowledge source", done: sources.length > 0, href: "/knowledge" },
    { label: "Set a watchlist", done: watchlist.length > 0, href: "/watchlist" },
    { label: "Link Telegram", done: !!account?.telegram_linked, href: "/settings" },
  ];
  const completed = steps.filter((s) => s.done).length;

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Getting started</h1>
      <p className="text-sm text-ink/50">{completed} of {steps.length} steps complete.</p>

      <section className="flex flex-col gap-3 rounded-lg border border-black/10 bg-panel p-5">
        {steps.map((step) => (
          <Link
            key={step.label}
            href={step.href}
            className="flex items-center justify-between rounded-md border border-black/5 px-4 py-3 hover:bg-black/5"
          >
            <span className="text-sm text-ink">{step.label}</span>
            <span className={`text-xs font-medium ${step.done ? "text-bullish" : "text-ink/40"}`}>
              {step.done ? "Done" : "Start →"}
            </span>
          </Link>
        ))}
      </section>
    </div>
  );
}
