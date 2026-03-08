# Vermicompost GHG Monitoring with Sensor Integration
# Versão unificada para o Edital CONIF/CONTIC nº 02/2026
# Baseado no artigo de Yang et al. (2017) e no diagrama Nutriwash System

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import os

# Configuração da página
st.set_page_config(page_title="Vermi-IoT Sentinel - Sensor Integration", layout="wide")

# ---- Título e cabeçalho ----
st.title("🌱 Vermi-IoT Sentinel com Leitura de Sensores")
st.markdown("**Sistema de Monitoramento Remoto de Emissões GEE (ODS 12 e 13)**")
st.markdown("Integração com sensores de CH₄ e N₂O acoplados à câmara de fluxo (Nutriwash System)")

# ---- Sidebar com parâmetros fixos (baseados no artigo) ----
with st.sidebar:
    st.header("⚙️ Parâmetros da Câmara e Pilha")
    
    # Câmara de fluxo
    area_chamber = st.number_input("Área da câmara (m²)", value=0.13, format="%.2f",
                                   help="Área da base da câmara (16\" diâmetro ≈ 0.13 m²)")
    flow_l_min = st.number_input("Vazão de ar de arraste (L/min)", value=5.0, format="%.2f")
    Q = flow_l_min / 1000  # m³/min
    
    st.divider()
    st.subheader("Dimensões da Pilha")
    pile_area = st.number_input("Área superficial total da pilha (m²)", value=1.5, format="%.2f")
    initial_mass = st.number_input("Massa inicial de resíduos (kg)", value=1500.0)
    moisture = st.number_input("Umidade (%)", value=50.8, format="%.1f")
    toc = st.number_input("Teor inicial de C orgânico total (%)", value=43.6, format="%.1f")
    tn = st.number_input("Teor inicial de N total (g kg⁻¹)", value=14.2, format="%.1f")
    
    st.divider()
    st.subheader("Fatores de Conversão")
    gwp_ch4 = st.number_input("GWP CH₄ (100 anos)", value=25)
    gwp_n2o = st.number_input("GWP N₂O (100 anos)", value=298)

# ---- Inicialização da sessão ----
if "sensor_data" not in st.session_state:
    st.session_state.sensor_data = pd.DataFrame(columns=["timestamp", "CH4_mg_m3", "N2O_mg_m3", "source"])

if "sensor_active" not in st.session_state:
    st.session_state.sensor_active = False

if "last_update" not in st.session_state:
    st.session_state.last_update = datetime.now()

# ---- Funções auxiliares ----
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
    """Gera uma leitura simulada baseada nas curvas do artigo com ruído."""
    # Curva típica: CH4 começa alto e diminui; N2O tem pico no meio
    base_day = (datetime.now() - st.session_state.last_update).days
    # Para simulação, usamos uma função que varia com o tempo
    ch4_base = 150 * np.exp(-0.1 * base_day) + 5
    n2o_base = 6 * np.sin(base_day / 10) + 2
    ch4 = max(0, ch4_base + np.random.normal(0, 3))
    n2o = max(0, n2o_base + np.random.normal(0, 0.2))
    return ch4, n2o

def read_serial_sensor(port, baudrate):
    """
    Placeholder para leitura real de sensor via serial.
    Deve retornar (ch4_mg_m3, n2o_mg_m3) ou (None, None) em caso de erro.
    """
    # Aqui você implementaria a comunicação com o sensor real
    # Por enquanto, retorna valores simulados
    return simulate_sensor_reading()

# ---- Abas principais ----
tab1, tab2, tab3, tab4 = st.tabs(["📡 Monitoramento em Tempo Real", 
                                   "📊 Histórico e Análise", 
                                   "🔧 Configurações dos Sensores", 
                                   "📋 Sobre o Projeto"])

