"""Cache fundamental ke SQLite lokal (prototipe D1). Skema identik dengan tabel D1 nanti."""
import json
import sqlite3
import time
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS fundamentals (
    ticker      TEXT PRIMARY KEY,
    fetched_at  INTEGER NOT NULL,
    payload     TEXT NOT NULL,
    verdict     TEXT NOT NULL
);
"""

TTL_SECONDS = 24 * 3600


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.execute(SCHEMA)
    return con


def get_fresh(con: sqlite3.Connection, ticker: str) -> dict[str, Any] | None:
    """Return payload+verdict jika cache masih segar, selain itu None."""
    row = con.execute(
        "SELECT fetched_at, payload, verdict FROM fundamentals WHERE ticker = ?",
        (ticker,),
    ).fetchone()
    if row is None:
        return None
    fetched_at, payload, verdict = row
    if time.time() - fetched_at > TTL_SECONDS:
        return None
    return {"payload": json.loads(payload), "verdict": json.loads(verdict)}


def put(con: sqlite3.Connection, ticker: str, payload: dict, verdict: list[str]) -> None:
    con.execute(
        "INSERT OR REPLACE INTO fundamentals (ticker, fetched_at, payload, verdict) VALUES (?, ?, ?, ?)",
        (ticker, int(time.time()), json.dumps(payload), json.dumps(verdict)),
    )
    con.commit()
