# ROADMAP — Status & Kriteria Selesai

> Diperbarui: 2026-10-08. Sumber: status pemilik + PRD.
> Aturan: status "selesai" hanya boleh dicantumkan dengan bukti
> (perintah yang dijalankan + output), sesuai AGENTS.md #2.

## Posisi

| Tahap | Status | Yang kurang | Bukti | Tanggal |
|---|---|---|---|---|
| Fase 0: pipeline crypto | **Selesai** | - | Tabel `ingest_runs` 48 jam: 10/10 run ok = 100% >= 95%; GitHub Actions 10 run hijau, semua pemicu "Scheduled"; jumlah GitHub = jumlah DB. Deviasi: cadence aktual 5-8 jam (throttle GitHub Actions, bukan bug) | 2026-10-08 |
| Fase 1 / tugas 1.7 | Selesai | - | pytest 181 passed; ruff bersih; CI hijau run #20 (commit 091a827) | 2026-10-08 |
| Fase 1 / tugas 1.8 | Selesai | Keputusan cabang ditulis di DECISIONS.md | `python -m analyzer.evaluate --write-db`; laporan `docs/reports/eval-2026-10-08.md`; 16 kandidat (8 seri × confluence/momentum) semua status **eksperimental**; baris tercatat di `model_runs` | 2026-10-08 |
| Fase 1 / tugas 1.3 | 3 indikator aktif | MACD, Bollinger, RSI, VWAP + tes kausalitas | | |
| Fase 1 / tugas 1.9 | Rusak, workflow mati | Tulis ulang forecast + kalibrator + publish | | |
| Fase 1 / tugas 1.10 | Worker parsial, UI mockup | Endpoint nyata, Track Record, label Eksperimental | | |
| Fase 2–5 | Belum | Lihat PRD | | |

## Hasil evaluasi resmi 1.8 (ringkas)

- G1 (sampel OOS ≥ 500): lolos di semua 16 kandidat (720 bar OOS untuk 1d; 7200 untuk 1h).
- G2 (CI bawah BSS > 0): **gagal di semua 16** — BSS berkisar −0.0145 s/d +0.0053,
  CI bawah selalu negatif. Belum ada edge terukur di atas base rate
  dengan fitur `confluence-3ind-v1`.
- G4 (ECE ≤ 0.05): gagal terutama di horizon panjang (24h:0.059–0.061; 7d: 0.081–0.126).
  Horizon 4h paling sehat (ECE 0.021–0.029, cakupan 0.80).
- G3, G5: bercampur lolos/gagal. G6 (holdout): tidak tercapai — hanya dijalankan
  untuk kandidat yang lolos G1–G5.
- Rentang volatilitas memberi perbaikan pinball kecil di kebanyakan seri —
  bagian pipeline yang paling berfungsi.
- Status "eksperimental" adalah hasil yang sah (SPEC-FASE-1 Bagian 5.6).

## Titik keputusan (jangan dilompati)
Hasil tugas 1.8 menentukan: (a) lanjut Fase 2 perbaiki fitur/model,
atau (b) reposisi sebagai alat analisa/screener edukatif.
JANGAN perluas ke pasar lain sebelum titik ini jelas.

**Status: [KEPUTUSAN: (a) / (b) — dicatat di DECISIONS.md, tanggal, alasan]**

## Urutan kerja terkunci
1. ~~Bukti 48 jam Fase 0 (satu query) → catat di KONTEKS.md~~ ✓ selesai 2026-10-08 (10/10 ok = 100%)
2. ~~Pasang tugas-1.7, uji, commit, CI hijau~~ ✓ selesai 2026-10-08
3. ~~Evaluasi nyata (1.8) → DECISIONS.md~~ ✓ evaluasi resmi selesai; keputusan cabang menunggu
4. Pilih 1.3 atau 1.9 berdasarkan hasil
