import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Configuração da Página para um Dashboard Profissional
st.set_page_config(page_title="Vermi-IoT Sentinel", layout="wide")

# --- CABEÇALHO ALINHADO AO EDITAL (Itens 1.1 e 3.1) ---
st.title("🌱 Vermi-IoT Sentinel")
st.subheader("Monitoramento de GEE em Vermicompostagem via Conectividade IoT")
st.markdown("""
**Objetivo:** Seleção de protótipos de soluções para o desenvolvimento sustentável[cite: 7].
**ODS Vinculados:** ODS 12 e 13.
**Nível de Maturidade:** TRL 4 (Protótipo validado em laboratório)[cite: 51].
""")

# --- SIMULAÇÃO DE RECEPÇÃO DE DADOS REMOTOS (Conectividade Item 4.6) ---
def fetch_iot_data():
    """Simula a telemetria de sensores instalados em pontos remotos"""
    nodes = ["Campus Norte", "Campus Sul", "Unidade Experimental"]
    data_list = []
    now = datetime.now()
    
    for node in nodes:
        for i in range(5): 
            data_list.append({
                "timestamp": now - timedelta(hours=i*2),
                "node_id": node,
                "ch4_mg_m3": np.random.uniform(80, 160),
                "n2o_mg_m3": np.random.uniform(2, 6),
                "temp_c": np.random.uniform(25, 35)
            })
    return pd.DataFrame(data_list)

# --- PROCESSAMENTO DOS DADOS (Baseado em Yang et al. 2017) ---
df_iot = fetch_iot_data()

# Constantes para cálculo de Impacto Tecnológico (Item 3.1.D1)
GWP_CH4, GWP_N2O = 25, 298
AREA_CHAMBER, FLOW_L_MIN = 0.13, 5.0
Q = FLOW_L_MIN / 1000 # m³/min

def process_metrics(df):
    # Fluxo (mg/m².h)
    df["flux_ch4"] = (df["ch4_mg_m3"] * Q * 60) / AREA_CHAMBER
    df["flux_n2o"] = (df["n2o_mg_m3"] * Q * 60) / AREA_CHAMBER
    # CO2 equivalente acumulado
    df["co2_eq_kg"] = ((df["flux_ch4"] * GWP_CH4) + (df["flux_n2o"] * GWP_N2O)) / 1e6
    return df

df_final = process_metrics(df_iot)

# --- INTERFACE DE MONITORAMENTO ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Nódulos Remotos", "3", "Online")
with col2:
    st.metric("Total CO₂eq (kg)", f"{df_final['co2_eq_kg'].sum():.4f}")
with col3:
    st.metric("Status TRL", "Nível 4", "Em Validação")

st.divider()

st.write("### 📈 Monitoramento de Fluxo por Unidade")
fig = px.line(df_final, x="timestamp", y="flux_ch4", color="node_id", 
              labels={"flux_ch4": "Fluxo CH₄ (mg/m².h)"})
st.plotly_chart(fig, use_container_width=True)

with st.expander("📋 Ver Log de Telemetria (Dados de Conectividade)"):
    st.dataframe(df_final[['timestamp', 'node_id', 'ch4_mg_m3', 'n2o_mg_m3', 'temp_c']])
