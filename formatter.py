def fmt(x):
    return f"{x:.8g}"


def format_signal(s):
    passed = [
        k for k, v in s["checks"].items() if v
    ]

    failed = [
        k for k, v in s["checks"].items() if not v
    ]

    return (
        "🟢 <b>SPOT BUY SETUP — RESEARCH ALERT</b>\n"
        f"<b>{s['symbol']}</b> | {s['exchange']} | {s['timeframe']}\n"
        f"Score: <b>{s['score']}/100</b> (rule score, not win probability)\n\n"
        f"Entry zone: <code>{fmt(s['entry'])}</code>\n"
        f"Stop loss: <code>{fmt(s['stop_loss'])}</code>\n"
        f"Take profit 1: <code>{fmt(s['take_profit_1'])}</code>\n"
        f"Take profit 2: <code>{fmt(s['take_profit_2'])}</code>\n"
        f"24h quote volume: <code>{s['quote_volume']:,.0f} USDT</code>\n"
        f"RSI: {s['rsi']:.1f} | ATR: {s['atr_pct']:.2f}%\n"
        f"Risk setting: {s['risk_percent']}% of account "
        "(position sizing must be calculated separately)\n"
        f"Confirmed: {', '.join(passed) or 'none'}\n"
        f"Not confirmed: {', '.join(failed) or 'none'}\n"
        f"Holding: {s['holding_estimate']}\n\n"
        "⚠️ Educational signal, not financial advice. Prices move quickly; "
        "verify spread, fees, slippage and the live chart. "
        "No guaranteed win rate. Signal expires if price reaches SL "
        "or the setup conditions fail."
    )
