import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

st.title("Dashboard de Vermicompostagem IoT")

st.write("Monitoramento de CH4, N2O e temperatura")

dias = 50

dados = pd.DataFrame({
    "Dia": range(1, dias+1),
    "CH4": np.random.uniform(0.01, 0.20, dias),
    "N2O": np.random.uniform(0.10, 0.60, dias),
    "Temperatura": np.random.uniform(20, 30, dias)
})

col1, col2, col3 = st.columns(3)

col1.metric("CH4 atual", f"{dados.CH4.iloc[-1]:.3f} mg m⁻² h⁻¹")
col2.metric("N2O atual", f"{dados.N2O.iloc[-1]:.3f} mg m⁻² h⁻¹")
col3.metric("Temperatura", f"{dados.Temperatura.iloc[-1]:.1f} °C")

fig1 = px.line(dados, x="Dia", y=["CH4","N2O"], title="Emissões simuladas")
st.plotly_chart(fig1)

fig2 = px.line(dados, x="Dia", y="Temperatura", title="Temperatura da vermicomposteira")
st.plotly_chart(fig2)

if dados.Temperatura.iloc[-1] > 35:
    st.error("⚠ Temperatura acima do limite!")
else:
    st.success("Temperatura dentro da faixa ideal")
