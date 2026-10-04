"""Adaptor Binance (endpoint data pasar saja: data-api.binance.vision)."""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import UTC, datetime

import httpx

from analyzer.models import Candle, interval_of
from analyzer.ratelimit import TokenBucket
from analyzer.sources.base import SourceBlockedError, SourceError

BASE_URL = "https://data-api.binance.vision"
PAGE_LIMIT = 1000


class BinanceVisionSource:
    name = "binance-vision"

    def __init__(
        self,
        client: httpx.Client | None = None,
        bucket: TokenBucket | None = None,
        max_retries: int = 4,
        backoff_base: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client or httpx.Client(timeout=20.0, base_url=BASE_URL)
        # Batas konservatif (bukan angka resmi): 2 permintaan per detik.
        self._bucket = bucket or TokenBucket(rate_per_sec=2.0, capacity=2)
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._sleep = sleep
        self.api_calls = 0

    def _request(self, params: dict[str, str | int]) -> list:
        last_problem = "tidak diketahui"
        for attempt in range(self._max_retries + 1):
            self._bucket.acquire()
            self.api_calls += 1
            try:
                response = self._client.get("/api/v3/klines", params=params)
            except httpx.HTTPError as exc:
                last_problem = f"koneksi: {type(exc).__name__}"
                self._sleep(self._backoff_base * (2**attempt))
                continue
            status = response.status_code
            if status == 200:
                data = response.json()
                if not isinstance(data, list):
                    raise SourceError("format respons tak terduga (bukan daftar)")
                return data
            if status in (451, 403):
                raise SourceBlockedError(f"akses diblokir (HTTP {status})")
            if status in (418, 429) or status >= 500:
                last_problem = f"HTTP {status}"
                self._sleep(self._retry_delay(response, attempt))
                continue
            raise SourceError(f"HTTP {status}")
        raise SourceError(f"gagal setelah {self._max_retries + 1} percobaan ({last_problem})")

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        header = response.headers.get("Retry-After")
        if header:
            try:
                return max(0.0, float(header))
            except ValueError:
                pass
        return self._backoff_base * (2**attempt)

    def fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        now: datetime | None = None,
    ) -> list[Candle]:
        if not symbol.isalnum() or symbol != symbol.upper():
            raise ValueError(f"Simbol tidak valid: {symbol!r}")
        interval = interval_of(timeframe)
        interval_ms = int(interval.total_seconds() * 1000)
        now = now or datetime.now(UTC)
        cursor = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        candles: list[Candle] = []
        while cursor < end_ms:
            rows = self._request(
                {
                    "symbol": symbol,
                    "interval": timeframe,
                    "startTime": cursor,
                    "endTime": end_ms - 1,
                    "limit": PAGE_LIMIT,
                }
            )
            if not rows:
                break
            for row in rows:
                if not isinstance(row, list) or len(row) < 6:
                    raise SourceError("baris candle tidak sesuai format")
                opened = datetime.fromtimestamp(int(row[0]) / 1000, UTC)
                if opened + interval > now:
                    continue  # candle belum tutup
                candles.append(
                    Candle(
                        market="crypto",
                        symbol=symbol,
                        timeframe=timeframe,
                        ts=opened,
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                        volume=float(row[5]),
                        source=self.name,
                    )
                )
            cursor = int(rows[-1][0]) + interval_ms
            if len(rows) < PAGE_LIMIT:
                break
        candles.sort(key=lambda c: c.ts)
        return candles
