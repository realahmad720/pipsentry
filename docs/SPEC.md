# Pipsentry: AI-Driven Forex Intelligence & Advisory Copilot

## Complete Build Specification (v2.1.0, Branded & Multi-Tenant Revision)

### (Internal engineering codename: FX-Sentient)

**Target Environment:** Multi-tenant microservices, web dashboard, advisory engine
**Execution Standard:** Enterprise quantitative and NLP engineering blueprint
**Prepared for:** Direct handoff to Claude Code for implementation

---

## 1. Executive Summary & Scope

FX-Sentient is an asymmetric decision-support tool for discretionary currency traders. It runs on a strict Advisory (human-in-the-loop) model.

- Autonomous trade execution is out of scope, permanently. The system never places orders.
- The system ingests trading knowledge, synthesizes multi-source data, and issues deterministic, time-stamped advisories (entry, stop loss, take profit, macro invalidation) through a web dashboard and Telegram push notifications.
- The system is being built **multi-tenant from the start**: multiple users will eventually sign up, each with their own knowledge base, watchlists, and alert history, isolated from every other user's data.
- A Dynamic Tool-First Knowledge Ingestion Pipeline lets each user index YouTube playlists, PDF rulebooks, or strategy transcripts incrementally, without developer intervention or cold restarts.

This document is a complete build spec: architecture, data model, agent logic, cost controls, security, deployment, and legal disclaimers.

---

## 2. Component Inclusion & Exclusion Matrix

| Layer / Domain | Included | Excluded | Justification |
|---|---|---|---|
| Execution | Advisory alerts, risk calculations, checklist verification | Direct broker execution (auto-order placement via MT4/MT5/cTrader APIs) | Prevents algorithmic capital erosion and API slippage; user retains final execution authority |
| Knowledge Base | Dynamic RAG via Qdrant, recursive character chunking, semantic metadata tagging, per-tenant collections | Static, pre-compiled context windows or hardcoded system prompts | Knowledge must evolve as market regimes and strategies shift, and must stay isolated per user |
| Reasoning | Hybrid LLM setup: Claude Sonnet (synthesis and code-to-logic) and DeepSeek-R1 (chain-of-thought) | Low-capacity local 7B models or pure rule-based decision trees | Financial nuance and multi-timeframe structural logic need top-tier reasoning |
| Market Data | MCP server integration, Financial Modeling Prep API, ForexFactory RSS, TwelveData | Unstructured scraping of social media or short-form video clips | Noise reduction; signals need structured, low-latency, high-integrity data |
| Identity | Managed auth (Clerk or Auth.js), per-user JWT sessions, row-level tenant isolation | Custom-built auth from scratch, shared single login | Multi-tenant safety and faster time to ship |
| Persistence | Postgres (users, subscriptions, ingested sources, advisories, audit log) + Qdrant (vectors) | Storing structured records inside the vector DB | Vector DBs are the wrong tool for relational, transactional data |
| UI/UX | Next.js dashboard, FastAPI backend, Telegram webhook bot | Monolithic desktop apps (C++ MFC, heavyweight native suites) | Faster iteration, cross-platform reach, cloud-native deployment |

---

## 3. End-to-End System Architecture

```
                      [ FRONTEND: Next.js + Tailwind Dashboard ]
                                        │
                          (Auth: Clerk/Auth.js, per-tenant session)
                                        │
                                        ▼
                    [ NOTIFICATIONS: Telegram Bot per user ]
                                        ▲
                                        │
┌───────────────────────────────────────┴───────────────────────────────────┐
│                     BACKEND CORE (Python FastAPI Service Layer)          │
│              Rate limiting · request auth · per-tenant routing           │
└──────────────┬───────────────────────────────────────────┬───────────────┘
               │                                            │
               ▼                                            ▼
┌──────────────────────────────┐          ┌────────────────────────────────┐
│ RELATIONAL STORE (Postgres)  │          │ KNOWLEDGE BASE SUBSYSTEM       │
│ • users, subscriptions       │          │ • YouTube transcript pipeline  │
│ • ingested_sources metadata  │          │ • Document ingestion (PDF/TXT) │
│ • advisories, alerts, logs   │          │ • Embedding generation         │
│ • billing / usage counters   │          │ • Vector DB (Qdrant, per-tenant│
└──────────────────────────────┘          │   collection namespace)        │
                                           └────────────────────────────────┘
               │                                            │
               └───────────────────┬────────────────────────┘
                                    ▼
                    ┌────────────────────────────────────┐
                    │    MULTI-AGENT INFERENCE ENGINE    │
                    │ • Technical Analysis Agent         │
                    │ • Macro & Sentiment Agent          │
                    │ • Strategy & RAG Retriever Agent   │
                    │ • Synthesis & Risk Auditor Agent   │
                    │ • MCP Bridge (live data pull)      │
                    └────────────────────────────────────┘
                                    │
                                    ▼
                      [ FOUNDATIONAL REASONING ]
                      Claude Sonnet / DeepSeek-R1
                                    │
                                    ▼
                    [ COST & TOKEN BUDGET GUARDRAIL ]
                                    │
                                    ▼
                       [ Final Advisory Delivered ]
```

