import Link from "next/link";

const GROUPS: { label: string; items: { href: string; label: string }[] }[] = [
  {
    label: "Core",
    items: [
      { href: "/dashboard", label: "Dashboard" },
      { href: "/watchlist", label: "Watchlist" },
      { href: "/advisories", label: "Advisory feed" },
      { href: "/chart", label: "Chart workspace" },
    ],
  },
  {
    label: "Market context",
    items: [
      { href: "/calendar", label: "Economic calendar" },
      { href: "/news", label: "News & sentiment" },
      { href: "/currency-strength", label: "Currency strength" },
      { href: "/correlation", label: "Correlation matrix" },
      { href: "/session-clock", label: "Session clock" },
      { href: "/cot", label: "COT positioning" },
    ],
  },
  {
    label: "Knowledge & strategy",
    items: [
      { href: "/knowledge", label: "Knowledge hub" },
      { href: "/strategy-library", label: "Strategy library" },
      { href: "/backtest", label: "Backtest & validation" },
    ],
  },
  {
    label: "Trading tools",
    items: [
      { href: "/position-size-calculator", label: "Position size calculator" },
      { href: "/trade-journal", label: "Trade journal" },
      { href: "/performance", label: "Performance analytics" },
    ],
  },
  {
    label: "Platform",
    items: [
      { href: "/connectors", label: "Connectors" },
      { href: "/settings", label: "Alerts & notifications" },
      { href: "/account", label: "Account & billing" },
      { href: "/onboarding", label: "Onboarding" },
      { href: "/help", label: "Help & disclaimer" },
    ],
  },
];

export function NavRail() {
  return (
    <nav className="flex h-screen w-64 flex-col gap-5 overflow-y-auto border-r border-black/10 bg-panel px-3 py-6">
      <div className="mb-2 flex items-center gap-2 px-2">
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-accent text-xs font-medium text-ink">
          PS
        </span>
        <span className="text-sm font-medium text-ink">Pipsentry</span>
      </div>
      {GROUPS.map((group) => (
        <div key={group.label} className="flex flex-col gap-1">
          <span className="px-3 text-[11px] font-medium uppercase tracking-wide text-ink/35">
            {group.label}
          </span>
          {group.items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-sm text-ink/80 hover:bg-black/5"
            >
              {item.label}
            </Link>
          ))}
        </div>
      ))}
    </nav>
  );
}
