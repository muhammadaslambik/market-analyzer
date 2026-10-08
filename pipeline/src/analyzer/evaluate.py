"""Evaluasi walk-forward, gerbang rilis, laporan, dan pencatatan model_runs.

Mengikuti docs/SPEC-FASE-1.md Bagian 5. Hasil "eksperimental" adalah hasil yang sah.
Jalankan: python -m analyzer.evaluate --symbols BTCUSDT,ETHUSDT [--write-db]
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from analyzer.calibration import ConfluenceCalibrator
from analyzer.config import require_env
from analyzer.cv import generate_walk_forward_splits
from analyzer.data import load_candles
from analyzer.features import (
    VOL_ALPHA,
    WARMUP_ROWS,
    compute_confluence_features,
    compute_momentum_sign,
    compute_volatility,
)
from analyzer.gate import (
    ALPHA_FAMILY,
    COVERAGE_BAND,
    ECE_MAX,
    HOLDOUT_COVERAGE_BAND,
    MIN_OOS_SAMPLES,
    GateInputs,
    GateResult,
    evaluate_gates,
)
from analyzer.labels import compute_labels
from analyzer.metrics import (
    block_bootstrap_bss,
    calculate_brier_score,
    calculate_brier_skill_score,
    expected_calibration_error_equal_count,
    interval_coverage,
    pinball_loss,
    wilson_interval,
)
from analyzer.migrate import REPO_ROOT, load_env_file
from analyzer.ml_models import (
    TAUS,
    BaseRateModel,
    MomentumModel,
    UncondQuantileModel,
    VolQuantileModel,
)
from analyzer.store.neon import NeonStore

SERIES = [("1h", 4), ("1h", 24), ("1d", 1), ("1d", 7)]
SPLIT_DEFAULTS = {"1h": (6000, 720), "1d": (500, 60)}  # (latihan awal, blok uji)
HOLDOUT_FRACTION = 0.2
N_BOOT = 2000
FEATURE_SET = "confluence-3ind-v1"  # ema_ribbon, supertrend, adx (indikator lain masih stub)


@dataclass
class CandidateResult:
    name: str
    brier: float
    bss_vs_base: float
    ci_lower: float
    ci_upper: float
    bss_vs_momentum: float | None
    ece: float
    hit_rate: float
    hit_lo: float
    hit_hi: float
    holdout_bss: float | None
    holdout_coverage: float | None
    gate: GateResult
    artifact: dict[str, Any]


@dataclass
class SeriesResult:
    symbol: str
    timeframe: str
    horizon: int
    n_rows: int = 0
    n_dev: int = 0
    n_oos: int = 0
    n_holdout: int = 0
    brier_base: float = 0.0
    coverage: float = 0.0
    coverage_uncond: float = 0.0
    pinball_vol: float = 0.0
    pinball_uncond: float = 0.0
    candidates: dict[str, CandidateResult] = field(default_factory=dict)
    note: str | None = None

    @property
    def horizon_label(self) -> str:
        return f"{self.horizon}h" if self.timeframe == "1h" else f"{self.horizon}d"


def prepare_dataset(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Fitur kausal + label. Masa pemanasan dan baris tanpa label dibuang."""
    features = compute_confluence_features(df)
    realized, labels = compute_labels(df, horizon)
    data = pd.DataFrame(
        {
            "score": features["confluence_score"],
            "mom_sign": compute_momentum_sign(df, horizon),
            "sigma": compute_volatility(df) * np.sqrt(horizon),
            "ret": realized,
            "y": labels,
        }
    )
    data = data.iloc[WARMUP_ROWS:].dropna()
    return data[data["sigma"] > 0]


def _holdout(
    dev: pd.DataFrame, hold: pd.DataFrame, horizon: int, name: str
) -> tuple[float | None, float | None]:
    """Evaluasi holdout. Dipanggil paling banyak satu kali per kandidat."""
    if len(hold) < 2:
        return None, None
    train = dev.iloc[:-horizon] if len(dev) > horizon else dev
    y_train = train["y"].to_numpy()
    y_hold = hold["y"].to_numpy()
    base = float(np.mean(y_train == 1.0))
    if name == "confluence":
        calibrator = ConfluenceCalibrator().fit(train["score"].to_numpy(), y_train)
        prob = calibrator.calibrate_clipped(hold["score"].to_numpy())
    else:
        model = MomentumModel().fit(train["mom_sign"].to_numpy(), y_train)
        prob = model.predict_proba(hold["mom_sign"].to_numpy())
    bss = calculate_brier_skill_score(
        calculate_brier_score(y_hold, prob),
        calculate_brier_score(y_hold, np.full(len(y_hold), base)),
    )
    quantiles = (
        VolQuantileModel()
        .fit(train["ret"].to_numpy(), train["sigma"].to_numpy())
        .predict(hold["sigma"].to_numpy())
    )
    coverage = interval_coverage(hold["ret"].to_numpy(), quantiles[:, 0], quantiles[:, 2])
    return float(bss), coverage