---

## 4. Persistent Data Model

Postgres (Neon or Supabase). Core tables:

- `users` — id, email, auth_provider_id, plan_tier, created_at
- `subscriptions` — user_id, plan, status, renewal_date, monthly_token_budget
- `ingested_sources` — id, user_id, source_type (youtube/pdf/txt), source_url, title, tags, chunk_count, vector_collection_name, status (pending/indexed/failed), created_at
- `watchlists` — id, user_id, symbol, timeframe, active
- `advisories` — id, user_id, symbol, timeframe, action, confidence_score, payload_json, delivered_at
- `alert_deliveries` — id, advisory_id, channel (telegram/dashboard), delivered_at, read_at
- `usage_counters` — user_id, date, tokens_used, api_calls_made, cost_estimate_usd
- `audit_log` — id, user_id, event_type, detail_json, created_at

Each user's Qdrant collection is namespaced as `kb_{user_id}` so retrieval never crosses tenant boundaries.

---

## 5. Authentication & Multi-Tenancy

- Managed auth provider: **Clerk** (decided). Issues JWTs the FastAPI backend verifies.
- Every backend request carries the authenticated `user_id`. All Postgres queries and Qdrant collection lookups are scoped by that id, enforced at the query layer.
- Plan tiers: Free (watchlist only, no live advisories), Pro (live advisories, limited monthly token budget), Unlimited (higher budget, priority queue).
- Billing integration (Stripe) is a Phase 6 item; `subscriptions` table exists from day one.

---

## 6. Data Ingestion & Knowledge Hub

1. **Source registration** — `/dashboard/knowledge`, YouTube URL/channel link or PDF/TXT upload.
2. **Ingestion worker** — `youtube-transcript-api`; falls back to `yt-dlp` + Whisper if unavailable.
3. **Metadata extraction** — title, author, source URL, upload timestamp, strategy tags (ICT, Supply and Demand, London Breakout, etc).
4. **Chunking** — `RecursiveCharacterTextSplitter`, 1,000 token chunks, 150 token overlap.
5. **Vector persistence** — embeddings via `text-embedding-3-small` or `BAAI/bge-large-en`, written to the user's namespaced Qdrant collection, tagged by strategy category.
6. **Reindex/purge** — per-source "purge and reindex" action.

---

## 7. Multi-Agent Reasoning Framework

Orchestrated via LangGraph:

```
        [ User Trigger / Scheduled Candle-Close Poll ]
                          │
           ┌──────────────┴──────────────┐
           ▼                              ▼
 [ Agent 1: Macro & News ]      [ Agent 2: Technical & Price Action ]
 • ForexFactory + RSS feeds     • Price data via MCP server
 • Economic calendar scan       • Trend, key levels, indicators
 • Sentiment score (-1 to +1)   • ATR, RSI, moving averages
           │                              │
           └──────────────┬───────────────┘
                          ▼
             [ Agent 3: Strategy & RAG Retriever ]
             • Queries the user's Qdrant namespace
             • Pulls relevant rule sets from their ingested knowledge
             • Checks the setup against those rules
                          │
                          ▼
             [ Agent 4: Risk & Synthesis Auditor ]
             • Compares technical setup against macro regime
             • Evaluates risk:reward (minimum 1:2)
             • Confirms no high-impact news within 45 minutes
             • Applies the conflict resolution rule below
             • Compiles the structured advisory
                          │
                          ▼
                [ Final Advisory Delivered ]
```

