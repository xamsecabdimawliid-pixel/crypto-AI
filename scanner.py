import os
import ccxt
import pandas as pd

from strategy import analyze_market

EXCHANGES = os.getenv(
    "EXCHANGES", "binance,bybit,okx"
).split(",")

MIN_VOLUME = 5_000_000
MAX_SYMBOLS = 15


def format_price(value):
    """Convert scientific notation to normal decimal price."""
    if value is None:
        return "N/A"

    try:
        value = float(value)

        if not pd.notna(value):
            return "N/A"

        return f"{value:.15f}".rstrip("0").rstrip(".")

    except (ValueError, TypeError):
        return str(value)


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

        if market.get("quote") != "USDT":
            continue

        ticker = tickers.get(symbol) or {}

        volume = ticker.get("quoteVolume") or 0

        if volume < MIN_VOLUME:
            continue

        candidates.append((symbol, market, volume))

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

                # Format signal prices without scientific notation
                for key in (
                    "entry", "stop_loss",
                    "sl", "tp1", "tp2", "tp3"
                ):
                    if key in signal and signal[key] is not None:
                        signal[key] = format_price(signal[key])

                exchange_names = {
                    "binance": "BINANCE",
                    "bybit": "BYBIT",
                    "okx": "OKX"
                }

                prefix = exchange_names.get(
                    exchange_id, exchange_id.upper()
                )

                market_id = market["id"]

                signal["tradingview_url"] = (
                    "https://www.tradingview.com/chart/?symbol="
                    f"{prefix}%3A{market_id}"
                )

                results.append(signal)

        except Exception as error:
            print(f"{symbol}: {error}")

    return results


def scan_top_signals():

    results = []

    for name in EXCHANGES:
        exchange_id = name.strip().lower()

        try:
            results.extend(scan_exchange(exchange_id))
        except Exception as error:
            print(f"{exchange_id}: {error}")

    results.sort(
        key=lambda x: (
            x.get("score", 0),
            x.get("quote_volume", 0)
        ),
        reverse=True
    )

    unique_coins = []
    seen_coins = set()

    for signal in results:
        symbol = signal.get("symbol", "")
        base_coin = symbol.split("/")[0]

        if base_coin in seen_coins:
            continue

        seen_coins.add(base_coin)
        unique_coins.append(signal)

        if len(unique_coins) == 3:
            break

    return unique_coins
