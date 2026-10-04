import httpx
import pytest

from analyzer.probe import (
    Candidate,
    Result,
    parse_binance,
    parse_bybit,
    parse_coinbase,
    parse_kraken,
    parse_okx,
    probe_one,
    render_table,
)


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parser_binance() -> None:
    data = [[1700000000000, "100", "110", "90", "105", "5", 0, "0", 1, "0", "0", "0"]]
    assert parse_binance(data) == [(1700000000000, 100.0, 105.0)]


def test_parser_bybit_dan_galat() -> None:
    ok = {"retCode": 0, "result": {"list": [["1700000000000", "1", "2", "0", "1.5", "9", "9"]]}}
    assert parse_bybit(ok) == [(1700000000000, 1.0, 1.5)]
    with pytest.raises(ValueError):
        parse_bybit({"retCode": 10001, "result": {}})


def test_parser_okx() -> None:
    data = {"code": "0", "data": [["1700000000000", "1", "2", "0", "1.5", "9", "9", "9", "1"]]}
    assert parse_okx(data) == [(1700000000000, 1.0, 1.5)]


def test_parser_kraken() -> None:
    data = {
        "error": [],
        "result": {
            "XXBTZUSD": [[1700000000, "1", "2", "0", "1.5", "1", "9", 3]],
            "last": 1700000000,
        },
    }
    assert parse_kraken(data) == [(1700000000000, 1.0, 1.5)]


def test_parser_coinbase() -> None:
    assert parse_coinbase([[1700000000, 0.5, 2.0, 1.0, 1.5, 9.0]]) == [(1700000000000, 1.0, 1.5)]
    with pytest.raises(ValueError):
        parse_coinbase({"message": "NotFound"})


def _cand() -> Candidate:
    return Candidate("uji", "https://contoh.test/klines", {}, parse_binance)


def test_probe_one_ok() -> None:
    row = [1700000000000, "100", "110", "90", "105", "5", 0, "0", 1, "0", "0", "0"]
    client = _client(lambda request: httpx.Response(200, json=[row, row]))
    result = probe_one(client, _cand())
    assert result.http == 200 and result.count == 2 and result.note == "OK"


def test_probe_one_diblokir_451() -> None:
    client = _client(lambda request: httpx.Response(451, text="blocked"))
    result = probe_one(client, _cand())
    assert result.http == 451 and "diblokir" in result.note


def test_probe_one_galat_koneksi_tidak_melempar() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("gagal")

    result = probe_one(_client(handler), _cand())
    assert result.http is None and "koneksi" in result.note


def test_probe_one_format_aneh() -> None:
    client = _client(lambda request: httpx.Response(200, json={"bukan": "daftar"}))
    result = probe_one(client, _cand())
    assert "format tak terduga" in result.note


def test_render_table_memuat_semua_sumber() -> None:
    table = render_table([Result("a", 200, 5, "x", "OK"), Result("b", None, 0, "", "gagal")], "US")
    assert "| a | 200 | 5 |" in table and "| b | - | 0 |" in table and "US" in table
