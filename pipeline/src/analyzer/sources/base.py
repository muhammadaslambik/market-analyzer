"""Antarmuka sumber data harga."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from analyzer.models import Candle


class SourceError(RuntimeError):
    """Galat umum dari sumber data."""


class SourceBlockedError(SourceError):
    """Sumber memblokir akses (mis. HTTP 451 atau 403). Tidak perlu di-retry."""


class CandleSource(Protocol):
    name: str
    api_calls: int

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        now: datetime | None = None,
    ) -> list[Candle]:
        """Ambil candle dengan waktu buka dalam [start, end). Hanya candle yang sudah tutup."""
        ...
