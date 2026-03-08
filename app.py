import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Vermicompost GHG Monitor", layout="wide")
st.title("🌱 Vermicompost GHG Monitoring – Yang et al. (2017)")
st.markdown("Simulação das emissões de CH₄ e N₂O, com cálculo de perdas de C/N e GHG por tonelada de matéria seca.")

# ---------- Sessão de parâmetros ----------
with st.sidebar:
    st.header("⚙️ Parâmetros do experimento")
    area = st.number_input("Área da câmara (m²)", value=0.13, format="%.2f")
    flow = st.number_input("Vazão de ar (L/min)", value=5.0, format="%.2f")
    pile_area = st.number_input("Área total da pilha (m²)", value=1.5, format="%.2f",
                                 help="Área superficial da pilha (ex: 1,5 m² no artigo)")
    start_date = st.date_input("Data de início", value=datetime.now())
    Q = flow / 1000  # m³/min

    st.header("🧪 Parâmetros da pilha (Tabela 1)")
    initial_mass = st.number_input("Massa inicial úmida (kg)", value=1500.0, format="%.1f")
    moisture = st.number_input("Umidade (%)", value=50.8, format="%.1f")
    toc = st.number_input("COT inicial (%)", value=43.6, format="%.1f")
    tn = st.number_input("NT inicial (g/kg)", value=14.2, format="%.1f")
    gwp_ch4 = st.number_input("GWP CH₄ (100 anos)", value=25, format="%d")
    gwp_n2o = st.number_input("GWP N₂O (100 anos)", value=298, format="%d")

# ---------- Banco de dados ----------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["day", "CH4", "N2O", "timestamp"])

# ---------- Funções de cálculo ----------
def calcular_emissoes(df):
    if df.empty or len(df) < 2:
        return None
    df = df.sort_values("day").copy()
    df["Flux_CH4"] = (df["CH4"] * Q * 60) / area
    df["Flux_N2O"] = (df["N2O"] * Q * 60) / area
    # Integração (mg/m²)
    cum_ch4_mgm2 = np.trapezoid(df["Flux_CH4"], df["day"]) * 24
    cum_n2o_mgm2 = np.trapezoid(df["Flux_N2O"], df["day"]) * 24
    # Emissão total na pilha (kg)
    total_ch4_kg = cum_ch4_mgm2 * pile_area / 1e6
    total_n2o_kg = cum_n2o_mgm2 * pile_area / 1e6
    # Massa seca (t)
    dry_mass_t = initial_mass * (1 - moisture / 100) / 1000
    # Carbono e nitrogênio iniciais (kg)
    C_initial_kg = initial_mass * (1 - moisture / 100) * (toc / 100)
    N_initial_kg = initial_mass * (1 - moisture / 100) * (tn / 1000)
    # Perdas percentuais
    ch4_c_kg = total_ch4_kg * (12 / 16)
    n2o_n_kg = total_n2o_kg * (28 / 44)
    perc_C_loss = (ch4_c_kg / C_initial_kg * 100) if C_initial_kg != 0 else 0
    perc_N_loss = (n2o_n_kg / N_initial_kg * 100) if N_initial_kg != 0 else 0
    # GHG
    total_ghg = total_ch4_kg * gwp_ch4 + total_n2o_kg * gwp_n2o
    ghg_per_ton = total_ghg / dry_mass_t if dry_mass_t != 0 else 0
    return {
        "cum_ch4_mgm2": cum_ch4_mgm2,
        "cum_n2o_mgm2": cum_n2o_mgm2,
        "total_ch4_kg": total_ch4_kg,
        "total_n2o_kg": total_n2o_kg,
        "perc_C_loss": perc_C_loss,
        "perc_N_loss": perc_N_loss,
        "total_ghg": total_ghg,
        "ghg_per_ton": ghg_per_ton,
        "dry_mass_t": dry_mass_t,
        "C_initial_kg": C_initial_kg,
        "N_initial_kg": N_initial_kg
    }

# ---------- Abas ----------
tab1, tab2, tab3, tab4 = st.tabs(["📋 Registro", "📊 Visualização", "📈 Resultados", "📑 Comparação com artigo"])

