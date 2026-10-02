"""Gold (XAUUSD) service - daily/intraday bars via yfinance (GC=F / XAUUSD=X)."""

from __future__ import annotations

import pandas as pd

from app.assets.base_asset import BaseAsset
from app.assets.generic_yf import fetch_yf


class GoldAsset(BaseAsset):
    asset_class = "gold"
    default_timeframe = "4h"
    timeframes = ("1h", "4h", "1d")
    _TICKERS = {"1h": "XAUUSD=X", "4h": "XAUUSD=X", "1d": "GC=F"}
    _PERIODS = {"1h": ("60d", "1h"), "4h": ("120d", "1h"), "1d": ("1y", "1d")}

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        period, interval = self._PERIODS.get(timeframe, ("1y", "1d"))
        return fetch_yf(self._TICKERS.get(timeframe, "GC=F"), period, interval).tail(limit)
