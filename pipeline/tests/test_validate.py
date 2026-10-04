from datetime import UTC, datetime, timedelta

import pytest

from analyzer.models import Candle
from analyzer.validate import validate_candles

T0 = datetime(2026, 1, 1, tzinfo=UTC)
NOW = T0 + timedelta(days=30)


def mk(hours: int, **kw: float) -> Candle:
    base = {"open": 100.0, "high": 110.0, "low": 90.0, "close": 105.0, "volume": 5.0}
    base.update(kw)
    return Candle("crypto", "BTCUSDT", "1h", T0 + timedelta(hours=hours), source="uji", **base)


def kinds(result) -> list[str]:
    return [i["issue"] for i in result.issues]


def test_seri_bersih_lolos_tanpa_masalah() -> None:
    result = validate_candles([mk(h) for h in range(5)], now=NOW)
    assert len(result.valid) == 5 and result.issues == []


def test_kosong() -> None:
    result = validate_candles([], now=NOW)
    assert result.valid == [] and result.issues == []


def test_hasil_diurutkan_menaik() -> None:
    result = validate_candles([mk(2), mk(0), mk(1)], now=NOW)
    assert [c.ts for c in result.valid] == [T0 + timedelta(hours=h) for h in range(3)]


def test_duplikat_dicatat_dan_yang_pertama_dipakai() -> None:
    first, second = mk(1, close=101.0), mk(1, close=102.0)
    result = validate_candles([mk(0), first, second], now=NOW)
    assert kinds(result) == ["duplicate"]
    assert [c.close for c in result.valid if c.ts == first.ts] == [101.0]


def test_candle_belum_tutup_ditolak() -> None:
    now = T0 + timedelta(hours=2, minutes=30)  # candle jam ke-2 masih berjalan
    result = validate_candles([mk(0), mk(1), mk(2)], now=now)
    assert kinds(result) == ["not_closed"] and len(result.valid) == 2


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"open": 0.0, "low": 0.0}, "harga_tidak_positif"),
        ({"low": 120.0}, "low_lebih_besar_dari_high"),
        ({"low": 102.0}, "low_di_atas_open_atau_close"),
        ({"high": 103.0}, "high_di_bawah_open_atau_close"),
        ({"volume": -1.0}, "volume_negatif"),
        ({"close": float("nan")}, "tidak_hingga_atau_nan"),
        ({"volume": float("inf")}, "tidak_hingga_atau_nan"),
    ],
)
def test_ohlc_tidak_valid(override: dict[str, float], reason: str) -> None:
    result = validate_candles([mk(0), mk(1, **override), mk(2)], now=NOW)
    ohlc = [i for i in result.issues if i["issue"] == "ohlc_invalid"]
    assert len(ohlc) == 1 and reason in ohlc[0]["detail"]["reasons"]
    assert T0 + timedelta(hours=1) not in [c.ts for c in result.valid]


def test_ts_tidak_selaras() -> None:
    odd = Candle("crypto", "BTCUSDT", "1h", T0 + timedelta(minutes=30), 100, 110, 90, 105, 5, "uji")
    result = validate_candles([odd], now=NOW)
    assert result.valid == []
    assert "ts_tidak_selaras" in result.issues[0]["detail"]["reasons"]


def test_celah_dicatat_dengan_jumlah_yang_hilang() -> None:
    result = validate_candles([mk(0), mk(1), mk(4), mk(5)], now=NOW)
    gaps = [i for i in result.issues if i["issue"] == "gap"]
    assert len(gaps) == 1
    assert gaps[0]["ts"] == T0 + timedelta(hours=2) and gaps[0]["detail"]["missing"] == 2
    assert len(result.valid) == 4  # candle di sekitar celah tetap valid


def test_candle_rusak_menimbulkan_celah_tercatat() -> None:
    result = validate_candles([mk(0), mk(1, volume=-1.0), mk(2)], now=NOW)
    assert sorted(kinds(result)) == ["gap", "ohlc_invalid"]


def test_outlier_hanya_ditandai_bukan_dibuang() -> None:
    result = validate_candles([mk(0), mk(1, open=200, high=320, low=190, close=300)], now=NOW)
    assert kinds(result) == ["outlier"] and len(result.valid) == 2


def test_ambang_outlier_bisa_diatur() -> None:
    series = [mk(0), mk(1, close=107.0)]
    assert validate_candles(series, now=NOW, outlier_threshold=0.5).issues == []
    assert kinds(validate_candles(series, now=NOW, outlier_threshold=0.01)) == ["outlier"]


def test_baris_masalah_siap_ditulis_ke_tabel() -> None:
    result = validate_candles([mk(0), mk(1, volume=-1.0)], now=NOW)
    row = result.issues[0]
    assert set(row) == {"market", "symbol", "timeframe", "ts", "issue", "detail"}
    assert row["market"] == "crypto" and row["symbol"] == "BTCUSDT" and row["timeframe"] == "1h"


def test_seri_campuran_ditolak() -> None:
    other = Candle("crypto", "ETHUSDT", "1h", T0, 100, 110, 90, 105, 5, "uji")
    with pytest.raises(ValueError):
        validate_candles([mk(0), other], now=NOW)


def test_ts_tanpa_timezone_ditolak() -> None:
    naive = Candle("crypto", "BTCUSDT", "1h", datetime(2026, 1, 1), 100, 110, 90, 105, 5, "uji")
    with pytest.raises(ValueError):
        validate_candles([naive], now=NOW)
