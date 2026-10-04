# PRD — Market Analyzer

**Versi:** 1.0 (4 Oktober 2026) · **Pemilik:** muhammadaslambik · **Status:** Draf untuk dikerjakan bertahap

> **Penting:** Aplikasi ini adalah alat analisa probabilistik, bukan nasihat keuangan dan bukan jaminan hasil. Semua angka batas layanan gratis di dokumen ini berasal dari dokumentasi dan sumber pihak ketiga per Oktober 2026 dan **harus diverifikasi ulang** sebelum dijadikan dasar (lihat Bagian 14).

---

## 1. Ringkasan dan tujuan

Market Analyzer memantau dan menganalisa **saham AS, saham Indonesia, XAUUSD, dan crypto**, lalu menghasilkan **probabilitas terkalibrasi** arah dan rentang harga untuk beberapa horizon waktu. Seluruh infrastruktur berjalan **gratis dan tanpa kartu kredit**.

**Tujuan produk**
1. Memberi analisa konfluensi indikator yang transparan (skor, bobot, penjelasan per indikator).
2. Memberi **probabilitas dan rentang** yang kalibrasinya terbukti di data yang tidak pernah dilihat model.
3. Membuktikan kualitas lewat **track record publik** (prediksi vs hasil nyata).
4. Berjalan stabil di batas layanan gratis.

**Bukan tujuan (non-goals)**
- Eksekusi order, manajemen portofolio, atau sinyal berbayar.
- Prediksi harga titik jangka panjang (6 bulan - 1 tahun) yang diklaim presisi.
- Menjanjikan akurasi tertentu. Target adalah **kalibrasi yang jujur dan keunggulan yang terukur di atas pembanding sederhana**.

## 2. Prinsip desain

1. **Probabilitas, bukan tebakan.** Setiap keluaran berupa peluang dan rentang, dengan tingkat keyakinan.
2. **Boleh menolak.** Jika tidak ada keunggulan statistik, UI menampilkan "Tidak ada sinyal" atau "Eksperimental".
3. **Evaluasi dulu, fitur kemudian.** Tidak ada model atau indikator yang tampil tanpa lulus gerbang evaluasi (Bagian 7.6).
4. **Hitung sebelumnya, sajikan murah.** Model dihitung terjadwal, UI hanya membaca hasil.
5. **Satu basis kode, adaptor per pasar.**
6. **Gratis tanpa kartu** sebagai batasan keras.

## 3. Pengguna dan skenario

| Pengguna | Kebutuhan |
|---|---|
| Trader/investor ritel (utama) | Melihat skor, peluang, rentang harga, stop loss dan target berbasis ATR per aset |
| Pembuat produk (pemilik) | Memantau kualitas model, drift, dan kesehatan pipeline |
| Calon klien/rekruter (portofolio) | Melihat bukti kemampuan analitik dan rekayasa |

## 4. Ruang lingkup

### 4.1 Universe awal (dibatasi karena kuota data gratis)

| Pasar | Universe v1 | Catatan |
|---|---|---|
| Crypto | BTC, ETH + sekitar 8 aset likuid | Data paling mudah, mulai di sini |
| XAUUSD | 1 instrumen | Pasar spot tidak punya volume sebenarnya, indikator volume tidak dipakai |
| Saham AS | SPY, QQQ + sekitar 30-40 saham besar | Data harian dulu |
| Saham Indonesia | IHSG + sekitar 20-30 saham likuid (mis. LQ45) | Sumber gratis belum terverifikasi, mulai belakangan |

### 4.2 Horizon dan tingkat kepercayaan

| Tier | Horizon | Data | Keluaran | Ekspektasi |
|---|---|---|---|---|
| A | 1, 3, 6, 10 jam; 1 hari | Candle 1 jam / harian | Peluang naik, kuantil return (10/50/90), peluang menyentuh target/stop | Keunggulan kecil tapi bisa diuji |
| B | 3 hari, 1 minggu | Harian | Sama | Lebih berisik, keunggulan lebih sulit |
| C | 1, 3, 6 bulan, 1 tahun | Harian/mingguan | **Skenario dan kerucut volatilitas bersyarat rezim**, tanpa prediksi titik | Informasi konteks, bukan sinyal |

