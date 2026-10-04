import json
import sqlite3
from pathlib import Path

import httpx
import pytest

from analyzer.migrate import apply_d1, load_env_file, split_statements

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKEN = "token-rahasia-uji"


def test_split_statements_membuang_komentar() -> None:
    sql = "-- judul\nCREATE TABLE a (x int); -- akhir\n\nCREATE TABLE b (y int);\n"
    assert split_statements(sql) == ["CREATE TABLE a (x int)", "CREATE TABLE b (y int)"]


def test_skema_d1_valid_di_sqlite_dan_idempoten() -> None:
    sql = (REPO_ROOT / "db" / "d1" / "schema.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(":memory:")
    for _ in range(2):
        for statement in split_statements(sql):
            conn.execute(statement)
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"latest_price", "meta", "latest_forecast", "latest_indicators"} <= names


def test_skema_neon_semua_idempoten() -> None:
    sql = (REPO_ROOT / "db" / "neon" / "schema.sql").read_text(encoding="utf-8")
    statements = split_statements(sql)
    assert len(statements) == 6
    assert all(s.startswith("CREATE TABLE IF NOT EXISTS") for s in statements)


def test_load_env_file_tidak_menimpa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env = tmp_path / ".env"
    env.write_text('# komentar\nBARU_A="nilai a"\nSUDAH_ADA=baru\n', encoding="utf-8")
    monkeypatch.delenv("BARU_A", raising=False)
    monkeypatch.setenv("SUDAH_ADA", "lama")
    load_env_file(env)
    import os

    assert os.environ["BARU_A"] == "nilai a"
    assert os.environ["SUDAH_ADA"] == "lama"


def test_apply_d1_mengirim_permintaan_benar() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/client/v4/accounts/akun1/d1/database/db1/query"
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        body = json.loads(request.content)
        seen.append(body)
        if "sqlite_master" in body["sql"]:
            payload = {"success": True, "result": [{"results": [{"name": "meta"}]}]}
        else:
            payload = {"success": True, "result": [{"results": []}]}
        return httpx.Response(200, json=payload)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    tables = apply_d1("akun1", "db1", TOKEN, "CREATE TABLE a (x int);", client=client)
    assert tables == ["meta"]
    assert seen[0] == {"sql": "CREATE TABLE a (x int)"}


def test_apply_d1_gagal_tanpa_membocorkan_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"success": False, "errors": [{"message": "ditolak"}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeError) as info:
        apply_d1("akun1", "db1", TOKEN, "CREATE TABLE a (x int);", client=client)
    assert TOKEN not in str(info.value)
    assert "403" in str(info.value)
