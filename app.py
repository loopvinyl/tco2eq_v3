import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(layout="wide")
st.title("Analisador de Emissões em Vermicompostagem")
st.markdown("---")

# Constantes
R = 8.314                     # J/(mol·K)
VOLUME_CAMARA = 0.03          # m³ (valor do artigo: 30 L)
M_CH4 = 16.04                  # g/mol
M_N2O = 44.01                  # g/mol
M_C = 12.01                    # g/mol
M_N = 14.01                    # g/mol

# ============================================================
# CARREGAMENTO DOS DADOS (FIXO)
# ============================================================
st.sidebar.header("Configurações")

# Carrega diretamente o arquivo CSV (deve estar na mesma pasta)
try:
    dados = pd.read_csv('dados_yang_fluxo_continuo.csv', parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    st.sidebar.success("Arquivo 'dados_yang_fluxo_continuo.csv' carregado!")
except FileNotFoundError:
    st.error("Arquivo 'dados_yang_fluxo_continuo.csv' não encontrado. Certifique-se de que ele está na mesma pasta do app.")
    st.stop()

# Mostrar primeiras linhas
st.subheader("Visualização dos dados")
st.write(dados.head())

# ============================================================
# PARÂMETROS DA CÂMARA (EXISTENTES) - AGORA COM VALORES DO ARTIGO
# ============================================================
st.sidebar.subheader("Parâmetros da câmara")
area_camara = st.sidebar.number_input("Área da base da câmara (m²)", value=0.13, step=0.01)
volume_camara = st.sidebar.number_input("Volume da câmara (m³)", value=VOLUME_CAMARA, step=0.01)

# ============================================================
# SEÇÃO 1: CÁLCULO DE MASSA E CONCENTRAÇÃO (EXISTENTE)
# ============================================================
st.header("1. Massa de gás na câmara")
# Converter ppm para fração molar
dados['CH4_mol'] = dados['CH4_ppm'] * 1e-6
dados['N2O_mol'] = dados['N2O_ppm'] * 1e-6

# Número de mols total na câmara (ar)
# Usar P e T médios para simplificar
P_media = dados['P_Pa'].mean()
T_media = dados['T_K'].mean()
n_total = (P_media * volume_camara) / (R * T_media)   # mol

dados['massa_CH4_g'] = dados['CH4_mol'] * n_total * M_CH4
dados['massa_N2O_g'] = dados['N2O_mol'] * n_total * M_N2O

st.line_chart(dados[['massa_CH4_g', 'massa_N2O_g']])
st.write("Massa média CH4 (g):", round(dados['massa_CH4_g'].mean(), 4))
st.write("Massa média N2O (g):", round(dados['massa_N2O_g'].mean(), 4))

# ============================================================
# SEÇÃO 2: PERDA DE CARBONO E NITROGÊNIO (EXISTENTE) - VALORES DEFAULT AJUSTADOS
# ============================================================
st.header("2. Perda de C e N (base acumulada)")
# Massa seca inicial do material (kg) - default 375 kg (calibrado)
massa_inicial_kg = st.number_input("Massa inicial do material (kg)", value=375.0)
teor_carbono_percent = st.number_input("Teor de carbono inicial (% massa seca)", value=43.6)
teor_nitrogenio_percent = st.number_input("Teor de nitrogênio inicial (% massa seca)", value=1.42)

# Carbono no CH4
dados['C_perdido_g'] = dados['massa_CH4_g'] * (M_C / M_CH4)
# Nitrogênio no N2O
dados['N_perdido_g'] = dados['massa_N2O_g'] * (2 * M_N / M_N2O)

C_total_inicial_g = massa_inicial_kg * 1000 * (teor_carbono_percent / 100)
N_total_inicial_g = massa_inicial_kg * 1000 * (teor_nitrogenio_percent / 100)

dados['perc_C_perdido'] = (dados['C_perdido_g'].cumsum() / C_total_inicial_g) * 100
dados['perc_N_perdido'] = (dados['N_perdido_g'].cumsum() / N_total_inicial_g) * 100

st.line_chart(dados[['perc_C_perdido', 'perc_N_perdido']])
st.write("Perda acumulada de C (%):", round(dados['perc_C_perdido'].iloc[-1], 2))
st.write("Perda acumulada de N (%):", round(dados['perc_N_perdido'].iloc[-1], 2))

# ============================================================
# SEÇÃO 4: FLUXO PELO MÉTODO CIENTÍFICO (dC/dt) - EXISTENTE
# ============================================================
st.header("4. Fluxo de emissão - método da taxa de concentração (dC/dt)")

# diferença de tempo em horas
dados['delta_t_h'] = dados.index.to_series().diff().dt.total_seconds() / 3600

# taxa de mudança da concentração
dados['dCH4_dt'] = dados['CH4_ppm'].diff() / dados['delta_t_h']
dados['dN2O_dt'] = dados['N2O_ppm'].diff() / dados['delta_t_h']

# cálculo do fluxo (mg m⁻² h⁻¹)
dados['flux_CH4_scientific'] = (
    dados['dCH4_dt'] *
    (dados['P_Pa'] * volume_camara) /
    (R * dados['T_K']) *
    M_CH4 /
    area_camara
) * 1000

dados['flux_N2O_scientific'] = (
    dados['dN2O_dt'] *
    (dados['P_Pa'] * volume_camara) /
    (R * dados['T_K']) *
    M_N2O /
    area_camara
) * 1000

st.line_chart(dados[['flux_CH4_scientific', 'flux_N2O_scientific']])
st.write("Fluxo médio CH₄ (mg m⁻² h⁻¹):", round(dados['flux_CH4_scientific'].mean(), 4))
st.write("Fluxo médio N₂O (mg m⁻² h⁻¹):", round(dados['flux_N2O_scientific'].mean(), 4))

# ============================================================
# SEÇÃO 5: MÉTODO DE CÂMARA DE FLUXO CONTÍNUO (YANG ET AL.) - NOVO
# ============================================================
st.header("5. Fluxo de emissão - método de câmara de fluxo contínuo (Yang et al. 2017)")

st.markdown("""
Este método utiliza a equação:

\[
E = \frac{Y \cdot (Q_{sw} + Q_{ad})}{A}
\]

onde:
- \(E\) = fluxo de emissão (mg m⁻² h⁻¹)
- \(Y\) = concentração do gás na saída da câmara (mg m⁻³)
- \(Q_{sw}\) = vazão de ar de arraste (m³ h⁻¹)
- \(Q_{ad}\) = vazão adicional determinada por traçador (m³ h⁻¹)
- \(A\) = área da base da câmara (m²)
""")

col1, col2, col3 = st.columns(3)
with col1:
    Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0, step=0.1)
    area_camara_yang = st.number_input("Área da câmara (m²)", value=0.13, step=0.01, key="area_yang")
