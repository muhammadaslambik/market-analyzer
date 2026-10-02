"""Momentum indicators: RSI, MACD, RSI divergence (heuristic)."""

import numpy as np
import pandas as pd

from .base import BULL, BEAR, NEUTRAL, register
from .trend import ema


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, min_periods=n, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


@register("rsi")
def rsi_signal(df: pd.DataFrame, n: int = 14, lo: float = 30, hi: float = 70) -> pd.Series:
    v = rsi(df["close"], n)
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[v < lo] = BULL          # oversold -> mean reversion buy
    sig[v > hi] = BEAR          # overbought
    return sig


@register("macd")
def macd_signal(df: pd.DataFrame, fast: int = 12, slow: int = 26, sig_n: int = 9) -> pd.Series:
    line = ema(df["close"], fast) - ema(df["close"], slow)
    signal = line.ewm(span=sig_n, adjust=False).mean()
    hist = line - signal
    out = pd.Series(NEUTRAL, index=df.index)
    out[(line > signal) & (hist > hist.shift(1))] = BULL
    out[(line < signal) & (hist < hist.shift(1))] = BEAR
    return out


@register("rsi_divergence")
def rsi_divergence(df: pd.DataFrame, n: int = 14, lookback: int = 60,
                   order: int = 5) -> pd.Series:
    """Heuristic: compare the last two swing highs/lows of price vs RSI.
    Regular bearish divergence -> -1, regular bullish -> +1, else 0.
    A pragmatic approximation - validate before trusting it live."""
    close, rv = df["close"].to_numpy(), rsi(df["close"], n).to_numpy()
    sig = np.zeros(len(df), dtype=int)
    for i in range(lookback, len(df)):
        w_lo, w_hi = i - lookback, i
        c_seg, r_seg = close[w_lo:w_hi], rv[w_lo:w_hi]
        def swings(seg):
            idx = [j for j in range(order, len(seg) - order)
                   if (seg[j] == max(seg[j - order:j + order + 1]) or
                       seg[j] == min(seg[j - order:j + order + 1]))]
            return idx
        sw = swings(c_seg)
        if len(sw) >= 2:
            a, b = sw[-2], sw[-1]
            if (c_seg[b] > c_seg[a] and r_seg[b] < r_seg[a] and
                    c_seg[b] == max(c_seg[a:])):
                sig[i] = BEAR
            elif (c_seg[b] < c_seg[a] and r_seg[b] > r_seg[a] and
                    c_seg[b] == min(c_seg[a:])):
                sig[i] = BULL
    return pd.Series(sig, index=df.index)
