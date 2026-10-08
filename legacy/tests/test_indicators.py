"""Sanity tests for the indicator engine - run with pytest (no network)."""

import numpy as np
import pandas as pd

from app.core.indicators.base import REGISTRY, latest_signal
from app.core.indicators.momentum import rsi
from app.core.indicators.trend import atr, supertrend
from app.core.signals.confluence import (WAIT, apply_adx_filter, confluence_score,
                                         status_of)


def synth_uptrend(n: int = 300, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    drift = np.linspace(100, 160, n) + rng.normal(0, 0.8, n).cumsum() * 0.15
    close = pd.Series(drift)
    spread = close.diff().abs().clip(0.2, 3) + 0.5
    return pd.DataFrame({
        "open": close - spread / 2,
        "high": close + spread / 2,
        "low": close - spread / 2,
        "close": close,
        "volume": rng.uniform(800, 1500, n),
    })


def test_rsi_bounds():
    df = synth_uptrend()
    v = rsi(df["close"]).dropna()
    assert v.between(0, 100).all()


def test_strong_uptrend_signals_bullish():
    df = synth_uptrend()
    assert latest_signal(REGISTRY["ema_ribbon"](df)) == 1
    assert latest_signal(REGISTRY["supertrend"](df)) == 1
    # vwap_signal sudah tidak terdaftar di REGISTRY; guard agar kompatibel
    if "vwap_signal" in REGISTRY:
        assert latest_signal(REGISTRY["vwap_signal"](df)) == 1


def test_supertrend_and_atr_length():
    df = synth_uptrend()
    assert len(supertrend(df)) == len(df)
    assert atr(df).dropna().gt(0).all()


def test_all_registered_indicators_run():
    df = synth_uptrend()
    for name, fn in REGISTRY.items():
        sig = fn(df)
        assert set(sig.dropna().unique()) <= {-1, 0, 1}, name
        assert len(sig) == len(df), name


def test_scorer_thresholds():
    assert status_of(72) == "strong_buy"
    assert status_of(35) == "buy"
    assert status_of(5) == WAIT
    assert status_of(-35) == "sell"
    assert status_of(-72) == "strong_sell"


def test_scorer_weights():
    s = confluence_score({"a": 1, "b": -1}, {"a": 12, "b": 12})
    assert s == 0
    s2 = confluence_score({"a": 1, "b": 1}, {"a": 12, "b": 12})
    assert s2 == 100


def test_adx_filter_forces_wait_in_chop():
    status, filtered = apply_adx_filter("buy", adx_val=15.0)
    assert status == WAIT and filtered is True
    status2, filtered2 = apply_adx_filter("buy", adx_val=30.0)
    assert status2 == "buy" and filtered2 is False
