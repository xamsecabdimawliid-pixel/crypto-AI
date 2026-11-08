import os
import pandas as pd

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "5"))

if RISK_PERCENT not in (1, 2, 3, 5):
    RISK_PERCENT = 5


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(
        alpha=1 / period, adjust=False
    ).mean()
    loss = (-delta.clip(upper=0)).ewm(
        alpha=1 / period, adjust=False
    ).mean()
    rs = gain / loss.replace(0, 1e-12)
    return 100 - (100 / (1 + rs))


def atr(df, period=14):
    previous = df["close"].shift(1)

    true_range = pd.concat([
        df["high"] - df["low"],
        (df["high"] - previous).abs(),
        (df["low"] - previous).abs()
    ], axis=1).max(axis=1)

    return true_range.ewm(
        alpha=1 / period, adjust=False
    ).mean()


def _valid_frame(frame, minimum=60):
    return isinstance(frame, pd.DataFrame) and len(frame) >= minimum


def _trend(frame, fast=20, slow=50):
    close = frame["close"]
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)

    return bool(
        close.iloc[-1] > fast_ema.iloc[-1] > slow_ema.iloc[-1]
        and slow_ema.iloc[-1] > slow_ema.iloc[-6]
    )


def analyze_market(frames):

    required = ("15m", "1h", "4h", "5h", "1d")

    if not isinstance(frames, dict):
        return None

    if any(k not in frames for k in required):
        return None

    if any(not _valid_frame(frames[k]) for k in required):
        return None

    m15, h1, h4, h5, d1 = (
        frames[k].copy() for k in required
    )

    # Ka saar candle-ka aan weli dhammaan.
    m15, h1, h4, h5, d1 = (
        x.iloc[:-1].copy()
        for x in (m15, h1, h4, h5, d1)
    )

    if any(len(x) < 55 for x in (m15, h1, h4, h5, d1)):
        return None

    daily_trend = (
        _trend(d1, 20, 50)
        and d1["close"].iloc[-1] > ema(d1["close"], 200).iloc[-1]
        if len(d1) >= 205
        else _trend(d1, 20, 50)
    )

    four_hour_trend = _trend(h4)
    five_hour_trend = _trend(h5)
    hourly_trend = _trend(h1)

    close = m15["close"]
    rsi15 = rsi(close)

    macd = ema(close, 12) - ema(close, 26)
    macd_signal = ema(macd, 9)

    volume_avg = m15["volume"].rolling(20).mean()
    atr15 = atr(m15)

    entry = float(close.iloc[-1])

    breakout_level = m15["high"].iloc[-21:-1].max()

    volume_confirm = (
        float(m15["volume"].iloc[-1])
        >= 1.2 * float(volume_avg.iloc[-1])
    )

    breakout_confirm = entry > float(breakout_level)

    rsi_confirm = 52 <= float(rsi15.iloc[-1]) <= 70

    macd_confirm = macd.iloc[-1] > macd_signal.iloc[-1]

    m15_trend = _trend(m15)

    checks = {
        "Jihada Daily bullish": daily_trend,
        "Trend 4H bullish": four_hour_trend,
        "Trend 5H bullish": five_hour_trend,
        "Trend 1H bullish": hourly_trend,
        "Trend 15M bullish": m15_trend,
        "RSI 15M ku habboon": rsi_confirm,
        "MACD 15M bullish": macd_confirm,
        "Volume kordhay": volume_confirm,
        "Breakout 20 candles": breakout_confirm
    }

    score = round(
        sum(bool(v) for v in checks.values())
        / len(checks) * 100
    )

    # A+ wuxuu u baahan yahay in dhammaan shuruudaha la buuxiyo.
    if score < 90 or not all(checks.values()):
        return None

    atr_now = float(atr15.iloc[-1])

    if not atr_now or atr_now <= 0:
        return None

    stop = entry - 1.5 * atr_now
    risk_per_unit = entry - stop

    return {
        "score": score,
        "entry": entry,
        "stop_loss": stop,
        "take_profit_1": entry + 1.5 * risk_per_unit,
        "take_profit_2": entry + 2.5 * risk_per_unit,
        "take_profit_3": entry + 3.5 * risk_per_unit,
        "rsi": float(rsi15.iloc[-1]),
        "atr_pct": atr_now / entry * 100,
        "checks": checks,
        "risk_percent": RISK_PERCENT,
        "holding_estimate": "Dib u eeg 15M; muddada hayntu waxay ku xiran tahay suuqa"
    }
