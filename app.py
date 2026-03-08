"""
Vermi-IoT Sentinel
Sistema de Monitoramento Remoto de Emissões de GEE (CH4 e N2O) em Vermicompostagem
Baseado no artigo de Yang et al. (2017) e alinhado ao Edital CONIF/CONTIC nº 02/2026
ODS 12 e 13
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os
import socket

# Configuração da página
st.set_page_config(page_title="Vermi-IoT Sentinel", layout="wide")

# =============================================================================
# Título e cabeçalho
# =============================================================================
st.title("🌱 Vermi-IoT Sentinel")
st.markdown("**Sistema de Monitoramento Remoto de Emissões GEE (CH₄ e N₂O)**")
st.markdown("ODS 12 (Consumo e Produção Responsáveis) e ODS 13 (Ação Contra a Mudança Global do Clima)")
st.markdown("Edital CONIF/CONTIC nº 02/2026 – Inovações para o Desenvolvimento Sustentável com Conectividade")

# =============================================================================
# Barra lateral com parâmetros fixos (baseados no artigo)
# =============================================================================
with st.sidebar:
    st.header("⚙️ Parâmetros da Câmara e Pilha")

    # Câmara de fluxo (Emission Isolation Flux Chamber)
    area_chamber = st.number_input("Área da câmara (m²)", value=0.13, format="%.2f",
                                   help="Área da base da câmara (16\" diâmetro ≈ 0.13 m²)")
    flow_l_min = st.number_input("Vazão de ar de arraste (L/min)", value=5.0, format="%.2f",
                                 help="Sweep air flow rate")
    Q = flow_l_min / 1000  # m³/min

    st.divider()
    st.subheader("📦 Dimensões da Pilha")
    pile_area = st.number_input("Área superficial total da pilha (m²)", value=1.5, format="%.2f")
    initial_mass = st.number_input("Massa inicial de resíduos (kg)", value=1500.0, format="%.1f")
    moisture = st.number_input("Umidade (%)", value=50.8, format="%.1f")
    toc = st.number_input("Teor inicial de C orgânico total (%)", value=43.6, format="%.1f")
    tn = st.number_input("Teor inicial de N total (g kg⁻¹)", value=14.2, format="%.1f")

    st.divider()
    st.subheader("🌍 Fatores de Conversão (GWP 100 anos)")
    gwp_ch4 = st.number_input("GWP CH₄", value=25, help="IPCC 2014")
    gwp_n2o = st.number_input("GWP N₂O", value=298, help="IPCC 2014")

# =============================================================================
# Inicialização da sessão (armazenamento dos dados)
# =============================================================================
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = pd.DataFrame(columns=["timestamp", "CH4_mg_m3", "N2O_mg_m3", "source"])

if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

# =============================================================================
# Funções auxiliares
# =============================================================================
def calculate_fluxes(row):
    """Calcula fluxos horários e diários a partir da concentração."""
    ch4_mg_m3 = row["CH4_mg_m3"]
    n2o_mg_m3 = row["N2O_mg_m3"]
    flux_ch4_h = (ch4_mg_m3 * Q * 60) / area_chamber  # mg/m².h
    flux_n2o_h = (n2o_mg_m3 * Q * 60) / area_chamber
    flux_ch4_d = flux_ch4_h * 24
    flux_n2o_d = flux_n2o_h * 24
    return pd.Series([flux_ch4_h, flux_n2o_h, flux_ch4_d, flux_n2o_d])

def integrate_emissions(df):
    """Integra as emissões ao longo do tempo (método trapezoidal)."""
    if len(df) < 2:
        return 0, 0
    days = (df["timestamp"] - df["timestamp"].iloc[0]).dt.total_seconds() / 86400
    cum_ch4 = np.trapezoid(df["Flux_CH4_d"], days)
    cum_n2o = np.trapezoid(df["Flux_N2O_d"], days)
    return cum_ch4, cum_n2o

def simulate_sensor_reading():
    """
    Gera uma leitura simulada baseada nas curvas do artigo com ruído.
    - CH4: decaimento exponencial de ~150 mg/m³ para ~5 mg/m³.
    - N2O: pico por volta do dia 15 (~6 mg/m³) seguido de declínio.
    """
    if st.session_state.sensor_data.empty:
        base_day = 0
    else:
        first_time = st.session_state.sensor_data["timestamp"].min()
        base_day = (datetime.now() - first_time).total_seconds() / 86400

    ch4_base = 150 * np.exp(-0.1 * base_day) + 5
    n2o_base = 6 * np.sin(base_day / 10) + 2
    ch4 = max(0, ch4_base + np.random.normal(0, 3))
    n2o = max(0, n2o_base + np.random.normal(0, 0.2))
    return ch4, n2o

def read_tcp_sensor(host, port):
    """Lê uma linha de dados do sensor via TCP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect((host, port))
            data = s.recv(1024).decode().strip()
            if data:
                ch4_str, n2o_str = data.split(',')
                return float(ch4_str), float(n2o_str)
    except Exception as e:
        st.error(f"Erro na leitura TCP: {e}")
    return None, None

