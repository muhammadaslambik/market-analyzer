import numpy as np
import pandas as pd


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def compute_ema_ribbon(df: pd.DataFrame) -> pd.Series:
    c = df["close"]
    ef = calculate_ema(c, 20)
    em = calculate_ema(c, 50)
    es = calculate_ema(c, 200)

    sig = pd.Series(0, index=df.index)
    sig[(c > ef) & (ef > em) & (em > es)] = 1
    sig[(c < ef) & (ef < em) & (em < es)] = -1
    return sig


def compute_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2
    atr_v = calculate_atr(df, period).to_numpy()

    up = (hl2 + multiplier * atr_v).to_numpy()
    lo = (hl2 - multiplier * atr_v).to_numpy()
    close = df["close"].to_numpy()

    sig = np.zeros(len(df), dtype=int)
    if len(df) == 0:
        return pd.Series(sig, index=df.index)

    st_up, st_lo, direction = up[0], lo[0], 1

    for i in range(len(df)):
        if i > 0:
            st_up = up[i] if (up[i] < st_up or close[i - 1] > st_up) else st_up
            st_lo = lo[i] if (lo[i] > st_lo or close[i - 1] < st_lo) else st_lo
        if close[i] > st_up:
            direction = 1
        elif close[i] < st_lo:
            direction = -1
        sig[i] = direction
    return pd.Series(sig, index=df.index)


def compute_adx_signals(df: pd.DataFrame, period: int = 14) -> tuple[pd.Series, pd.Series]:
    up = df["high"].diff()
    dn = -df["low"].diff()

    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)

    atr_s = calculate_atr(df, period)
    pdi = 100 * pdm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_s
    mdi = 100 * mdm.ewm(alpha=1 / period, min_periods=period, adjust=False).mean() / atr_s

    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    adx_v = dx.ewm(alpha=1 / period, min_periods=period, adjust=False).mean().fillna(0)

    sig = pd.Series(0, index=df.index)
    sig[(adx_v > 25) & (pdi > mdi)] = 1
    sig[(adx_v > 25) & (mdi > pdi)] = -1
    return sig, adx_v


def compute_confluence_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menyusun matriks sinyal dan menghitung skor akhir konfluensi skala [-100, 100].
    """
    features = pd.DataFrame(index=df.index)

    # 1. Hitung Sinyal-Sinyal Utama
    features["ema_ribbon"] = compute_ema_ribbon(df)
    features["supertrend"] = compute_supertrend(df)
    adx_sig, adx_val = compute_adx_signals(df)
    features["adx"] = adx_sig

    # Tambah placeholder stub netral (0) untuk sisa indikator agar pembobotan adil
    for stub in ["macd", "bollinger", "vwap_signal", "cvd", "volume_profile"]:
        features[stub] = 0

    # 2. Definisikan Struktur Bobot Asli dari YAML Proyek
    weights = {
        "ema_ribbon": 12,
        "supertrend": 12,
        "macd": 10,
        "bollinger": 8,
        "vwap_signal": 10,
        "cvd": 12,
        "adx": 8,
        "volume_profile": 6,
    }

    total_w = sum(weights.values())

    # Hitung rata-rata tertimbang dikali 100
    weighted_sum = sum(features[name] * w for name, w in weights.items())
    raw_score = (weighted_sum / total_w) * 100

    # Terapkan filter ADX Sideways jika ADX < 20
    features["confluence_score"] = np.where(adx_val < 20.0, 0.0, raw_score)
    features["confluence_score"] = np.clip(features["confluence_score"], -100.0, 100.0)

    return features
