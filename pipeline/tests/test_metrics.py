import numpy as np

from analyzer.metrics import (
    calculate_brier_score,
    calculate_brier_skill_score,
    calculate_expected_calibration_error,
)


def test_brier_and_ece_perfection():
    # Skenario 1: Tebakan model 100% sempurna cocok dengan hasil riil pasar
    y_true = np.array([1, 0, 1, 0])
    y_prob = np.array([1.0, 0.0, 1.0, 0.0])

    bs = calculate_brier_score(y_true, y_prob)
    ece = calculate_expected_calibration_error(y_true, y_prob)

    assert bs == 0.0
    assert ece == 0.0


def test_brier_skill_score():
    # Skenario 2: Model lebih unggul daripada pembanding sederhana
    bs_model = 0.15
    bs_ref = 0.25

    bss = calculate_brier_skill_score(bs_model, bs_ref)
    assert bss == 0.40  # 1.0 - (0.15 / 0.25) = 0.40
