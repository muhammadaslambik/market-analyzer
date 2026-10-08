"""Market Analyzer API - entry point.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""

import os
import sys
from pathlib import Path

# supaya API bisa import modul pipeline (analyzer.*)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipeline" / "src"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analyze import router
from app.api.routes_fundamental import router as fundamental_router

# Origin frontend dipisah koma lewat env CORS_ORIGINS, e.g.:
#   CORS_ORIGINS="https://market-analyzer.pages.dev,http://localhost:5173"
# Default "*" hanya untuk development - batasi di produksi.
_origins = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(title="Market Analyzer", version="0.1.0",
              description="Multi-asset confluence analysis (crypto, XAUUSD, IDX, US stocks). "
                          "Signals are probabilistic, not guarantees.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(fundamental_router)


@app.get("/health")
def health():
    return {"status": "ok"}
