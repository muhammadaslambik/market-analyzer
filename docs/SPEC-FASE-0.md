# Spesifikasi Teknis — Fase 0: Fondasi dan Pipeline Data Crypto

Dokumen ini turunan dari `docs/PRD.md` (Bagian 5, 6, 10, 11, 12). Jika bertentangan, **tanyakan ke pemilik**, jangan memilih sendiri.

## 1. Tujuan dan kriteria selesai

Membangun fondasi repo dan pipeline yang mengambil, memvalidasi, dan menyimpan candle crypto secara otomatis, gratis, tanpa kartu kredit.

**Fase 0 dianggap selesai bila:**
1. Backfill selesai: untuk BTC dan ETH minimal 2 tahun candle 1 jam dan 5 tahun candle 1 hari (atau sebanyak yang disediakan sumber), tanpa celah yang tidak terdokumentasi.
2. Job terjadwal berjalan **48 jam berturut-turut tanpa intervensi**, dengan ≥ 95% run berstatus `ok` di tabel `ingest_runs`.
3. Semua tes lulus di CI (ruff + pytest).
4. `meta` di D1 menampilkan waktu sukses terakhir tiap job.
5. Tidak ada secret di repo atau log. README menjelaskan setup dari nol.

## 2. Keputusan teknis

| Topik | Keputusan |
|---|---|
| Bahasa pipeline | Python 3.12, `pyproject.toml`, tipe statis (type hints), `ruff`, `pytest` |
| Penyimpanan candle | **Neon Postgres** (tabel `candles`). Volume kecil (≈ 10 simbol × 8.760 candle 1 jam per tahun), jadi muat di 1 GB. Snapshot parquet ke repo dataset Hugging Face hanya sebagai cadangan opsional (tugas 0.9) |
| Hasil terbaru untuk UI | **Cloudflare D1**, ditulis dari Actions lewat REST API Cloudflare (API token izin D1 Edit). Verifikasi endpoint di dokumentasi saat ini |
| Penjadwal | GitHub Actions (cron + `workflow_dispatch`) |
| Waktu | Semua timestamp **UTC**, disimpan sebagai waktu *buka* candle |
| Candle | Hanya candle yang **sudah tutup** (`ts + interval <= sekarang`) |
| Idempotensi | Semua job aman dijalankan ulang (`INSERT ... ON CONFLICT DO NOTHING`) |
| Sumber data | Dipilih lewat **uji probe dari runner Actions** (tugas 0.3), bukan ditebak. Lihat Bagian 5 |
| Biaya | Rp0. Dilarang menambah layanan yang butuh kartu |

## 3. Struktur repo

```
market-analyzer/
├─ AGENTS.md
├─ README.md
├─ docs/
│  ├─ PRD.md
│  ├─ SPEC-FASE-0.md
│  └─ DECISIONS.md            # catatan keputusan (sumber data terpilih, alasan, tanggal)
├─ db/
│  ├─ neon/schema.sql
│  ├─ d1/schema.sql
│  └─ migrate.py
├─ pipeline/
│  ├─ pyproject.toml
│  ├─ config/symbols.yaml     # daftar simbol dan pemetaan per sumber
│  ├─ src/analyzer/
│  │  ├─ config.py
│  │  ├─ models.py            # dataclass Candle, dll
│  │  ├─ sources/{base.py, <sumber_terpilih>.py}
│  │  ├─ ratelimit.py
│  │  ├─ validate.py
│  │  ├─ store/{neon.py, d1.py}
│  │  └─ jobs/{backfill.py, crypto_hourly.py, crypto_daily.py}
│  └─ tests/
├─ worker/                    # opsional di Fase 0 (tugas 0.9)
│  ├─ wrangler.toml
│  └─ src/index.ts
└─ .github/workflows/{ci.yml, probe-sources.yml, crypto-hourly.yml, crypto-daily.yml}
```

## 4. Skema database

