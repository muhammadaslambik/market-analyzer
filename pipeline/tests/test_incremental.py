from datetime import UTC, datetime, timedelta

from analyzer.jobs.backfill import floor_to_interval
from analyzer.jobs.incremental import run_incremental
from analyzer.models import Candle, interval_of
from analyzer.sources.base import SourceBlockedError

T0 = datetime(2026, 1, 1, tzinfo=UTC)
NOW = T0 + timedelta(hours=105, minutes=20)


class FakeSource:
    name = "fake"

    def __init__(self, blocked: bool = False) -> None:
        self.api_calls = 0
        self.blocked = blocked

    def fetch_candles(self, symbol, timeframe, start, end, now=None):
        self.api_calls += 1
        if self.blocked:
            raise SourceBlockedError("451")
        interval = interval_of(timeframe)
        out = []
        ts = floor_to_interval(start, timeframe)
        if ts < start:
            ts += interval
        while ts < end:
            if ts + interval <= (now or end):
                idx = int((ts - T0) / timedelta(hours=1))
                out.append(
                    Candle(
                        "crypto",
                        symbol,
                        timeframe,
                        ts,
                        100.0,
                        300.0,
                        50.0,
                        100.0 + idx,
                        1.0,
                        "fake",
                    )
                )
            ts += interval
        return out


class FakeNeon:
    def __init__(self) -> None:
        self.rows: dict[tuple, Candle] = {}
        self.issues: list = []
        self.runs: list[tuple] = []

    def get_max_ts(self, market, symbol, timeframe):
        times = [k[3] for k in self.rows if k[:3] == (market, symbol, timeframe)]
        return max(times) if times else None

    def get_latest(self, market, symbol, timeframe):
        ts = self.get_max_ts(market, symbol, timeframe)
        if ts is None:
            return None
        c = self.rows[(market, symbol, timeframe, ts)]
        return ts, c.close, c.source

    def insert_candles(self, candles):
        new = 0
        for c in candles:
            key = (c.market, c.symbol, c.timeframe, c.ts)
            if key not in self.rows:
                self.rows[key] = c
                new += 1
        return new

    def insert_issues(self, issues):
        self.issues.extend(issues)
        return len(issues)

    def log_run(self, job, started_at, finished_at, status, rows_written, api_calls, error):
        self.runs.append((job, status, rows_written, error))


class FakeD1:
    def __init__(self, fail: bool = False) -> None:
        self.prices: list[tuple] = []
        self.meta: dict[str, str] = {}
        self.fail = fail

    def upsert_latest_price(self, market, symbol, timeframe, close, asof, source):
        if self.fail:
            raise RuntimeError("D1 menolak query (HTTP 500): x")
        self.prices.append((symbol, close, asof))

    def set_meta(self, key, value):
        self.meta[key] = value


def _seed(neon: FakeNeon, symbol: str, hours: int) -> None:
    for h in range(hours):
        ts = T0 + timedelta(hours=h)
        neon.rows[("crypto", symbol, "1h", ts)] = Candle(
            "crypto", symbol, "1h", ts, 100.0, 300.0, 50.0, 100.0 + h, 1.0, "fake"
        )


def _run(neon, d1, source=None, symbols=("BTCUSDT",)):
    return run_incremental(
        source or FakeSource(), neon, d1, symbols, "1h", "crypto_hourly", NOW, log=lambda _: None
    )


def test_pembaruan_normal_menulis_candle_baru_dan_d1() -> None:
    neon, d1 = FakeNeon(), FakeD1()
    _seed(neon, "BTCUSDT", 100)  # candle terakhir dibuka T0+99h
    result = _run(neon, d1)
    assert result.status == "ok" and result.summary.inserted == 5  # jam 100..104
    symbol, close, asof = d1.prices[0]
    assert (symbol, close) == ("BTCUSDT", 204.0)
    assert asof == T0 + timedelta(hours=105)  # waktu TUTUP candle terakhir
    assert d1.meta["crypto_hourly.status"] == "ok" and "crypto_hourly.last_success" in d1.meta
    assert neon.runs == [("crypto_hourly", "ok", 5, None)]


def test_simbol_baru_mulai_dari_48_candle_terakhir() -> None:
    neon, d1 = FakeNeon(), FakeD1()
    result = _run(neon, d1, symbols=("SOLUSDT",))
    assert result.summary.inserted == 48 and result.status == "ok"


def test_job_terlewat_lama_tetap_lanjut_dari_candle_terakhir_tanpa_celah() -> None:
    neon, d1 = FakeNeon(), FakeD1()
    _seed(neon, "BTCUSDT", 10)  # terakhir T0+9h, jauh lebih lama dari 48 candle lalu
    result = _run(neon, d1)
    assert result.summary.inserted == 95  # jam 10..104, tanpa celah
    assert not [i for i in neon.issues if i["issue"] == "gap"]


def test_d1_gagal_data_neon_tetap_aman_status_partial() -> None:
    neon, d1 = FakeNeon(), FakeD1(fail=True)
    _seed(neon, "BTCUSDT", 100)
    result = _run(neon, d1)
    assert result.status == "partial" and result.d1_error
    assert len(neon.rows) == 105
    assert neon.runs[0][1] == "partial" and "D1 gagal" in neon.runs[0][3]
    assert "crypto_hourly.last_success" not in d1.meta


def test_diblokir_status_error_dan_d1_tidak_disentuh() -> None:
    neon, d1 = FakeNeon(), FakeD1()
    result = _run(neon, d1, source=FakeSource(blocked=True))
    assert result.status == "error"
    assert d1.prices == [] and d1.meta == {}
    assert neon.runs[0][1] == "error"


def test_tanpa_d1_untuk_uji_coba() -> None:
    neon = FakeNeon()
    result = run_incremental(
        FakeSource(), neon, None, ["BTCUSDT"], "1h", "crypto_hourly", NOW, log=lambda _: None
    )
    assert result.status == "ok" and result.summary.inserted == 48
