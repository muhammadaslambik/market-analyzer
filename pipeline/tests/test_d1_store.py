import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from analyzer.migrate import split_statements
from analyzer.store.d1 import UPSERT_META_SQL, UPSERT_PRICE_SQL, D1Store, iso_utc

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "token-rahasia-uji"
ASOF = datetime(2026, 1, 1, 5, 0, tzinfo=UTC)


def _store(handler) -> D1Store:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return D1Store("akun1", "db1", TOKEN, client=client)


def test_upsert_latest_price_mengirim_sql_dan_parameter_teks() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/client/v4/accounts/akun1/d1/database/db1/query"
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"success": True, "result": [{"results": []}]})

    _store(handler).upsert_latest_price("crypto", "BTCUSDT", "1h", 64230.5, ASOF, "binance-vision")
    body = seen[0]
    assert body["sql"] == UPSERT_PRICE_SQL
    assert body["params"] == [
        "crypto",
        "BTCUSDT",
        "1h",
        "64230.5",
        "2026-01-01T05:00:00Z",
        "binance-vision",
    ]


def test_set_meta() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json={"success": True})

    _store(handler).set_meta("crypto_hourly.status", "ok")
    assert seen[0] == {"sql": UPSERT_META_SQL, "params": ["crypto_hourly.status", "ok"]}


def test_galat_d1_tanpa_membocorkan_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"success": False, "errors": [{"message": "ditolak"}]})

    with pytest.raises(RuntimeError) as info:
        _store(handler).set_meta("k", "v")
    assert TOKEN not in str(info.value) and "403" in str(info.value)


def test_iso_utc() -> None:
    assert iso_utc(ASOF) == "2026-01-01T05:00:00Z"


def test_sql_upsert_valid_di_sqlite_dan_menjadi_angka() -> None:
    schema = (REPO_ROOT / "db" / "d1" / "schema.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(":memory:")
    for statement in split_statements(schema):
        conn.execute(statement)
    first = ["crypto", "BTCUSDT", "1h", "64230.5", "2026-01-01T05:00:00Z", "a"]
    second = ["crypto", "BTCUSDT", "1h", "65000.25", "2026-01-01T06:00:00Z", "b"]
    conn.execute(UPSERT_PRICE_SQL, first)
    conn.execute(UPSERT_PRICE_SQL, second)
    rows = conn.execute("SELECT close, typeof(close), asof, source FROM latest_price").fetchall()
    assert rows == [(65000.25, "real", "2026-01-01T06:00:00Z", "b")]
    conn.execute(UPSERT_META_SQL, ["k", "1"])
    conn.execute(UPSERT_META_SQL, ["k", "2"])
    assert conn.execute("SELECT key, value FROM meta").fetchall() == [("k", "2")]
