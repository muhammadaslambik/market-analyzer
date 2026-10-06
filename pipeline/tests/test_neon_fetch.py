from datetime import UTC, datetime, timedelta, timezone

from analyzer.store.neon import NeonStore

T0 = datetime(2026, 1, 1, tzinfo=UTC)


class Cursor:
    def __init__(self, rows: list[tuple]) -> None:
        self._rows = rows

    def fetchall(self) -> list[tuple]:
        return self._rows


class Conn:
    def __init__(self, rows: list[tuple]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple = ()) -> Cursor:
        self.calls.append((sql, params))
        return Cursor(self.rows)


def test_fetch_candles_membangun_candle_utc() -> None:
    wib = timezone(timedelta(hours=7))
    rows = [(T0.astimezone(wib), "100", "110", "90", "105", "5", "binance-vision")]
    conn = Conn(rows)
    candles = NeonStore(conn).fetch_candles("crypto", "BTCUSDT", "1h")
    assert len(candles) == 1
    candle = candles[0]
    assert candle.ts == T0 and candle.ts.utcoffset() == timedelta(0)
    assert (candle.open, candle.close, candle.source) == (100.0, 105.0, "binance-vision")
    sql, params = conn.calls[0]
    assert "FROM candles" in sql and "ORDER BY ts" in sql
    assert params[:3] == ("crypto", "BTCUSDT", "1h")


def test_fetch_candles_meneruskan_batas_waktu() -> None:
    conn = Conn([])
    start, end = T0, T0 + timedelta(days=1)
    assert NeonStore(conn).fetch_candles("crypto", "BTCUSDT", "1h", start, end) == []
    assert conn.calls[0][1][3:] == (start, end)
