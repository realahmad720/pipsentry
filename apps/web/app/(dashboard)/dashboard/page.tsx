import Link from "next/link";

import { apiFetch, type Account, type Advisory, type Watchlist } from "@/lib/api";

async function safeFetch<T>(path: string): Promise<T[]> {
  try {
    return await apiFetch<T[]>(path);
  } catch {
    return [];
  }
}

const QUICK_LINKS = [
  { href: "/chart", label: "Evaluate a setup" },
  { href: "/watchlist", label: "Manage watchlist" },
  { href: "/knowledge", label: "Knowledge hub" },
  { href: "/backtest", label: "Run a backtest" },
];

export default async function DashboardPage() {
  const [watchlist, advisories, account] = await Promise.all([
    safeFetch<Watchlist>("/watchlists"),
    safeFetch<Advisory>("/advisories"),
    apiFetch<Account>("/account").catch(() => null),
  ]);

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-medium text-ink">Today&apos;s advisories</h1>
        <div className="flex gap-2">
          {QUICK_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="rounded-md border border-black/10 px-3 py-1.5 text-sm text-ink/70 hover:bg-black/5"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>

      {account && (
        <section className="rounded-lg border border-black/10 bg-panel p-5">
          <h2 className="mb-3 text-sm font-medium text-ink/70">Token budget</h2>
          <div className="tabular flex gap-8 text-sm text-ink">
            <div>
              <div className="text-ink/50">Plan</div>
              {account.plan_tier}
            </div>
            <div>
              <div className="text-ink/50">Used this month</div>
              {account.month_to_date_tokens.toLocaleString()}
              {account.subscription ? ` / ${account.subscription.monthly_token_budget.toLocaleString()}` : ""}
            </div>
          </div>
        </section>
      )}

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Watchlist</h2>
        {watchlist.length === 0 ? (
          <p className="text-sm text-ink/50">No symbols tracked yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {watchlist.map((w) => (
              <li key={w.id} className="tabular flex justify-between text-sm text-ink">
                <span>{w.symbol}</span>
                <span className="text-ink/50">{w.timeframe}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Recent advisories</h2>
        {advisories.length === 0 ? (
          <p className="text-sm text-ink/50">No advisories yet.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {advisories.map((a) => (
              <li key={a.id} className="tabular flex justify-between text-sm text-ink">
                <span>
                  {a.symbol} · {a.action}
                </span>
                <span
                  className={a.action.includes("SELL") ? "text-bearish" : "text-bullish"}
                >
                  {(a.confidence_score * 100).toFixed(0)}%
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
