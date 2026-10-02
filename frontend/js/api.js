// Lapisan API: coba backend FastAPI, fallback ke data demo bila tidak terjangkau.
const Api = (() => {
  let mode = "checking"; // "live" | "demo"

  async function ping() {
    try {
      const r = await fetch(CONFIG.API_BASE + "/health", { signal: AbortSignal.timeout(2500) });
      mode = r.ok ? "live" : "demo";
    } catch { mode = "demo"; }
    return mode;
  }

  async function analyze(asset, symbol, tf) {
    if (mode === "live") {
      try {
        const r = await fetch(`${CONFIG.API_BASE}/analyze/${asset}/${symbol}?timeframe=${tf}`,
          { signal: AbortSignal.timeout(12000) });
        if (r.ok) return await r.json();
      } catch { /* jatuh ke demo */ }
    }
    return demoAnalyze(asset, symbol, tf);
  }

  async function screener(asset, tf, filter) {
    if (mode === "live") {
      try {
        const q = filter ? `&status_filter=${filter}` : "";
        const r = await fetch(`${CONFIG.API_BASE}/screener/${asset}?timeframe=${tf}${q}`,
          { signal: AbortSignal.timeout(30000) });
        if (r.ok) return await r.json();
      } catch { /* jatuh ke demo */ }
    }
    const results = CONFIG.ASSETS[asset].syms
      .map(s => { const r = demoAnalyze(asset, s, tf); return { symbol: s, score: r.score, status: r.status }; })
      .filter(x => !filter || x.status === filter);
    return { asset_class: asset, timeframe: tf, results, demo: true };
  }

  async function backtest(asset, symbol, tf) {
    if (mode === "live") {
      try {
        const r = await fetch(CONFIG.API_BASE + "/backtest", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ asset_class: asset, symbol, timeframe: tf, limit: 1000 }),
          signal: AbortSignal.timeout(60000),
        });
        if (r.ok) return await r.json();
      } catch { /* jatuh ke demo */ }
    }
    return { ...DEMO_BT[asset], demo: true };
  }

  return { ping, analyze, screener, backtest, get mode() { return mode; } };
})();
