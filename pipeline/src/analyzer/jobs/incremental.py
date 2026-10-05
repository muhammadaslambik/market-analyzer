"""Job pembaruan berkala candle crypto (dipakai oleh job per jam dan job harian).

Alur: baca candle terakhir di Neon, ambil candle baru dari sumber, validasi, tulis ke Neon,
lalu perbarui `latest_price` dan `meta` di D1 dan catat ke `ingest_runs`.
Status: ok | partial (sebagian gagal, atau D1 gagal tetapi Neon aman) | error (diblokir).
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
import psycopg

from analyzer.config import require_env
from analyzer.jobs.backfill import (
    BackfillSummary,
    DryRunStore,
    Store,
    floor_to_interval,
    run_backfill,
)
from analyzer.migrate import REPO_ROOT, load_env_file
from analyzer.models import interval_of
from analyzer.sources.base import CandleSource
from analyzer.sources.binance_vision import BinanceVisionSource
from analyzer.store.d1 import D1Store, iso_utc
from analyzer.store.neon import NeonStore

MARKET = "crypto"
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
CATCHUP_CANDLES = 48  # untuk simbol yang belum punya riwayat: ambil 48 candle terakhir


class NeonLike(Store, Protocol):
    def get_latest(
        self, market: str, symbol: str, timeframe: str
    ) -> tuple[datetime, float, str] | None: ...

    def log_run(
        self,
        job: str,
        started_at: datetime,
        finished_at: datetime,
        status: str,
        rows_written: int,
        api_calls: int,
        error: str | None,
    ) -> None: ...


class D1Like(Protocol):
    def upsert_latest_price(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        close: float,
        asof: datetime,
        source: str,
    ) -> None: ...

    def set_meta(self, key: str, value: str) -> None: ...


class DryRunNeon(DryRunStore):
    def get_latest(self, market: str, symbol: str, timeframe: str) -> None:
        return None

    def log_run(self, *args: Any, **kwargs: Any) -> None:
        return None


@dataclass
class JobResult:
    status: str
    summary: BackfillSummary
    d1_error: str | None = None


def run_incremental(
    source: CandleSource,
    neon: NeonLike,
    d1: D1Like | None,
    symbols: Sequence[str],
    timeframe: str,
    job: str,
    now: datetime,
    *,
    started_at: datetime | None = None,
    log: Callable[[str], None] = print,
) -> JobResult:
    started = started_at or datetime.now(UTC)
    interval = interval_of(timeframe)
    # Simbol baru mulai dari 48 candle terakhir; simbol dengan riwayat selalu lanjut dari
    # candle terakhirnya (resume_always) supaya tidak ada celah walau job sempat terlewat.
    since = {timeframe: floor_to_interval(now, timeframe) - interval * CATCHUP_CANDLES}
    summary = run_backfill(
        source, neon, symbols, [timeframe], since, now, resume_always=True, log=log
    )
    status = summary.status
    d1_error: str | None = None

    if d1 is not None and status != "error":
        try:
            for symbol in symbols:
                latest = neon.get_latest(MARKET, symbol, timeframe)
                if latest is None:
                    continue
                opened, close, price_source = latest
                d1.upsert_latest_price(
                    MARKET, symbol, timeframe, close, opened + interval, price_source
                )
            stamp = iso_utc(datetime.now(UTC))
            d1.set_meta(f"{job}.last_run", stamp)
            d1.set_meta(f"{job}.status", status)
            if status == "ok":
                d1.set_meta(f"{job}.last_success", stamp)
        except (RuntimeError, httpx.HTTPError) as exc:
            first_line = (str(exc).splitlines() or [""])[0]
            d1_error = f"D1 gagal ({type(exc).__name__}): {first_line}"
            if status == "ok":
                status = "partial"

    errors = summary.errors + ([d1_error] if d1_error else [])
    neon.log_run(
        job,
        started,
        datetime.now(UTC),
        status,
        summary.inserted,
        source.api_calls,
        "; ".join(errors)[:500] or None,
    )
    return JobResult(status, summary, d1_error)


def main_for(timeframe: str, job: str, argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Job {job}: perbarui candle crypto.")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS), help="dipisah koma")
    parser.add_argument("--dry-run", action="store_true", help="ambil dan validasi, tanpa menulis")
    args = parser.parse_args(argv)
    load_env_file(REPO_ROOT / ".env")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    source = BinanceVisionSource()
    neon: NeonStore | None = None
    d1: D1Store | None = None
    try:
        if args.dry_run:
            result = run_incremental(
                source, DryRunNeon(), None, symbols, timeframe, job, datetime.now(UTC)
            )
        else:
            neon = NeonStore.connect(require_env("DATABASE_URL"))
            d1 = D1Store(
                require_env("CF_ACCOUNT_ID"),
                require_env("CF_D1_DATABASE_ID"),
                require_env("CF_API_TOKEN"),
            )
            result = run_incremental(source, neon, d1, symbols, timeframe, job, datetime.now(UTC))
    except (RuntimeError, psycopg.Error, httpx.HTTPError, OSError) as exc:
        first_line = (str(exc).splitlines() or [""])[0]
        print(f"GAGAL ({type(exc).__name__}): {first_line}")
        return 1
    finally:
        if neon is not None:
            neon.close()
        if d1 is not None:
            d1.close()
    print(
        f"{job}: status {result.status}. Baris baru: {result.summary.inserted}. "
        f"Panggilan API: {source.api_calls}"
    )
    return 1 if result.status == "error" else 0
