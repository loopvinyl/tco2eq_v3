import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Vermicompost GHG Emissions Model")

st.header("Chamber parameters")

area = st.number_input("Chamber area (m²)", value=0.13)

flow = st.number_input("Sweep air flow (L/min)", value=5.0)

Q = flow/1000


st.header("Gas sampling campaigns")

gas_default = pd.DataFrame({

"Day":[0,3,7,14,21,30,45,60],

"CH4 mg/m3":[2.1,2.5,3.2,4.5,4.0,3.5,3.0,2.4],

"N2O mg/m3":[0.8,1.0,1.2,1.5,1.3,1.1,1.0,0.9]

})

gas_df = st.data_editor(gas_default)


st.header("Material samples")

mat_default = pd.DataFrame({

"Day":[0,30,60],

"Mass kg":[100,75,60],

"C %":[45,36,30],

"N %":[2.0,2.4,2.8]

})

mat_df = st.data_editor(mat_default)


if st.button("Calculate emissions"):

    gas_df["Flux_CH4"] = (gas_df["CH4 mg/m3"] * Q * 60) / area

    gas_df["Flux_N2O"] = (gas_df["N2O mg/m3"] * Q * 60) / area


    gas_df["CO2eq"] = gas_df["Flux_CH4"]*25 + gas_df["Flux_N2O"]*298


    st.subheader("Gas Flux")

    st.dataframe(gas_df)


    mat_df["C_total"] = mat_df["Mass kg"] * mat_df["C %"] / 100

    mat_df["N_total"] = mat_df["Mass kg"] * mat_df["N %"] / 100


    C0 = mat_df.loc[0,"C_total"]

    N0 = mat_df.loc[0,"N_total"]


    mat_df["C_loss"] = C0 - mat_df["C_total"]

    mat_df["N_loss"] = N0 - mat_df["N_total"]


    st.subheader("Material balance")

    st.dataframe(mat_df)


    fig, ax = plt.subplots()

    ax.plot(gas_df["Day"], gas_df["Flux_CH4"], label="CH4")

    ax.plot(gas_df["Day"], gas_df["Flux_N2O"], label="N2O")

    ax.set_xlabel("Days")

    ax.set_ylabel("Flux (mg m⁻² h⁻¹)")

    ax.legend()

    st.pyplot(fig)
