import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.title("Vermicompost Emissions Model")

st.header("Chamber Parameters")

area = st.number_input("Chamber area (m²)", value=0.13)
flow = st.number_input("Sweep air flow (L/min)", value=5.0)

Q = flow / 1000

st.header("Gas Sampling Campaigns")

days_gas = [0,3,7,14,21,30,45,60]

gas_data = pd.DataFrame({
    "Day":days_gas,
    "CH4 mg/m3":[0.0]*8,
    "N2O mg/m3":[0.0]*8,
    "NH3 mg/m3":[0.0]*8
})

gas_df = st.data_editor(gas_data)

st.header("Material Samples")

days_material = [0,30,60]

mat_data = pd.DataFrame({
    "Day":days_material,
    "Mass kg":[0.0]*3,
    "C %":[0.0]*3,
    "N %":[0.0]*3
})

mat_df = st.data_editor(mat_data)

if st.button("Calculate emissions"):

    gas_df["Flux_CH4"] = (gas_df["CH4 mg/m3"] * Q * 60) / area
    gas_df["Flux_N2O"] = (gas_df["N2O mg/m3"] * Q * 60) / area
    gas_df["Flux_NH3"] = (gas_df["NH3 mg/m3"] * Q * 60) / area

    st.subheader("Gas Flux")

    st.dataframe(gas_df)

    mat_df["C_total"] = mat_df["Mass kg"] * mat_df["C %"] / 100
    mat_df["N_total"] = mat_df["Mass kg"] * mat_df["N %"] / 100

    C0 = mat_df.loc[0,"C_total"]
    N0 = mat_df.loc[0,"N_total"]

    mat_df["C_loss"] = C0 - mat_df["C_total"]
    mat_df["N_loss"] = N0 - mat_df["N_total"]

    st.subheader("Material Balance")

    st.dataframe(mat_df)

    fig, ax = plt.subplots()

    ax.plot(gas_df["Day"], gas_df["Flux_CH4"], label="CH4")
    ax.plot(gas_df["Day"], gas_df["Flux_N2O"], label="N2O")
    ax.plot(gas_df["Day"], gas_df["Flux_NH3"], label="NH3")

    ax.set_xlabel("Days")
    ax.set_ylabel("Flux (mg m-2 h-1)")
    ax.legend()

    st.pyplot(fig)
