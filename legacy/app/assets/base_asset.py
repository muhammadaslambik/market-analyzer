"""Abstract asset layer. Every asset class implements fetch_ohlcv(); the
confluence analysis itself lives here and is shared by all assets."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
import yaml

from app.core.indicators import momentum, trend, volatility, volume  # noqa: F401 (registers all)
from app.core.indicators.base import REGISTRY, latest_signal, NEUTRAL
from app.core.indicators.trend import adx_value
from app.core.indicators.volatility import atr
from app.core.signals.confluence import (apply_adx_filter, confluence_score,
                                         status_of)

CONFIG_DIR = Path(__file__).parent


class BaseAsset(ABC):
    asset_class: str = "base"
    yaml_name: str = "indicators_config.yaml"
    default_timeframe: str = "1d"
    timeframes: tuple[str, ...] = ("1d",)

    def __init__(self) -> None:
        cfg_path = Path(CONFIG_DIR, self.asset_class, self.yaml_name)
        with open(cfg_path) as f:
            self.config = yaml.safe_load(f)

    @abstractmethod
    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Return DataFrame with columns: open, high, low, close, volume
        (plus optional asset-specific columns such as taker_buy_volume)."""

    def indicator_specs(self) -> list[dict]:
        return self.config["indicators"]

    def compute(self, df: pd.DataFrame) -> dict:
        """Pure analysis on an OHLCV frame - no network, fully testable."""
        signals, rows = {}, []
        for spec in self.indicator_specs():
            name, weight = spec["name"], float(spec["weight"])
            fn = REGISTRY.get(name)
            if fn is None:
                sig = NEUTRAL
                note = "indicator not registered -> treated neutral"
            else:
                try:
                    sig = latest_signal(fn(df))
                    note = ""
                except Exception as exc:  # never let one bad indicator kill the run
                    sig, note = NEUTRAL, f"error: {exc}"
            signals[name] = sig
            rows.append({"name": name, "category": spec.get("category", ""),
                         "weight": weight, "signal": sig,
                         "contribution": round(sig * weight, 1), "note": note})
        score = confluence_score(signals, {r["name"]: r["weight"] for r in rows})
        status, filtered = apply_adx_filter(status_of(score), adx_value(df))
        a = float(atr(df).iloc[-1])
        px = float(df["close"].iloc[-1])
        direction = 1 if score >= 0 else -1
        return {
            "asset_class": self.asset_class,
            "price": px,
            "score": score,
            "status": status,
            "adx_filter_applied": filtered,
            "atr": a,
            "suggested_stop_loss": round(px - direction * 1.5 * a, 8),
            "suggested_take_profit": round(px + direction * 2.0 * a, 8),
            "indicators": rows,
        }

    def analyze(self, symbol: str, timeframe: str | None = None, limit: int = 500) -> dict:
        tf = timeframe or self.default_timeframe
        df = self.fetch_ohlcv(symbol, tf, limit)
        result = self.compute(df)
        result.update({"symbol": symbol, "timeframe": tf, "bars": len(df)})
        return result
