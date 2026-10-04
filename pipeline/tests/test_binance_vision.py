from datetime import UTC, datetime, timedelta

import httpx
import pytest

from analyzer.ratelimit import TokenBucket
from analyzer.sources.base import SourceBlockedError, SourceError
from analyzer.sources.binance_vision import PAGE_LIMIT, BinanceVisionSource

T0 = datetime(2026, 1, 1, tzinfo=UTC)
HOUR_MS = 3_600_000


def _row(open_ms: int) -> list:
    return [open_ms, "100", "110", "90", "105", "5", open_ms + HOUR_MS - 1, "0", 1, "0", "0", "0"]


def _source(handler, sleeps: list[float] | None = None) -> BinanceVisionSource:
    client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="https://data-api.binance.vision"
    )
    log = sleeps if sleeps is not None else []
    return BinanceVisionSource(
        client=client,
        bucket=TokenBucket(1000.0, capacity=1000),
        max_retries=3,
        backoff_base=1.0,
        sleep=log.append,
    )


def _paging_handler(total_hours: int):
    first = int(T0.timestamp() * 1000)

    def handler(request: httpx.Request) -> httpx.Response:
        start = int(request.url.params["startTime"])
        end = int(request.url.params["endTime"])
        limit = int(request.url.params["limit"])
        rows = []
        ms = start
        while ms <= end and len(rows) < limit and ms < first + total_hours * HOUR_MS:
            rows.append(_row(ms))
            ms += HOUR_MS
        return httpx.Response(200, json=rows)

    return handler


def test_paginasi_mengumpulkan_semua_candle() -> None:
    source = _source(_paging_handler(2500))
    now = T0 + timedelta(days=365)
    candles = source.fetch_candles("BTCUSDT", "1h", T0, T0 + timedelta(hours=2500), now=now)
    assert len(candles) == 2500
    assert source.api_calls == 3
    assert candles[0].ts == T0 and candles[-1].ts == T0 + timedelta(hours=2499)
    assert len({c.ts for c in candles}) == 2500
    assert candles[0].source == "binance-vision" and candles[0].market == "crypto"


def test_candle_belum_tutup_dibuang() -> None:
    source = _source(_paging_handler(10))
    now = T0 + timedelta(hours=5, minutes=30)  # candle jam ke-5 masih berjalan
    candles = source.fetch_candles("BTCUSDT", "1h", T0, T0 + timedelta(hours=10), now=now)
    assert [c.ts for c in candles] == [T0 + timedelta(hours=h) for h in range(5)]


def test_diblokir_451_tanpa_retry() -> None:
    source = _source(lambda request: httpx.Response(451, text="blocked"))
    with pytest.raises(SourceBlockedError):
        source.fetch_candles(
            "BTCUSDT", "1h", T0, T0 + timedelta(hours=1), now=T0 + timedelta(days=1)
        )
    assert source.api_calls == 1


def test_429_menghormati_retry_after_lalu_berhasil() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "7"})
        return httpx.Response(200, json=[_row(int(T0.timestamp() * 1000))])

    sleeps: list[float] = []
    source = _source(handler, sleeps)
    candles = source.fetch_candles(
        "BTCUSDT", "1h", T0, T0 + timedelta(hours=1), now=T0 + timedelta(days=1)
    )
    assert len(candles) == 1 and sleeps == [7.0] and source.api_calls == 2


def test_error_server_berulang_menyerah_setelah_retry() -> None:
    source = _source(lambda request: httpx.Response(500))
    with pytest.raises(SourceError):
        source.fetch_candles(
            "BTCUSDT", "1h", T0, T0 + timedelta(hours=1), now=T0 + timedelta(days=1)
        )
    assert source.api_calls == 4  # 1 percobaan + 3 retry


def test_baris_tidak_sesuai_format() -> None:
    source = _source(lambda request: httpx.Response(200, json=[[1, 2]]))
    with pytest.raises(SourceError):
        source.fetch_candles(
            "BTCUSDT", "1h", T0, T0 + timedelta(hours=1), now=T0 + timedelta(days=1)
        )


def test_simbol_dan_timeframe_tidak_valid() -> None:
    source = _source(lambda request: httpx.Response(200, json=[]))
    with pytest.raises(ValueError):
        source.fetch_candles("btc/usdt", "1h", T0, T0 + timedelta(hours=1))
    with pytest.raises(ValueError):
        source.fetch_candles("BTCUSDT", "5m", T0, T0 + timedelta(hours=1))


def test_page_limit_sesuai_dugaan() -> None:
    assert PAGE_LIMIT == 1000
