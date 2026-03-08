import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.title("Vermicompost GHG Monitoring Prototype")

st.header("Experiment setup")
area = st.number_input("Chamber area (m²)", value=0.13, format="%.2f")
flow = st.number_input("Sweep air flow (L/min)", value=5.0, format="%.2f")
start_date = st.date_input("Experiment start date", value=datetime.now())
Q = flow / 1000  # converte L/min para m³/min

# Dias de medição (baseado no artigo)
schedule = [0, 3, 7, 14, 21, 30, 45, 60]
st.header("Sampling schedule")
st.write(schedule)

# Inicializa o banco de dados se não existir
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["day", "CH4", "N2O", "timestamp"])

# --- Botão para carregar dados de exemplo do artigo ---
if st.button("Carregar dados de exemplo do artigo"):
    # Valores aproximados extraídos das Figuras 2A e 2B (vermicompostagem)
    # CH4 (mg/m³) e N2O (mg/m³) – convertidos aproximadamente dos fluxos apresentados
    exemplo = pd.DataFrame({
        "day": schedule,
        "CH4": [0.8, 0.6, 0.4, 0.3, 0.2, 0.1, 0.05, 0.02],   # valores simulados
        "N2O": [0.15, 0.25, 0.30, 0.28, 0.20, 0.12, 0.08, 0.05],
        "timestamp": [datetime.now()] * len(schedule)
    })
    st.session_state.data = exemplo
    st.success("Dados de exemplo carregados!")

st.header("Register measurement")
day = st.selectbox("Sampling day", schedule)

# Campos com valores padrão (baseados no artigo)
ch4_default = 0.5
n2o_default = 0.2
ch4 = st.number_input("CH4 (mg/m³)", value=ch4_default, format="%.2f")
n2o = st.number_input("N2O (mg/m³)", value=n2o_default, format="%.2f")

if st.button("Save measurement"):
    new = pd.DataFrame({
        "day": [day],
        "CH4": [ch4],
        "N2O": [n2o],
        "timestamp": [datetime.now()]
    })
    st.session_state.data = pd.concat(
        [st.session_state.data, new],
        ignore_index=True
    )
    st.success("Measurement saved")

# --- Processamento e visualização dos dados ---
data = st.session_state.data.copy()

if not data.empty and all(col in data.columns for col in ["CH4", "N2O"]):
    # Cálculo do fluxo (mg/m²·h)
    data["Flux_CH4"] = (data["CH4"] * Q * 60) / area
    data["Flux_N2O"] = (data["N2O"] * Q * 60) / area
    data = data.sort_values("day").reset_index(drop=True)

    # Integração temporal (cumulativo)
    if len(data) > 1:
        data["cum_CH4"] = np.trapz(data["Flux_CH4"], data["day"])
        data["cum_N2O"] = np.trapz(data["Flux_N2O"], data["day"])

    st.subheader("Measurements")
    st.dataframe(data)

    # Gráfico de fluxos
    fig, ax = plt.subplots()
    ax.plot(data["day"], data["Flux_CH4"], marker='o', label="CH₄")
    ax.plot(data["day"], data["Flux_N2O"], marker='s', label="N₂O")
    ax.set_xlabel("Days")
    ax.set_ylabel("Flux (mg m⁻² h⁻¹)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # Mostrar totais cumulativos
    if len(data) > 1:
        st.metric("Emissão cumulativa de CH₄ (mg/m²)", f"{data['cum_CH4'].iloc[-1]:.2f}")
        st.metric("Emissão cumulativa de N₂O (mg/m²)", f"{data['cum_N2O'].iloc[-1]:.2f}")
else:
    st.info("Nenhuma medição registrada ainda. Use o formulário acima ou carregue os dados de exemplo.")
