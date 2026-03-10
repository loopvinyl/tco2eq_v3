import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(layout="wide", page_title="Analisador de Emissões GEE")
st.title("🌿 Analisador de Emissões em Vermicompostagem")
st.markdown("---")

# Constantes Físico-Químicas [cite: 3, 4]
R = 8.314                     # J/(mol·K)
M_CH4 = 16.04                 # g/mol
M_N2O = 44.01                 # g/mol
M_C = 12.01                   # g/mol
M_N = 14.01                   # g/mol

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================
try:
    # Carregando o CSV referenciado no código original [cite: 5]
    dados = pd.read_csv('dados_yang_fluxo_continuo.csv', parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    st.success("✅ Arquivo de dados carregado com sucesso!")
except FileNotFoundError:
    st.error("❌ Arquivo 'dados_yang_fluxo_continuo.csv' não encontrado.")
    st.stop()

# ============================================================
# SIDEBAR - PARÂMETROS DO EXPERIMENTO [cite: 1, 2, 10]
# ============================================================
st.sidebar.header("Parâmetros Iniciais")
massa_umida = st.sidebar.number_input("Massa Inicial Úmida (kg)", value=245.28)
umidade_perc = st.sidebar.number_input("Moisture Content (%)", value=50.8)

# Cálculo da Matéria Seca (DM) - Correção sugerida
massa_seca_kg = massa_umida * (1 - (umidade_perc / 100))
st.sidebar.write(f"**Matéria Seca (DM):** {massa_seca_kg:.2f} kg")

teor_c_perc = st.sidebar.number_input("Teor de TOC (% na MS)", value=43.6)
teor_n_gkg = st.sidebar.number_input("Teor de TN (g/kg na MS)", value=14.2)

# Massas elementares iniciais 
C_inicial_kg = massa_seca_kg * (teor_c_perc / 100)
N_inicial_kg = massa_seca_kg * (teor_n_gkg / 1000)

# ============================================================
# SEÇÃO 1: CÁLCULO DE FLUXOS DIÁRIOS (YANG ET AL. 2017) [cite: 7, 8, 9]
# ============================================================
st.header("1. Fluxo de Emissão (Método de Câmara)")

col1, col2 = st.columns(2)
with col1:
    area_camara = st.number_input("Área da base da câmara (m²)", value=0.13)
    Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0)
with col2:
    volume_camara = st.number_input("Volume da câmara (m³)", value=0.03)
    area_reator = st.number_input("Área total do reator/leito (m²)", value=1.5)

Q_total_m3h = Q_sw * 60 / 1000 # Conversão L/min para m³/h

# Processamento por dia
dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    P_media = grupo['P_Pa'].mean()
    T_media = grupo['T_K'].mean()
    P_RT = P_media / (R * T_media) # mol/m³
    
    # Concentrações em mg/m³
    C_ch4_mg_m3 = grupo['CH4_ppm'].mean() * P_RT * M_CH4
    C_n2o_mg_m3 = grupo['N2O_ppm'].mean() * P_RT * M_N2O
    
    # Fluxo (E = (Y * Q) / A) [cite: 7]
    fluxo_ch4 = (C_ch4_mg_m3 * Q_total_m3h) / area_camara
    fluxo_n2o = (C_n2o_mg_m3 * Q_total_m3h) / area_camara
    
    fluxos_dia.append({
        'data': dia,
        'fluxo_CH4_mg_m2_h': fluxo_ch4,
        'fluxo_N2O_mg_m2_h': fluxo_n2o
    })

df_fluxos = pd.DataFrame(fluxos_dia)
df_fluxos['data'] = pd.to_datetime(df_fluxos['data'])

# ============================================================
# SEÇÃO 2: EMISSÕES ACUMULADAS E GWP [cite: 11, 16, 18, 19]
# ============================================================
st.header("2. Emissões Acumuladas e Impacto Ambiental")

# Cálculo de intervalos [cite: 11]
df_fluxos['intervalo_dias'] = df_fluxos['data'].diff().dt.days.shift(-1)
df_fluxos['intervalo_dias'].fillna(df_fluxos['intervalo_dias'].median(), inplace=True)

# Massa total emitida (kg) no período [cite: 16]
df_fluxos['massa_CH4_kg'] = df_fluxos['fluxo_CH4_mg_m2_h'] * 1e-6 * area_reator * df_fluxos['intervalo_dias'] * 24
df_fluxos['massa_N2O_kg'] = df_fluxos['fluxo_N2O_mg_m2_h'] * 1e-6 * area_reator * df_fluxos['intervalo_dias'] * 24

total_CH4_kg = df_fluxos['massa_CH4_kg'].sum()
total_N2O_kg = df_fluxos['massa_N2O_kg'].sum()

# Perdas elementares (Estequiometria) [cite: 12]
C_perdido_kg = total_CH4_kg * (M_C / M_CH4)
N_perdido_kg = total_N2O_kg * (2 * M_N / M_N2O)

# Percentual de perda sobre o inicial
perc_C = (C_perdido_kg / C_inicial_kg) * 100
perc_N = (N_perdido_kg / N_inicial_kg) * 100

# Cálculo de GWP (Global Warming Potential) 
GWP_CH4 = 25
GWP_N2O = 298
total_CO2_eq = (total_CH4_kg * GWP_CH4) + (total_N2O_kg * GWP_N2O)
emissao_por_t_ms = total_CO2_eq / (massa_seca_kg / 1000)

# Exibição de Métricas
m1, m2, m3 = st.columns(3)
m1.metric("Total CH₄", f"{total_CH4_kg:.4f} kg", f"{perc_C:.3f}% do C inicial")
m2.metric("Total N₂O", f"{total_N2O_kg:.4f} kg", f"{perc_N:.3f}% do N inicial")
m3.metric("Emissão Total", f"{total_CO2_eq:.2f} kg CO₂-eq")

st.info(f"💡 **Intensidade de Emissão:** {emissao_por_t_ms:.2f} kg CO₂-eq / t MS")
st.caption("Referência Yang et al. (2017): 8.1 kg CO₂-eq / t MS")

# Visualização Gráfica
st.subheader("Evolução dos Fluxos Diários")
st.line_chart(df_fluxos.set_index('data')[['fluxo_CH4_mg_m2_h', 'fluxo_N2O_mg_m2_h']])

st.markdown("---")
st.caption("Script desenvolvido com base nos parâmetros de Yang et al. (2017).")