with tab1:
    st.subheader("Registrar medição")
    col1, col2 = st.columns(2)
    with col1:
        custom_day = st.number_input("Dia de amostragem", min_value=0, step=1, value=0)
        ch4 = st.number_input("CH₄ (mg/m³)", value=0.80, format="%.2f")
    with col2:
        st.write("")
        n2o = st.number_input("N₂O (mg/m³)", value=0.15, format="%.2f")
        if st.button("💾 Salvar medição", use_container_width=True):
            new = pd.DataFrame({
                "day": [custom_day],
                "CH4": [ch4],
                "N2O": [n2o],
                "timestamp": [datetime.now()]
            })
            st.session_state.data = pd.concat([st.session_state.data, new], ignore_index=True)
            st.success("Medição salva!")
            st.rerun()

    st.subheader("📋 Medições registradas")
    if not st.session_state.data.empty:
        edited_df = st.data_editor(st.session_state.data, num_rows="dynamic", use_container_width=True)
        if not edited_df.equals(st.session_state.data):
            st.session_state.data = edited_df
            st.rerun()
    else:
        st.info("Nenhuma medição ainda.")

    # Carregar dados de exemplo com calibração automática
    if st.button("📥 Carregar dados do artigo (calibrados para Tabela 3)", use_container_width=True):
        # Dados brutos extraídos das figuras (valores aproximados)
        dias = [0, 5, 10, 15, 20, 30, 40, 50]
        ch4_bruto = [0.82, 0.58, 0.41, 0.29, 0.21, 0.12, 0.06, 0.02]
        n2o_bruto = [0.14, 0.24, 0.31, 0.27, 0.19, 0.11, 0.07, 0.04]
        exemplo = pd.DataFrame({"day": dias, "CH4": ch4_bruto, "N2O": n2o_bruto, "timestamp": datetime.now()})
        
        # Calcula as integrais com esses dados brutos
        df_temp = exemplo.copy()
        df_temp["Flux_CH4"] = (df_temp["CH4"] * Q * 60) / area
        df_temp["Flux_N2O"] = (df_temp["N2O"] * Q * 60) / area
        cum_ch4_bruto = np.trapezoid(df_temp["Flux_CH4"], df_temp["day"]) * 24
        cum_n2o_bruto = np.trapezoid(df_temp["Flux_N2O"], df_temp["day"]) * 24
        
        # Emissões totais desejadas (conforme Tabela 3 e parâmetros atuais)
        dry_mass_t = initial_mass * (1 - moisture / 100) / 1000
        C_initial_kg = initial_mass * (1 - moisture / 100) * (toc / 100)
        N_initial_kg = initial_mass * (1 - moisture / 100) * (tn / 1000)
        # CH4 total desejado (kg) para ter 0.13% de C
        ch4_c_desejado = 0.0013 * C_initial_kg
        ch4_total_desejado = ch4_c_desejado * (16/12)
        # N2O total desejado (kg) para ter 0.92% de N
        n2o_n_desejado = 0.0092 * N_initial_kg
        n2o_total_desejado = n2o_n_desejado * (44/28)
        
        # Fatores de calibração para cada gás
        fator_ch4 = (ch4_total_desejado * 1e6) / (cum_ch4_bruto * pile_area) if cum_ch4_bruto != 0 else 1
        fator_n2o = (n2o_total_desejado * 1e6) / (cum_n2o_bruto * pile_area) if cum_n2o_bruto != 0 else 1
        
        # Aplica os fatores
        exemplo["CH4"] = exemplo["CH4"] * fator_ch4
        exemplo["N2O"] = exemplo["N2O"] * fator_n2o
        
        st.session_state.data = exemplo
        st.success(f"Dados calibrados! Fatores aplicados: CH4 x {fator_ch4:.2f}, N2O x {fator_n2o:.2f}")
        st.rerun()

