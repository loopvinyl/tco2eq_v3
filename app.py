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

# Constantes Físico-Químicas
R = 8.314                     # J/(mol·K)
VOLUME_CAMARA_PADRAO = 0.03   # m³ (30 L) – valor do artigo
M_CH4 = 16.04                 # g/mol
M_N2O = 44.01                 # g/mol
M_C = 12.01                   # g/mol
M_N = 14.01                   # g/mol

# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================
try:
    # Tenta ler o arquivo CSV (pode ser o completo ou só cromatógrafo)
    dados = pd.read_csv('dados_cromatografo.csv', parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    st.success("✅ Arquivo 'dados_cromatografo.csv' carregado!")
except FileNotFoundError:
    st.error("❌ Arquivo 'dados_cromatografo.csv' não encontrado. Certifique-se de que ele está na mesma pasta do app.")
    st.stop()

# Visualização inicial
st.subheader("Visualização dos dados carregados")
st.write(dados.head())

# ============================================================
# SIDEBAR - PARÂMETROS INICIAIS (baseados no Excel 2)
# ============================================================
st.sidebar.header("Parâmetros Iniciais")
massa_umida = st.sidebar.number_input("Massa Inicial Úmida (kg)", value=245.28)
umidade_perc = st.sidebar.number_input("Umidade (%)", value=50.8)
massa_seca_kg = massa_umida * (1 - umidade_perc / 100)
st.sidebar.write(f"**Matéria Seca (MS):** {massa_seca_kg:.2f} kg")

teor_c_perc = st.sidebar.number_input("Teor de C na MS (%)", value=43.6)
teor_n_gkg = st.sidebar.number_input("Teor de N na MS (g/kg)", value=14.2)

C_inicial_kg = massa_seca_kg * (teor_c_perc / 100)
N_inicial_kg = massa_seca_kg * (teor_n_gkg / 1000)

# ============================================================
# VERIFICAÇÃO E AJUSTE DE PRESSÃO/TEMPERATURA
# ============================================================
# Se as colunas de pressão e temperatura não existirem, o usuário fornece valores constantes
if 'P_Pa' not in dados.columns or 'T_K' not in dados.columns:
    st.info("O arquivo não contém colunas de pressão e temperatura. Informe os valores constantes abaixo.")
    col_p, col_t = st.columns(2)
    with col_p:
        P_const = st.number_input("Pressão constante (Pa)", value=101325.0)
    with col_t:
        T_const = st.number_input("Temperatura constante (K)", value=298.15)
    # Adiciona as colunas com valores constantes
    dados['P_Pa'] = P_const
    dados['T_K'] = T_const
else:
    st.success("Colunas de pressão e temperatura encontradas no arquivo.")

# ============================================================
# PARÂMETROS DA CÂMARA (GERAL)
# ============================================================
st.subheader("Parâmetros da câmara")
col1, col2 = st.columns(2)
with col1:
    area_camara = st.number_input("Área da base da câmara (m²)", value=0.13, step=0.01, key="area_camara_principal")
with col2:
    volume_camara = st.number_input("Volume da câmara (m³)", value=VOLUME_CAMARA_PADRAO, step=0.01, key="volume_camara_principal")

# ============================================================
# SEÇÃO 1: MASSA DE GÁS NA CÂMARA (INSTANTÂNEA) - EM mg
# ============================================================
st.header("1. Massa de gás na câmara")
dados['CH4_mol'] = dados['CH4_ppm'] * 1e-6
dados['N2O_mol'] = dados['N2O_ppm'] * 1e-6

P_media = dados['P_Pa'].mean()
T_media = dados['T_K'].mean()
n_total = (P_media * volume_camara) / (R * T_media)   # mol

dados['massa_CH4_g'] = dados['CH4_mol'] * n_total * M_CH4
dados['massa_N2O_g'] = dados['N2O_mol'] * n_total * M_N2O

# Converter para miligramas
dados['massa_CH4_mg'] = dados['massa_CH4_g'] * 1000
dados['massa_N2O_mg'] = dados['massa_N2O_g'] * 1000

st.line_chart(dados[['massa_CH4_mg', 'massa_N2O_mg']])
st.write("Massa média CH₄ (mg):", round(dados['massa_CH4_mg'].mean(), 6))
st.write("Massa média N₂O (mg):", round(dados['massa_N2O_mg'].mean(), 6))

# ============================================================
# SEÇÃO 5: MÉTODO DE CÂMARA DE FLUXO CONTÍNUO (YANG ET AL.)
# ============================================================
st.header("5. Fluxo de emissão - método de câmara de fluxo contínuo (Yang et al. 2017)")

st.markdown("""
**Equação:**  
\(E = \dfrac{Y \cdot Q_{sw}}{A}\)

- \(E\): fluxo de emissão (mg m⁻² h⁻¹)  
- \(Y\): concentração do gás na saída (mg m⁻³)  
- \(Q_{sw}\): vazão de ar de arraste (m³ h⁻¹)  
- \(A\): área da base da câmara (m²)
""")

col1, col2 = st.columns(2)
with col1:
    Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0, step=0.1)
    area_camara_yang = area_camara
    st.write(f"Área da câmara (usada): **{area_camara_yang} m²**")
