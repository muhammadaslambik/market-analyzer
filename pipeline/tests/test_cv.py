import numpy as np
import pandas as pd

from analyzer.cv import generate_walk_forward_splits
from analyzer.labels import compute_labels


def test_labels_and_purging_logic():
    dates = pd.date_range(start="2026-01-01", periods=100, freq="D", tz="UTC")
    df = pd.DataFrame({"close": np.linspace(100, 200, 100)}, index=dates)

    ret, labels = compute_labels(df, horizon=5)
    assert pd.isna(labels.iloc[-5:]).all()

    splits = generate_walk_forward_splits(df, horizon=5, min_train_size=40, test_size=10)

    assert len(splits) > 0
    for train_idx, test_idx in splits:
        assert test_idx.min() > train_idx.max()

        # Jarak antara akhir latihan ter-purged dengan awal pengujian
        time_gap = (test_idx.min() - train_idx.max()).days
        assert time_gap >= 5
