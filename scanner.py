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
MIN_QUOTE_VOLUME = float(
    os.getenv("MIN_24H_QUOTE_VOLUME", "500000")
)
TIMEFRAME = os.getenv("TIMEFRAME", "15m")
MAX_SYMBOLS = int(
    os.getenv("MAX_SYMBOLS_PER_EXCHANGE", "100")
)


def scan_exchange(exchange_id):
    exchange_class = getattr(ccxt, exchange_id)

    exchange = exchange_class({
        "enableRateLimit": True,
        "options": {"defaultType": "spot"}
    })

    markets = exchange.load_markets()
    tickers = exchange.fetch_tickers()
    results = []

    for symbol, market in markets.items():
        if not market.get("spot"):
            continue

        if not market.get("active", True):
            continue

        if market.get("quote") != QUOTE:
            continue

        ticker = tickers.get(symbol) or {}
        volume = ticker.get("quoteVolume") or 0

        if volume < MIN_QUOTE_VOLUME:
            continue

        try:
            candles = exchange.fetch_ohlcv(
                symbol,
                timeframe=TIMEFRAME,
                limit=250
            )

            if len(candles) < 210:
                continue

            df = pd.DataFrame(
                candles,
                columns=[
                    "timestamp", "open", "high",
                    "low", "close", "volume"
                ]
            )

            signal = analyze_market(df)

            if signal and signal["score"] >= 75:
                signal.update({
                    "symbol": symbol,
                    "exchange": exchange_id.upper(),
                    "quote_volume": volume,
                    "timeframe": TIMEFRAME
                })

                results.append(signal)

        except Exception:
            continue

    return results


def scan_top_signals():
    results = []

    for exchange_id in EXCHANGES:
        try:
            results.extend(scan_exchange(exchange_id))
        except Exception as error:
            print(f"{exchange_id} error: {error}")

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:3]
