# Deploy gratis (tanpa kartu, tanpa sleep)

Arsitektur: frontend static di Cloudflare Pages/Netlify (tidak pernah sleep),
backend FastAPI di Render Free + keep-alive GitHub Actions.

## 1. Backend - Render (gratis, tanpa kartu)

1. Push repo ke GitHub.
2. dashboard.render.com -> **New +** -> **Web Service** -> pilih repo.
3. Isi form:
   - **Name**: bebas
   - **Region**: Singapore (terdekat dengan Indonesia)
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**  <- PENTING: pilih Free, bukan Starter.
     Free tidak meminta kartu; Starter yang memunculkan dialog Add Card.
4. Deploy. Catat URL, mis. `https://market-analyzer-api.onrender.com`.

## 2. Keep-alive (cegah sleep 15 menit)

Buat `.github/workflows/keep-alive.yml`:

```yaml
name: Keep Alive
on:
  schedule:
    - cron: '*/10 * * * *'
  workflow_dispatch:
jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - run: curl -s -o /dev/null https://NAMA-APP-ANDA.onrender.com/health
```

Kuota Render 750 jam/bulan cukup untuk 1 service 24/7 (744 jam).

## 3. Frontend - Cloudflare Pages (gratis, tanpa kartu, no sleep)

1. cloudflare.com -> Pages -> **Create a project** -> pilih repo.
2. **Build settings**: framework = None, build command kosong,
   output directory = `frontend`.
3. Tambahkan env var sebelum config.js dimuat? Lebih mudah: buat
   `frontend/js/api-config.js` berisi:
   `window.API_BASE = "https://NAMA-APP-ANDA.onrender.com";`
   dan muat sebelum `config.js` di index.html.
4. Deploy -> dapat URL `https://NAMA-APP.pages.dev`.

Alternatif frontend: Netlify (drag & drop folder `frontend`), GitHub Pages.

## 4. CORS di backend

Set env var di Render -> Environment:
```
CORS_ORIGINS=https://NAMA-APP.pages.dev,http://localhost:5173
```
Tanpa ini, browser akan memblokir panggilan API dari domain frontend.

## Catatan geo-block Binance

Server Render/HF berlokasi di AS; api.binance.com dapat membatasi akses
dari IP AS. Bila endpoint crypto error 502/403, ganti provider data ke
CoinGecko atau KuCoin (gratis, ramah AS) - lihat `app/assets/crypto/service.py`.
