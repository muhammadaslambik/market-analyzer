# Catatan Keputusan

## 2026-10-05 — Sumber data crypto (tugas 0.3)

**Hasil probe dari runner GitHub Actions (IP mesin: US), candle 1 jam BTC:**

| Sumber | HTTP | Candle | Catatan |
|---|---|---|---|
| binance (api.binance.com) | 451 | 0 | Diblokir wilayah |
| binance-vision (data-api.binance.vision) | 200 | 1000 | OK, pasangan BTCUSDT |
| bybit | 403 | 0 | Ditolak, kemungkinan diblokir |
| okx | 200 | 300 | OK, pasangan BTC-USDT |
| kraken | 200 | 721 | OK, pasangan USD |
| coinbase | 200 | 350 | OK, pasangan USD |

**Keputusan**
- **Sumber utama:** `binance-vision` (`https://data-api.binance.vision`). Alasan: lolos dari IP AS, 1000 candle per permintaan (backfill 2 tahun data 1 jam ≈ 18 permintaan per simbol), dan memakai pasangan USDT yang sama dengan nama simbol di PRD.
- **Cadangan:** OKX (pasangan USDT). Dokumentasi pihak ketiga menyebut endpoint `history-candles` menyediakan riwayat penuh dengan maksimal 100 candle per permintaan. Adaptor cadangan belum dibuat dan perlu diverifikasi sebelum dipakai.
- **Tidak dipakai:** `binance` biasa (451), `bybit` (403). Kraken dan Coinbase memakai pasangan USD, bukan USDT, sehingga harganya tidak identik dengan seri utama.

**Aturan turunan**
- Satu seri (simbol + timeframe) memakai **satu sumber**. Jangan mencampur sumber dalam satu seri tanpa menandainya di kolom `source`.
- Hanya candle yang sudah tutup yang disimpan (candle terakhir yang masih berjalan dibuang).
- Nama simbol kanonik tetap gaya `BTCUSDT`.

**Belum diuji, perlu diverifikasi nanti**
- Data turunan (funding rate, open interest) untuk indikator crypto di Fase 2. Endpoint futures Binance (`fapi.binance.com`) kemungkinan juga diblokir dari IP AS. Uji dari runner sebelum merancang indikator itu.
- Batas laju resmi `binance-vision`. Adaptor memakai batas konservatif (2 permintaan per detik), bukan angka resmi.
- Status `data-api.binance.vision` bisa berubah sewaktu-waktu. Itu alasan adanya sumber cadangan.
## 2026-10-08 — Tugas 1.7 selesai

**Status:** SELESAI.

**Bukti**
- `python -m pytest` → 181 passed, 0 gagal.
- `python -m ruff check .` → All checks passed!; `ruff format --check .` → 57 files already formatted.
- CI hijau: run #20 (commit 091a827, kode 1.7 final + marker verifikasi, pytest + ruff
  dengan DATABASE_URL nyata) dan run #15 (kode identik sebelumnya).
- `git diff origin/main` → kosong sebelum push marker.

**Deviasi**
- Paket zip tugas-1.7 tidak ditemukan di disk; terkonfirmasi sudah terpasang dan
  di-push (f469601) sebelum sesi ini. Deviasi prosedural, tanpa dampak teknis.
- Uji mutasi dilakukan dalam paket 1.7 sebelumnya; belum ditunjukkan ulang di sesi ini
  (dapat diminta saat pemeriksaan C.6).

**Dampak:** prasyarat Fase 1 terpenuhi; lanjut ke tugas 1.8 (evaluasi nyata 8 seri).

## 2026-10-08 — Tugas 1.8: evaluasi resmi 8 seri + keputusan titik cabang

**Status:** SELESAI (evaluasi) + keputusan cabang: **(a) lanjut Fase 2**.

**Bukti**
- `python -m analyzer.evaluate` (dry-run) → 8 seri dievaluasi, laporan
  `docs/reports/eval-2026-10-08.md`, "Dry-run: model_runs tidak ditulis".
- `python -m analyzer.evaluate --write-db` (run resmi, **sekali**) → hasil identik
  dengan dry-run; "model_runs ditulis." Karena ambang gerbang beku (A8) dan seed
  bootstrap tetap, hasilnya deterministik dan tidak pernah dipakai memilih model.
- Laporan lengkap: `docs/reports/eval-2026-10-08.md` (tabel 16 kandidat + catatan
  jumlah baris, Brier base, pinball).

**Hasil ringkas (semua 16 kandidat = 8 seri × confluence/momentum)**
- Status semua: **eksperimental** — hasil yang sah (SPEC-FASE-1 Bagian 5.6), bukan kegagalan.
- G1 (n OOS ≥ 500): lolos semua (720–7200 bar OOS).
- G2 (CI bawah BSS > 0): **gagal semua** — BSS −0.0145 s/d +0.0053, CI bawah selalu negatif.
- G3 (confluence ≥ momentum): gagal di 6 dari 8 seri.
- G4 (ECE ≤ 0.05): gagal terutama horizon panjang (24h: 0.059–0.061; 7d: 0.081–0.126);
  horizon 4h paling sehat (ECE 0.021–0.029, cakupan 0.798–0.800).
- G5 (cakupan 0.75–0.85): lolos semua.
- G6 (holdout sekali): tidak tercapai — hanya dijalankan bila G1–G5 lolos.

**Interpretasi**
- Tidak ada edge terukur di atas base rate dengan fitur `confluence-3ind-v1`
  (3 indikator aktif). Ini temuan ilmiah yang sah, bukan bukti pipeline rusak:
  G1/G5 lolos semua, angka konsisten, sampel besar (7200 bar OOS untuk 1h).
- Rentang volatilitas memberi perbaikan pinball kecil di sebagian besar seri —
  bagian pipeline yang paling berfungsi.
- Kegagalan terkonsentrasi di G2/G3 = kualitas sinyal, yaitu persis target
  perbaikan Fase 2 (fitur funding/OI, indikator tambahan tugas 1.3).

**Keputusan cabang: (a) lanjut Fase 2, perbaiki fitur/model**
- Alasan: infrastruktur terbukti sehat (G1, G5 lolos semua; kalibrasi 4h hampir lolos);
  kegagalan ada di dimensi yang memang direncanakan untuk diperbaiki di Fase 2;
  reposisi (b) dini akan membuang infrastruktur yang baru terbukti berjalan.
- Panduan arah: utamakan horizon 4h (hasil paling sehat); prioritas sumber sinyal
  baru (funding rate, open interest) sesuai PRD. **Catatan dari keputusan 0.3:**
  endpoint futures Binance kemungkinan diblokir dari IP AS — uji dari runner
  sebelum merancang indikator tersebut.

**Batasan yang tetap berlaku**
- Status semua model tetap **eksperimental** — tidak ada rekomendasi publik
  berlabel selain eksperimental (tugas 1.10 wajib menampilkan label ini).
- Run resmi `--write-db` sudah terpakai; run resmi berikutnya hanya setelah ada
  perubahan yang disetujui di ROADMAP (fitur baru Fase 2), bukan ulang atas hasil ini.
