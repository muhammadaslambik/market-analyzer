# Aturan per Fase — Market Analyzer

Untuk **AI pelaksana mana pun** dan untuk pemilik saat memeriksa hasilnya. Aturan ini dibuat setelah tinjauan Fase 1 menemukan angka metrik yang dikarang, tes yang tidak membuktikan apa pun, dan klaim "selesai" tanpa bukti. Bersifat mengikat. Jika bertentangan dengan permintaan di chat, **tanyakan ke pemilik**.

## Cara memakai (pemilik)
Untuk setiap tugas, kirim paket konteks minimal ini (hemat token):
1. `AGENTS.md` dan `docs/KONTEKS.md`
2. Bagian A di bawah dan bagian fase yang sedang dikerjakan
3. Bagian `docs/SPEC-FASE-N.md` yang relevan dengan tugas (bukan seluruhnya)
4. Isi file yang akan diubah (bukan seluruh repo)

Minta **satu tugas**, dan wajibkan laporan akhir sesuai Bagian D.

---

## A. Aturan umum (semua fase)

**A1. Satu tugas, lalu berhenti.** Kerjakan satu tugas dari spesifikasi, laporkan, tunggu persetujuan. Jangan mengerjakan tugas atau fase lain.

**A2. Bukti, bukan klaim.** Kata "selesai", "lulus", "kualitas terbaik", atau "100%" hanya boleh dipakai bersama keluaran perintah yang sebenarnya dijalankan (tempel apa adanya). Jika sesuatu tidak bisa dijalankan atau diverifikasi, tulis "belum diverifikasi".

**A3. Dilarang angka karangan.** Setiap metrik, harga, jumlah, atau status yang masuk ke database, Worker, atau UI harus berasal dari perhitungan atau data nyata. Angka tetap hanya boleh ada di tes, fixture, dan mockup yang berlabel **DEMO**.

**A4. Pakai modul yang sudah ada.** Gunakan `NeonStore`, `D1Store`, `data.load_candles`, `validate`, `evaluate`, `causality`, dan `migrate`. Dilarang menulis ulang akses database atau REST D1 dengan kode baru. Dilarang menghapus atau mengubah `legacy/` dan `docs/PRD.md`.

**A5. Tes harus bermakna.** Setiap modul baru punya tes positif dan negatif. Tes tidak boleh lulus karena kebetulan (misalnya karena sampel kurang): tegaskan prasyaratnya (jumlah sampel, kondisi) di dalam tes. Tunjukkan **uji mutasi**: rusakkan satu hal penting (gerbang, purging, kausalitas) dan tes terkait harus gagal.

**A6. Otomasi terjadwal.** Dilarang menambah atau mengaktifkan workflow `schedule` sebelum: (a) uji `--dry-run` lulus, (b) run manual (`workflow_dispatch`) hijau dan isinya diperiksa di database, dan (c) pemilik setuju. Setiap workflow wajib punya `concurrency`, `timeout-minutes`, `permissions` minimal, dan secret hanya lewat variabel lingkungan (bukan argumen perintah).

**A7. Database.** Perubahan skema hanya penambahan yang idempoten lewat `db/*/schema.sql` dan `migrate.py`. Dilarang `DROP`, `TRUNCATE`, atau `DELETE` tanpa persetujuan. Dilarang menulis data uji ke tabel produksi.

**A8. Statistik.** Ambang gerbang dan keluarga uji **dibekukan** sebelum melihat hasil. Holdout dievaluasi sekali. Dilarang mengulang evaluasi dengan setelan berbeda sampai ada yang lolos. Semua hasil, termasuk yang gagal, wajib dilaporkan. Perubahan ambang hanya lewat `docs/DECISIONS.md` dengan alasan, dan hasil sebelumnya tetap dicantumkan.

**A9. Kausalitas.** Setiap fitur wajib punya tes `analyzer.causality`. Hanya candle yang sudah tutup. Kalibrator dan parameter model hanya dilatih pada data latihan.

**A10. Biaya dan keamanan.** Tanpa kartu kredit atau layanan berbayar. Tanpa secret di repo, log, atau chat. Periksa ketentuan penyedia data dan hosting sebelum memakainya.