# =============================================================================
# Abas principais
# =============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📡 Monitoramento em Tempo Real",
    "📊 Histórico e Análise",
    "🔧 Configurações dos Sensores",
    "📋 Sobre o Projeto"
])

# -----------------------------------------------------------------------------
# ABA 1: Monitoramento em Tempo Real
# -----------------------------------------------------------------------------
with tab1:
    st.header("Leitura em Tempo Real dos Sensores")
    st.markdown("**Sensor acoplado à câmara de fluxo (Emission Isolation Flux Chamber)**")

    # Exibir imagem do sistema (se disponível na mesma pasta)
    image_path = "Nutriwash_System.png"
    if os.path.exists(image_path):
        st.image(image_path, caption="Diagrama do sistema Nutriwash (câmara de fluxo sobre o leito de vermicompostagem)", width=600)
    else:
        st.info("ℹ️ Para visualizar o diagrama, coloque a imagem 'Nutriwash_System.png' no mesmo diretório do script.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("✏️ Inserir Medição Manual")
        ch4_manual = st.number_input("CH₄ (mg/m³)", value=150.0, step=1.0, format="%.2f")
        n2o_manual = st.number_input("N₂O (mg/m³)", value=2.0, step=0.1, format="%.2f")
        if st.button("📥 Registrar Medição Manual"):
            new_row = pd.DataFrame({
                "timestamp": [datetime.now()],
                "CH4_mg_m3": [ch4_manual],
                "N2O_mg_m3": [n2o_manual],
                "source": ["manual"]
            })
            st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_row], ignore_index=True)
            st.success("Medição registrada manualmente!")

    with col2:
        st.subheader("🔄 Leitura Automática (Sensor)")
        if st.button("🔁 Obter nova leitura do sensor"):
            # Verifica o tipo de sensor configurado
            sensor_type = st.session_state.get("sensor_type", "Simulado")
            if sensor_type == "TCP/IP":
                host = st.session_state.get("tcp_host", "localhost")
                port = st.session_state.get("tcp_port", 5000)
                ch4, n2o = read_tcp_sensor(host, port)
                if ch4 is None or n2o is None:
                    st.error("Falha na leitura TCP. Usando simulação interna.")
                    ch4, n2o = simulate_sensor_reading()
                    source = "simulado (fallback)"
                else:
                    source = "tcp"
            else:
                ch4, n2o = simulate_sensor_reading()
                source = "simulado"

            new_row = pd.DataFrame({
                "timestamp": [datetime.now()],
                "CH4_mg_m3": [ch4],
                "N2O_mg_m3": [n2o],
                "source": [source]
            })
            st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_row], ignore_index=True)
            st.session_state.last_update = datetime.now()
            st.rerun()

        # Exibir a última medição
        if not st.session_state.sensor_data.empty:
            last = st.session_state.sensor_data.iloc[-1]
            st.metric("CH₄ (mg/m³)", f"{last['CH4_mg_m3']:.2f}")
            st.metric("N₂O (mg/m³)", f"{last['N2O_mg_m3']:.2f}")
            st.caption(f"Fonte: {last['source']} | {last['timestamp'].strftime('%d/%m/%Y %H:%M:%S')}")
        else:
            st.info("Nenhuma leitura ainda. Clique em 'Obter nova leitura' para começar.")

    # Gráfico das últimas 24 horas
    st.subheader("📈 Tendência Recente (últimas 24h)")
    if not st.session_state.sensor_data.empty:
        df_display = st.session_state.sensor_data.copy()
        # Calcular fluxos
        fluxes = df_display.apply(calculate_fluxes, axis=1)
        df_display[["Flux_CH4_h", "Flux_N2O_h", "Flux_CH4_d", "Flux_N2O_d"]] = fluxes

        cutoff = datetime.now() - timedelta(hours=24)
        df_recent = df_display[df_display["timestamp"] >= cutoff]

        if not df_recent.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_recent["timestamp"], y=df_recent["Flux_CH4_h"],
                                      mode='lines+markers', name='CH₄ (mg/m².h)'))
            fig.add_trace(go.Scatter(x=df_recent["timestamp"], y=df_recent["Flux_N2O_h"],
                                      mode='lines+markers', name='N₂O (mg/m².h)'))
            fig.update_layout(xaxis_title="Tempo", yaxis_title="Fluxo (mg/m².h)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico nas últimas 24h.")
    else:
        st.info("Nenhum dado registrado.")

