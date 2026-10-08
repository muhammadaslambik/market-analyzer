import numpy as np
from sklearn.isotonic import IsotonicRegression

PROB_FLOOR = 0.02
PROB_CEIL = 0.98


class ConfluenceCalibrator:
    """
    Mengkalibrasi skor konfluensi mentah menjadi probabilitas (0.0 - 1.0)
    menggunakan Isotonic Regression secara kausal (out-of-sample).
    """

    def __init__(self):
        self.ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self._frozen: tuple[np.ndarray, np.ndarray] | None = None  # dari to_dict/from_dict

    def fit(self, scores: np.ndarray, y_true: np.ndarray):
        """Melatih kalibrator pada data latihan."""
        if len(scores) == 0 or len(y_true) == 0:
            return self

        # Pastikan input berupa float64
        x = scores.astype(np.float64)
        y = y_true.astype(np.float64)

        self.ir.fit(x, y)
        self._frozen = None
        return self

    def calibrate(self, scores: np.ndarray) -> np.ndarray:
        """Mengonversi skor mentah menjadi probabilitas empiris terkalibrasi."""
        if len(scores) == 0:
            return np.array([])

        x = scores.astype(np.float64)
        if self._frozen is not None:
            probs = np.interp(x, self._frozen[0], self._frozen[1])
        else:
            probs = self.ir.predict(x)

        # Penanganan jika hasil regresi menghasilkan NaN
        return np.nan_to_num(probs, nan=0.5)

    def calibrate_clipped(self, scores: np.ndarray) -> np.ndarray:
        """Seperti calibrate, dijepit ke [0.02, 0.98] agar tidak ada peluang tepat 0 atau 1."""
        return np.clip(self.calibrate(scores), PROB_FLOOR, PROB_CEIL)

    def to_dict(self) -> dict:
        """Serialisasi ke JSON (titik-titik regresi isotonik)."""
        if self._frozen is not None:
            xs, ys = self._frozen
        else:
            xs, ys = self.ir.X_thresholds_, self.ir.y_thresholds_
        return {"type": "isotonic", "x": [float(v) for v in xs], "y": [float(v) for v in ys]}

    @classmethod
    def from_dict(cls, data: dict) -> "ConfluenceCalibrator":
        obj = cls()
        obj._frozen = (
            np.asarray(data["x"], dtype=np.float64),
            np.asarray(data["y"], dtype=np.float64),
        )
        return obj
