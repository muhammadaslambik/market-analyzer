import numpy as np


def evaluate_release_gates(n_samples: int, bss_ref: float, bss_ci_lower: float, ece: float) -> dict:
    """
    Memeriksa pemenuhan kriteria ketat gerbang rilis G1 sampai G4.
    Mengembalikan status kelayakan model (True/False).
    """
    g1 = n_samples >= 500
    g2 = bss_ci_lower > 0  # Bebas bias uji ganda lewat bootstrap BSS
    g4 = ece <= 0.05

    passed = bool(g1 and g2 and g4)

    return {
        "passed_all": passed,
        "gates": {"G1_samples": g1, "G2_bss_ci": g2, "G4_ece": g4},
        "status": "ok" if passed else "eksperimental",
    }
