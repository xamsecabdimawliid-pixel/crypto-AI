import pandas as pd
import numpy as np


# ==========================================
# ICT STRATEGY CONFIGURATION
# ==========================================

RISK_REWARD_1 = 1.0
RISK_REWARD_2 = 2.0
RISK_REWARD_3 = 3.0

ATR_PERIOD = 14

EMA_FAST = 20
EMA_SLOW = 50

SWING_LOOKBACK = 10
SETUP_LOOKBACK = 12

DISPLACEMENT_ATR = 1.2
STOP_BUFFER_ATR = 0.2

MIN_DAILY_ATR = 3.5
MIN_SCORE = 70


# ==========================================
# DATA VALIDATION
# ==========================================

def validate_data(df):

    required = [
        "open", "high", "low",
        "close", "volume"
    ]

    if not isinstance(df, pd.DataFrame):
        raise ValueError("Invalid market data")

    if not all(col in df.columns for col in required):
        raise ValueError("Missing OHLCV columns")

    df = df.copy()

    df = df.sort_index()

    for col in required:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        )

    df = df.dropna(subset=required)

    return df


# ==========================================
# EMA
# ==========================================

def ema(series, period):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()


# ==========================================
# RSI
# ==========================================

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


# ==========================================
# ATR
# ==========================================

def atr(df, period=ATR_PERIOD):

    previous = df["close"].shift(1)

    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - previous).abs(),
        (df["low"] - previous).abs()
    ], axis=1).max(axis=1)

    return tr.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()


# ==========================================
# HTF MARKET DIRECTION
# ==========================================

def trend_up(df):

    if len(df) < 55:
        return False

    close = df["close"]

    e20 = ema(close, EMA_FAST)
    e50 = ema(close, EMA_SLOW)

    return bool(
        close.iloc[-1] > e50.iloc[-1]
        and e20.iloc[-1] > e50.iloc[-1]
        and e50.iloc[-1] > e50.iloc[-6]
    )


# ==========================================
# LIQUIDITY SWEEP
# ==========================================

def find_liquidity_sweep(df, start, end):

    for i in range(start, end):

        if i < SWING_LOOKBACK:
            continue

        previous_lows = df["low"].iloc[
            i - SWING_LOOKBACK:i
        ]

        liquidity_level = float(
            previous_lows.min()
        )

        candle_low = float(df["low"].iloc[i])
        candle_close = float(df["close"].iloc[i])

        # Sell-side liquidity sweep
        if (
            candle_low < liquidity_level
            and candle_close > liquidity_level
        ):

            return {
                "index": i,
                "liquidity_level": liquidity_level,
                "sweep_low": candle_low
            }

    return None


# ==========================================
# BULLISH DISPLACEMENT + MSS + FVG
# ==========================================

def find_ict_setup(df):

    if len(df) < 60:
        return None

    df = df.copy()

    df["atr"] = atr(df)

    latest = len(df) - 1

    # Search recent displacement candles
    start = max(
        SWING_LOOKBACK + 2,
        latest - SETUP_LOOKBACK
    )

    for i in range(latest - 1, start - 1, -1):

        candle_open = float(df["open"].iloc[i])
        candle_close = float(df["close"].iloc[i])
        candle_atr = float(df["atr"].iloc[i])

        if candle_atr <= 0:
            continue

        body = candle_close - candle_open

        # Bullish displacement
        displacement = (
            body > 0
            and body >= candle_atr * DISPLACEMENT_ATR
        )if not displacement:
            continue

        # Previous liquidity sweep
        sweep = find_liquidity_sweep(
            df,
            max(SWING_LOOKBACK, i - 10),
            i
        )

        if sweep is None:
            continue

        sweep_index = sweep["index"]

        # Market Structure Shift
        previous_high = float(
            df["high"].iloc[
                max(0, sweep_index - 10):sweep_index
            ].max()
        )

        bullish_mss = candle_close > previous_high

        if not bullish_mss:
            continue

        # Bullish Fair Value Gap
        fvg_low = float(df["high"].iloc[i - 2])
        fvg_high = float(df["low"].iloc[i])

        bullish_fvg = fvg_high > fvg_low

        if not bullish_fvg:
            continue

        # Wait for price to return to FVG
        current = df.iloc[latest]

        entry = (fvg_low + fvg_high) / 2

        retest = (
            float(current["low"]) <= entry
            and float(current["high"]) >= entry
        )

        bullish_rejection = (
            float(current["close"]) > float(current["open"])
            and float(current["close"]) > entry
        )

        if not retest or not bullish_rejection:
            continue

        return {
            "liquidity_sweep": True,
            "bullish_mss": True,
            "displacement": True,
            "bullish_fvg": True,
            "fvg_low": fvg_low,
            "fvg_high": fvg_high,
            "entry": entry,
            "sweep_low": sweep["sweep_low"],
            "setup_index": i
        }

    return None


