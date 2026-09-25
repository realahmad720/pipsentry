"""TwelveData client — read-only price data (Section 3 "Market Data" row).

OANDA and MT5 read-only feeds are named in the spec alongside TwelveData for
this MCP server, but neither is wired in here: both need a live brokerage
account to authenticate against, which this scaffold has no credentials for.
The tool surface in `mcp_server.py` is shaped so either slots in as another
`get_candles`-style function without touching callers — or, more likely,
a user registers their own OANDA/MT5 read-only bridge through the generic
connector framework (Section 20 / Phase 8) instead of it being built-in here.
"""

from dataclasses import dataclass
from datetime import datetime

import httpx

from app.config import settings

BASE_URL = "https://api.twelvedata.com"


class TwelveDataError(Exception):
    pass


@dataclass
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float


def _require_api_key() -> str:
    if not settings.twelvedata_api_key:
        raise TwelveDataError("TWELVEDATA_API_KEY is not configured")
    return settings.twelvedata_api_key


def to_twelvedata_symbol(symbol: str) -> str:
    """"EURUSD" -> "EUR/USD". Already-slashed or non-6-letter symbols pass through."""
    symbol = symbol.upper().strip()
    if "/" in symbol or len(symbol) != 6:
        return symbol
    return f"{symbol[:3]}/{symbol[3:]}"


def fetch_candles(symbol: str, interval: str, outputsize: int = 200) -> list[Candle]:
    params = {
        "symbol": to_twelvedata_symbol(symbol),
        "interval": interval,
        "outputsize": outputsize,
        "apikey": _require_api_key(),
        "order": "ASC",
    }
    response = httpx.get(f"{BASE_URL}/time_series", params=params, timeout=15.0)
    response.raise_for_status()
    data = response.json()
    if data.get("status") == "error":
        raise TwelveDataError(data.get("message", "TwelveData returned an error"))

    values = data.get("values") or []
    return [
        Candle(
            time=datetime.fromisoformat(v["datetime"]),
            open=float(v["open"]),
            high=float(v["high"]),
            low=float(v["low"]),
            close=float(v["close"]),
        )
        for v in values
    ]


def fetch_candles_range(symbol: str, interval: str, start_date: str, end_date: str) -> list[Candle]:
    """Historical OHLC for a fixed date range (Section 9: "min 6 months"),
    rather than the last N candles. `start_date`/`end_date` are "YYYY-MM-DD"."""
    params = {
        "symbol": to_twelvedata_symbol(symbol),
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "apikey": _require_api_key(),
        "order": "ASC",
    }
    response = httpx.get(f"{BASE_URL}/time_series", params=params, timeout=30.0)
    response.raise_for_status()
    data = response.json()
    if data.get("status") == "error":
        raise TwelveDataError(data.get("message", "TwelveData returned an error"))

    values = data.get("values") or []
    return [
        Candle(
            time=datetime.fromisoformat(v["datetime"]),
            open=float(v["open"]),
            high=float(v["high"]),
            low=float(v["low"]),
            close=float(v["close"]),
        )
        for v in values
    ]


def fetch_quote_price(symbol: str) -> float:
    params = {"symbol": to_twelvedata_symbol(symbol), "apikey": _require_api_key()}
    response = httpx.get(f"{BASE_URL}/price", params=params, timeout=10.0)
    response.raise_for_status()
    data = response.json()
    if "price" not in data:
        raise TwelveDataError(data.get("message", "TwelveData returned no price"))
    return float(data["price"])