# -----------------------------------------------------------------------------
# ABA 2: Histórico e Análise
# -----------------------------------------------------------------------------
with tab2:
    st.header("Análise Histórica e Balanço de Massa")

    if st.session_state.sensor_data.empty:
        st.warning("Nenhum dado disponível. Faça leituras na aba 'Monitoramento em Tempo Real'.")
    else:
        # Processar todos os dados
        df = st.session_state.sensor_data.copy().sort_values("timestamp")

        # Calcular fluxos
        fluxes = df.apply(calculate_fluxes, axis=1)
        df[["Flux_CH4_h", "Flux_N2O_h", "Flux_CH4_d", "Flux_N2O_d"]] = fluxes

        # Calcular dias desde o início
        start_time = df["timestamp"].min()
        df["day"] = (df["timestamp"] - start_time).dt.total_seconds() / 86400

        # Integração
        cum_ch4_mg_m2, cum_n2o_mg_m2 = integrate_emissions(df)

        # Balanço de massa
        dry_matter = initial_mass * (1 - moisture/100)
        initial_C_kg = dry_matter * (toc / 100)
        initial_N_kg = (tn / 1000) * dry_matter

        # Extrapolação para a pilha inteira (usando a área da pilha)
        total_ch4_kg = cum_ch4_mg_m2 * pile_area / 1e6
        total_n2o_kg = cum_n2o_mg_m2 * pile_area / 1e6

        ch4_c_kg = total_ch4_kg * (12/16)
        n2o_n_kg = total_n2o_kg * (28/44)

        ch4_c_perc = (ch4_c_kg / initial_C_kg) * 100 if initial_C_kg > 0 else 0
        n2o_n_perc = (n2o_n_kg / initial_N_kg) * 100 if initial_N_kg > 0 else 0

        total_co2eq = total_ch4_kg * gwp_ch4 + total_n2o_kg * gwp_n2o
        ghg_per_ton = (total_co2eq / dry_matter) * 1000 if dry_matter > 0 else 0

        # Exibir métricas principais
        cola, colb, colc, cold = st.columns(4)
        cola.metric("Perda CH₄-C (% C inicial)", f"{ch4_c_perc:.3f}%")
        colb.metric("Perda N₂O-N (% N inicial)", f"{n2o_n_perc:.3f}%")
        colc.metric("Total CO₂-eq (kg)", f"{total_co2eq:.2f}")
        cold.metric("Pegada GEE (kg CO₂-eq/t MS)", f"{ghg_per_ton:.2f}")

        # Gráfico de fluxo ao longo do tempo
        st.subheader("Fluxos ao Longo do Experimento")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=df["day"], y=df["Flux_CH4_h"],
                                   mode='lines+markers', name='CH₄ (mg/m².h)'))
        fig2.add_trace(go.Scatter(x=df["day"], y=df["Flux_N2O_h"],
                                   mode='lines+markers', name='N₂O (mg/m².h)'))
        fig2.update_layout(xaxis_title="Dias desde o início", yaxis_title="Fluxo (mg/m².h)")
        st.plotly_chart(fig2, use_container_width=True)

        # Tabela de dados brutos
        with st.expander("🔍 Ver dados completos (concentrações e fluxos)"):
            st.dataframe(df[["timestamp", "day", "CH4_mg_m3", "N2O_mg_m3",
                             "Flux_CH4_h", "Flux_N2O_h", "source"]])

        # Comparação com artigo (valores de referência)
        st.caption("📚 **Comparação com o artigo de Yang et al. (2017) – Tabela 3**")
        st.caption("Vermicompostagem: CH₄-C = 0.13% do C inicial, N₂O-N = 0.92% do N inicial, "
                   "GHG total = 8.1 kg CO₂-eq/t MS")
        st.caption("Os valores calculados acima são baseados nos seus dados e podem variar.")

