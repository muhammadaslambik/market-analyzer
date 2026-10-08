"""Backtest engine test on synthetic data (no network)."""

import pandas as pd

from app.core.indicators.base import REGISTRY
from backtest.engine import run_backtest


def _df() -> pd.DataFrame:
    import numpy as np
    rng = np.random.default_rng(3)
    n = 400
    t = np.arange(n)
    cyc = 100 + 8 * np.sin(t / 12) + t * 0.03
    close = pd.Series(cyc + rng.normal(0, 0.7, n).cumsum() * 0.1)
    sp = close.diff().abs().clip(0.2, 2.5) + 0.4
    return pd.DataFrame({"open": close - sp / 2, "high": close + sp / 2,
                         "low": close - sp / 2, "close": close,
                         "volume": rng.uniform(500, 1200, n)})


def test_backtest_runs_and_reports():
    df = _df()
    indicators = {name: {"fn": fn, "weight": 10.0}
                  for name, fn in REGISTRY.items()
                  if name not in ("funding_oi", "foreign_flow", "rs_vs_index", "rsi")}
    r = run_backtest(df, indicators)
    for k in ("trades", "win_rate", "total_return", "max_drawdown", "profit_factor"):
        assert k in r
    assert -1 <= r["max_drawdown"] <= 0
