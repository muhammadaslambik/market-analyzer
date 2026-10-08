"""Base types and the indicator registry."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

BULL, NEUTRAL, BEAR = 1, 0, -1

REGISTRY: dict[str, Callable[[pd.DataFrame], pd.Series]] = {}


def register(name: str) -> Callable:
    def deco(fn: Callable[[pd.DataFrame], pd.Series]):
        if name in REGISTRY:
            raise ValueError(f"Indicator '{name}' sudah terdaftar")
        REGISTRY[name] = fn
        return fn
    return deco


def latest_signal(series: pd.Series) -> int:
    """Last non-NaN signal value (defaults to NEUTRAL)."""
    s = series.dropna()
    return int(s.iloc[-1]) if len(s) else NEUTRAL