**Conflict resolution rule:** if Agent 1 (macro) and Agent 2 (technical) disagree in direction (e.g. technical is bullish but macro sentiment is below -0.4), Agent 4 downgrades the advisory to `STATUS: CONFLICTED / REDUCED SIZE` and caps suggested position sizing at 50% of the strategy's normal risk unit, rather than issuing a full-confidence directional call. It never silently picks one agent's view over the other.

**LLM assignment (decided):** DeepSeek-R1 for Agents 1–3 (cheaper chain-of-thought passes), Claude Sonnet reserved for Agent 4 (final synthesis/risk audit) to control cost while keeping the highest-stakes output on the stronger model.

---

## 8. Cost & Token Budget Controls

- Each user has a `monthly_token_budget` in `subscriptions`. Every agent call logs token usage to `usage_counters`.
- Budget middleware checks remaining balance before invoking Agent 4. If over budget, returns `STATUS: BUDGET_EXCEEDED` instead of silently degrading quality.
- Nightly job aggregates `usage_counters` into a per-user cost estimate, surfaced on the dashboard.

---

## 9. Backtesting & Validation

1. **Historical replay harness** — feed the pipeline historical OHLC + economic calendar for a fixed date range (min 6 months), agents evaluate each candle close as if live.
2. **Advisory scorecard** — for every historical advisory, log whether SL or TP hit first; compute win rate, average R-multiple, max drawdown.
3. **Gate to forward testing** — a strategy/symbol only moves to the live 3-week forward paper test after clearing a minimum backtest threshold (positive expectancy over the historical window).

---

## 10. Signal & Advisory Payload Specification

```json
{
  "timestamp": "2026-09-25T05:30:00Z",
  "user_id": "usr_8841",
  "symbol": "EURUSD",
  "timeframe": "1H",
  "action": "SELL_LIMIT",
  "bias": "BEARISH",
  "confidence_score": 0.86,
  "conflict_status": "NONE",
  "execution_zones": {
    "entry_range": [1.08450, 1.08550],
    "suggested_entry": 1.08500,
    "stop_loss": 1.08820,
    "take_profit_1": 1.07900,
    "take_profit_2": 1.07450,
    "risk_reward_ratio": "1:2.85"
  },
  "rationale": {
    "technical": "Rejection from 4H order block. Bearish market structure shift confirmed on 15M with a clear fair value gap.",
    "macro_fundamental": "US dollar remains bid post-Core PCE print; European PMI missed consensus by 1.8 points.",
    "strategy_match": "ICT Silver Bullet short sequence retrieved from ingested source #src_0842."
  },
  "warnings": [
    "Fed Chair speech scheduled in 4 hours; move stop to breakeven if Target 1 is hit before the event."
  ],
  "disclaimer": "This is an automated advisory for informational purposes only and does not constitute financial advice. You are solely responsible for your own trading decisions."
}
```

---

## 11. Security & Secrets Management

