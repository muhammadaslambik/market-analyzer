import numpy as np


class BaseRateModel:
    """Model pembanding sederhana (baseline) berbasis frekuensi dasar data."""

    def __init__(self):
        self.base_rate = 0.5

    def fit(self, y_train: np.ndarray):
        if len(y_train) > 0:
            self.base_rate = float(np.mean(y_train == 1.0))
        else:
            self.base_rate = 0.5

    def predict_proba(self, n_samples: int) -> np.ndarray:
        return np.full(n_samples, self.base_rate)


SMOOTHING = 20.0  # bobot semu menuju frekuensi dasar saat sampel suatu keadaan sedikit
TAUS = (0.1, 0.5, 0.9)


class MomentumModel:
    """Peluang naik dari tanda return h candle terakhir, dengan penghalusan ke frekuensi dasar."""

    def __init__(self):
        self.base_rate = 0.5
        self.table: dict[int, float] = {-1: 0.5, 0: 0.5, 1: 0.5}

    def fit(self, mom_sign: np.ndarray, y_train: np.ndarray):
        if len(y_train) == 0:
            return self
        self.base_rate = float(np.mean(y_train == 1.0))
        signs = np.sign(mom_sign).astype(int)
        for state in (-1, 0, 1):
            mask = signs == state
            ups = float(np.sum(y_train[mask] == 1.0))
            self.table[state] = (ups + SMOOTHING * self.base_rate) / (mask.sum() + SMOOTHING)
        return self

    def predict_proba(self, mom_sign: np.ndarray) -> np.ndarray:
        signs = np.sign(mom_sign).astype(int)
        return np.array([self.table[int(s)] for s in signs], dtype=float)

    def to_dict(self) -> dict:
        return {
            "type": "momentum",
            "base_rate": self.base_rate,
            "table": {str(k): v for k, v in self.table.items()},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MomentumModel":
        obj = cls()
        obj.base_rate = float(data["base_rate"])
        obj.table = {int(k): float(v) for k, v in data["table"].items()}
        return obj


class VolQuantileModel:
    """Rentang q10, q50, q90 = kuantil empiris (return / volatilitas) x volatilitas saat ini."""

    def __init__(self):
        self.z = np.zeros(len(TAUS))

    def fit(self, ret: np.ndarray, sigma: np.ndarray):
        mask = np.isfinite(ret) & np.isfinite(sigma) & (sigma > 0)
        if mask.sum() > 0:
            self.z = np.quantile(ret[mask] / sigma[mask], TAUS)
        return self

    def predict(self, sigma: np.ndarray) -> np.ndarray:
        return sigma[:, None] * self.z[None, :]

    def to_dict(self) -> dict:
        return {"type": "vol_quantile", "taus": list(TAUS), "z": [float(v) for v in self.z]}

    @classmethod
    def from_dict(cls, data: dict) -> "VolQuantileModel":
        obj = cls()
        obj.z = np.asarray(data["z"], dtype=float)
        return obj


class UncondQuantileModel:
    """Pembanding rentang: kuantil empiris return tanpa syarat."""

    def __init__(self):
        self.q = np.zeros(len(TAUS))

    def fit(self, ret: np.ndarray):
        finite = ret[np.isfinite(ret)]
        if len(finite) > 0:
            self.q = np.quantile(finite, TAUS)
        return self

    def predict(self, n_samples: int) -> np.ndarray:
        return np.tile(self.q, (n_samples, 1))
