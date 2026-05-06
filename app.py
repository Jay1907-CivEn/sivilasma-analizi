import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Classification Logic
def get_risk_level(fs):
    if fs < 1.0:
        return 'High Risk', '#FF4B4B'  # Red
    elif 1.0 <= fs < 1.2:
        return 'Moderate Risk', '#FFA500'  # Orange/Yellow
    else:
        return 'Low Risk', '#28A745'  # Green

def analyze_liquefaction(df, mw, amax):
    # Calculations
    df['rd'] = df['Derinlik'].apply(lambda z: 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z)
    df['CSR'] = 0.65 * amax * (df['Toplam_Gerilme'] / df['Etkili_Gerilme']) * df['rd']
    
    df['Cn'] = np.sqrt(100 / df['Etkili_Gerilme'])
    df['Cn'] = df['Cn'].clip(upper=1.7)
    df['N1_60'] = df['SPT_N'] * df['Cn']
    
    df['CRR'] = np.exp((df['N1_60'] / 14.1) + (df['N1_60'] / 126)**2 - (df['N1_60'] / 23.6)**3 + (df['N1_60'] / 25.4)**4 - 2.8)
    
    # MSF Calculation (Idriss & Boulanger 2014)
    msf = 6.9 * np.exp(-mw / 4) - 0.058
    df['CRR'] = df['CRR'] * msf
    
    df['FS'] = df['CRR'] / df['CSR']
    
    # Apply Risk Classification
    df['Risk Status'] = df['FS'].apply(lambda x: get_risk_level(x)[0])
    return df

# UI Configuration
st.set_page_config(page_title="Liquefaction Analysis Portal", layout="wide")
st.title("Liquefaction Risk Analysis Tool")

# Sidebar
st.sidebar.header("Analysis Parameters")
mw = st.sidebar.number_input("Earthquake Magnitude (Mw)", value=7.5, step=0.1)
amax = st.sidebar.number_input("Peak Ground Acceleration (amax/g)", value=0.30, step=0.05)

st.sidebar.subheader("Data Input")
upload = st.sidebar.file_uploader("Upload SPT CSV File", type="csv")

if upload is not None:
    df = pd.read_csv(upload)
else:
    # Default Dummy Data
    df = pd.DataFrame({
        'Derinlik': [1.5, 3.0, 4.5, 6.0, 7.5, 9.0],
        'SPT_N': [10, 12, 15, 13, 18, 20],
        'Toplam_Gerilme': [27, 54, 81, 108, 135, 162],
        'Etkili_Gerilme': [27, 45, 55, 65, 75, 85]
    })

results = analyze_liquefaction(df, mw, amax)

# Visuals
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Analysis Results Table")
    # Styling Table by Risk Level
    def style_risk(val):
        color = '#FF4B4B' if val == 'High Risk' else '#FFA500' if val == 'Moderate Risk' else '#28A745'
        return f'background-color: {color}; color: white; font-weight: bold'

    st.dataframe(results.style.applymap(style_risk, subset=['Risk Status']))

with col2:
    st.subheader("FS vs Depth Profile")
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.plot(results['FS'], results['Derinlik'], marker='o', color='blue', label='Factor of Safety (FS)')
    ax.axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Liquefaction Limit (FS=1.0)')
    ax.axvline(x=1.2, color='orange', linestyle=':', label='Threshold (FS=1.2)')
    
    ax.set_xlabel("Factor of Safety (FS)")
    ax.set_ylabel("Depth (m)")
    ax.set_ylim(max(results['Derinlik']) + 1, 0)
    ax.grid(True, alpha=0.3)
    ax.legend()
    st.pyplot(fig)
