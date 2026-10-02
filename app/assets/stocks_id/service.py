"""Indonesian stocks service (yfinance .JK tickers, benchmark: ^JKSE)."""

from __future__ import annotations

import pandas as pd

from app.assets.base_asset import BaseAsset
from app.assets.generic_yf import fetch_yf


class StocksIDAsset(BaseAsset):
    asset_class = "stocks_id"
    default_timeframe = "1d"
    timeframes = ("1d", "1wk")
    _PERIODS = {"1d": ("1y", "1d"), "1wk": ("5y", "1wk")}

    def _ticker(self, symbol: str) -> str:
        s = symbol.upper()
        return s if s.endswith(".JK") else f"{s}.JK"

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        period, interval = self._PERIODS.get(timeframe, ("1y", "1d"))
        return fetch_yf(self._ticker(symbol), period, interval).tail(limit)

    def compute(self, df: pd.DataFrame) -> dict:
        result = super().compute(df)
        for row in result["indicators"]:
            if row["name"] in ("foreign_flow", "rs_vs_index") and row["signal"] == 0:
                row["note"] = ("needs external data (foreign flow CSV / index series) "
                               "- signal neutral in MVP")
        return result
