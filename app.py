import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Sayfa Yapılandırması
st.set_page_config(page_title="Liquefaction Risk Report", layout="centered")

# Sabit Parametreler (Arka planda çalışır)
MW = 7.5
AMAX = 0.30

def calculate_lpi(df):
    """Liquefaction Potential Index (LPI) Hesabı - Iwasaki et al. (1982)"""
    lpi_total = 0
    # Sadece ilk 20 metre dikkate alınır
    df_20m = df[df['Derinlik'] <= 20].sort_values('Derinlik').copy()
    
    for i in range(len(df_20m)):
        z = df_20m.iloc[i]['Derinlik']
        fs = df_20m.iloc[i]['FS']
        
        # F katsayısı: FS < 1 ise F = 1-FS, değilse 0
        F = (1 - fs) if fs < 1 else 0
        # w(z) ağırlık fonksiyonu: Derinlik arttıkça etkisi azalır
        w_z = 10 - 0.5 * z
        
        # Basitleştirilmiş integral adımı (Delta z = noktalar arası mesafe)
        dz = 1.5 if i == 0 else (df_20m.iloc[i]['Derinlik'] - df_20m.iloc[i-1]['Derinlik'])
        lpi_total += F * w_z * dz
        
    return lpi_total

def get_risk_grade(lpi):
    """LPI Değerine Göre Renk Skalası"""
    if lpi == 0:
        return "None / Very Low", "#28A745" # Yeşil
    elif 0 < lpi <= 5:
        return "Low Risk", "#8CC63F"        # Açık Yeşil
    elif 5 < lpi <= 15:
        return "Moderate Risk", "#FFC107"   # Sarı/Turuncu
    else:
        return "High Risk", "#DC3545"       # Kırmızı

# Arayüz
st.title("Liquefaction Risk Assessment")
st.write("Upload your borehole data (Excel or CSV) to generate a professional risk report.")

uploaded_file = st.file_uploader("Select Data File", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Veri Okuma
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        
        # 1. Mühendislik Hesaplamaları
        df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
        df['CSR'] = 0.65 * AMAX * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
        df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme']).clip(upper=1.7)
        df['N1_60'] = df['SPT_N'] * df['Cn']
        df['CRR_base'] = np.exp((df['N1_60'] / 14.1) + (df['N1_60'] / 126)**2 - (df['N1_60'] / 23.6)**3 + (df['N1_60'] / 25.4)**4 - 2.8)
        df['FS'] = df['CRR_base'] * (6.9 * np.exp(-MW / 4) - 0.058)
        
        # 2. Bütünsel Risk (LPI) Hesabı
        lpi_score = calculate_lpi(df)
        risk_text, risk_color = get_risk_grade(lpi_score)
        avg_fs = df['FS'].mean()

        # 3. Özet Dashboard (Kart Yapısı)
        st.markdown(f"""
            <div style="background-color:{risk_color}; padding:20px; border-radius:10px; text-align:center; color:white">
                <h2 style="margin:0">OVERALL RISK: {risk_text}</h2>
                <p style="font-size:24px; margin:5px">LPI Score: {lpi_score:.2f}</p>
                <p style="font-size:18px; margin:0">Average Safety Factor: {avg_fs:.2f}</p>
            </div>
        """, unsafe_allow_html=True)

        # 4. Grafik Gösterimi
        st.write("### Soil Sensitivity Profile")
        fig, ax = plt.subplots(figsize=(7, 8))
        ax.plot(df['FS'], df['Derinlik'], marker='o', color='#1f77b4', linewidth=2.5, label='FS Profile')
        
        # Arka plan renk skalası (FS ekseninde)
        ax.axvspan(0, 1.0, color='#DC3545', alpha=0.2, label='Unstable')
        ax.axvspan(1.0, 1.2, color='#FFC107', alpha=0.15, label='Marginal')
        ax.axvspan(1.2, 3.0, color='#28A745', alpha=0.1, label='Stable')
        
        ax.set_xlabel("Factor of Safety (FS)", fontsize=10)
        ax.set_ylabel("Depth (m)", fontsize=10)
        ax.set_ylim(max(df['Derinlik']) + 1, 0)
        ax.set_xlim(0, 3)
        ax.grid(True, linestyle='--', alpha=0.4)
        ax.legend(loc='lower right')
        
        st.pyplot(fig)

    except Exception as e:
        st.error(f"Error: Please check your column names. (Derinlik, SPT_N, Toplam_Gerilme, Etkili_Gerilme)")

else:
    st.info("Waiting for data upload...")
