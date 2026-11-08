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

    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "💎 <b>VIP ALTCOIN SIGNAL</b> 💎\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🪙 <b>Coin:</b> {escape(s['symbol'])}\n"
        f"🏦 <b>Suuqa:</b> {escape(s['exchange'])} SPOT\n"
        f"{emoji} <b>Heerka:</b> {s['grade']}\n"
        f"⭐ <b>Score:</b> {s['score']}/100\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📍 <b>QIIMAHA GELITAANKA</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🟢 ENTRY: <code>{fmt(s['entry'])}</code>\n"
        f"🛑 STOP LOSS (-5%): <code>{fmt(s['stop_loss'])}</code>\n\n"
        f"🎯 TP1 (+5%): <code>{fmt(s['take_profit_1'])}</code>\n"
        f"🎯 TP2 (+10%): <code>{fmt(s['take_profit_2'])}</code>\n"
        f"🚀 TP3 (+20%): <code>{fmt(s['take_profit_3'])}</code>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 <b>FAAHFAAHINTA SUUQA</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 24H Volume: ${s['quote_volume']:,.0f}\n"
        f"📈 RSI: {s['rsi']:.1f}\n"
        f"🔥 Daily ATR: {s['daily_atr_pct']:.2f}%\n"
        "⏱ Timeframes: 15M | 1H | 4H | 5H | 1D\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🔍 <b>SHURUUDAHA LA BUUXIYEY</b>\n"
        f"{passed}\n\n"
        f"📈 <a href=\"{s['tradingview_url']}\">FUR COINKA TRADINGVIEW</a>\n\n"
        "⚠️ TP20% waa bartilmaameed, ma aha ballanqaad. "
        "SL5% waa qiimaha ka bixitaanka ee la qorsheeyey.\n"
        "━━━━━━━━━━━━━━━━━━"
    )
