"""Penyimpanan ke Neon Postgres. Semua penulisan idempoten (ON CONFLICT DO NOTHING)."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from analyzer.models import Candle

CHUNK_ROWS = 500  # 500 baris x 10 kolom = 5.000 parameter, jauh di bawah batas Postgres

_INSERT_CANDLES = (
    "INSERT INTO candles "
    "(market, symbol, timeframe, ts, open, high, low, close, volume, source) "
    "VALUES {values} ON CONFLICT (market, symbol, timeframe, ts) DO NOTHING"
)
_INSERT_ISSUES = (
    "INSERT INTO data_quality_log (market, symbol, timeframe, ts, issue, detail) VALUES {values}"
)
_INSERT_RUN = (
    "INSERT INTO ingest_runs "
    "(job, started_at, finished_at, status, rows_written, api_calls, error) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
)
_MAX_TS = "SELECT max(ts) FROM candles WHERE market = %s AND symbol = %s AND timeframe = %s"


def _chunks[T](items: Sequence[T], size: int) -> Iterator[Sequence[T]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _placeholders(columns: int, rows: int) -> str:
    one = "(" + ",".join(["%s"] * columns) + ")"
    return ",".join([one] * rows)


class NeonStore:
    def __init__(self, conn: Any) -> None:
        self._conn = conn

    @classmethod
    def connect(cls, url: str) -> NeonStore:
        return cls(psycopg.connect(url, connect_timeout=20))

    def close(self) -> None:
        self._conn.close()

    def get_max_ts(self, market: str, symbol: str, timeframe: str) -> datetime | None:
        row = self._conn.execute(_MAX_TS, (market, symbol, timeframe)).fetchone()
        return row[0] if row else None

    def insert_candles(self, candles: Sequence[Candle]) -> int:
        """Tulis candle. Mengembalikan jumlah baris yang benar-benar baru."""
        inserted = 0
        for chunk in _chunks(candles, CHUNK_ROWS):
            params = [
                value
                for c in chunk
                for value in (
                    c.market,
                    c.symbol,
                    c.timeframe,
                    c.ts,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume,
                    c.source,
                )
            ]
            sql = _INSERT_CANDLES.format(values=_placeholders(10, len(chunk)))
            inserted += max(self._conn.execute(sql, params).rowcount, 0)
        self._conn.commit()
        return inserted

    def insert_issues(self, issues: Sequence[dict[str, Any]]) -> int:
        """Tulis catatan kualitas data ke data_quality_log."""
        written = 0
        for chunk in _chunks(issues, CHUNK_ROWS):
            params = [
                value
                for row in chunk
                for value in (
                    row["market"],
                    row["symbol"],
                    row["timeframe"],
                    row["ts"],
                    row["issue"],
                    Jsonb(row["detail"]),
                )
            ]
            sql = _INSERT_ISSUES.format(values=_placeholders(6, len(chunk)))
            written += max(self._conn.execute(sql, params).rowcount, 0)
        self._conn.commit()
        return written

    def log_run(
        self,
        job: str,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        rows_written: int,
        api_calls: int,
        error: str | None,
    ) -> None:
        self._conn.execute(
            _INSERT_RUN,
            (job, started_at, finished_at, status, rows_written, api_calls, error),
        )
        self._conn.commit()
