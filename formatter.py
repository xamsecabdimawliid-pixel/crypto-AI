def fmt(value):
    return f"{value:.8g}"


def format_signal(signal):

    passed = [
        name
        for name, ok in signal["checks"].items()
        if ok
    ]

    passed_text = "\n".join(
        f"✅ {name}" for name in passed
    )

    return (
        "💎 <b>A+ VIP CRYPTO SIGNAL</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Coin:</b> {signal['symbol']}\n"
        f"🏦 <b>Suuqa:</b> {signal['exchange']} — SPOT\n"
        f"⭐ <b>Tayada gelitaanka:</b> A+ — {signal['score']}/100\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🟢 <b>ENTRY:</b> <code>{fmt(signal['entry'])}</code>\n"
        f"🛑 <b>STOP LOSS:</b> <code>{fmt(signal['stop_loss'])}</code>\n"
        f"🎯 <b>TP1:</b> <code>{fmt(signal['take_profit_1'])}</code>\n"
        f"🎯 <b>TP2:</b> <code>{fmt(signal['take_profit_2'])}</code>\n"
        f"🚀 <b>TP3:</b> <code>{fmt(signal['take_profit_3'])}</code>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Mugga 24-saac:</b> ${signal['quote_volume']:,.0f} USDT\n"
        f"📊 <b>RSI 15M:</b> {signal['rsi']:.1f}\n"
        f"📉 <b>ATR:</b> {signal['atr_pct']:.2f}%\n"
        f"⏱ <b>Waqtiyada:</b> {signal['timeframe']}\n"
        f"⚠️ <b>Risk setting:</b> {signal['risk_percent']}%\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "<b>Shuruudaha la xaqiijiyey:</b>\n"
        f"{passed_text}\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📈 <a href=\"{signal['tradingview_url']}\">Ka fur TradingView</a>\n"
        f"🕒 <b>Muddada haynta:</b> {signal['holding_estimate']}\n\n"
        "⚠️ <b>Digniin:</b> Signal-ku ma dammaanad qaadayo faa'iido "
        "ama win rate. Hubi qiimaha, spread-ka iyo khidmadaha."
    )
