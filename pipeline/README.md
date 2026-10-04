# Pipeline data market-analyzer

Paket Python untuk mengambil, memvalidasi, dan menyimpan data pasar, serta (nanti) menghitung analisa.
Rujukan: `../docs/PRD.md` dan `../docs/SPEC-FASE-0.md`.

## Setup lokal (Windows PowerShell)

```powershell
cd pipeline
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Jika PowerShell menolak menjalankan skrip aktivasi:
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`

## Perintah

```powershell
ruff check .
ruff format --check .
pytest
```

## Variabel lingkungan

Salin nama variabel dari `.env.example` di folder utama ke `.env` (jangan di-commit) atau
simpan sebagai GitHub Secrets. Jangan menaruh nilai rahasia di kode.

## Catatan

Folder `../legacy/` berisi kode lama dan tidak ikut diperiksa oleh ruff, pytest, maupun CI.
