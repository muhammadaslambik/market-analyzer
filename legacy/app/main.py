"""Market Analyzer API - entry point.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analyze import router

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


@app.get("/health")
def health():
    return {"status": "ok"}