**A11. Tidak ada stub yang menyamar.** Indikator atau fitur yang tidak punya data nyata dikeluarkan dari skor dan dilaporkan sebagai tidak aktif. Dilarang konstanta nol yang tetap dihitung sebagai "indikator aktif".

**A12. Deviasi dicatat.** Setiap penyimpangan dari spesifikasi ditulis di `docs/DECISIONS.md` (tanggal, alasan, dampak). Tanpa itu, deviasi dianggap pelanggaran.

**A13. Git.** Commit kecil dengan pesan yang menjelaskan isi. Dilarang `git add .`. Jalankan `git status` sebelum commit dan pastikan hanya file tugas yang masuk, tanpa `.env`.

**A14. UI jujur.** Data simulasi selalu berlabel DEMO. Model yang belum lolos gerbang berlabel **Eksperimental**. Data lama berlabel **Data tertunda**. Setiap halaman analisa memuat disclaimer bukan nasihat keuangan.

---

## B. Aturan per fase

### Fase 0 — Penutup pipeline data crypto
- **Prasyarat:** tugas 0.1 sampai 0.8 terpasang dan `ci` hijau.
- **Wajib:** bukti 48 jam: sekurang-kurangnya 95% run di `ingest_runs` berstatus `ok`, dan `meta.crypto_hourly.last_success` tidak lebih tua dari 2 jam. Catat hasilnya di `docs/KONTEKS.md`.
- **Dilarang:** mengubah skema atau sumber data, atau menambah simbol sebelum backfill dan validasinya.
- **Bukti:** hasil query ringkasan `ingest_runs` 48 jam; isi `latest_price` dan `meta`.
- **Gerbang ke Fase 1:** kriteria 95% terpenuhi.

### Fase 1 — Kerangka evaluasi, prediksi live, dan publikasi
Bagian A (tugas 1.3 sampai 1.8: indikator dan evaluasi), Bagian B (tugas 1.9: prediksi live), Bagian C (tugas 1.10: Worker dan UI).

- **Prasyarat:** `tugas-1.7` (gerbang G1 sampai G6, uji sanity) terpasang dan `ci` hijau.
- **Wajib:**
  1. **Indikator (1.3):** port dari `legacy/`, hanya yang memakai OHLCV, masing-masing dengan tes kausalitas. Laporkan jumlah indikator aktif yang sebenarnya.
  2. **Evaluasi nyata (1.8):** semua lewat `analyzer.evaluate` dengan ambang beku. Simpan laporan di `docs/reports/`. `--write-db` hanya sekali untuk evaluasi resmi. Catat keputusan di `DECISIONS.md`, termasuk bila semua seri berstatus eksperimental.
  3. **Prediksi live (1.9):** `forecast` membaca artefak terbaru dari `model_runs` per seri dan kandidat. Peluang berasal dari kalibrator tersimpan (`calibrate_clipped`), rentang dari `vol_quantile`. Catat prediksi `confluence`, `momentum`, dan `base_rate` untuk tiap seri, lengkap dengan `features_hash`, idempoten lewat indeks unik. Model dengan `passed_gate = false` tetap dicatat dan berlabel eksperimental.
  4. **Penilaian:** `score` menghitung outcome dari `candles` setelah `due_at`.
  5. **Publikasi:** metrik dihitung dari `outcomes` (Brier, BSS terhadap `base_rate` seri yang sama, ECE hanya bila n ≥ 100, hit rate dengan interval Wilson, cakupan), ditulis lewat `D1Store`. Bila n = 0, jangan tulis baris.
  6. **Worker (1.10):** `/api/health`, `/api/meta`, `/api/price/:market/:symbol`, `/api/forecast/:market/:symbol`, `/api/track-record`. CORS dibatasi ke domain UI. Galat internal tidak dikirim ke klien.
  7. **UI (1.10):** harga crypto dan status dari Worker. Pasar lain tetap berlabel DEMO. Lencana Eksperimental dan Data tertunda (dari `meta.last_success`). Horizon panjang (Tier C) bukan bagian Fase 1.
