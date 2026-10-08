import time

from analyzer.fund_cache import connect, put
from analyzer.idx_fetcher import CacingParams, get_fundamentals_cached


def seed(con, ticker):
    put(con, ticker,
        {"market_cap": 1_000_000_000, "pbv": 0.5,
         "trailing_eps": 10, "net_income": 1_000_000, "currency": "IDR"},
        ["seeded"])


def test_cache_hit_tidak_fetch(tmp_path):
    # Cache segar -> verdict dihitung ulang dari payload cache, tanpa network call.
    db = str(tmp_path / "g.db")
    con = connect(db)
    seed(con, "CCCC.JK")
    con.close()

    is_cacing, reasons, fund = get_fundamentals_cached("CCCC.JK", CacingParams(), db)

    assert is_cacing is False          # PBV 0.5, laba positif, cap >= 500M -> bukan cacing
    assert fund["pbv"] == 0.5          # data benar-benar dari cache
    assert reasons                     # alasan eksplisit tetap dihasilkan


def test_cache_basi_maka_fetch(tmp_path, monkeypatch):
    # Cache basi (> 24 jam) -> fetch_fundamentals terpanggil, hasilnya tersimpan lagi.
    db = str(tmp_path / "g.db")
    con = connect(db)
    seed(con, "DDDD.JK")
    con.execute("UPDATE fundamentals SET fetched_at = ? WHERE ticker = 'DDDD.JK'",
                (int(time.time()) - 25 * 3600,))
    con.commit()
    con.close()

    calls = []

    def fake_fetch(ticker):
        calls.append(ticker)
        return {"market_cap": 400_000_000, "pbv": 0.3, "trailing_eps": 5,
                "net_income": -1, "currency": "IDR"}

    import analyzer.idx_fetcher as mod
    monkeypatch.setattr(mod, "fetch_fundamentals", fake_fetch)

    is_cacing, reasons, fund = get_fundamentals_cached("DDDD.JK", CacingParams(), db)
    assert calls == ["DDDD.JK"]                       # fetch terpanggil karena cache basi
    assert is_cacing is True                          # net_income -1 -> lolos filter cacing
    assert reasons == []                              # tidak ada kriteria yang gagal


    # Panggilan kedua: cache sudah di-refresh, jadi TIDAK boleh fetch lagi.
    calls.clear()

    def must_not_fetch(ticker):
        raise AssertionError("harus cache hit, tidak boleh fetch ulang")

    monkeypatch.setattr(mod, "fetch_fundamentals", must_not_fetch)
    is_cacing2, _, _ = get_fundamentals_cached("DDDD.JK", CacingParams(), db)
    assert is_cacing2 is True
def test_non_cacing_punya_alasan(tmp_path, monkeypatch):
    # Saham sehat -> TIDAK lolos filter cacing, dengan alasan eksplisit.
    db = str(tmp_path / "g.db")

    import analyzer.idx_fetcher as mod

    def fake_fetch(ticker):
        return {"market_cap": 900_000_000_000, "pbv": 3.2, "trailing_eps": 500,
                "net_income": 50_000_000_000, "currency": "IDR"}

    monkeypatch.setattr(mod, "fetch_fundamentals", fake_fetch)

    is_cacing, reasons, fund = get_fundamentals_cached("EEEE.JK", CacingParams(), db)
    assert is_cacing is False
    assert any("market_cap" in r for r in reasons)
    assert any("pbv" in r for r in reasons)
    assert any("net_income" in r for r in reasons)