with col2:
    usar_Q_ad = st.checkbox("Usar vazão adicional (Q_ad)")
    if usar_Q_ad:
        Q_ad = st.number_input("Q_ad (L/min)", value=0.0, step=0.1)
    else:
        Q_ad = 0.0
with col3:
    st.info("Concentrações em ppm convertidas usando P e T médios.")

# Converter vazão para m³/h
Q_total_m3h = (Q_sw + Q_ad) * 60 / 1000

# Calcular fluxo diário (agrupar por dia)
dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    # Média das concentrações no dia
    C_ch4_ppm = grupo['CH4_ppm'].mean()
    C_n2o_ppm = grupo['N2O_ppm'].mean()
    
    # Média de P e T no dia
    P_media_dia = grupo['P_Pa'].mean()
    T_media_dia = grupo['T_K'].mean()
    
    # Converter ppm para mg/m³
    # mg/m³ = ppm * (P/RT) * M * 1000
    P_RT = P_media_dia / (R * T_media_dia)   # mol/m³
    C_ch4_mg_m3 = C_ch4_ppm * P_RT * M_CH4 * 1000
    C_n2o_mg_m3 = C_n2o_ppm * P_RT * M_N2O * 1000
    
    # Fluxo (mg/m²/h)
    fluxo_ch4 = (C_ch4_mg_m3 * Q_total_m3h) / area_camara_yang
    fluxo_n2o = (C_n2o_mg_m3 * Q_total_m3h) / area_camara_yang
    
    fluxos_dia.append({
        'data': dia,
        'fluxo_CH4_mg': fluxo_ch4,
        'fluxo_N2O_mg': fluxo_n2o,
        'C_ch4_ppm': C_ch4_ppm,
        'C_n2o_ppm': C_n2o_ppm
    })

df_fluxos = pd.DataFrame(fluxos_dia).sort_values('data')
st.write("Fluxos calculados por dia de medição:")
st.dataframe(df_fluxos)
st.line_chart(df_fluxos.set_index('data')[['fluxo_CH4_mg', 'fluxo_N2O_mg']])

