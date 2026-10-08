import numpy as np
import pandas as pd

from analyzer.causality import first_violation, is_causal
from analyzer.features import (
    compute_confluence_features,
    compute_momentum_sign,
    compute_volatility,
)


def make_df(n: int = 1500, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    spread = np.abs(rng.normal(0, 0.3, n)) + 0.05
    index = pd.date_range("2026-01-01", periods=n, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "open": np.r_[close[0], close[:-1]],
            "high": close + spread,
            "low": close - spread,
            "close": close,
            "volume": rng.uniform(100, 1000, n),
        },
        index=index,
    )


CUTS = [300, 600, 900, 1200]


def test_fitur_masa_depan_terdeteksi() -> None:
    df = make_df()
    leaky = lambda d: d["close"].shift(-1)  # noqa: E731
    assert first_violation(leaky, df, CUTS) is not None
    assert not is_causal(leaky, df, CUTS)


def test_jendela_berpusat_terdeteksi() -> None:
    df = make_df()
    centered = lambda d: d["close"].rolling(5, center=True).mean()  # noqa: E731
    assert not is_causal(centered, df, CUTS)


def test_fitur_konfluensi_kausal() -> None:
    assert is_causal(compute_confluence_features, make_df(), CUTS)


def test_fitur_momentum_dan_volatilitas_kausal() -> None:
    df = make_df()
    assert is_causal(lambda d: compute_momentum_sign(d, 4), df, CUTS)
    assert is_causal(compute_volatility, df, CUTS)
