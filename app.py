import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Vermicompost GHG Monitoring Prototype")

# parâmetros da câmara
st.header("Chamber parameters")

area = st.number_input("Chamber area (m²)", value=0.13)

flow = st.number_input("Sweep air flow (L/min)", value=5.0)

Q = flow / 1000


# valores default do artigo
default_data = pd.DataFrame({

"Day":[0,3,7,14,21,30,45,60],

"CH4 mg/m3":[2.1,2.5,3.2,4.5,4.0,3.5,3.0,2.4],

"N2O mg/m3":[0.8,1.0,1.2,1.5,1.3,1.1,1.0,0.9]

})


# manter dados durante a sessão
if "data" not in st.session_state:

    st.session_state.data = default_data.copy()


st.header("Gas measurements")

df = st.data_editor(st.session_state.data)


st.session_state.data = df


if st.button("Calculate emissions"):

    df["Flux_CH4"] = (df["CH4 mg/m3"] * Q * 60) / area

    df["Flux_N2O"] = (df["N2O mg/m3"] * Q * 60) / area


    # integração temporal
    cum_ch4 = np.trapz(df["Flux_CH4"], df["Day"])

    cum_n2o = np.trapz(df["Flux_N2O"], df["Day"])


    st.subheader("Flux results")

    st.dataframe(df)


    st.subheader("Cumulative emissions")

    st.write("CH4 cumulative emission:", cum_ch4)

    st.write("N2O cumulative emission:", cum_n2o)


    fig, ax = plt.subplots()

    ax.plot(df["Day"], df["Flux_CH4"], label="CH4")

    ax.plot(df["Day"], df["Flux_N2O"], label="N2O")

    ax.set_xlabel("Days")

    ax.set_ylabel("Flux mg m⁻² h⁻¹")

    ax.legend()

    st.pyplot(fig)
