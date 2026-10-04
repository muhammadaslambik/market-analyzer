"""Trend indicators: EMA ribbon, Supertrend, ADX (trend-strength filter)."""

import numpy as np
import pandas as pd

from .base import BULL, BEAR, NEUTRAL, register


def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False).mean()


@register("ema_ribbon")
def ema_ribbon(df: pd.DataFrame, fast: int = 20, mid: int = 50, slow: int = 200) -> pd.Series:
    """+1 when close is above all three EMAs and they are ordered, -1 when below
    all and inverted, else 0."""
    c, ef, em, es = df["close"], ema(df["close"], fast), ema(df["close"], mid), ema(df["close"], slow)
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[(c > ef) & (ef > em) & (em > es)] = BULL
    sig[(c < ef) & (ef < em) & (em < es)] = BEAR
    return sig


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"],
                    (df["high"] - pc).abs(),
                    (df["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()


@register("supertrend")
def supertrend(df: pd.DataFrame, n: int = 10, mult: float = 3.0) -> pd.Series:
    hl2 = (df["high"] + df["low"]) / 2
    a = atr(df, n).to_numpy()
    up, lo = (hl2 + mult * a).to_numpy(), (hl2 - mult * a).to_numpy()
    h, l, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy()
    sig = np.zeros(len(df), dtype=int)
    st_up, st_lo, dirn = up[0], lo[0], 1
    for i in range(len(df)):
        if i > 0:
            st_up = up[i] if (up[i] < st_up or c[i - 1] > st_up) else st_up
            st_lo = lo[i] if (lo[i] > st_lo or c[i - 1] < st_lo) else st_lo
        if c[i] > st_up:
            dirn = 1
        elif c[i] < st_lo:
            dirn = -1
        sig[i] = dirn
    return pd.Series(sig, index=df.index)


@register("adx")
def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """+1 when ADX > 25 and +DI > -DI (strong uptrend), -1 mirror, else 0.
    Below ADX 20 the market is ranging -> NEUTRAL so the confluence filter
    can force WAIT."""
    up, dn = df["high"].diff(), -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(),
                    (df["low"] - pc).abs()], axis=1).max(axis=1)
    atr_s = tr.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1 / n, min_periods=n, adjust=False).mean() / atr_s
    mdi = 100 * mdm.ewm(alpha=1 / n, min_periods=n, adjust=False).mean() / atr_s
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    adx_v = dx.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[(adx_v > 25) & (pdi > mdi)] = BULL
    sig[(adx_v > 25) & (mdi > pdi)] = BEAR
    return sig


def adx_value(df: pd.DataFrame, n: int = 14) -> float:
    """Raw ADX number (used by the global sideways filter)."""
    up, dn = df["high"].diff(), -df["low"].diff()
    pdm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    mdm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    pc = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(),
                    (df["low"] - pc).abs()], axis=1).max(axis=1)
    atr_s = tr.ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1 / n, min_periods=n, adjust=False).mean() / atr_s
    mdi = 100 * mdm.ewm(alpha=1 / n, min_periods=n, adjust=False).mean() / atr_s
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return float(dx.ewm(alpha=1 / n, min_periods=n, adjust=False).mean().iloc[-1])