def _fit_artifact(data: pd.DataFrame, timeframe: str, horizon: int, name: str) -> dict[str, Any]:
    """Model akhir dilatih pada semua data berlabel. Disimpan sebagai JSON."""
    y = data["y"].to_numpy()
    vol = VolQuantileModel().fit(data["ret"].to_numpy(), data["sigma"].to_numpy())
    artifact: dict[str, Any] = {
        "artifact_version": 1,
        "feature_set": FEATURE_SET,
        "timeframe": timeframe,
        "horizon": horizon,
        "model": name,
        "base_rate": float(np.mean(y == 1.0)),
        "vol_quantile": vol.to_dict(),
        "vol_alpha": VOL_ALPHA,
        "trained_rows": int(len(data)),
        "trained_until": data.index[-1].isoformat(),
    }
    if name == "confluence":
        artifact["calibrator"] = ConfluenceCalibrator().fit(data["score"].to_numpy(), y).to_dict()
    else:
        artifact["momentum"] = MomentumModel().fit(data["mom_sign"].to_numpy(), y).to_dict()
    return artifact


def evaluate_series(
    df: pd.DataFrame,
    symbol: str,
    timeframe: str,
    horizon: int,
    *,
    min_train: int | None = None,
    test_size: int | None = None,
    n_boot: int = N_BOOT,
    seed: int = 42,
) -> SeriesResult:
    default_train, default_test = SPLIT_DEFAULTS[timeframe]
    min_train = min_train or default_train
    test_size = test_size or default_test

    data = prepare_dataset(df, horizon)
    result = SeriesResult(symbol, timeframe, horizon, n_rows=len(data))
    split_point = int(len(data) * (1.0 - HOLDOUT_FRACTION))
    dev, hold = data.iloc[:split_point], data.iloc[split_point:]
    result.n_dev, result.n_holdout = len(dev), len(hold)

    needed = min_train + test_size
    if len(dev) < needed:
        result.note = f"Data tidak cukup: {len(dev)} baris pengembangan, butuh minimal {needed}."
        return result
    splits = generate_walk_forward_splits(dev, horizon, min_train, test_size)
    if not splits:
        result.note = "Tidak ada lipatan walk-forward yang terbentuk."
        return result

    collected: dict[str, list[np.ndarray]] = {
        k: [] for k in ("y", "ret", "base", "conf", "mom", "qvol", "qunc")
    }
    for train_idx, test_idx in splits:
        train, test = dev.loc[train_idx], dev.loc[test_idx]
        y_train = train["y"].to_numpy()
        base_model = BaseRateModel()
        base_model.fit(y_train)
        calibrator = ConfluenceCalibrator().fit(train["score"].to_numpy(), y_train)
        momentum = MomentumModel().fit(train["mom_sign"].to_numpy(), y_train)
        vol = VolQuantileModel().fit(train["ret"].to_numpy(), train["sigma"].to_numpy())
        uncond = UncondQuantileModel().fit(train["ret"].to_numpy())

        collected["y"].append(test["y"].to_numpy())
        collected["ret"].append(test["ret"].to_numpy())
        collected["base"].append(base_model.predict_proba(len(test)))
        collected["conf"].append(calibrator.calibrate_clipped(test["score"].to_numpy()))
        collected["mom"].append(momentum.predict_proba(test["mom_sign"].to_numpy()))
        collected["qvol"].append(vol.predict(test["sigma"].to_numpy()))
        collected["qunc"].append(uncond.predict(len(test)))

    y = np.concatenate(collected["y"])
    ret = np.concatenate(collected["ret"])
    p_base = np.concatenate(collected["base"])
    q_vol = np.vstack(collected["qvol"])
    q_unc = np.vstack(collected["qunc"])
    result.n_oos = len(y)
    result.brier_base = calculate_brier_score(y, p_base)
    result.coverage = interval_coverage(ret, q_vol[:, 0], q_vol[:, 2])
    result.coverage_uncond = interval_coverage(ret, q_unc[:, 0], q_unc[:, 2])
    result.pinball_vol = float(
        np.mean([pinball_loss(ret, q_vol[:, i], t) for i, t in enumerate(TAUS)])
    )
    result.pinball_uncond = float(
        np.mean([pinball_loss(ret, q_unc[:, i], t) for i, t in enumerate(TAUS)])
    )

    probs = {
        "confluence": np.concatenate(collected["conf"]),
        "momentum": np.concatenate(collected["mom"]),
    }
    brier_momentum = calculate_brier_score(y, probs["momentum"])
    for name, prob in probs.items():
        brier = calculate_brier_score(y, prob)
        bss = calculate_brier_skill_score(brier, result.brier_base)
        ci_lower, ci_upper = block_bootstrap_bss(
            y, prob, p_base, 2 * horizon, n_boot=n_boot, alpha=ALPHA_FAMILY, seed=seed
        )
        bss_momentum = (
            calculate_brier_skill_score(brier, brier_momentum) if name == "confluence" else None
        )
        ece = expected_calibration_error_equal_count(y, prob)
        hits = int(np.sum((prob >= 0.5) == (y == 1.0)))
        hit_lo, hit_hi = wilson_interval(hits, len(y))

        inputs = GateInputs(result.n_oos, ci_lower, bss_momentum, ece, result.coverage)
        gate = evaluate_gates(inputs, is_confluence=name == "confluence")
        holdout_bss = holdout_cov = None
        dev_ok = all(gate.gates[k] for k in ("G1", "G2", "G3", "G4", "G5"))
        if dev_ok:  # holdout hanya disentuh bila gerbang pengembangan lolos
            holdout_bss, holdout_cov = _holdout(dev, hold, horizon, name)
            inputs = GateInputs(
                result.n_oos, ci_lower, bss_momentum, ece, result.coverage, holdout_bss, holdout_cov
            )
            gate = evaluate_gates(inputs, is_confluence=name == "confluence")

        result.candidates[name] = CandidateResult(
            name=name,
            brier=brier,
            bss_vs_base=bss,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            bss_vs_momentum=bss_momentum,
            ece=ece,
            hit_rate=hits / len(y),
            hit_lo=hit_lo,
            hit_hi=hit_hi,
            holdout_bss=holdout_bss,
            holdout_coverage=holdout_cov,
            gate=gate,
            artifact=_fit_artifact(data, timeframe, horizon, name),
        )
    return result