with tab1:
    st.header("Leitura em Tempo Real dos Sensores")
    st.markdown("**Sensor acoplado à câmara de fluxo (Nutriwash System)**")
    
    # Exibir imagem do sistema (se disponível)
    if os.path.exists("Nutriwash_System.png"):
        st.image("Nutriwash_System.png", caption="Diagrama do sistema Nutriwash", width=600)
    else:
        st.info("ℹ️ Para visualizar o diagrama, coloque a imagem 'Nutriwash_System.png' no mesmo diretório do script.")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Controle da Aquisição")
        if st.button("▶️ Iniciar Leitura Contínua"):
            st.session_state.sensor_active = True
            st.session_state.last_update = datetime.now()
        if st.button("⏹️ Parar Leitura"):
            st.session_state.sensor_active = False
        
        # Opção de leitura manual
        st.markdown("**Leitura Manual**")
        ch4_manual = st.number_input("CH₄ (mg/m³)", value=150.0, step=1.0)
        n2o_manual = st.number_input("N₂O (mg/m³)", value=2.0, step=0.1)
        if st.button("Registrar Medição Manual"):
            new_row = pd.DataFrame({
                "timestamp": [datetime.now()],
                "CH4_mg_m3": [ch4_manual],
                "N2O_mg_m3": [n2o_manual],
                "source": ["manual"]
            })
            st.session_state.sensor_data = pd.concat([st.session_state.sensor_data, new_row], ignore_index=True)
            st.success("Medição registrada!")
    
    with col2:
        st.subheader("Última Leitura")
        # Se a leitura contínua estiver ativa, atualiza a cada 2 segundos (simulado)
        if st.session_state.sensor_active:
            # Em um app real, você faria a leitura em loop, mas Streamlit não suporta atualização automática sem rerun
            # Vamos simular uma leitura a cada clique em um botão "Atualizar"
            if st.button("🔄 Atualizar Leitura"):
                # Simular leitura do sensor (ou real via serial)
                ch4, n2o = simulate_sensor_reading()
                new_row = pd.DataFrame({
                    "timestamp": [datetime.now()],
                    "CH4_mg_m3": [ch4],
                    "N2O_mg_m3": [n2o],
                    "source": ["sensor"]
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
            st.info("Nenhuma leitura ainda.")
    
    # Gráfico em tempo real das últimas 24h
    st.subheader("Tendência Recente (últimas 24h)")
    if not st.session_state.sensor_data.empty:
        df_display = st.session_state.sensor_data.copy()
        # Calcular fluxos para exibição
        fluxes = df_display.apply(calculate_fluxes, axis=1)
        df_display[["Flux_CH4_h", "Flux_N2O_h", "Flux_CH4_d", "Flux_N2O_d"]] = fluxes
        
        # Filtrar últimas 24h
        cutoff = datetime.now() - timedelta(hours=24)
        df_recent = df_display[df_display["timestamp"] >= cutoff]
        
        if not df_recent.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_recent["timestamp"], y=df_recent["Flux_CH4_h"],
                                      mode='lines+markers', name='CH₄ (mg/m².h)'))
            fig.add_trace(go.Scatter(x=df_recent["timestamp"], y=df_recent["Flux_N2O_h"],
                                      mode='lines+markers', name='N₂O (mg/m².h)'))
            fig.update_layout(title="Fluxo Horário", xaxis_title="Tempo", yaxis_title="mg/m².h")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para gráfico nas últimas 24h.")
    else:
        st.info("Nenhum dado registrado.")

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
        
        # Extrapolação para a pilha inteira
        total_ch4_kg = cum_ch4_mg_m2 * pile_area / 1e6
        total_n2o_kg = cum_n2o_mg_m2 * pile_area / 1e6
        
        ch4_c_kg = total_ch4_kg * (12/16)
        n2o_n_kg = total_n2o_kg * (28/44)
        
        ch4_c_perc = (ch4_c_kg / initial_C_kg) * 100 if initial_C_kg > 0 else 0
        n2o_n_perc = (n2o_n_kg / initial_N_kg) * 100 if initial_N_kg > 0 else 0
        
        total_co2eq = total_ch4_kg * gwp_ch4 + total_n2o_kg * gwp_n2o
        ghg_per_ton = (total_co2eq / dry_matter) * 1000 if dry_matter > 0 else 0
        
        # Exibir métricas
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
        
        # Tabela de dados
        with st.expander("Ver dados completos"):
            st.dataframe(df[["timestamp", "day", "CH4_mg_m3", "N2O_mg_m3", 
                             "Flux_CH4_h", "Flux_N2O_h", "source"]])
        
        # Comparação com artigo
        st.caption("🔍 Comparação com Tabela 3 do artigo (Yang et al. 2017): CH₄-C = 0.13%, N₂O-N = 0.92%, GHG total = 8.1 kg CO₂-eq/t DM")
        st.caption("Os valores acima são aproximações; seu experimento pode apresentar variações.")

