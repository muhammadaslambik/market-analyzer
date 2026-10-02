"""Volatility indicators: Bollinger Bands (signal) and ATR (risk sizing)."""

import pandas as pd

from .base import BULL, BEAR, NEUTRAL, register
from .trend import atr as atr_fn


@register("bollinger")
def bollinger(df: pd.DataFrame, n: int = 20, k: float = 2.0) -> pd.Series:
    """Mean-reversion framing: touch of lower band in non-squeeze = bullish
    bounce; touch of upper = bearish. Squeeze (bandwidth percentile low) is
    flagged neutral here and belongs to breakout logic in later phases."""
    mid = df["close"].rolling(n).mean()
    sd = df["close"].rolling(n).std()
    up_b, lo_b = mid + k * sd, mid - k * sd
    c = df["close"]
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[c <= lo_b] = BULL
    sig[c >= up_b] = BEAR
    return sig


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return atr_fn(df, n)
