import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sayfa Ayarları
st.set_page_config(page_title="Smart Liquefaction Tool", layout="centered")

# Sabit Değerler
GAMMA_SOIL = 19.0 
GAMMA_WATER = 9.81
MW = 7.5
AMAX = 0.30

def get_soil_description(n):
    """SPT-N değerine göre temel zemin tanımlaması"""
    if n < 4: return "Very Loose Sand", "#B22222" # Koyu Kırmızı
    elif n < 10: return "Loose Sand", "#FF4500"   # Turuncu-Kırmızı
    elif n < 30: return "Medium Dense Sand", "#FFD700" # Altın/Sarı
    elif n < 50: return "Dense Sand", "#9ACD32"    # Sarı-Yeşil
    else: return "Very Dense Sand", "#228B22"      # Koyu Yeşil

def calculate_lpi(df):
    lpi_total = 0
    df_20m = df[df['Derinlik'] <= 20].sort_values('Derinlik').copy()
    for i in range(len(df_20m)):
        z = df_20m.iloc[i]['Derinlik']
        fs = df_20m.iloc[i]['FS']
        F = (1 - fs) if fs < 1 else 0
        w_z = 10 - 0.5 * z
        dz = 1.5 if i == 0 else (df_20m.iloc[i]['Derinlik'] - df_20m.iloc[i-1]['Derinlik'])
        lpi_total += F * w_z * dz
    return lpi_total

st.title("Automated Soil & Risk Analysis")
st.write("Automatic stress calculation and soil type estimation based on SPT values.")

gwt = st.slider("Groundwater Table Depth (m)", 0.0, 15.0, 2.0)
uploaded_file = st.file_uploader("Upload Data", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # Sütun İsimlerini Normalize Etme (Hata Çözücü)
        column_map = {
            'depth': 'Derinlik', 'derinlik': 'Derinlik', 'z': 'Derinlik',
            'n': 'SPT_N', 'spt': 'SPT_N', 'spt_n': 'SPT_N', 'spt n': 'SPT_N'
        }
        df.columns = [column_map.get(col.lower().strip(), col) for col in df.columns]

        # Otomatik Hesaplamalar
        df['Toplam_Gerilme'] = df['Derinlik'] * GAMMA_SOIL
        df['u'] = df['Derinlik'].apply(lambda z: (z - gwt) * GAMMA_WATER if z > gwt else 0)
        df['Etkili_Gerilme'] = df['Toplam_Gerilme'] - df['u']
        
        # Sıvılaşma Analizi
        df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
        df['CSR'] = 0.65 * AMAX * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
        df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme']).clip(upper=1.7)
        df['N1_60'] = df['SPT_N'] * df['Cn']
        df['CRR'] = np.exp((df['N1_60'] / 14.1) + (df['N1_60'] / 126)**2 - (df['N1_60'] / 23.6)**3 + (df['N1_60'] / 25.4)**4 - 2.8) * (6.9 * np.exp(-MW / 4) - 0.058)
        df['FS'] = df['CRR'] / df['CSR']
        
        # Zemin Tahmini
        df['Soil_Type'] = df['SPT_N'].apply(lambda x: get_soil_description(x)[0])

        # Skorlar
        lpi_score = calculate_lpi(df)
        st.metric("Liquefaction Potential Index (LPI)", f"{lpi_score:.2f}")

        # Görsel: Zemin Profili Özeti
        st.write("### Automated Soil Description")
        cols = st.columns(len(df))
        for i, row in df.iterrows():
            desc, color = get_soil_description(row['SPT_N'])
            st.markdown(f"<div style='background-color:{color}; color:white; padding:5px; margin:2px; border-radius:5px; font-size:10px; text-align:center;'>{row['Derinlik']}m<br>{desc}</div>", unsafe_allow_html=True)

        # Grafik
        st.write("### Risk Profile")
        fig, ax = plt.subplots(figsize=(6, 8))
        ax.plot(df['FS'], df['Derinlik'], marker='o', label='FS Profile')
        ax.axhline(y=gwt, color='blue', linestyle='--', label='Water Table')
        ax.axvspan(0, 1.0, color='red', alpha=0.1, label='Unstable')
        ax.set_ylim(max(df['Derinlik']) + 1, 0)
        ax.set_xlim(0, 3)
        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing file: {e}")
