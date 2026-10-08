from dataclasses import dataclass


def evaluate_release_gates(n_samples: int, bss_ref: float, bss_ci_lower: float, ece: float) -> dict:
    """Memeriksa pemenuhan kriteria ketat gerbang rilis G1 sampai G4."""
    g1 = n_samples >= 500
    g2 = bss_ci_lower > 0
    g4 = ece <= 0.05

    passed = bool(g1 and g2 and g4)

    return {
        "passed_all": passed,
        "gates": {"G1_samples": g1, "G2_bss_ci": g2, "G4_ece": g4},
        "status": "ok" if passed else "eksperimental",
    }


# ---- Gerbang rilis lengkap sesuai docs/SPEC-FASE-1.md Bagian 5.6 (dibekukan) ----
MIN_OOS_SAMPLES = 500
ALPHA_FAMILY = 0.05 / 16  # koreksi Bonferroni: 8 seri x 2 model kandidat
ECE_MAX = 0.05
COVERAGE_BAND = (0.75, 0.85)
HOLDOUT_COVERAGE_BAND = (0.70, 0.90)


@dataclass(frozen=True)
class GateInputs:
    n_oos: int
    bss_ci_lower: float  # batas bawah BSS vs base_rate pada tingkat ALPHA_FAMILY
    bss_vs_momentum: float | None  # hanya dipakai untuk model confluence
    ece: float
    coverage: float  # cakupan q10-q90 dari model rentang, data pengembangan
    holdout_bss: float | None = None
    holdout_coverage: float | None = None


@dataclass(frozen=True)
class GateResult:
    gates: dict[str, bool | None]  # None = tidak dievaluasi
    passed: bool
    status: str  # 'ok' | 'eksperimental'


def evaluate_gates(inputs: GateInputs, *, is_confluence: bool) -> GateResult:
    """G1 sampai G6. G6 (holdout) hanya bermakna bila G1 sampai G5 lolos."""
    g1 = inputs.n_oos >= MIN_OOS_SAMPLES
    g2 = inputs.bss_ci_lower > 0
    if is_confluence:
        g3 = inputs.bss_vs_momentum is not None and inputs.bss_vs_momentum >= 0
    else:
        g3 = True
    g4 = inputs.ece <= ECE_MAX
    g5 = COVERAGE_BAND[0] <= inputs.coverage <= COVERAGE_BAND[1]

    g6: bool | None = None
    if all((g1, g2, g3, g4, g5)) and inputs.holdout_bss is not None:
        cov = inputs.holdout_coverage
        g6 = bool(
            inputs.holdout_bss > 0
            and cov is not None
            and HOLDOUT_COVERAGE_BAND[0] <= cov <= HOLDOUT_COVERAGE_BAND[1]
        )
    passed = bool(all((g1, g2, g3, g4, g5)) and g6 is True)
    gates = {"G1": g1, "G2": g2, "G3": g3, "G4": g4, "G5": g5, "G6": g6}
    return GateResult(gates, passed, "ok" if passed else "eksperimental")
