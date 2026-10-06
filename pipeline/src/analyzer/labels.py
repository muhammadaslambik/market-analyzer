import numpy as np
import pandas as pd


def compute_labels(df: pd.DataFrame, horizon: int) -> tuple[pd.Series, pd.Series]:
    """
    Menghitung realized return dan label biner arah pergerakan harga.
    y = 1 jika return > 0, y = 0 jika return < 0. Return tepat 0 dibuang.
    Baris sebanyak 'horizon' di akhir tidak diberi label (NaN).
    """
    # Menghitung return berdasarkan forward close price
    future_close = df["close"].shift(-horizon)
    realized_return = (future_close / df["close"]) - 1.0

    # Label biner arah pergerakan harga
    labels = pd.Series(np.nan, index=df.index)
    labels[realized_return > 0] = 1.0
    labels[realized_return < 0] = 0.0

    return realized_return, labels
