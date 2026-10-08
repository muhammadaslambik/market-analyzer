"""Uji sanity kerangka evaluasi (SPEC-FASE-1 Bagian 5.7).

Kerangka harus (a) tidak meloloskan model pada data acak, dan (b) meloloskan model pada data
yang sinyalnya sengaja ditanam. Tanpa (b), hasil "eksperimental" bisa muncul hanya karena
kerangka tidak pernah mampu meloloskan apa pun.
"""

import pytest
from synthetic import KW, ar1, make_df, random_walk, regime_drift

from analyzer.evaluate import evaluate_series


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_random_walk_tidak_ada_model_lolos(seed: int) -> None:
    result = evaluate_series(make_df(random_walk(seed)), "RW", "1h", 4, **KW)
    assert result.n_oos >= 500  # gagal bukan karena sampel kurang
    for name, cand in result.candidates.items():
        assert cand.gate.gates["G1"] is True, name
        assert cand.gate.gates["G2"] is False, name  # tidak ada keunggulan statistik
        assert cand.gate.passed is False and cand.gate.status == "eksperimental", name
        assert cand.holdout_bss is None, name  # holdout tidak disentuh


def test_sinyal_autokorelasi_tertanam_meloloskan_momentum() -> None:
    result = evaluate_series(make_df(ar1(7, 0.7)), "AR", "1h", 4, **KW)
    cand = result.candidates["momentum"]
    assert cand.bss_vs_base > 0.03 and cand.ci_lower > 0
    assert all(cand.gate.gates[g] is True for g in ("G1", "G2", "G3", "G4", "G5", "G6"))
    assert cand.gate.passed and cand.gate.status == "ok"


def test_sinyal_rezim_tertanam_meloloskan_confluence() -> None:
    result = evaluate_series(make_df(regime_drift(9, 0.004)), "RG", "1h", 4, **KW)
    cand = result.candidates["confluence"]
    assert cand.bss_vs_base > 0.1 and cand.ci_lower > 0
    assert all(cand.gate.gates[g] is True for g in ("G1", "G2", "G3", "G4", "G5", "G6"))
    assert cand.gate.passed and cand.holdout_bss is not None and cand.holdout_bss > 0


def test_data_terlalu_sedikit_tidak_pernah_dianggap_lolos() -> None:
    result = evaluate_series(make_df(random_walk(1)[:800]), "KECIL", "1h", 4)
    assert result.note and not result.candidates
