"""Konfigurasi: variabel lingkungan dan ambang bawaan (tanpa menyimpan secret di kode)."""

import os

# Ambang anomali: selisih logaritma harga close antara dua candle berurutan.
# Melewati ambang hanya menandai candle ('outlier'), tidak membuangnya. Boleh disesuaikan.
OUTLIER_LOG_RETURN: dict[str, float] = {
    "1h": 0.15,  # sekitar 15% dalam satu jam
    "1d": 0.40,  # sekitar 40% dalam satu hari
}


def require_env(name: str) -> str:
    """Ambil variabel lingkungan wajib. Gagal jelas jika kosong atau tidak ada."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Variabel lingkungan wajib belum diisi: {name}")
    return value