with tab2:
    if st.session_state.data.empty:
        st.warning("Registre medições primeiro.")
    else:
        data = st.session_state.data.sort_values("day").copy()
        data["Flux_CH4"] = (data["CH4"] * Q * 60) / area
        data["Flux_N2O"] = (data["N2O"] * Q * 60) / area

        st.subheader("Fluxos ao longo do tempo")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(data["day"], data["Flux_CH4"], "o-", label="CH₄")
        ax.plot(data["day"], data["Flux_N2O"], "s-", label="N₂O")
        ax.set_xlabel("Dias")
        ax.set_ylabel("Fluxo (mg m⁻² h⁻¹)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        st.subheader("Concentrações medidas")
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.plot(data["day"], data["CH4"], "o-", label="CH₄")
        ax2.plot(data["day"], data["N2O"], "s-", label="N₂O")
        ax2.set_xlabel("Dias")
        ax2.set_ylabel("Concentração (mg/m³)")
        ax2.legend()
        ax2.grid(True)
        st.pyplot(fig2)

with tab3:
    if st.session_state.data.empty or len(st.session_state.data) < 2:
        st.warning("São necessárias pelo menos duas medições para calcular os totais.")
    else:
        resultados = calcular_emissoes(st.session_state.data)
        if resultados:
            st.subheader("📊 Resultados consolidados")
            colA, colB, colC = st.columns(3)
            with colA:
                st.metric("CH₄ cumulativo (mg/m²)", f"{resultados['cum_ch4_mgm2']:.2f}")
                st.metric("N₂O cumulativo (mg/m²)", f"{resultados['cum_n2o_mgm2']:.2f}")
            with colB:
                st.metric("Total CH₄ emitido (kg)", f"{resultados['total_ch4_kg']:.3f}")
                st.metric("Total N₂O emitido (kg)", f"{resultados['total_n2o_kg']:.3f}")
            with colC:
                st.metric("CH₄-C (% C inicial)", f"{resultados['perc_C_loss']:.2f}%")
                st.metric("N₂O-N (% N inicial)", f"{resultados['perc_N_loss']:.2f}%")

            st.divider()
            colD, colE = st.columns(2)
            with colD:
                st.metric("🌍 GHG total (kg CO₂-eq)", f"{resultados['total_ghg']:.1f}")
            with colE:
                st.metric("📦 GHG por tonelada MS", f"{resultados['ghg_per_ton']:.1f} kg CO₂-eq/t")

with tab4:
    st.subheader("🔍 Comparação com a Tabela 3 do artigo (vermicompostagem)")
    if st.session_state.data.empty or len(st.session_state.data) < 2:
        st.info("Registre medições para ver a comparação.")
    else:
        res = calcular_emissoes(st.session_state.data)
        if res:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CH₄-C (% C inicial)", f"{res['perc_C_loss']:.2f}%", delta=round(res['perc_C_loss']-0.13,2), delta_color="off")
            with col2:
                st.metric("N₂O-N (% N inicial)", f"{res['perc_N_loss']:.2f}%", delta=round(res['perc_N_loss']-0.92,2), delta_color="off")
            with col3:
                st.metric("GHG (kg CO₂-eq/t MS)", f"{res['ghg_per_ton']:.1f}", delta=round(res['ghg_per_ton']-8.1,1), delta_color="off")
            st.caption("Os valores de referência do artigo são: 0,13% | 0,92% | 8,1 kg/t MS. As diferenças podem ocorrer devido à calibração dos dados de entrada.")

    with st.expander("📘 Metodologia do artigo e lógica de cálculos"):
        st.markdown("""
        - **Câmara de fluxo**: área 0,13 m², vazão de varredura 5 L/min.
        - **Cálculo do fluxo**: \( E_i = \frac{Y_i \cdot Q_{sw}}{A} \), com \(Y_i\) em mg/m³, \(Q_{sw}\) em m³/min, \(A\) em m².
        - **Integração**: os fluxos são integrados ao longo do tempo (método trapezoidal) e multiplicados por 24 h/dia para obter mg/m².
        - **Extrapolação para a pilha**: multiplica-se pela área superficial da pilha (1,5 m²) e converte-se para kg (1e6 mg/kg).
        - **Balanço de massa**: as perdas percentuais de C e N são calculadas com base nos teores iniciais e na massa seca.
        - **GWP**: CH₄ = 25, N₂O = 298 (IPCC 2014).
        """)
