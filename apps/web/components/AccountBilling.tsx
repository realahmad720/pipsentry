"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Account } from "@/lib/types";

export function AccountBilling() {
  const { request } = useApi();
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<Account>("/account").then(setAccount).catch((err) => setError(err instanceof Error ? err.message : "Failed to load account"));
  }, [request]);

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Account & billing</h1>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      {!account ? (
        <p className="text-sm text-ink/50">Loading…</p>
      ) : (
        <>
          <section className="rounded-lg border border-black/10 bg-panel p-5">
            <h2 className="mb-3 text-sm font-medium text-ink/70">Profile</h2>
            <div className="tabular grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <div><div className="text-ink/50">Email</div>{account.email}</div>
              <div><div className="text-ink/50">Plan tier</div>{account.plan_tier}</div>
              <div><div className="text-ink/50">Telegram</div>{account.telegram_linked ? "Linked" : "Not linked"}</div>
            </div>
          </section>

          <section className="rounded-lg border border-black/10 bg-panel p-5">
            <h2 className="mb-3 text-sm font-medium text-ink/70">Subscription</h2>
            {account.subscription ? (
              <div className="tabular grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
                <div><div className="text-ink/50">Plan</div>{account.subscription.plan}</div>
                <div><div className="text-ink/50">Status</div>{account.subscription.status}</div>
                <div><div className="text-ink/50">Monthly token budget</div>{account.subscription.monthly_token_budget.toLocaleString()}</div>
              </div>
            ) : (
              <p className="text-sm text-ink/50">No subscription on file — the Free tier is watchlist-only, no live advisories.</p>
            )}
          </section>

          <section className="rounded-lg border border-black/10 bg-panel p-5">
            <h2 className="mb-3 text-sm font-medium text-ink/70">Usage</h2>
            <div className="tabular grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <div><div className="text-ink/50">Tokens this month</div>{account.month_to_date_tokens.toLocaleString()}</div>
              <div><div className="text-ink/50">Tokens today</div>{account.today_usage?.tokens_used.toLocaleString() ?? 0}</div>
              <div><div className="text-ink/50">Estimated cost today</div>${(account.today_usage?.cost_estimate_usd ?? 0).toFixed(4)}</div>
            </div>
          </section>

          <section className="rounded-lg border border-dashed border-black/10 p-5 text-sm text-ink/50">
            Stripe checkout is deferred (Section 21) — this page reads real plan/usage data but
            there&apos;s no payment flow behind it yet.
          </section>
        </>
      )}
    </div>
  );
}
