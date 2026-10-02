"""Market Analyzer API - entry point.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_analyze import router

app = FastAPI(title="Market Analyzer", version="0.1.0",
              description="Multi-asset confluence analysis (crypto, XAUUSD, IDX, US stocks). "
                          "Signals are probabilistic, not guarantees.")

# Tambahan Pengaman CORS: Mengizinkan halaman visual membaca mesin data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
