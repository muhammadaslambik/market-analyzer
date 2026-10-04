"""Placeholder for scheduled analysis jobs (APScheduler/Celery in Fase-1.5)."""

from app.api.routes_analyze import ASSETS


def refresh_all(timeframe: str | None = None) -> list[dict]:
    """Refresh every watchlist symbol. Wire this to a cron/APScheduler job."""
    from app.api.routes_analyze import screener  # reuse the same path as the API
    out = []
    for asset_class in ASSETS:
        out.append(screener(asset_class, timeframe))
    return out
