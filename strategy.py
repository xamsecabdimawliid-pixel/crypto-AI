import os
import pandas as pd

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "2"))

if RISK_PERCENT not in (1, 2, 3):
    RISK_PERCENT = 2


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0).ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = gain / loss.replace(0, 1e-12)

    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    prev = df["close"].shift(1)

    tr = pd.concat([
        (df["high"] - df["low"]),
        (df["high"] - prev).abs(),
        (df["low"] - prev).abs()
    ], axis=1).max(axis=1)

    return tr.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


def analyze_market(df):
    # Use only completed candles.
    d = df.iloc[:-1].copy()

    if len(d) < 205:
        return None

    close = d["close"]
    vol = d["volume"]

    e20 = ema(close, 20)
    e50 = ema(close, 50)
    e200 = ema(close, 200)

    r = rsi(close)

    macd = ema(close, 12) - ema(close, 26)
    macd_signal = ema(macd, 9)

    vwap20 = (
        (d["close"] * d["volume"]).rolling(20).sum()
        / d["volume"].rolling(20).sum()
    )

    vol_avg = vol.rolling(20).mean()
    a = atr(d)

    price = float(close.iloc[-1])
    atr_now = float(a.iloc[-1])

    if not price or not atr_now:
        return None

    checks = {
        "EMA trend": (
            e20.iloc[-1] > e50.iloc[-1] > e200.iloc[-1]
        ),
        "RSI momentum": (
            50 <= r.iloc[-1] <= 68
        ),
        "MACD bullish": (
            macd.iloc[-1] > macd_signal.iloc[-1]
        ),
        "VWAP support": (
            price > vwap20.iloc[-1]
        ),
        "Volume confirmation": (
            vol.iloc[-1] > 1.15 * vol_avg.iloc[-1]
        ),
        "Higher close": (
            close.iloc[-1] > close.iloc[-2]
        )
    }

    score = int(
        sum(checks.values()) / len(checks) * 100
    )

    if score < 75:
        return None

    entry = price
    stop = entry - 1.5 * atr_now

    risk = entry - stop

    tp1 = entry + 1.5 * risk
    tp2 = entry + 2.5 * risk

    return {
        "score": score,
        "entry": entry,
        "stop_loss": stop,
        "take_profit_1": tp1,
        "take_profit_2": tp2,
        "rsi": float(r.iloc[-1]),
        "atr_pct": atr_now / price * 100,
        "checks": checks,
        "risk_percent": RISK_PERCENT,
        "holding_estimate": (
            "Review each 15m candle; no fixed holding guarantee"
        )
    }
