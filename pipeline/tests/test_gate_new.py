import pytest

from analyzer.gate import ALPHA_FAMILY, GateInputs, evaluate_gates, evaluate_release_gates


def good(**kw) -> GateInputs:
    base = {
        "n_oos": 1000,
        "bss_ci_lower": 0.01,
        "bss_vs_momentum": 0.005,
        "ece": 0.03,
        "coverage": 0.80,
        "holdout_bss": 0.01,
        "holdout_coverage": 0.80,
    }
    base.update(kw)
    return GateInputs(**base)


def test_semua_lolos() -> None:
    result = evaluate_gates(good(), is_confluence=True)
    assert result.passed and result.status == "ok"
    assert all(result.gates[g] is True for g in ("G1", "G2", "G3", "G4", "G5", "G6"))


@pytest.mark.parametrize(
    ("override", "gate"),
    [
        ({"n_oos": 499}, "G1"),
        ({"bss_ci_lower": 0.0}, "G2"),
        ({"bss_vs_momentum": -0.001}, "G3"),
        ({"ece": 0.0501}, "G4"),
        ({"coverage": 0.74}, "G5"),
        ({"coverage": 0.86}, "G5"),
    ],
)
def test_satu_gerbang_gagal_membuat_status_eksperimental(override: dict, gate: str) -> None:
    result = evaluate_gates(good(**override), is_confluence=True)
    assert result.gates[gate] is False
    assert not result.passed and result.status == "eksperimental"
    assert result.gates["G6"] is None  # holdout tidak dinilai bila gerbang pengembangan gagal


def test_batas_tepat_lolos() -> None:
    result = evaluate_gates(good(n_oos=500, ece=0.05, coverage=0.75), is_confluence=True)
    assert result.passed
    assert evaluate_gates(good(coverage=0.85), is_confluence=True).passed


def test_g3_tidak_berlaku_untuk_momentum() -> None:
    result = evaluate_gates(good(bss_vs_momentum=None), is_confluence=False)
    assert result.gates["G3"] is True and result.passed
    assert evaluate_gates(good(bss_vs_momentum=None), is_confluence=True).gates["G3"] is False


@pytest.mark.parametrize(
    "override", [{"holdout_bss": 0.0}, {"holdout_coverage": 0.69}, {"holdout_coverage": 0.91}]
)
def test_holdout_gagal(override: dict) -> None:
    result = evaluate_gates(good(**override), is_confluence=True)
    assert result.gates["G6"] is False and not result.passed


def test_tanpa_data_holdout_tidak_lolos() -> None:
    result = evaluate_gates(good(holdout_bss=None, holdout_coverage=None), is_confluence=True)
    assert result.gates["G6"] is None and not result.passed


def test_alpha_bonferroni_dibekukan() -> None:
    assert ALPHA_FAMILY == pytest.approx(0.05 / 16)


def test_fungsi_lama_tetap_berjalan() -> None:
    assert evaluate_release_gates(600, 0.1, 0.01, 0.03)["passed_all"] is True
