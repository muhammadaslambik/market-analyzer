// Data demo - dipakai otomatis bila backend belum berjalan, agar UI bisa dieksplorasi.
// Angka bersifat ilustrasi, bukan data pasar nyata.

const WHY = {
  ema_ribbon: "Harga dibanding tiga EMA (20/50/200). Di atas ketiganya = tren naik terkonfirmasi di tiga horizon waktu. Bobot terbesar karena arah tren adalah dasar semua keputusan.",
  supertrend: "Trailing stop dinamis berbasis ATR (10,3). Berpindah hijau saat harga tembus ke atas garis - buyer mulai mengendalikan.",
  macd: "Selisih EMA 12/26 terhadap garis sinyal 9. Membaca percepatan momentum: histogram membesar = momentum menguat, menyempit = memudar.",
  rsi_divergence: "RSI 14 plus deteksi divergensi. Harga membentuk higher high tapi RSI lower high = momentum bearish tersembunyi, peringatan dini pembalikan.",
  bollinger: "Pita volatilitas (20,2). Squeeze - pita menyempit - sering mendahului breakout; sentuh band bawah dalam uptren biasanya pullback sehat.",
  vwap_signal: "Harga rata-rata tertimbang volume, acuan institusional. Bertahan di atas VWAP = buyer dominan; kehilangan VWAP = buyer kehilangan kendali intraday.",
  cvd: "Cumulative volume delta: selisih volume market order buy vs sell yang berjalan kumulatif. CVD naik saat harga sideways = akumulasi diam-diam.",
  funding_oi: "Sentimen pasar derivatif. Funding sangat positif dengan open interest melonjak = posisi long overleveraged - rawan long squeeze. Sebaliknya untuk short.",
  adx: "Average directional index: kekuatan tren, bukan arah. Di atas 25 = tren kuat, sinyal tren dipercaya. Di bawah 20 = sideways, sistem memaksa status wait.",
  volume_profile: "Volume yang diperdagangkan di tiap level harga. Node volume tinggi bertindak sebagai magnet harga sekaligus support/resistance yang dihargai pasar.",
  obv: "On-balance volume mengakumulasikan volume mengikuti arah pergerakan. OBV naik saat harga datar = akumulasi; OBV turun saat harga naik = distribusi.",
  rs_vs_index: "Kekuatan relatif terhadap benchmark (DXY untuk emas, IHSG/S&P untuk saham). Instrumen yang konsisten outperform = kandidat terbaik.",
  foreign_flow: "Akumulasi net buy investor asing - driver paling konsisten untuk saham blue chip Indonesia. Butuh data eksternal; netral di MVP.",
};

const _n = (name, cat, w) => ({ name, category: cat, weight: w });

// Struktur indikator per aset (urutan harus cocok dengan array s di DEMO)
const IND_SETS = {
  crypto: [_n("ema_ribbon","tren",12),_n("supertrend","tren",12),_n("macd","momentum",10),
           _n("rsi_divergence","momentum",10),_n("bollinger","volatilitas",8),_n("vwap_signal","volume",10),
           _n("cvd","order flow",12),_n("funding_oi","derivatif",12),_n("adx","filter",8),
           _n("volume_profile","volume",6)],
  gold: [_n("ema_ribbon","tren",12),_n("supertrend","tren",12),_n("macd","momentum",10),
         _n("rsi_divergence","momentum",10),_n("bollinger","volatilitas",10),_n("vwap_signal","volume",12),
         _n("adx","filter",10),_n("obv","volume",10),_n("rs_vs_index","makro",12),
         _n("foreign_flow","makro",2)],
  stocks_id: [_n("ema_ribbon","tren",12),_n("macd","momentum",10),_n("rsi_divergence","momentum",10),
              _n("bollinger","volatilitas",8),_n("obv","volume",12),_n("vwap_signal","volume",10),
              _n("adx","filter",10),_n("foreign_flow","khas IHSG",14),_n("rs_vs_index","stock picking",14),
              _n("volume_profile","volume",10)],
  stocks_us: [_n("ema_ribbon","tren",12),_n("supertrend","tren",10),_n("macd","momentum",10),
              _n("rsi_divergence","momentum",10),_n("bollinger","volatilitas",8),_n("obv","volume",12),
              _n("vwap_signal","volume",12),_n("adx","filter",8),_n("rs_vs_index","stock picking",14),
              _n("volume_profile","volume",14)],
};