def to_model_run_rows(result: SeriesResult) -> list[dict[str, Any]]:
    """Baris siap ditulis ke tabel model_runs (satu per kandidat)."""
    rows = []
    for name, cand in result.candidates.items():
        metrics = {
            "n_oos": result.n_oos,
            "n_dev": result.n_dev,
            "n_holdout": result.n_holdout,
            "brier": cand.brier,
            "brier_base": result.brier_base,
            "bss_vs_base": cand.bss_vs_base,
            "bss_ci_lower": cand.ci_lower,
            "bss_ci_upper": cand.ci_upper,
            "bss_vs_momentum": cand.bss_vs_momentum,
            "ece": cand.ece,
            "hit_rate": cand.hit_rate,
            "hit_lo": cand.hit_lo,
            "hit_hi": cand.hit_hi,
            "coverage": result.coverage,
            "coverage_uncond": result.coverage_uncond,
            "pinball_vol": result.pinball_vol,
            "pinball_uncond": result.pinball_uncond,
            "holdout_bss": cand.holdout_bss,
            "holdout_coverage": cand.holdout_coverage,
            "gates": cand.gate.gates,
            "alpha": ALPHA_FAMILY,
        }
        rows.append(
            {
                "version": f"crypto-{result.timeframe}-{result.horizon_label}-{name}-v1",
                "market": "crypto",
                "symbol": result.symbol,
                "timeframe": result.timeframe,
                "horizon": result.horizon_label,
                "metrics": metrics,
                "passed_gate": cand.gate.passed,
                "artifact": cand.artifact,
            }
        )
    return rows


def _mark(value: bool | None) -> str:
    return "-" if value is None else ("lolos" if value else "gagal")


