import numpy as np


def calculate_brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float(np.mean((y_prob - y_true) ** 2))


def calculate_brier_skill_score(brier_model: float, brier_reference: float) -> float:
    if brier_reference == 0:
        return 0.0 if brier_model == 0 else -np.inf
    return float(1.0 - (brier_model / brier_reference))


def calculate_expected_calibration_error(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> float:
    if len(y_true) == 0:
        return 0.0

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_edges[i]
        bin_upper = bin_edges[i + 1]

        in_bin = (
            (y_prob >= bin_lower) & (y_prob < bin_upper)
            if i < n_bins - 1
            else (y_prob >= bin_lower) & (y_prob <= bin_upper)
        )
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += prop_in_bin * np.abs(bin_acc - bin_conf)

    return float(ece)


def moving_block_bootstrap_bss(
    y_true: np.ndarray,
    y_prob_model: np.ndarray,
    y_prob_ref: np.ndarray,
    horizon: int,
    n_splits: int = 10,
    seed: int = 42,
) -> tuple[float, float]:
    np.random.seed(seed)
    n = len(y_true)
    block_length = max(2 * horizon, 1)

    if n <= block_length:
        bs_model = calculate_brier_score(y_true, y_prob_model)
        bs_ref = calculate_brier_score(y_true, y_prob_ref)
        bss = calculate_brier_skill_score(bs_model, bs_ref)
        return bss, bss

    bss_distribution = []
    n_blocks = int(np.ceil(n / block_length))

    for _ in range(n_splits):
        start_indices = np.random.randint(0, n - block_length + 1, size=n_blocks)

        boot_indices = []
        for start in start_indices:
            boot_indices.extend(range(start, start + block_length))
        boot_indices = np.array(boot_indices[:n])

        bs_m = calculate_brier_score(y_true[boot_indices], y_prob_model[boot_indices])
        bs_r = calculate_brier_score(y_true[boot_indices], y_prob_ref[boot_indices])
        bss_distribution.append(calculate_brier_skill_score(bs_m, bs_r))

    ci_lower = float(np.percentile(bss_distribution, 2.5))
    ci_upper = float(np.percentile(bss_distribution, 97.5))

    return ci_lower, ci_upper


def expected_calibration_error_equal_count(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> float:
    """ECE dengan bin berisi sama banyak (sesuai SPEC-FASE-1 Bagian 5.5)."""
    n = len(y_true)
    if n == 0:
        return 0.0
    order = np.argsort(y_prob, kind="stable")
    ece = 0.0
    for chunk in np.array_split(order, n_bins):
        if len(chunk) == 0:
            continue
        ece += (len(chunk) / n) * abs(float(np.mean(y_true[chunk])) - float(np.mean(y_prob[chunk])))
    return float(ece)


def block_bootstrap_bss(
    y_true: np.ndarray,
    p_model: np.ndarray,
    p_ref: np.ndarray,
    block_length: int,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 42,
    batch: int = 250,
) -> tuple[float, float]:
    """Moving-block bootstrap untuk BSS.

    Mengembalikan (batas bawah satu sisi pada tingkat `alpha`, batas atas pada `1 - alpha`).
    Memakai generator acak lokal (tidak mengubah seed global).
    """
    n = len(y_true)
    se_model = (p_model - y_true) ** 2
    se_ref = (p_ref - y_true) ** 2
    if n == 0:
        return 0.0, 0.0
    length = min(max(int(block_length), 1), n)
    n_blocks = int(np.ceil(n / length))
    offsets = np.arange(length)
    rng = np.random.default_rng(seed)
    samples: list[np.ndarray] = []
    done = 0
    while done < n_boot:
        size = min(batch, n_boot - done)
        starts = rng.integers(0, n - length + 1, size=(size, n_blocks))
        idx = (starts[:, :, None] + offsets[None, None, :]).reshape(size, -1)[:, :n]
        bs_model = se_model[idx].mean(axis=1)
        bs_ref = se_ref[idx].mean(axis=1)
        with np.errstate(divide="ignore", invalid="ignore"):
            samples.append(np.where(bs_ref > 0, 1.0 - bs_model / bs_ref, -np.inf))
        done += size
    dist = np.concatenate(samples)
    return float(np.quantile(dist, alpha)), float(np.quantile(dist, 1.0 - alpha))


def pinball_loss(y_true: np.ndarray, q_pred: np.ndarray, tau: float) -> float:
    diff = y_true - q_pred
    return float(np.mean(np.maximum(tau * diff, (tau - 1.0) * diff)))


def interval_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    if len(y_true) == 0:
        return 0.0
    return float(np.mean((y_true >= lower) & (y_true <= upper)))


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = successes / n
    denom = 1.0 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return float(center - margin), float(center + margin)
