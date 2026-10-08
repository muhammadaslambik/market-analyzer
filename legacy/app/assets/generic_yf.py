"""Shared yfinance fetcher for non-crypto assets."""

from __future__ import annotations

import pandas as pd


def fetch_yf(ticker: str, period: str, interval: str) -> pd.DataFrame:
    import yfinance as yf  # lazy import: heavy dependency, only used here

    raw = yf.download(ticker, period=period, interval=interval, progress=False)
    if raw is None or raw.empty:
        raise ValueError(f"yfinance returned no data for {ticker}")

    # yfinance versi baru mengembalikan MultiIndex (Field, Ticker) -> flatten dulu
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
    df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="last")]
    return df.dropna()
