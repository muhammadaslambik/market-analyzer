import numpy as np
import pytest

from analyzer.metrics import (
    block_bootstrap_bss,
    expected_calibration_error_equal_count,
    interval_coverage,
    pinball_loss,
    wilson_interval,
)


def test_ece_bin_sama_banyak_nilai_tangan() -> None:
    y = np.array([0.0, 0.0, 1.0, 1.0])
    p = np.array([0.1, 0.1, 0.9, 0.9])
    assert expected_calibration_error_equal_count(y, p, n_bins=2) == pytest.approx(0.1)


def test_ece_kosong() -> None:
    assert expected_calibration_error_equal_count(np.array([]), np.array([])) == 0.0


def _data(n: int = 4000, seed: int = 1) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    p_true = rng.choice([0.2, 0.8], size=n)
    y = (rng.random(n) < p_true).astype(float)
    return y, p_true, np.full(n, 0.5)


def test_bootstrap_model_lebih_baik_batas_bawah_positif() -> None:
    y, p_model, p_ref = _data()
    lower, upper = block_bootstrap_bss(y, p_model, p_ref, 8, n_boot=500)
    assert 0 < lower < upper


def test_bootstrap_model_sama_dengan_pembanding_mencakup_nol() -> None:
    y, _, p_ref = _data()
    lower, upper = block_bootstrap_bss(y, p_ref, p_ref, 8, n_boot=300)
    assert lower <= 0 <= upper


def test_bootstrap_reproducible_dan_tidak_mengubah_seed_global() -> None:
    y, p_model, p_ref = _data(1000)
    a = block_bootstrap_bss(y, p_model, p_ref, 8, n_boot=200, seed=5)
    b = block_bootstrap_bss(y, p_model, p_ref, 8, n_boot=200, seed=5)
    assert a == b
    np.random.seed(11)
    expected = np.random.rand()
    np.random.seed(11)
    block_bootstrap_bss(y, p_model, p_ref, 8, n_boot=50)
    assert np.random.rand() == expected


def test_pinball_nilai_tangan() -> None:
    y = np.array([1.0, 2.0, 3.0])
    assert pinball_loss(y, np.array([2.0, 2.0, 2.0]), 0.5) == pytest.approx(1 / 3)
    assert pinball_loss(y, np.array([2.0, 2.0, 2.0]), 0.9) == pytest.approx((0.1 + 0 + 0.9) / 3)


def test_cakupan_interval() -> None:
    y = np.array([1.0, 5.0, 3.0, 10.0])
    assert interval_coverage(y, np.zeros(4), np.full(4, 4.0)) == 0.5


def test_wilson() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)
    lo, hi = wilson_interval(50, 100)
    assert lo == pytest.approx(0.4038, abs=1e-3) and hi == pytest.approx(0.5962, abs=1e-3)