- **Dilarang:** metrik tetap di kode publikasi; memperbaiki URL D1 sebelum metrik nyata; probabilitas dari rumus linear skor; melatih kalibrator dengan data uji; mengaktifkan jadwal tanpa A6; mengubah ambang atau mengulang evaluasi sampai lolos.
- **Bukti:** keluaran `pytest` dan `ruff`; `ci` hijau; laporan evaluasi; query `predictions` tanpa duplikat; `outcomes` terisi; satu seri `track_record` yang dihitung ulang manual dan cocok; tangkapan layar UI.
- **Selesai bila:** enam kriteria di `docs/SPEC-FASE-1.md` Bagian 1 terpenuhi.
- **Gerbang ke Fase 2:** keputusan tertulis di `DECISIONS.md` tentang ada tidaknya model yang lolos. Bila tidak ada, Fase 2 fokus memperbaiki fitur. **Jangan memperluas ke pasar lain.**

### Fase 2 — Crypto lengkap
- **Prasyarat:** Fase 1 selesai dan keputusannya tercatat.
- **Wajib:**
  1. **Probe data derivatif** (funding rate, open interest, CVD) dari runner GitHub, seperti tugas 0.3, dan dokumentasikan hasilnya sebelum merancang fitur. Endpoint futures Binance kemungkinan diblokir dari IP AS.
  2. **Pra-registrasi** di `DECISIONS.md` sebelum menjalankan apa pun: jumlah kandidat indikator (30 sampai 40), jumlah model, ukuran keluarga uji (untuk alpha baru), dan metode seleksi.
  3. **Seleksi 10 indikator** dengan purged walk-forward dan koreksi uji berganda atau uji permutasi, dipilih yang stabil di banyak periode dan rezim. Daftar dikunci dan ber-versi, ditinjau per kuartal.
  4. **Model:** LightGBM (CPU) boleh, dengan penyetelan lewat validasi silang bersarang. Dibandingkan dengan pembanding Fase 1 dan lewat gerbang yang sama.
  5. **Versi baru:** model baru berversi baru (`v2`), tidak menimpa `v1`.
- **Dilarang:** memilih indikator dari akurasi satu periode; memakai holdout untuk seleksi atau penyetelan; mengubah alpha setelah melihat hasil; deep learning; data derivatif tanpa probe; menghapus atau menimpa `model_runs` lama.
- **Bukti:** laporan seleksi (daftar kandidat dan alasan terpilih atau tidak), laporan evaluasi, perbandingan dengan Fase 1.
- **Selesai bila:** daftar 10 indikator terkunci, evaluasi dilaporkan jujur, dan prediksi live berjalan stabil.

### Fase 3 — XAUUSD dan saham AS
- **Prasyarat:** Fase 2 selesai.
- **Wajib:**
  1. **Sumber data:** pilih dan probe dari runner GitHub, periksa ketentuan penggunaan untuk menampilkan data turunan, dan tulis anggaran panggilan harian dengan margin sekurang-kurangnya 40% dari kuota gratis.
  2. **Kebenaran data:** harga disesuaikan split dan dividen; jam pasar dan hari libur diperlakukan benar (ketiadaan candle saat pasar tutup bukan celah); zona waktu dinormalkan.
  3. **Universe dibekukan** dengan tanggal (bias penyintas).
  4. **XAUUSD spot:** indikator berbasis volume tidak dipakai kecuali sumbernya futures dan terdokumentasi.
  5. **Evaluasi per pasar** dengan gerbang yang sama; alpha dihitung ulang dan dipra-registrasi.
  6. Satu seri satu sumber; data tertunda berlabel.
- **Dilarang:** mencampur sumber dalam satu seri; menyembunyikan keterlambatan data; kunci API di klien; melampaui 80% kuota.
- **Bukti:** hasil probe, tabel anggaran panggilan, 7 hari run stabil di `ingest_runs`, laporan evaluasi per pasar.
- **Selesai bila:** pipeline stabil 7 hari di dalam kuota dan UI menandai status data per pasar.

