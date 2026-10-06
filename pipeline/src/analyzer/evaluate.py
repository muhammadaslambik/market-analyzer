import os
import pandas as pd
import numpy as np
from datetime import datetime
from analyzer.labels import compute_labels
from analyzer.cv import generate_walk_forward_splits
from analyzer.features import compute_confluence_features
from analyzer.metrics import (
    calculate_brier_score,
    calculate_brier_skill_score,
    calculate_expected_calibration_error,
    moving_block_bootstrap_bss,
)
from analyzer.ml_models import BaseRateModel
from analyzer.calibration import ConfluenceCalibrator
from analyzer.gate import evaluate_release_gates


def run_evaluation_pipeline(df: pd.DataFrame, symbol: str, timeframe: str, horizon: int) -> str:
    """Runs walk-forward evaluation and returns a Markdown report summary."""
    # 1. Hitung fitur & label
    features = compute_confluence_features(df)
    realized_ret, labels = compute_labels(df, horizon)

    # Buat dataset gabungan, bersihkan baris kosong
    dataset = features.copy()
    dataset["y"] = labels
    dataset.dropna(subset=["y"], inplace=True)

    if len(dataset) < 600:
        return f"### Seri {symbol} {timeframe}: Data tidak mencukupi ({len(dataset)} baris)."

    # Split data: 80% pengembangan, 20% holdout dikunci
    split_point = int(len(dataset) * 0.8)
    dev_data = dataset.iloc[:split_point]
    holdout_data = dataset.iloc[split_point:]

    # 2. Jalankan Walk-Forward dengan Purging pada data pengembangan
    splits = generate_walk_forward_splits(dev_data, horizon, min_train_size=400, test_size=100)

    y_true_all = []
    y_prob_model_all = []
    y_prob_ref_all = []

    for train_idx, test_idx in splits:
        train_df = dev_data.loc[train_idx]
        test_df = dev_data.loc[test_idx]

        # Fit Base Rate (Reference)
        base_model = BaseRateModel()
        base_model.fit(train_df["y"].to_numpy())

        # Fit & Calibrate Confluence Model
        calibrator = ConfluenceCalibrator()
        calibrator.fit(train_df["confluence_score"].to_numpy(), train_df["y"].to_numpy())

        # Predict out-of-sample
        probs_ref = base_model.predict_proba(len(test_df))
        probs_model = calibrator.calibrate(test_df["confluence_score"].to_numpy())

        y_true_all.extend(test_df["y"].to_numpy())
        y_prob_model_all.extend(probs_model)
        y_prob_ref_all.extend(probs_ref)

    y_true = np.array(y_true_all)
    y_mod = np.array(y_prob_model_all)
    y_ref = np.array(y_prob_ref_all)

    if len(y_true) == 0:
        return "Gagal mengumpulkan sampel out-of-sample."

    # 3. Hitung Metrik Evaluasi Kuantitatif
    bs_model = calculate_brier_score(y_true, y_mod)
    bs_ref = calculate_brier_score(y_true, y_ref)
    bss = calculate_brier_skill_score(bs_model, bs_ref)
    ece = calculate_expected_calibration_error(y_true, y_mod)
    ci_low, ci_high = moving_block_bootstrap_bss(y_true, y_mod, y_ref, horizon, n_splits=50)

    # 4. Filter melalui Gerbang Rilis
    gate_res = evaluate_release_gates(len(y_true), bss, ci_low, ece)

    # 5. Susun Laporan Markdown
    report = f"""
## Hasil Evaluasi Seri: {symbol} {timeframe} (Horizon: {horizon}h)
- **Jumlah Sampel Uji (Out-of-Sample):** {len(y_true)}
- **Brier Score Model:** {bs_model:.4f} (Reference: {bs_ref:.4f})
- **Brier Skill Score (BSS):** {bss:.4f}
- **95% BSS Confidence Interval:** [{ci_low:.4f}, {ci_high:.4f}]
- **Expected Calibration Error (ECE):** {ece:.4f}
- **Status Akhir Model:** **{gate_res["status"].upper()}**
"""
    return report
