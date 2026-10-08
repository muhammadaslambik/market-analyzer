# ROADMAP — Status & Kriteria Selesai

> Diperbarui: 2026-10-08. Sumber: status pemilik + PRD + DECISIONS.md.
> Aturan: status "selesai" hanya boleh dicantumkan dengan bukti
> (perintah yang dijalankan + output), sesuai AGENTS.md #2.

## Posisi

| Tahap | Status | Yang kurang | Bukti | Tanggal |
|---|---|---|---|---|
| Fase 0: pipeline crypto | **Selesai** | - | Tabel `ingest_runs` 48 jam: 10/10 run ok = 100% >= 95%; GitHub Actions 10 run hijau, semua pemicu "Scheduled"; jumlah GitHub = jumlah DB. Deviasi: cadence aktual 5–8 jam (throttle GitHub Actions, bukan bug) | 2026-10-08 |
| Fase 1 / tugas 1.7 | **Selesai** | - | pytest 181 passed; ruff bersih; CI hijau run #20 (commit 091a827) | 2026-10-08 |
| Fase 1 / tugas 1.8 | **Selesai** (evaluasi + keputusan cabang) | - | `python -m analyzer.evaluate --write-db`; laporan `docs/reports/eval-2026-10-08.md`; 16 kandidat semua **eksperimental**; baris tercatat di `model_runs`. Keputusan cabang **(c)** dicatat di DECISIONS.md | 2026-10-08 |
| Fase 1 / tugas 1.3 | 3 indikator aktif (EMA/SMA/ATR) | MACD, Bollinger, RSI, VWAP + tes kausalitas tiap indikator | - | - |
| Fase 1 / tugas 1.9 | Rusak, workflow mati | Tulis ulang forecast + kalibrator + publish; lalu evaluasi ulang resmi (`--write-db`) hanya setelah fitur 1.3 disetujui | - | - |
| Fase 1 / tugas 1.10 | Worker parsial, UI mockup | Endpoint nyata, Track Record, label **Eksperimental** wajib tampil | - | - |
| Fase 2 (fitur funding/OI) | Belum | Probe endpoint futures dari runner AS dulu (lihat DECISIONS 0.3) | - | - |
| Lapisan 2: 12 mesin | Belum | Dimulai setelah crypto-swing lolos G1–G6 (lihat "Urutan kerja terkunci") | - | - |

## Hasil evaluasi resmi 1.8 (ringkas)

- G1 (sampel OOS ≥ 500): lolos di semua 16 kandidat (720 bar OOS untuk 1d; 7200 untuk 1h).
- G2 (CI bawah BSS > 0): **gagal di semua 16** — BSS −0.0145 s/d +0.0053,
  CI bawah selalu negatif. Belum ada edge terukur di atas base rate
  dengan fitur `confluence-3ind-v1`.
- G4 (ECE ≤ 0.05): gagal terutama di horizon panjang (24h: 0.059–0.061; 7d: 0.081–0.126).
  Horizon 4h paling sehat (ECE 0.021–0.029, cakupan 0.798–0.800).
- G3: gagal di 6 dari 8 seri. G5 (cakupan 0.75–0.85): lolos semua.
  G6 (holdout): tidak tercapai — hanya dijalankan untuk kandidat yang lolos G1–G5.
- Rentang volatilitas memberi perbaikan pinball kecil di kebanyakan seri —
  bagian pipeline yang paling berfungsi.
- Status "eksperimental" adalah hasil yang sah (SPEC-FASE-1 Bagian 5.6).

## Titik keputusan (jangan dilompati)
Hasil tugas 1.8 menentukan: (a) lanjut Fase 2 perbaiki fitur/model,
(b) reposisi sebagai alat analisa/screener edukatif,
atau (c) framing lain dari pemilik.
JANGAN perluas ke pasar lain sebelum titik ini jelas.

**Status: KEPUTUSAN (c) — alat analisa berlapis (2026-10-08).**
Lapisan 1 aktif sekarang (semua output berlabel **eksperimental**); lapisan 2 =
12 mesin (4 pasar × 3 gaya) yang dipromosikan per-mesin hanya setelah lolos
G1–G6 pada pasarnya. Fase 2 tetap jalan sebagai jalur menuju lapisan 2.
Rincian dan alasan: DECISIONS.md, entri "Keputusan pemilik: framing (c)".

## Urutan kerja terkunci (satu per satu, JANGAN paralel)
1. ~~Bukti 48 jam Fase 0 (satu query) → catat di KONTEKS.md~~ ✓ selesai 2026-10-08 (10/10 ok = 100%)
2. ~~Pasang tugas-1.7, uji, commit, CI hijau~~ ✓ selesai 2026-10-08
3. ~~Evaluasi nyata (1.8) + keputusan cabang → DECISIONS.md~~ ✓ selesai 2026-10-08, keputusan (c)
4. Tugas 1.3: indikator tambahan (MACD, Bollinger, RSI, VWAP) + tes kausalitas → sebelum 1.9, karena fitur baru masuk evaluasi berikutnya
5. Tugas 1.9: tulis ulang forecast + kalibrator + publish
6. Tugas 1.10: endpoint nyata, Track Record, label Eksperimental
7. Evaluasi ulang resmi (`--write-db`) dengan fitur 1.3 → cek gate per mesin crypto-swing
8. Jika lolos G1–G6: promosikan crypto-swing ke "alat keputusan"; jika tidak: iterasi fitur (Fase 2)
9. Ekspansi lapisan 2 (crypto-scalp → crypto-invest → XAUUSD-swing → saham AS → saham ID),
   masing-masing butuh fondasi datanya sendiri (candle menit, data fundamental,
   sumber XAUUSD/saham) dan diblokir sampai crypto-swing lolos gate

## Aturan tetap lintas fase
- Semua output model berlabel **eksperimental** sampai mesin terkait lolos G1–G6.
- Run resmi `--write-db` hanya setelah perubahan yang disetujui di roadmap ini.
- Satu seri = satu sumber data (DECISIONS.md 0.3).