def build_report(results: Sequence[SeriesResult], today: str | None = None) -> str:
    today = today or datetime.now(UTC).strftime("%Y-%m-%d")
    lines = [
        f"# Laporan Evaluasi — {today}",
        "",
        "Hasil walk-forward out-of-sample dengan gerbang rilis yang dibekukan "
        "(docs/SPEC-FASE-1.md Bagian 5.6). Status **eksperimental** adalah hasil yang sah, "
        "bukan kegagalan.",
        "",
        "## Ambang gerbang (dibekukan)",
        "",
        f"- G1: sampel out-of-sample >= {MIN_OOS_SAMPLES}",
        f"- G2: batas bawah BSS vs base_rate > 0 pada tingkat alpha = {ALPHA_FAMILY:.5f} (0,05/16)",
        "- G3: (confluence) BSS vs momentum >= 0",
        f"- G4: ECE <= {ECE_MAX}",
        f"- G5: cakupan q10 sampai q90 di {COVERAGE_BAND[0]:.2f} sampai {COVERAGE_BAND[1]:.2f}",
        f"- G6: holdout (sekali): BSS > 0 dan cakupan {HOLDOUT_COVERAGE_BAND[0]:.2f} "
        f"sampai {HOLDOUT_COVERAGE_BAND[1]:.2f}",
        "",
        f"Fitur: `{FEATURE_SET}` (hanya 3 indikator yang aktif).",
        "",
        "## Ringkasan",
        "",
        "| Seri | Model | n uji | BSS vs base | CI bawah | ECE | Cakupan | G1 | G2 | G3 | G4 | G5 "
        "| G6 | Status |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for res in results:
        if res.note:
            lines.append(
                f"| {res.symbol} {res.timeframe} {res.horizon_label} | - | - | - | - | - | - "
                f"| - | - | - | - | - | - | {res.note} |"
            )
            continue
        for name, c in res.candidates.items():
            g = c.gate.gates
            lines.append(
                f"| {res.symbol} {res.timeframe} {res.horizon_label} | {name} | {res.n_oos} "
                f"| {c.bss_vs_base:+.4f} | {c.ci_lower:+.4f} | {c.ece:.4f} | {res.coverage:.3f} "
                f"| {_mark(g['G1'])} | {_mark(g['G2'])} | {_mark(g['G3'])} | {_mark(g['G4'])} "
                f"| {_mark(g['G5'])} | {_mark(g['G6'])} | {c.gate.status} |"
            )
    lines += ["", "## Catatan", ""]
    for res in results:
        if res.note:
            continue
        lines.append(
            f"- {res.symbol} {res.timeframe} {res.horizon_label}: baris {res.n_rows} "
            f"(pengembangan {res.n_dev}, holdout {res.n_holdout}); "
            f"Brier base {res.brier_base:.4f}; "
            f"cakupan rentang vol {res.coverage:.3f} vs tanpa syarat {res.coverage_uncond:.3f}; "
            f"pinball vol {res.pinball_vol:.6f} vs tanpa syarat {res.pinball_uncond:.6f}."
        )
    return "\n".join(lines) + "\n"


def run_evaluation_pipeline(
    df: pd.DataFrame, symbol: str, timeframe: str, horizon: int, **kwargs: Any
) -> str:
    """Kompatibel dengan versi lama: evaluasi satu seri dan kembalikan laporan Markdown."""
    return build_report([evaluate_series(df, symbol, timeframe, horizon, **kwargs)])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluasi walk-forward market-analyzer.")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT")
    parser.add_argument("--report-dir", type=Path, default=REPO_ROOT / "docs" / "reports")
    parser.add_argument("--n-boot", type=int, default=N_BOOT)
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="tulis hasil ke model_runs (jalankan sekali per evaluasi resmi)",
    )
    args = parser.parse_args(argv)
    load_env_file(REPO_ROOT / ".env")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    store = NeonStore.connect(require_env("DATABASE_URL"))
    results: list[SeriesResult] = []
    try:
        for symbol in symbols:
            for timeframe, horizon in SERIES:
                frame = load_candles(store, symbol, timeframe)
                res = evaluate_series(frame, symbol, timeframe, horizon, n_boot=args.n_boot)
                results.append(res)
                status = ", ".join(f"{n}={c.gate.status}" for n, c in res.candidates.items())
                print(f"{symbol} {timeframe} {res.horizon_label}: {res.note or status}")
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        args.report_dir.mkdir(parents=True, exist_ok=True)
        path = args.report_dir / f"eval-{today}.md"
        path.write_text(build_report(results, today), encoding="utf-8")
        print(f"Laporan ditulis: {path}")
        if args.write_db:
            for res in results:
                for row in to_model_run_rows(res):
                    store.insert_model_run(**row)
            print("model_runs ditulis.")
        else:
            print("Dry-run: model_runs tidak ditulis (gunakan --write-db untuk pencatatan resmi).")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
