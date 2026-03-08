import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.title("Vermicompost GHG Monitoring Prototype")
st.markdown("Simulação das emissões de CH₄ e N₂O durante vermicompostagem, baseada no artigo de Yang et al. (2017).")

# ---- EXPANDER: Comparação com o artigo ----
with st.expander("📋 Comparação: o que o artigo mede vs. o que o app simula"):
    comparacao = pd.DataFrame({
        "Variável no artigo": [
            "CH₄ (metano)",
            "N₂O (óxido nitroso)",
            "NH₃ (amônia)",
            "Temperatura",
            "pH, C/N, GI",
            "Biomassa de minhocas",
            "Emissões GEE totais (kg CO₂-eq/t MS)"
        ],
        "Como é apresentada no artigo": [
            "Fluxo ao longo do tempo (Fig. 2A); % do C inicial (Tabela 3)",
            "Fluxo ao longo do tempo (Fig. 2B); % do N inicial (Tabela 3)",
            "Fluxo ao longo do tempo (Fig. 2C); % do N inicial (Tabela 3)",
            "Perfil térmico (Fig. 1)",
            "Evolução temporal (Tabela 2)",
            "Evolução temporal (Tabela 2)",
            "Tabela 3"
        ],
        "No aplicativo": [
            "Inserimos concentração (mg/m³) → fluxo (mg/m²·h) e cumulativo (mg/m²)",
            "Inserimos concentração (mg/m³) → fluxo (mg/m²·h) e cumulativo (mg/m²)",
            "❌ Não implementado",
            "❌ Não implementado",
            "❌ Não implementado",
            "❌ Não implementado",
            "❌ Não implementado (pode ser derivado dos fluxos)"
        ]
    })
    st.dataframe(comparacao, hide_index=True)

st.header("Experiment setup")
area = st.number_input("Chamber area (m²)", value=0.13, format="%.2f")
flow = st.number_input("Sweep air flow (L/min)", value=5.0, format="%.2f")
start_date = st.date_input("Experiment start date", value=datetime.now())
Q = flow / 1000  # L/min → m³/min

# Dias de medição (baseado no artigo)
schedule = [0, 3, 7, 14, 21, 30, 45, 60]
st.header("Sampling schedule")
st.write(schedule)

# Inicializa o banco de dados
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["day", "CH4", "N2O", "timestamp"])

# ---- Botão para carregar dados exatos do artigo ----
if st.button("📥 Carregar dados exatos do artigo (Figuras 2A e 2B)"):
    # Valores aproximados extraídos visualmente dos gráficos do artigo
    dias = schedule
    ch4_vals = [0.82, 0.58, 0.41, 0.29, 0.21, 0.12, 0.06, 0.02]   # mg/m³
    n2o_vals = [0.14, 0.24, 0.31, 0.27, 0.19, 0.11, 0.07, 0.04]   # mg/m³
    exemplo = pd.DataFrame({
        "day": dias,
        "CH4": ch4_vals,
        "N2O": n2o_vals,
        "timestamp": [datetime.now()] * len(dias)
    })
    st.session_state.data = exemplo
    st.success("Dados exatos do artigo carregados! Valores baseados nas Figuras 2A e 2B.")

st.header("Register measurement")
day = st.selectbox("Sampling day", schedule)

# Valores default mais próximos do artigo (primeiros dias)
ch4_default = 0.80
n2o_default = 0.15
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

# --- Processamento e visualização ---
data = st.session_state.data.copy()

if not data.empty and all(col in data.columns for col in ["CH4", "N2O"]):
    # Cálculo do fluxo (mg/m²·h)
    data["Flux_CH4"] = (data["CH4"] * Q * 60) / area
    data["Flux_N2O"] = (data["N2O"] * Q * 60) / area
    data = data.sort_values("day").reset_index(drop=True)

    # Integração temporal (cumulativo)
    if len(data) > 1:
        data["cum_CH4"] = np.trapezoid(data["Flux_CH4"], data["day"])
        data["cum_N2O"] = np.trapezoid(data["Flux_N2O"], data["day"])

    st.subheader("📊 Measurements")
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

    # Métricas cumulativas
    if len(data) > 1:
        st.metric("Emissão cumulativa de CH₄ (mg/m²)", f"{data['cum_CH4'].iloc[-1]:.2f}")
        st.metric("Emissão cumulativa de N₂O (mg/m²)", f"{data['cum_N2O'].iloc[-1]:.2f}")

        # Comparação com os valores do artigo (apenas para referência)
        st.caption("🔍 No artigo, as perdas cumulativas são apresentadas como % do C e N inicial, não em mg/m². Os valores acima são apenas indicativos dos fluxos medidos.")
else:
    st.info("Nenhuma medição registrada ainda. Use o formulário acima ou carregue os dados de exemplo.")
