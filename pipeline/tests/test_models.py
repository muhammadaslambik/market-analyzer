from datetime import timedelta

import pytest

from analyzer.models import interval_of


def test_interval_didukung() -> None:
    assert interval_of("1h") == timedelta(hours=1)
    assert interval_of("1d") == timedelta(days=1)


def test_interval_tidak_didukung() -> None:
    with pytest.raises(ValueError):
        interval_of("5m")
