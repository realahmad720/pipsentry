# Pipsentry

AI-driven forex intelligence & advisory copilot. Advisory only — this system never places trades. See [docs/SPEC.md](docs/SPEC.md) for the full build specification.

## Repo layout

```
apps/
  web/   Next.js dashboard (Clerk auth, design tokens from the brand kit)
  api/   FastAPI backend (Postgres via SQLAlchemy/Alembic, per-tenant Qdrant)
docs/
  SPEC.md  Full build spec (architecture, data model, agents, roadmap)
```

## Status

Phase 1 (Environment & Foundation) of the roadmap in `docs/SPEC.md` Section 15:

- [x] FastAPI service skeleton, CORS, health check
- [x] Postgres schema (users, subscriptions, ingested_sources, watchlists, advisories, alert_deliveries, usage_counters, audit_log) via SQLAlchemy models + initial Alembic migration
- [x] Qdrant per-tenant collection helper (`kb_{user_id}` namespacing)
- [x] Clerk JWT verification wired into the API, `get_current_user` dependency scopes every query by tenant
- [x] Next.js dashboard shell: nav rail, brand color tokens as CSS variables, tabular numerals for financial data, Clerk sign-in/sign-up

Phase 2 (Knowledge Ingestion Engine), spec Section 6:

- [x] YouTube ingestion: `youtube-transcript-api` first, falling back to yt-dlp's own caption tracks (`app/ingestion/youtube.py`)
- [x] PDF/TXT upload (`POST /knowledge/sources/upload`), stored locally under `apps/api/uploads/{user_id}/` (swap for S3 before running >1 API instance)
- [x] Chunking: `RecursiveCharacterTextSplitter`, exact 1,000/150 token sizing via `tiktoken` (`app/ingestion/chunking.py`)
- [x] Embeddings: OpenAI `text-embedding-3-small`, written into the tenant's Qdrant collection (`app/ingestion/embeddings.py`)
- [x] Purge/reindex per source (`POST /knowledge/sources/{id}/reindex`), and vector cleanup on delete
- [x] Knowledge Hub dashboard page (`/knowledge`): YouTube URL form, drag-and-drop upload, live status table (polls while any source is `pending`)
- [ ] Whisper audio transcription fallback for videos with no captions at all — intentionally left out (pulls in torch/ffmpeg); the extraction interface is already shaped so it slots in later without touching callers
- [ ] Background job queue (Celery/Redis or Render Cron) — ingestion currently runs as a FastAPI `BackgroundTask` in-process, which is correct for MVP volume but won't survive a process restart mid-ingestion or scale past a single instance (Section 12)

Phase 3 (Market Data Feeds & MCP Bridge), spec Section 3:

- [x] TwelveData client (`app/marketdata/twelvedata.py`) — candles, quote, and a date-ranged history fetch for backtesting
- [x] Economic calendar (`app/marketdata/forexfactory.py`) — ForexFactory has no official API or working RSS feed anymore; this consumes the same static JSON snapshot the ForexFactory widget itself uses, called out explicitly rather than silently pretending to parse RSS. Verified live against the real feed.
- [x] Surprise-based macro sentiment scoring (`app/marketdata/sentiment.py`) — deterministic, not headline NLP; see its docstring for the seam a real NLP model would plug into
- [x] Read-only market-data MCP server (`app/marketdata/mcp_server.py`, `python -m app.marketdata.mcp_server`) exposing candles/quote/calendar/sentiment as MCP tools
- [x] CFTC Commitment of Traders (`app/marketdata/cot.py`), currency strength (`currency_strength.py`) and correlation matrix (`correlation.py`) — all real computations against live public data, verified against the live endpoints during this build
- [ ] OANDA/MT5 read-only feeds named alongside TwelveData in the spec — not wired in; both need a live brokerage account this scaffold has no credentials for. A user's own OANDA/MT5 bridge is meant to come in through the Phase 8 connector framework instead.

Phase 4 (Multi-Agent Logic Assembly), spec Section 7:

- [x] LangGraph wiring for all four agents (`app/agents/graph.py`): Agents 1+2 fan out in parallel, then Agent 3, then a budget gate, then Agent 4
- [x] Agent 1 Macro & News, Agent 2 Technical & Price Action, Agent 3 Strategy & RAG Retriever on DeepSeek-R1; Agent 4 Risk & Synthesis Auditor on Claude Sonnet (Section 21)
- [x] Conflict resolution rule (`app/agents/conflict.py`) and the 1:2 minimum risk:reward gate are computed in Python, not left to the model — narrated by Claude, never decided by it
- [x] Token budget middleware (`app/agents/budget.py`) — checks `usage_counters` against `subscriptions.monthly_token_budget` before Agent 4 runs; `STATUS: BUDGET_EXCEEDED` short-circuits instead of degrading quality
- [x] `POST /advisories/evaluate` — runs the full pipeline, persists + delivers the advisory
- [ ] Real SMC order-block/fair-value-gap detection — Agent 2 reasons over ATR/RSI/SMA/swing levels instead, a coarser read than the spec's own ICT-style example payload; documented in `app/agents/agent_technical.py`
- [ ] Scheduled candle-close polling — evaluation is on-demand only (the "Evaluate Setup" button), not a background scheduler; that's a queue-backed job (Section 12), out of scope here

