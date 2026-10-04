"""Pembacaan konfigurasi dari variabel lingkungan (tanpa menyimpan secret di kode)."""

import os


def require_env(name: str) -> str:
    """Ambil variabel lingkungan wajib. Gagal jelas jika kosong atau tidak ada."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Variabel lingkungan wajib belum diisi: {name}")
    return value