# -----------------------------------------------------------------------------
# ABA 3: Configurações dos Sensores
# -----------------------------------------------------------------------------
with tab3:
    st.header("Configurações dos Sensores e Conectividade")

    # Escolha do tipo de sensor
    sensor_type = st.selectbox("Tipo de Sensor",
                               ["Simulado (geração interna)", "TCP/IP (sensor virtual)"],
                               index=0, key="sensor_type")

    if sensor_type == "TCP/IP (sensor virtual)":
        st.subheader("🌐 Configuração da Conexão TCP")
        tcp_host = st.text_input("Endereço do servidor", value="localhost", key="tcp_host")
        tcp_port = st.number_input("Porta", value=5000, min_value=1, max_value=65535, key="tcp_port")
        st.info("Certifique-se de que o sensor virtual (sensor_virtual.py) esteja rodando no endereço e porta indicados.")
    else:
        st.info("Modo simulado: os dados serão gerados internamente com base nas curvas do artigo.")

    # Opção de exportação
    st.divider()
    st.subheader("💾 Exportar Dados")
    if st.button("Exportar para CSV"):
        if not st.session_state.sensor_data.empty:
            csv = st.session_state.sensor_data.to_csv(index=False)
            st.download_button("📥 Download CSV", data=csv,
                               file_name=f"dados_gee_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                               mime="text/csv")
        else:
            st.warning("Nenhum dado para exportar.")

# -----------------------------------------------------------------------------
# ABA 4: Sobre o Projeto
# -----------------------------------------------------------------------------
with tab4:
    st.header("Sobre o Vermi-IoT Sentinel")

    st.markdown("""
    ### 🔬 Descrição do Projeto
    O **Vermi-IoT Sentinel** é um sistema de monitoramento remoto de emissões de gases de efeito estufa (CH₄ e N₂O) durante o processo de vermicompostagem. Utiliza uma câmara de fluxo (Emission Isolation Flux Chamber) acoplada a sensores de gases, com transmissão de dados via protocolo TCP/IP (conectividade). Os dados são processados em tempo real, gerando fluxos horários, emissões acumuladas e balanço de massa, permitindo avaliar a pegada de carbono do processo.

    ### 📚 Base Científica
    Todo o modelo de cálculos é baseado no artigo:
    > Yang, F., Li, G., Zang, B., & Zhang, Z. (2017). The Maturity and CH₄, N₂O, NH₃ Emissions from Vermicomposting with Agricultural Waste. *Compost Science & Utilization*, 25(4), 262–271.

    Os parâmetros da câmara (área 0.13 m², vazão 5 L/min) e as curvas de emissão foram extraídos desse estudo.

    ### 🌍 Alinhamento com os ODS
    - **ODS 12** (Consumo e Produção Responsáveis): Promove a gestão sustentável de resíduos orgânicos, transformando resíduos agrícolas em fertilizante de alta qualidade (vermicomposto) e reduzindo emissões.
    - **ODS 13** (Ação Contra a Mudança Global do Clima): Quantifica e permite a mitigação das emissões de gases de efeito estufa (CH₄ e N₂O) durante o tratamento de resíduos.

    ### 📡 Conectividade e Inovação
    O sistema utiliza tecnologias de conectividade (TCP/IP) para transmitir dados de sensores remotos, permitindo o monitoramento contínuo e em tempo real de múltiplas unidades de vermicompostagem espalhadas pela RFEPCT. Os dados podem ser acessados via dashboard web (Streamlit), possibilitando análise histórica, comparação com metas e emissão de relatórios.

    ### 🖼️ Diagrama do Sistema
    """)

    # Exibir imagem novamente
    if os.path.exists("Nutriwash_System.png"):
        st.image("Nutriwash_System.png", caption="Diagrama do sistema Nutriwash", width=500)
    else:
        st.info("ℹ️ Para visualizar o diagrama, coloque a imagem 'Nutriwash_System.png' no mesmo diretório do script.")

    st.markdown("""
    ### 👥 Equipe
    - Coordenador: [Nome do servidor]
    - Estudantes: [Nomes]
    - Colaborador externo: [se houver]

    ### 📄 Edital
    Este protótipo foi desenvolvido para concorrer no **Edital CONIF/CONTIC nº 02/2026 – Soluções e Inovações para o Desenvolvimento Sustentável com Uso de Tecnologias de Conectividade**.
    """)
