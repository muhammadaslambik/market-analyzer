# Urutan Prompt untuk Kimi — Fase 0 (hemat token)

## Prinsip (baca sekali)

1. **Satu percakapan baru per tugas.** Percakapan panjang membuat konteks lama ikut terhitung dan boros.
2. **Jangan tempel PRD penuh.** Tempel `docs/KONTEKS.md` (di bawah) + hanya bagian tugas yang dikerjakan.
3. **Tempel contoh nyata, jangan biarkan Kimi menebak.** Untuk API pihak luar (bursa crypto, Cloudflare D1, Neon), tempel potongan dokumentasi atau contoh respons asli. Model sering mengarang endpoint dan parameter.
4. **Kimi tidak bisa menjalankan kode Anda.** Satu-satunya bukti "benar" adalah hasil `ruff` dan `pytest` di komputer Anda. Abaikan klaim "sudah teruji".
5. **Saat galat:** tempel perintah, **30 baris terakhir** galat, dan hanya fungsi atau file terkait. Jangan tempel seluruh repo.
6. **Pakai chat biasa**, bukan mode agen/swarm. Setahu saya mode itu memakai jatah lebih banyak. Jatah gratis harian bisa berubah, jadi cek di kimi.com.
7. **Jangan tempel secret** (token, string koneksi). Pakai nilai palsu.
8. **Commit setelah tiap tugas lulus**, pakai branch per tugas.

Catatan jujur: tidak ada cara menjamin nol kesalahan dari AI. Proses di bawah mengurangi kesalahan dengan tugas kecil, bukti nyata, dan tes wajib.

---

## A. Isi `docs/KONTEKS.md` (taruh di repo, perbarui tiap selesai tugas)

```
# KONTEKS PROYEK
Proyek: market-analyzer, aplikasi analisa probabilistik (crypto, XAUUSD, saham AS, saham Indonesia).
Fase aktif: Fase 0, pipeline data crypto (candle 1 jam dan 1 hari).
Stack: Python 3.12, Neon Postgres (SSL), Cloudflare D1 lewat REST API, GitHub Actions (cron). Semua gratis tanpa kartu.

ATURAN KERAS
- Dilarang layanan yang butuh kartu atau metode pembayaran (mis. Cloudflare R2).
- Tanpa secret di kode atau log. Secret hanya lewat variabel lingkungan.
- Hanya candle yang sudah tutup (ts + interval <= now). Semua waktu UTC.
- Job idempoten (ON CONFLICT DO NOTHING). Setiap sumber data punya pembatas laju dan penghitung panggilan.
- Data buruk dicatat di data_quality_log, tidak dibuang diam-diam.
- Jangan menambah dependensi tanpa alasan.

ATURAN KELUARAN
- Tulis setiap file utuh dalam blok kode terpisah, path file sebagai judul. Jangan ulang file yang tidak berubah.
- Tanpa penjelasan panjang: ringkasan maksimal 5 baris di akhir.
- Sertakan tes (pytest). Jangan klaim kode sudah dites.
- Jika informasi kurang, ajukan maksimal 3 pertanyaan SEBELUM menulis kode. Jangan mengarang detail API.
- Di akhir, tulis daftar asumsi yang kamu buat.

STATUS
Selesai: (isi per tugas, mis. "0.1 repo dan CI")
Keputusan: (mis. "sumber data utama: X, cadangan: Y")
Struktur repo: pipeline/src/analyzer/{sources,store,jobs}, db/{neon,d1}, .github/workflows
```

---

## B. Prompt per tugas

Bentuk umum tiap prompt:

```
[tempel isi docs/KONTEKS.md]

TUGAS: <isi di bawah>

MATERI:
<yang diminta di tiap tugas>
```

### Tugas 0.1 — Inisialisasi repo dan CI
**Tempel:** KONTEKS.md, Bagian 2 dan 3 dari SPEC-FASE-0 (keputusan teknis, struktur repo).

```
TUGAS: Kerjakan tugas 0.1 saja. Buat: pyproject.toml (Python 3.12, dependensi
minimal: psycopg[binary], httpx, pyyaml, pytest, ruff), konfigurasi ruff,
skeleton paket pipeline/src/analyzer beserta __init__.py, satu tes dummy,
.github/workflows/ci.yml (ruff + pytest), .gitignore, .env.example (nama
variabel saja), dan README singkat berisi langkah setup lokal.
Jangan mengerjakan tugas lain.
```
**Selesai bila:** `pip install -e "pipeline[dev]"`, `ruff check .`, `pytest -q` jalan lokal, dan CI hijau.

