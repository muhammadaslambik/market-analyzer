"""Job harian (candle 1 hari).

Jalankan: python -m analyzer.jobs.crypto_daily [--symbols BTCUSDT,ETHUSDT] [--dry-run]
"""

from analyzer.jobs.incremental import main_for


def main(argv: list[str] | None = None) -> int:
    return main_for("1d", "crypto_daily", argv)


if __name__ == "__main__":
    raise SystemExit(main())
