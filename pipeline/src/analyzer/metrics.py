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
