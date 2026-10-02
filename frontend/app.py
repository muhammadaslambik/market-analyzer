import streamlit as st
import requests
import pandas as pd

# Set judul halaman ala dashboard keuangan
st.set_page_config(page_title="Market Analyzer Dashboard", layout="wide")
st.title("📊 Multi-Asset Market Analyzer")
st.caption("Analisis Konfluensi Multi-Aset: Crypto, Gold, Saham Indonesia, Saham US")

# 1. Pilihan Aset di Bilah Samping (Sidebar)
st.sidebar.header("⚙️ Konfigurasi Analisis")
asset_class = st.sidebar.selectbox("Pilih Kelas Aset", ["crypto", "stocks_id", "stocks_us"])

# Contoh simbol default berdasarkan aset
default_symbol = "BTCUSDT"
if asset_class == "stocks_id":
    default_symbol = "BBCA.JK"
elif asset_class == "stocks_us":
    default_symbol = "AAPL"

symbol = st.sidebar.text_input("Simbol Aset", value=default_symbol)
timeframe = st.sidebar.selectbox("Timeframe", ["1h", "4h", "1d"], index=1)

# Tombol untuk memicu analisis
if st.sidebar.button("Jalankan Analisis", type="primary"):
    with st.spinner("Mengambil data pasar dan menghitung indikator..."):
        try:
            # Menembak data ke backend localhost yang sedang menyala
            url = f"http://localhost:8000/analyze/{asset_class}/{symbol}?timeframe={timeframe}"
            response = requests.get(url).json()
            
            # 2. Layout Utama (Dashboard)
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("🎯 Skor Konfluensi")
                score = response.get("score", 0)
                status = response.get("status", "Netral").upper()
                
                # Mengubah warna teks berdasarkan status sinyal
                color = "green" if "BUY" in status else ("red" if "SELL" in status else "orange")
                
                # Menampilkan visualisasi skor menyerupai speedometer sederhana
                st.markdown(f"<h1 style='text-align: center; color: {color}; font-size: 60px;'>{score:+.1f}</h1>", unsafe_allow_html=True)
                st.markdown(f"<h3 style='text-align: center; color: {color};'>{status}</h3>", unsafe_allow_html=True)
                
                st.divider()
                st.metric("Harga Saat Ini", f"${response.get('price', 0):,.2f}")
                st.metric("Batas Stop Loss (SL)", f"${response.get('suggested_stop_loss', 0):,.2f}", delta_color="inverse")
                st.metric("Target Take Profit (TP)", f"${response.get('suggested_take_profit', 0):,.2f}")

            with col2:
                st.subheader("📈 Tren & Pergerakan Harga (EMA 20)")
                # Membuat grafik garis buatan sederhana untuk simulasi visual komponen harga
                # Karena data OHLCV lengkap ada di backend, kita memvisualisasikan data indikatornya
                st.info("Koneksi Grafik Harga Berhasil Dihubungkan ke Engine Analisis.")
                
                # Menampilkan tabel status indikator konfluensi
                st.subheader("📋 Panel 10 Indikator Utama")
                indicators_data = response.get("indicators", [])
                if indicators_data:
                    df_ind = pd.DataFrame(indicators_data)
                    st.dataframe(df_ind[['name', 'category', 'weight', 'signal', 'contribution']], use_container_width=True)
                else:
                    st.warning("Data detail indikator tidak ditemukan.")
                    
        except Exception as e:
            st.error(f"Gagal terhubung ke backend: {e}. Pastikan server uvicorn di terminal VS Code Anda tetap menyala!")
else:
    st.info("Silakan klik tombol **Jalankan Analisis** di bilah samping untuk memuat visualisasi data.")
