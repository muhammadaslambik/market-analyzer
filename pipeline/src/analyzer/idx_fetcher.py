"""Fetcher data saham IDX via yfinance (gratis, tanpa kartu).

Filter 1 (fundamental "cacing") + Filter 4 (OHLCV untuk teknikal).
Semua angka "cacing" adalah parameter, bukan konstanta hardcoded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import yfinance as yf

from analyzer.fund_cache import connect as store_connect, get_fresh, put   # ← tambahan


# --- Parameter Filter 1 (dari STRATEGY_ID_SHELL_DETECTOR.md) ---
@dataclass(frozen=True)
class CacingParams:
    max_market_cap: float = 500e9          # < Rp 500 Miliar
    max_pbv: float = 1.0                   # PBV rendah atau negatif
    require_negative_profit: bool = True   # laba bersih negatif/stagnan


def fetch_ohlcv(ticker: str, period: str = "1y") -> pd.DataFrame:
    """OHLCV harian .JK. Kolom lowercase: open high low close volume."""
    df = yf.Ticker(ticker).history(period=period, interval="1d")
    if df.empty:
        raise ValueError(f"tidak ada OHLCV untuk {ticker}")

    # yfinance versi baru balikin kolom MultiIndex: ("Close", "BBCA.JK")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Normalisasi: semua kolom lowercase agar konsisten dengan build_features
    df.columns = [str(c).lower() for c in df.columns]

    df = df[["open", "high", "low", "close", "volume"]].copy()
    df.index = df.index.tz_localize(None)
    return df



def fetch_fundamentals(ticker: str) -> dict:
    """Ringkasan fundamental dari yfinance .info."""
    info = yf.Ticker(ticker).info
    return {
        "ticker": ticker,
        "market_cap": info.get("marketCap"),
        "pbv": info.get("priceToBook"),
        "trailing_eps": info.get("trailingEps"),
        "net_income": _latest_net_income(ticker),
        "currency": info.get("financialCurrency") or "IDR",
    }


def _latest_net_income(ticker: str) -> Optional[float]:
    """Laba bersih tahun fiskal terakhir; None kalau data tidak ada."""
    try:
        inc = yf.Ticker(ticker).income_stmt
        if inc.empty:
            return None
        for row in ("Net Income", "Net Income Common Stockholders"):
            if row in inc.index:
                return float(inc.loc[row].iloc[0])
    except Exception:
        return None
    return None


def is_cacing_fundamental(fund: dict, p: CacingParams) -> tuple[bool, list[str]]:
    """Filter 1: shell kecil + kinerja buruk.

    Return (lolos, alasan) — alasan berisi setiap kriteria yang gagal,
    supaya output bisa diaudit, bukan black box.
    """
    reasons: list[str] = []

    mc = fund.get("market_cap")
    if mc is None:
        reasons.append("market_cap: tidak ada data")
    elif mc >= p.max_market_cap:
        reasons.append(f"market_cap {mc:.0f} >= {p.max_market_cap:.0f}")

    pbv = fund.get("pbv")
    if pbv is None:
        reasons.append("pbv: tidak ada data")
    elif pbv > p.max_pbv:
        reasons.append(f"pbv {pbv:.2f} > {p.max_pbv:.2f}")

    ni = fund.get("net_income")
    if ni is None:
        if p.require_negative_profit:
            reasons.append("net_income: tidak ada data")
    elif p.require_negative_profit and ni > 0:
        reasons.append(f"net_income {ni:.0f} > 0")

    return (len(reasons) == 0, reasons)


def get_fundamentals_cached(
    ticker: str, params: CacingParams, db_path: str
) -> tuple[bool, list[str], dict]:
    """Cache-first: return (is_cacing, reasons, fundamental).

    Cache segar (< 24 jam) -> tidak ada network call.
    Cache basi/tidak ada  -> fetch yfinance, simpan verdict ke cache.
    """
    con = store_connect(db_path)
    cached = get_fresh(con, ticker)
    if cached is not None:
        is_cacing, reasons = is_cacing_fundamental(cached["payload"], params)
        return is_cacing, reasons, cached["payload"]

    fund = fetch_fundamentals(ticker)
    is_cacing, reasons = is_cacing_fundamental(fund, params)
    put(con, ticker, fund, reasons)
    con.close()
    return is_cacing, reasons, fund
