"""Data sintetis bersama untuk tes evaluasi."""

import numpy as np
import pandas as pd

N = 12000
KW = {"min_train": 2000, "test_size": 500, "n_boot": 1000}


def make_df(returns: np.ndarray) -> pd.DataFrame:
    n = len(returns)
    close = 100.0 * np.exp(np.cumsum(returns))
    index = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    volume = np.random.default_rng(0).uniform(100, 1000, n)
    spread = np.abs(returns) * close * 0.5 + 0.05
    return pd.DataFrame(
        {
            "open": np.r_[close[0], close[:-1]],
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def random_walk(seed: int) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, 0.01, N)


def ar1(seed: int, phi: float) -> np.ndarray:
    eps = np.random.default_rng(seed).normal(0, 0.01, N)
    out = np.zeros(N)
    for t in range(1, N):
        out[t] = phi * out[t - 1] + eps[t]
    return out


def regime_drift(seed: int, mu: float, flip: float = 0.002) -> np.ndarray:
    rng = np.random.default_rng(seed)
    state, out = 1.0, np.zeros(N)
    for t in range(N):
        if rng.random() < flip:
            state = -state
        out[t] = state * mu + rng.normal(0, 0.01)
    return out
