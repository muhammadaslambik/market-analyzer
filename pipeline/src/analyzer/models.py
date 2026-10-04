"""Model data bersama."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

INTERVALS: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "1d": timedelta(days=1),
}


def interval_of(timeframe: str) -> timedelta:
    """Kembalikan lama satu candle untuk timeframe yang didukung."""
    try:
        return INTERVALS[timeframe]
    except KeyError:
        raise ValueError(f"Timeframe tidak didukung: {timeframe!r}") from None


@dataclass(frozen=True)
class Candle:
    market: str
    symbol: str
    timeframe: str  # '1h' atau '1d'
    ts: datetime  # waktu BUKA candle, UTC (timezone-aware)
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str
