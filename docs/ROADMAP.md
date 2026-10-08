# ROADMAP — Status & Kriteria Selesai

> Diperbarui: [tanggal]. Sumber: status pemilik + PRD.
> Aturan: status "selesai" hanya boleh dicantumkan dengan bukti
> (perintah yang dijalankan + output), sesuai AGENTS.md #2.

## Posisi

| Tahap | Status | Yang kurang | Bukti | Tanggal |
|---|---|---|---|---|
| Fase 0: pipeline crypto | Hampir tutup | Bukti 48 jam: ≥95% ingest_runs ok | [query + output] | |
| Fase 1 / tugas 1.7 | Selesai | - | pytest 181 passed; ruff bersih; CI hijau run #20 (commit 091a827) | 2026-10-08 |
| Fase 1 / tugas 1.8 | Belum | Evaluasi 8 seri + catat di DECISIONS.md | | |
| Fase 1 / tugas 1.3 | 3 indikator aktif | MACD, Bollinger, RSI, VWAP + tes kausalitas | | |
| Fase 1 / tugas 1.9 | Rusak, workflow mati | Tulis ulang forecast + kalibrator + publish | | |
| Fase 1 / tugas 1.10 | Worker parsial, UI mockup | Endpoint nyata, Track Record, label Eksperimental | | |
| Fase 2–5 | Belum | Lihat PRD | | |

## Titik keputusan (jangan dilompati)
Hasil tugas 1.8 menentukan: (a) lanjut Fase 2 perbaiki fitur/model,
atau (b) reposisi sebagai alat analisa/screener edukatif.
JANGAN perluas ke pasar lain sebelum titik ini jelas.

## Urutan kerja terkunci
1. Bukti 48 jam Fase 0 (satu query) → catat di KONTEKS.md
2. Pasang tugas-1.7, uji, commit, CI hijau
3. Evaluasi nyata (1.8) → DECISIONS.md
4. Pilih 1.3 atau 1.9 berdasarkan hasil
