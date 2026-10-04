# AGENTS.md — Aturan Kerja untuk Agen AI

## Tentang proyek
Market Analyzer: aplikasi analisa probabilistik untuk saham AS, saham Indonesia, XAUUSD, dan crypto. Seluruh infrastruktur **gratis dan tanpa kartu kredit**. Baca **`docs/PRD.md`** dan spesifikasi fase aktif (**`docs/SPEC-FASE-0.md`**) sebelum mulai bekerja. Jika keduanya bertentangan atau tidak jelas, **tanya pemilik** dan jangan menebak.

## Cara kerja
1. Kerjakan **satu tugas** dari daftar tugas pada spesifikasi, lalu **berhenti** dan beri ringkasan: apa yang diubah, cara mengujinya, dan hal yang belum selesai.
2. Jangan mengerjakan tugas atau fase lain tanpa diminta.
3. Setiap modul baru wajib punya tes. Jalankan tes dan linter sebelum menyatakan selesai.
4. Jika harus menyimpang dari spesifikasi, jelaskan alasannya dan catat di `docs/DECISIONS.md`.
5. Jangan mengarang hasil. Jika sebuah perintah tidak bisa dijalankan atau sebuah fakta tidak bisa diverifikasi, katakan terus terang.

## Perintah
```bash
cd pipeline
pip install -e ".[dev]"      # pasang dependensi
ruff check . && ruff format --check .
pytest -q
python -m analyzer.jobs.crypto_hourly   # jalankan job manual (butuh env)
python ../db/migrate.py                 # pasang skema
```

## Gaya kode
- Python 3.12, type hints di semua fungsi publik, `ruff` untuk lint dan format.
- Identifier dan nama file dalam bahasa Inggris. Dokumentasi, komentar, dan pesan ke pengguna dalam **bahasa Indonesia**.
- Fungsi kecil, tanpa efek samping tersembunyi. Pisahkan I/O (jaringan, database) dari logika murni agar mudah dites.
- Semua waktu **UTC**. Jangan memakai waktu lokal.

## Aturan keras (jangan dilanggar)
- **Tanpa kartu kredit:** jangan menambah atau menyarankan layanan yang butuh kartu atau metode pembayaran (termasuk Cloudflare R2). Jika sebuah solusi butuh itu, cari alternatif gratis tanpa kartu atau tanya pemilik.
- **Tanpa secret di repo:** API key, token, dan string koneksi hanya lewat GitHub Secrets atau secret Worker. Jangan mencetaknya ke log. Sediakan `.env.example` berisi nama variabel saja.
- **Tanpa API key di kode UI.** Semua akses data berkunci lewat job terjadwal atau Worker.
- **Anti-lookahead:** hanya candle yang sudah tutup yang boleh dipakai untuk fitur, model, atau tampilan. Tulis tes untuk ini.
- **Idempoten:** job harus aman dijalankan ulang. Gunakan `ON CONFLICT DO NOTHING` atau upsert.
- **Hormati kuota gratis:** setiap sumber data memakai pembatas laju dan penghitung panggilan. Jangan menulis loop tanpa batas atau polling berlebihan. Cache respons.
- **Data buruk dicatat, bukan dibuang diam-diam.** Masalah kualitas masuk `data_quality_log`.
- **Jangan menambah dependensi** tanpa alasan jelas. Utamakan pustaka standar dan yang sudah ada. Sebutkan dependensi baru di ringkasan.
- **Jangan mengubah `docs/PRD.md`** tanpa persetujuan pemilik. Usulkan perubahan di ringkasan.

## Aturan khusus produk
- Keluaran model berupa **probabilitas dan rentang**, bukan janji harga. Jangan menulis teks atau UI yang menjanjikan akurasi atau hasil.
- Model hanya tampil sebagai sinyal setelah lulus **gerbang rilis** (PRD Bagian 7.6). Jika belum lulus, tampilkan label "Eksperimental".
- Jangan memilih indikator "terbaik" dari akurasi satu periode. Gunakan prosedur seleksi di PRD Bagian 7.3.
- Sertakan disclaimer bahwa aplikasi ini bukan nasihat keuangan pada setiap halaman analisa.

## Kriteria selesai untuk sebuah tugas
- Tes baru ditulis dan seluruh tes lulus. Linter bersih.
- Kriteria "Selesai bila" pada tugas di spesifikasi terpenuhi dan bisa diperagakan.
- Tidak ada secret, file sementara, atau kode debug yang tertinggal.
- Ringkasan akhir ditulis: perubahan, cara uji, keputusan, dan risiko atau pertanyaan terbuka.
