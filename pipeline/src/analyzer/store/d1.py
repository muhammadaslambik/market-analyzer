"""Penulisan hasil terbaru ke Cloudflare D1 lewat REST API."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

D1_QUERY_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account}/d1/database/{database}/query"
)
UPSERT_PRICE_SQL = (
    "INSERT INTO latest_price (market, symbol, timeframe, close, asof, source) "
    "VALUES (?, ?, ?, ?, ?, ?) "
    "ON CONFLICT (market, symbol, timeframe) DO UPDATE SET "
    "close = excluded.close, asof = excluded.asof, source = excluded.source"
)
UPSERT_META_SQL = (
    "INSERT INTO meta (key, value) VALUES (?, ?) "
    "ON CONFLICT (key) DO UPDATE SET value = excluded.value"
)


def iso_utc(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class D1Store:
    """Klien D1 minimal. Parameter dikirim sebagai teks (sesuai skema REST D1)."""

    def __init__(
        self, account: str, database: str, token: str, client: httpx.Client | None = None
    ) -> None:
        self._account = account
        self._database = database
        self._token = token
        self._client = client or httpx.Client(timeout=30)

    def _query(self, sql: str, params: list[str]) -> None:
        response = self._client.post(
            D1_QUERY_URL.format(account=self._account, database=self._database),
            headers={"Authorization": f"Bearer {self._token}"},
            json={"sql": sql, "params": params},
        )
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.status_code != 200 or not data.get("success", False):
            detail = data.get("errors") or response.text[:200]
            raise RuntimeError(f"D1 menolak query (HTTP {response.status_code}): {detail}")

    def upsert_latest_price(
        self,
        market: str,
        symbol: str,
        timeframe: str,
        close: float,
        asof: datetime,
        source: str,
    ) -> None:
        """Simpan harga terakhir. `asof` = waktu TUTUP candle terakhir (UTC)."""
        self._query(
            UPSERT_PRICE_SQL,
            [market, symbol, timeframe, repr(float(close)), iso_utc(asof), source],
        )

    def set_meta(self, key: str, value: str) -> None:
        self._query(UPSERT_META_SQL, [key, value])

    def close(self) -> None:
        self._client.close()
