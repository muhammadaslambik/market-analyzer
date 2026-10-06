"""Pemuatan data candle menjadi DataFrame untuk analisa dan evaluasi.

Aturan: hanya candle yang sudah tutup, satu seri (market, simbol, timeframe), indeks waktu UTC
terurut tanpa duplikat. Candle di Neon sudah lolos validator saat ditulis; loader ini
memeriksa ulang hal-hal yang menentukan kebenaran evaluasi (urutan, duplikat, celah).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Protocol

import pandas as pd

from analyzer.models import Candle, interval_of

COLUMNS = ["open", "high", "low", "close", "volume"]


class CandleReader(Protocol):
    def fetch_candles(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Candle]: ...


def _empty_frame(market: str, symbol: str, timeframe: str) -> pd.DataFrame:
    index = pd.DatetimeIndex([], tz="UTC", name="ts")
    frame = pd.DataFrame({c: pd.Series(dtype="float64") for c in COLUMNS}, index=index)
    frame.attrs = {"market": market, "symbol": symbol, "timeframe": timeframe}
    return frame


def candles_to_frame(
    candles: Sequence[Candle],
    *,
    market: str = "crypto",
    symbol: str = "",
    timeframe: str = "",
    now: datetime | None = None,
) -> pd.DataFrame:
    """Ubah daftar candle satu seri menjadi DataFrame. Candle yang belum tutup dibuang."""
    if not candles:
        return _empty_frame(market, symbol, timeframe)
    first = candles[0]
    key = (first.market, first.symbol, first.timeframe)
    if any((c.market, c.symbol, c.timeframe) != key for c in candles):
        raise ValueError("candles_to_frame hanya menerima satu seri (market, simbol, timeframe)")
    if any(c.ts.tzinfo is None for c in candles):
        raise ValueError("ts candle harus timezone-aware (UTC)")

    interval = interval_of(first.timeframe)
    cutoff = now or datetime.now(UTC)
    ordered = sorted((c for c in candles if c.ts + interval <= cutoff), key=lambda c: c.ts)
    stamps = [c.ts for c in ordered]
    if len(set(stamps)) != len(stamps):
        raise ValueError("ditemukan candle duplikat pada seri yang sama")
    if not ordered:
        return _empty_frame(*key)

    index = pd.DatetimeIndex(stamps, name="ts").tz_convert("UTC")
    frame = pd.DataFrame(
        {
            "open": [c.open for c in ordered],
            "high": [c.high for c in ordered],
            "low": [c.low for c in ordered],
            "close": [c.close for c in ordered],
            "volume": [c.volume for c in ordered],
        },
        index=index,
        dtype="float64",
    )
    frame.attrs = {"market": first.market, "symbol": first.symbol, "timeframe": first.timeframe}
    return frame


def find_gaps(frame: pd.DataFrame, timeframe: str) -> list[tuple[datetime, int]]:
    """Daftar celah: (waktu candle pertama yang hilang, jumlah candle yang hilang)."""
    if len(frame) < 2:
        return []
    step = pd.Timedelta(interval_of(timeframe))
    diffs = frame.index.to_series().diff().iloc[1:]
    gaps: list[tuple[datetime, int]] = []
    for ts, delta in diffs[diffs > step].items():
        missing = int(delta / step) - 1
        gaps.append(((ts - delta + step).to_pydatetime(), missing))
    return gaps


def load_candles(
    reader: CandleReader,
    symbol: str,
    timeframe: str,
    *,
    market: str = "crypto",
    start: datetime | None = None,
    end: datetime | None = None,
    now: datetime | None = None,
) -> pd.DataFrame:
    """Muat satu seri dari penyimpanan (Neon) menjadi DataFrame."""
    candles = reader.fetch_candles(market, symbol, timeframe, start, end)
    return candles_to_frame(candles, market=market, symbol=symbol, timeframe=timeframe, now=now)
