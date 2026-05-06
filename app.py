import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page Setup
st.set_page_config(page_title="Auto-Stress Liquefaction Tool", layout="centered")

# Sabit Mühendislik Değerleri
GAMMA_SOIL = 19.0  # kN/m3 (Zemin ortalama birim hacim ağırlığı)
GAMMA_WATER = 9.81 # kN/m3 (Suyun birim hacim ağırlığı)
MW_DEFAULT = 7.5   # Design Earthquake Magnitude
AMAX_DEFAULT = 0.30 # Design Acceleration

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

def get_risk_grade(lpi):
    if lpi == 0: return "None", "#28A745"
    elif lpi <= 5: return "Low Risk", "#8CC63F"
    elif lpi <= 15: return "Moderate Risk", "#FFC107"
    else: return "High Risk", "#DC3545"

# --- UI ---
st.title("Automated Liquefaction Risk Assessment")
st.write("Enter the groundwater level and upload your SPT-N values. Stresses are calculated automatically.")

# Kullanıcıdan sadece Su Seviyesi girdisi alıyoruz
gwt = st.slider("Groundwater Table Depth (m)", 0.0, 10.0, 2.0)

uploaded_file = st.file_uploader("Upload CSV/Excel (Needs 'Derinlik' and 'SPT_N' columns)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # 1. OTOMATİK GERİLME HESAPLARI (Mühendislik Mutfağı)
        # Toplam Gerilme: sigma_v = derinlik * gamma_zemin
        df['Toplam_Gerilme'] = df['Derinlik'] * GAMMA_SOIL
        
        # Boşluk Suyu Basıncı (u): Eğer derinlik > su seviyesi ise hesapla
        df['u'] = df['Derinlik'].apply(lambda z: (z - gwt) * GAMMA_WATER if z > gwt else 0)
        
        # Etkili Gerilme: sigma_v' = sigma_v - u
        df['Etkili_Gerilme'] = df['Toplam_Gerilme'] - df['u']

        # 2. SIVILAŞMA ANALİZİ (Idriss & Boulanger 2014)
        df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
        df['CSR'] = 0.65 * AMAX_DEFAULT * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
        df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme']).clip(upper=1.7)
        df['N1_60'] = df['SPT_N'] * df['Cn']
        df['CRR_base'] = np.exp((df['N1_60'] / 14.1) + (df['N1_60'] / 126)**2 - (df['N1_60'] / 23.6)**3 + (df['N1_60'] / 25.4)**4 - 2.8)
        msf = 6.9 * np.exp(-MW_DEFAULT / 4) - 0.058
        df['FS'] = df['CRR_base'] * msf
        
        # 3. SONUÇLAR VE GÖRSELLEŞTİRME
        lpi_score = calculate_lpi(df)
        risk_text, risk_color = get_risk_grade(lpi_score)

        st.markdown(f"""
            <div style="background-color:{risk_color}; padding:25px; border-radius:15px; text-align:center; color:white; font-family:sans-serif">
                <h2 style="margin:0">OVERALL ANALYSIS: {risk_text}</h2>
                <p style="font-size:28px; margin:10px 0">LPI Score: {lpi_score:.2f}</p>
                <p style="font-size:16px; margin:0; opacity:0.8">Automatic Stress Calculation Enabled (GWT: {gwt}m)</p>
            </div>
        """, unsafe_allow_html=True)

        # Grafik
        st.write("### Soil Factor of Safety Profile")
        fig, ax = plt.subplots(figsize=(6, 8))
        ax.plot(df['FS'], df['Derinlik'], marker='o', color='#1f77b4', linewidth=2, label='FS (Safety Factor)')
        
        # Risk Arka Planı
        ax.axvspan(0, 1.0, color='#DC3545', alpha=0.15, label='High Risk Zone')
        ax.axvspan(1.0, 1.2, color='#FFC107', alpha=0.1, label='Marginal Zone')
        
        # Su Seviyesi Göstergesi (Grafikte mavi kesikli çizgi)
        ax.axhline(y=gwt, color='blue', linestyle='--', alpha=0.5, label=f'Water Table ({gwt}m)')
        
        ax.set_ylim(max(df['Derinlik']) + 1, 0)
        ax.set_xlim(0, 3)
        ax.set_xlabel("Factor of Safety (FS)")
        ax.set_ylabel("Depth (m)")
        ax.legend(loc='lower right')
        ax.grid(True, alpha=0.2)
        st.pyplot(fig)

    except Exception as e:
        st.error("Missing Data: Please ensure your file has 'Derinlik' and 'SPT_N' columns.")
else:
    st.info("Awaiting data file for automatic stress and risk analysis.")
