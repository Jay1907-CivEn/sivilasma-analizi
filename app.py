import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sayfa Ayarları
st.set_page_config(page_title="Geotechnical Risk Report", layout="wide")

# Mühendislik Katsayıları
GAMMA_SOIL = 19.0 
GAMMA_WATER = 9.81
MW = 7.5
AMAX = 0.30

def get_soil_description(n):
    if n < 4: return "Very Loose Sand", "#B22222"
    elif n < 10: return "Loose Sand", "#FF4500"
    elif n < 30: return "Medium Dense Sand", "#FFD700"
    elif n < 50: return "Dense Sand", "#9ACD32"
    else: return "Very Dense Sand", "#228B22"

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

st.title("Professional Liquefaction Risk Analysis")
st.write("Automatic Stress Calculation & Soil Characterization Portal")

# Kullanıcı Parametreleri
gwt = st.sidebar.slider("Groundwater Table Depth (m)", 0.0, 15.0, 2.0)
uploaded_file = st.file_uploader("Upload Your Borehole Data", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # AYRAÇ SORUNUNU ÇÖZME: sep=None ve engine='python' ayraç tipini otomatik algılar
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='utf-8-sig')
        else:
            df = pd.read_excel(uploaded_file)
        
        # Daha Kapsamlı Sütun Eşleştirme
        column_map = {
            'depth': 'Derinlik', 'derinlik': 'Derinlik', 'z': 'Derinlik', 'm': 'Derinlik',
            'n': 'SPT_N', 'spt': 'SPT_N', 'spt_n': 'SPT_N', 'spt n': 'SPT_N', 'n30': 'SPT_N', 'darbe': 'SPT_N'
        }
        df.columns = [column_map.get(col.lower().strip(), col) for col in df.columns]

        if 'Derinlik' not in df.columns or 'SPT_N' not in df.columns:
            st.error(f"Sütunlar bulunamadı! Mevcut sütunlar: {list(df.columns)}")
            st.info("Lütfen CSV dosyanızdaki başlıkların 'Derinlik' ve 'SPT_N' olduğundan emin olun.")
        else:
            # Hesaplamalar
            df['Toplam_Gerilme'] = df['Derinlik'] * GAMMA_SOIL
            df['u'] = df['Derinlik'].apply(lambda z: (z - gwt) * GAMMA_WATER if z > gwt else 0)
            df['Etkili_Gerilme'] = df['Toplam_Gerilme'] - df['u']
            df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
            df['CSR'] = 0.65 * AMAX * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
            df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme']).clip(upper=1.7)
            df['N1_60'] = df['SPT_N'] * df['Cn']
            df['CRR'] = np.exp((df['N1_60'] / 14.1) + (df['N1_60'] / 126)**2 - (df['N1_60'] / 23.6)**3 + (df['N1_60'] / 25.4)**4 - 2.8) * (6.9 * np.exp(-MW / 4) - 0.058)
            df['FS'] = df['CRR'] / df['CSR']
            
            # Görselleştirme
            lpi_score = calculate_lpi(df)
            st.metric("Overall LPI Score", f"{lpi_score:.2f}")

            c1, c2 = st.columns([1, 1])
            with c1:
                st.write("### Calculated Stresses")
                st.dataframe(df[['Derinlik', 'Toplam_Gerilme', 'Etkili_Gerilme', 'FS']].style.format("{:.2f}"))

            with c2:
                st.write("### Factor of Safety Profile")
                fig, ax = plt.subplots(figsize=(5, 7))
                ax.plot(df['FS'], df['Derinlik'], marker='o', color='#1f77b4', linewidth=2)
                ax.axhline(y=gwt, color='blue', linestyle='--', label=f'Water Table: {gwt}m')
                ax.axvspan(0, 1.0, color='red', alpha=0.1)
                ax.set_ylim(max(df['Derinlik']) + 1, 0)
                ax.set_xlim(0, 3)
                ax.set_xlabel("FS")
                ax.set_ylabel("Depth (m)")
                ax.legend()
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Hata oluştu: {e}")

else:
    st.info("Lütfen analiz için bir dosya yükleyin.")
