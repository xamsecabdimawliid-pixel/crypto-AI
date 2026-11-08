import os
import pandas as pd

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "5"))


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

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - previous).abs(),
        (df["low"] - previous).abs()
    ], axis=1).max(axis=1)

    return tr.ewm(
        alpha=1 / period, adjust=False
    ).mean()


def trend_up(df):
    if len(df) < 55:
        return False

    close = df["close"]
    e20 = ema(close, 20)
    e50 = ema(close, 50)

    return bool(
        close.iloc[-1] > e20.iloc[-1]
        and e20.iloc[-1] > e50.iloc[-1]
        and e50.iloc[-1] > e50.iloc[-6]
    )


def analyze_market(frames):

    required = ["15m", "1h", "4h", "5h", "1d"]

    if not isinstance(frames, dict):
        return None

    if any(k not in frames for k in required):
        return None

    data = {}

    for key in required:
        df = frames[key].copy()

        if len(df) < 60:
            return None

        # Ka tag candle-ka aan weli dhammaan
        data[key] = df.iloc[:-1].copy()

        if len(data[key]) < 55:
            return None

    m15 = data["15m"]
    h1 = data["1h"]
    h4 = data["4h"]
    h5 = data["5h"]
    d1 = data["1d"]

    daily = trend_up(d1)
    four_hour = trend_up(h4)
    five_hour = trend_up(h5)
    hourly = trend_up(h1)
    fifteen_min = trend_up(m15)

    close = m15["close"]
    rsi_value = rsi(close)
    atr_value = atr(m15)

    macd = ema(close, 12) - ema(close, 26)
    macd_signal = ema(macd, 9)

    volume_average = m15["volume"].rolling(20).mean()

    entry = float(close.iloc[-1])
    current_rsi = float(rsi_value.iloc[-1])
    current_atr = float(atr_value.iloc[-1])

    if current_atr <= 0 or entry <= 0:
        return None

    volume_confirm = (
        float(m15["volume"].iloc[-1])
        > float(volume_average.iloc[-1])
    )

    breakout = (
        entry > float(m15["high"].iloc[-21:-1].max())
    )

    rsi_confirm = 50 <= current_rsi <= 70

    macd_confirm = (
        macd.iloc[-1] > macd_signal.iloc[-1]
    )

    checks = {
        "Daily trend bullish": daily,
        "4H trend bullish": four_hour,
        "5H trend bullish": five_hour,
        "1H trend bullish": hourly,
        "15M trend bullish": fifteen_min,
        "RSI wanaagsan": rsi_confirm,
        "MACD bullish": macd_confirm,
        "Volume kordhay": volume_confirm,
        "Breakout xaqiijiyey": breakout
    }

    score = round(
        sum(checks.values()) / len(checks) * 100
    )

    # Daily iyo 4H waa shuruudo khasab ah
    if not daily or not four_hour:
        return None

    if score >= 90:
        grade = "A+"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B+"
    elif score >= 60:
        grade = "B"
    else:
        return None

    stop = entry - (1.5 * current_atr)
    risk_distance = entry - stop

    return {
        "grade": grade,
        "score": score,
        "entry": entry,
        "stop_loss": stop,
        "take_profit_1": entry + risk_distance * 1.5,
        "take_profit_2": entry + risk_distance * 2.5,
        "take_profit_3": entry + risk_distance * 3.5,
        "rsi": current_rsi,
        "atr_pct": current_atr / entry * 100,
        "checks": checks,
        "risk_percent": RISK_PERCENT,
        "holding_estimate": "La soco 15M ilaa 5H"
    }