## 5. Arsitektur (gratis tanpa kartu)

```
Sumber data (API gratis) ─┐
                          ├─► GitHub Actions (cron, Python)
Data historis (cache) ────┘     ├─ ambil & validasi data
                                ├─ hitung fitur & indikator
                                ├─ inferensi model + kalibrasi
                                ├─ tulis hasil ──► Cloudflare D1 (hasil terbaru)
                                ├─ tulis log ───► Neon Postgres (log prediksi, evaluasi)
                                └─ unggah riwayat ► Dataset repo Hugging Face (parquet)

Pengunjung ─► Cloudflare Pages (UI statis) ─► Cloudflare Worker (cache + API tipis) ─► D1
Browser ─► stream publik crypto (harga live, tanpa key)
```

| Lapisan | Pilihan | Batas gratis (verifikasi!) | Alasan |
|---|---|---|---|
| Hitung dan model | GitHub Actions | Gratis untuk repo publik | Cron, Python, tanpa kartu |
| Hasil terbaru | Cloudflare D1 | ~5 GB, ~5 jt baca & ~100 rb tulis/hari (sumber pihak ketiga) | Baca cepat dari edge |
| Log dan evaluasi | Neon Postgres | 1 GB/project, 20 GB total, 100 CU-jam | Query evaluasi relasional |
| Riwayat besar | Repo dataset Hugging Face | Gratis | Parquet/CSV, jangan taruh di Pages |
| API tipis dan cache | Cloudflare Workers | 100 rb permintaan/hari, 10 ms CPU | Menyembunyikan key, melindungi kuota data |
| UI | Cloudflare Pages | Permintaan statis tanpa batas, 500 build/bulan | Hasil di D1 sehingga data baru tidak memicu build |

**Sengaja dihindari:** R2 (butuh metode pembayaran), Oracle (butuh kartu), Hugging Face Space komputasi (berbayar), Supabase (project gratis bisa di-pause), GitHub Pages sebagai hosting produk komersial (ketentuan melarang SaaS komersial).

**Pagar keamanan:** semua API key hanya di GitHub Secrets / Worker secrets. Tidak ada key di kode UI.

## 6. Data

### 6.1 Sumber per pasar

| Pasar | Sumber awal | Batas/risiko |
|---|---|---|
| Saham AS, XAUUSD | Twelve Data gratis (800 panggilan/hari, 8/menit, 5.000 titik/permintaan, data tertunda); cadangan Alpha Vantage (25/hari) | Kuota kecil, wajib cache dan batch terjadwal |
| Crypto | API publik bursa + CoinGecko gratis | Sebagian bursa memblokir IP server AS, uji dari runner Actions |
| Saham Indonesia | Yahoo (kode .JK), tidak resmi | Bisa putus kapan saja, ketentuan penggunaan, mulai dengan data harian |

### 6.2 Anggaran panggilan harian (contoh)
- Harian: ~45 simbol AS dan XAUUSD ≈ 45 panggilan.
- Candle 1 jam: XAUUSD + ~10 simbol AS × ~7 pembaruan/hari ≈ 77 panggilan.
- Total ≈ 120-150 dari 800 per hari. Sisanya cadangan untuk retry dan backfill.

### 6.3 Aturan kualitas data (wajib)
- Gunakan hanya **candle yang sudah tutup** (anti-lookahead).
- Harga disesuaikan split/dividen untuk saham. Zona waktu dan jam pasar dinormalkan.
- Validasi: celah data, duplikat, lonjakan tidak wajar. Data gagal validasi tidak dipakai, UI menampilkan status "data tertunda".
- Bias penyintas: universe saham dibekukan per tanggal, dan perubahan dicatat.
- Hormati ketentuan penyedia data: tampilkan hasil turunan, jangan mendistribusikan ulang data mentah.