Phase 5 (Backtesting & Validation), spec Section 9:

- [x] Historical replay harness (`app/backtest/harness.py`) — one position at a time, walks forward to see whether SL or TP hits first
- [x] Advisory scorecard (win rate, avg R-multiple, max drawdown) and the positive-expectancy gate (`app/backtest/scorecard.py`, `gate.py`)
- [x] `POST /backtest/run`
- [ ] Replaying the real four-agent LLM pipeline candle-by-candle — cost-prohibitive (thousands of paid LLM calls per run over a 6-month window); the harness instead replays a deterministic SMA-cross/ATR reference strategy (`app/backtest/strategy.py`), with the LLM pipeline swappable in later behind the same `signal_fn` seam

Phase 6 (Delivery Surface & Forward Testing), spec Section 6/9.3:

- [x] Telegram bot delivery (`app/delivery/telegram.py`, `dispatch.py`) — one platform bot, per-user chat id linked via a self-expiring Fernet code (`GET /telegram/link-code`, `POST /telegram/webhook`), chat id encrypted at rest (Section 11)
- [x] Advisory outcome grading against the live quote (`app/delivery/outcomes.py`)
- [x] 3-week forward paper test per watchlist entry (`app/delivery/forward_test.py`, `POST /watchlists/{id}/forward-test/start`) — graded by the same expectancy gate as the backtest, against real delivered advisories
- [ ] Quiet hours / per-symbol severity alert rules — no preference storage for these in the data model; the Alerts settings page says so rather than faking a toggle

Phase 7 (Multi-Tenant Hardening & Launch), spec Section 11:

- [x] Row-level tenant isolation tests (`apps/api/tests/test_tenant_isolation.py`) — need a real Postgres (Postgres-only column types), so they skip cleanly in a sandbox without Docker and run for real via `docker compose up -d`
- [x] Pure-logic test suite for the conflict rule, risk:reward math, and the expectancy gate (`tests/test_agent_logic.py`) — runs anywhere, no DB/network/LLM key needed
- [x] In-memory rate limiting middleware (`app/core/rate_limit.py`) — per-process; needs Redis once the API runs on more than one instance
- [x] JSON structured logging (`app/core/logging.py`) and Sentry init (inert until `SENTRY_DSN` is set)
- [x] Financial disclaimer + ToS content (`/help`) — a template, not a substitute for legal review before opening to paying users across jurisdictions
- [ ] Stripe billing — explicitly deferred (Section 21); `subscriptions`/usage data is real and surfaced on `/account`, there's just no payment flow behind it yet

Phase 8 (Full Page Set & Generic Connector Framework), spec Sections 19/20:

- [x] All 22 pages from Section 19 exist and are wired to real endpoints — Dashboard, Watchlist, Advisory Feed/Detail, Chart Workspace (hand-rolled SVG candlesticks, no charting dependency), Economic Calendar, News & Sentiment, Currency Strength, Correlation Matrix, Session Clock, COT Positioning, Knowledge Hub, Strategy Library, Backtest & Validation, Position Size Calculator, Trade Journal, Performance Analytics, Connectors, Alerts & Notifications, Account & Billing, Onboarding, Help & Disclaimer
- [x] Generic MCP connector framework (`app/connectors/mcp_bridge.py`, `/connectors`) — register any MCP server, it's discovered (tool list + health) over the real MCP client protocol on registration and on demand
- [x] Trade journal and account/usage endpoints backing their pages (`trade_journal_entries` table, `/account`)
- [ ] Strategy Library has no dedicated `strategies` table — strategies are derived read-only from Knowledge Hub source tags, with no persisted enable/disable state (documented on the page itself)
- [ ] Discovered connector tools aren't fed into Agent 1/2's reasoning pass yet — safely bridging an arbitrary, unknown-shaped external tool into a pipeline that must still produce our fixed advisory JSON is a harder, separate problem; what's real today is discovery, health checks, and category tagging

## Local development

Prerequisites: Docker, Node 20+, Python 3.12+.

```bash
docker compose up -d
```

### Backend (`apps/api`)

```bash
cd apps/api
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend (`apps/web`)

```bash
cd apps/web
npm install
copy .env.example .env.local
npm run dev
```

Fill in `CLERK_SECRET_KEY` / `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` (web) and `CLERK_JWKS_URL` / `CLERK_SECRET_KEY` (api) from your Clerk instance before auth will work end to end.

For the full pipeline beyond auth + knowledge ingestion, also set: `TWELVEDATA_API_KEY` (candles/quotes — most of the Chart Workspace, Agent 2, backtesting, and the currency strength/correlation pages depend on this), `ANTHROPIC_API_KEY` + `DEEPSEEK_API_KEY` (Agents 1–4), and `FIELD_ENCRYPTION_KEY` (generate with the command in `.env.example`) before Telegram linking or connector credentials will work. The economic calendar and CFTC COT pages need no keys — both hit free public endpoints.

## Decisions locked in (spec Section 21)

- Auth: Clerk
- LLM split: DeepSeek-R1 for Agents 1–3, Claude Sonnet for Agent 4
- Instrument scope: forex majors for MVP (schema is symbol-agnostic, so this is a config choice, not a migration)
- Billing: deferred to Phase 7; `subscriptions` table exists from day one
