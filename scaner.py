import os
import ccxt
import pandas as pd

from strategy import analyze_market

EXCHANGES = [
    x.strip().lower()
    for x in os.getenv(
        "EXCHANGES", "binance,bybit,okx"
    ).split(",")
    if x.strip()
]

QUOTE = os.getenv("QUOTE_CURRENCY", "USDT")

MIN_24H_VOLUME = float(
    os.getenv("MIN_24H_QUOTE_VOLUME", "5000000")
)

MAX_SYMBOLS = int(
    os.getenv("MAX_SYMBOLS_PER_EXCHANGE", "10")
)


def _to_frame(candles):
    return pd.DataFrame(
        candles,
        columns=[
            "timestamp", "open", "high",
            "low", "close", "volume"
        ]
    )


def _five_hour_from_hourly(hourly):

    data = hourly.copy()

    data["time"] = pd.to_datetime(
        data["timestamp"],
        unit="ms",
        utc=True
    )

    data = data.set_index("time")

    result = data.resample(
        "5h",
        label="right",
        closed="right"
    ).agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "timestamp": "last"
    }).dropna()

    return result.reset_index(drop=True)[
        ["timestamp", "open", "high", "low", "close", "volume"]
    ]


def _fetch_frames(exchange, symbol):

    hourly = _to_frame(
        exchange.fetch_ohlcv(
            symbol,
            timeframe="1h",
            limit=1000
        )
    )

    frames = {
        "15m": _to_frame(
            exchange.fetch_ohlcv(
                symbol, timeframe="15m", limit=220
            )
        ),

        "1h": hourly,

        "4h": _to_frame(
            exchange.fetch_ohlcv(
                symbol, timeframe="4h", limit=220
            )
        ),

        "5h": _five_hour_from_hourly(hourly),

        "1d": _to_frame(
            exchange.fetch_ohlcv(
                symbol, timeframe="1d", limit=220
            )
        )
    }

    return frames


def _tradingview_url(exchange_id, market):

    exchange_names = {
        "binance": "BINANCE",
        "bybit": "BYBIT",
        "okx": "OKX"
    }

    prefix = exchange_names.get(
        exchange_id.lower(),
        exchange_id.upper()
    )

    market_id = market.get("id", "").replace("/", "").replace(":", "")

    return (
        "https://www.tradingview.com/chart/?symbol="
        f"{prefix}%3A{market_id}"
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

        if not market.get("spot"):
            continue

        if not market.get("active", True):
            continue

        if market.get("quote") != QUOTE:
            continue

        if market.get("base") == QUOTE:
            continue

        ticker = tickers.get(symbol) or {}

        quote_volume = ticker.get("quoteVolume")

        if quote_volume is None:
            last = ticker.get("last")
            base_volume = ticker.get("baseVolume")

            quote_volume = (last or 0) * (base_volume or 0)

        if quote_volume and float(quote_volume) >= MIN_24H_VOLUME:
            candidates.append(
                (symbol, market, float(quote_volume))
            )

    candidates.sort(
        key=lambda item: item[2],
        reverse=True
    )

    results = []

    for symbol, market, quote_volume in candidates[:MAX_SYMBOLS]:

        try:
            frames = _fetch_frames(exchange, symbol)

            signal = analyze_market(frames)

            if signal:

                signal.update({
                    "symbol": symbol,
                    "exchange": exchange_id.upper(),
                    "quote_volume": quote_volume,
                    "timeframe": "15M / 1H / 4H / 5H / 1D",
                    "tradingview_url": _tradingview_url(
                        exchange_id, market
                    )
                })

                results.append(signal)