## 7. Metodologi analisa dan prediksi

### 7.1 Target prediksi
- **Arah:** P(return > 0) pada horizon H.
- **Rentang:** kuantil 10/50/90 return pada horizon H.
- **Barrier:** peluang menyentuh target sebelum stop (berbasis ATR) dalam H.
- Tier C: distribusi skenario bersyarat rezim (volatilitas tinggi/rendah, tren naik/turun/sideways).

### 7.2 Kandidat fitur per pasar (30-40 per pasar)

| Kelompok | Contoh |
|---|---|
| Tren | EMA ribbon, supertrend, ADX, posisi vs MA 50/200 |
| Momentum | MACD, RSI, divergensi RSI, rate of change |
| Volatilitas | ATR, Bollinger width, realized volatility, regime flag |
| Volume (jika tersedia) | VWAP, volume relatif, volume profile |
| Derivatif crypto | Funding rate, open interest, CVD |
| Lintas aset | Saham AS: VIX, imbal hasil, dolar. XAUUSD: dolar, imbal hasil riil. IHSG: USDIDR, harga komoditas. Crypto: dominasi BTC |

Ketersediaan tiap fitur di sumber gratis diverifikasi di Fase 1. Fitur yang tidak punya data andal dibuang.

### 7.3 Pemilihan "10 indikator terbaik" per pasar
Bukan daftar statis yang dipilih dari akurasi masa lalu (rawan overfitting). Prosesnya:
1. Evaluasi tiap kandidat dengan **purged walk-forward CV** (dengan embargo) per pasar dan horizon.
2. Ukur kegunaan: information coefficient, hit rate dengan interval kepercayaan, kontribusi ke Brier skill.
3. **Koreksi uji berganda** (uji permutasi atau deflated metrics) untuk mengurangi kebetulan beruntung.
4. Pilih 10 yang **stabil di banyak periode dan rezim**, bukan yang tertinggi di satu periode.
5. Daftar dikunci dan ditinjau **per kuartal**. Perubahan dicatat dengan versi.

### 7.4 Model berlapis
1. **Skor konfluensi** transparan (bobot indikator, -100 s/d +100), untuk penjelasan di UI.
2. **Model per pasar × horizon:** regresi logistik (arah) dan LightGBM (arah dan kuantil) di CPU.
3. **Ensemble** sederhana dengan bobot adaptif dari performa terbaru.
4. **Kalibrasi** (isotonic atau Platt) agar "peluang 60%" berarti sekitar 60% di data uji.
5. **Interval prediksi** dengan conformal prediction untuk rentang yang cakupannya terukur.
6. **Abstain:** jika keyakinan atau stabilitas rendah, keluaran "Tidak ada sinyal".

Deep learning tidak dipakai di v1: data harga sedikit dan berisik sehingga mudah overfit.

### 7.5 Pembanding (baseline) wajib
Tebakan acak terkalibrasi frekuensi dasar, buy-and-hold, momentum sederhana, dan random walk untuk rentang.

### 7.6 Gerbang rilis model
Sebuah model (pasar × horizon) tampil sebagai sinyal hanya jika di data uji out-of-sample:
- Brier skill score > 0 terhadap baseline, dengan interval kepercayaan tidak mencakup nol.
- Kurva reliabilitas dan ECE dalam batas yang ditetapkan.
- Cakupan interval mendekati target (mis. 80% untuk interval 80%).
- Tetap unggul setelah biaya transaksi pada strategi turunan, jika ditampilkan.

Jika gagal, UI menandai "Eksperimental, tanpa keunggulan terbukti".

