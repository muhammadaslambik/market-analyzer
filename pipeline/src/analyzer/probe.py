"""Probe sumber data crypto.

Menguji beberapa API publik dari mesin yang menjalankan kode ini (mis. runner GitHub Actions)
untuk melihat mana yang bisa diakses, berapa candle yang dikembalikan, dan apakah ada
pemblokiran wilayah. Jalankan: python -m analyzer.probe
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

TIMEOUT = 20.0
Row = tuple[int, float, float]  # (waktu buka dalam ms, harga open, harga close)


def parse_binance(data: Any) -> list[Row]:
    return [(int(r[0]), float(r[1]), float(r[4])) for r in data]


def parse_bybit(data: Any) -> list[Row]:
    if data.get("retCode") != 0:
        raise ValueError(f"retCode={data.get('retCode')}")
    return [(int(r[0]), float(r[1]), float(r[4])) for r in data["result"]["list"]]


def parse_okx(data: Any) -> list[Row]:
    if data.get("code") != "0":
        raise ValueError(f"code={data.get('code')}")
    return [(int(r[0]), float(r[1]), float(r[4])) for r in data["data"]]


def parse_kraken(data: Any) -> list[Row]:
    if data.get("error"):
        raise ValueError(str(data["error"]))
    result = data["result"]
    key = next(k for k in result if k != "last")
    return [(int(r[0]) * 1000, float(r[1]), float(r[4])) for r in result[key]]


def parse_coinbase(data: Any) -> list[Row]:
    if isinstance(data, dict):
        raise ValueError(str(data.get("message", "galat")))
    # Format baris: [waktu, low, high, open, close, volume]
    return [(int(r[0]) * 1000, float(r[3]), float(r[4])) for r in data]


@dataclass(frozen=True)
class Candidate:
    name: str
    url: str
    params: dict[str, Any]
    parser: Callable[[Any], list[Row]]


@dataclass(frozen=True)
class Result:
    name: str
    http: int | None
    count: int
    sample: str
    note: str


CANDIDATES: list[Candidate] = [
    Candidate(
        "binance",
        "https://api.binance.com/api/v3/klines",
        {"symbol": "BTCUSDT", "interval": "1h", "limit": 1000},
        parse_binance,
    ),
    Candidate(
        "binance-vision",
        "https://data-api.binance.vision/api/v3/klines",
        {"symbol": "BTCUSDT", "interval": "1h", "limit": 1000},
        parse_binance,
    ),
    Candidate(
        "bybit",
        "https://api.bybit.com/v5/market/kline",
        {"category": "spot", "symbol": "BTCUSDT", "interval": "60", "limit": 1000},
        parse_bybit,
    ),
    Candidate(
        "okx",
        "https://www.okx.com/api/v5/market/candles",
        {"instId": "BTC-USDT", "bar": "1H", "limit": 300},
        parse_okx,
    ),
    Candidate(
        "kraken",
        "https://api.kraken.com/0/public/OHLC",
        {"pair": "XBTUSD", "interval": 60},
        parse_kraken,
    ),
    Candidate(
        "coinbase",
        "https://api.exchange.coinbase.com/products/BTC-USD/candles",
        {"granularity": 3600},
        parse_coinbase,
    ),
]


def _iso(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, UTC).strftime("%Y-%m-%d %H:%M")


def probe_one(client: httpx.Client, cand: Candidate) -> Result:
    """Uji satu kandidat. Tidak pernah melempar galat jaringan atau format."""
    try:
        response = client.get(cand.url, params=cand.params)
    except httpx.HTTPError as exc:
        return Result(cand.name, None, 0, "", f"gagal koneksi: {type(exc).__name__}")
    status = response.status_code
    if status == 451:
        return Result(cand.name, status, 0, "", "diblokir wilayah (451)")
    if status == 403:
        return Result(cand.name, status, 0, "", "ditolak (403), mungkin diblokir")
    if status != 200:
        return Result(cand.name, status, 0, "", f"HTTP {status}")
    try:
        rows = sorted(cand.parser(response.json()))
    except (ValueError, KeyError, IndexError, TypeError, StopIteration) as exc:
        return Result(cand.name, status, 0, "", f"format tak terduga: {type(exc).__name__}")
    sample = "; ".join(f"{_iso(ts)} o={o:g} c={c:g}" for ts, o, c in rows[:3])
    return Result(cand.name, status, len(rows), sample, "OK" if rows else "kosong")


def runner_country(client: httpx.Client) -> str:
    """Perkiraan negara asal IP mesin ini (hanya kode negara, bukan IP)."""
    try:
        response = client.get("https://ipinfo.io/country")
        if response.status_code == 200:
            return response.text.strip() or "tidak diketahui"
    except httpx.HTTPError:
        pass
    return "tidak diketahui"


def render_table(results: list[Result], country: str) -> str:
    lines = [
        f"Negara asal IP mesin: {country}",
        "",
        "| Sumber | HTTP | Candle | Contoh 3 candle pertama | Catatan |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        http = "-" if r.http is None else str(r.http)
        lines.append(f"| {r.name} | {http} | {r.count} | {r.sample or '-'} | {r.note} |")
    return "\n".join(lines)


def main() -> int:
    with httpx.Client(timeout=TIMEOUT, headers={"User-Agent": "market-analyzer-probe/0.1"}) as c:
        country = runner_country(c)
        results = [probe_one(c, cand) for cand in CANDIDATES]
    table = render_table(results, country)
    print(table)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(table + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
