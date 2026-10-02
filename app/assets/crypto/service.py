"""Crypto asset service - Binance public API (spot klines + futures extras)."""

from __future__ import annotations

import os

import pandas as pd
import requests

from app.assets.base_asset import BaseAsset

SPOT = os.getenv("BINANCE_SPOT_URL", "https://api.binance.com")
FUTURES = os.getenv("BINANCE_FUTURES_URL", "https://fapi.binance.com")
KLINES = f"{SPOT}/api/v3/klines"


class CryptoAsset(BaseAsset):
    asset_class = "crypto"
    default_timeframe = "4h"
    timeframes = ("1h", "4h", "1d")

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        r = requests.get(KLINES, params={"symbol": symbol.upper(),
                                         "interval": timeframe, "limit": limit}, timeout=15)
        r.raise_for_status()
        cols = ["open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades",
                "taker_buy_volume", "taker_buy_quote", "ignore"]
        df = pd.DataFrame(r.json(), columns=cols)
        num = ["open", "high", "low", "close", "volume", "taker_buy_volume"]
        df[num] = df[num].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df.set_index("open_time")

    def funding_oi_signal(self, symbol: str) -> int:
        """Live override for the funding/OI placeholder: extreme funding +
        rising OI warns of an overleveraged move against the crowd."""
        try:
            fr = requests.get(f"{FUTURES}/fapi/v1/premiumIndex",
                              params={"symbol": symbol.upper()}, timeout=10).json()
            funding = float(fr.get("lastFundingRate", 0) or 0)
            oi = requests.get(f"{FUTURES}/fapi/v1/openInterest",
                              params={"symbol": symbol.upper()}, timeout=10).json()
            oi_val = float(oi.get("openInterest", 0) or 0)
            _ = oi_val  # MVP: funding alone drives the signal; OI history for Fase-2
            if funding > 0.0008:
                return -1
            if funding < -0.0008:
                return 1
        except Exception:
            pass
        return 0

    def analyze(self, symbol: str, timeframe: str | None = None, limit: int = 500) -> dict:
        result = super().analyze(symbol, timeframe, limit)
        live = self.funding_oi_signal(symbol)
        if live != 0:
            for row in result["indicators"]:
                if row["name"] == "funding_oi":
                    row["signal"] = live
                    row["note"] = "live futures data (funding rate)"
                    row["contribution"] = round(live * row["weight"], 1)
            from app.core.signals.confluence import confluence_score, status_of
            from app.core.indicators.trend import adx_value
            df = self.fetch_ohlcv(symbol, timeframe or self.default_timeframe, limit)
            signals = {r["name"]: r["signal"] for r in result["indicators"]}
            score = confluence_score(signals, {r["name"]: r["weight"] for r in result["indicators"]})
            status, filtered = __import__("app.core.signals.confluence", fromlist=["apply_adx_filter"]).apply_adx_filter(status_of(score), adx_value(df))
            result.update(score=score, status=status, adx_filter_applied=filtered)
        return result
