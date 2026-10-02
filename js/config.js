// Konfigurasi global. Ubah API_BASE lewat window.API_BASE sebelum config.js dimuat,
// atau edit langsung nilai default berikut.
const CONFIG = {
  API_BASE: window.API_BASE || "http://localhost:8000",
  ASSETS: {
    crypto:    { 
      label: "Crypto",          
      tfs: ["1h", "4h", "1d"],
      syms: [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT", 
        "MATICUSDT", "SUIUSDT", "NEARUSDT", "FETUSDT", "APTUSDT", 
        "SHIBUSDT", "PEPEUSDT", "RENDERUSDT", "TAOUSDT", "INJUSDT"
      ] 
    },
    gold:      { 
      label: "XAUUSD",          
      tfs: ["1h", "4h", "1d"],  
      syms: ["XAUUSD"] 
    },
    stocks_id: { 
      label: "Saham Indonesia", 
      tfs: ["1d", "1wk"],
      syms: [
        // Perbankan & Bluechips Utama
        "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", "ASII.JK", 
        // Komoditas, Energi & Pertambangan
        "ADRO.JK", "ANTM.JK", "PTBA.JK", "ITMG.JK", "INCO.JK", "BRMS.JK",
        "HRUM.JK", "MEDC.JK", "MBMA.JK", "AMMN.JK", "PGEO.JK", "PGAS.JK",
        // Infrastruktur, Ritel, Teknologi & Konsumer
        "GOTO.JK", "ISAT.JK", "EXCL.JK", "UNVR.JK", "ICBP.JK", "INDF.JK", 
        "CPIN.JK", "KLBF.JK", "MAPI.JK", "ACES.JK", "SMGR.JK", "PSSI.JK"
      ] 
    },
    stocks_us: { 
      label: "Saham US",        
      tfs: ["4h", "1d"],
      syms: [
        // The Magnificent Seven
        "NVDA", "AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META",
        // Chipmakers & AI Hardware
        "AMD", "INTC", "AVGO", "QCOM", "SMCI", "ASML",
        // Finansial, Teknologi Kreatif & Crypto Proxy
        "COIN", "MSTR", "PLTR", "NFLX", "DIS", "BRK-B", "JPM", "V"
      ] 
    },
  },
};
