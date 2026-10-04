import pytest

import analyzer
from analyzer.config import require_env


def test_version_tersedia() -> None:
    assert analyzer.__version__ == "0.1.0"


def test_require_env_membaca_nilai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTOH_VAR", " nilai ")
    assert require_env("CONTOH_VAR") == "nilai"


def test_require_env_gagal_jika_kosong(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VAR_TIDAK_ADA", raising=False)
    with pytest.raises(RuntimeError):
        require_env("VAR_TIDAK_ADA")
