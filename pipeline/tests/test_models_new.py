import json

import numpy as np

from analyzer.calibration import PROB_CEIL, PROB_FLOOR, ConfluenceCalibrator
from analyzer.ml_models import MomentumModel, UncondQuantileModel, VolQuantileModel


def test_momentum_menangkap_informasi_dan_roundtrip_json() -> None:
    rng = np.random.default_rng(1)
    sign = rng.choice([-1.0, 0.0, 1.0], size=3000)
    y = (rng.random(3000) < np.where(sign > 0, 0.7, np.where(sign < 0, 0.3, 0.5))).astype(float)
    model = MomentumModel().fit(sign, y)
    assert model.table[1] > 0.6 > 0.4 > model.table[-1]
    restored = MomentumModel.from_dict(json.loads(json.dumps(model.to_dict())))
    probe = np.array([-1.0, 0.0, 1.0, 1.0])
    assert np.array_equal(model.predict_proba(probe), restored.predict_proba(probe))


def test_momentum_penghalusan_untuk_keadaan_langka() -> None:
    sign = np.array([1.0] * 200 + [-1.0])
    y = np.array([1.0] * 100 + [0.0] * 100 + [1.0])
    model = MomentumModel().fit(sign, y)
    assert 0.3 < model.table[-1] < 0.7  # satu sampel tidak boleh menghasilkan 0 atau 1


def test_kalibrator_roundtrip_menghasilkan_prediksi_identik() -> None:
    rng = np.random.default_rng(2)
    scores = rng.choice([-30.0, 0.0, 20.0, 41.0], size=2000)
    y = (rng.random(2000) < 0.5 + scores / 200).astype(float)
    calibrator = ConfluenceCalibrator().fit(scores, y)
    restored = ConfluenceCalibrator.from_dict(json.loads(json.dumps(calibrator.to_dict())))
    probe = np.array([-100.0, -30.0, -5.0, 0.0, 10.0, 20.0, 41.0, 100.0])
    assert np.allclose(calibrator.calibrate(probe), restored.calibrate(probe), atol=1e-12)
    assert np.allclose(
        calibrator.calibrate_clipped(probe), restored.calibrate_clipped(probe), atol=1e-12
    )


def test_kalibrator_dijepit() -> None:
    scores = np.array([-10.0] * 50 + [10.0] * 50)
    y = np.array([0.0] * 50 + [1.0] * 50)
    probs = ConfluenceCalibrator().fit(scores, y).calibrate_clipped(scores)
    assert probs.min() >= PROB_FLOOR and probs.max() <= PROB_CEIL


def test_kuantil_volatilitas_cakupan_mendekati_80_persen() -> None:
    rng = np.random.default_rng(3)
    sigma_train = rng.uniform(0.5, 2.0, 5000)
    sigma_test = rng.uniform(0.5, 2.0, 5000)
    ret_train = rng.normal(0, 1, 5000) * sigma_train
    ret_test = rng.normal(0, 1, 5000) * sigma_test
    model = VolQuantileModel().fit(ret_train, sigma_train)
    q = model.predict(sigma_test)
    covered = np.mean((ret_test >= q[:, 0]) & (ret_test <= q[:, 2]))
    assert abs(covered - 0.8) < 0.03
    restored = VolQuantileModel.from_dict(json.loads(json.dumps(model.to_dict())))
    assert np.allclose(restored.predict(sigma_test), q)


def test_kuantil_tanpa_syarat() -> None:
    ret = np.random.default_rng(4).normal(0, 1, 2000)
    q = UncondQuantileModel().fit(ret).predict(3)
    assert q.shape == (3, 3) and np.all(q[:, 0] < q[:, 1]) and np.all(q[:, 1] < q[:, 2])
