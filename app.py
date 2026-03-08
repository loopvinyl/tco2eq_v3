import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px

# Configuração da página para Dashboard
st.set_page_config(page_title="Vermi-IoT Sentinel", layout="wide")

# --- CABEÇALHO ALINHADO AO EDITAL CONIF/CONTIC 02/2026 [cite: 5, 6] ---
st.title("🌱 Vermi-IoT Sentinel")
st.subheader("Inovação em Monitoramento de GEE via Conectividade IoT")
st.markdown("""
**ODS:** 12 e 13 | **Maturidade:** TRL 4 | **Foco:** Desenvolvimento Sustentável[cite: 9, 51].
""")

# --- CONFIGURAÇÕES TÉCNICAS (Câmara e Pilha) ---
with st.sidebar:
    st.header("⚙️ Parâmetros do Sistema")
    area_chamber = st.number_input("Área da câmara (m²)", value=0.13)
    flow_l_min = st.number_input("Vazão de arraste (L/min)", value=5.0)
    pile_area = st.number_input("Área total da pilha (m²)", value=1.5)
    Q = flow_l_min / 1000  # m³/min
    
    st.divider()
    st.write("**Parâmetros da Pilha (Yang et al. 2017)**")
    initial_mass = st.number_input("Massa inicial (kg)", value=1500.0)
    moisture = st.number_input("Umidade (%)", value=50.8)
    toc = st.number_input("Teor C total (%)", value=43.6)
    tn = st.number_input("Teor N total (g/kg)", value=14.2)

# --- FUNÇÃO DE CONECTIVIDADE (RECEPÇÃO REMOTA) [cite: 46] ---
def fetch_remote_data():
    """Simula a recepção de dados de sensores em diversos pontos da composteira"""
    nodes = ["Nódulo-Norte", "Nódulo-Sul", "Nódulo-Central"]
    schedule = [0, 3, 7, 14, 21, 30, 45, 50]
    data_list = []
    
    for node in nodes:
        # Gerando dados baseados na curva do artigo para cada nódulo
        ch4_base = [150, 100, 80, 50, 30, 20, 10, 5]
        n2o_base = [2, 4, 6, 5, 3, 2, 1, 0.5]
        
        for i, day in enumerate(schedule):
            data_list.append({
                "day": day,
                "node_id": node,
                "CH4": ch4_base[i] + np.random.normal(0, 5), # Simula ruído do sensor
                "N2O": n2o_base[i] + np.random.normal(0, 0.2),
                "timestamp": datetime.now() - timedelta(days=(50-day))
            })
    return pd.DataFrame(data_list)

# --- LÓGICA DE PROCESSAMENTO ---
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()

if st.button("📡 Sincronizar Dados de Equipamentos Remotos"):
    st.session_state.data = fetch_remote_data()
    st.success("Dados centralizados com sucesso de 3 pontos remotos!")

df = st.session_state.data.copy()

if not df.empty:
    # 1. Cálculos de Fluxo (mg/m²·h)
    df["Flux_CH4_h"] = (df["CH4"] * Q * 60) / area_chamber
    df["Flux_N2O_h"] = (df["N2O"] * Q * 60) / area_chamber
    
    # 2. Integração por Nódulo
    results = []
    for node in df["node_id"].unique():
        node_df = df[df["node_id"] == node].sort_values("day")
        cum_ch4 = np.trapezoid(node_df["Flux_CH4_h"] * 24, node_df["day"])
        cum_n2o = np.trapezoid(node_df["Flux_N2O_h"] * 24, node_df["day"])
        results.append({"node_id": node, "cum_ch4_mg_m2": cum_ch4, "cum_n2o_mg_m2": cum_n2o})
    
    res_df = pd.DataFrame(results)
    
    # 3. Métricas Consolidadas (Balanço de Massa)
    dry_matter = initial_mass * (1 - moisture/100)
    initial_C_kg = dry_matter * (toc / 100)
    
    avg_ch4_mg_m2 = res_df["cum_ch4_mg_m2"].mean()
    total_ch4_kg = (avg_ch4_mg_m2 * pile_area) / 1e6
    ch4_c_percent = ((total_ch4_kg * 12/16) / initial_C_kg) * 100

    # --- DASHBOARD VISUAL ---
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Perda CH₄-C", f"{ch4_c_percent:.3f}%", help="Alvo Yang et al: 0.13%")
    c2.metric("Total GEE Estimado", f"{total_ch4_kg * 25:.2f} kg CO₂eq")
    c3.metric("Status Conectividade", "3 Nódulos Ativos", "TRL 4")

    # Gráfico de Monitoramento Espacial
    fig = px.line(df, x="day", y="Flux_CH4_h", color="node_id", 
                  title="Monitoramento de Fluxo de Metano por Ponto Remoto",
                  labels={"Flux_CH4_h": "Fluxo (mg/m²·h)", "day": "Dia"})
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("📋 Detalhes da Tabela de Comparação (Artigo vs IoT)"):
        st.write("Comparação com Tabela 3 do artigo: CH₄-C: 0.13% | N₂O-N: 0.92%")
        st.dataframe(df)
else:
    st.info("Aguardando conexão com os sensores remotos... Clique no botão acima.")
