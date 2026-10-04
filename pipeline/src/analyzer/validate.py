"""Validasi kualitas data candle (satu seri: satu market, simbol, dan timeframe).

Masalah dicatat, tidak dibuang diam-diam. Candle yang gagal validasi dikeluarkan dari hasil
`valid`, tetapi selalu ada catatan di `issues` yang siap ditulis ke tabel data_quality_log.
Jenis masalah: duplicate, not_closed, ohlc_invalid, gap, outlier.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from analyzer.config import OUTLIER_LOG_RETURN
from analyzer.models import Candle, interval_of


@dataclass(frozen=True)
class ValidationResult:
    valid: list[Candle]
    issues: list[dict[str, Any]]  # kolom: market, symbol, timeframe, ts, issue, detail


def _ohlc_problems(c: Candle, interval_seconds: int) -> list[str]:
    values = (c.open, c.high, c.low, c.close, c.volume)
    if not all(math.isfinite(v) for v in values):
        return ["tidak_hingga_atau_nan"]
    reasons: list[str] = []
    if min(c.open, c.high, c.low, c.close) <= 0:
        reasons.append("harga_tidak_positif")
    if c.low > c.high:
        reasons.append("low_lebih_besar_dari_high")
    if c.low > min(c.open, c.close):
        reasons.append("low_di_atas_open_atau_close")
    if c.high < max(c.open, c.close):
        reasons.append("high_di_bawah_open_atau_close")
    if c.volume < 0:
        reasons.append("volume_negatif")
    if int(c.ts.timestamp()) % interval_seconds != 0:
        reasons.append("ts_tidak_selaras")
    return reasons


def validate_candles(
    candles: list[Candle],
    *,
    now: datetime | None = None,
    outlier_threshold: float | None = None,
) -> ValidationResult:
    """Validasi satu seri candle. Candle valid dikembalikan terurut menaik berdasarkan waktu."""
    if not candles:
        return ValidationResult([], [])
    first = candles[0]
    key = (first.market, first.symbol, first.timeframe)
    if any((c.market, c.symbol, c.timeframe) != key for c in candles):
        raise ValueError("validate_candles hanya menerima satu seri (market, simbol, timeframe)")
    if any(c.ts.tzinfo is None for c in candles):
        raise ValueError("ts candle harus timezone-aware (UTC)")

    interval = interval_of(first.timeframe)
    interval_seconds = int(interval.total_seconds())
    threshold = (
        outlier_threshold if outlier_threshold is not None else OUTLIER_LOG_RETURN[first.timeframe]
    )
    now = now or datetime.now(UTC)
    issues: list[dict[str, Any]] = []

    def add(ts: datetime, kind: str, detail: dict[str, Any]) -> None:
        issues.append(
            {
                "market": first.market,
                "symbol": first.symbol,
                "timeframe": first.timeframe,
                "ts": ts,
                "issue": kind,
                "detail": detail,
            }
        )

    accepted: list[Candle] = []
    seen: set[datetime] = set()
    for c in sorted(candles, key=lambda item: item.ts):
        if c.ts in seen:
            add(c.ts, "duplicate", {"kept": "pertama"})
            continue
        seen.add(c.ts)
        if c.ts + interval > now:
            add(c.ts, "not_closed", {"closes_at": (c.ts + interval).isoformat()})
            continue
        reasons = _ohlc_problems(c, interval_seconds)
        if reasons:
            add(c.ts, "ohlc_invalid", {"reasons": reasons})
            continue
        accepted.append(c)

    for prev, cur in zip(accepted, accepted[1:], strict=False):
        delta = cur.ts - prev.ts
        if delta > interval:
            add(
                prev.ts + interval,
                "gap",
                {
                    "from": prev.ts.isoformat(),
                    "to": cur.ts.isoformat(),
                    "missing": int(delta / interval) - 1,
                },
            )
        else:
            move = abs(math.log(cur.close / prev.close))
            if move > threshold:
                add(cur.ts, "outlier", {"log_return": round(move, 6), "threshold": threshold})

    return ValidationResult(accepted, issues)
