// Mode gelap/terang: ikut sistem saat pertama kali, lalu ingat pilihan user.
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem("ma-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  apply(saved || (prefersDark ? "dark" : "light"));

  function apply(mode) {
    root.setAttribute("data-theme", mode);
    localStorage.setItem("ma-theme", mode);
    const btn = document.getElementById("themeToggle");
    if (btn) btn.innerHTML = mode === "dark" ? iconSun() : iconMoon();
  }
  function iconMoon() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>';
  }
  function iconSun() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  }
  document.addEventListener("click", (e) => {
    if (e.target.closest("#themeToggle")) {
      apply(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
    }
  });
})();
