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
- Folder legacy/ berisi kode lama: jangan diubah atau dihapus, dan kecualikan dari ruff, pytest, dan CI.

ATURAN KELUARAN
- Tulis setiap file utuh dalam blok kode terpisah, path file sebagai judul. Jangan ulang file yang tidak berubah.
- Tanpa penjelasan panjang: ringkasan maksimal 5 baris di akhir.
- Sertakan tes (pytest). Jangan klaim kode sudah dites.
- Jika informasi kurang, ajukan maksimal 3 pertanyaan SEBELUM menulis kode. Jangan mengarang detail API.
- Di akhir, tulis daftar asumsi yang kamu buat.

STATUS
Selesai: kode lama diarsipkan ke legacy/ (tag v0-legacy); workflow Keep Alive dihapus; dokumen proyek (PRD, SPEC-FASE-0, AGENTS.md) ditambahkan.
Keputusan: pipeline baru di pipeline/, skema di db/, UI baru nanti di web/. Folder frontend/ dan js/ lama dibiarkan di tempatnya (belum dipindah, menunggu cek Cloudflare Pages).
Struktur repo: pipeline/src/analyzer/{sources,store,jobs}, db/{neon,d1}, legacy/ (kode lama), docs/, .github/workflows