### 4.1 Neon (Postgres) — `db/neon/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS candles (
  market      text             NOT NULL,           -- 'crypto'
  symbol      text             NOT NULL,           -- mis. 'BTCUSDT'
  timeframe   text             NOT NULL,           -- '1h' | '1d'
  ts          timestamptz      NOT NULL,           -- waktu BUKA candle, UTC
  open        double precision NOT NULL,
  high        double precision NOT NULL,
  low         double precision NOT NULL,
  close       double precision NOT NULL,
  volume      double precision NOT NULL,
  source      text             NOT NULL,
  ingested_at timestamptz      NOT NULL DEFAULT now(),
  PRIMARY KEY (market, symbol, timeframe, ts)
);

CREATE TABLE IF NOT EXISTS ingest_runs (
  id            bigserial PRIMARY KEY,
  job           text        NOT NULL,
  started_at    timestamptz NOT NULL,
  finished_at   timestamptz,
  status        text        NOT NULL,              -- 'ok' | 'partial' | 'error'
  rows_written  integer     NOT NULL DEFAULT 0,
  api_calls     integer     NOT NULL DEFAULT 0,
  error         text
);

CREATE TABLE IF NOT EXISTS data_quality_log (
  id        bigserial PRIMARY KEY,
  market    text, symbol text, timeframe text,
  ts        timestamptz,
  issue     text        NOT NULL,                  -- 'gap' | 'duplicate' | 'ohlc_invalid' | 'outlier' | 'not_closed'
  detail    jsonb,
  logged_at timestamptz NOT NULL DEFAULT now()
);

-- Disiapkan untuk Fase 1 (dibuat sekarang, belum diisi)
CREATE TABLE IF NOT EXISTS predictions (
  id bigserial PRIMARY KEY, market text, symbol text, horizon text,
  issued_at timestamptz, due_at timestamptz,
  p_up double precision, q10 double precision, q50 double precision, q90 double precision,
  model_version text, features_hash text
);
CREATE TABLE IF NOT EXISTS outcomes (
  prediction_id bigint PRIMARY KEY REFERENCES predictions(id),
  realized_return double precision, direction_hit boolean, interval_hit boolean,
  scored_at timestamptz
);
CREATE TABLE IF NOT EXISTS model_runs (
  version text, market text, horizon text, metrics_json jsonb,
  passed_gate boolean, created_at timestamptz DEFAULT now()
);
```

Koneksi wajib memakai SSL (`sslmode=require`) lewat `DATABASE_URL`.

### 4.2 D1 (SQLite) — `db/d1/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS latest_price (
  market TEXT NOT NULL, symbol TEXT NOT NULL, timeframe TEXT NOT NULL,
  close REAL NOT NULL, asof TEXT NOT NULL, source TEXT NOT NULL,
  PRIMARY KEY (market, symbol, timeframe)
);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
-- Disiapkan untuk fase berikutnya
CREATE TABLE IF NOT EXISTS latest_forecast (
  market TEXT, symbol TEXT, horizon TEXT,
  p_up REAL, q10 REAL, q50 REAL, q90 REAL,
  confidence TEXT, status TEXT, model_version TEXT, asof TEXT,
  PRIMARY KEY (market, symbol, horizon)
);
CREATE TABLE IF NOT EXISTS latest_indicators (
  market TEXT, symbol TEXT, timeframe TEXT, indicator TEXT,
  signal TEXT, weight REAL, value REAL, asof TEXT,
  PRIMARY KEY (market, symbol, timeframe, indicator)
);
```

Contoh isi `meta`: `crypto_hourly.last_success = 2026-10-04T08:07:00Z`.

## 5. Sumber data crypto

**Masalah yang diketahui:** sebagian bursa memblokir IP dari server di AS, dan runner GitHub Actions biasanya berada di infrastruktur AS. Karena itu sumber **tidak ditentukan di awal**.

**Tugas probe (0.3):** buat workflow `probe-sources.yml` (manual) yang, dari runner Actions, mencoba mengambil 100 candle 1 jam BTC dari beberapa kandidat API publik (mis. Binance dan endpoint data-only miliknya, Bybit, OKX, Kraken, Coinbase). Catat per kandidat: status HTTP, jumlah candle, batas permintaan, ada/tidaknya blokir wilayah, dan batas candle per permintaan. Pilih sumber utama dan satu cadangan, lalu tulis keputusan di `docs/DECISIONS.md`.

Jika hanya pasangan USD (bukan USDT) yang tersedia, dokumentasikan bahwa itu pendekatan (*proxy*) dan beri nama simbol kanonik sesuai kenyataan (mis. `BTCUSD`).

**Antarmuka adaptor:**

```python
@dataclass(frozen=True)
class Candle:
    market: str; symbol: str; timeframe: str   # '1h' | '1d'
    ts: datetime                                # UTC, waktu buka
    open: float; high: float; low: float; close: float; volume: float
    source: str

