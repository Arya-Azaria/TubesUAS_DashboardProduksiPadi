import streamlit as st
import pandas as pd
import json
import plotly.express as px
import pydeck as pdk
import numpy as np

st.set_page_config(
    page_title="Dashboard Padi Final",
    page_icon="🌾",
    layout="wide"
)

# 1. Load Data dari JSON
@st.cache_data
def load_data(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        
        # Konversi tipe data
        df['produksi_ton'] = pd.to_numeric(df['produksi_ton'], errors='coerce')
        df['tahun'] = pd.to_numeric(df['tahun'], errors='coerce')
        
        df['provinsi'] = df['provinsi'].astype(str).str.strip().str.title()
        df['kabupaten_kota'] = df['kabupaten_kota'].astype(str).str.strip().str.title()
        
        df['provinsi'] = df['provinsi'].str.replace('Sumatra', 'Sumatera')
        
        df['provinsi'] = df['provinsi'].replace({
            'Dki Jakarta': 'DKI Jakarta',
            'Di Yogyakarta': 'DI Yogyakarta',
            'Bangka Belitung': 'Kepulauan Bangka Belitung'
        })
        
        return df
    except Exception as e:
        st.error(f"Error membaca file: {e}")
        return pd.DataFrame()

#2. Database Koordinat
def get_coordinates():
    return {
        "Aceh": {"lat": 4.6951, "lon": 96.7494},
        "Sumatera Utara": {"lat": 2.1154, "lon": 99.5451},
        "Sumatera Barat": {"lat": -0.7399, "lon": 100.8000},
        "Riau": {"lat": 0.5071, "lon": 101.4478},
        "Jambi": {"lat": -1.6101, "lon": 103.6131},
        "Sumatera Selatan": {"lat": -3.3194, "lon": 104.9145},
        "Bengkulu": {"lat": -3.7928, "lon": 102.2608},
        "Lampung": {"lat": -4.5585, "lon": 105.4068},
        "Kepulauan Bangka Belitung": {"lat": -2.7411, "lon": 106.4406},
        "Kepulauan Riau": {"lat": 3.9159, "lon": 108.1961},
        "DKI Jakarta": {"lat": -6.2088, "lon": 106.8456},
        "Jawa Barat": {"lat": -6.9175, "lon": 107.6191},
        "Jawa Tengah": {"lat": -7.1510, "lon": 110.1403},
        "DI Yogyakarta": {"lat": -7.7956, "lon": 110.3695},
        "Jawa Timur": {"lat": -7.5361, "lon": 112.2384},
        "Banten": {"lat": -6.4058, "lon": 106.0640},
        "Bali": {"lat": -8.4095, "lon": 115.1889},
        "Nusa Tenggara Barat": {"lat": -8.6529, "lon": 117.3616},
        "Nusa Tenggara Timur": {"lat": -8.6574, "lon": 121.0794},
        "Kalimantan Barat": {"lat": -0.2787, "lon": 111.4753},
        "Kalimantan Tengah": {"lat": -1.6815, "lon": 113.3824},
        "Kalimantan Selatan": {"lat": -3.0926, "lon": 115.2838},
        "Kalimantan Timur": {"lat": 0.5387, "lon": 116.4194},
        "Kalimantan Utara": {"lat": 3.0731, "lon": 116.0414},
        "Sulawesi Utara": {"lat": 0.6247, "lon": 123.9750},
        "Sulawesi Tengah": {"lat": -1.4300, "lon": 121.4456},
        "Sulawesi Selatan": {"lat": -3.6687, "lon": 119.9740},
        "Sulawesi Tenggara": {"lat": -4.1449, "lon": 122.1746},
        "Gorontalo": {"lat": 0.6999, "lon": 122.4467},
        "Sulawesi Barat": {"lat": -2.8441, "lon": 119.2321},
        "Maluku": {"lat": -3.2385, "lon": 130.1453},
        "Maluku Utara": {"lat": 1.5709, "lon": 127.8087},
        "Papua": {"lat": -4.2699, "lon": 138.0804},
        "Papua Barat": {"lat": -1.3361, "lon": 133.1747},
        "Papua Selatan": {"lat": -7.4927, "lon": 139.6997},
        "Papua Tengah": {"lat": -4.1783, "lon": 136.2570},
        "Papua Pegunungan": {"lat": -4.0931, "lon": 139.1174}
    }

def add_coordinates(df):
    coords = get_coordinates()
    df_map = df.groupby(['provinsi'])['produksi_ton'].sum().reset_index()
    df_map['lat'] = df_map['provinsi'].map(lambda x: coords.get(x, {}).get('lat'))
    df_map['lon'] = df_map['provinsi'].map(lambda x: coords.get(x, {}).get('lon'))
    return df_map.dropna(subset=['lat', 'lon'])

# PROGRAM UTAMA
def main():
    st.title("🌾 Dashboard Monitoring Padi Nasional")
    
    df = load_data('data_padi_final.json')
    if df.empty:
        st.warning("Data kosong atau file tidak ditemukan.")
        return

    years_list = sorted(df['tahun'].dropna().unique().astype(int))
    year_options = ["Semua Data"] + years_list
    prov_list = sorted(df['provinsi'].unique().tolist())
    prov_options = ["Semua Provinsi"] + prov_list

    # TAB
    tab_gis, tab_chart, tab_warning,tab_forecasting, tab_data = st.tabs([
        "🗺️ Peta Sebaran (GIS)", 
        "📈 Analisis Grafik", 
        "🚨 Early Warning Penurunan", 
        "🔮 Prediksi 2025",
        "📂 Data Detail"
    ])

    # TAB 1: PETA GIS

    with tab_gis:
        st.subheader("Geospasial Produksi Padi")
        col_ctrl_gis, col_info_gis = st.columns([1, 3])
        with col_ctrl_gis:
            selected_year_gis = st.selectbox("Pilih Tahun Peta:", year_options, key="year_gis")
        
        df_gis_filtered = df if selected_year_gis == "Semua Data" else df[df['tahun'] == selected_year_gis]
        total_prod_gis = df_gis_filtered['produksi_ton'].sum()
        
        with col_info_gis:
            st.info(f"Total Produksi Nasional: **{total_prod_gis:,.0f} Ton**")

        df_map_ready = add_coordinates(df_gis_filtered)
        
        if not df_map_ready.empty:
            df_map_ready['produksi_formatted'] = df_map_ready['produksi_ton'].apply(lambda x: f"{x:,.0f}")
            
            max_val = df_map_ready['produksi_ton'].max()
            if max_val == 0: max_val = 1 

            # WARNA TABUNG
            def kustom_warna(nilai):
                sepuluh_juta = 10000000 
                duapuluh_juta = 20000000

                if nilai >= duapuluh_juta:
                    return [255, 0, 0, 200]  
                elif nilai >= sepuluh_juta:
                    return [0, 255, 0, 200]  
                else:
                    return [255, 255, 0, 200]

            df_map_ready['color'] = df_map_ready['produksi_ton'].apply(lambda x: kustom_warna(x))

            layer = pdk.Layer(
                "ColumnLayer",
                data=df_map_ready,
                get_position=["lon", "lat"],
                get_elevation="produksi_ton",
                elevation_scale=0.015,
                radius=30000,           
                get_fill_color="color", 
                pickable=True,
                auto_highlight=True,
                extruded=True,
            )

            view_state = pdk.ViewState(
                latitude=-2.5, longitude=118.0, zoom=4, pitch=45, bearing=0
            )

            tooltip = {
                "html": "<b>{provinsi}</b><br/>Produksi: {produksi_formatted} Ton",
                "style": {"backgroundColor": "rgba(0, 0, 0, 0.8)", "color": "white"}
            }

            deck = pdk.Deck(
                map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
                initial_view_state=view_state,
                layers=[layer],
                tooltip=tooltip
            )

            st.pydeck_chart(deck, use_container_width=True)


    # TAB 2: VISUALISASI GRAFIK

    with tab_chart:
        st.subheader("Peringkat & Detail Wilayah")
        c_filter1, c_filter2, c_filter3 = st.columns(3)
        with c_filter1: selected_year_chart = st.selectbox("Pilih Tahun:", year_options, key="year_chart")
        with c_filter2: limit_show = st.selectbox("Tampilkan Top:", ["10", "20", "50", "Semua"], index=1)
        with c_filter3: selected_prov_chart = st.selectbox("Filter Provinsi:", ["Semua"] + prov_list)

        df_chart = df.copy()
        if selected_year_chart != "Semua Data": df_chart = df_chart[df_chart['tahun'] == selected_year_chart]
        if selected_prov_chart != "Semua": df_chart = df_chart[df_chart['provinsi'] == selected_prov_chart]

        df_chart_final = df_chart.sort_values('produksi_ton', ascending=False)
        limit_int = len(df_chart_final) if limit_show == "Semua" else int(limit_show)
        df_chart_final = df_chart_final.head(limit_int)

        if not df_chart_final.empty:
            fig_bar = px.bar(df_chart_final, x='produksi_ton', y='kabupaten_kota', orientation='h',
                             color='produksi_ton', color_continuous_scale='Viridis', height=600)
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)


    # TAB 3: EARLY WARNING (UPDATED)

    with tab_warning:
        st.subheader("🚨 Deteksi Penurunan Produksi Drastis")
        st.markdown("""
        **Tujuan:** Mengidentifikasi wilayah dengan penurunan produksi padi paling signifikan pada rentang waktu terpilih.
        """)
    
        # --- INPUT FILTER ---
        col_f1, col_f2 = st.columns([2, 1])
        
        with col_f1:
            # Filter rentang tahun
            if len(years_list) >= 2:
                year_range = st.select_slider(
                    "Pilih Rentang Tahun Perbandingan:",
                    options=years_list,
                    value=(years_list[-2], years_list[-1])
                )
                y_prev, y_now = year_range
            else:
                year_range = None
    
        with col_f2:
            # Filter Top N
            top_n = st.number_input("Tampilkan Top Berapa?", min_value=1, max_value=20, value=5)
    
        # --- LOGIKA ANALISIS ---
        if year_range and y_prev != y_now:
            # Hitung selisih per kabupaten berdasarkan tahun yang dipilih
            df_now = df[df['tahun'] == y_now].groupby(['provinsi', 'kabupaten_kota'])['produksi_ton'].sum()
            df_prev = df[df['tahun'] == y_prev].groupby(['provinsi', 'kabupaten_kota'])['produksi_ton'].sum()
            
            # Gabungkan data (menggunakan inner join agar hanya muncul yang ada di kedua tahun)
            diff_df = (df_now - df_prev).reset_index()
            diff_df.columns = ['Provinsi', 'Kabupaten/Kota', 'Selisih_Ton']
            
            # Ambil yang mengalami penurunan (filter nilai negatif)
            drop_df = diff_df[diff_df['Selisih_Ton'] < 0].sort_values('Selisih_Ton').head(top_n)
            
            if not drop_df.empty:
                st.error(f"⚠️ **Peringatan:** {len(drop_df)} Wilayah dengan penurunan terbesar dari {y_prev} ke {y_now}")
                
                # Tampilan Metric (Gunakan baris baru jika top_n terlalu banyak)
                # Agar tidak memenuhi layar secara horizontal, kita batasi per baris
                rows_metric = st.columns(min(len(drop_df), 5)) 
                for i, row in enumerate(drop_df.head(5).itertuples()): # Limit display metric hanya 5 pertama
                    with rows_metric[i]:
                        st.metric(label=row._2, value=f"{row.Selisih_Ton:,.0f} Ton")
                
                # Chart
                fig_warning = px.bar(
                    drop_df, 
                    x='Selisih_Ton', 
                    y='Kabupaten/Kota', 
                    title=f"Top {top_n} Wilayah Kritis Penurunan Produksi ({y_prev} - {y_now})",
                    color='Selisih_Ton', 
                    color_continuous_scale='Reds_r', 
                    orientation='h',
                    text_auto='.2s'
                )
                # Membalikkan urutan y agar yang paling turun ada di paling atas
                fig_warning.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_warning, use_container_width=True)
                
            else:
                st.success(f"✅ Tidak ditemukan penurunan produksi dari tahun {y_prev} ke {y_now}.")
        
        elif y_prev == y_now:
            st.warning("Pilih dua tahun yang berbeda pada slider untuk melihat perbandingan.")
        else:
            st.info("Data tahunan tidak cukup untuk melakukan analisis perbandingan.")
    

    # TAB 4: DATA PREDIKSI

    with tab_forecasting:
        st.subheader("🔮 Prediksi Produksi Tahun 2025")
        st.markdown("**Tujuan:** Perencanaan stok pangan nasional untuk mencegah impor mendadak dengan memprediksi tren masa depan.")
        
        target_prov = st.selectbox("Pilih Provinsi untuk Prediksi:", prov_list)
        df_target = df[df['provinsi'] == target_prov].groupby('tahun')['produksi_ton'].sum().reset_index()
        
        if len(df_target) > 1:
            # Simple Linear Regression: y = mx + c
            x = df_target['tahun'].values
            y = df_target['produksi_ton'].values
            m, c = np.polyfit(x, y, 1)
            
            pred_2025 = m * 2025 + c
            
            # Visualisasi Tren
            fig_pred = px.line(df_target, x='tahun', y='produksi_ton', title=f"Tren Produksi {target_prov}", markers=True)
            fig_pred.add_scatter(x=[2025], y=[pred_2025], name='Prediksi 2025', marker=dict(color='red', size=12))
            st.plotly_chart(fig_pred, use_container_width=True)
            
            # Alert Hasil
            st.info(f"💡 **Hasil Analisis:** Berdasarkan tren {len(x)} tahun terakhir, prediksi produksi **{target_prov}** pada tahun 2025 adalah **{max(0, pred_2025):,.0f} Ton**.")
        else:
            st.warning("Data historis tidak cukup untuk membuat prediksi.")


    # TAB 5: DATA TABLE 

    with tab_data:
        st.subheader("🗃️ Eksplorasi Data Mentah")
        
        with st.container(border=True):
            st.markdown("**Filter Data Tabel**")
            c_d1, c_d2, c_d3 = st.columns(3)
            
            with c_d1:
                sel_year_data = st.selectbox("Tahun:", year_options, key="year_data")
            with c_d2:
                sel_prov_data = st.selectbox("Provinsi:", prov_options, key="prov_data")
            with c_d3:
                search_query = st.text_input("🔍 Cari Kabupaten/Kota:", placeholder="Ketikan nama wilayah...", key="search_data")
    
        # Proses Filtering tetap sama
        df_table = df.copy()
    
        if sel_year_data != "Semua Data":
            df_table = df_table[df_table['tahun'] == sel_year_data]
        
        if sel_prov_data != "Semua Provinsi":
            df_table = df_table[df_table['provinsi'] == sel_prov_data]
            
        if search_query:
            df_table = df_table[df_table['kabupaten_kota'].str.contains(search_query, case=False)]
    
        if not df_table.empty:
            # --- KUNCI PERBAIKAN DI SINI ---
            # 1. Reset index agar nomor urut kembali dari 0 setelah difilter
            df_display = df_table.reset_index(drop=True)
            # 2. Opsional: Tambah 1 agar nomor dimulai dari angka 1, bukan 0
            df_display.index += 1 
    
            m1, m2 = st.columns(2)
            m1.metric("Total Produksi (Filtered)", f"{df_table['produksi_ton'].sum():,.0f} Ton")
            m2.metric("Jumlah Wilayah", f"{len(df_table)} Lokasi")
            
            st.divider()
    
            st.dataframe(
                df_display, # Gunakan dataframe yang sudah di-reset index-nya
                use_container_width=True,
                column_config={
                    "tahun": st.column_config.NumberColumn(
                        "Tahun",
                        format="%d"
                    ),
                    "provinsi": "Provinsi",
                    "kabupaten_kota": "Kabupaten / Kota",
                    "produksi_ton": st.column_config.ProgressColumn(
                        "Produksi (Ton)",
                        help="Visualisasi volume produksi",
                        format="%d",
                        min_value=0,
                        max_value=df['produksi_ton'].max(),
                    ),
                },
                hide_index=False # Tampilkan index agar nomor terlihat ramping di kiri
            )
            
            csv = df_table.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Data CSV",
                data=csv,
                file_name=f'data_padi_filter.csv',
                mime='text/csv',
            )
        else:
            st.warning("Data tidak ditemukan dengan kombinasi filter tersebut.")

if __name__ == "__main__":
    main()