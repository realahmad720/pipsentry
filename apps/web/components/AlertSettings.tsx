"use client";

import { useEffect, useState } from "react";

import { useApi } from "@/lib/useApi";
import type { Account } from "@/lib/types";

export function AlertSettings() {
  const { request } = useApi();
  const [account, setAccount] = useState<Account | null>(null);
  const [linkCode, setLinkCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    request<Account>("/account").then(setAccount).catch((err) => setError(err instanceof Error ? err.message : "Failed to load account"));
  }, [request]);

  async function handleGenerateCode() {
    try {
      const { code } = await request<{ code: string; expires_in_seconds: number }>("/telegram/link-code");
      setLinkCode(code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate a linking code");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-medium text-ink">Alerts & notifications</h1>
      {error && <p className="rounded-md bg-bearish/10 px-3 py-2 text-sm text-bearish">{error}</p>}

      <section className="flex flex-col gap-4 rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="text-sm font-medium text-ink/70">Telegram</h2>
        {account?.telegram_linked ? (
          <p className="text-sm text-bullish">Telegram is linked — advisories will be pushed there as they&apos;re delivered.</p>
        ) : (
          <>
            <p className="text-sm text-ink/60">
              Message the Pipsentry bot with <span className="tabular font-medium">/start &lt;code&gt;</span> to link
              your account. Codes expire after 10 minutes.
            </p>
            <button onClick={handleGenerateCode} className="w-fit rounded-md bg-ink px-4 py-2 text-sm font-medium text-base">
              Generate linking code
            </button>
            {linkCode && (
              <p className="tabular rounded-md bg-accent/10 px-3 py-2 text-sm text-ink">/start {linkCode}</p>
            )}
          </>
        )}
      </section>

      <section className="flex flex-col gap-2 rounded-lg border border-dashed border-black/10 p-5 text-sm text-ink/50">
        Quiet hours and per-symbol/severity alert rules aren&apos;t wired in yet — there&apos;s no
        preference storage for them in the current data model, so this is a documented gap rather
        than a fake toggle.
      </section>
    </div>
  );
}
