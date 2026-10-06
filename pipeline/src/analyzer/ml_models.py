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
