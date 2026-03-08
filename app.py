import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Vermi-IoT Sentinel - Gestão de GEE", layout="wide")

## --- CABEÇALHO E ALINHAMENTO AO EDITAL ---
st.title("🌱 Vermi-IoT Sentinel")
st.subheader("Sistema de Monitoramento Remoto de Emissões GEE (ODS 12 e 13)")
st.markdown(f"**Protótipo para o Edital CONIF/CONTIC nº 02/2026** [cite: 5, 6]")

# ---- PAINEL LATERAL: PARÂMETROS TÉCNICOS (Obrigatórios para o cálculo) ----
with st.sidebar:
    st.header("⚙️ Configurações da Unidade")
    area_chamber = st.number_input("Área da câmara (m²)", value=0.13, format="%.2f")
    flow_l_min = st.number_input("Vazão de arraste (L/min)", value=5.0, format="%.2f")
    Q = flow_l_min / 1000  # m³/min
    
    st.divider()
    st.write("**Parâmetros da Pilha (Balanço de Massa)**")
    initial_mass = st.number_input("Massa inicial de resíduos (kg)", value=1500.0)
    moisture = st.number_input("Umidade (%)", value=50.8)
    toc = st.number_input("Teor inicial de C total (%)", value=43.6)
    tn = st.number_input("Teor inicial de N total (g kg⁻¹)", value=14.2)
    
    st.divider()
    st.write("**Fatores Globais (GWP)**")
    gwp_ch4 = st.number_input("GWP CH₄", value=25)
    gwp_n2o = st.number_input("GWP N₂O", value=298)

# ---- ABA 1: CONECTIVIDADE E LEITURAS REMOTAS ----
st.write("### 📡 Central de Recebimento de Dados (IoT)")
st.info("Este módulo centraliza informações de equipamentos instalados em diferentes pontos da RFEPCT[cite: 9, 16].")

def fetch_iot_readings():
    """Simula a recepção automática de dados via conectividade"""
    nodes = ["Nódulo-A (Campus)", "Nódulo-B (Rural)", "Nódulo-C (Laboratório)"]
    schedule = [0, 3, 7, 14, 21, 30, 45, 50]
    data_list = []
    for node in nodes:
        # Valores baseados na curva do artigo com variação randômica (ruído de sensor)
        ch4_vals = [150.0, 100.0, 80.0, 50.0, 30.0, 20.0, 10.0, 5.0]
        n2o_vals = [2.0, 4.0, 6.0, 5.0, 3.0, 2.0, 1.0, 0.5]
        for i, day in enumerate(schedule):
            data_list.append({
                "day": day,
                "node_id": node,
                "CH4": ch4_vals[i] + np.random.normal(0, 3),
                "N2O": n2o_vals[i] + np.random.normal(0, 0.1),
                "timestamp": datetime.now() - timedelta(days=(50-day))
            })
    return pd.DataFrame(data_list)

if "iot_data" not in st.session_state:
    st.session_state.iot_data = pd.DataFrame()

if st.button("🔄 Sincronizar Leituras dos Equipamentos Remotos"):
    st.session_state.iot_data = fetch_iot_readings()
    st.success("Dados sincronizados com sucesso via protocolo de conectividade!")

df = st.session_state.iot_data.copy()

if not df.empty:
    # ---- CÁLCULOS TÉCNICOS DETALHADOS ----
    # 1. Fluxos horários e diários
    df["Flux_CH4_h"] = (df["CH4"] * Q * 60) / area_chamber
    df["Flux_N2O_h"] = (df["N2O"] * Q * 60) / area_chamber
    df["Flux_CH4_d"] = df["Flux_CH4_h"] * 24
    df["Flux_N2O_d"] = df["Flux_N2O_h"] * 24

    # 2. Integração Temporal por Nódulo (Área sob a curva)
    nodes_summary = []
    for node in df["node_id"].unique():
        node_df = df[df["node_id"] == node].sort_values("day")
        cum_ch4_mg = np.trapezoid(node_df["Flux_CH4_d"], node_df["day"])
        cum_n2o_mg = np.trapezoid(node_df["Flux_N2O_d"], node_df["day"])
        nodes_summary.append({
            "node_id": node, 
            "cum_ch4_mg_m2": cum_ch4_mg, 
            "cum_n2o_mg_m2": cum_n2o_mg
        })
    
    summary_df = pd.DataFrame(nodes_summary)
    
    # 3. Balanço de Massa Médio da Planta
    avg_ch4_mg_m2 = summary_df["cum_ch4_mg_m2"].mean()
    avg_n2o_mg_m2 = summary_df["cum_n2o_mg_m2"].mean()
    
    # Extrapolação para a massa total
    dry_matter = initial_mass * (1 - moisture/100)
    initial_C_kg = dry_matter * (toc / 100)
    initial_N_kg = (tn / 1000) * dry_matter
    
    total_ch4_kg = (avg_ch4_mg_m2 * 1.5) / 1e6 # 1.5m² área pilha
    total_n2o_kg = (avg_n2o_mg_m2 * 1.5) / 1e6
    
    ch4_c_kg = total_ch4_kg * (12/16)
    n2o_n_kg = total_n2o_kg * (28/44)
    
    ch4_c_perc = (ch4_c_kg / initial_C_kg) * 100
    n2o_n_perc = (n2o_n_kg / initial_N_kg) * 100
    
    total_co2eq = (total_ch4_kg * gwp_ch4) + (total_n2o_kg * gwp_n2o)
    ghg_per_ton = (total_co2eq / dry_matter) * 1000

    # ---- ABA 2: VISUALIZAÇÃO E RESULTADOS ----
    st.divider()
    st.write("### 📊 Análise Consolidada das Emissões")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Perda CH₄-C", f"{ch4_c_perc:.3f}%")
    m2.metric("Perda N₂O-N", f"{n2o_n_perc:.3f}%")
    m3.metric("Total CO₂eq", f"{total_co2eq:.2f} kg")
    m4.metric("Pegada GEE/t MS", f"{ghg_per_ton:.2f} kg")

    # Gráficos
    st.write("#### Monitoramento em Tempo Real por Ponto de Coleta")
    fig_line = px.line(df, x="day", y="Flux_CH4_h", color="node_id", markers=True,
                       title="Fluxo de Metano (mg/m².h) - Monitoramento Remoto")
    st.plotly_chart(fig_line, use_container_width=True)

    # Tabela de dados brutos para auditoria (Item 3.1.D do edital)
    with st.expander("🔎 Ver Leituras de Sensores e Cálculos por Amostra"):
        st.dataframe(df[["day", "node_id", "CH4", "N2O", "Flux_CH4_h", "Flux_N2O_h"]])

else:
    st.warning("Nenhum dado recebido. Clique no botão de sincronização para ler os equipamentos remotos.")
