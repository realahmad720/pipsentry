"""Read-only market-data MCP server (Phase 3 / Section 3: "MCP server
integration"). Exposes Pipsentry's built-in TwelveData + economic-calendar
feeds as MCP tools any MCP client (Claude Desktop, another agent) can attach
to over stdio.

The in-process agents (app/agents/*) do NOT call through this server — they
call `twelvedata.py` / `forexfactory.py` / `sentiment.py` directly, since
round-tripping their own built-in tools through the MCP wire protocol would
add latency and a subprocess dependency for no benefit. This server exists
for *external* consumers of Pipsentry's data, and to give the generic
connector framework (Section 20 / Phase 8) a first real example of the
MCP-server shape a user-registered connector also has.

Run standalone: `python -m app.marketdata.mcp_server`
"""

from dataclasses import asdict

from mcp.server.mcpserver import MCPServer

from app.marketdata import forexfactory, sentiment
from app.marketdata.twelvedata import fetch_candles, fetch_quote_price

server = MCPServer(name="pipsentry-market-data", version="0.1.0")


@server.tool()
def get_candles(symbol: str, interval: str = "1h", outputsize: int = 200) -> list[dict]:
    """Fetch OHLC candles for a forex pair (e.g. "EURUSD") from TwelveData."""
    return [
        {**asdict(c), "time": c.time.isoformat()} for c in fetch_candles(symbol, interval, outputsize)
    ]


@server.tool()
def get_quote(symbol: str) -> dict:
    """Fetch the latest traded price for a forex pair."""
    return {"symbol": symbol, "price": fetch_quote_price(symbol)}


@server.tool()
def get_economic_calendar(currency: str | None = None, hours_ahead: int = 24) -> list[dict]:
    """List upcoming high-impact economic calendar events, optionally filtered
    to one currency (e.g. "USD")."""
    from datetime import timedelta

    events = forexfactory.fetch_calendar()
    upcoming = forexfactory.upcoming_high_impact(events, currency, timedelta(hours=hours_ahead))
    return [
        {
            "title": e.title,
            "country": e.country,
            "impact": e.impact,
            "event_time": e.event_time.isoformat(),
            "forecast": e.forecast,
            "previous": e.previous,
            "actual": e.actual,
        }
        for e in upcoming
    ]


@server.tool()
def get_macro_sentiment(currency: str) -> dict:
    """Surprise-based macro sentiment score (-1..1) for a single currency,
    from recently released economic prints. See marketdata/sentiment.py."""
    return {"currency": currency, "score": sentiment.macro_sentiment_score(currency)}


if __name__ == "__main__":
    server.run(transport="stdio")