class CandleSource(Protocol):
    name: str
    def fetch_candles(self, symbol: str, timeframe: str,
                      start: datetime, end: datetime) -> list[Candle]: ...
```

Aturan adaptor: pagination otomatis, retry dengan backoff eksponensial, `ratelimit.py` (token bucket per sumber) dan penghitung `api_calls`, timeout jelas, dan tidak pernah mengembalikan candle yang belum tutup.

**Simbol awal (`config/symbols.yaml`):** BTC, ETH, SOL, XRP, BNB, ADA, DOGE, AVAX, LINK, LTC (boleh disesuaikan setelah probe; BNB mungkin tidak ada di semua sumber).

## 6. Validasi data (`validate.py`)

Aturan per candle dan per deret:
- `low <= min(open, close)` dan `high >= max(open, close)`, semua harga > 0, `volume >= 0`.
- Tidak ada duplikat `ts`. Tidak ada celah: tiap timestamp yang diharapkan harus ada.
- Candle belum tutup ditolak.
- Anomali: `|ln(close_t / close_{t-1})|` melebihi ambang di `config.py` ditandai `outlier`. **Dicatat, tidak dihapus diam-diam.**

Hasil validasi: candle valid ditulis ke `candles`. Masalah ditulis ke `data_quality_log`. Celah yang bisa diisi ulang dicoba sekali, sisanya dibiarkan tercatat.

## 7. Job

**`backfill.py`** — idempoten dan bisa dilanjutkan. Mengambil mundur per jendela sampai batas kedalaman yang ditentukan, dengan penghormatan ke rate limit. Argumen: `--symbols`, `--timeframe`, `--since`.

**`crypto_hourly.py`** (cron `7 * * * *`, jeda beberapa menit setelah candle tutup):
1. Baca `max(ts)` per (simbol, timeframe) dari Neon.
2. Ambil candle dari `max(ts)+interval` sampai candle tutup terakhir.
3. Validasi, lalu upsert dengan `ON CONFLICT DO NOTHING`.
4. Tulis `latest_price` dan `meta` ke D1.
5. Catat `ingest_runs` (`ok`, `partial` jika D1 gagal tapi Neon berhasil, `error` jika gagal).

**`crypto_daily.py`** (cron `12 0 * * *`): sama untuk timeframe `1d`.

Kegagalan satu simbol tidak boleh menghentikan simbol lain. Job keluar dengan kode non-nol hanya bila status `error`.

## 8. GitHub Actions (kerangka `crypto-hourly.yml`)

```yaml
name: crypto-hourly
on:
  schedule: [{ cron: "7 * * * *" }]
  workflow_dispatch: {}
concurrency: { group: crypto-hourly, cancel-in-progress: false }
jobs:
  run:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12", cache: pip }
      - run: pip install -e pipeline
      - run: python -m analyzer.jobs.crypto_hourly
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          CF_ACCOUNT_ID: ${{ secrets.CF_ACCOUNT_ID }}
          CF_D1_DATABASE_ID: ${{ secrets.CF_D1_DATABASE_ID }}
          CF_API_TOKEN: ${{ secrets.CF_API_TOKEN }}
