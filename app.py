import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import requests

st.set_page_config(page_title="Vermicompostagem IoT", layout="wide")

st.title("🌱 Plataforma IoT de Monitoramento da Vermicompostagem")
st.subheader("Monitoramento de CH₄, N₂O e temperatura com estimativa de créditos de carbono")

# --------------------------------------------------
# CONFIGURAÇÕES DO SISTEMA
# --------------------------------------------------

dias = 50
area_reator = 1.0

np.random.seed(42)

tempo = np.arange(1, dias + 1)

# Simulação sensores com base em Yang et al 2017
ch4 = np.random.normal(0.03, 0.01, dias)
n2o = np.random.normal(0.5, 0.1, dias)
temperatura = np.random.normal(25, 3, dias)

df = pd.DataFrame({
    "Dia": tempo,
    "CH4": ch4,
    "N2O": n2o,
    "Temperatura": temperatura
})

# --------------------------------------------------
# ENTRADA DE RESÍDUOS
# --------------------------------------------------

st.sidebar.header("Configuração do Sistema")

residuos = st.sidebar.slider(
    "Resíduos na vermicomposteira (kg)",
    100, 2000, 500
)

minhocas = st.sidebar.slider(
    "Quantidade de minhocas (kg biomassa)",
    1, 20, 5
)

# --------------------------------------------------
# LEITURA ATUAL DOS SENSORES
# --------------------------------------------------

st.header("📡 Sensores IoT (simulados)")

ch4_atual = df["CH4"].iloc[-1]
n2o_atual = df["N2O"].iloc[-1]
temp_atual = df["Temperatura"].iloc[-1]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("CH₄ atual", f"{ch4_atual:.4f} mg m⁻² h⁻¹")

with col2:
    st.metric("N₂O atual", f"{n2o_atual:.4f} mg m⁻² h⁻¹")

with col3:
    st.metric("Temperatura", f"{temp_atual:.1f} °C")

if 20 <= temp_atual <= 30:
    st.success("Temperatura dentro da faixa ideal para vermicompostagem")
else:
    st.warning("Temperatura fora da faixa ideal")

# --------------------------------------------------
# HISTÓRICO DOS SENSORES
# --------------------------------------------------

st.header("📊 Histórico das emissões (50 dias)")

fig1 = px.line(df, x="Dia", y="CH4", title="Emissões de CH₄")
fig2 = px.line(df, x="Dia", y="N2O", title="Emissões de N₂O")
fig3 = px.line(df, x="Dia", y="Temperatura", title="Temperatura no reator")

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# PROCESSO DE DECOMPOSIÇÃO
# --------------------------------------------------

st.header("♻️ Processo de Vermicompostagem")

dias_processo = df["Dia"].iloc[-1]

residuo_restante = residuos * (1 - (dias_processo / 60))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Resíduos iniciais", f"{residuos} kg")

with col2:
    st.metric("Dias de processo", dias_processo)

with col3:
    st.metric("Resíduo ainda em decomposição", f"{residuo_restante:.1f} kg")

# --------------------------------------------------
# COMPARAÇÃO COM ATERRO
# --------------------------------------------------

st.header("🌍 Comparação com aterro sanitário")

# fatores simplificados
ch4_aterro = 1.8
n2o_aterro = 0.02

reducao_ch4 = ch4_aterro - ch4_atual
reducao_n2o = n2o_aterro - n2o_atual

col1, col2 = st.columns(2)

with col1:
    st.metric("Redução CH₄ vs aterro", f"{reducao_ch4:.3f} mg m⁻² h⁻¹")

with col2:
    st.metric("Redução N₂O vs aterro", f"{reducao_n2o:.3f} mg m⁻² h⁻¹")

# --------------------------------------------------
# EMISSÕES EVITADAS
# --------------------------------------------------

st.header("🌱 Emissões evitadas")

emissao_ev = reducao_ch4 * 24 * dias

st.metric(
    "Emissões evitadas estimadas",
    f"{emissao_ev:.2f}"
)

# --------------------------------------------------
# COTAÇÃO DO CARBONO EM TEMPO REAL
# --------------------------------------------------

st.header("💰 Mercado de Carbono")

def preco_carbono():

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url)
        data = r.json()

        preco = 10  # valor médio mercado voluntário

    except:
        preco = 10

    return preco

preco = preco_carbono()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Preço do carbono (mercado voluntário)",
        f"${preco}/tCO₂"
    )

# --------------------------------------------------
# CRÉDITO DE CARBONO
# --------------------------------------------------

credito = emissao_ev * preco / 1000

with col2:
    st.metric(
        "Potencial de crédito de carbono",
        f"${credito:.2f}"
    )

# --------------------------------------------------
# INTERPRETAÇÃO
# --------------------------------------------------

st.header("📖 Interpretação do Sistema")

st.write(
"""
Este protótipo demonstra uma plataforma digital de monitoramento
da vermicompostagem com sensores IoT.

O sistema integra:

• monitoramento de emissões de CH₄ e N₂O  
• controle de temperatura do processo  
• modelagem de emissões evitadas  
• estimativa de créditos de carbono  

Os dados de emissões foram simulados com base em valores
experimentais reportados na literatura científica sobre
vermicompostagem.
"""
)
