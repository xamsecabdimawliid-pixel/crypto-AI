import asyncio
import logging
import os
from telegram.ext import Application, CommandHandler
from scanner import scan_top_signals
from storage import init_db, save_signal, get_stats
from formatter import format_signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("crypto_bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
SCAN_MINUTES = int(os.getenv("SCAN_MINUTES", "15"))


async def scan_job(context):
    try:
        signals = await asyncio.to_thread(scan_top_signals)
        sent = 0

        for signal in signals[:3]:
            if save_signal(signal):
                msg = format_signal(signal)
                if CHAT_ID:
                    await context.bot.send_message(
                        chat_id=CHAT_ID,
                        text=msg,
                        parse_mode="HTML",
                        disable_web_page_preview=True
                    )
                sent += 1

        log.info("Scan complete. New signals: %s", sent)

    except Exception:
        log.exception("Scheduled scan failed")


async def start(update, context):
    await update.message.reply_text(
        "Welcome to AI Crypto Signals (Spot).\n"
        "Commands: /scan - scan now, /stats - tracked signal results, /help - help.\n"
        "Signals are research alerts, not guaranteed returns."
    )


async def scan_cmd(update, context):
    await update.message.reply_text(
        "Scanning USDT spot markets. This may take a minute..."
    )

    try:
        signals = await asyncio.to_thread(scan_top_signals)

        if not signals:
            await update.message.reply_text(
                "No setup passed the filters. No trade is better than a weak signal."
            )
            return

        for s in signals[:3]:
            await update.message.reply_text(
                format_signal(s),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
            save_signal(s)

    except Exception as e:
        log.exception("Manual scan failed")
        await update.message.reply_text(
            f"Scan failed: {type(e).name}. Check Render logs."
        )


async def stats_cmd(update, context):
    stats = get_stats()

    await update.message.reply_text(
        f"Tracked signals: {stats['total']}\n"
        f"Closed: {stats['closed']} | Wins: {stats['wins']} | Losses: {stats['losses']}\n"
        f"Observed win rate: {stats['win_rate']}%\n"
        "Win rate is meaningful only after enough closed, non-overlapping signals."
    )


async def help_cmd(update, context):
    await update.message.reply_text(
        "/start - welcome\n"
        "/scan - run a scan now\n"
        "/stats - view tracked signal stats\n"
        "Automatic scan runs every 15 minutes. Spot only; no exchange trading keys are needed."
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "Set TELEGRAM_BOT_TOKEN in Render environment variables."
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("help", help_cmd))

    app.job_queue.run_repeating(
        scan_job,
        interval=SCAN_MINUTES * 60,
        first=15
    )

    log.info("Bot starting; scan interval=%s minutes", SCAN_MINUTES)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
