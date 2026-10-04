"""Confluence scorer: combines indicator signals + weights into a score,
a status label, and the global ADX sideways filter."""

from __future__ import annotations

import pandas as pd

STRONG_BUY, BUY, WAIT, SELL, STRONG_SELL = "strong_buy", "buy", "wait", "sell", "strong_sell"


def status_of(score: float) -> str:
    if score >= 60:
        return STRONG_BUY
    if score >= 20:
        return BUY
    if score > -20:
        return WAIT
    if score > -60:
        return SELL
    return STRONG_SELL


def confluence_score(signals: dict[str, int], weights: dict[str, float]) -> float:
    """Weighted sum of signals normalized to -100..+100."""
    total_w = sum(weights.values()) or 1.0
    return round(sum(signals[k] * weights[k] for k in signals) / total_w * 100, 1)


def apply_adx_filter(status: str, adx_val: float, threshold: float = 20.0) -> tuple[str, bool]:
    """Sideways regime -> force WAIT unless the status already is WAIT."""
    if adx_val < threshold and status != WAIT:
        return WAIT, True
    return status, False


def score_series(df: pd.DataFrame, indicators: dict) -> pd.Series:
    """Point-in-time score series for backtesting. `indicators` maps
    name -> dict(fn=callable, weight=float)."""
    out = pd.Series(0.0, index=df.index)
    total = sum(v["weight"] for v in indicators.values()) or 1.0
    for name, cfg in indicators.items():
        sig = cfg["fn"](df).reindex(df.index).fillna(0)
        out = out + sig * cfg["weight"]
    return out / total * 100
