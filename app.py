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

# Constantes Físico-Químicas (Baseadas no Artigo)
R = 8.314                     # J/(mol·K) [cite: 3]
M_CH4 = 16.04                 # g/mol [cite: 3]
M_N2O = 44.01                 # g/mol [cite: 4]
M_C = 12.01                   # g/mol [cite: 4]
M_N = 14.01                   # g/mol [cite: 4]

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================
try:
    # Tenta carregar o arquivo CSV necessário
    dados = pd.read_csv('dados_yang_fluxo_continuo.csv', parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    st.success("✅ Arquivo de dados carregado com sucesso!")
except FileNotFoundError:
    st.error("❌ Arquivo 'dados_yang_fluxo_continuo.csv' não encontrado.")
    st.stop()

# ============================================================
# SIDEBAR - PARÂMETROS DO MATERIAL (Ajustados conforme Fonte 2)
# ============================================================
st.sidebar.header("Parâmetros do Material")
massa_umida = st.sidebar.number_input("Massa Inicial Úmida (kg)", value=245.28)
umidade_perc = st.sidebar.number_input("Teor de Umidade (%)", value=50.8)

# Cálculo da Matéria Seca (Dry Matter - DM) para evitar erros de base
massa_seca_kg = massa_umida * (1 - (umidade_perc / 100))
st.sidebar.info(f"Matéria Seca (DM): {massa_seca_kg:.2f} kg")

teor_c_perc = st.sidebar.number_input("Teor de Carbono (% na MS)", value=43.6)
teor_n_gkg = st.sidebar.number_input("Teor de Nitrogênio (g/kg na MS)", value=14.2)

# Massas elementares iniciais (Base de comparação para perdas)
C_inicial_kg = massa_seca_kg * (teor_c_perc / 100)
N_inicial_kg = massa_seca_kg * (teor_n_gkg / 1000)

# ============================================================
# 1. CÁLCULO DE FLUXOS (MÉTODO YANG ET AL. 2017)
# ============================================================
st.header("1. Fluxo de Emissão Diário")

col1, col2 = st.columns(2)
with col1:
    area_camara = st.number_input("Área da base da câmara (m²)", value=0.13)
    Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0)
with col2:
    volume_camara = st.number_input("Volume da câmara (m³)", value=0.03)
    area_reator = st.number_input("Área total do reator (m²)", value=1.5)

Q_total_m3h = (Q_sw * 60) / 1000 # L/min -> m³/h [cite: 8]

# Agrupamento por dia para cálculo de fluxos
dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    P_media = grupo['P_Pa'].mean()
    T_media = grupo['T_K'].mean()
    P_RT = P_media / (R * T_media) # mol/m³ [cite: 8]
    
    # Concentrações médias diárias em mg/m³
    C_ch4_mg_m3 = grupo['CH4_ppm'].mean() * P_RT * M_CH4
    C_n2o_mg_m3 = grupo['N2O_ppm'].mean() * P_RT * M_N2O
    
    # Fluxo (E = (Y * Q) / A) conforme Yang et al.
    fluxo_ch4 = (C_ch4_mg_m3 * Q_total_m3h) / area_camara [cite: 9]
    fluxo_n2o = (C_n2o_mg_m3 * Q_total_m3h) / area_camara [cite: 9]
    
    fluxos_dia.append({
        'data': dia,
        'fluxo_CH4': fluxo_ch4,
        'fluxo_N2O': fluxo_n2o
    })

df_fluxos = pd.DataFrame(fluxos_dia)
df_fluxos['data'] = pd.to_datetime(df_fluxos['data'])

# ============================================================
# 2. EMISSÕES ACUMULADAS E GWP (CORREÇÃO DE ESTEQUIOMETRIA)
# ============================================================
st.header("2. Emissões Acumuladas e GEE")

if not df_fluxos.empty:
    # Cálculo dos intervalos entre medições
    df_fluxos['intervalo'] = df_fluxos['data'].diff().dt.days.shift(-1)
    df_fluxos['intervalo'].fillna(df_fluxos['intervalo'].median(), inplace=True)
    
    # Massa total emitida (kg)
    total_CH4_kg = (df_fluxos['fluxo_CH4'] * 1e-6 * area_reator * df_fluxos['intervalo'] * 24).sum()
    total_N2O_kg = (df_fluxos['fluxo_N2O'] * 1e-6 * area_reator * df_fluxos['intervalo'] * 24).sum()
    
    # Perdas elementares (C e N)
    C_perdido_kg = total_CH4_kg * (M_C / M_CH4) [cite: 12]
    N_perdido_kg = total_N2O_kg * (2 * M_N / M_N2O) [cite: 12]
    
    # Cálculo de GWP (Global Warming Potential)
    GWP_CH4 = 25 [cite: 18]
    GWP_N2O = 298 [cite: 18]
    total_CO2_eq = (total_CH4_kg * GWP_CH4) + (total_N2O_kg * GWP_N2O)
    
    # Indicador de Intensidade
    emissao_por_t_ms = total_CO2_eq / (massa_seca_kg / 1000)

    # Exibição de Resultados
    c1, c2, c3 = st.columns(3)
    c1.metric("Perda de C-CH₄", f"{C_perdido_kg:.4f} kg", f"{(C_perdido_kg/C_inicial_kg)*100:.3f}% do C")
    c2.metric("Perda de N-N₂O", f"{N_perdido_kg:.4f} kg", f"{(N_perdido_kg/N_inicial_kg)*100:.3f}% do N")
    c3.metric("Impacto Total GEE", f"{total_CO2_eq:.2f} kg CO₂-eq")

    st.info(f"📊 **Intensidade de Emissão:** {emissao_por_t_ms:.2f} kg CO₂-eq / t MS")
    st.caption("Referência Yang et al. (2017): ~8.1 kg CO₂-eq / t MS [cite: 19]")

    # Gráfico de Fluxos
    st.subheader("Evolução dos Fluxos Diários (mg m⁻² h⁻¹)")
    st.line_chart(df_fluxos.set_index('data')[['fluxo_CH4', 'fluxo_N2O']])
