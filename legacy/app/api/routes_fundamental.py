"""Endpoints fundamental (Filter 1 "cacing") untuk saham IDX."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException

from analyzer.idx_fetcher import CacingParams, get_fundamentals_cached

router = APIRouter()

# Params bisa dioverride via env, default dari dataclass
CACING_PARAMS = CacingParams(
    max_market_cap=float(os.getenv("CACING_MAX_MARKET_CAP", 500e9)),
    max_pbv=float(os.getenv("CACING_MAX_PBV", 1.0)),
    require_negative_profit=os.getenv("CACING_REQUIRE_NEG_PROFIT", "1") == "1",
)
DB_PATH = str(Path(__file__).resolve().parents[3] / "db" / "fundamentals.db")


@router.get("/fundamental/{symbol}")
def fundamental(symbol: str):
    """Filter 1 audit: apakah {symbol} lolos sieve fundamental?"""
    try:
        is_cacing, reasons, fund = get_fundamentals_cached(
            symbol, CACING_PARAMS, DB_PATH
        )
    except Exception as exc:
        raise HTTPException(502, f"fundamental fetch failed: {exc}")
    return {
        "symbol": symbol,
        "is_cacing": is_cacing,
        "reasons": reasons,
        "fundamentals": fund,
        "params": {
            "max_market_cap": CACING_PARAMS.max_market_cap,
            "max_pbv": CACING_PARAMS.max_pbv,
            "require_negative_profit": CACING_PARAMS.require_negative_profit,
        },
    }
