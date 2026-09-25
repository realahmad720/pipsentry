"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { IngestedSource } from "@/lib/types";

type StrategyGroup = { tag: string; sources: IngestedSource[] };

export function StrategyLibrary() {
  const { request } = useApi();
  const [groups, setGroups] = useState<StrategyGroup[]>([]);
  const [untagged, setUntagged] = useState<IngestedSource[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<IngestedSource[]>("/knowledge/sources")
      .then((sources) => {
        const byTag = new Map<string, IngestedSource[]>();
        const noTag: IngestedSource[] = [];
        for (const source of sources) {
          if (source.tags.length === 0) {
            noTag.push(source);
            continue;
          }
          for (const tag of source.tags) {
            byTag.set(tag, [...(byTag.get(tag) ?? []), source]);
          }
        }
        setGroups(Array.from(byTag.entries()).map(([tag, srcs]) => ({ tag, sources: srcs })));
        setUntagged(noTag);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load strategies"))
      .finally(() => setLoaded(true));
  }, [request]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Strategy library</h1>
      <p className="text-sm text-ink/50">
        Every strategy here comes from tags on your ingested Knowledge Hub sources — there&apos;s no
        separate strategies table, so this is a read-only view derived from what you&apos;ve tagged
        (Section 6). Run a backtest to see a strategy&apos;s historical performance.
      </p>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      {!loaded ? (
        <p className="text-sm text-ink/50">Loading…</p>
      ) : groups.length === 0 && untagged.length === 0 ? (
        <p className="text-sm text-ink/50">Ingest and tag a source in the Knowledge Hub to build your first strategy.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {groups.map((group) => (
            <section key={group.tag} className="rounded-lg border border-black/10 bg-panel p-5">
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-sm font-medium text-ink">{group.tag}</h2>
                <Link href="/backtest" className="text-xs text-ink/60 hover:text-ink hover:underline">
                  Backtest this strategy
                </Link>
              </div>
              <ul className="flex flex-col gap-1 text-sm text-ink/70">
                {group.sources.map((s) => (
                  <li key={s.id}>{s.title ?? s.source_url ?? "Untitled source"}</li>
                ))}
              </ul>
            </section>
          ))}
          {untagged.length > 0 && (
            <section className="rounded-lg border border-dashed border-black/10 p-5 text-sm text-ink/50">
              {untagged.length} untagged source(s) — add tags in the Knowledge Hub to group them into a strategy.
            </section>
          )}
        </div>
      )}
    </div>
  );
}
