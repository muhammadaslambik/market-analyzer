import json

import numpy as np
import pandas as pd
from synthetic import KW, make_df, random_walk, regime_drift

from analyzer.evaluate import (
    build_report,
    evaluate_series,
    prepare_dataset,
    run_evaluation_pipeline,
    to_model_run_rows,
)
from analyzer.features import WARMUP_ROWS


def test_dataset_tanpa_nan_dan_tanpa_masa_pemanasan() -> None:
    df = make_df(random_walk(1)[:3000])
    data = prepare_dataset(df, 4)
    assert not data.isna().any().any()
    assert data.index[0] >= df.index[WARMUP_ROWS]
    assert data.index[-1] <= df.index[-1 - 4]  # baris tanpa label dibuang


def test_baris_model_runs_dapat_diserialisasi_json() -> None:
    result = evaluate_series(make_df(regime_drift(9, 0.004)), "BTCUSDT", "1h", 24, **KW)
    rows = to_model_run_rows(result)
    assert {r["version"] for r in rows} == {
        "crypto-1h-24h-confluence-v1",
        "crypto-1h-24h-momentum-v1",
    }
    json.dumps(rows)  # tidak boleh gagal (tanpa numpy yang tak bisa diserialisasi)
    first = rows[0]
    assert first["market"] == "crypto" and first["horizon"] == "24h"
    assert "calibrator" in rows[0]["artifact"] or "momentum" in rows[0]["artifact"]
    assert set(first["metrics"]["gates"]) == {"G1", "G2", "G3", "G4", "G5", "G6"}


def test_label_horizon_harian() -> None:
    df = make_df(random_walk(2)[:2500])
    daily = df.resample("1D").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )
    daily = daily.dropna()
    result = evaluate_series(daily, "BTCUSDT", "1d", 7, min_train=40, test_size=10, n_boot=100)
    assert result.horizon_label == "7d"


def test_laporan_memuat_ambang_dan_status() -> None:
    result = evaluate_series(make_df(random_walk(3)), "RW", "1h", 4, **KW)
    report = build_report([result], today="2026-10-07")
    assert "Laporan Evaluasi — 2026-10-07" in report
    assert "0,05/16" in report and "eksperimental" in report
    assert "RW 1h 4h" in report


def test_laporan_untuk_data_kurang_memuat_alasan() -> None:
    result = evaluate_series(make_df(random_walk(1)[:800]), "KECIL", "1h", 4)
    assert "Data tidak cukup" in build_report([result])


def test_run_evaluation_pipeline_kompatibel() -> None:
    report = run_evaluation_pipeline(make_df(random_walk(4)), "RW", "1h", 4, **KW)
    assert isinstance(report, str) and "eksperimental" in report


def test_hasil_deterministik() -> None:
    df = make_df(random_walk(5))
    a = evaluate_series(df, "RW", "1h", 4, **KW)
    b = evaluate_series(df, "RW", "1h", 4, **KW)
    assert a.candidates["confluence"].ci_lower == b.candidates["confluence"].ci_lower
    assert np.isclose(a.coverage, b.coverage) and isinstance(a.n_oos, int)
    assert isinstance(df, pd.DataFrame)
