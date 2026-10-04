"""Pembatas laju permintaan (token bucket) agar kuota sumber data gratis tidak terlampaui."""

from __future__ import annotations

import time
from collections.abc import Callable


class TokenBucket:
    """Token bucket sederhana. `acquire()` menunggu sampai satu token tersedia."""

    def __init__(
        self,
        rate_per_sec: float,
        capacity: int = 1,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if rate_per_sec <= 0 or capacity < 1:
            raise ValueError("rate_per_sec harus > 0 dan capacity >= 1")
        self._rate = rate_per_sec
        self._capacity = float(capacity)
        self._clock = clock
        self._sleep = sleep
        self._tokens = float(capacity)
        self._last = clock()

    def acquire(self) -> None:
        while True:
            now = self._clock()
            self._tokens = min(self._capacity, self._tokens + (now - self._last) * self._rate)
            self._last = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return
            self._sleep((1.0 - self._tokens) / self._rate)
