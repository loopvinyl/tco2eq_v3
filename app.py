import streamlit as st
import pandas as pd
import numpy as np

st.title("Monitoramento de Gases - Vermicompostagem")

# ===============================
# Upload dos dados
# ===============================

arquivo = st.file_uploader("Carregar arquivo CSV com os dados do analisador", type=["csv"])

if arquivo is not None:

    dados = pd.read_csv(arquivo)

    if "timestamp" in dados.columns:
        dados["timestamp"] = pd.to_datetime(dados["timestamp"])
        dados = dados.set_index("timestamp")

    st.subheader("Dados coletados do analisador")
    st.write(dados.head())

    # ===============================
    # Gráfico CH4 e N2O
    # ===============================

    st.subheader("Concentração de CH4 e N2O (ppm)")

    gases = dados[["CH4_ppm", "N2O_ppm"]]

    st.line_chart(gases)

    # ===============================
    # Gráfico CO2
    # ===============================

    if "CO2_ppm" in dados.columns:

        st.subheader("Concentração de CO2")

        st.line_chart(dados["CO2_ppm"])

    # ===============================
    # Temperatura
    # ===============================

    if "temperature" in dados.columns:

        st.subheader("Temperatura do sistema")

        st.line_chart(dados["temperature"])

    # ===============================
    # PARÂMETROS DO SISTEMA
    # ===============================

    st.sidebar.header("Parâmetros do sistema")

    volume_camara = st.sidebar.number_input("Volume da câmara (L)", value=20.0)
    massa_residuo = st.sidebar.number_input("Massa de resíduo (kg)", value=5.0)

    # ===============================
    # CÁLCULO SIMPLIFICADO DE FLUXO
    # ===============================

    fator_conversao = 0.001

    dados["CH4_flux"] = dados["CH4_ppm"] * fator_conversao
    dados["N2O_flux"] = dados["N2O_ppm"] * fator_conversao

    dados["CH4_cumulative"] = dados["CH4_flux"].cumsum()
    dados["N2O_cumulative"] = dados["N2O_flux"].cumsum()

    # ===============================
    # MASSA DOS GASES
    # ===============================

    CH4_massa = dados["CH4_cumulative"] * volume_camara / massa_residuo
    N2O_massa = dados["N2O_cumulative"] * volume_camara / massa_residuo

    dados["CH4_mass"] = CH4_massa
    dados["N2O_mass"] = N2O_massa

    # ===============================
    # PERDA ELEMENTAR (Fe Yang approach)
    # ===============================

    C_inicial = st.sidebar.number_input("Carbono inicial (g)", value=1000.0)
    N_inicial = st.sidebar.number_input("Nitrogênio inicial (g)", value=100.0)

    fracao_C_CH4 = 12 / 16
    fracao_N_N2O = 28 / 44

    dados["C_loss"] = dados["CH4_mass"] * fracao_C_CH4
    dados["N_loss"] = dados["N2O_mass"] * fracao_N_N2O

    dados["C_loss_percent"] = (dados["C_loss"] / C_inicial) * 100
    dados["N_loss_percent"] = (dados["N_loss"] / N_inicial) * 100

    # ===============================
    # Gráfico perda percentual
    # ===============================

    st.subheader("Evolução da perda percentual de C e N")

    perdas = dados[["C_loss_percent", "N_loss_percent"]]

    st.line_chart(perdas)

    # ===============================
    # NOVO BLOCO (percentual de perda)
    # ===============================

    st.subheader("Percentual de perda convertido em emissões atmosféricas")

    st.markdown(
    """
    Nos sistemas de compostagem e vermicompostagem, a fração de carbono e nitrogênio
    perdida na forma gasosa corresponde às emissões liberadas para a atmosfera.

    - **Carbono perdido via CH4-C** representa o carbono emitido como **metano (CH4)**.
    - **Nitrogênio perdido via N2O-N** representa o nitrogênio emitido como **óxido nitroso (N2O)**.

    Assim, os percentuais abaixo indicam a fração do carbono e do nitrogênio inicial
    que foi convertida em gases de efeito estufa e emitida para a atmosfera.
    """
    )

    C_loss_final = dados["C_loss_percent"].iloc[-1]
    N_loss_final = dados["N_loss_percent"].iloc[-1]

    col1, col2 = st.columns(2)

    col1.metric(
        "Carbono emitido como CH4 (%)",
        f"{C_loss_final:.3f}"
    )

    col2.metric(
        "Nitrogênio emitido como N2O (%)",
        f"{N_loss_final:.3f}"
    )

    # ===============================
    # GWP selection
    # ===============================

    st.sidebar.header("Escolha do GWP")

    gwp_opcao = st.sidebar.selectbox(
        "Horizonte temporal",
        ["Yang (100 anos)", "GWP-20", "GWP-100", "GWP-500"]
    )

    if gwp_opcao == "Yang (100 anos)":

        CH4_GWP = 25
        N2O_GWP = 298

    elif gwp_opcao == "GWP-20":

        CH4_GWP = 79.7
        N2O_GWP = 273

    elif gwp_opcao == "GWP-100":

        CH4_GWP = 27
        N2O_GWP = 273

    else:

        CH4_GWP = 7.2
        N2O_GWP = 130

    # ===============================
    # CO2eq
    # ===============================

    dados["CH4_CO2eq"] = dados["CH4_mass"] * CH4_GWP
    dados["N2O_CO2eq"] = dados["N2O_mass"] * N2O_GWP

    # ===============================
    # Gráfico CO2eq dos gases
    # ===============================

    st.subheader("Emissões dos gases em CO2 equivalente")

    co2eq_gases = dados[["CH4_CO2eq", "N2O_CO2eq"]]

    st.line_chart(co2eq_gases)

    # ===============================
    # Total CO2eq
    # ===============================

    dados["CO2eq_total"] = dados["CH4_CO2eq"] + dados["N2O_CO2eq"]

    st.subheader("Emissões totais em CO2 equivalente")

    st.line_chart(dados["CO2eq_total"])
