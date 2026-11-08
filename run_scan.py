import os
import asyncio

from telegram import Bot
from scanner import scan_top_signals
from storage import init_db, save_signal
from formatter import format_signal


async def main():

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    init_db()

    signals = await asyncio.to_thread(
        scan_top_signals
    )

    async with Bot(token=token) as bot:

        if not signals:

            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "🔎 Baaritaan waa dhammaaday.\n\n"
                    "Maanta lama helin coin buuxiyey "
                    "shuruudaha A+ VIP.\n\n"
                    "💎 Sug baaritaanka xiga."
                )
            )

            return

        sent = 0

        for signal in signals[:3]:

            if save_signal(signal):

                await bot.send_message(
                    chat_id=chat_id,
                    text=format_signal(signal),
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )

                sent += 1

        if sent == 0:

            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "ℹ️ Signals-kii hore ayaa hore loo diray. "
                    "Signal cusub lama helin."
                )
            )


if __name__ == "__main__":
    asyncio.run(main())
