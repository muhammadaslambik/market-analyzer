"""Backfill candle historis. Idempoten, bisa dilanjutkan, dan menghormati pembatas laju.

Contoh (dari folder utama repo, lingkungan pipeline aktif):
    python -m analyzer.jobs.backfill --symbols BTCUSDT --timeframe 1d --since 2026-09-01 --dry-run
    python -m analyzer.jobs.backfill --symbols BTCUSDT,ETHUSDT --timeframe all
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from analyzer.config import require_env
from analyzer.migrate import REPO_ROOT, load_env_file
from analyzer.models import Candle, interval_of
from analyzer.sources.base import CandleSource, SourceBlockedError, SourceError
from analyzer.sources.binance_vision import BinanceVisionSource
from analyzer.store.neon import NeonStore
from analyzer.validate import validate_candles

MARKET = "crypto"
DEFAULT_DAYS = {"1h": 730, "1d": 1825}  # 2 tahun data 1 jam, 5 tahun data 1 hari
WINDOW_CANDLES = 5000


class Store(Protocol):
    def get_max_ts(self, market: str, symbol: str, timeframe: str) -> datetime | None: ...
    def insert_candles(self, candles: Sequence[Candle]) -> int: ...
    def insert_issues(self, issues: Sequence[dict[str, Any]]) -> int: ...


class DryRunStore:
    """Tidak menulis apa pun. Dipakai untuk uji coba (--dry-run)."""

    def get_max_ts(self, market: str, symbol: str, timeframe: str) -> datetime | None:
        return None

    def insert_candles(self, candles: Sequence[Candle]) -> int:
        return 0

    def insert_issues(self, issues: Sequence[dict[str, Any]]) -> int:
        return 0


@dataclass
class SeriesReport:
    symbol: str
    timeframe: str
    fetched: int = 0
    inserted: int = 0
    issues: int = 0
    error: str | None = None


@dataclass
class BackfillSummary:
    reports: list[SeriesReport] = field(default_factory=list)
    status: str = "ok"  # ok | partial | error

    @property
    def inserted(self) -> int:
        return sum(r.inserted for r in self.reports)

    @property
    def errors(self) -> list[str]:
        return [f"{r.symbol} {r.timeframe}: {r.error}" for r in self.reports if r.error]


def floor_to_interval(ts: datetime, timeframe: str) -> datetime:
    seconds = int(interval_of(timeframe).total_seconds())
    return datetime.fromtimestamp((int(ts.timestamp()) // seconds) * seconds, UTC)


def _backfill_series(
    source: CandleSource,
    store: Store,
    symbol: str,
    timeframe: str,
    since: datetime,
    now: datetime,
    full: bool,
    window_candles: int,
    report: SeriesReport,
) -> None:
    interval = interval_of(timeframe)
    cursor = floor_to_interval(since, timeframe)
    if not full:
        last = store.get_max_ts(MARKET, symbol, timeframe)
        if last is not None and last > cursor:
            cursor = last  # lanjutkan; candle terakhir diambil ulang agar celah di batas terdeteksi
    window = interval * window_candles
    while cursor < now:
        end = min(cursor + window, now)
        candles = source.fetch_candles(symbol, timeframe, cursor, end, now=now)
        report.fetched += len(candles)
        if candles:
            result = validate_candles(candles, now=now)
            report.inserted += store.insert_candles(result.valid)
            if result.issues:
                report.issues += store.insert_issues(result.issues)
        if end >= now:
            break
        cursor = end - interval  # tumpang tindih 1 candle supaya celah di batas jendela terdeteksi


def run_backfill(
    source: CandleSource,
    store: Store,
    symbols: Sequence[str],
    timeframes: Sequence[str],
    since: dict[str, datetime],
    now: datetime,
    *,
    full: bool = False,
    window_candles: int = WINDOW_CANDLES,
    log: Callable[[str], None] = print,
) -> BackfillSummary:
    if window_candles < 2:
        raise ValueError("window_candles minimal 2")
    summary = BackfillSummary()
    for symbol in symbols:
        for timeframe in timeframes:
            report = SeriesReport(symbol, timeframe)
            summary.reports.append(report)
            try:
                _backfill_series(
                    source,
                    store,
                    symbol,
                    timeframe,
                    since[timeframe],
                    now,
                    full,
                    window_candles,
                    report,
                )
            except SourceBlockedError as exc:
                report.error = f"diblokir: {exc}"
                summary.status = "error"
                log(f"{symbol} {timeframe}: BERHENTI, {report.error}")
                return summary
            except SourceError as exc:
                report.error = str(exc)
                summary.status = "partial"
            note = f", GALAT {report.error}" if report.error else ""
            log(
                f"{symbol} {timeframe}: diambil {report.fetched}, ditulis {report.inserted}, "
                f"catatan masalah {report.issues}{note}"
            )
    return summary


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill candle crypto ke Neon.")
    parser.add_argument("--symbols", default="BTCUSDT,ETHUSDT", help="dipisah koma")
    parser.add_argument("--timeframe", choices=["1h", "1d", "all"], default="all")
    parser.add_argument(
        "--since",
        help="tanggal awal UTC, format YYYY-MM-DD (bawaan: 2 tahun untuk 1h, 5 tahun untuk 1d)",
    )
    parser.add_argument("--full", action="store_true", help="abaikan data yang sudah ada")
    parser.add_argument("--dry-run", action="store_true", help="ambil dan validasi, tanpa menulis")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    load_env_file(REPO_ROOT / ".env")
    now = datetime.now(UTC)
    timeframes = ["1h", "1d"] if args.timeframe == "all" else [args.timeframe]
    if args.since:
        start = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=UTC)
        since = dict.fromkeys(timeframes, start)
    else:
        since = {tf: now - timedelta(days=DEFAULT_DAYS[tf]) for tf in timeframes}
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    source = BinanceVisionSource()
    neon: NeonStore | None = None
    started = datetime.now(UTC)
    try:
        store: Store = DryRunStore()
        if not args.dry_run:
            neon = NeonStore.connect(require_env("DATABASE_URL"))
            store = neon
        summary = run_backfill(source, store, symbols, timeframes, since, now, full=args.full)
        if neon is not None:
            neon.log_run(
                "backfill",
                started,
                datetime.now(UTC),
                summary.status,
                summary.inserted,
                source.api_calls,
                "; ".join(summary.errors)[:500] or None,
            )
    finally:
        if neon is not None:
            neon.close()
    print(
        f"Selesai. Status: {summary.status}. Baris baru: {summary.inserted}. "
        f"Panggilan API: {source.api_calls}"
    )
    return 0 if summary.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
