// Pembangun SVG: gauge skor, sparkline harga, kerucut prakiraan rentang.
const Charts = (() => {

  // ---- gauge semicircle, score -100..100 ----
  function gauge(score, color) {
    const rad = score / 100 * Math.PI / 2;
    const nx = 100 + 62 * Math.sin(rad), ny = 100 - 62 * Math.cos(rad);
    const dx = 100 + 74 * Math.sin(rad), dy = 100 - 74 * Math.cos(rad);
    set("needle", { x2: nx, y2: ny });
    set("dot", { cx: dx, cy: dy, fill: color });
    const g = document.getElementById("gScore");
    g.textContent = (score > 0 ? "+" : "") + Math.round(score);
  }

  // ---- sparkline random-walk deterministik (untuk visual; data live dari charting lib Fase-2) ----
  function sparkline(price, seedStr) {
    let seed = 0;
    for (const c of seedStr) seed = (seed * 31 + c.charCodeAt(0)) % 233280;
    const N = 80, rnd = () => { seed = (seed * 9301 + 49297) % 233280; return seed / 233280 - 0.48; };
    let cum = 0; const pts = [];
    for (let i = 0; i < N; i++) { cum += rnd() * 0.9; pts.push(cum); }
    let mn = Math.min(...pts), mx = Math.max(...pts);
    if (mx - mn < 1e-9) { mx += 1; mn -= 1; }
    const X = i => (i / (N - 1) * 600).toFixed(1);
    const Y = v => (140 - (v - mn) / (mx - mn) * 120).toFixed(1);
    let dPx = "", ema = 0, dEm = "";
    pts.forEach((p, i) => { ema += (p - ema) * 0.18; dPx += `${i ? "L" : "M"}${X(i)} ${Y(p)} `; dEm += `${i ? "L" : "M"}${X(i)} ${Y(ema)} `; });
    set("spPx", { d: dPx.trim() });
    set("spEma", { d: dEm.trim() });
    void price;
  }

  // ---- kerucut prakiraan: EV miring dari skor, lebar = z x ATR x sqrt(t) ----
  function cone(px, atr, score, tfLabel) {
    const sig = atr * 4;            // asumsi 4 bar ke depan untuk horizon terpilih
    const drift = score / 100 * 0.4 * sig;
    const ev = px + drift;
    const Z = [[1.96, "c95"], [1.282, "c80"], [0.674, "c50"]];
    const hi = ev + 1.96 * sig, lo = ev - 1.96 * sig, pad = (hi - lo) * 0.08;
    const top = hi + pad, bot = lo - pad;
    const X = t => 10 + t * 280, Y = p => 8 + (top - p) / (top - bot) * 130;
    const N = 40, bd = (t, z, sg) => (px + drift * t) + sg * z * sig * Math.sqrt(Math.max(t, 1e-4));
    Z.forEach(([z, id]) => {
      let d = "";
      for (let i = 0; i <= N; i++) d += `${i ? "L" : "M"}${X(i / N).toFixed(1)} ${Y(bd(i / N, z, 1)).toFixed(1)} `;
      for (let i = N; i >= 0; i--) d += `L${X(i / N).toFixed(1)} ${Y(bd(i / N, z, -1)).toFixed(1)} `;
      set(id, { d: d + "Z" });
    });
    let dm = "";
    for (let i = 0; i <= N; i++) dm += `${i ? "L" : "M"}${X(i / N).toFixed(1)} ${Y(px + drift * i / N).toFixed(1)} `;
    set("cMed", { d: dm });
    const cy = Y(px);
    set("cCur", { x1: 10, x2: 290, y1: cy, y2: cy });
    const ct = document.getElementById("cCurT");
    ct.setAttribute("x", 14); ct.setAttribute("y", cy - 5);
    ct.textContent = fmtN(px) + " sekarang";
    return { ev, sig, lo, hi, tfLabel };
  }

  function set(id, attrs) {
    const el = document.getElementById(id);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
  }

  function fmtN(n) {
    const d = n > 5000 ? 0 : n > 500 ? 1 : 2;
    return n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
  }

  return { gauge, sparkline, cone, fmtN };
})();
