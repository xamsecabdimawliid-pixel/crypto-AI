# AI Crypto Telegram Signals Bot

A research/alert bot for liquid USDT spot pairs.

It scans Binance, Bybit and OKX every 15 minutes and sends at most three qualifying setups to Telegram.

## Important limitations

- This starter uses technical rules. It does not promise a 70–80% win rate.
- The score is a checklist score, not a probability of winning.
- It sends alerts only. It does not place orders.
- No exchange trading API keys are needed.
- The included SQLite database tracks alerts, but automatic outcome labeling and backtesting are not yet implemented.
- Do not interpret /stats as a validated win rate until outcomes are reliably recorded.

## Signal rules

15-minute completed candles:

- EMA 20/50/200 trend
- RSI 50–68
- MACD bullish
- Price above rolling VWAP
- Volume above 1.15x 20-candle average
- Higher close

At least 75/100 checklist score is required.

ATR defines a provisional stop loss and two targets.

## Run locally

1. Install Python 3.11 or newer.
2. Create a Telegram bot using @BotFather.
3. Copy your Telegram bot token.
4. Copy .env.example to .env.
5. Fill in your token and numeric Telegram chat ID.
6. Install dependencies:

   pip install -r requirements.txt

7. Start the bot:

   python main.py

## Telegram commands

/start - Start the bot

/scan - Run a scan now

/stats - View tracked signal statistics

/help - Show help

## Deploy to Render

1. Upload this project to GitHub.
2. In Render, create a Background Worker.
3. Connect your GitHub repository.
4. Build command:

   pip install -r requirements.txt

5. Start command:

   python main.py

6. Add the environment variables shown in .env.example.
7. Add a persistent disk mounted at /var/data if you want SQLite data to survive restarts.
8. Deploy and check worker logs.

Never publish your Telegram bot token or commit your .env file.

## Risk sizing

RISK_PERCENT is a risk budget setting, not a recommendation to risk that amount.

Position size depends on account equity, entry-to-stop distance, fees and slippage. Calculate it separately and consider paper trading first.

## Before using real money

- Add proper backtesting with fees, spread and slippage.
- Add forward paper-trading.
- Add automatic signal outcome resolution.
- Validate across different market conditions and exchanges.
- Do not assume past results guarantee future performance.
