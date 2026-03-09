import streamlit as st
import pandas as pd
import numpy as np
import os

st.title("Monitoramento de Gases - Vermicompostagem")

# -----------------------------
# Escolha do GWP
# -----------------------------

st.subheader("Configuração do cálculo climático")

gwp_option = st.selectbox(
    "Escolha o horizonte de tempo do GWP",
    [
        "Yang et al. (GWP-100 clássico)",
        "IPCC AR6 - GWP20",
        "IPCC AR6 - GWP100",
        "IPCC AR6 - GWP500"
    ]
)

if gwp_option == "Yang et al. (GWP-100 clássico)":
    GWP_CH4 = 25
    GWP_N2O = 298

elif gwp_option == "IPCC AR6 - GWP20":
    GWP_CH4 = 79.7
    GWP_N2O = 273

elif gwp_option == "IPCC AR6 - GWP100":
    GWP_CH4 = 27.0
    GWP_N2O = 273

elif gwp_option == "IPCC AR6 - GWP500":
    GWP_CH4 = 7.2
    GWP_N2O = 130


arquivo = "dados_emissoes.csv"

# -----------------------------
# Criar CSV exemplo se não existir
# -----------------------------

if not os.path.exists(arquivo):

    dados_exemplo = pd.DataFrame({
        "timestamp":[
        "2016-06-01 10:00",
        "2016-06-06 10:00",
        "2016-06-11 10:00",
        "2016-06-16 10:00",
        "2016-06-21 10:00",
        "2016-06-26 10:00",
        "2016-07-01 10:00",
        "2016-07-06 10:00",
        "2016-07-11 10:00",
        "2016-07-16 10:00",
        "2016-07-21 10:00"
        ],

        "chamber_id":[1]*11,

        "CH4_ppm":[2.1,1.9,1.7,1.4,1.1,0.85,0.65,0.50,0.35,0.25,0.18],
        "N2O_ppm":[0.2,0.28,0.45,0.70,0.90,1.05,0.95,0.75,0.55,0.35,0.22],
        "CO2_ppm":[410,415,420,425,430,435,438,440,442,444,445],

        "temperature_C":[25.1,25.4,25.7,26.0,26.3,26.6,26.8,27.0,27.2,27.4,27.6],

        "pressure_kPa":[101.3,101.2,101.2,101.1,101.1,101.0,101.0,100.9,100.9,100.8,100.8],

        "humidity_percent":[60,61,62,63,64,65,65,66,66,67,67]
    })

    dados_exemplo.to_csv(arquivo,index=False)


# -----------------------------
# Ler dados
# -----------------------------

dados = pd.read_csv(arquivo)

dados["timestamp"] = pd.to_datetime(dados["timestamp"])

dados = dados.set_index("timestamp")

st.subheader("Dados coletados do analisador")

st.dataframe(dados)

# -----------------------------
# Gráficos de concentração
# -----------------------------

st.subheader("Concentração de CH4 e N2O (ppm)")
st.line_chart(dados[["CH4_ppm","N2O_ppm"]])

st.subheader("Concentração de CO2")
st.line_chart(dados["CO2_ppm"])

st.subheader("Temperatura do sistema")
st.line_chart(dados["temperature_C"])

# -----------------------------
# Cálculo de massa
# -----------------------------

R = 8.314
VOLUME_CAMARA = 0.02

M_CH4 = 16.04
M_N2O = 44.01

dados["T_K"] = dados["temperature_C"] + 273.15
dados["P_Pa"] = dados["pressure_kPa"] * 1000

dados["mol_total"] = (dados["P_Pa"] * VOLUME_CAMARA) / (R * dados["T_K"])

dados["CH4_frac"] = dados["CH4_ppm"] / 1e6
dados["N2O_frac"] = dados["N2O_ppm"] / 1e6

dados["mol_CH4"] = dados["mol_total"] * dados["CH4_frac"]
dados["mol_N2O"] = dados["mol_total"] * dados["N2O_frac"]

dados["CH4_g"] = dados["mol_CH4"] * M_CH4
dados["N2O_g"] = dados["mol_N2O"] * M_N2O

dados["CH4_acum_g"] = dados["CH4_g"].cumsum()
dados["N2O_acum_g"] = dados["N2O_g"].cumsum()

st.subheader("Massa acumulada de gases")

st.line_chart(dados[["CH4_acum_g","N2O_acum_g"]])

# -----------------------------
# Perda de elementos
# -----------------------------

st.subheader("Perda de Carbono e Nitrogênio")

st.caption("Valores padrão baseados em parâmetros utilizados ou inferidos do estudo de Yang et al.")

C_inicial = st.number_input(
    "Carbono inicial do material (g)",
    value=1000.0,
    step=10.0
)

N_inicial = st.number_input(
    "Nitrogênio inicial do material (g)",
    value=100.0,
    step=1.0
)

dados["C_perdido_g"] = dados["CH4_g"] * (12/16)
dados["N_perdido_g"] = dados["N2O_g"] * (28/44)

dados["C_perdido_acum_g"] = dados["C_perdido_g"].cumsum()
dados["N_perdido_acum_g"] = dados["N_perdido_g"].cumsum()

dados["C_loss_percent"] = (dados["C_perdido_acum_g"] / C_inicial) * 100
dados["N_loss_percent"] = (dados["N_perdido_acum_g"] / N_inicial) * 100

st.subheader("Evolução da perda percentual")

st.line_chart(dados[["C_loss_percent","N_loss_percent"]])

C_loss_final = dados["C_loss_percent"].iloc[-1]
N_loss_final = dados["N_loss_percent"].iloc[-1]

st.subheader("Perda total acumulada")

col1, col2 = st.columns(2)

col1.metric("Perda de C via CH4 (%)",f"{C_loss_final:.3f}")
col2.metric("Perda de N via N2O (%)",f"{N_loss_final:.3f}")

# -----------------------------
# CO2 equivalente
# -----------------------------

dados["CH4_CO2eq_g"] = dados["CH4_g"] * GWP_CH4
dados["N2O_CO2eq_g"] = dados["N2O_g"] * GWP_N2O

dados["CO2eq_total_g"] = dados["CH4_CO2eq_g"] + dados["N2O_CO2eq_g"]

dados["CO2eq_acum_g"] = dados["CO2eq_total_g"].cumsum()

# -----------------------------
# CO2eq por gás
# -----------------------------

st.subheader("Emissões de cada gás em CO2 equivalente")

dados["CH4_CO2eq_acum_g"] = dados["CH4_CO2eq_g"].cumsum()
dados["N2O_CO2eq_acum_g"] = dados["N2O_CO2eq_g"].cumsum()

st.line_chart(dados[["CH4_CO2eq_acum_g","N2O_CO2eq_acum_g"]])

# -----------------------------
# CO2eq total
# -----------------------------

st.subheader("Emissões acumuladas em CO2 equivalente")

st.line_chart(dados["CO2eq_acum_g"])
