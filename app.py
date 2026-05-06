import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="SPT Soil Analysis", layout="centered")

def get_spt_insight(n):
    """Engineering inferences based on SPT-N values"""
    if n < 4:
        return "Very Loose", "Critically Liquefiable", "#8B0000"
    elif n < 10:
        return "Loose", "High Liquefaction Potential", "#FF4B4B"
    elif n < 30:
        return "Medium Dense", "Marginal/Possible Liquefaction", "#FFA500"
    elif n < 50:
        return "Dense", "Low Liquefaction Risk", "#2E8B57"
    else:
        return "Very Dense", "Liquefaction Unlikely", "#006400"

# Header Section
st.title("Borehole Insight: SPT-Based Analysis")
st.write("Minimalist engineering inferences based on raw SPT values. No technical clutter, just data-driven results.")

# File Upload
uploaded_file = st.file_uploader("Upload Data File (CSV/Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    try:
        # Data Reading & Column Normalization
        df = pd.read_csv(uploaded_file, sep=None, engine='python') if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        column_map = {'depth': 'Depth', 'derinlik': 'Depth', 'z': 'Depth', 'n': 'SPT_N', 'spt': 'SPT_N', 'spt_n': 'SPT_N'}
        df.columns = [column_map.get(col.lower().strip(), col) for col in df.columns]

        if 'Depth' in df.columns and 'SPT_N' in df.columns:
            
            # --- OVERALL RISK SUMMARY ---
            avg_n = df['SPT_N'].mean()
            worst_n = df['SPT_N'].min()
            insight, risk_desc, color = get_spt_insight(worst_n)
            
            st.markdown(f"""
                <div style="background-color:{color}; padding:30px; border-radius:15px; text-align:center; color:white; margin-bottom:20px">
                    <h1 style="margin:0">OVERALL RISK: {risk_desc.upper()}</h1>
                    <p style="font-size:18px; margin:10px 0">Lowest SPT-N: {worst_n} | Average SPT-N: {avg_n:.2f}</p>
                </div>
            """, unsafe_allow_html=True)

            # --- ENGINEERING NOTES ---
            st.subheader("Engineering Inferences")
            with st.expander("Detailed Analysis Notes", expanded=True):
                if worst_n < 10:
                    st.write("**Observations:** Critically low SPT values detected. The soil profile is susceptible to contractive behavior under seismic loading.")
                    st.write("- **Bearing Capacity:** High risk of differential settlement.")
                    st.write("- **Stability:** Ground improvement is strongly recommended.")
                elif worst_n < 30:
                    st.write("**Observations:** Medium dense soil profile. Liquefaction may be triggered depending on peak ground acceleration.")
                    st.write("- **Action:** Detailed laboratory testing is advised.")
                else:
                    st.write("**Observations:** Competent soil profile with high stiffness.")

            # --- DEPTH-BASED LIST ---
            st.subheader("Depth-Based Characterization")
            for _, row in df.iterrows():
                char, risk, row_color = get_spt_insight(row['SPT_N'])
                st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; align-items: center; 
                                border-left: 10px solid {row_color}; background: #1e1e1e; padding: 12px; margin: 8px 0; border-radius: 8px">
                        <span style="font-weight: bold; color: #ddd">{row['Depth']} m</span>
                        <span style="color: {row_color}; font-weight: bold">N: {row['SPT_N']}</span>
                        <span style="font-style: italic; color: #bbb">{char}</span>
                        <span style="font-weight: bold; color: {row_color}">{risk}</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Column mismatch! Please ensure your file contains 'Depth' and 'SPT_N'.")

    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
else:
    st.info("Awaiting data upload for automated soil characterization.")
