import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Configuração da Página para um visual profissional (Dashboard)
st.set_page_config(page_title="Vermi-IoT Sentinel", layout="wide")

## --- CABEÇALHO ALINHADO AO EDITAL ---
st.title("🌱 Vermi-IoT Sentinel")
st.subheader("Monitoramento de GEE em Vermicompostagem Distribuída via IoT")
st.markdown("""
**ODS Prioritário:** 12 (Consumo e Produção Responsáveis) e 13 (Ação Contra a Mudança Global do Clima).  
**Conectividade:** Integração de sensores remotos via protocolo de telemetria para cálculo de pegada de carbono em tempo real.
""")

---

# 📡 SIMULAÇÃO DE RECEPÇÃO DE DADOS (O "Coração" IoT)
# No mundo real, aqui leríamos de um banco de dados (Firebase/AWS) ou API.
def fetch_iot_data():
    """Simula a recepção de dados de 3 unidades de compostagem remotas"""
    nodes = ["Nódulo-Sul (Campus A)", "Nódulo-Norte (Campus B)", "Nódulo-Central (Experimental)"]
    data_list = []
    now = datetime.now()
    
    for node in nodes:
        for i in range(10): # Últimas 10 leituras
            data_list.append({
                "timestamp": now - timedelta(hours=i),
                "node_id": node,
                "ch4_mg_m3": np.random.uniform(50, 150),
                "n2o_mg_m3": np.random.uniform(1, 5),
                "temp_c": np.random.uniform(25, 45)
            })
    return pd.DataFrame(data_list)

# Interface Principal
col_metrics = st.columns(4)
df_iot = fetch_iot_data()

# --- CÁLCULOS TÉCNICOS (Baseados no Edital e Yang et al. 2017) ---
# Constantes de Conversão
GWP_CH4, GWP_N2O = 25, 298
AREA_CHAMBER, FLOW_L_MIN = 0.13, 5.0
Q = FLOW_L_MIN / 1000 # m3/min

def calculate_emissions(df):
    # Cálculo de Fluxo (mg/m2.h)
    df["flux_ch4"] = (df["ch4_mg_m3"] * Q * 60) / AREA_CHAMBER
    df["flux_n2o"] = (df["n2o_mg_m3"] * Q * 60) / AREA_CHAMBER
    # CO2 Equivalente total (kg) - Simplificado para o Dashboard
    df["co2_eq"] = ((df["flux_ch4"] * GWP_CH4) + (df["flux_n2o"] * GWP_N2O)) / 1e6
    return df

df_processed = calculate_emissions(df_iot)

# --- DASHBOARD DE MONITORAMENTO ---
with col_metrics[0]:
    st.metric("Nódulos Ativos", "03", "Conectado via 4G/LoRaWAN")
with col_metrics[1]:
    total_co2 = df_processed["co2_eq"].sum()
    st.metric("Total CO₂eq Capturado (Estimado)", f"{total_co2:.4f} kg")
with col_metrics[2]:
    avg_temp = df_processed["temp_c"].mean()
    st.metric("Temperatura Média", f"{avg_temp:.1f} °C")
with col_metrics[3]:
    st.metric("Status do Sistema", "TRL 4", "Protótipo Funcional")

st.markdown("---")

# Visualização Geográfica/Espacial das Emissões
st.write("### 📊 Emissões por Unidade de Tratamento")
fig_flux = px.line(df_processed, x="timestamp", y="flux_ch4", color="node_id", 
                  title="Fluxo de Metano (CH₄) em Tempo Real por Localidade",
                  labels={"flux_ch4": "Fluxo (mg/m².h)", "timestamp": "Hora da Leitura"})
st.plotly_chart(fig_flux, use_container_width=True)

# Expansor de Dados Brutos para Auditoria (Importante para o item 3.1.D do edital)
with st.expander("🔍 Auditoria de Dados Brutos (Telemetria IoT)"):
    st.dataframe(df_iot.style.highlight_max(axis=0))

st.info("💡 Este protótipo utiliza o protocolo de cálculo de Yang et al. (2017) para transformar concentrações de sensores em fluxos de emissão.")
