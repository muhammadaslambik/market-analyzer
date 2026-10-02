// Konfigurasi global teroptimasi: Ringan untuk Screener, Bebas Cari Semua Aset di Analisa.
const CONFIG = {
  API_BASE: window.API_BASE || "http://localhost:8000",
  ASSETS: {
    crypto:    { 
      label: "Crypto",          
      tfs: ["1h", "4h", "1d"],
      // Daftar koin utama untuk menu pindaian Screener massal otomatis
      syms: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "NEARUSDT", "SUIUSDT"] 
    },
    gold:      { 
      label: "XAUUSD",          
      tfs: ["1h", "4h", "1d"],  
      syms: ["XAUUSD"] 
    },
    stocks_id: { 
      label: "Saham Indonesia", 
      tfs: ["1d", "1wk"],
      // Membatasi scan massal hanya ke 10 top mover IDX agar backend anti-freeze
      syms: ["BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "ADRO.JK", "ANTM.JK", "AMMN.JK"] 
    },
    stocks_us: { 
      label: "Saham US",        
      tfs: ["4h", "1d"],
      // Membatasi scan massal bursa Amerika hanya untuk saham teknologi raksasa
      syms: ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "PLTR"] 
    },
  },
};
