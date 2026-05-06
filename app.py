import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- HESAPLAMA MODÜLÜ ---
def analiz_yap(df, mw, amax):
    # 1. CSR (Devirsel Gerilme Oranı)
    # rd: Gerilme Azaltma Katsayısı (Liao ve Whitman, 1986)
    df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
    df['CSR'] = 0.65 * amax * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
    
    # 2. CRR (Devirsel Direnç Oranı) - Idriss & Boulanger (2014)
    # Cn: Gerilme Düzeltme Katsayısı
    df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme'])
    df['Cn'] = df['Cn'].clip(upper=1.7) # Üst sınır 1.7
    
    df['N1_60'] = df['SPT_N'] * df['Cn']
    
    # Basitleştirilmiş CRR Formülü
    df['CRR'] = np.exp(
        (df['N1_60'] / 14.1) + 
        (df['N1_60'] / 126)**2 - 
        (df['N1_60'] / 23.6)**3 + 
        (df['N1_60'] / 25.4)**4 - 2.8
    )
    
    # MSF (Magnitude Scaling Factor) - Deprem Büyüklüğü Düzeltmesi
    msf = 6.9 * np.exp(-mw / 4) - 0.058
    df['CRR'] = df['CRR'] * msf
    
    # 3. Güvenlik Sayısı (FS)
    df['FS'] = df['CRR'] / df['CSR']
    return df

# --- WEB ARAYÜZÜ ---
st.set_page_config(page_title="SPT Sıvılaşma Analizi", layout="wide")

st.title("🏗️ SPT Temelli Sıvılaşma Analiz Portalı")
st.markdown("Bu araç, SPT verilerini kullanarak derinliğe bağlı sıvılaşma güvenlik sayısını hesaplar.")

# Yan Panel (Parametreler)
st.sidebar.header("⚙️ Analiz Parametreleri")
mw = st.sidebar.number_input("Deprem Büyüklüğü (Mw)", value=7.5, step=0.1)
amax = st.sidebar.number_input("Tasarım İvmesi (amax/g)", value=0.30, step=0.05)

st.sidebar.subheader("Veri Girişi")
upload = st.sidebar.file_uploader("SPT CSV Dosyası Yükle", type="csv")

# Veri Hazırlığı
if upload is not None:
    df = pd.read_csv(upload)
else:
    st.info("Aşağıda örnek veri seti görüyorsunuz. Kendi verilerinizi soldaki menüden yükleyebilirsiniz.")
    df = pd.DataFrame({
        'Derinlik': [1.5, 3.0, 4.5, 6.0, 7.5, 9.0, 10.5],
        'SPT_N': [10, 12, 15, 13, 18, 20, 22],
        'Toplam_Gerilme': [27, 54, 81, 108, 135, 162, 189],
        'Etkili_Gerilme': [27, 45, 55, 65, 75, 85, 95]
    })

# Analizi Çalıştır
results = analiz_yap(df, mw, amax)

# --- GÖRSELLEŞTİRME ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("📋 Analiz Sonuçları")
    # FS < 1.0 olanları kırmızı işaretle
    st.dataframe(results[['Derinlik', 'SPT_N', 'CSR', 'CRR', 'FS']].style.highlight_between(
        left=0, right=1.0, subset=['FS'], color='#FFCCCC'
    ))

with c2:
    st.subheader("📈 FS vs Derinlik Grafiği")
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.plot(results['FS'], results['Derinlik'], marker='o', linestyle='-', color='blue', label='Güvenlik Sayısı (FS)')
    ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Sıvılaşma Sınırı (FS=1)')
    
    ax.set_xlabel("Güvenlik Sayısı (FS)")
    ax.set_ylabel("Derinlik (m)")
    ax.set_ylim(max(results['Derinlik']) + 1, 0) # Derinlik aşağı doğru artar
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend()
    st.pyplot(fig)

# İndirme Alanı
st.download_button(
    label="Sonuçları Excel/CSV Olarak İndir",
    data=results.to_csv(index=False).encode('utf-8'),
    file_name='sivilasmas_analiz_sonuclari.csv',
    mime='text/csv',
)