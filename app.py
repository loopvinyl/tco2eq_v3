import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

# ---------- Configuração da página ----------
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

# ---------- Abas ----------
tab1, tab2, tab3, tab4 = st.tabs(["📋 Registro", "📊 Visualização", "📈 Resultados", "📑 Comparação com artigo"])

with tab1:
    st.subheader("Registrar medição")
    col1, col2 = st.columns(2)
    with col1:
        # Permitir dias personalizados
        day_options = st.session_state.data["day"].tolist() if not st.session_state.data.empty else []
        custom_day = st.number_input("Dia de amostragem", min_value=0, step=1, value=0)
        ch4 = st.number_input("CH₄ (mg/m³)", value=0.80, format="%.2f")
    with col2:
        st.write("")  # espaçamento
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

    st.subheader("📋 Medições registradas")
    if not st.session_state.data.empty:
        # Editor para remover/editar linhas
        edited_df = st.data_editor(st.session_state.data, num_rows="dynamic", use_container_width=True)
        if not edited_df.equals(st.session_state.data):
            st.session_state.data = edited_df
            st.rerun()
    else:
        st.info("Nenhuma medição ainda.")

    # Carregar dados de exemplo
    if st.button("📥 Carregar dados do artigo (Figuras 2A/2B)", use_container_width=True):
        dias = [0, 5, 10, 15, 20, 30, 40, 50]  # dias reais do artigo
        ch4_vals = [0.82, 0.58, 0.41, 0.29, 0.21, 0.12, 0.06, 0.02]
        n2o_vals = [0.14, 0.24, 0.31, 0.27, 0.19, 0.11, 0.07, 0.04]
        exemplo = pd.DataFrame({
            "day": dias,
            "CH4": ch4_vals,
            "N2O": n2o_vals,
            "timestamp": [datetime.now()] * len(dias)
        })
        st.session_state.data = exemplo
        st.success("Dados carregados com os dias exatos do artigo (0,5,10,15,20,30,40,50).")
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

        # Gráfico de concentrações
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
        data = st.session_state.data.sort_values("day").copy()
        data["Flux_CH4"] = (data["CH4"] * Q * 60) / area
        data["Flux_N2O"] = (data["N2O"] * Q * 60) / area

        # Integração (mg/m²)
        cum_ch4_mgm2 = np.trapezoid(data["Flux_CH4"], data["day"]) * 24
        cum_n2o_mgm2 = np.trapezoid(data["Flux_N2O"], data["day"]) * 24

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

        st.subheader("📊 Resultados consolidados")
        colA, colB, colC = st.columns(3)
        with colA:
            st.metric("CH₄ cumulativo (mg/m²)", f"{cum_ch4_mgm2:.2f}")
            st.metric("N₂O cumulativo (mg/m²)", f"{cum_n2o_mgm2:.2f}")
        with colB:
            st.metric("Total CH₄ emitido (kg)", f"{total_ch4_kg:.3f}")
            st.metric("Total N₂O emitido (kg)", f"{total_n2o_kg:.3f}")
        with colC:
            st.metric("CH₄-C (% C inicial)", f"{perc_C_loss:.2f}%")
            st.metric("N₂O-N (% N inicial)", f"{perc_N_loss:.2f}%")

        st.divider()
        colD, colE = st.columns(2)
        with colD:
            st.metric("🌍 GHG total (kg CO₂-eq)", f"{total_ghg:.1f}")
        with colE:
            st.metric("📦 GHG por tonelada MS", f"{ghg_per_ton:.1f} kg CO₂-eq/t")

with tab4:
    st.subheader("🔍 Comparação com a Tabela 3 do artigo (vermicompostagem)")
    st.markdown("""
    | Parâmetro | Artigo | Seu cálculo |
    |-----------|--------|-------------|
    | CH₄-C (% C inicial) | 0,13% | `{:.2f}%` |
    | N₂O-N (% N inicial) | 0,92% | `{:.2f}%` |
    | GHG total (kg CO₂-eq/t MS) | 8,1 | `{:.1f}` |
    """.format(
        perc_C_loss if 'perc_C_loss' in locals() else 0,
        perc_N_loss if 'perc_N_loss' in locals() else 0,
        ghg_per_ton if 'ghg_per_ton' in locals() else 0
    ))

    st.info("As diferenças podem ocorrer devido à área da pilha, vazão, massa inicial e à amostragem. No artigo, a área da pilha era de 1,5 m² e a massa seca era compatível com os valores aqui utilizados.")

    with st.expander("📘 Metodologia do artigo"):
        st.markdown("""
        - **Câmara de fluxo**: área 0,13 m², vazão de varredura 5 L/min.
        - **Cálculo do fluxo**: \( E_i = \frac{Y_i \cdot Q_{sw}}{A} \)
        - **Integração**: os fluxos foram integrados ao longo do tempo para obter a emissão cumulativa por unidade de área.
        - **Extrapolação**: a emissão total da pilha foi obtida multiplicando pela área superficial da pilha (1,5 m²) e convertendo para kg.
        - **Balanço de massa**: as perdas de C e N foram calculadas com base nos teores iniciais e na massa seca.
        - **GWP**: CH₄ = 25, N₂O = 298 (IPCC 2014).
        """)