### 7.7 Track record live
- Setiap prediksi dicatat tak berubah (waktu, versi model, input, probabilitas, rentang).
- Otomatis dinilai setelah horizon lewat. Metrik live ditampilkan publik: kalibrasi, Brier, hit rate dengan interval kepercayaan, dan jumlah sampel.
- **Drift monitoring:** peringatan jika kalibrasi live menyimpang. Retraining terjadwal (mis. bulanan untuk Tier A/B, kuartalan untuk Tier C).

## 8. Kebutuhan fungsional

| ID | Kebutuhan | Prioritas |
|---|---|---|
| FR-1 | Halaman **Analisa**: pilih pasar, simbol, timeframe; tampilkan chart, skor konfluensi, panel indikator (bull/bear/netral + bobot + penjelasan) | P0 |
| FR-2 | Tampilkan peluang naik, rentang 10/50/90, stop loss dan target ATR, serta tingkat keyakinan per horizon | P0 |
| FR-3 | Status data (waktu pembaruan, tertunda/ok) dan label "Eksperimental/Tidak ada sinyal" | P0 |
| FR-4 | Halaman **Track Record**: kalibrasi, Brier, hit rate dengan CI, jumlah sampel per pasar dan horizon | P0 |
| FR-5 | Halaman **Screener**: peringkat simbol berdasarkan skor dan keyakinan, filter pasar | P1 |
| FR-6 | Halaman **Backtest**: hasil walk-forward, biaya, pembanding | P1 |
| FR-7 | Penjelasan metodologi, daftar 10 indikator per pasar (dengan versi), dan disclaimer | P0 |
| FR-8 | Harga live crypto lewat stream publik di browser | P2 |
| FR-9 | Ekspor hasil (CSV/JSON) tanpa data mentah penyedia | P2 |

## 9. Kebutuhan non-fungsional
- **Kinerja:** halaman interaktif < 2 dtk di jaringan menengah. Data dari cache Worker, TTL sesuai timeframe.
- **Keandalan:** job terjadwal gagal ditandai dan UI menampilkan data terakhir yang valid. Target job sukses ≥ 95%.
- **Keamanan:** secrets terpisah, tanpa key di klien, CORS dikunci ke domain sendiri.
- **Biaya:** Rp0 dan tanpa kartu. Setiap komponen punya alarm saat mendekati 80% kuota.
- **Keterlacakan:** versi model, versi daftar indikator, dan versi data tercatat pada setiap prediksi.

## 10. Model data (ringkas)

**D1 (hasil terbaru)**
- `latest_forecast(market, symbol, horizon, p_up, q10, q50, q90, confidence, status, model_version, asof)`
- `latest_indicators(market, symbol, timeframe, indicator, signal, weight, value, asof)`
- `meta(key, value)` untuk status pembaruan.

**Neon (log dan evaluasi)**
- `predictions(id, market, symbol, horizon, issued_at, due_at, p_up, q10, q50, q90, model_version, features_hash)`
- `outcomes(prediction_id, realized_return, direction_hit, interval_hit, scored_at)`
- `model_runs(version, market, horizon, metrics_json, passed_gate, created_at)`

Contoh keluaran JSON per simbol:

```json
{"market":"crypto","symbol":"BTCUSDT","asof":"2026-10-04T08:00:00Z",
 "horizons":{"4h":{"p_up":0.57,"q10":-0.021,"q50":0.002,"q90":0.024,
 "confidence":"rendah","status":"ok","model":"crypto-4h-v3"}}}
```

## 11. Jadwal pipeline

| Job | Frekuensi | Isi |
|---|---|---|
| Crypto 1 jam | Tiap jam | Ambil data, fitur, inferensi, tulis D1 dan Neon |
| XAUUSD/Saham AS 1 jam | Tiap jam saat pasar buka | Idem |
| Harian semua pasar | Setelah pasar tutup | Fitur harian, Tier B dan C, penilaian outcome |
| Evaluasi dan drift | Harian | Hitung metrik live, peringatan |
| Retraining | Bulanan / kuartalan | Walk-forward, gerbang rilis, versi baru |

