import sqlite3
import os

DB_PATH = os.getenv("DB_PATH", "signals.db")


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                exchange TEXT,
                timeframe TEXT,
                entry REAL,
                stop_loss REAL,
                tp1 REAL,
                tp2 REAL,
                score INTEGER,
                created_at TEXT,
                status TEXT DEFAULT 'OPEN',
                outcome TEXT DEFAULT ''
            )
        """)


def save_signal(s):
    init_db()

    with connect() as con:
        cur = con.execute(
            """
            SELECT id FROM signals
            WHERE symbol=? AND exchange=? AND status='OPEN'
            ORDER BY id DESC LIMIT 1
            """,
            (s["symbol"], s["exchange"])
        )

        if cur.fetchone():
            return False

        con.execute(
            """
            INSERT INTO signals (
                symbol, exchange, timeframe, entry,
                stop_loss, tp1, tp2, score, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                s["symbol"],
                s["exchange"],
                s["timeframe"],
                s["entry"],
                s["stop_loss"],
                s["take_profit_1"],
                s["take_profit_2"],
                s["score"]
            )
        )

        return True


def get_stats():
    init_db()

    with connect() as con:
        total = con.execute(
            "SELECT COUNT(*) FROM signals"
        ).fetchone()[0]

        closed, wins, losses = con.execute(
            """
            SELECT
                COUNT(*),
                SUM(outcome='WIN'),
                SUM(outcome='LOSS')
            FROM signals
            WHERE status='CLOSED'
            """
        ).fetchone()

    wins = wins or 0
    losses = losses or 0

    decided = wins + losses

    return {
        "total": total,
        "closed": closed,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / decided * 100, 1) if decided else 0
    }
