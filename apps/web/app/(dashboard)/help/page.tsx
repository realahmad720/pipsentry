export default function HelpPage() {
  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-xl font-medium text-ink">Help & disclaimer</h1>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">What Pipsentry is</h2>
        <p className="text-sm text-ink/80">
          Pipsentry is an asymmetric decision-support tool for discretionary currency traders. It runs
          on a strict advisory, human-in-the-loop model: autonomous trade execution is out of scope,
          permanently. The system never places orders. It ingests trading knowledge, synthesizes
          multi-source data, and issues deterministic, time-stamped advisories through this dashboard
          and Telegram — the decision to act on any of them is always yours.
        </p>
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Financial disclaimer</h2>
        <p className="text-sm text-ink/80">
          Every advisory Pipsentry produces is an automated output for informational purposes only and
          does not constitute financial advice. Pipsentry does not register as, and does not represent
          itself as, a licensed financial advisor. Trading foreign exchange carries a high level of
          risk and may not be suitable for all investors. You are solely responsible for your own
          trading decisions and their outcomes.
        </p>
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Terms of service</h2>
        <p className="text-sm text-ink/80">
          By using Pipsentry you agree that its advisories, backtests, and analytics are provided
          &quot;as is&quot;, without warranty of accuracy or fitness for a particular purpose. Data feeds
          (TwelveData, the CFTC, economic calendar providers) are third-party sources Pipsentry does
          not control the accuracy or availability of. This is a template ToS for an MVP, not a
          substitute for legal review before opening the product to paying users across jurisdictions
          (Section 14 of the build spec).
        </p>
      </section>

      <section className="rounded-lg border border-black/10 bg-panel p-5">
        <h2 className="mb-3 text-sm font-medium text-ink/70">Support</h2>
        <p className="text-sm text-ink/80">
          For questions about a specific advisory, open it from the Advisory Feed — every advisory
          carries its full four-agent reasoning trail. For platform issues, use the connectors page to
          check whether a data source is unreachable before assuming the advisory itself is wrong.
        </p>
      </section>
    </div>
  );
}
