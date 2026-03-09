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
# Criar CSV exemplo
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

        "CH4_ppm":[2.1,1.9,1.7,1.4,1.1,0.85,0.65,0.50,0.35,0.25,0.18],
        "N2O_ppm":[0.2,0.28,0.45,0.70,0.90,1.05,0.95,0.75,0.55,0.35,0.22],
        "CO2_ppm":[410,415,420,425,430,435,438,440,442,444,445],

        "temperature_C":[25.1,25.4,25.7,26.0,26.3,26.6,26.8,27.0,27.2,27.4,27.6],
        "pressure_kPa":[101.3,101.2,101.2,101.1,101.1,101.0,101.0,100.9,100.9,100.8,100.8],
        "humidity_percent":[60,61,62,63,64,65,65,66,66,67,67]
    })

    dados_exemplo.to_csv(arquivo,index=False)

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
# Cálculo de massa dos gases
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
# Parâmetros do material (Yang)
# -----------------------------

st.subheader("Parâmetros do material inicial (Yang et al. 2017)")

massa_inicial = st.number_input("Massa inicial do resíduo (g)",value=245.28)
umidade = st.number_input("Umidade (%)",value=50.8)
TOC = st.number_input("Carbono orgânico total (%)",value=43.6)
TN = st.number_input("Nitrogênio total (g/kg)",value=14.2)

DM = massa_inicial*(1-umidade/100)

C_inicial = DM*(TOC/100)
N_inicial = DM*(TN/1000)

st.write("Carbono inicial estimado (g):",round(C_inicial,3))
st.write("Nitrogênio inicial estimado (g):",round(N_inicial,3))

# -----------------------------
# Perda de elementos
# -----------------------------

dados["C_perdido_g"] = dados["CH4_g"]*(12/16)
dados["N_perdido_g"] = dados["N2O_g"]*(28/44)

dados["C_perdido_acum_g"]=dados["C_perdido_g"].cumsum()
dados["N_perdido_acum_g"]=dados["N_perdido_g"].cumsum()

dados["C_loss_percent"]=(dados["C_perdido_acum_g"]/C_inicial)*100
dados["N_loss_percent"]=(dados["N_perdido_acum_g"]/N_inicial)*100

st.subheader("Evolução da perda percentual")
st.line_chart(dados[["C_loss_percent","N_loss_percent"]])

# -----------------------------
# CO2 equivalente
# -----------------------------

dados["CH4_CO2eq_g"]=dados["CH4_g"]*GWP_CH4
dados["N2O_CO2eq_g"]=dados["N2O_g"]*GWP_N2O

dados["CO2eq_total_g"]=dados["CH4_CO2eq_g"]+dados["N2O_CO2eq_g"]
dados["CO2eq_acum_g"]=dados["CO2eq_total_g"].cumsum()

st.subheader("Emissões de cada gás em CO2 equivalente")

dados["CH4_CO2eq_acum_g"]=dados["CH4_CO2eq_g"].cumsum()
dados["N2O_CO2eq_acum_g"]=dados["N2O_CO2eq_g"].cumsum()

st.line_chart(dados[["CH4_CO2eq_acum_g","N2O_CO2eq_acum_g"]])

st.subheader("Emissões acumuladas em CO2 equivalente")
st.line_chart(dados["CO2eq_acum_g"])
