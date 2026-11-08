from html import escape


def fmt(value):
    return f"{value:.8g}"


def format_signal(s):

    grade_emojis = {
        "A+": "💎",
        "A": "🟢",
        "B+": "🔵",
        "B": "🟡"
    }

    emoji = grade_emojis.get(s["grade"], "📊")

    passed = "\n".join(
        f"✅ {name}"
        for name, value in s["checks"].items()
        if value
    )

    symbol = escape(s["symbol"])
    exchange = escape(s["exchange"])

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>VIP CRYPTO SIGNAL</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 <b>Coin:</b> {symbol}\n"
        f"🏦 <b>Exchange:</b> {exchange} SPOT\n"
        f"{emoji} <b>Heerka:</b> {s['grade']}\n"
        f"⭐ <b>Score:</b> {s['score']}/100\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📍 <b>QIIMAHA GELITAANKA</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🟢 Entry: <code>{fmt(s['entry'])}</code>\n"
        f"🛑 Stop Loss: <code>{fmt(s['stop_loss'])}</code>\n\n"
        f"🎯 TP1: <code>{fmt(s['take_profit_1'])}</code>\n"
        f"🎯 TP2: <code>{fmt(s['take_profit_2'])}</code>\n"
        f"🚀 TP3: <code>{fmt(s['take_profit_3'])}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>FAAHFAAHINTA SUUQA</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 24H Volume: ${s['quote_volume']:,.0f}\n"
        f"📈 RSI: {s['rsi']:.1f}\n"
        f"📉 ATR: {s['atr_pct']:.2f}%\n"
        f"⏱ Timeframes: 15M | 1H | 4H | 5H | 1D\n"
        f"⚠️ Risk setting: {s['risk_percent']}%\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔍 <b>SHURUUDAHA LA BUUXIYEY</b>\n"
        f"{passed}\n\n"
        f"📈 <a href=\"{s['tradingview_url']}\">FUR TRADINGVIEW</a>\n\n"
        "⚠️ Fiiro gaar ah: Score ma aha win rate. "
        "Hubi qiimaha iyo khatarta ka hor gelitaanka.\n"
        "━━━━━━━━━━━━━━━━━━"
    )