Catatan: cron GitHub Actions tidak dijamin tepat waktu. UI selalu menampilkan `asof`.

## 12. Roadmap

| Fase | Isi | Kriteria selesai |
|---|---|---|
| 0. Fondasi | Repo, struktur, skema D1/Neon, pipeline data crypto | Data crypto valid tersimpan otomatis |
| 1. Evaluasi dahulu | Kerangka walk-forward, pembanding, kalibrasi, log prediksi, halaman Track Record | Model awal (skor) dinilai dengan metrik; gerbang rilis berfungsi |
| 2. Crypto penuh | Fitur derivatif, seleksi 10 indikator, LightGBM, rentang | Minimal satu horizon lulus gerbang atau diberi label eksperimental |
| 3. XAUUSD dan saham AS | Adaptor data, fitur lintas aset, seleksi indikator | Pipeline stabil dalam kuota |
| 4. Saham Indonesia | Validasi sumber data, universe, seleksi | Sumber stabil dan kualitas data lulus |
| 5. Tier C dan penyempurnaan | Skenario jangka panjang, drift, peninjauan kuartalan | Dashboard kesehatan model |

## 13. Metrik keberhasilan

| Metrik | Target kerja (bukan jaminan) |
|---|---|
| Brier skill score vs baseline (out-of-sample) | > 0 dengan CI tidak mencakup nol, per model yang tampil sebagai sinyal |
| ECE kalibrasi | Rendah dan stabil di track record live |
| Cakupan interval | Mendekati nominal (mis. 80% ± 5 poin) |
| Keberhasilan job terjadwal | ≥ 95% |
| Pemakaian kuota | < 80% pada semua layanan |
| Jumlah model berlabel "Eksperimental" | Dilaporkan terbuka. Jujur lebih penting dari jumlah sinyal |

Ekspektasi realistis: untuk arah harga jangka pendek, keunggulan yang bertahan di data baru umumnya kecil. Nilai produk ada pada kalibrasi, transparansi, dan manajemen risiko.

## 14. Risiko, asumsi, dan hal yang harus diverifikasi

| Risiko | Mitigasi |
|---|---|
| Overfitting dan seleksi indikator karena kebetulan | Purged walk-forward, koreksi uji berganda, kuncian kuartalan, gerbang rilis |
| Kuota/data gratis berubah atau tertunda | Cache, cadangan penyedia, status data di UI, alarm kuota |
| Sumber saham Indonesia tidak resmi | Mulai belakangan, simpan salinan, siapkan penyedia alternatif |
| Batas layanan gratis diubah tanpa pemberitahuan | Arsitektur modular, ekspor berkala, rencana pindah |
| Ketentuan penyedia data dan hosting | Tampilkan data turunan saja. Baca ketentuan sebelum monetisasi (GitHub Pages melarang SaaS komersial) |
| Pengguna menganggap sebagai nasihat/jaminan | Disclaimer jelas, label keyakinan, track record apa adanya |

**Harus diverifikasi sebelum membangun:**
1. Pendaftaran Cloudflare (Pages, Workers, D1) benar-benar tanpa kartu.
2. Batas resmi D1, Workers, Neon, dan jatah GitHub Actions saat ini.
3. Syarat penggunaan Twelve Data/Alpha Vantage untuk menampilkan data turunan.
4. Ketersediaan candle 1 jam XAUUSD dan fitur derivatif crypto dari IP runner.
5. Sumber data saham Indonesia yang stabil.
6. Peraturan setempat bila produk akan dipublikasikan atau dikomersialkan.

## 15. Langkah berikutnya
1. Buat repo dan skema D1/Neon (Fase 0).
2. Bangun pipeline data crypto dan kerangka evaluasi (Fase 1) **sebelum** menambah pasar atau horizon.
3. Hubungkan UI Static Space yang ada ke Worker/D1 dan tambahkan halaman Track Record.
