import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INICIAIS 
# ============================================================
st.set_page_config(layout="wide", page_title="Analisador de Emissões")
st.title("Analisador de Emissões em Vermicompostagem")
st.markdown("---")

# Constantes Físico-Químicas [cite: 3, 4]
R = 8.314                     # J/(mol·K)
VOLUME_CAMARA_PADRAO = 0.03    # m³ (30 L)
M_CH4 = 16.04                  # g/mol
M_N2O = 44.01                  # g/mol
M_C = 12.01                    # g/mol
M_N = 14.01                    # g/mol

# ============================================================
# CARREGAMENTO DOS DADOS (FIXO) [cite: 5]
# ============================================================
try:
    dados = pd.read_csv('dados_yang_fluxo_continuo.csv', parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    st.success("Arquivo 'dados_yang_fluxo_continuo.csv' carregado!")
except FileNotFoundError:
    st.error("Arquivo 'dados_yang_fluxo_continuo.csv' não encontrado.")
    st.stop()

st.subheader("Visualização dos dados")
st.write(dados.head())

# ============================================================
# PARÂMETROS DA CÂMARA E MATERIAL [cite: 7, 10]
# ============================================================
st.sidebar.header("Configurações do Experimento")
area_camara = st.sidebar.number_input("Área da base da câmara (m²)", value=0.13, step=0.01)
volume_camara = st.sidebar.number_input("Volume da câmara (m³)", value=VOLUME_CAMARA_PADRAO, step=0.01)
area_reator = st.sidebar.number_input("Área do Reator (m²)", value=1.5)

st.sidebar.markdown("---")
massa_inicial_kg = st.sidebar.number_input("Massa Inicial Úmida (kg)", value=245.28) [cite: 1]
moisture_perc = st.sidebar.number_input("Umidade (%)", value=50.8) [cite: 1]

# CÁLCULO DA MATÉRIA SECA (Ajuste para precisão)
massa_seca_kg = massa_inicial_kg * (1 - (moisture_perc / 100)) [cite: 1]
st.sidebar.info(f"Matéria Seca (DM): {massa_seca_kg:.2f} kg")

teor_c_perc = st.sidebar.number_input("Teor de Carbono (% na MS)", value=43.6) [cite: 1]
teor_n_gkg = st.sidebar.number_input("Teor de Nitrogênio (g/kg na MS)", value=14.2) [cite: 1]

# ============================================================
# 1. MASSA DE GÁS NA CÂMARA (INSTANTÂNEA) 
# ============================================================
st.header("1. Massa de gás na câmara (Instantânea)")
dados['CH4_mol_frac'] = dados['CH4_ppm'] * 1e-6
dados['N2O_mol_frac'] = dados['N2O_ppm'] * 1e-6

P_media = dados['P_Pa'].mean()
T_media = dados['T_K'].mean()
n_total_camara = (P_media * volume_camara) / (R * T_media)

dados['massa_CH4_mg'] = dados['CH4_mol_frac'] * n_total_camara * M_CH4 * 1000
dados['massa_N2O_mg'] = dados['N2O_mol_frac'] * n_total_camara * M_N2O * 1000

st.line_chart(dados[['massa_CH4_mg', 'massa_N2O_mg']])
st.write(f"Massa média CH₄: {dados['massa_CH4_mg'].mean():.4f} mg | N₂O: {dados['massa_N2O_mg'].mean():.4f} mg")

# ============================================================
# 2. FLUXO DE EMISSÃO - MÉTODO YANG ET AL. [cite: 7, 8, 9]
# ============================================================
st.header("2. Fluxo de emissão (Yang et al. 2017)")
Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0)
Q_total_m3h = Q_sw * 60 / 1000

dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    P_m = grupo['P_Pa'].mean()
    T_m = grupo['T_K'].mean()
    P_RT = P_m / (R * T_m)
    
    C_ch4_mg_m3 = grupo['CH4_ppm'].mean() * P_RT * M_CH4 * 1000
    C_n2o_mg_m3 = grupo['N2O_ppm'].mean() * P_RT * M_N2O * 1000
    
    fluxo_ch4 = (C_ch4_mg_m3 * Q_total_m3h) / area_camara
    fluxo_n2o = (C_n2o_mg_m3 * Q_total_m3h) / area_camara
    
    fluxos_dia.append({
        'data': dia,
        'fluxo_CH4': fluxo_ch4,
        'fluxo_N2O': fluxo_n2o
    })

df_fluxos = pd.DataFrame(fluxos_dia)
df_fluxos['data'] = pd.to_datetime(df_fluxos['data'])
st.dataframe(df_fluxos)

# ============================================================
# 3. PERDA ACUMULADA E GEE (INOVAÇÃO COM PRECISÃO) [cite: 10, 11, 16, 18]
# ============================================================
st.header("3. Balanço de Massa e Impacto Global (GEE)")

if not df_fluxos.empty:
    df_temp = df_fluxos.copy()
    df_temp['intervalo'] = df_temp['data'].diff().dt.days.shift(-1)
    df_temp['intervalo'].fillna(df_temp['intervalo'].median(), inplace=True)
    
    # Emissões em kg [cite: 11]
    df_temp['m_CH4_kg'] = df_temp['fluxo'] * 1e-6 * area_reator * df_temp['intervalo'] * 24 # ajuste fluxos
    # (Note: Usei lógica simplificada para o exemplo, aplique para CH4 e N2O separadamente)
    
    total_CH4_kg = (df_temp['fluxo_CH4'] * 1e-6 * area_reator * df_temp['intervalo'] * 24).sum()
    total_N2O_kg = (df_temp['fluxo_N2O'] * 1e-6 * area_reator * df_temp['intervalo'] * 24).sum()
    
    # Estequiometria [cite: 12]
    C_perdido = total_CH4_kg * (M_C / M_CH4)
    N_perdido = total_N2O_kg * (2 * M_N / M_N2O)
    
    # Bases iniciais baseadas na DM 
    C_inicial_total = massa_seca_kg * (teor_c_perc / 100)
    N_inicial_total = massa_seca_kg * (teor_n_gkg / 1000)
    
    # GWP 
    co2_ch4 = total_CH4_kg * 25
    co2_n2o = total_N2O_kg * 298
    total_gee = co2_ch4 + co2_n2o
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Perda C-CH₄", f"{C_perdido:.4f} kg", f"{(C_perdido/C_inicial_total)*100:.3f}%")
    col2.metric("Perda N-N₂O", f"{N_perdido:.4f} kg", f"{(N_perdido/N_inicial_total)*100:.3f}%")
    col3.metric("Total GEE", f"{total_gee:.2f} kg CO₂-eq", f"{total_gee/(massa_seca_kg/1000):.2f} /t MS")

st.markdown("---")
st.caption("App consolidado: Monitoramento em tempo real + Cálculos de Yang et al. (2017)")
