import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import time

st.set_page_config(layout="wide")

st.title("🌱 Dashboard de Vermicompostagem IoT")
st.write("Monitoramento de emissões de CH₄, N₂O e temperatura")

dias = 50

# gerar dados simulados
dados = pd.DataFrame({
    "Dia": range(1, dias+1),
    "CH4": np.random.uniform(0.01, 0.20, dias),
    "N2O": np.random.uniform(0.10, 0.60, dias),
    "Temperatura": np.random.uniform(20, 30, dias)
})

st.subheader("📡 Leituras atuais dos sensores")

col1, col2, col3 = st.columns(3)

col1.metric("CH₄ atual", f"{dados.CH4.iloc[-1]:.4f} mg m⁻² h⁻¹")
col2.metric("N₂O atual", f"{dados.N2O.iloc[-1]:.4f} mg m⁻² h⁻¹")
col3.metric("Temperatura", f"{dados.Temperatura.iloc[-1]:.1f} °C")

st.divider()

colA, colB = st.columns(2)

with colA:
    fig1 = px.line(
        dados,
        x="Dia",
        y=["CH4","N2O"],
        title="Emissões simuladas de CH₄ e N₂O"
    )
    st.plotly_chart(fig1, use_container_width=True)

with colB:
    fig2 = px.line(
        dados,
        x="Dia",
        y="Temperatura",
        title="Temperatura da vermicomposteira"
    )
    fig2.add_hline(y=35)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

st.subheader("📊 Dados simulados dos sensores")
st.dataframe(dados)

if dados.Temperatura.iloc[-1] > 35:
    st.error("⚠ Temperatura acima do limite recomendado")
else:
    st.success("✅ Temperatura dentro da faixa ideal")
