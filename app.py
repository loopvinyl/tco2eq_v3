import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Vermicompostagem IoT", layout="wide")

st.title("🌱 Plataforma IoT de Monitoramento da Vermicompostagem")
st.subheader("Sensores simulados de CH₄, N₂O e temperatura com cálculo de emissões evitadas")

# =====================================================
# CONFIGURAÇÃO DO SISTEMA
# =====================================================

dias = 50
area_reator = 1.0
residuos_iniciais = 500  # kg de resíduos

# =====================================================
# SIMULAÇÃO DOS SENSORES (base Yang et al. 2017)
# =====================================================

np.random.seed(42)

tempo = np.arange(1, dias + 1)

ch4 = np.random.normal(0.03, 0.01, dias)
n2o = np.random.normal(0.5, 0.1, dias)
temperatura = np.random.normal(25, 3, dias)

df = pd.DataFrame({
    "Dia": tempo,
    "CH4": ch4,
    "N2O": n2o,
    "Temperatura": temperatura
})

# =====================================================
# LEITURA ATUAL DOS SENSORES
# =====================================================

st.header("📡 Leituras atuais dos sensores")

ch4_atual = df["CH4"].iloc[-1]
n2o_atual = df["N2O"].iloc[-1]
temp_atual = df["Temperatura"].iloc[-1]

col1, col2, col3 = st.columns(3)

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

if 20 <= temp_atual <= 30:
    st.success("Temperatura dentro da faixa ideal")
else:
    st.warning("Temperatura fora da faixa ideal")

# =====================================================
# GRÁFICOS DOS SENSORES
# =====================================================

st.header("📊 Histórico das emissões (sensores simulados)")

fig1 = px.line(df, x="Dia", y="CH4",
               title="Emissões de CH₄ durante a vermicompostagem")

fig2 = px.line(df, x="Dia", y="N2O",
               title="Emissões de N₂O durante a vermicompostagem")

fig3 = px.line(df, x="Dia", y="Temperatura",
               title="Temperatura no reator")

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)

# =====================================================
# RESÍDUOS NA VERMICOMPOSTEIRA
# =====================================================

st.header("♻️ Resíduos em processamento")

dias_processo = df["Dia"].iloc[-1]

residuo_restante = residuos_iniciais * (1 - (dias_processo / 60))

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Resíduos iniciais", f"{residuos_iniciais} kg")

with col2:
    st.metric("Dias de processo", f"{dias_processo}")

with col3:
    st.metric("Resíduo ainda em decomposição", f"{residuo_restante:.1f} kg")

st.info("Sistema de vermicompostagem em caixas com minhocas.")

# =====================================================
# COMPARAÇÃO COM ATERRO
# =====================================================

st.header("🌍 Comparação com aterro sanitário")

ch4_aterro = 1.8
n2o_aterro = 0.02

reducao_ch4 = ch4_aterro - ch4_atual
reducao_n2o = n2o_aterro - n2o_atual

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Redução de CH₄ vs aterro",
        f"{reducao_ch4:.3f} mg m⁻² h⁻¹"
    )

with col2:
    st.metric(
        "Redução de N₂O vs aterro",
        f"{reducao_n2o:.3f} mg m⁻² h⁻¹"
    )

# =====================================================
# EMISSÕES EVITADAS
# =====================================================

st.header("🌱 Emissões evitadas")

carbono_ev = reducao_ch4 * 24 * dias

st.metric(
    "Emissão evitada estimada",
    f"{carbono_ev:.2f} unidades"
)

# =====================================================
# MERCADO DE CARBONO
# =====================================================

st.header("💰 Potencial de créditos de carbono")

preco_carbono = 10  # USD exemplo

potencial_credito = carbono_ev * preco_carbono / 1000

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Preço do carbono",
        f"${preco_carbono}/tCO₂"
    )

with col2:
    st.metric(
        "Valor potencial estimado",
        f"${potencial_credito:.2f}"
    )

# =====================================================
# INTERPRETAÇÃO
# =====================================================

st.header("📖 Interpretação do sistema")

st.write("""
Esta plataforma demonstra um protótipo de monitoramento IoT aplicado
à vermicompostagem com minhocas.

Sensores ambientais instalados nos reatores medem:

• emissões de CH₄  
• emissões de N₂O  
• temperatura do processo

Os dados são processados pela plataforma digital para estimar:

• desempenho ambiental do sistema  
• emissões evitadas em comparação com aterros  
• potencial de geração de créditos de carbono

Os valores utilizados neste protótipo foram simulados a partir de
dados experimentais reportados na literatura científica.
""")
