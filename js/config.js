// Konfigurasi global. Ubah API_BASE lewat window.API_BASE sebelum config.js dimuat,
// atau edit langsung nilai default berikut.
const CONFIG = {
  API_BASE: window.API_BASE || "http://localhost:8000",
  ASSETS: {
    crypto:    { label: "Crypto",          tfs: ["1h", "4h", "1d"],
                 syms: ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT"] },
    gold:      { label: "XAUUSD",          tfs: ["1h", "4h", "1d"],  syms: ["XAUUSD"] },
    stocks_id: { label: "Saham Indonesia", tfs: ["1d", "1wk"],
                 syms: ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "BMRI.JK"] },
    stocks_us: { label: "Saham US",        tfs: ["4h", "1d"],
                 syms: ["NVDA", "AAPL", "MSFT", "TSLA", "AMZN"] },
  },
};
