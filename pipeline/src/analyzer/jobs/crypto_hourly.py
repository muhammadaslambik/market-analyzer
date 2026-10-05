"""Job per jam (candle 1 jam).

Jalankan: python -m analyzer.jobs.crypto_hourly [--symbols BTCUSDT,ETHUSDT] [--dry-run]
"""

from analyzer.jobs.incremental import main_for


def main(argv: list[str] | None = None) -> int:
    return main_for("1h", "crypto_hourly", argv)


if __name__ == "__main__":
    raise SystemExit(main())
