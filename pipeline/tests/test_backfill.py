from datetime import UTC, datetime, timedelta

import pytest

from analyzer.jobs.backfill import floor_to_interval, run_backfill
from analyzer.models import Candle, interval_of
from analyzer.sources.base import SourceBlockedError, SourceError

T0 = datetime(2026, 1, 1, tzinfo=UTC)
NOW = T0 + timedelta(hours=250, minutes=30)


class FakeSource:
    name = "fake"

    def __init__(
        self,
        drop: set[datetime] | None = None,
        blocked: bool = False,
        fail_symbols: tuple[str, ...] = (),
    ) -> None:
        self.api_calls = 0
        self.calls: list[tuple[str, str, datetime, datetime]] = []
        self.drop = drop or set()
        self.blocked = blocked
        self.fail_symbols = fail_symbols

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        now: datetime | None = None,
    ) -> list[Candle]:
        self.api_calls += 1
        self.calls.append((symbol, timeframe, start, end))
        if self.blocked:
            raise SourceBlockedError("451")
        if symbol in self.fail_symbols:
            raise SourceError("gagal")
        interval = interval_of(timeframe)
        out = []
        ts = floor_to_interval(start, timeframe)
        if ts < start:
            ts += interval
        while ts < end:
            if ts + interval <= (now or end) and ts not in self.drop:
                out.append(
                    Candle("crypto", symbol, timeframe, ts, 100.0, 110.0, 90.0, 105.0, 1.0, "fake")
                )
            ts += interval
        return out


class FakeStore:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str, str, datetime], Candle] = {}
        self.issues: list[dict] = []

    def get_max_ts(self, market: str, symbol: str, timeframe: str) -> datetime | None:
        times = [k[3] for k in self.rows if k[:3] == (market, symbol, timeframe)]
        return max(times) if times else None

    def insert_candles(self, candles) -> int:
        new = 0
        for c in candles:
            key = (c.market, c.symbol, c.timeframe, c.ts)
            if key not in self.rows:
                self.rows[key] = c
                new += 1
        return new

    def insert_issues(self, issues) -> int:
        self.issues.extend(issues)
        return len(issues)


def _run(source, store, symbols=("BTCUSDT",), **kw):
    return run_backfill(source, store, symbols, ["1h"], {"1h": T0}, NOW, log=lambda _: None, **kw)


def test_backfill_baru_lalu_idempoten() -> None:
    source, store = FakeSource(), FakeStore()
    first = _run(source, store, ("BTCUSDT", "ETHUSDT"))
    assert first.status == "ok" and first.inserted == 2 * 250
    second = _run(FakeSource(), store, ("BTCUSDT", "ETHUSDT"), full=True)
    assert second.inserted == 0 and len(store.rows) == 500


def test_resume_mulai_dari_candle_terakhir() -> None:
    store = FakeStore()
    _run(FakeSource(), store)
    later = NOW + timedelta(hours=10)
    source = FakeSource()
    summary = run_backfill(
        source, store, ["BTCUSDT"], ["1h"], {"1h": T0}, later, log=lambda _: None
    )
    last_before = T0 + timedelta(hours=249)
    assert source.calls[0][2] == last_before  # mulai dari candle terakhir, bukan dari awal
    assert summary.inserted == 10


def test_jendela_kecil_banyak_panggilan_dan_celah_batas_terdeteksi() -> None:
    boundary = T0 + timedelta(hours=100)
    source, store = FakeSource(drop={boundary}), FakeStore()
    summary = _run(source, store, window_candles=100)
    assert source.api_calls > 2
    gaps = [i for i in store.issues if i["issue"] == "gap"]
    assert len(gaps) == 1 and gaps[0]["ts"] == boundary
    assert summary.reports[0].issues == 1


def test_diblokir_menghentikan_semuanya() -> None:
    summary = _run(FakeSource(blocked=True), FakeStore(), ("BTCUSDT", "ETHUSDT"))
    assert summary.status == "error" and len(summary.reports) == 1


def test_satu_simbol_gagal_simbol_lain_tetap_jalan() -> None:
    store = FakeStore()
    summary = _run(FakeSource(fail_symbols=("BTCUSDT",)), store, ("BTCUSDT", "ETHUSDT"))
    assert summary.status == "partial"
    assert summary.reports[0].error and summary.reports[1].inserted == 250


def test_window_terlalu_kecil_ditolak() -> None:
    with pytest.raises(ValueError):
        _run(FakeSource(), FakeStore(), window_candles=1)