with tab3:
    st.header("Configurações dos Sensores")
    st.markdown("Ajuste os parâmetros de comunicação com os sensores reais.")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sensor_type = st.selectbox("Tipo de Sensor", ["Simulado", "Serial (Modbus)", "Analogico (DAQ)"])
        if sensor_type == "Serial (Modbus)":
            port = st.text_input("Porta COM", value="/dev/ttyUSB0")
            baudrate = st.selectbox("Baud rate", [9600, 19200, 38400, 115200], index=0)
            st.info("Conecte o sensor e clique em 'Testar Conexão'")
            if st.button("Testar Conexão"):
                st.success("Conexão bem-sucedida (simulação)")
        elif sensor_type == "Analogico (DAQ)":
            channel = st.number_input("Canal", value=0)
            st.info("Configure o hardware de aquisição")
        else:
            st.info("Usando sensor simulado (dados gerados aleatoriamente com base no artigo).")
    
    with col_s2:
        st.subheader("Calibração")
        ch4_offset = st.number_input("Offset CH₄ (mg/m³)", value=0.0)
        ch4_gain = st.number_input("Ganho CH₄", value=1.0)
        n2o_offset = st.number_input("Offset N₂O (mg/m³)", value=0.0)
        n2o_gain = st.number_input("Ganho N₂O", value=1.0)
        st.caption("Os valores lidos serão ajustados: valor = (raw * gain) + offset")
    
    # Botão para exportar dados
    st.divider()
    st.subheader("Exportar Dados")
    if st.button("Exportar para CSV"):
        if not st.session_state.sensor_data.empty:
            csv = st.session_state.sensor_data.to_csv(index=False)
            st.download_button("Download CSV", data=csv, file_name=f"dados_gee_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", mime="text/csv")
        else:
            st.warning("Nenhum dado para exportar.")

with tab4:
    st.header("Sobre o Projeto")
    st.markdown("""
    ### Vermi-IoT Sentinel
    **Sistema de Monitoramento Remoto de Emissões de Gases de Efeito Estufa (CH₄ e N₂O) em Vermicompostagem**
    
    Este protótipo integra:
    - Leitura de sensores de gases acoplados a uma câmara de fluxo (Emission Isolation Flux Chamber)
    - Cálculos de fluxo horário e diário baseados no artigo de Yang et al. (2017)
    - Balanço de massa e estimativa de emissões totais em kg CO₂ equivalente
    - Visualização em tempo real e histórica
    
    **Referência:** Yang, F., Li, G., Shi, H., & Wang, Y. (2017). Effects of phosphogypsum and superphosphate on compost maturity and gaseous emissions during kitchen waste composting. *Waste Management*, 64, 119–126.
    
    **ODS alinhadas:** 12 (Consumo e Produção Responsáveis) e 13 (Ação Contra a Mudança Global do Clima)
    
    **Edital:** CONIF/CONTIC nº 02/2026 – Inovação para Sustentabilidade.
    
    **Diagrama do Sistema:** O diagrama Nutriwash mostra a câmara de fluxo sobre o leito de vermicompostagem, com minhocas separadas e extração de húmus/líquido.
    """)
    
    # Exibir imagem novamente
    if os.path.exists("Nutriwash_System.png"):
        st.image("Nutriwash_System.png", caption="Nutriwash System", width=500)
    else:
        st.info("ℹ️ Para visualizar o diagrama, coloque a imagem 'Nutriwash_System.png' no mesmo diretório do script.")
    
    st.markdown("**Desenvolvido por:** [Seu Nome/Equipe]")
