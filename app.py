import streamlit as st
import pandas as pd

# Sayfa Tasarımı (Sade ve Minimalist)
st.set_page_config(page_title="SPT Inferences", layout="centered")

def get_spt_insight(n):
    """Sadece SPT-N değerine bakarak mühendislik çıkarımları"""
    if n < 4:
        return "Çok Gevşek (Very Loose)", "Kritik Derecede Sıvılaşabilir", "#8B0000" # Koyu Kırmızı
    elif n < 10:
        return "Gevşek (Loose)", "Yüksek Sıvılaşma Potansiyeli", "#FF4B4B" # Kırmızı
    elif n < 30:
        return "Orta Sıkı (Medium Dense)", "Sınırlı/Olası Sıvılaşma", "#FFA500" # Turuncu
    elif n < 50:
        return "Sıkı (Dense)", "Düşük Sıvılaşma Riski", "#2E8B57" # Yeşil
    else:
        return "Çok Sıkı (Very Dense)", "Sıvılaşma Beklenmez", "#006400" # Koyu Yeşil

st.title("Borehole Insight: SPT-Based Analysis")
st.write("Teknik karmaşa yok. Sadece SPT-N verilerine dayalı zemin davranış çıkarımları.")

# Dosya Yükleme
uploaded_file = st.file_uploader("Sadece Veri Dosyasını Yükle (CSV/Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Veri Okuma ve Sütun Düzenleme
        df = pd.read_csv(uploaded_file, sep=None, engine='python') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        column_map = {'depth': 'Derinlik', 'derinlik': 'Derinlik', 'z': 'Derinlik', 'n': 'SPT_N', 'spt': 'SPT_N', 'spt_n': 'SPT_N'}
        df.columns = [column_map.get(col.lower().strip(), col) for col in df.columns]

        if 'Derinlik' in df.columns and 'SPT_N' in df.columns:
            
            # --- GLOBAL RİSK SKALASI (Summary Card) ---
            avg_n = df['SPT_N'].mean()
            worst_n = df['SPT_N'].min()
            insight, risk_desc, color = get_spt_insight(worst_n) # En kötü noktaya odaklanıyoruz
            
            st.markdown(f"""
                <div style="background-color:{color}; padding:30px; border-radius:15px; text-align:center; color:white; margin-bottom:20px">
                    <h1 style="margin:0">GENEL RİSK: {risk_desc.upper()}</h1>
                    <p style="font-size:20px; margin:10px 0">En Düşük SPT-N: {worst_n} | Ortalama SPT-N: {avg_n:.2f}</p>
                </div>
            """, unsafe_allow_html=True)

            # --- MÜHENDİSLİK ÇIKARIMLARI (Bullet Points) ---
            st.subheader("📊 Zemin Davranış Çıkarımları")
            
            # Dinamik çıkarımlar yapalım
            with st.expander("Detaylı Mühendislik Notları", expanded=True):
                if worst_n < 10:
                    st.error(f"⚠️ **Kritik Gözlem:** Derinlik boyunca {worst_n} gibi çok düşük SPT değerleri tespit edilmiştir. Bu, zeminin sismik sarsıntı altında hacim daralmasına (contractive behavior) meyilli olduğunu gösterir.")
                    st.write("- **Taşıma Gücü:** Temel altı zeminlerde ani oturma riski mevcut.")
                    st.write("- **Sıvılaşma:** Su varlığı durumunda zemin mukavemetini tamamen kaybedebilir.")
                elif worst_n < 30:
                    st.warning(f"🔔 **Gözlem:** Zemin orta sıkı karakterdedir. Deprem yükü şiddetine bağlı olarak sıvılaşma tetiklenebilir.")
                    st.write("- **Öneri:** Zemin ıslahı (kompaksiyon vb.) değerlendirilebilir.")
                else:
                    st.success("✅ **Gözlem:** Zemin profili oldukça sıkı ve güvenli bir yapı sunmaktadır.")

            # --- DERİNLİĞE GÖRE SKALA (Table-Like View) ---
            st.subheader("Depth-Based Vulnerability")
            for _, row in df.iterrows():
                char, risk, row_color = get_spt_insight(row['SPT_N'])
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                border-left: 10px solid {row_color}; background: #1e1e1e; padding: 10px; margin: 5px 0; border-radius: 5px">
                        <span style="font-weight: bold; color: #ddd">{row['Derinlik']} m</span>
                        <span style="color: {row_color}">SPT-N: {row['SPT_N']}</span>
                        <span style="font-style: italic; color: #bbb">{char}</span>
                        <span style="font-weight: bold; color: {row_color}">{risk}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Dosyada 'Derinlik' ve 'SPT_N' sütunlarını bulamadım.")

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
else:
    st.info("Analiz için bir veri dosyası yükle. Sadece SPT sayılarına bakarak ne olduğunu söyleyeceğim.")
