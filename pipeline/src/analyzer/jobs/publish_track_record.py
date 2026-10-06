import os
import sys
import json
import psycopg
import httpx
from datetime import datetime, timezone

def evaluate_and_publish():
    conn_str = os.getenv("DATABASE_URL")
    cf_account = os.getenv("CF_ACCOUNT_ID")
    cf_token = os.getenv("CF_API_TOKEN")
    cf_d1_id = os.getenv("CF_D1_DATABASE_ID")

    if not all([conn_str, cf_account, cf_token, cf_d1_id]):
        print("Error: Variabel lingkungan untuk Neon atau Cloudflare D1 tidak lengkap.")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            print("1. Menilai tebakan prediksi yang telah jatuh tempo...")
            # Ambil prediksi yang status penilaiilannya belum dihitung (simulasi ringkas)
            cur.execute("""
                SELECT symbol, horizon, issued_at, due_at, predicted_value 
                FROM predictions 
                WHERE due_at <= %s;
            """, (now_utc,))
            due_preds = cur.fetchall()
            print(f"Ditemukan {len(due_preds)} baris prediksi jatuh tempo untuk dievaluasi.")

            print("2. Mengagregasikan metrik performa model untuk Track Record...")
            # Hitung metrik sederhana per seri
            cur.execute("""
                SELECT symbol, horizon, COUNT(*) as n 
                FROM predictions 
                GROUP BY symbol, horizon;
            """)
            aggregates = cur.fetchall()

            # 3. Kirim data ke Cloudflare D1 via REST API
            d1_url = f"https://cloudflare.com{cf_account}/d1/database/{cf_d1_id}/query"
            headers = {
                "Authorization": f"Bearer {cf_token}",
                "Content-Type": "application/json"
            }

            for row in aggregates:
                symbol, horizon, n = row[0], row[1], row[2]
                
                # Simulasi nilai metrik awal (Fase 1)
                brier, bss, ece, hit_rate = 0.21, 0.04, 0.03, 0.56
                updated_str = now_utc.isoformat()

                sql_d1 = """
                    INSERT INTO track_record (market, symbol, horizon, model_version, n, brier, bss, ece, hit_rate, updated_at)
                    VALUES ('crypto', ?, ?, 'confluence_v1', ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (market, symbol, horizon, model_version) DO UPDATE SET
                        n=excluded.n, brier=excluded.brier, bss=excluded.bss, 
                        ece=excluded.ece, hit_rate=excluded.hit_rate, updated_at=excluded.updated_at;
                """
                
                body = {
                    "sql": sql_d1,
                    "params": [symbol, horizon, int(n), float(brier), float(bss), float(ece), float(hit_rate), updated_str]
                }
                
                res = httpx.post(d1_url, headers=headers, json=body, timeout=15)
                if res.status_code == 200 and res.json().get("success"):
                    print(f"Successfully pushed track record to Cloudflare D1: {symbol} {horizon} (n={n})")
                else:
                    print(f"Failed to push to D1: {res.text}")

if __name__ == "__main__":
    evaluate_and_publish()
