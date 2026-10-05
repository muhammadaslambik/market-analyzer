from datetime import UTC, datetime

from analyzer.models import Candle
from analyzer.store.neon import CHUNK_ROWS, NeonStore

T0 = datetime(2026, 1, 1, tzinfo=UTC)


class FakeCursor:
    def __init__(self, rowcount: int = 0, row: tuple | None = None) -> None:
        self.rowcount = rowcount
        self._row = row

    def fetchone(self) -> tuple | None:
        return self._row


class FakeConn:
    def __init__(self, max_ts: datetime | None = None) -> None:
        self.calls: list[tuple[str, object]] = []
        self.commits = 0
        self._max_ts = max_ts

    def execute(self, sql: str, params: object = None) -> FakeCursor:
        self.calls.append((sql, params))
        if sql.startswith("SELECT max(ts)"):
            return FakeCursor(row=(self._max_ts,))
        n_values = sql.count("(%s")
        return FakeCursor(rowcount=n_values)

    def commit(self) -> None:
        self.commits += 1

    def close(self) -> None:
        pass


def _candles(n: int) -> list[Candle]:
    return [
        Candle(
            "crypto",
            "BTCUSDT",
            "1h",
            datetime.fromtimestamp(1767225600 + i * 3600, UTC),
            1.0,
            2.0,
            0.5,
            1.5,
            3.0,
            "uji",
        )
        for i in range(n)
    ]


def test_insert_candles_dipecah_per_chunk_dan_idempoten() -> None:
    conn = FakeConn()
    store = NeonStore(conn)
    inserted = store.insert_candles(_candles(CHUNK_ROWS * 2 + 100))
    assert inserted == CHUNK_ROWS * 2 + 100
    assert len(conn.calls) == 3
    conflict = "ON CONFLICT (market, symbol, timeframe, ts) DO NOTHING"
    assert all(conflict in sql for sql, _ in conn.calls)
    assert len(conn.calls[0][1]) == CHUNK_ROWS * 10  # type: ignore[arg-type]
    assert conn.commits == 1


def test_insert_candles_kosong_tidak_memanggil_database() -> None:
    conn = FakeConn()
    assert NeonStore(conn).insert_candles([]) == 0
    assert conn.calls == []


def test_insert_issues_membungkus_detail_json() -> None:
    conn = FakeConn()
    row = {
        "market": "crypto",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "ts": T0,
        "issue": "gap",
        "detail": {"missing": 2},
    }
    assert NeonStore(conn).insert_issues([row]) == 1
    sql, params = conn.calls[0]
    assert "data_quality_log" in sql
    assert params[5].obj == {"missing": 2}  # type: ignore[index]


def test_get_max_ts() -> None:
    assert NeonStore(FakeConn(max_ts=T0)).get_max_ts("crypto", "BTCUSDT", "1h") == T0
    assert NeonStore(FakeConn(max_ts=None)).get_max_ts("crypto", "BTCUSDT", "1h") is None


def test_log_run_menulis_ingest_runs() -> None:
    conn = FakeConn()
    NeonStore(conn).log_run("backfill", T0, T0, "ok", 10, 3, None)
    sql, params = conn.calls[0]
    assert "ingest_runs" in sql and params == ("backfill", T0, T0, "ok", 10, 3, None)
    assert conn.commits == 1
