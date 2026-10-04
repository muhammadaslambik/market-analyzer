import pytest

from analyzer.ratelimit import TokenBucket


class FakeTime:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_burst_awal_tanpa_menunggu() -> None:
    t = FakeTime()
    bucket = TokenBucket(2.0, capacity=2, clock=t.clock, sleep=t.sleep)
    bucket.acquire()
    bucket.acquire()
    assert t.sleeps == []


def test_menunggu_saat_token_habis() -> None:
    t = FakeTime()
    bucket = TokenBucket(2.0, capacity=1, clock=t.clock, sleep=t.sleep)
    bucket.acquire()
    bucket.acquire()
    assert t.sleeps == [pytest.approx(0.5)]


def test_parameter_tidak_valid() -> None:
    with pytest.raises(ValueError):
        TokenBucket(0.0)
