"""Shared yfinance fetcher for non-crypto assets."""

from __future__ import annotations

import pandas as pd


def fetch_yf(ticker: str, period: str, interval: str) -> pd.DataFrame:
    import yfinance as yf  # lazy import: heavy dependency, only used here

    raw = yf.download(ticker, period=period, interval=interval, progress=False)
    if raw.empty:
        raise ValueError(f"yfinance returned no data for {ticker}")
    df = raw.rename(columns=str.lower)[["open", "high", "low", "close", "volume"]].copy()
    df.index = pd.to_datetime(df.index)
    df = df[~df.index.duplicated(keep="last")]
    return df.dropna()
