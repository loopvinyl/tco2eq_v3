import streamlit as st
import pandas as pd
import os

st.title("Monitoramento de Gases - Vermicompostagem")

arquivo = "dados_emissoes.csv"

# Se o arquivo não existir, cria um exemplo
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

        "chamber_id":[1,1,1,1,1,1,1,1,1,1,1],

        "CH4_ppm":[2.10,1.95,1.70,1.40,1.10,0.85,0.65,0.50,0.35,0.25,0.18],
        "N2O_ppm":[0.20,0.28,0.45,0.70,0.90,1.05,0.95,0.75,0.55,0.35,0.22],
        "CO2_ppm":[410,415,420,425,430,435,438,440,442,444,445],

        "temperature_C":[25.1,25.4,25.7,26.0,26.3,26.6,26.8,27.0,27.2,27.4,27.6],

        "pressure_kPa":[101.3,101.2,101.2,101.1,101.1,101.0,101.0,100.9,100.9,100.8,100.8],

        "humidity_percent":[60,61,62,63,64,65,65,66,66,67,67]
    })

    dados_exemplo.to_csv(arquivo,index=False)

# Ler CSV
dados = pd.read_csv(arquivo)

# Converter timestamp
dados["timestamp"] = pd.to_datetime(dados["timestamp"])

# Definir timestamp como índice
dados = dados.set_index("timestamp")

st.subheader("Dados coletados do analisador")

st.dataframe(dados)

st.subheader("Concentração de CH4 e N2O (ppm)")

st.line_chart(dados[["CH4_ppm","N2O_ppm"]])

st.subheader("Concentração de CO2")

st.line_chart(dados["CO2_ppm"])

st.subheader("Temperatura do sistema")

st.line_chart(dados["temperature_C"])
