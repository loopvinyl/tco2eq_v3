import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Vermicompost GHG Monitor", layout="wide")

st.title("Vermicompost GHG Monitoring Prototype")
st.write("Simulation based on experimental protocol from Yang et al. 2017")

# -----------------------------
# SIDEBAR – EXPERIMENT SETTINGS
# -----------------------------

with st.sidebar:

    st.header("Chamber parameters")

    area = st.number_input("Chamber area (m²)", value=0.13)

    flow = st.number_input("Air flow (L/min)", value=5.0)

    pile_area = st.number_input("Pile surface area (m²)", value=1.5)

    Q = flow / 1000

    st.header("Pile parameters")

    initial_mass = st.number_input("Initial wet mass (kg)", value=1500.0)

    moisture = st.number_input("Moisture (%)", value=50.8)

    toc = st.number_input("Total organic carbon (%)", value=43.6)

    tn = st.number_input("Total nitrogen (g/kg)", value=14.2)

    gwp_ch4 = st.number_input("GWP CH4", value=25)

    gwp_n2o = st.number_input("GWP N2O", value=298)

# -----------------------------
# DATABASE
# -----------------------------

if "data" not in st.session_state:

    st.session_state.data = pd.DataFrame(
        columns=["day","CH4","N2O","timestamp"]
    )

# -----------------------------
# FUNCTIONS
# -----------------------------

def calculate_emissions(df):

    df = df.sort_values("day").copy()

    df["Flux_CH4"] = (df["CH4"] * Q * 60) / area

    df["Flux_N2O"] = (df["N2O"] * Q * 60) / area

    cum_ch4 = np.trapz(df["Flux_CH4"], df["day"]) * 24
    cum_n2o = np.trapz(df["Flux_N2O"], df["day"]) * 24

    total_ch4_kg = cum_ch4 * pile_area / 1e6
    total_n2o_kg = cum_n2o * pile_area / 1e6

    dry_mass_t = initial_mass * (1 - moisture/100) / 1000

    C_initial = initial_mass * (1 - moisture/100) * (toc/100)
    N_initial = initial_mass * (1 - moisture/100) * (tn/1000)

    ch4_c = total_ch4_kg * (12/16)
    n2o_n = total_n2o_kg * (28/44)

    perc_C = ch4_c / C_initial * 100
    perc_N = n2o_n / N_initial * 100

    ghg_total = total_ch4_kg * gwp_ch4 + total_n2o_kg * gwp_n2o

    ghg_per_ton = ghg_total / dry_mass_t

    return df, cum_ch4, cum_n2o, total_ch4_kg, total_n2o_kg, perc_C, perc_N, ghg_total, ghg_per_ton

# -----------------------------
# TABS
# -----------------------------

tab1, tab2, tab3, tab4 = st.tabs(
[
"Measurements",
"Graphs",
"Results",
"Article comparison"
]
)

# -----------------------------
# TAB 1 – MEASUREMENTS
# -----------------------------

with tab1:

    st.subheader("Register measurement")

    col1,col2 = st.columns(2)

    with col1:

        day = st.number_input("Day", value=0)

        ch4 = st.number_input("CH4 (mg/m3)", value=0.80)

    with col2:

        n2o = st.number_input("N2O (mg/m3)", value=0.15)

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

            st.success("Saved")

            st.rerun()

    st.subheader("Measurements table")

    st.dataframe(st.session_state.data)

    # Example data

    if st.button("Load article example data"):

        days=[0,5,10,15,20,30,40,50]

        ch4=[22.1,15.6,11.0,7.8,5.6,3.1,1.5,0.6]

        n2o=[3.8,6.5,8.3,7.2,5.0,2.9,1.8,1.0]

        example=pd.DataFrame({

        "day":days,
        "CH4":ch4,
        "N2O":n2o,
        "timestamp":datetime.now()

        })

        st.session_state.data=example

        st.success("Example data loaded")

        st.rerun()

# -----------------------------
# TAB 2 – GRAPHS
# -----------------------------

with tab2:

    if len(st.session_state.data) > 1:

        df, *_ = calculate_emissions(st.session_state.data)

        fig,ax = plt.subplots()

        ax.plot(df["day"],df["Flux_CH4"],marker="o",label="CH4")

        ax.plot(df["day"],df["Flux_N2O"],marker="o",label="N2O")

        ax.set_xlabel("Days")

        ax.set_ylabel("Flux mg m-2 h-1")

        ax.legend()

        st.pyplot(fig)

# -----------------------------
# TAB 3 – RESULTS
# -----------------------------

with tab3:

    if len(st.session_state.data) > 1:

        df,cum_ch4,cum_n2o,total_ch4,total_n2o,perc_C,perc_N,ghg_total,ghg_per_ton = calculate_emissions(st.session_state.data)

        col1,col2,col3 = st.columns(3)

        col1.metric("CH4 cumulative (mg/m2)",f"{cum_ch4:.1f}")

        col2.metric("N2O cumulative (mg/m2)",f"{cum_n2o:.1f}")

        col3.metric("Total GHG (kg CO2-eq)",f"{ghg_total:.2f}")

        st.divider()

        col4,col5 = st.columns(2)

        col4.metric("CH4-C (% C initial)",f"{perc_C:.2f}%")

        col5.metric("N2O-N (% N initial)",f"{perc_N:.2f}%")

        st.divider()

        ghg_model = ghg_per_ton
        ghg_artigo = round(ghg_model,1)

        col6,col7 = st.columns(2)

        col6.metric(
        "GHG model (kg CO2-eq/t)",
        f"{ghg_model:.2f}"
        )

        col7.metric(
        "Article equivalent",
        f"{ghg_artigo:.1f}"
        )

# -----------------------------
# TAB 4 – ARTICLE COMPARISON
# -----------------------------

with tab4:

    st.subheader("Reference values from article")

    ref=pd.DataFrame({

    "Parameter":[
    "CH4-C (% C initial)",
    "N2O-N (% N initial)",
    "GHG (kg CO2-eq/t DM)"
    ],

    "Article":[
    "0.13",
    "0.92",
    "8.1"
    ]

    })

    st.table(ref)

    if len(st.session_state.data) > 1:

        _,_,_,_,_,perc_C,perc_N,_,ghg_per_ton = calculate_emissions(st.session_state.data)

        st.subheader("Model results")

        result=pd.DataFrame({

        "Parameter":[
        "CH4-C (% C initial)",
        "N2O-N (% N initial)",
        "GHG (kg CO2-eq/t DM)"
        ],

        "Model":[
        f"{perc_C:.2f}",
        f"{perc_N:.2f}",
        f"{ghg_per_ton:.2f}"
        ]

        })

        st.table(result)
