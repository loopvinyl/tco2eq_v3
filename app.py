import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import socket
import os

# Configuração da página
st.set_page_config(page_title="Vermi-IoT Sentinel", layout="wide")

# =============================================================================
# Cabeçalho
# =============================================================================
st.title("🌱 Vermi-IoT Sentinel")
st.markdown("### Monitoramento Remoto Exclusivo via Sensor Virtual (TCP/IP)")
st.caption("Alinhado ao Edital CONIF/CONTIC nº 02/2026 | ODS 12 e 13")

# =============================================================================
# Parâmetros e Configurações (Barra Lateral)
# =============================================================================
with st.sidebar:
    st.header("🌐 Conexão do Sensor")
    # Agora o host e porta são fixos ou editáveis aqui
    tcp_host = st.text_input("Endereço IP/Host", value="localhost")
    tcp_port = st.number_input("Porta TCP", value=5000)
    
    st.divider()
    st.header("⚙️ Parâmetros da Câmara")
    area_chamber = st.number_input("Área da câmara (m²)", value=0.13)
    flow_l_min = st.number_input("Vazão (L/min)", value=5.0)
    Q = flow_l_min / 1000  # Conversão para m³/min

    st.divider()
    st.subheader("📦 Dados da Pilha")
    pile_area = st.number_input("Área total da pilha (m²)", value=1.5)
    initial_mass = st.number_input("Massa inicial (kg)", value=1500.0)
    moisture = st.number_input("Umidade (%)", value=50.8)
    toc = st.number_input("C Orgânico Total (%)", value=43.6)
    tn = st.number_input("N Total (g/kg)", value=14.2)

# =============================================================================
# Inicialização de Estado
# =============================================================================
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = pd.DataFrame(columns=["timestamp", "CH4_mg_m3", "N2O_mg_m3", "source"])

# =============================================================================
# Funções de Comunicação e Cálculo
# =============================================================================
def read_tcp_sensor(host, port):
    """Tenta ler os dados brutos do sensor_virtual.py via TCP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((host, port))
            data = s.recv(1024).decode().strip()
            if data:
                # Espera formato "CH4,N2O"
                ch4_val, n2o_val = data.split(',')
                return float(ch4_val), float(n2o_val)
    except Exception as e:
        st.sidebar.error(f"Erro de conexão: {e}")
    return None, None

def calculate_fluxes(row):
    """Calcula fluxos baseados na concentração lida."""
    ch4 = row["CH4_mg_m3"]
    n2o = row["N2O_mg_m3"]
    # Fluxo (mg/m².h) = (Conc * Vazão * 60 min) / Área da Câmara
    f_ch4 = (ch4 * Q * 60) / area_chamber
    f_n2o = (n2o * Q * 60) / area_chamber
    return pd.Series([f_ch4, f_n2o])

# =============================================================================
# Interface Principal (Abas)
# =============================================================================
tab1, tab2, tab3 = st.tabs(["📡 Monitoramento Local", "📊 Análise Acumulada", "📋 Info"])

with tab1:
    col_btn, col_status = st.columns([1, 3])
    
    with col_btn:
        if st.button("🔄 Capturar Dado do Sensor"):
            ch4, n2o = read_tcp_sensor(tcp_host, tcp_port)
            if ch4 is not None:
                new_data = pd.DataFrame({
                    "timestamp": [datetime.now()],
                    "CH4_mg_m3": [ch4],
                    "N2O_mg_m3": [n2o],
                    "source": ["TCP/IP Virtual"]
                })
                st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_data], ignore_index=True)
                st.success("Leitura realizada!")
            else:
                st.error("Sensor Offline. Inicie o 'sensor_virtual.py'.")

    # Métricas em Tempo Real
    if not st.session_state.sensor_data.empty:
        last = st.session_state.sensor_data.iloc[-1]
        m1, m2, m3 = st.columns(3)
        m1.metric("CH₄ Atual", f"{last['CH4_mg_m3']:.2f} mg/m³")
        m2.metric("N₂O Atual", f"{last['N2O_mg_m3']:.2f} mg/m³")
        m3.metric("Última Sincronização", last['timestamp'].strftime('%H:%M:%S'))

        # Gráfico de Tendência
        df_plot = st.session_state.sensor_data.copy()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_plot["timestamp"], y=df_plot["CH4_mg_m3"], name="CH₄"))
        fig.add_trace(go.Scatter(x=df_plot["timestamp"], y=df_plot["N2O_mg_m3"], name="N₂O"))
        fig.update_layout(title="Concentrações Recebidas via TCP/IP", yaxis_title="mg/m³")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aguardando primeira leitura do sensor virtual...")

with tab2:
    if not st.session_state.sensor_data.empty:
        df = st.session_state.sensor_data.copy()
        # Aplicar cálculos de fluxo
        df[["Flux_CH4", "Flux_N2O"]] = df.apply(calculate_fluxes, axis=1)
        
        st.subheader("Cálculo de Emissões (Base: Yang et al. 2017)")
        st.dataframe(df.tail(10))
        
        # Botão para baixar CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Baixar Histórico CSV", data=csv, file_name="sensores_vermi.csv")
    else:
        st.warning("Sem dados para análise histórica.")

with tab3:
    st.markdown("""
    ### Instruções de Uso:
    1. Certifique-se que o script `sensor_virtual.py` está rodando em seu terminal.
    2. O endereço padrão é `localhost` na porta `5000`.
    3. Este dashboard lê apenas os dados transmitidos via rede, simulando um dispositivo IoT real no campo.
    """)
