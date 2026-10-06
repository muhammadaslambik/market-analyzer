import numpy as np
import pandas as pd

from analyzer.features import compute_confluence_features


def test_confluence_output_range_and_causality():
    # Buat deret data tiruan (dummy data) sebanyak 100 baris
    dates = pd.date_range(start="2026-01-01", periods=100, freq="1h", tz="UTC")
    df = pd.DataFrame(
        {
            "open": np.linspace(100, 150, 100),
            "high": np.linspace(102, 152, 100),
            "low": np.linspace(98, 148, 100),
            "close": np.linspace(101, 151, 100),
            "volume": np.random.uniform(500, 1500, 100),
        },
        index=dates,
    )

    # 1. Jalankan Engine Fitur
    res = compute_confluence_features(df)

    # Pastikan rentang nilai aman di batas keras [-100, 100]
    assert res["confluence_score"].min() >= -100.0
    assert res["confluence_score"].max() <= 100.0

    # 2. Uji Kebocoran Data (Truncation Invariance)
    truncated_df = df.iloc[:50]
    res_truncated = compute_confluence_features(truncated_df)

    # Nilai baris ke-50 (index 49) pada data terpotong harus identik dengan data utuh!
    assert np.isclose(
        res["confluence_score"].iloc[49], res_truncated["confluence_score"].iloc[49]
    ), "LOOK-AHEAD BIAS DETECTED: Nilai berubah saat data masa depan dipotong!"