# ==========================================
# MAIN MARKET ANALYSIS
# ==========================================

def analyze_market(frames):

    required = [
        "15m", "1h", "4h", "5h", "1d"
    ]

    if not isinstance(frames, dict):
        return None

    if any(key not in frames for key in required):
        return None

    data = {}

    try:

        for key in required:

            df = validate_data(frames[key])

            if len(df) < 60:
                return None

            # Ignore incomplete latest candle
            data[key] = df.iloc[:-1].copy()

            if len(data[key]) < 55:
                return None

    except (ValueError, TypeError, KeyError):
        return None

    m15 = data["15m"]
    h1 = data["1h"]
    h4 = data["4h"]
    h5 = data["5h"]
    d1 = data["1d"]

    # ======================================
    # 1. HIGHER TIMEFRAME ANALYSIS
    # ======================================

    daily = trend_up(d1)
    four_hour = trend_up(h4)
    five_hour = trend_up(h5)
    hourly = trend_up(h1)

    # Daily volatility
    daily_atr_value = atr(d1).iloc[-1]

    daily_close = float(d1["close"].iloc[-1])

    if daily_close <= 0:
        return None

    daily_atr_pct = float(
        daily_atr_value / daily_close * 100
    )

    if not np.isfinite(daily_atr_pct):
        return None

    if daily_atr_pct < MIN_DAILY_ATR:
        return None

    # Main HTF direction
    if not daily or not four_hour or not hourly:
        return None

    # ======================================
    # 2. LOWER TIMEFRAME ICT ANALYSIS
    # ======================================

    setup = find_ict_setup(m15)

    if setup is None:
        return None

    # ======================================
    # 3. ENTRY / STOP LOSS
    # ======================================

    entry = float(setup["entry"])

    current_atr = float(atr(m15).iloc[-1])

    stop = (
        float(setup["sweep_low"])
        - current_atr * STOP_BUFFER_ATR
    )

    risk = entry - stop

    if risk <= 0 or entry <= 0:
        return None

    # ======================================
    # 4. TAKE PROFIT
    # ======================================

    target_1 = entry + risk * RISK_REWARD_1

    target_2 = entry + risk * RISK_REWARD_2

    target_3 = entry + risk * RISK_REWARD_3

    # ======================================
    # 5. ADDITIONAL CONFIRMATIONS
    # ======================================
current_rsi = float(
    rsi(m15["close"]).iloc[-1]
)
        

    volume_average = (
        m15["volume"].rolling(20).mean().iloc[-1]
    )

    volume_confirm = (
        float(m15["volume"].iloc[-1])
        > float(volume_average)
        if pd.notna(volume_average)
        else False
    )

    # ======================================
    # 6. ICT CONFLUENCE SCORE
    # ======================================

    checks = {

        "Daily bullish bias": daily,

        "4H bullish bias": four_hour,

        "1H bullish bias": hourly,

        "5H bullish confirmation": five_hour,

        "Sell-side liquidity sweep":
            setup["liquidity_sweep"],

        "Bullish MSS":
            setup["bullish_mss"],

        "Bullish displacement":
            setup["displacement"],

        "Bullish FVG":
            setup["bullish_fvg"],

        "FVG retracement":
            True,

        "Volume confirmation":
            volume_confirm
    }

    score = round(
        sum(checks.values()) / len(checks) * 100
    )

    # ======================================
    # 7. SIGNAL QUALITY
    # ======================================

    if score >= 90:
        grade = "A+"

    elif score >= 80:
        grade = "A"

    elif score >= 70:
        grade = "B+"

    else:
        return None

    # ======================================
    # 8. FINAL SIGNAL
    # ======================================

    return {

        "grade": grade,

        "score": score,

        "direction": "BUY",

        "strategy": "ICT HTF LTF",

        "entry": entry,

        "stop_loss": stop,

        "take_profit_1": target_1,

        "take_profit_2": target_2,

        "take_profit_3": target_3,

        "risk_reward": "1:3",

        "rsi": current_rsi,

        "daily_atr_pct": daily_atr_pct,

        "fvg_low": setup["fvg_low"],

        "fvg_high": setup["fvg_high"],

        "checks": checks,

        "holding_estimate": "15M ilaa 1D"
    }
