import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================

st.set_page_config(
    page_title="Dashboard IoT - Vermicompostagem",
    page_icon="🌱",
    layout="wide"
)

st.title("🌱 Dashboard de Vermicompostagem IoT")
st.markdown("Monitoramento de emissões de **CH₄, N₂O e temperatura** em reatores de vermicompostagem")

st.info("""
Protótipo de sistema de monitoramento ambiental para vermicompostagem.
Nesta versão, os valores de emissão são simulados com base em dados experimentais
da literatura científica.
""")

# ==========================================================
# SIMULAÇÃO DE SENSORES (BASEADO EM YANG 2017)
# ==========================================================

dias = 50

datas = pd.date_range(
    start=datetime.now() - timedelta(days=dias),
    periods=dias
)

np.random.seed(42)

# valores baseados em faixa do artigo
ch4 = np.random.normal(0.03, 0.01, dias)
n2o = np.random.normal(0.40, 0.12, dias)
temperatura = np.random.normal(27, 3, dias)

df = pd.DataFrame({
    "data": datas,
    "CH4": ch4,
    "N2O": n2o,
    "Temperatura": temperatura
})

# ==========================================================
# LEITURAS ATUAIS
# ==========================================================

st.header("📡 Leituras atuais dos sensores")

col1, col2, col3 = st.columns(3)

ch4_atual = df["CH4"].iloc[-1]
n2o_atual = df["N2O"].iloc[-1]
temp_atual = df["Temperatura"].iloc[-1]

with col1:
    st.metric(
        "CH₄ atual",
        f"{ch4_atual:.4f} mg m⁻² h⁻¹"
    )

with col2:
    st.metric(
        "N₂O atual",
        f"{n2o_atual:.4f} mg m⁻² h⁻¹"
    )

with col3:
    st.metric(
        "Temperatura",
        f"{temp_atual:.1f} °C"
    )

# alerta de temperatura

if temp_atual < 15:
    st.warning("⚠️ Temperatura baixa para atividade microbiana ideal")
elif temp_atual > 35:
    st.error("🔥 Temperatura acima da faixa recomendada para vermicompostagem")
else:
    st.success("✅ Temperatura dentro da faixa ideal")

# ==========================================================
# GRÁFICOS
# ==========================================================

st.header("📈 Evolução das emissões (50 dias)")

fig1 = px.line(
    df,
    x="data",
    y="CH4",
    title="Emissões de CH₄"
)

fig2 = px.line(
    df,
    x="data",
    y="N2O",
    title="Emissões de N₂O"
)

fig3 = px.line(
    df,
    x="data",
    y="Temperatura",
    title="Temperatura do reator"
)

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# ==========================================================
# INTEGRAÇÃO COM MODELO DE CÁLCULO
# ==========================================================

st.markdown("---")

st.header("🧮 Integração com Modelo de Emissões")

st.write("""
Os valores monitorados podem ser utilizados como entrada para o modelo
de cálculo de emissões de gases de efeito estufa do sistema.

O sistema compara:

• cenário de vermicompostagem  
• cenário contrafactual de disposição em aterro sanitário

permitindo estimar **emissões evitadas e potencial de créditos de carbono**.
""")

st.subheader("Valores utilizados no modelo")

st.write(f"CH₄: **{ch4_atual:.4f} mg m⁻² h⁻¹**")
st.write(f"N₂O: **{n2o_atual:.4f} mg m⁻² h⁻¹**")

st.info("""
Esses valores representam leituras de sensores ou dados simulados
baseados em experimentos científicos.

Quando sensores físicos forem integrados ao sistema,
os dados serão coletados automaticamente em tempo real
via Internet das Coisas (IoT).
""")

# ==========================================================
# REFERÊNCIA CIENTÍFICA
# ==========================================================

st.markdown("---")

st.markdown("""
📚 **Base científica dos parâmetros utilizados**

Yang et al. (2017) – estudo experimental sobre emissões de gases
durante processos de vermicompostagem.

Os valores utilizados neste protótipo são consistentes com as
faixas observadas experimentalmente na literatura científica.
""")
