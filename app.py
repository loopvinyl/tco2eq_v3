import streamlit as st
import pandas as pd
import numpy as np

st.title("Monitoramento de Gases - Vermicompostagem")

st.markdown("Dados coletados do analisador")

# -----------------------------
# Upload dos dados
# -----------------------------

arquivo = st.file_uploader("Carregar arquivo CSV", type=["csv"])

if arquivo is not None:

    dados = pd.read_csv(arquivo)

    if "date" in dados.columns:
        dados["date"] = pd.to_datetime(dados["date"])
        dados = dados.set_index("date")

    # -----------------------------
    # Gráfico CH4 e N2O
    # -----------------------------

    st.subheader("Concentração de CH4 e N2O (ppm)")
    st.line_chart(dados[["CH4_ppm", "N2O_ppm"]])

    # -----------------------------
    # CO2
    # -----------------------------

    if "CO2_ppm" in dados.columns:
        st.subheader("Concentração de CO2")
        st.line_chart(dados["CO2_ppm"])

    # -----------------------------
    # Temperatura
    # -----------------------------

    if "temperature" in dados.columns:
        st.subheader("Temperatura do sistema")
        st.line_chart(dados["temperature"])

    # -----------------------------
    # Parâmetros do sistema
    # -----------------------------

    st.sidebar.header("Parâmetros do sistema")

    massa_substrato = st.sidebar.number_input(
        "Massa do substrato (kg)", value=10.0
    )

    carbono_percentual = st.sidebar.number_input(
        "Carbono total (%)", value=40.0
    )

    nitrogenio_percentual = st.sidebar.number_input(
        "Nitrogênio total (%)", value=2.0
    )

    # -----------------------------
    # Estoque inicial de C e N
    # -----------------------------

    C_inicial = massa_substrato * (carbono_percentual / 100) * 1000
    N_inicial = massa_substrato * (nitrogenio_percentual / 100) * 1000

    st.sidebar.write("C inicial estimado (g):", round(C_inicial, 2))
    st.sidebar.write("N inicial estimado (g):", round(N_inicial, 2))

    # -----------------------------
    # Conversão simplificada ppm → massa
    # -----------------------------

    dados["CH4_mass"] = dados["CH4_ppm"] * 0.001
    dados["N2O_mass"] = dados["N2O_ppm"] * 0.001

    dados["CH4_cum"] = dados["CH4_mass"].cumsum()
    dados["N2O_cum"] = dados["N2O_mass"].cumsum()

    # -----------------------------
    # Conversão para C e N emitidos
    # -----------------------------

    dados["C_emitido"] = dados["CH4_cum"] * (12 / 16)
    dados["N_emitido"] = dados["N2O_cum"] * (28 / 44)

    # -----------------------------
    # Percentual de perda (Yang)
    # -----------------------------

    dados["C_loss_percent"] = (dados["C_emitido"] / C_inicial) * 100
    dados["N_loss_percent"] = (dados["N_emitido"] / N_inicial) * 100

    st.subheader("Perda percentual de C e N")

    st.line_chart(
        dados[["C_loss_percent", "N_loss_percent"]]
    )

    # -----------------------------
    # Módulo explicando perdas
    # -----------------------------

    st.subheader("Percentual de perda convertido em emissões atmosféricas")

    st.markdown(
        """
Nos sistemas de compostagem e vermicompostagem, parte do carbono e do nitrogênio
do material inicial é perdido na forma gasosa.

Essas perdas correspondem diretamente às emissões de gases de efeito estufa
liberadas para a atmosfera.

• **Perda de carbono (C loss)** → emitida principalmente como **CH4**  
• **Perda de nitrogênio (N loss)** → emitida principalmente como **N2O**

Portanto, os percentuais abaixo representam a fração do estoque inicial
de C e N do sistema que foi convertida em gases e liberada para a atmosfera.
"""
    )

    C_final = dados["C_loss_percent"].iloc[-1]
    N_final = dados["N_loss_percent"].iloc[-1]

    col1, col2 = st.columns(2)

    col1.metric(
        "Carbono emitido como CH4 (%)",
        f"{C_final:.4f}"
    )

    col2.metric(
        "Nitrogênio emitido como N2O (%)",
        f"{N_final:.4f}"
    )

    # -----------------------------
    # Escolha do GWP
    # -----------------------------

    st.sidebar.header("Escolha do GWP")

    metodo = st.sidebar.selectbox(
        "Horizonte de GWP",
        [
            "Yang (25 / 298)",
            "GWP-20",
            "GWP-100",
            "GWP-500"
        ]
    )

    if metodo == "Yang (25 / 298)":
        GWP_CH4 = 25
        GWP_N2O = 298

    elif metodo == "GWP-20":
        GWP_CH4 = 79.7
        GWP_N2O = 273

    elif metodo == "GWP-100":
        GWP_CH4 = 27.0
        GWP_N2O = 273

    else:
        GWP_CH4 = 7.2
        GWP_N2O = 130

    # -----------------------------
    # CO2 equivalente
    # -----------------------------

    dados["CH4_CO2eq"] = dados["CH4_mass"] * GWP_CH4
    dados["N2O_CO2eq"] = dados["N2O_mass"] * GWP_N2O

    dados["CH4_CO2eq_cum"] = dados["CH4_CO2eq"].cumsum()
    dados["N2O_CO2eq_cum"] = dados["N2O_CO2eq"].cumsum()

    dados["Total_CO2eq"] = (
        dados["CH4_CO2eq_cum"] + dados["N2O_CO2eq_cum"]
    )

    # -----------------------------
    # Gráfico emissões individuais
    # -----------------------------

    st.subheader("Emissões acumuladas em CO2 equivalente")

    st.line_chart(
        dados[["CH4_CO2eq_cum", "N2O_CO2eq_cum"]]
    )

    # -----------------------------
    # Gráfico final total
    # -----------------------------

    st.subheader("Emissão total de GEE (CO2 equivalente)")

    st.line_chart(dados["Total_CO2eq"])
