# AGENTS.md — Aturan Kerja untuk Agen AI

## Tentang proyek
Market Analyzer: aplikasi analisa probabilistik untuk crypto, XAUUSD, saham AS, dan saham Indonesia. Seluruh infrastruktur **gratis dan tanpa kartu kredit**. Baca `docs/PRD.md`, `docs/KONTEKS.md`, spesifikasi fase aktif (`docs/SPEC-FASE-N.md`), dan **`docs/ATURAN-FASE.md`** (Bagian A dan fase aktif) sebelum bekerja. Jika ada yang bertentangan atau tidak jelas, **tanya pemilik**.

## Cara kerja
1. Kerjakan **satu tugas** dari spesifikasi, lalu berhenti dan beri laporan sesuai templat di `docs/ATURAN-FASE.md` Bagian D.
2. **Bukti, bukan klaim.** Jangan menulis "selesai", "lulus", atau "kualitas terbaik" tanpa keluaran perintah yang benar-benar dijalankan. Jika tidak bisa diverifikasi, tulis "belum diverifikasi".
3. Setiap modul baru punya tes positif dan negatif. Tes tidak boleh lulus karena kebetulan, dan harus gagal bila kode penting dirusak (uji mutasi).
4. Deviasi dari spesifikasi dicatat di `docs/DECISIONS.md`.

## Perintah (dari folder `pipeline`, lingkungan `.venv` pipeline aktif)
```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest -q
python -m analyzer.evaluate --symbols BTCUSDT,ETHUSDT   # evaluasi (dry-run tanpa --write-db)
python ../db/migrate.py                                  # pasang skema
```

## Aturan keras
- **Tanpa kartu kredit** atau layanan berbayar (termasuk Cloudflare R2).
- **Tanpa secret** di kode, log, atau chat. Hanya lewat variabel lingkungan dan GitHub Secrets.
- **Dilarang angka karangan.** Metrik, harga, atau status di database, Worker, dan UI harus dari data atau perhitungan nyata. Data simulasi hanya di tes dan mockup berlabel DEMO.
- **Pakai modul yang sudah ada** (`NeonStore`, `D1Store`, `data`, `validate`, `evaluate`, `causality`, `migrate`). Dilarang menulis ulang akses database atau REST D1.
- **Kausalitas:** hanya candle yang sudah tutup; semua fitur lolos `analyzer.causality`; parameter model hanya dilatih pada data latihan.
- **Statistik:** ambang gerbang dibekukan, holdout dievaluasi sekali, dan semua hasil (termasuk yang gagal) dilaporkan. Dilarang mengulang evaluasi dengan setelan berbeda sampai lolos.
- **Workflow terjadwal** hanya boleh ditambah atau diaktifkan setelah dry-run lulus, run manual hijau dan terverifikasi, dan pemilik setuju. Wajib `concurrency`, `timeout-minutes`, `permissions` minimal.
- **Database:** perubahan skema hanya penambahan idempoten. Tanpa `DROP`, `TRUNCATE`, atau `DELETE` tanpa persetujuan.
- **Tanpa stub yang menyamar:** indikator tanpa data nyata dikeluarkan dari skor, bukan dihitung sebagai konstanta.
- Folder `legacy/` dan `docs/PRD.md` jangan diubah. Jangan menambah dependensi tanpa alasan, dan sebutkan dependensi baru di laporan.
- **Git:** jangan `git add .`; periksa `git status` agar `.env` tidak ikut.

## Aturan produk
- Keluaran model berupa **probabilitas dan rentang**, bukan janji harga.
- Model hanya tampil sebagai sinyal setelah lulus gerbang (G1 sampai G6). Selain itu berlabel **Eksperimental**.
- Data simulasi berlabel **DEMO**, data lama berlabel **Data tertunda**, dan setiap halaman analisa memuat disclaimer bahwa ini bukan nasihat keuangan.
