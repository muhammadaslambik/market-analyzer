"""Market Analyzer API - entry point.

Run:  uvicorn app.main:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI

from app.api.routes_analyze import router

app = FastAPI(title="Market Analyzer", version="0.1.0",
              description="Multi-asset confluence analysis (crypto, XAUUSD, IDX, US stocks). "
                          "Signals are probabilistic, not guarantees.")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}
