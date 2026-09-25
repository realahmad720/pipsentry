import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import configure_logging
from app.core.rate_limit import RateLimitMiddleware
from app.routers import (
    account,
    advisories,
    backtest,
    connectors,
    health,
    knowledge,
    market_context,
    telegram,
    trade_journal,
    watchlists,
)

configure_logging("DEBUG" if settings.environment == "development" else "INFO")

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1, environment=settings.environment)

app = FastAPI(title="Pipsentry API", version="0.1.0")

# Order matters: Starlette makes the most-recently-added middleware outermost,
# so CORS must be added last — otherwise a 429 from RateLimitMiddleware never
# gets CORS headers attached and shows up in the browser as a CORS failure
# instead of a rate limit.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(watchlists.router)
app.include_router(advisories.router)
app.include_router(knowledge.router)
app.include_router(backtest.router)
app.include_router(telegram.router)
app.include_router(connectors.router)
app.include_router(trade_journal.router)
app.include_router(market_context.router)
app.include_router(account.router)