```

Catatan: cron tidak dijamin tepat waktu. Setahu saya, GitHub menonaktifkan workflow terjadwal di repo publik yang tidak aktif 60 hari. Verifikasi aturan terbaru, dan siapkan langkah menjaga aktivitas repo bila perlu.

## 9. Worker (opsional, tugas 0.9)

Kontrak API (semua JSON, CORS dibatasi ke `ALLOWED_ORIGIN`):

| Endpoint | Respons |
|---|---|
| `GET /api/health` | `{"ok":true,"time":"<ISO UTC>"}` |
| `GET /api/meta` | `{"jobs":{"crypto_hourly":{"last_success":"<ISO>","status":"ok"}}}` |
| `GET /api/price/crypto/:symbol?timeframe=1h` | `{"market":"crypto","symbol":"BTCUSDT","timeframe":"1h","close":64230.5,"asof":"<ISO>","source":"<nama>","stale":false}` |

`stale = true` bila `asof` lebih tua dari 2× interval. Cache `max-age` 60 detik untuk harga. Batas 100 ribu permintaan per hari (Workers gratis) dijaga lewat cache.

## 10. Konfigurasi dan secrets

| Nama | Lokasi | Keterangan |
|---|---|---|
| `DATABASE_URL` | GitHub Secrets | String koneksi Neon (SSL) |
| `CF_ACCOUNT_ID`, `CF_D1_DATABASE_ID`, `CF_API_TOKEN` | GitHub Secrets | Akses D1 lewat REST. Token seminimal mungkin |
| `ALLOWED_ORIGIN` | Variabel Worker | Domain UI |
| Ambang outlier, daftar simbol | `config.py` / `symbols.yaml` | Bukan secret |

Jangan pernah mencetak nilai secret ke log atau commit file `.env`. Sediakan `.env.example` berisi nama saja.

## 11. Daftar tugas bertahap

Kerjakan **satu tugas per sesi**, lalu berhenti dan ringkas hasilnya.

| ID | Tugas | Selesai bila |
|---|---|---|
| 0.1 | Inisialisasi repo, struktur, `pyproject.toml`, `ruff`, `pytest`, `ci.yml`, README | CI hijau pada commit pertama |
| 0.2 | `schema.sql` Neon dan D1 + `migrate.py` | Skema terpasang di Neon dan D1, dapat dijalankan ulang tanpa error |
| 0.3 | Workflow dan skrip probe sumber data, `docs/DECISIONS.md` | Tabel hasil probe tercatat, sumber utama dan cadangan dipilih |
| 0.4 | Adaptor sumber, `ratelimit.py`, tes dengan HTTP palsu | Tes lulus tanpa jaringan, pagination dan retry teruji |
| 0.5 | `validate.py` + tes | Tiap aturan di Bagian 6 punya tes lulus dan tes gagal |
| 0.6 | `backfill.py` | Backfill BTC/ETH 1h dan 1d selesai, dijalankan dua kali tanpa duplikat |
| 0.7 | `crypto_hourly.py`, `crypto_daily.py`, penulisan D1 | Dijalankan manual: `candles`, `ingest_runs`, `latest_price`, `meta` terisi |
| 0.8 | Workflow terjadwal dan pemantauan | 48 jam tanpa intervensi, ≥ 95% run `ok` |
| 0.9 | (Opsional) Worker `/api/*`, snapshot parquet ke HF | Endpoint sesuai kontrak, tes dasar lulus |

## 12. Risiko khusus Fase 0

| Risiko | Mitigasi |
|---|---|
| Sumber memblokir IP runner | Probe di 0.3, sumber cadangan, catat di DECISIONS.md |
| Batas permintaan sumber | Token bucket, backoff, hitung `api_calls` |
| Neon compute tidur (bangun lambat) | Retry koneksi dengan backoff pendek |
| Cron tertunda atau dinonaktifkan | `workflow_dispatch` manual, pantau `meta.last_success` |
| Candle belum tutup masuk ke database | Filter `ts + interval <= now` dan tes khusus |

## 13. Di luar cakupan Fase 0

Model, indikator, skor konfluensi, UI baru, pasar selain crypto, dan semua hal pada Fase 1 ke atas.
