import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.title("Vermicompost GHG Monitoring Prototype")

st.header("Experiment setup")

area = st.number_input("Chamber area (m²)", value=0.13)

flow = st.number_input("Sweep air flow (L/min)", value=5.0)

start_date = st.date_input("Experiment start date")

Q = flow/1000


# dias de medição
schedule = [0,3,7,14,21,30,45,60]

st.header("Sampling schedule")

st.write(schedule)


# banco de dados em memória
if "data" not in st.session_state:

    st.session_state.data = pd.DataFrame(
        columns=["day","CH4","N2O","timestamp"]
    )


st.header("Register measurement")

day = st.selectbox("Sampling day", schedule)

ch4 = st.number_input("CH4 mg/m3")

n2o = st.number_input("N2O mg/m3")


if st.button("Save measurement"):

    new = pd.DataFrame({

        "day":[day],
        "CH4":[ch4],
        "N2O":[n2o],
        "timestamp":[datetime.now()]

    })

    st.session_state.data = pd.concat(
        [st.session_state.data,new],
        ignore_index=True
    )

    st.success("Measurement saved")


data = st.session_state.data


if len(data) > 0:

    data["Flux_CH4"] = (data["CH4"] * Q * 60) / area

    data["Flux_N2O"] = (data["N2O"] * Q * 60) / area

    data = data.sort_values("day")


    # integração temporal
    if len(data) > 1:

        data["cum_CH4"] = np.trapz(data["Flux_CH4"], data["day"])

        data["cum_N2O"] = np.trapz(data["Flux_N2O"], data["day"])


    st.subheader("Measurements")

    st.dataframe(data)


    fig, ax = plt.subplots()

    ax.plot(data["day"], data["Flux_CH4"], label="CH4")

    ax.plot(data["day"], data["Flux_N2O"], label="N2O")

    ax.set_xlabel("Days")

    ax.set_ylabel("Flux mg m⁻² h⁻¹")

    ax.legend()

    st.pyplot(fig)
