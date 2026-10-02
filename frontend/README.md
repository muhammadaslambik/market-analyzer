# Frontend - Market Analyzer

Dashboard statis (HTML/CSS/JS tanpa build step) untuk API FastAPI di `app/`.

## Menjalankan

Cukup serve folder ini secara statik, misalnya:

```bash
cd frontend
python -m http.server 5173
# buka http://localhost:5173
```

atau gunakan ekstensi Live Server di VS Code.

## Mode demo

Bila backend belum berjalan, UI otomatis memakai data demo (`js/demo.js`)
sehingga semua tampilan bisa dieksplorasi. Indikator status API ada di header:
hijau = API terhubung, kuning = mode demo.

Arahkan backend dengan mengatur `window.API_BASE` sebelum `config.js` dimuat,
atau edit default di `js/config.js`.

## Fitur

- **Analisa**: gauge skor konfluensi, status, SL/TP berbasis ATR, kerucut
  prakiraan rentang (50/80/95%), panel 10 indikator dengan penjelasan edukatif.
- **Screener**: pindai watchlist per kelas aset dengan filter status.
- **Backtest**: jalankan engine backtest backend, tampilkan metrik utama.
- **Mode gelap/terang**: ikut preferensi sistem, tersimpan di localStorage.
- **Responsif**: layout satu kolom di ponsel, kontrol menyesuaikan layar kecil.
