"""Tes idx_fetcher. Tidak memanggil jaringan — fungsi murni diuji dengan
data sintetis. Tes integrasi yfinance ditandai dan tidak jalan otomatis."""
import pandas as pd
import pytest

from analyzer.idx_fetcher import CacingParams, is_cacing_fundamental

P = CacingParams()


def _fund(mc, pbv, ni):
    return {"ticker": "TEST.JK", "market_cap": mc, "pbv": pbv, "net_income": ni}


class TestCacingFilter:
    def test_cacing_lolos(self):
        ok, reasons = is_cacing_fundamental(_fund(100e9, 0.3, -5e9), P)
        assert ok is True and reasons == []

    def test_bukan_cacing_karena_cap(self):
        ok, reasons = is_cacing_fundamental(_fund(456e12, 0.3, -5e9), P)
        assert ok is False and any("market_cap" in r for r in reasons)

    def test_bukan_cacing_karena_pbv(self):
        ok, reasons = is_cacing_fundamental(_fund(100e9, 1.42, -5e9), P)
        assert ok is False and any("pbv" in r for r in reasons)

    def test_bukan_cacing_karena_laba(self):
        ok, reasons = is_cacing_fundamental(_fund(100e9, 0.3, 20e9), P)
        assert ok is False and any("net_income" in r for r in reasons)

    def test_data_kosong_ditolak(self):
        ok, reasons = is_cacing_fundamental(_fund(None, None, None), P)
        assert ok is False and len(reasons) == 3

    def test_pbv_negatif_ekuitas_hampir_habis(self):
        ok, _ = is_cacing_fundamental(_fund(100e9, -0.1, -1e9), P)
        assert ok is True


class TestParams:
    def test_params_bisa_diubah(self):
        p = CacingParams(max_market_cap=1e12, require_negative_profit=False)
        ok, _ = is_cacing_fundamental(_fund(800e9, 0.5, 10e9), p)
        assert ok is True