// DEMO[asset][symbol][timeframe] = {px, atr, s:[10 sinyal -1/0/1]}
const DEMO = {
  crypto: {
    BTCUSDT: { "1h":{px:63980,atr:640,s:[1,0,0,-1,0,1,0,-1,0,0]},
               "4h":{px:64230,atr:1850,s:[1,1,0,0,0,1,1,-1,0,0]},
               "1d":{px:64850,atr:3200,s:[1,1,1,0,1,1,1,0,1,0]} },
    ETHUSDT: { "4h":{px:3152,atr:98,s:[1,1,0,0,0,1,1,-1,0,0]},
               "1h":{px:3138,atr:42,s:[0,1,0,0,-1,1,0,0,0,0]},
               "1d":{px:3190,atr:150,s:[1,1,1,1,0,1,0,1,1,0]} },
    SOLUSDT: { "4h":{px:148.2,atr:4.6,s:[1,0,0,-1,0,0,1,-1,0,0]},
               "1h":{px:146.9,atr:2.1,s:[0,0,0,-1,0,0,0,-1,0,0]},
               "1d":{px:151.4,atr:7.8,s:[1,1,0,0,0,1,1,0,1,1]} },
    BNBUSDT: { "4h":{px:585.4,atr:9.8,s:[1,1,0,0,0,1,0,0,0,0]} },
    XRPUSDT: { "4h":{px:0.612,atr:0.014,s:[0,0,-1,0,0,0,-1,-1,0,0]} },
  },
  gold: {
    XAUUSD: { "1h":{px:2658.2,atr:8.4,s:[1,0,0,0,0,1,0,-1,0,0]},
              "4h":{px:2661.5,atr:14.2,s:[1,1,0,1,0,1,0,1,0,0]},
              "1d":{px:2669.0,atr:31.5,s:[1,1,1,1,0,1,1,1,1,1]} },
  },
  stocks_id: {
    "BBCA.JK": { "1d":{px:9850,atr:175,s:[1,1,0,0,0,1,0,1,1,0]},
                 "1wk":{px:9800,atr:420,s:[0,1,0,0,0,0,0,1,1,0]} },
    "BBRI.JK": { "1d":{px:4620,atr:110,s:[1,0,0,-1,0,0,1,0,1,0]} },
    "TLKM.JK": { "1d":{px:2980,atr:72,s:[0,0,0,0,-1,0,0,0,0,0]} },
    "ASII.JK": { "1d":{px:5050,atr:130,s:[1,1,0,0,0,1,0,1,0,1]} },
    "BMRI.JK": { "1d":{px:6725,atr:140,s:[1,0,0,0,0,1,0,1,1,1]} },
  },
  stocks_us: {
    NVDA: { "1d":{px:131.4,atr:3.2,s:[1,1,1,1,0,0,1,0,1,1]},
            "4h":{px:130.9,atr:1.4,s:[1,0,0,1,0,0,1,0,0,0]} },
    AAPL: { "1d":{px:232.8,atr:4.1,s:[1,0,0,0,0,1,0,1,0,0]} },
    MSFT: { "1d":{px:428.3,atr:6.8,s:[1,1,0,1,0,1,1,0,1,0]} },
    TSLA: { "1d":{px:248.5,atr:9.6,s:[-1,-1,0,-1,0,0,0,0,-1,0]} },
    AMZN: { "1d":{px:197.2,atr:3.9,s:[1,0,0,0,0,1,0,0,1,0]} },
  },
};

// Demo backtest per aset (ilustrasi hasil engine)
const DEMO_BT = {
  crypto:    { trades: 86,  win_rate: 0.56, profit_factor: 1.42, total_return: 0.38,  buy_hold_return: 0.55,  max_drawdown: -0.14, bars: 1000, avg_score: 12.4 },
  gold:      { trades: 64,  win_rate: 0.53, profit_factor: 1.21, total_return: 0.17,  buy_hold_return: 0.24,  max_drawdown: -0.11, bars: 1000, avg_score: 8.1 },
  stocks_id: { trades: 41,  win_rate: 0.54, profit_factor: 1.18, total_return: 0.11,  buy_hold_return: 0.06,  max_drawdown: -0.09, bars: 750,  avg_score: 6.8 },
  stocks_us: { trades: 58,  win_rate: 0.55, profit_factor: 1.31, total_return: 0.22,  buy_hold_return: 0.19,  max_drawdown: -0.12, bars: 1000, avg_score: 9.6 },
};

// Bangun objek hasil analisa ala respons API /analyze
function demoAnalyze(asset, symbol, tf) {
  const set = IND_SETS[asset];
  const d = (DEMO[asset][symbol] || {})[tf] || Object.values(DEMO[asset][symbol])[0];
  const indicators = set.map((spec, i) => ({
    ...spec, signal: d.s[i], contribution: +(d.s[i] * spec.weight).toFixed(1),
    note: spec.name === "foreign_flow" ? "butuh data eksternal - netral di demo" : "",
  }));
  const totalW = set.reduce((a, x) => a + x.weight, 0);
  const score = +(indicators.reduce((a, x) => a + x.contribution, 0) / totalW * 100).toFixed(1);
  const dir = score >= 0 ? 1 : -1;
  let status = score >= 60 ? "strong_buy" : score >= 20 ? "buy" : score > -20 ? "wait" : score > -60 ? "sell" : "strong_sell";
  // Filter ADX asli (nilai < 20 -> wait) dihitung backend; di demo tidak dipaksa
  // agar status konsisten dengan respons API nyata.
  const adxFiltered = false;
  return {
    asset_class: asset, symbol, timeframe: tf, price: d.px, score, status,
    adx_filter_applied: adxFiltered, atr: d.atr,
    suggested_stop_loss: +(d.px - dir * 1.5 * d.atr).toFixed(8),
    suggested_take_profit: +(d.px + dir * 2 * d.atr).toFixed(8),
    indicators, demo: true,
  };
}
