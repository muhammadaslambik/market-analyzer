import numpy as np
import pandas as pd

from analyzer.cv import generate_walk_forward_splits


def test_purging_tidak_ada_label_latihan_yang_menembus_blok_uji() -> None:
    n, horizon, min_train, test_size = 3000, 24, 500, 100
    df = pd.DataFrame({"x": np.arange(n)}, index=pd.date_range("2026-01-01", periods=n, freq="h"))
    splits = generate_walk_forward_splits(df, horizon, min_train, test_size)
    assert len(splits) == (n - min_train) // test_size
    previous_test_end = -1
    for train_idx, test_idx in splits:
        last_train = df.index.get_loc(train_idx[-1])
        first_test = df.index.get_loc(test_idx[0])
        assert last_train + horizon < first_test  # label baris latihan terakhir tidak menembus uji
        assert train_idx.max() < test_idx.min()
        assert first_test > previous_test_end  # blok uji berurutan tanpa tumpang tindih
        previous_test_end = df.index.get_loc(test_idx[-1])
