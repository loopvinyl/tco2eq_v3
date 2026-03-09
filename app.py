import streamlit as st
import pandas as pd

st.title("Monitoramento de Gases - Vermicompostagem")

dados = pd.read_csv("dados_emissoes.csv")

st.subheader("Dados coletados")
st.dataframe(dados)

st.subheader("Emissões ao longo do tempo")

st.line_chart(dados.set_index("dia")[["CH4","N2O"]])