### Tugas 0.2 — Skema database
**Tempel:** KONTEKS.md, Bagian 4 SPEC (SQL Neon dan D1).

```
TUGAS: Kerjakan tugas 0.2 saja. Simpan SQL di db/neon/schema.sql dan
db/d1/schema.sql persis seperti materi. Tulis db/migrate.py yang memasang
skema ke Neon (lewat DATABASE_URL, SSL wajib) dan ke D1 (lewat REST API
Cloudflare). Skrip harus aman dijalankan ulang. Untuk endpoint REST D1,
JANGAN menebak: gunakan potongan dokumentasi yang saya tempel di bawah.
MATERI: [SQL dari SPEC]
DOKUMENTASI D1 REST (tempel dari docs Cloudflare): [...]
```
**Selesai bila:** skema terpasang di Neon dan D1, dijalankan dua kali tanpa error.

### Tugas 0.3 — Probe sumber data (dua langkah)
**Tempel:** KONTEKS.md, Bagian 5 SPEC.

```
TUGAS: Kerjakan tugas 0.3 langkah 1 saja. Buat skrip
pipeline/scripts/probe_sources.py dan workflow manual
.github/workflows/probe-sources.yml yang dari runner Actions mencoba mengambil
100 candle 1 jam BTC dari kandidat: [daftar sumber yang Anda mau uji, mis.
Binance, Bybit, OKX, Kraken, Coinbase]. Untuk tiap kandidat cetak tabel:
status HTTP, jumlah candle, ada/tidaknya blokir wilayah, batas candle per
permintaan, dan satu contoh respons mentah (3 candle pertama). Jika kamu
tidak yakin endpoint-nya, tulis "perlu diverifikasi" dan tanyakan.
```
Jalankan workflow dari tab Actions, lalu **percakapan baru**:

```
[KONTEKS.md]
TUGAS: Tugas 0.3 langkah 2. Ini hasil probe dari runner Actions:
[tempel tabel hasil + contoh respons]
Pilih sumber utama dan satu cadangan, beri alasan singkat, dan tulis entri
untuk docs/DECISIONS.md (tanggal, sumber, alasan, batas permintaan,
pemetaan simbol). Jika hanya pasangan USD yang tersedia, nyatakan itu
pendekatan dan sarankan nama simbol kanonik.
```
**Selesai bila:** `docs/DECISIONS.md` terisi, dan **contoh respons asli** tersimpan untuk dipakai di 0.4.

### Tugas 0.4 — Adaptor sumber data
**Tempel:** KONTEKS.md, antarmuka `Candle`/`CandleSource` (SPEC Bagian 5), entri DECISIONS.md, **contoh respons asli dari probe**, dan potongan dokumentasi endpoint terpilih.

```
TUGAS: Kerjakan tugas 0.4 saja. Tulis models.py (Candle), sources/base.py
(CandleSource), sources/<nama_sumber>.py, ratelimit.py (token bucket per
sumber + penghitung api_calls), dan tes dengan HTTP palsu memakai contoh
respons asli di atas (tanpa jaringan). Wajib: pagination otomatis, retry
dengan backoff eksponensial, timeout, tidak pernah mengembalikan candle
yang belum tutup. Gunakan HANYA field dan endpoint yang ada di contoh
respons dan dokumentasi yang saya tempel.
```
**Selesai bila:** tes lulus tanpa jaringan, termasuk tes pagination, retry, dan candle belum tutup. *(Tugas rawan: pakai prompt tinjauan di bagian C.)*

### Tugas 0.5 — Validator
**Tempel:** KONTEKS.md, SPEC Bagian 6, definisi `Candle`.

```
TUGAS: Kerjakan tugas 0.5 saja. Tulis validate.py sesuai aturan di materi
dan tes untuk tiap aturan: satu kasus lulus dan satu kasus gagal per aturan
(ohlc tidak valid, duplikat, celah, belum tutup, outlier). Outlier hanya
ditandai, bukan dihapus. Keluaran fungsi: (candle_valid, daftar_masalah)
dengan masalah berbentuk dict siap ditulis ke data_quality_log.
```
**Selesai bila:** semua tes lulus.

