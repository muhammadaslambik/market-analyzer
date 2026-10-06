import numpy as np
import pandas as pd

from analyzer.evaluate import run_evaluation_pipeline


def test_framework_sanity_on_random_walk():
    """Kriteria 5.7: Model acak wajib dinilai EKSPERIMENTAL."""
    np.random.seed(42)
    periods = 800
    dates = pd.date_range(start="2026-01-01", periods=periods, freq="h", tz="UTC")

    random_returns = np.random.normal(0, 0.01, periods)
    price_series = 100.0 * np.exp(np.cumsum(random_returns))

    df = pd.DataFrame(
        {
            "open": price_series - 1,
            "high": price_series + 2,
            "low": price_series - 2,
            "close": price_series,
            "volume": np.random.uniform(100, 1000, periods),
        },
        index=dates,
    )

    report = run_evaluation_pipeline(df, symbol="RANDOM", timeframe="1h", horizon=4)
    assert "EKSPERIMENTAL" in report