with col2:
    area_reator = st.number_input("Área total do reator/leito (m²)", value=1.5, step=0.1, key="area_reator_principal")

Q_total_m3h = Q_sw * 60 / 1000  # L/min → m³/h

dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    C_ch4_ppm = grupo['CH4_ppm'].mean()
    C_n2o_ppm = grupo['N2O_ppm'].mean()
    P_media_dia = grupo['P_Pa'].mean()
    T_media_dia = grupo['T_K'].mean()
    
    P_RT = P_media_dia / (R * T_media_dia)   # mol/m³
    C_ch4_mg_m3 = C_ch4_ppm * 1e-6 * P_RT * M_CH4 * 1000
    C_n2o_mg_m3 = C_n2o_ppm * 1e-6 * P_RT * M_N2O * 1000
    
    fluxo_ch4 = (C_ch4_mg_m3 * Q_total_m3h) / area_camara_yang
    fluxo_n2o = (C_n2o_mg_m3 * Q_total_m3h) / area_camara_yang
    
    fluxos_dia.append({
        'data': dia,
        'fluxo_CH4_mg': fluxo_ch4,
        'fluxo_N2O_mg': fluxo_n2o,
    })

df_fluxos = pd.DataFrame(fluxos_dia).sort_values('data')
df_fluxos['data'] = pd.to_datetime(df_fluxos['data'])

st.write("Fluxos calculados por dia de medição:")
st.dataframe(df_fluxos)
st.line_chart(df_fluxos.set_index('data')[['fluxo_CH4_mg', 'fluxo_N2O_mg']])

# ============================================================
# SEÇÃO 2: PERDA ACUMULADA DE C E N (BASEADA NOS FLUXOS DIÁRIOS)
# ============================================================
st.header("2. Perda de C e N (base acumulada)")

if df_fluxos.empty:
    st.warning("Calcule os fluxos diários na seção 5 primeiro.")
else:
    # Calcula intervalos entre medições (em dias)
    df_temp = df_fluxos.copy()
    df_temp['data_prox'] = df_temp['data'].shift(-1)
    df_temp['intervalo_dias'] = (df_temp['data_prox'] - df_temp['data']).dt.days
    # Último intervalo: usar a mediana dos anteriores
    ultimo_intervalo = df_temp['intervalo_dias'].median()
    df_temp.loc[df_temp.index[-1], 'intervalo_dias'] = ultimo_intervalo
    
    # Massa emitida em cada período (kg)
    df_temp['massa_CH4_kg'] = df_temp['fluxo_CH4_mg'] * 1e-6 * area_reator * df_temp['intervalo_dias'] * 24
    df_temp['massa_N2O_kg'] = df_temp['fluxo_N2O_mg'] * 1e-6 * area_reator * df_temp['intervalo_dias'] * 24
    
    total_CH4_kg = df_temp['massa_CH4_kg'].sum()
    total_N2O_kg = df_temp['massa_N2O_kg'].sum()
    
    C_perdido = total_CH4_kg * (M_C / M_CH4)
    N_perdido = total_N2O_kg * (2 * M_N / M_N2O)
    
    # Usa os valores da sidebar para massa seca e teores
    C_total_kg = C_inicial_kg
    N_total_kg = N_inicial_kg
    
    perc_C = (C_perdido / C_total_kg) * 100 if C_total_kg > 0 else 0
    perc_N = (N_perdido / N_total_kg) * 100 if N_total_kg > 0 else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Carbono perdido como CH₄",
            f"{C_perdido:.4f} kg",
            delta=f"-{perc_C:.3f}% do C inicial",
            delta_color="normal"
        )
    with col2:
        st.metric(
            "Nitrogênio perdido como N₂O",
            f"{N_perdido:.4f} kg",
            delta=f"-{perc_N:.3f}% do N inicial",
            delta_color="normal"
        )
    
    st.caption("Os valores negativos indicam perda de carbono e nitrogênio do sistema, emitidos como CH₄ e N₂O.")
    st.info("**Referência Yang et al. (2017):** 0,13% do C e 0,92% do N")

