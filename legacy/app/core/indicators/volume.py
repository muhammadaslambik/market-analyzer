"""Volume indicators: VWAP, OBV, volume profile, CVD (crypto), stubs for
asset-specific data (funding/OI, foreign flow, relative strength)."""

import numpy as np
import pandas as pd

from .base import BULL, BEAR, NEUTRAL, register


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].replace(0, np.nan)
    return (tp * vol).cumsum() / vol.cumsum()


@register("vwap_signal")
def vwap_signal(df: pd.DataFrame) -> pd.Series:
    v = vwap(df)
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[df["close"] > v] = BULL
    sig[df["close"] < v] = BEAR
    return sig


@register("obv")
def obv_signal(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff().fillna(0))
    obv = (direction * df["volume"]).cumsum()
    slope = obv.diff(5)
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[slope > 0] = BULL
    sig[slope < 0] = BEAR
    return sig


@register("volume_profile")
def volume_profile(df: pd.DataFrame, bins: int = 24, lookback: int = 120) -> pd.Series:
    """Neutral-until-migration heuristic: +1 when price closes above the
    high-volume node of the trailing window (acceptance above value), -1 below."""
    sig = pd.Series(NEUTRAL, index=df.index)
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    v, c = df["volume"].to_numpy(), df["close"].to_numpy()
    for i in range(lookback, len(df)):
        hh, ll = h[i - lookback:i].max(), l[i - lookback:i].min()
        if hh <= ll:
            continue
        edges = np.linspace(ll, hh, bins + 1)
        idx = np.clip(np.digitize((h[i - lookback:i] + l[i - lookback:i]) / 2, edges) - 1, 0, bins - 1)
        vol_by_bin = np.zeros(bins)
        np.add.at(vol_by_bin, idx, v[i - lookback:i])
        poc = (edges[np.argmax(vol_by_bin)] + edges[np.argmax(vol_by_bin) + 1]) / 2
        sig.iloc[i] = BULL if c[i] > poc else BEAR if c[i] < poc else NEUTRAL
    return sig


@register("cvd")
def cvd_signal(df: pd.DataFrame) -> pd.Series:
    """Cumulative volume delta from taker buy volume (Binance klines column
    'taker_buy_volume'). Falls back to NEUTRAL if the column is absent."""
    if "taker_buy_volume" not in df.columns:
        return pd.Series(NEUTRAL, index=df.index)
    delta = 2 * df["taker_buy_volume"] - df["volume"]
    cvd = delta.cumsum()
    slope = cvd.diff(5)
    sig = pd.Series(NEUTRAL, index=df.index)
    sig[slope > 0] = BULL
    sig[slope < 0] = BEAR
    return sig


@register("funding_oi")
def funding_oi_stub(df: pd.DataFrame) -> pd.Series:
    """Placeholder: real implementation lives in the crypto service, which has
    access to the futures API. Returning NEUTRAL keeps the scoring honest
    instead of fabricating a signal."""
    return pd.Series(NEUTRAL, index=df.index)


@register("foreign_flow")
def foreign_flow_stub(df: pd.DataFrame) -> pd.Series:
    """Placeholder for IDX net buy/sell data (manual CSV upload in MVP)."""
    return pd.Series(NEUTRAL, index=df.index)


@register("rs_vs_index")
def rs_vs_index_stub(df: pd.DataFrame) -> pd.Series:
    """Placeholder for relative strength vs a benchmark index. The asset
    services may override this with a real implementation when the benchmark
    series is available."""
    return pd.Series(NEUTRAL, index=df.index)