# ============================================================
# SEÇÃO 6: COMPARAÇÃO COM RESULTADOS DO ARTIGO (OPCIONAL)
# ============================================================
st.header("6. Comparação com Yang et al. 2017 (opcional)")

st.markdown("""
Para reproduzir os valores do artigo, utilize:
- Massa seca total: **375 kg**
- Teor de C inicial: **43,6%**
- Teor de N inicial: **1,42%**
- Área do reator: **1,5 m²**
- Vazão de ar de arraste: **5 L/min**
- Área da câmara: **0,13 m²**

Após calcular os fluxos diários, integre-os ao longo do tempo para obter as emissões acumuladas.
""")

if st.checkbox("Calcular emissões acumuladas (necessário área do reator e intervalos entre medições)"):
    area_reator = st.number_input("Área da base do reator (m²)", value=1.5, step=0.1)
    
    # Estimar intervalos entre medições (dias consecutivos)
    df_fluxos = df_fluxos.copy()
    df_fluxos['data_prox'] = df_fluxos['data'].shift(-1)
    df_fluxos['intervalo_dias'] = (df_fluxos['data_prox'] - df_fluxos['data']).dt.days
    # Para o último dia, assumir intervalo igual à mediana dos anteriores
    ultimo_intervalo = df_fluxos['intervalo_dias'].median()
    df_fluxos.loc[df_fluxos.index[-1], 'intervalo_dias'] = ultimo_intervalo
    
    # Converter fluxo (mg/m²/h) para massa emitida no período (kg)
    # massa (kg) = fluxo (mg/m²/h) * 1e-6 * área_reator (m²) * intervalo (dias) * 24 h/dia
    df_fluxos['massa_CH4_kg'] = df_fluxos['fluxo_CH4_mg'] * 1e-6 * area_reator * df_fluxos['intervalo_dias'] * 24
    df_fluxos['massa_N2O_kg'] = df_fluxos['fluxo_N2O_mg'] * 1e-6 * area_reator * df_fluxos['intervalo_dias'] * 24
    
    total_CH4_kg = df_fluxos['massa_CH4_kg'].sum()
    total_N2O_kg = df_fluxos['massa_N2O_kg'].sum()
    
    st.write(f"**Emissão total de CH₄:** {total_CH4_kg:.4f} kg")
    st.write(f"**Emissão total de N₂O:** {total_N2O_kg:.4f} kg")
    
    # Perdas de C e N
    C_perdido_CH4 = total_CH4_kg * (M_C / M_CH4)
    N_perdido_N2O = total_N2O_kg * (2 * M_N / M_N2O)
    
    massa_seca_total = st.number_input("Massa seca total (kg)", value=375.0, key="massa_seca")
    teor_c = st.number_input("Teor de C inicial (%)", value=43.6, key="teor_c")
    teor_n = st.number_input("Teor de N inicial (%)", value=1.42, key="teor_n")
    
    C_inicial_kg = massa_seca_total * teor_c / 100
    N_inicial_kg = massa_seca_total * teor_n / 100
    
    perc_C = (C_perdido_CH4 / C_inicial_kg) * 100
    perc_N = (N_perdido_N2O / N_inicial_kg) * 100
    
    st.write(f"**Carbono perdido como CH₄:** {C_perdido_CH4:.4f} kg ({perc_C:.3f}% do C inicial)")
    st.write(f"**Yang et al. (2017):** 0,13%")
    st.write(f"**Nitrogênio perdido como N₂O:** {N_perdido_N2O:.4f} kg ({perc_N:.3f}% do N inicial)")
    st.write(f"**Yang et al. (2017):** 0,92%")
    
    # GEE por tonelada de MS
    GWP_CH4 = 25
    GWP_N2O = 298
    CO2eq_CH4 = total_CH4_kg * GWP_CH4
    CO2eq_N2O = total_N2O_kg * GWP_N2O
    CO2eq_total = CO2eq_CH4 + CO2eq_N2O
    CO2eq_por_t = CO2eq_total / (massa_seca_total / 1000)   # kg CO₂-eq / t MS
    
    st.write(f"**Emissão total de GEE:** {CO2eq_total:.2f} kg CO₂-eq")
    st.write(f"**Emissão por tonelada de MS:** {CO2eq_por_t:.2f} kg CO₂-eq/t MS")
    st.write(f"**Yang et al. (2017):** 8,1 kg CO₂-eq/t MS")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.caption("Aplicativo desenvolvido para análise de emissões em vermicompostagem, baseado em Yang et al. 2017.")
