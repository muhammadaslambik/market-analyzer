# Market Analyzer

Aplikasi analisa multi-aset: **Crypto, XAUUSD, Saham Indonesia, Saham US** —
masing-masing dengan panel 10 indikator yang di-scoring menjadi satu
**skor konfluensi** (Bullish / Netral / Bearish) plus rekomendasi SL/TP berbasis ATR.

> Sinyal bersifat probabilistik, bukan jaminan. Lihat `backtest/` untuk
> ekspektasi realistis (win rate 50-60% dengan manajemen risiko), bukan klaim akurasi tinggi.

## Struktur

```
app/
  core/indicators/   # engine generik (trend, momentum, volatility, volume)
  core/signals/      # confluence scorer + filter ADX
  assets/            # crypto, gold, stocks_id, stocks_us (+ config YAML per aset)
  api/               # FastAPI routes
backtest/            # engine backtest (fee + slippage)
tests/               # pytest, tanpa jaringan
```

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Contoh:
```
GET http://localhost:8000/analyze/crypto/BTCUSDT?timeframe=4h
GET http://localhost:8000/analyze/stocks_id/BBCA.JK
GET http://localhost:8000/screener/crypto?status_filter=strong_buy
POST http://localhost:8000/backtest
  {"asset_class": "crypto", "symbol": "BTCUSDT", "timeframe": "1d",
   "fee_bps": 10, "slippage_bps": 5}
```

Docker: `docker compose up --build`

## Menambah aset baru

1. Buat folder `app/assets/<nama>/` + `indicators_config.yaml` (10 indikator + bobot).
2. Subclass `BaseAsset`, implementasi `fetch_ohlcv()`.
3. Daftarkan di `app/api/routes_analyze.py::ASSETS`.

## Catatan jujur

- `foreign_flow`, `rs_vs_index`, `funding_oi` (non-crypto) saat ini stub
  netral — butuh data eksternal (CSV upload / futures API) di fase berikutnya.
- Bobot indikator harus divalidasi lewat backtest walk-forward sebelum dipercaya.
