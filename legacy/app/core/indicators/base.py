"""Base types and the indicator registry.

Every indicator takes an OHLCV DataFrame and returns a pandas Series of
signals in {+1 (bullish), 0 (neutral), -1 (bearish)}, one per row.
"""

from __future__ import annotations

import pandas as pd

BULL, NEUTRAL, BEAR = 1, 0, -1

# name -> callable(df) -> Series[int]; filled in by submodules and registered here
REGISTRY: dict[str, callable] = {}


def register(name: str):
    def deco(fn):
        REGISTRY[name] = fn
        return fn
    return deco


def latest_signal(series: pd.Series) -> int:
    """Last non-NaN signal value (defaults to NEUTRAL)."""
    s = series.dropna()
    return int(s.iloc[-1]) if len(s) else NEUTRAL
