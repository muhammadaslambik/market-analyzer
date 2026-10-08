import time
from analyzer.fund_cache import connect, get_fresh, put


def make_con(tmp_path):
    return connect(str(tmp_path / "test.db"))


def test_put_lalu_get_fresh(tmp_path):
    con = make_con(tmp_path)
    put(con, "AAAA.JK", {"market_cap": 1_000}, ["market_cap 1000 >= 500000000"])
    r = get_fresh(con, "AAAA.JK")
    assert r["payload"]["market_cap"] == 1_000
    assert r["verdict"][0].startswith("market_cap")


def test_ticker_belum_ada_return_none(tmp_path):
    con = make_con(tmp_path)
    assert get_fresh(con, "NOPE.JK") is None


def test_cache_basi_return_none(tmp_path):
    con = make_con(tmp_path)
    put(con, "OLD.JK", {"market_cap": 1}, [])
    # paksa fetched_at jadi tua
    con.execute("UPDATE fundamentals SET fetched_at = ? WHERE ticker = 'OLD.JK'",
                (int(time.time()) - 25 * 3600,))
    con.commit()
    assert get_fresh(con, "OLD.JK") is None


def test_put_dua_kali_timenya_upsert(tmp_path):
    con = make_con(tmp_path)
    put(con, "BB.JK", {"market_cap": 1}, ["a"])
    put(con, "BB.JK", {"market_cap": 2}, ["b"])
    r = get_fresh(con, "BB.JK")
    assert r["payload"]["market_cap"] == 2
    assert r["verdict"] == ["b"]