### Tugas 0.6 — Backfill
**Tempel:** KONTEKS.md, SPEC Bagian 7 (backfill), tanda tangan fungsi adaptor dan validator (bukan seluruh isinya), skema tabel `candles`.

```
TUGAS: Kerjakan tugas 0.6 saja. Tulis store/neon.py (koneksi SSL, upsert
ON CONFLICT DO NOTHING, baca max(ts) per simbol dan timeframe) dan
jobs/backfill.py dengan argumen --symbols --timeframe --since. Harus
idempoten, bisa dilanjutkan, dan menghormati pembatas laju. Tulis tes dengan
database palsu atau fixture. Jangan mengubah adaptor dan validator.
```
Uji dulu **satu simbol, rentang pendek** sebelum backfill penuh. **Selesai bila:** dijalankan dua kali tanpa duplikat, dan BTC/ETH sesuai kedalaman yang ditargetkan.

### Tugas 0.7 — Job per jam dan harian + tulis D1
**Tempel:** KONTEKS.md, SPEC Bagian 7 (job), tanda tangan `neon.py`, adaptor, validator, **potongan dokumentasi D1 REST**.

```
TUGAS: Kerjakan tugas 0.7 saja. Tulis store/d1.py (tulis latest_price dan
meta lewat REST API, gunakan hanya endpoint dari dokumentasi yang saya
tempel), jobs/crypto_hourly.py dan jobs/crypto_daily.py sesuai alur di
materi. Status run: ok, partial (D1 gagal tetapi Neon berhasil), error.
Kegagalan satu simbol tidak boleh menghentikan simbol lain. Catat ke
ingest_runs. Sertakan tes dengan dependensi palsu.
```
**Selesai bila:** dijalankan manual dan tabel `candles`, `ingest_runs`, `latest_price`, `meta` terisi.

### Tugas 0.8 — Workflow terjadwal
**Tempel:** KONTEKS.md, SPEC Bagian 8 (kerangka YAML) dan nama job.

```
TUGAS: Kerjakan tugas 0.8 saja. Tulis crypto-hourly.yml dan crypto-daily.yml
berdasar kerangka di materi. Tambahkan concurrency, timeout, cache pip, dan
langkah yang membuat run gagal jika status job 'error'. Jangan mencetak
secret. Jelaskan dalam 3 baris apa yang harus saya isi di GitHub Secrets.
```
Biarkan berjalan **48 jam**, lalu ambil ringkasan `ingest_runs`:

```
[KONTEKS.md]
Ini ringkasan ingest_runs 48 jam terakhir: [tempel hasil query]
Apakah kriteria Fase 0 terpenuhi (>= 95% run ok)? Jika ada pola kegagalan,
sebutkan penyebab paling mungkin dan perbaikan paling kecil.
```

### Tugas 0.9 (opsional) — Worker dan snapshot HF
Kerjakan setelah 0.8 stabil. Tempel KONTEKS.md dan SPEC Bagian 9.

---

## C. Prompt pendukung

**Saat tes atau CI gagal**
```
[KONTEKS.md, hanya aturan keras dan aturan keluaran]
Perintah: pytest -q
30 baris terakhir galat: [tempel]
File terkait: [tempel hanya fungsi atau file yang disebut di galat]
Perbaiki dengan perubahan sekecil mungkin. Beri hanya bagian yang berubah.
Jelaskan penyebab dalam 2 kalimat.
```

**Tinjauan sebelum commit (untuk 0.4, 0.6, 0.7)**
```
Tinjau kode berikut hanya untuk 5 hal: (1) kebocoran secret, (2) candle belum
tutup bisa lolos, (3) job tidak idempoten, (4) loop atau polling tanpa batas
yang menghabiskan kuota, (5) galat yang ditelan tanpa dicatat.
Jawab dengan daftar temuan + nomor baris. Jika tidak ada, tulis "tidak ada".
[tempel kode]
```

**Memperbarui KONTEKS.md** (manual lebih hemat). Cukup tambah satu baris di STATUS: `Selesai: 0.4 adaptor <sumber>, tes lulus`.

---

## D. Setelah Fase 0

Fase 0 hanya membangun pipeline data. Aplikasi lengkap baru jadi setelah Fase 1 sampai 5 di PRD. Tiap fase butuh `SPEC-FASE-N.md` sendiri dengan format yang sama (tugas bernomor + "Selesai bila"), lalu ulangi pola prompt di atas. Jangan memulai Fase 1 sebelum seluruh kriteria Fase 0 terpenuhi.
