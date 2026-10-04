"""US stocks service (benchmark: ^GSPC for relative strength in Fase-2)."""

from __future__ import annotations

import pandas as pd

from app.assets.base_asset import BaseAsset
from app.assets.generic_yf import fetch_yf


class StocksUSAsset(BaseAsset):
    asset_class = "stocks_us"
    default_timeframe = "1d"
    timeframes = ("4h", "1d")
    _PERIODS = {"4h": ("120d", "1h"), "1d": ("1y", "1d")}

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        period, interval = self._PERIODS.get(timeframe, ("1y", "1d"))
        return fetch_yf(symbol.upper(), period, interval).tail(limit)
