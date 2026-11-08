import os
import asyncio

from telegram import Bot

from scanner import scan_top_signals
from formatter import format_signal


async def main():

    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    print("Bilowga baaritaanka coins...")

    signals = await asyncio.to_thread(
        scan_top_signals
    )

    async with Bot(token=token) as bot:

        if not signals:

            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "🔎 Baaritaanka waa dhammaaday.\n\n"
                    "Maanta lama helin coin buuxiyey "
                    "shuruudaha A+, A, B+ ama B.\n\n"
                    "💎 Sug baaritaanka xiga."
                )
            )

            print("Signal lama helin.")
            return

        for signal in signals[:3]:

            await bot.send_message(
                chat_id=chat_id,
                text=format_signal(signal),
                parse_mode="HTML",
                disable_web_page_preview=True
            )

            print(
                f"Signal la diray: "
                f"{signal['symbol']} {signal['grade']}"
            )


if __name__ == "__main__":
    asyncio.run(main())
