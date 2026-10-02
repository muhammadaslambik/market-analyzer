// Logika utama: routing view, kontrol analisa, screener, backtest.
(function () {
  const \$ = id => document.getElementById(id);
  const STATUS_LABEL = { strong_buy: "Strong buy", buy: "Buy", wait: "Wait", sell: "Sell", strong_sell: "Strong sell" };
  const STATUS_COLOR = { strong_buy: "var(--pos)", buy: "var(--pos)", wait: "var(--text3)", sell: "var(--neg)", strong_sell: "var(--neg)" };
  const SIGNAL_LABEL = { "-1": "Bear", 0: "Netral", 1: "Bull" };

  let curA = "crypto", curS = "BTCUSDT", curT = "4h", selCard = -1;

  // ---------- routing ----------
  document.querySelectorAll("#mainTabs .tab").forEach(t => {
    t.onclick = () => {
      document.querySelectorAll("#mainTabs .tab").forEach(x => x.classList.toggle("on", x === t));
      ["analisa", "screener", "backtest"].forEach(v => \$("view-" + v).hidden = v !== t.dataset.view);
    };
  });

  // ---------- isi kontrol ----------
  function fillAssets(selId) {
    const sel = \$(selId);
    if (!sel) return;
    sel.innerHTML = Object.entries(CONFIG.ASSETS)
      .map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
  }
  fillAssets("selAsset"); fillAssets("scrAsset"); fillAssets("btAsset");
  \$("btTf").innerHTML = '<option value="1d">1d</option><option value="4h">4h</option><option value="1h">1h</option>';

  // Menyesuaikan logika pemuatan Timeframe sesuai konfigurasi CONFIG
  function fillTf() {
    \$("tfChips").innerHTML = CONFIG.ASSETS[curA].tfs
      .map(t => `<button class="chip ${t === curT ? "on" : ""}" data-t="${t}">${t}</button>`).join("");
    document.querySelectorAll("#tfChips .chip").forEach(c => c.onclick = () => { curT = c.dataset.t; selCard = -1; \$("detail").hidden = true; load(); });
  }

  // Event saat user mengubah jenis Kelas Aset di dropdown utama
  \$("selAsset").onchange = e => { 
    curA = e.target.value; 
    curS = CONFIG.ASSETS[curA].default || CONFIG.ASSETS[curA].syms[0]; 
    curT = CONFIG.ASSETS[curA].tfs[Math.min(1, CONFIG.ASSETS[curA].tfs.length - 1)]; 
    selCard = -1; 
    \$("detail").hidden = true; 
    
    // Perbarui nilai pada kotak teks input pencarian baru
    const inputField = \$("symbolInput");
    if (inputField) inputField.value = curS;
    
    fillTf(); 
    load(); 
  };

  // Mengubah tombol Muat Ulang agar membaca teks dari Search Box
  \$("btnRefresh").onclick = () => {
    const inputField = \$("symbolInput");
    if (inputField) {
      let val = inputField.value.trim().toUpperCase();
      // Proteksi otomatis: menambahkan akhiran .JK jika pengguna lupa mengetik bursa efek Indonesia
      if (curA === 'stocks_id' && val && !val.endsWith('.JK')) {
        val = val + '.JK';
        inputField.value = val;
      }
      curS = val || CONFIG.ASSETS[curA].default;
    }
    load();
  };

  // ---------- analisa ----------
  async function load() {
    const r = await Api.analyze(curA, curS, curT);
    renderAnalysis(r);
  }

  function renderAnalysis(r) {
    const col = STATUS_COLOR[r.status] || "var(--text3)";
    Charts.gauge(r.score, col);
    \$("vStatus").textContent = STATUS_LABEL[r.status] || r.status;
    \$("vStatus").style.color = col;
    \$("vPrice").textContent = Charts.fmtN(r.price);
    \$("vSL").textContent = Charts.fmtN(r.suggested_stop_loss);
    \$("vTP").textContent = Charts.fmtN(r.suggested_take_profit);
    \$("vATR").textContent = "ATR(14) " + Charts.fmtN(r.atr) + " - SL 1.5x ATR, target 2x ATR" +
      (r.adx_filter_applied ? " - filter sideways (ADX < 20) aktif" : "");
    \$("vChartLab").textContent = r.symbol + " - harga vs EMA 20";
    \$("vTfLab").textContent = "timeframe " + r.timeframe;
    Charts.sparkline(r.price, r.symbol + r.timeframe);

    // forecast cone
    const f = Charts.cone(r.price, r.atr, r.score, r.timeframe);
    const pUp = Math.round((0.5 + r.score / 100 * 0.12) * 100);
    \$("forecastNums").innerHTML =
      `<span class="muted">probabilitas arah ${r.score >= 0 ? "naik" : "turun"}: <strong style="color:${col}">${pUp}%</strong></span>` +
      `<span class="num">tengah: ${Charts.fmtN(f.ev)}</span>`;
    \$("forecastNote").textContent = "Rentang 95%: " + Charts.fmtN(f.lo) + " - " + Charts.fmtN(f.hi) +
      ". Harga nyata seharusnya berada di dalam rentang 80% sekitar 8 dari 10 periode bila model terkalibrasi.";

    // kartu indikator
    \$("indGrid").innerHTML = r.indicators.map((ind, i) => {
      const cls = ind.signal > 0 ? "bull" : ind.signal < 0 ? "bear" : "neut";
      return `<div class="ind-card ${i === selCard ? "sel" : ""}" data-i="${i}">
        <div class="row-between"><span class="ind-name">${ind.name}</span>
        <span class="badge ${cls}">${SIGNAL_LABEL[ind.signal]}</span></div>
        <div class="ind-meta"><span>${ind.category}</span><span class="num">bobot ${ind.weight}%</span></div></div>`;
    }).join("");
    document.querySelectorAll(".ind-card").forEach(el => el.onclick = () => {
      const i = +el.dataset.i;
      selCard = selCard === i ? -1 : i;
      if (selCard < 0) { \$("detail").hidden = true; }
      else {
        const ind = r.indicators[i];
        \$("dName").textContent = ind.name;
        \$("dMeta").textContent = `${ind.category} - bobot ${ind.weight}% - sinyal: ${SIGNAL_LABEL[ind.signal]}${ind.note ? " - " + ind.note : ""}`;
        \$("dWhy").textContent = WHY[ind.name] || "";
        \$("detail").hidden = false;
      }
      renderAnalysis(r);
    });

    // tally
    const b = r.indicators.filter(x => x.signal > 0).length;
    const n = r.indicators.filter(x => x.signal === 0).length;
    const br = r.indicators.filter(x => x.signal < 0).length;
    \$("vTally").innerHTML =
      `<span><span class="dot-b">●</span> ${b} bullish</span>` +
      `<span><span class="dot-n">●</span> ${n} netral</span>` +
      `<span><span class="dot-r">●</span> ${br} bearish</span>` +
      `<span class="muted">konfluensi ${r.indicators.length} indikator${r.demo ? " - mode demo" : ""}</span>`;
    void curT;
  }

  ("dClose").onclick = () => selCard = -1; ("detail").hidden = true; document.querySelectorAll(".ind-card").forEach(c => c.classList.remove("sel")); };

  // ---------- screener ----------
  \$("btnScr").onclick = async () => {
    const asset = ("scrAsset").value, filter = ("scrFilter").value;
    const r = await Api.screener(asset, CONFIG.ASSETS[asset].tfs[0], filter);
    const tb = document.querySelector("#scrTable tbody");
    \$("scrEmpty").hidden = r.results.length > 0;
    tb.innerHTML = r.results.map(x => `<tr>
      <td>${x.symbol}</td><td class="num">${x.score > 0 ? "+" : ""}${x.score}</td>
      <td><span class="badge ${x.status.includes("buy") && !x.status.includes("sell") ? "bull" : x.status === "wait" ? "neut" : "bear"}">${STATUS_LABEL[x.status]}</span></td>
    </tr>`).join("");
  };

  // ---------- backtest ----------
  \$("btnBt").onclick = async () => {
    \$("btStats").hidden = true;
    const asset = \$("btAsset").value, sym = \(("btSymbol").value.trim() \vert{}\vert{} CONFIG.ASSETS[asset].syms[0], tf = \)("btTf").value;
    const r = await Api.backtest(asset, sym, tf);
    const pct = v => (v * 100).toFixed(1) + "%";
    \$("btWin").textContent = pct(r.win_rate);
    \$("btPF").textContent = r.profit_factor == null ? "-" : r.profit_factor.toFixed(2);
    \$("btRet").textContent = pct(r.total_return);
    \$("btBH").textContent = pct(r.buy_hold_return);
    \$("btDD").textContent = pct(r.max_drawdown);
    \$("btTr").textContent = r.trades;
    \$("btStats").hidden = false;
  };

  // ---------- init ----------
  (async () => {
    const mode = await Api.ping();
    const dot = \$("apiDot");
    dot.className = "api-dot " + (mode === "live" ? "on" : "demo");
    dot.title = mode === "live" ? "API terhubung" : "API tidak terjangkau - mode demo";
    
    // Inisialisasi pengisian nilai awal dari kotak teks input pencarian baru
    const inputField = \$("symbolInput");
    if (inputField) inputField.value = CONFIG.ASSETS[curA].default || "BTCUSDT";
    
    fillTf(); 
    await load();
  })();
})();
