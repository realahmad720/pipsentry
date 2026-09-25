"""CFTC Commitment of Traders — weekly institutional positioning (Section 19
page 11). Public, free, no key needed: the CFTC's own Socrata "Legacy"
Futures-Only report (dataset `6dca-aqww` on publicreporting.cftc.gov).

Field names and market names below (e.g. "EURO FX - CHICAGO MERCANTILE
EXCHANGE") were confirmed directly against the live endpoint, not guessed.
NZD has no consistently-reported legacy contract in this dataset, so it's
left out rather than silently mapped to something wrong.
"""

import httpx

COT_BASE_URL = "https://publicreporting.cftc.gov/resource/6dca-aqww.json"

_CURRENCY_MARKET_NAMES = {
    "EUR": "EURO FX - CHICAGO MERCANTILE EXCHANGE",
    "GBP": "BRITISH POUND - CHICAGO MERCANTILE EXCHANGE",
    "JPY": "JAPANESE YEN - CHICAGO MERCANTILE EXCHANGE",
    "AUD": "AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "CAD": "CANADIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE",
    "CHF": "SWISS FRANC - CHICAGO MERCANTILE EXCHANGE",
}


class CotError(Exception):
    pass


def fetch_cot_positioning(currency: str) -> dict:
    market_name = _CURRENCY_MARKET_NAMES.get(currency.upper())
    if market_name is None:
        raise CotError(f"No CFTC legacy contract mapped for {currency!r}")

    params = {
        "$where": f"market_and_exchange_names = '{market_name}'",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 1,
    }
    response = httpx.get(COT_BASE_URL, params=params, timeout=15.0)
    response.raise_for_status()
    rows = response.json()
    if not rows:
        raise CotError(f"CFTC returned no rows for {market_name!r}")

    row = rows[0]
    noncomm_long = int(row["noncomm_positions_long_all"])
    noncomm_short = int(row["noncomm_positions_short_all"])
    return {
        "currency": currency.upper(),
        "market_name": market_name,
        "report_date": row["report_date_as_yyyy_mm_dd"][:10],
        "noncommercial_long": noncomm_long,
        "noncommercial_short": noncomm_short,
        "noncommercial_net": noncomm_long - noncomm_short,
        "commercial_long": int(row["comm_positions_long_all"]),
        "commercial_short": int(row["comm_positions_short_all"]),
        "open_interest": int(row["open_interest_all"]),
    }


def supported_currencies() -> list[str]:
    return sorted(_CURRENCY_MARKET_NAMES.keys())