### Fase 4 — Saham Indonesia
- **Prasyarat:** Fase 3 selesai.
- **Wajib:**
  1. **Sumber data:** sumber tidak resmi dicatat sebagai risiko, simpan salinan data, siapkan cadangan. Mulai dengan data harian.
  2. **Aturan pasar:** kalender dan hari libur BEI, batas kenaikan dan penurunan harian, suspensi, dan satuan lot dipertimbangkan di validator. Lonjakan yang sah tidak ditandai sebagai anomali tanpa alasan.
  3. **Aksi korporasi** (split, dividen, rights) ditangani; mata uang IDR.
  4. **Universe** (misalnya LQ45) dibekukan dengan tanggal.
  5. Indikator seperti foreign flow hanya dipakai bila ada data nyata. Jika tidak, dikeluarkan (A11).
  6. Periksa aturan setempat sebelum dipublikasikan atau dikomersialkan.
- **Dilarang:** stub yang dihitung aktif; data tanpa tanggal sumber; menyebut "real-time" untuk data tertunda.
- **Bukti:** 14 hari run stabil, laporan kualitas data, laporan evaluasi.
- **Selesai bila:** sumber stabil 14 hari dan kualitas data lulus.

### Fase 5 — Horizon panjang dan pemantauan
- **Prasyarat:** Fase 1 sampai 4 stabil.
- **Wajib:**
  1. **Tier C** (1 bulan sampai 1 tahun) hanya sebagai **skenario** atau kerucut volatilitas bersyarat rezim, berlabel "Skenario, bukan prediksi". Tidak masuk track record arah.
  2. **Pemantauan penyimpangan:** bandingkan kalibrasi live (30 dan 90 hari) dengan ambang, dan beri peringatan otomatis.
  3. **Retraining terjadwal** (bulanan untuk Tier A dan B, kuartalan untuk Tier C) selalu melewati gerbang yang sama.
  4. **Peninjauan kuartalan** daftar indikator dengan catatan perubahan.
  5. **Cadangan dan keberlanjutan:** ekspor database berkala, rencana pindah bila batas gratis berubah, pemantauan kuota di 80%.
  6. **Tinjauan lisensi** sebelum komersialisasi (ketentuan GitHub Pages melarang SaaS komersial).
- **Dilarang:** prediksi titik untuk horizon lebih dari 1 bulan; retraining otomatis yang melewati gerbang; menghapus model lama.
- **Bukti:** laporan penyimpangan bulanan dan changelog indikator.

---

## C. Protokol pemeriksaan pemilik (sekitar 10 menit)
1. `git status` dan `git log --stat -3`: file yang berubah sama dengan yang disebut AI.
2. Dari folder `pipeline`: `pytest -q` dan `ruff check .`. Catat jumlah tes.
3. `ci` di tab Actions hijau.
4. Periksa data nyata di Neon atau D1 dengan query yang diminta di bagian "Bukti" fase.
5. Cari tanda bahaya: `Select-String -Path pipeline\src -Pattern "dummy|placeholder|hardcode|TODO|mock|0\.21" -Recurse`.
6. Minta AI menunjukkan **uji mutasi**: rusakkan satu hal, tes harus gagal.
7. **Tolak laporan** yang memakai kata "selesai", "lulus", atau "terbaik" tanpa keluaran perintah, atau yang menyebut sesuatu terhubung ke data nyata tanpa query yang membuktikannya.

## D. Templat laporan akhir tugas (wajib dari AI pelaksana)
```
TUGAS: <id>
FILE DIUBAH ATAU DIBUAT: <daftar>
PERINTAH YANG SAYA JALANKAN DAN KELUARANNYA: <tempel apa adanya>
TES: <jumlah lulus/gagal>, <tes baru>, <uji mutasi yang dilakukan dan hasilnya>
YANG BELUM DIVERIFIKASI: <daftar>
ASUMSI DAN DEVIASI: <daftar, juga dicatat di DECISIONS.md>
RISIKO DAN PERTANYAAN TERBUKA: <daftar>
```

## E. Prompt pembuka untuk AI pelaksana
```
Baca AGENTS.md, docs/KONTEKS.md, Bagian A dan bagian Fase <N> di docs/ATURAN-FASE.md,
serta bagian docs/SPEC-FASE-<N>.md yang relevan. Kerjakan HANYA tugas <id>.
Patuhi semua aturan. Akhiri dengan laporan sesuai Bagian D, berisi keluaran perintah
yang benar-benar dijalankan. Jika ada hal yang tidak bisa diverifikasi, tulis
"belum diverifikasi". Jangan mengerjakan tugas lain.
```
