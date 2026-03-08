import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="GHG Compost Monitor", layout="wide")

st.title("GHG Monitoring Prototype (CH4 + N2O)")
st.write("Experimental protocol simulation based on Yang et al.")

# -------------------------
# SIDEBAR SETTINGS
# -------------------------

with st.sidebar:

    st.header("Chamber parameters")

    area = st.number_input("Chamber area (m²)", value=0.13)
    flow = st.number_input("Air flow (L/min)", value=5.0)
    pile_area = st.number_input("Pile surface area (m²)", value=1.5)

    Q = flow / 1000

    st.header("Pile properties")

    initial_mass = st.number_input("Initial mass (kg)", value=1500.0)
    moisture = st.number_input("Moisture (%)", value=50.8)
    toc = st.number_input("TOC (%)", value=43.6)
    tn = st.number_input("Total N (g/kg)", value=14.2)

    st.header("GWP")

    gwp_ch4 = st.number_input("CH4 GWP", value=25)
    gwp_n2o = st.number_input("N2O GWP", value=298)

# -------------------------
# DEFAULT SAMPLING SCHEDULE
# -------------------------

sampling_days = [0,5,10,15,20,30,40,50]

# -------------------------
# DATABASE
# -------------------------

if "data" not in st.session_state:

    st.session_state.data = pd.DataFrame({
        "day":sampling_days,
        "CH4":[0.8]*len(sampling_days),
        "N2O":[0.15]*len(sampling_days),
        "timestamp":[datetime.now()]*len(sampling_days)
    })

# -------------------------
# FUNCTIONS
# -------------------------

def calculate_emissions(df):

    df = df.sort_values("day").copy()

    df["Flux_CH4"] = (df["CH4"] * Q * 60) / area
    df["Flux_N2O"] = (df["N2O"] * Q * 60) / area

    cum_ch4 = np.trapezoid(df["Flux_CH4"], df["day"]) * 24
    cum_n2o = np.trapezoid(df["Flux_N2O"], df["day"]) * 24

    total_ch4 = cum_ch4 * pile_area / 1e6
    total_n2o = cum_n2o * pile_area / 1e6

    dry_mass_t = initial_mass * (1 - moisture/100) / 1000

    C_initial = initial_mass * (1 - moisture/100) * (toc/100)
    N_initial = initial_mass * (1 - moisture/100) * (tn/1000)

    ch4_c = total_ch4 * (12/16)
    n2o_n = total_n2o * (28/44)

    perc_C = ch4_c / C_initial * 100
    perc_N = n2o_n / N_initial * 100

    ghg_total = total_ch4 * gwp_ch4 + total_n2o * gwp_n2o

    ghg_per_ton = ghg_total / dry_mass_t

    return df,cum_ch4,cum_n2o,total_ch4,total_n2o,perc_C,perc_N,ghg_total,ghg_per_ton

# -------------------------
# TABS
# -------------------------

tab1,tab2,tab3,tab4 = st.tabs([
"Measurements",
"Graphs",
"Results",
"Export"
])

# -------------------------
# TAB 1 – MEASUREMENTS
# -------------------------

with tab1:

    st.subheader("Sampling schedule")

    st.write("Default sampling days based on experimental protocol")

    edited = st.data_editor(
        st.session_state.data,
        num_rows="fixed"
    )

    st.session_state.data = edited

# -------------------------
# TAB 2 – GRAPHS
# -------------------------

with tab2:

    df,*_ = calculate_emissions(st.session_state.data)

    fig,ax = plt.subplots()

    ax.plot(df["day"],df["Flux_CH4"],marker="o",label="CH4 flux")

    ax.plot(df["day"],df["Flux_N2O"],marker="o",label="N2O flux")

    ax.set_xlabel("Days")
    ax.set_ylabel("Flux mg m⁻² h⁻¹")
    ax.legend()

    st.pyplot(fig)

# -------------------------
# TAB 3 – RESULTS
# -------------------------

with tab3:

    df,cum_ch4,cum_n2o,total_ch4,total_n2o,perc_C,perc_N,ghg_total,ghg_per_ton = calculate_emissions(st.session_state.data)

    col1,col2,col3 = st.columns(3)

    col1.metric("CH4 cumulative (mg m-2)",f"{cum_ch4:.2f}")
    col2.metric("N2O cumulative (mg m-2)",f"{cum_n2o:.2f}")
    col3.metric("Total GHG (kg CO2-eq)",f"{ghg_total:.2f}")

    st.divider()

    col4,col5 = st.columns(2)

    col4.metric("CH4-C loss (%)",f"{perc_C:.3f}")
    col5.metric("N2O-N loss (%)",f"{perc_N:.3f}")

    st.divider()

    st.metric("GHG intensity (kg CO2-eq t⁻¹ DM)",f"{ghg_per_ton:.2f}")

# -------------------------
# TAB 4 – EXPORT
# -------------------------

with tab4:

    csv = st.session_state.data.to_csv(index=False)

    st.download_button(
        "Download dataset CSV",
        csv,
        "ghg_dataset.csv",
        "text/csv"
    )
