import streamlit as st
import pandas as pd
import os

st.title("Monitoramento de Gases - Vermicompostagem")

arquivo = "dados_emissoes.csv"

# Se o arquivo não existir, cria um exemplo
if not os.path.exists(arquivo):

    dados_exemplo = pd.DataFrame({
        "timestamp":[
        "2026-05-01 10:00",
        "2026-05-01 10:05",
        "2026-05-01 10:10",
        "2026-05-01 10:15",
        "2026-05-01 10:20"
        ],

        "CH4_ppm":[1.82,1.79,1.76,1.74,1.72],
        "N2O_ppm":[0.34,0.36,0.40,0.44,0.47],
        "CO2_ppm":[410,412,415,418,420],
        "temperature":[25.2,25.4,25.6,25.7,25.9]
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

st.line_chart(dados["temperature"])
