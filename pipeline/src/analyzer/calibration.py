import numpy as np
from sklearn.isotonic import IsotonicRegression


class ConfluenceCalibrator:
    """
    Mengkalibrasi skor konfluensi mentah menjadi probabilitas (0.0 - 1.0)
    menggunakan Isotonic Regression secara kausal (out-of-sample).
    """

    def __init__(self):
        self.ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)

    def fit(self, scores: np.ndarray, y_true: np.ndarray):
        """Melatih kalibrator pada data latihan."""
        if len(scores) == 0 or len(y_true) == 0:
            return self

        # Pastikan input berupa float64
        x = scores.astype(np.float64)
        y = y_true.astype(np.float64)

        self.ir.fit(x, y)
        return self

    def calibrate(self, scores: np.ndarray) -> np.ndarray:
        """Mengonversi skor mentah menjadi probabilitas empiris terkalibrasi."""
        if len(scores) == 0:
            return np.array([])

        x = scores.astype(np.float64)
        probs = self.ir.predict(x)

        # Penanganan jika hasil regresi menghasilkan NaN
        return np.nan_to_num(probs, nan=0.5)
