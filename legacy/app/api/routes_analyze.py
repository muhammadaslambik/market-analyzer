"""REST endpoints: /analyze, /screener, /backtest."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from analyzer.idx_fetcher import CacingParams, get_fundamentals_cached

from app.assets.crypto.service import CryptoAsset
from app.assets.gold.service import GoldAsset
from app.assets.stocks_id.service import StocksIDAsset
from app.assets.stocks_us.service import StocksUSAsset
from app.core.indicators.base import REGISTRY
from app.api.routes_fundamental import CACING_PARAMS, DB_PATH
from backtest.engine import run_backtest

router = APIRouter()

ASSETS = {
    "crypto": CryptoAsset,
    "gold": GoldAsset,
    "stocks_id": StocksIDAsset,
    "stocks_us": StocksUSAsset,
}


def _service(asset_class: str):
    cls = ASSETS.get(asset_class)
    if cls is None:
        raise HTTPException(404, f"unknown asset class: {asset_class}")
    return cls()


@router.get("/analyze/{asset_class}/{symbol}")
def analyze(asset_class: str, symbol: str, timeframe: str | None = None, limit: int = 500):
    svc = _service(asset_class)
    tf = timeframe or svc.default_timeframe
    if tf not in svc.timeframes:
        raise HTTPException(400, f"timeframe must be one of {svc.timeframes}")
    try:
        result = svc.analyze(symbol, tf, limit)
    except Exception as exc:
        raise HTTPException(502, f"data fetch failed: {exc}")

    # Gate fundamental hanya untuk saham IDX
    if asset_class == "stocks_id":
        try:
            is_cacing, reasons, fund = get_fundamentals_cached(
                symbol, CACING_PARAMS, DB_PATH
            )
            result["fundamental_gate"] = {"is_cacing": is_cacing, "reasons": reasons}
            if is_cacing:
                # shell stock: paksa status jadi WAIT — jangan recommend entry
                result["status"] = "WAIT"
                result["adx_filter_applied"] = True
        except Exception as exc:
            result["fundamental_gate"] = {"error": str(exc)}
    return result


@router.get("/screener/{asset_class}")
def screener(asset_class: str, timeframe: str | None = None, status_filter: str | None = None):
    """Scan a watchlist and return symbols whose status matches the filter."""
    watchlists = {
        "crypto": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"],
        "gold": ["XAUUSD"],
        "stocks_id": ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "BMRI.JK"],
        "stocks_us": ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"],
    }
    svc = _service(asset_class)
    tf = timeframe or svc.default_timeframe
    out = []
    for sym in watchlists.get(asset_class, []):
        try:
            r = svc.analyze(sym, tf, 300)
        except Exception as exc:
            out.append({"symbol": sym, "error": str(exc)})
            continue
        if status_filter is None or r["status"] == status_filter:
            out.append({"symbol": sym, "score": r["score"], "status": r["status"]})
    return {"asset_class": asset_class, "timeframe": tf, "results": out}


@router.post("/backtest")
def backtest(payload: dict):
    """Body: {asset_class, symbol, timeframe, config_path?, fee_bps, slippage_bps}."""
    svc = _service(payload.get("asset_class", "crypto"))
    tf = payload.get("timeframe") or svc.default_timeframe
    try:
        df = svc.fetch_ohlcv(payload["symbol"], tf, int(payload.get("limit", 1000)))
    except Exception as exc:
        raise HTTPException(502, f"data fetch failed: {exc}")
    indicators = {s["name"]: {"fn": REGISTRY[s["name"]], "weight": float(s["weight"])}
                  for s in svc.indicator_specs() if s["name"] in REGISTRY}
    return run_backtest(df, indicators,
                        fee_bps=float(payload.get("fee_bps", 10)),
                        slippage_bps=float(payload.get("slippage_bps", 5)))
