"""Logika pemasangan skema database (Neon Postgres dan Cloudflare D1)."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import httpx
import psycopg

from analyzer.config import require_env

REPO_ROOT = Path(__file__).resolve().parents[3]
D1_QUERY_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account}/d1/database/{database}/query"
)
D1_LIST_TABLES = (
    "SELECT name FROM sqlite_master WHERE type = 'table' "
    "AND substr(name, 1, 4) <> '_cf_' AND substr(name, 1, 7) <> 'sqlite_' ORDER BY name"
)
NEON_LIST_TABLES = (
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema = 'public' ORDER BY table_name"
)


def split_statements(sql: str) -> list[str]:
    """Pecah skrip SQL menjadi pernyataan tunggal (komentar -- dibuang)."""
    without_comments = re.sub(r"--[^\n]*", "", sql)
    return [part.strip() for part in without_comments.split(";") if part.strip()]


def load_env_file(path: Path) -> None:
    """Muat berkas .env sederhana. Tidak menimpa variabel yang sudah ada."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def apply_neon(url: str, sql: str) -> list[str]:
    """Pasang skema ke Neon dan kembalikan daftar tabel di skema public."""
    statements = split_statements(sql)
    with psycopg.connect(url, connect_timeout=20) as conn:
        for statement in statements:
            conn.execute(statement)
        rows = conn.execute(NEON_LIST_TABLES).fetchall()
    return [str(row[0]) for row in rows]


def d1_query(client: httpx.Client, account: str, database: str, token: str, sql: str) -> dict:
    """Jalankan satu pernyataan di D1 lewat REST API. Token tidak pernah dicetak."""
    response = client.post(
        D1_QUERY_URL.format(account=account, database=database),
        headers={"Authorization": f"Bearer {token}"},
        json={"sql": sql},
    )
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code != 200 or not data.get("success", False):
        detail = data.get("errors") or response.text[:200]
        raise RuntimeError(f"D1 menolak query (HTTP {response.status_code}): {detail}")
    return data


def apply_d1(
    account: str,
    database: str,
    token: str,
    sql: str,
    client: httpx.Client | None = None,
) -> list[str]:
    """Pasang skema ke D1 dan kembalikan daftar tabel."""
    owns_client = client is None
    http = client or httpx.Client(timeout=30)
    try:
        for statement in split_statements(sql):
            d1_query(http, account, database, token, statement)
        data = d1_query(http, account, database, token, D1_LIST_TABLES)
    finally:
        if owns_client:
            http.close()
    results = (data.get("result") or [{}])[0].get("results") or []
    return [str(item["name"]) for item in results]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pasang skema database market-analyzer.")
    parser.add_argument("--target", choices=["neon", "d1", "all"], default="all")
    parser.add_argument("--schema-dir", type=Path, default=REPO_ROOT / "db")
    args = parser.parse_args(argv)
    load_env_file(REPO_ROOT / ".env")

    try:
        if args.target in ("neon", "all"):
            sql = (args.schema_dir / "neon" / "schema.sql").read_text(encoding="utf-8")
            tables = apply_neon(require_env("DATABASE_URL"), sql)
            print(f"Neon OK. Tabel: {', '.join(tables)}")
        if args.target in ("d1", "all"):
            sql = (args.schema_dir / "d1" / "schema.sql").read_text(encoding="utf-8")
            tables = apply_d1(
                require_env("CF_ACCOUNT_ID"),
                require_env("CF_D1_DATABASE_ID"),
                require_env("CF_API_TOKEN"),
                sql,
            )
            print(f"D1 OK. Tabel: {', '.join(tables)}")
    except (RuntimeError, psycopg.Error, httpx.HTTPError, OSError) as exc:
        first_line = (str(exc).splitlines() or [""])[0]
        print(f"GAGAL ({type(exc).__name__}): {first_line}", file=sys.stderr)
        return 1
    return 0
