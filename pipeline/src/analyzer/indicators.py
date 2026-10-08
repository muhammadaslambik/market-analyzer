"""Indikator teknikal kausal — hanya memakai data yang sudah lewat (shift).

Aturan kausalitas: nilai indikator di bar t TIDAK BOLEH memakai
harga bar t (close t). Semua indikator di sini dihitung lalu di-shift 1 bar,
sehingga fitur di bar t = indikator yang selesai di bar t-1.

Aturan warm-up: bar dengan data belum cukup = NaN, TIDAK BOLEH diisi nilai.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _shift(s: pd.Series) -> pd.Series:
    """Shift 1 bar agar tidak ada kebocoran bar saat ini."""
    return s.shift(1)


def ema(series: pd.Series, span: int) -> pd.Series:
    """EMA dengan warm-up: span bar pertama = NaN (belum cukup data)."""
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
         ) -> pd.DataFrame:
    """MACD line, signal line, histogram. Output sudah kausal (shift 1).
    macd valid mulai bar ke-slow; macd_signal/hist mulai bar ke-slow+signal."""
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal)
    out = pd.DataFrame({
        "macd": macd_line,
        "macd_signal": signal_line,
        "macd_hist": macd_line - signal_line,
    })
    return out.apply(_shift)


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI Wilder. Output kausal (shift 1).
    Kasus avg_loss == 0 (uptrend murni) → RSI 100.
    Bar warm-up tetap NaN (tidak diisi 100)."""
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period,
                        adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period,
                        adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    # isi 100 hanya untuk uptrend murni yang datanya sudah cukup
    out = out.mask(avg_loss.eq(0.0) & avg_gain.gt(0.0) & avg_gain.notna(), 100.0)
    return _shift(out)


def bollinger(close: pd.Series, period: int = 20, n_std: float = 2.0
              ) -> pd.DataFrame:
    """Bollinger Bands (SMA ± n*std) + posisi %B & bandwidth. Kausal (shift 1)."""
    mid = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std(ddof=0)
    upper = mid + n_std * std
    lower = mid - n_std * std
    band_width = (upper - lower) / mid.replace(0.0, np.nan)
    pct_b = (close - lower) / (upper - lower).replace(0.0, np.nan)
    out = pd.DataFrame({
        "bb_mid": mid,
        "bb_upper": upper,
        "bb_lower": lower,
        "bb_bandwidth": band_width,
        "bb_pct_b": pct_b,
    })
    return out.apply(_shift)


def vwap(df: pd.DataFrame, day_col: str | None = None,
         bars_per_session: int = 24) -> pd.Series:
    """Session VWAP, reset per hari. Butuh kolom high, low, close, volume.
    Kausal: output di-shift 1 (nilai sesi bar t-1).

    - day_col diberikan  → reset per nilai kolom tsb.
    - day_col None dan index datetime → reset per tanggal kalender (UTC).
    - day_col None dan index bukan datetime → rolling bars_per_session bar
      (wajib dipanggil dengan nilai yang benar per timeframe:
      1h→24, 4h→6, 1d→1)."""
    price = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].clip(lower=0.0)
    pv = price * vol

    if day_col is not None:
        day = df[day_col]
        cum_pv = pv.groupby(day).cumsum()
        cum_v = vol.groupby(day).cumsum()
    elif df.index.dtype.kind in "MO":
        day = pd.to_datetime(df.index).date
        cum_pv = pv.groupby(day).cumsum()
        cum_v = vol.groupby(day).cumsum()
    else:
        cum_pv = pv.rolling(bars_per_session, min_periods=1).sum()
        cum_v = vol.rolling(bars_per_session, min_periods=1).sum()

    out = cum_pv / cum_v.replace(0.0, np.nan)
    return _shift(out)


def build_features(df: pd.DataFrame, bars_per_session: int = 24
                   ) -> pd.DataFrame:
    """Gabungkan semua indikator menjadi matriks fitur.

    Input: DataFrame OHLCV dengan kolom open/high/low/close/volume,
    index datetime (1 bar = 1 periode).
    Output: fitur kausal siap dipakai model (tanpa kolom harga mentah).
    """
    close = df["close"]
    feats = pd.DataFrame(index=df.index)
    feats["rsi_14"] = rsi(close)
    feats["ret_1"] = close.pct_change(1).shift(1)
    feats["ret_6"] = close.pct_change(6).shift(1)
    feats["ret_24"] = close.pct_change(24).shift(1)
    feats = feats.join(macd(close)).join(bollinger(close))
    feats["vwap_dist"] = close.shift(1) / vwap(df, bars_per_session=bars_per_session) - 1.0
    return feats
