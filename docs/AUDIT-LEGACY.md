# AUDIT KODE LEGACY — INDIKATOR & KAUSALITAS FASE 1

Dokumen ini mendokumentasikan hasil audit terhadap repositori kode `legacy/` untuk memilah indikator berbasis OHLCV yang valid, menganalisis struktur pembobotan, serta menguji status kausalitas (*truncation invariance*).

## 1. Ringkasan Konfigurasi & Pembobotan Crypto
Berdasarkan file `indicators_config.yaml` lama, total bobot bawaan dari 10 indikator terdaftar adalah **94.0**:

| Nama Indikator | Kategori | Bobot | Input Data | Status Porting / Keputusan Fase 1 |
| :--- | :--- | :--- | :--- | :--- |
| `ema_ribbon` | Tren | 12 | close | **Porting** — Kausal penuh. |
| `supertrend` | Tren | 12 | high, low, close | **Porting** — Kausal, butuh rekursi state loop. |
| `macd` | Momentum | 10 | close | **Porting** — Kausal penuh. |
| `rsi_divergence`| Momentum | 10 | close, high, low | **DITUNDA / REFACTOR** — Menggunakan fixed swing high/low window yang rawan bias masa depan jika tidak dibatasi ketat. |
| `bollinger` | Volatilitas | 8 | close | **Porting** — Kausal penuh. |
| `vwap_signal` | Volume | 10 | high, low, close, volume | **Porting** — Kausal penuh. |
| `cvd` | Order Flow | 12 | volume, taker_buy_volume| **Porting** — Menggunakan kolom internal Binance. |
| `funding_oi` | Derivatif | 12 | API Futures | **DIBUANG (STUB)** — Sesuai batas lingkup Fase 1. |
| `adx` | Filter | 8 | high, low, close | **Porting** — Kausal penuh. |
| `volume_profile`| Volume | 6 | high, low, volume, close| **Porting** — Menggunakan fixed trailing window. |

## 2. Analisis Kausalitas & Look-Ahead Bias
Evaluasi ketat terhadap invariant pemotongan data (*truncation invariance*):
- **EMA Ribbon, ADX, MACD, Bollinger, VWAP, CVD:** Menggunakan fungsi bawaan Pandas `.ewm()`, `.rolling()`, atau `.cumsum()` dengan pergeseran searah waktu. 100% Kausal dan aman dari kebocoran data masa depan.
- **Supertrend:** Menggunakan struktur perulangan `for i in range(len(df))` yang melakukan evaluasi berdasarkan data `c[i-1]` (lilin sebelumnya). Struktur ini kausal dan aman di-porting ke skema array NumPy/Pandas.
- **RSI Divergence (Kritis):** Algoritma swing point menggunakan metode pemeriksaan manual dalam *window segmentation*. Algoritma ini harus dipastikan hanya membaca data mundur dari titik waktu t, tanpa melihat titik puncak setelah waktu t.

## 3. Logika Confluence Scorer & Filter ADX
- **Normalisasi Skor:** Menggunakan rumus rata-rata tertimbang `(sum(sig * weight) / total_weight) * 100` untuk menghasilkan nilai presisi dalam rentang rentang keras **[-100, 100]**. Logika ini idempoten dan aman.
- **Filter Sideways:** Fungsi `apply_adx_filter` mendeteksi jika nilai rata-rata ADX berada di bawah ambang batas `< 20` (atau 25) untuk memaksa status menjadi `WAIT` guna menghindari sinyal palsu saat market konsolidasi. Logika filter ini dipertahankan sebagai penyaring akhir.
