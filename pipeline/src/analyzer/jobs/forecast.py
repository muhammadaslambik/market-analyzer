import argparse
import json

import numpy as np
import pandas as pd
import psycopg

from analyzer.features import compute_confluence_features


def predict_live(symbol: str, timeframe: str, horizon: int, conn_str: str):
    """Menghitung skor konfluensi dan menyimpan probabilitas ke tabel predictions."""
    from datetime import timedelta

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            # Tarik data 200 candle terbaru untuk menghitung indikator
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume 
                FROM candles 
                WHERE symbol = %s AND timeframe = %s 
                ORDER BY timestamp DESC LIMIT 200;
            """,
                (symbol, timeframe),
            )
            rows = cur.fetchall()

            if len(rows) < 200:
                print(f"[{symbol} {timeframe}] Data historis di Neon kurang.")
                return

            df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_convert("UTC")
            df = df.sort_values("timestamp").reset_index(drop=True)
            df.set_index("timestamp", inplace=True)

            features_df = compute_confluence_features(df)
            latest_time = features_df.index[-1]
            latest_score = float(features_df["confluence_score"].iloc[-1])

            delta = timedelta(hours=horizon) if timeframe == "1h" else timedelta(days=horizon)
            due_time = latest_time + delta

            prob_up = float(np.clip((latest_score + 100.0) / 200.0, 0.0, 1.0))
            pred_json = json.dumps({"up": prob_up, "down": 1.0 - prob_up})

            # Tulis ke tabel predictions secara idempoten
            cur.execute(
                """
                INSERT INTO predictions (
                    market, symbol, horizon, issued_at, due_at, model_version, predicted_value
                ) VALUES ('crypto', %s, %s, %s, %s, 'confluence_v1', %s)
                ON CONFLICT (market, symbol, horizon, issued_at, model_version) DO NOTHING;
            """,
                (
                    symbol,
                    f"{horizon}h" if timeframe == "1h" else f"{horizon}d",
                    latest_time,
                    due_time,
                    pred_json,
                ),
            )
            print(
                f"[{symbol} {timeframe}] Live forecast success. "
                f"Skor: {latest_score:.1f}, P(Up): {prob_up:.2f}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--timeframe", required=True)
    parser.add_argument("--horizon", type=int, required=True)
    parser.add_argument("--conn", required=True)
    args = parser.parse_args()

    predict_live(args.symbol, args.timeframe, args.horizon, args.conn)
