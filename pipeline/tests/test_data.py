from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

from analyzer.data import candles_to_frame, find_gaps, load_candles
from analyzer.models import Candle

T0 = datetime(2026, 1, 1, tzinfo=UTC)
NOW = T0 + timedelta(days=10)


def mk(hours: int, symbol: str = "BTCUSDT", close: float = 100.0) -> Candle:
    return Candle(
        "crypto", symbol, "1h", T0 + timedelta(hours=hours), 100.0, 110.0, 90.0, close, 5.0, "uji"
    )


def test_frame_bentuk_dan_tipe() -> None:
    frame = candles_to_frame([mk(2), mk(0), mk(1)], now=NOW)
    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert str(frame.index.tz) == "UTC" and frame.index.name == "ts"
    assert frame.index.is_monotonic_increasing and frame.index.is_unique
    assert (frame.dtypes == "float64").all()
    assert frame.attrs == {"market": "crypto", "symbol": "BTCUSDT", "timeframe": "1h"}


def test_candle_belum_tutup_dibuang() -> None:
    now = T0 + timedelta(hours=2, minutes=30)
    frame = candles_to_frame([mk(0), mk(1), mk(2)], now=now)
    assert list(frame.index) == [pd.Timestamp(T0), pd.Timestamp(T0 + timedelta(hours=1))]


def test_seri_campuran_ditolak() -> None:
    with pytest.raises(ValueError):
        candles_to_frame([mk(0), mk(1, symbol="ETHUSDT")], now=NOW)


def test_duplikat_ditolak() -> None:
    with pytest.raises(ValueError):
        candles_to_frame([mk(0), mk(0, close=101.0)], now=NOW)


def test_tanpa_timezone_ditolak() -> None:
    naive = Candle("crypto", "BTCUSDT", "1h", datetime(2026, 1, 1), 1, 2, 0.5, 1.5, 1, "uji")
    with pytest.raises(ValueError):
        candles_to_frame([naive], now=NOW)


def test_kosong_menghasilkan_frame_kosong_berstruktur() -> None:
    frame = candles_to_frame([], symbol="BTCUSDT", timeframe="1h")
    assert frame.empty and list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert str(frame.index.tz) == "UTC"


def test_find_gaps() -> None:
    frame = candles_to_frame([mk(0), mk(1), mk(4), mk(5), mk(9)], now=NOW)
    assert find_gaps(frame, "1h") == [
        (T0 + timedelta(hours=2), 2),
        (T0 + timedelta(hours=6), 3),
    ]
    assert find_gaps(candles_to_frame([mk(0), mk(1)], now=NOW), "1h") == []


def test_load_candles_lewat_pembaca() -> None:
    class Reader:
        def fetch_candles(self, market, symbol, timeframe, start=None, end=None):
            self.args = (market, symbol, timeframe, start, end)
            return [mk(0), mk(1)]

    reader = Reader()
    frame = load_candles(reader, "BTCUSDT", "1h", now=NOW)
    assert len(frame) == 2 and reader.args == ("crypto", "BTCUSDT", "1h", None, None)