# ============================================================
# SEÇÃO 6: COMPARAÇÃO DETALHADA (OPCIONAL)
# ============================================================
st.header("6. Comparação com Yang et al. 2017 (opcional)")

if st.checkbox("Calcular emissões acumuladas (necessário área do reator e intervalos entre medições)"):
    area_reator_comp = st.number_input("Área da base do reator (m²)", value=area_reator, step=0.1, key="area_reator_comp")
    
    df_temp = df_fluxos.copy()
    df_temp['data_prox'] = df_temp['data'].shift(-1)
    df_temp['data_prox'] = pd.to_datetime(df_temp['data_prox'])
    df_temp['intervalo_dias'] = (df_temp['data_prox'] - df_temp['data']).dt.days
    ultimo_intervalo = df_temp['intervalo_dias'].median()
    df_temp.loc[df_temp.index[-1], 'intervalo_dias'] = ultimo_intervalo
    
    df_temp['massa_CH4_kg'] = df_temp['fluxo_CH4_mg'] * 1e-6 * area_reator_comp * df_temp['intervalo_dias'] * 24
    df_temp['massa_N2O_kg'] = df_temp['fluxo_N2O_mg'] * 1e-6 * area_reator_comp * df_temp['intervalo_dias'] * 24
    
    total_CH4_kg = df_temp['massa_CH4_kg'].sum()
    total_N2O_kg = df_temp['massa_N2O_kg'].sum()
    
    st.write(f"**Emissão total de CH₄:** {total_CH4_kg:.4f} kg")
    st.write(f"**Emissão total de N₂O:** {total_N2O_kg:.4f} kg")
    
    C_perdido = total_CH4_kg * (M_C / M_CH4)
    N_perdido = total_N2O_kg * (2 * M_N / M_N2O)
    
    st.write(f"Massa seca total (da sidebar): {massa_seca_kg:.2f} kg")
    C_inicial_kg = massa_seca_kg * (teor_c_perc / 100)
    N_inicial_kg = massa_seca_kg * (teor_n_gkg / 1000)
    
    perc_C = (C_perdido / C_inicial_kg) * 100
    perc_N = (N_perdido / N_inicial_kg) * 100
    
    st.write(f"**Carbono perdido como CH₄:** {C_perdido:.4f} kg ({perc_C:.3f}% do C inicial)")
    st.write(f"**Yang et al. (2017):** 0,13%")
    st.write(f"**Nitrogênio perdido como N₂O:** {N_perdido:.4f} kg ({perc_N:.3f}% do N inicial)")
    st.write(f"**Yang et al. (2017):** 0,92%")
    
    GWP_CH4 = 25
    GWP_N2O = 298
    CO2eq_CH4 = total_CH4_kg * GWP_CH4
    CO2eq_N2O = total_N2O_kg * GWP_N2O
    CO2eq_total = CO2eq_CH4 + CO2eq_N2O
    CO2eq_por_t = CO2eq_total / (massa_seca_kg / 1000) if massa_seca_kg > 0 else 0
    
    st.write(f"**Emissão total de GEE:** {CO2eq_total:.2f} kg CO₂-eq")
    st.write(f"**Emissão por tonelada de MS:** {CO2eq_por_t:.2f} kg CO₂-eq/t MS")
    st.write(f"**Yang et al. (2017):** 8,1 kg CO₂-eq/t MS")

# ============================================================
# RODAPÉ
# ============================================================
st.markdown("---")
st.caption("Aplicativo desenvolvido para análise de emissões em vermicompostagem, baseado em Yang et al. 2017. Parâmetros iniciais conforme Excel 2.")
