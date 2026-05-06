import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(page_title="Liquefaction Risk", layout="centered")

def get_spt_insight(n):
    """Engineering inferences based on SPT-N values with color scale"""
    if n < 4:
        return "Very Loose", "Critically Liquefiable", "#8B0000" # Dark Red
    elif n < 10:
        return "Loose", "High Risk", "#FF4B4B" # Red
    elif n < 30:
        return "Medium Dense", "Moderate Risk", "#FFA500" # Orange/Yellow
    elif n < 50:
        return "Dense", "Low Risk", "#2E8B57" # Green
    else:
        return "Very Dense", "Negligible Risk", "#006400" # Dark Green

# Header Section - Short and Professional
st.title("Liquefaction Risk")

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
            # It takes the minimum SPT-N to define the most critical risk level color
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
                    st.write("**Observations:** Critically low SPT values detected. High susceptibility to liquefaction.")
                    st.write("- **Bearing Capacity:** Risk of significant settlement.")
                    st.write("- **Stability:** Ground improvement is likely required.")
                elif worst_n < 30:
                    st.write("**Observations:** Medium dense soil. Liquefaction potential is moderate.")
                    st.write("- **Action:** Site-specific seismic analysis recommended.")
                else:
                    st.write("**Observations:** Dense soil profile. Generally safe from liquefaction.")

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
            st.error("Column mismatch! Ensure file contains 'Depth' and 'SPT_N'.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Awaiting data upload...")
