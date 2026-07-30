"""Thin wrapper around the Twelve Data free-tier API: symbol search, live
quotes, and daily history — with in-memory TTL caching shared across every
player, so a classroom of concurrent users doesn't blow through the free
rate limit (the data itself is only refreshed every QUOTE_TTL seconds
anyway, so per-user polling never needs to reach the API directly).
"""
import os
import time
import requests

API_KEY = os.environ.get("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"

QUOTE_TTL = 30          # seconds a cached quote stays valid
HISTORY_TTL = 60 * 60    # seconds a cached daily-history series stays valid
SEARCH_TTL = 60 * 60     # seconds a cached search result stays valid

_cache = {}  # key -> (expires_at, value)


class MarketDataError(Exception):
    pass


def _cached(key, ttl, fetch_fn):
    entry = _cache.get(key)
    if entry and entry[0] > time.time():
        return entry[1]
    value = fetch_fn()
    _cache[key] = (time.time() + ttl, value)
    return value


def _get(endpoint, params):
    if not API_KEY:
        raise MarketDataError("TWELVE_DATA_API_KEY is not set")
    params = {**params, "apikey": API_KEY}
    try:
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        raise MarketDataError(f"Market data request failed: {e}") from e
    if isinstance(data, dict) and data.get("status") == "error":
        raise MarketDataError(data.get("message", "Unknown API error"))
    return data


def search_symbols(query):
    query = query.strip()
    if not query:
        return []

    def fetch():
        data = _get("symbol_search", {"symbol": query})
        results = data.get("data", [])
        # Keep it to common stock listings, not every warrant/ETF variant
        filtered = [
            r for r in results
            if r.get("instrument_type") == "Common Stock"
        ]
        return [
            {"symbol": r["symbol"], "name": r["instrument_name"], "exchange": r.get("exchange")}
            for r in (filtered or results)[:15]
        ]

    return _cached(f"search:{query.lower()}", SEARCH_TTL, fetch)


def get_quote(symbol):
    symbol = symbol.upper()

    def fetch():
        data = _get("price", {"symbol": symbol})
        if "price" not in data:
            raise MarketDataError(f"No price found for {symbol}")
        return float(data["price"])

    return _cached(f"quote:{symbol}", QUOTE_TTL, fetch)


def get_daily_history(symbol, outputsize=30):
    symbol = symbol.upper()

    def fetch():
        data = _get("time_series", {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": outputsize,
        })
        values = data.get("values", [])
        # Twelve Data returns newest-first; charts want oldest-first
        closes = [float(v["close"]) for v in reversed(values)]
        if not closes:
            raise MarketDataError(f"No history found for {symbol}")
        return closes

    return _cached(f"history:{symbol}:{outputsize}", HISTORY_TTL, fetch)