- All third-party API keys (Anthropic, DeepSeek, TwelveData, Financial Modeling Prep, Telegram) live in a managed secrets vault (Doppler, or the hosting platform's encrypted env vars). Never committed, never in pushed `.env` files.
- Per-user Telegram bot tokens/chat IDs encrypted at rest in Postgres.
- Rate limiting on all public API endpoints.
- Row-level tenant isolation enforced at the database query layer, tested explicitly (user A cannot retrieve user B's advisories or knowledge base).

---

## 12. Deployment & Infrastructure Recommendation

| Component | Recommendation | Why |
|---|---|---|
| Frontend (Next.js) | **Vercel** | Zero-config deploys, preview environments, generous free tier |
| Backend (FastAPI) | **Render** or **Railway** | Simple container deploys, background worker support |
| Relational DB | **Neon** or **Supabase** (Postgres) | Serverless Postgres, branching for safe migrations |
| Vector DB | **Qdrant Cloud** | Managed, namespaced collections per tenant |
| Background jobs / queue | **Render Cron Jobs** or Celery + Redis on Railway | Scheduled candle-close evaluations and ingestion workers |
| Notifications | **Telegram Bot API** | No app store approval cycle, instant delivery |
| Secrets | **Doppler**, or platform-native encrypted env vars | Centralized secret management |

---

## 13. Observability & Monitoring

- **Error tracking:** Sentry (frontend + backend).
- **Uptime monitoring:** Better Uptime / UptimeRobot pinging the health endpoint every 60s.
- **Structured logging:** JSON logs, shipped to platform log viewer or Logtail.
- **Agent-level tracing:** log each agent's input/output and latency per advisory generation.

---

## 14. Legal & Compliance Note

- Every advisory (dashboard + Telegram) must include the disclaimer field from the payload spec.
- The system does not register as, and must not represent itself as, a licensed financial advisor. ToS and disclaimer page are part of the MVP signup flow.
- Not legal advice; consult an actual lawyer before opening to paying multi-tenant users across jurisdictions.

---

## 15. Implementation Roadmap

**Phase 1: Environment & Foundation** — FastAPI service, Postgres schema, Qdrant per-tenant collections, Clerk auth integration, secrets vault. *(this scaffold)*

**Phase 2: Knowledge Ingestion Engine** — dashboard ingestion UI, extraction microservice, purge/reindex.

**Phase 3: Market Data Feeds & MCP Bridge** — MCP server for TwelveData/OANDA/MT5 (read-only), ForexFactory + news RSS collectors, sentiment scoring.

**Phase 4: Multi-Agent Logic Assembly** — LangGraph wiring for Agents 1–4, no-trade-zone guardrail, token budget middleware.

**Phase 5: Backtesting & Validation** — historical replay harness, advisory scorecard, expectancy gate.

**Phase 6: Delivery Surface & Forward Testing** — Telegram bot, advisory console, 3-week forward paper test.

**Phase 7: Multi-Tenant Hardening & Launch** — row-level isolation tests, rate limiting, Sentry/uptime/logging, ToS/disclaimer, optional Stripe billing.

**Phase 8: Full Page Set & Generic Connector Framework** — every page in Section 19, generic MCP Connector Framework from Section 20.

---

## 16. Design & UX Direction

Light dashboard, SaaS-grade visual quality (Linear/Vercel/Stripe tier) without copying any of them, "AI futuristic" feel via one signature animation rather than scattered effects.

**Color**
- Base: `#FAFAFC`, panel surfaces `#F1F3F8`.
- Ink: `#10131C` (primary text).
- Bullish/buy: `#0F9B8E` (deep teal). Bearish/sell: `#FF3B5C` (vivid red-pink).
- AI/reasoning accent: `#00F5D4` (neon teal) — used only where the system itself is "thinking" (agent pipeline, advisory generation state, chart highlights, glow focus states).

**Typography**
- One grotesk sans-serif for UI and headlines (General Sans / Söhne / Inter family), real optical weights.
- Tabular figures for all numeric data (prices, pips, percentages, confidence scores).
- Sentence case section titles, no all-caps tracked-out eyebrows.

**Layout**
- Left-hand navigation rail (Watchlist, Advisories, Knowledge Base, Settings), not a top nav bar.
- Modular but not uniform-card-grid main canvas: chart panel, advisory feed panel, reasoning trail panel each get distinct visual treatment.
- Left-aligned throughout; no centered marketing hero.

```
┌───────┬──────────────────────────────────────────────┬────────────────┐
│  Nav  │  Chart / Price Structure Panel                │  Reasoning     │
│  Rail │  (candles, order blocks, key levels)          │  Trail Panel   │
│       │                                                │  (live agent   │
│  •    │                                                │   pipeline)    │
│  •    ├──────────────────────────────────────────────┤                │
│  •    │  Advisory Feed (this pair, most recent first) │                │
└───────┴──────────────────────────────────────────────┴────────────────┘
```

**Motion — one signature moment**
- "Evaluate Setup" triggers the Reasoning Trail panel lighting up the four agents in order, each completing with a brief neon-teal glow before the next begins, ending in the advisory card sliding into the feed.
- Everywhere else, motion is restrained. Reduced-motion preference respected throughout.

**Avoids:** the near-black-background-plus-neon-accent cliché (neon lives on a light canvas here instead), identical rounded-card grids with uniform shadows, middle-dot metadata strings, spaced-em-dash labels, monospace data labels, arrow glyphs on buttons.

---

## 17. Brand Kit

**Name: Pipsentry** — "pip" (the unit of price movement in forex) + "sentry" (something that watches continuously).

**Tagline options**
- "Every pip, watched."
- "Your edge, always awake."
- "The market never sleeps. Neither does this."
- "Read the market before it moves."

**Logo concept:** rounded badge in neon teal (`#00F5D4`) containing two abstract candlestick bars in dark ink, beside the wordmark in ink navy (`#10131C`), same grotesk sans as the product. Simple enough to work as a 32px favicon/app icon.

**Color tokens** (shared with dashboard, Section 16): Base `#FAFAFC` · Panel `#F1F3F8` · Ink `#10131C` · Bullish `#0F9B8E` · Bearish `#FF3B5C` · AI/reasoning accent `#00F5D4`.

**Type:** One grotesk sans-serif family across logo, UI, and marketing. Medium weight wordmark, regular weight body. Tabular figures for all financial numbers.

**Voice:** Direct, precise, calm — the way a trading terminal should sound. No hype language. State what the system found and why. Errors/warnings are specific and actionable, never vague.

---

## 19. Pages & Information Architecture

**Core**
1. Dashboard (Home) — today's advisories, watchlist snapshot, token budget status, quick links.
2. Watchlist — add/remove tracked symbols, per-symbol alert rules.
3. Advisory Feed — full history, filterable by symbol/timeframe/status/outcome/date range.
4. Advisory Detail — chart, rationale, full four-agent reasoning trail, SL/TP outcome once known.
5. Chart Workspace — full price/structure chart with order blocks and key levels, multi-timeframe side by side.

**Market Context**
6. Economic Calendar — upcoming high-impact events by currency, countdown to no-trade-zone blackout.
7. News & Sentiment — aggregated headlines with AI sentiment score per currency.
8. Currency Strength Meter — relative strength of the eight major currencies, live.
9. Correlation Matrix — cross-pair correlation table.
10. Session Clock — Asian/London/New York session times and overlaps.
11. COT Positioning — CFTC Commitment of Traders report data, weekly institutional positioning.

**Knowledge & Strategy**
12. Knowledge Hub — ingest/manage YouTube/PDF/TXT sources (Section 6).
13. Strategy Library — every strategy extracted from ingested knowledge, tagged by school, individually enabled/disabled, own backtest performance.
14. Backtest & Validation — run/review historical replays and scorecards per strategy (Section 9).

**Trading Tools**
15. Position Size Calculator — lot size and risk-per-trade from account balance, stop distance, risk %.
16. Trade Journal — manual log of trades actually taken, separate from AI advisories.
17. Performance Analytics — win rate, expectancy, equity curve, drawdown by strategy/symbol/timeframe, exportable.

**Platform**
18. Connectors — manage built-in and user-added MCP servers (Section 20).
19. Alerts & Notification Settings — Telegram linking, quiet hours, per-symbol/severity rules.
20. Account & Billing — profile, subscription tier, token budget usage, API usage.
21. Onboarding Wizard — connect a data feed, ingest a first knowledge source, set a watchlist, link Telegram.
22. Help & Disclaimer — documentation, ToS, financial disclaimer (Section 14).

---

## 20. User-Configurable MCP Connector Framework

- On the Connectors page, a user registers any MCP server: name, endpoint URL, credentials (encrypted per Section 11), category tag (market data, broker read-only feed, news, custom).
- On registration, the backend calls that server's tool-discovery endpoint and records exposed tools, no code change needed per new server.
- Agent 1 (Macro) and Agent 2 (Technical) dynamically pull in connected MCP tools relevant to their category, alongside built-in ForexFactory/TwelveData/OANDA sources.
- The Reasoning Trail panel shows, per advisory, exactly which connected sources contributed to that read.
- Each connector gets a scheduled health check; broken/unauthenticated connectors show clear status rather than silently degrading advisory quality.

**On "every forex strategy in the world":** no fixed list can guarantee full coverage. The Knowledge Hub ingests whatever the user feeds it, and the Strategy Library turns that into organized, individually trackable strategies — genuinely open ingestion plus a page to manage what's been taught.

---

## 21. Decisions

- **Auth provider:** Clerk.
- **LLM split:** DeepSeek-R1 for Agents 1–3, Claude Sonnet for Agent 4 (as spec'd).
- **Instrument scope:** forex majors for MVP (schema does not hardcode this — `watchlists.symbol` is a free-text field, so minors/indices/crypto can be added later without a migration).
- **Billing:** deferred to Phase 7 per roadmap; `subscriptions` table exists from day one so no schema migration is needed later.
