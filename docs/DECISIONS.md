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
