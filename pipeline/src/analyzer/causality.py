"""Pemeriksaan kausalitas (truncation invariance): nilai di waktu t tidak boleh berubah
bila data setelah t dibuang. Fungsi yang melanggar berarti memakai data masa depan."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd


def first_violation(
    fn: Callable[[pd.DataFrame], pd.DataFrame | pd.Series],
    df: pd.DataFrame,
    cut_points: Sequence[int],
    rtol: float = 1e-9,
) -> int | None:
    """Kembalikan titik potong pertama yang melanggar kausalitas, atau None bila semuanya lolos."""
    full = fn(df)
    full_frame = full.to_frame() if isinstance(full, pd.Series) else full
    for k in cut_points:
        part = fn(df.iloc[:k])
        part_frame = part.to_frame() if isinstance(part, pd.Series) else part
        a = full_frame.iloc[:k].to_numpy(dtype=float)
        b = part_frame.to_numpy(dtype=float)
        if a.shape != b.shape or not np.allclose(a, b, rtol=rtol, atol=1e-12, equal_nan=True):
            return k
    return None


def is_causal(
    fn: Callable[[pd.DataFrame], pd.DataFrame | pd.Series],
    df: pd.DataFrame,
    cut_points: Sequence[int],
) -> bool:
    return first_violation(fn, df, cut_points) is None
