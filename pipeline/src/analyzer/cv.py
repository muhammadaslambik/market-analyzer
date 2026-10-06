import pandas as pd


def generate_walk_forward_splits(
    df: pd.DataFrame, horizon: int, min_train_size: int, test_size: int
) -> list[tuple[pd.Index, pd.Index]]:
    """Menghasilkan indeks latih/uji menggunakan metode Expanding Window dengan Purging.

    Menghapus 'horizon' baris terakhir di data latihan yang labelnya
    tumpang tindih dengan awal blok uji.
    """
    splits = []
    n_samples = len(df)

    start_idx = min_train_size
    while start_idx + test_size <= n_samples:
        train_end = start_idx
        test_end = start_idx + test_size

        raw_train_idx = df.index[:train_end]
        test_idx = df.index[train_end:test_end]

        purged_train_idx = (
            raw_train_idx[:-horizon] if len(raw_train_idx) > horizon else raw_train_idx
        )

        splits.append((purged_train_idx, test_idx))
        start_idx += test_size

    return splits
