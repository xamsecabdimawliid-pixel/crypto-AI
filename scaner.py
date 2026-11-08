import ccxt
import pandas as pd
from urllib.parse import quote

from strategy import analyze_market

EXCHANGES = ["binance", "bybit", "okx"]

MIN_VOLUME = 5_000_000
MAX_SYMBOLS = 20

# Stablecoins laga reebayo
STABLECOINS = {
    "USDT", "USDC", "BUSD", "DAI", "TUSD",
    "FDUSD", "USDE", "USDS", "USDP", "PYUSD",
    "USDD", "FRAX", "LUSD", "GUSD", "USD1",
    "EURC", "EURS", "USTC", "UST", "USDX",
    "USDE", "USDJ", "SUSD", "CUSD"
}

# Leveraged tokens laga reebayo
BAD_SUFFIXES = (
    "UP", "DOWN", "BULL", "BEAR",
    "3L", "3S", "5L", "5S"
)

TV_EXCHANGES = {
    "binance": "BINANCE",
    "bybit": "BYBIT",
    "okx": "OKX"
}


def to_frame(candles):
    return pd.DataFrame(
        candles,
        columns=[
            "timestamp", "open", "high",
            "low", "close", "volume"
        ]
    )


def make_5h(hourly):

    df = hourly.copy()

    df["time"] = pd.to_datetime(
        df["timestamp"], unit="ms", utc=True
    )

    df = df.set_index("time")

    result = df.resample(
        "5h", label="right", closed="right"
    ).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "timestamp": "last"
    }).dropna()

    return result.reset_index(drop=True)


def get_frames(exchange, symbol):

    hourly = to_frame(
        exchange.fetch_ohlcv(
            symbol, "1h", limit=1000
        )
    )

    return {
        "15m": to_frame(exchange.fetch_ohlcv(
            symbol, "15m", limit=220
        )),
        "1h": hourly,
        "4h": to_frame(exchange.fetch_ohlcv(
            symbol, "4h", limit=220
        )),
        "5h": make_5h(hourly),
        "1d": to_frame(exchange.fetch_ohlcv(
            symbol, "1d", limit=220
        ))
    }


def is_good_coin(market):

    base = market.get("base", "").upper()

    if base in STABLECOINS:
        return False

    if any(base.endswith(x) for x in BAD_SUFFIXES):
        return False

    if market.get("quote") != "USDT":
        return False

    if not market.get("spot"):
        return False

    if not market.get("active", True):
        return False

    return True


def tradingview_link(exchange_id, market):

    exchange_name = TV_EXCHANGES.get(exchange_id)

    if not exchange_name:
        return ""

    symbol = market["id"].replace("/", "").replace(":", "")

    tv_symbol = f"{exchange_name}:{symbol}"

    return (
        "https://www.tradingview.com/chart/?symbol="
        + quote(tv_symbol, safe="")
    )


def scan_exchange(exchange_id):

    exchange_class = getattr(ccxt, exchange_id)

    exchange = exchange_class({
        "enableRateLimit": True,
        "timeout": 30000,
        "options": {"defaultType": "spot"}
    })

    markets = exchange.load_markets()
    tickers = exchange.fetch_tickers()

    candidates = []

    for symbol, market in markets.items():

        if not is_good_coin(market):
            continue

        ticker = tickers.get(symbol) or {}

        volume = ticker.get("quoteVolume") or 0

        if volume < MIN_VOLUME:
            continue

        candidates.append((symbol, market, float(volume)))

    candidates.sort(
        key=lambda x: x[2],
        reverse=True
    )

    results = []

    for symbol, market, volume in candidates[:MAX_SYMBOLS]:

        try:
            frames = get_frames(exchange, symbol)

            signal = analyze_market(frames)

            if signal:

                signal["symbol"] = symbol
                signal["exchange"] = exchange_id.upper()
                signal["quote_volume"] = volume
                signal["tradingview_url"] = tradingview_link(
                    exchange_id, market
                )

                if signal["tradingview_url"]:
                    results.append(signal)

        except Exception as error:
            print(f"{symbol}: {error}")

    return results


def scan_top_signals():

    results = []

    for exchange_id in EXCHANGES:

        try:
            results.extend(scan_exchange(exchange_id))except Exception as error:
            print(f"{exchange_id}: {error}")

    results.sort(
        key=lambda x: (x["score"], x["quote_volume"]),
        reverse=True
    )

    return results[:3]
