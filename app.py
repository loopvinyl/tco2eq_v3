import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================
st.set_page_config(page_title="Analisador de Emissões - Vermicompostagem", layout="wide")
st.title("📊 Análise de Emissões de Gases em Vermicompostagem")
st.markdown("Aplicativo para cálculo de emissões de CH₄ e N₂O, perda de C/N, CO₂ equivalente e fluxo pelos métodos científico e de Yang et al. (2017)")

# Constantes universais
R = 8.314                     # Constante dos gases (J/mol·K)
VOLUME_CAMARA = 0.03          # m³ (calibrado para o artigo Yang)
M_CH4 = 16.04                 # g/mol
M_N2O = 44.01                 # g/mol
GWP_CH4 = 25                  # IPCC 100 anos
GWP_N2O = 298

# ============================================================
# SIDEBAR - CARREGAMENTO DE DADOS E PARÂMETROS
# ============================================================
st.sidebar.header("1. Carregar dados")
uploaded_file = st.sidebar.file_uploader("Escolha um arquivo CSV", type="csv")

if uploaded_file is not None:
    dados = pd.read_csv(uploaded_file, parse_dates=['timestamp'])
    dados.set_index('timestamp', inplace=True)
    dados.sort_index(inplace=True)

    st.sidebar.success("Arquivo carregado com sucesso!")
    st.sidebar.write(f"Número de linhas: {len(dados)}")
    st.sidebar.write(f"Período: {dados.index.min().date()} a {dados.index.max().date()}")

    # Mostrar amostra dos dados
    with st.expander("Prévia dos dados carregados"):
        st.dataframe(dados.head(10))
else:
    st.warning("Por favor, carregue um arquivo CSV no formato adequado.")
    st.stop()

# Parâmetros gerais (podem ser ajustados pelo usuário)
st.sidebar.header("2. Parâmetros da câmara")
area_camara = st.sidebar.number_input("Área da base da câmara (m²)", value=0.13, step=0.01, format="%.2f")
# Para o método de Yang, também precisamos da vazão de ar (pode ser definida depois)

st.sidebar.header("3. Parâmetros do experimento")
massa_seca_total = st.sidebar.number_input("Massa seca total (kg)", value=375.0, help="Estimativa para reator de 1,5 m³")
teor_c_inicial = st.sidebar.number_input("Teor de C inicial (% MS)", value=43.6, step=0.1)
teor_n_inicial = st.sidebar.number_input("Teor de N inicial (% MS)", value=1.42, step=0.01)
area_reator = st.sidebar.number_input("Área da base do reator (m²)", value=1.5, help="Usada para integrar fluxos e obter emissão total")

# ============================================================
# VISUALIZAÇÃO DOS DADOS BRUTOS
# ============================================================
st.header("📈 Dados brutos de concentração")
fig, ax = plt.subplots(2, 1, figsize=(10, 6))
ax[0].plot(dados.index, dados['CH4_ppm'], color='green', marker='.', linestyle='-', markersize=2)
ax[0].set_ylabel('CH₄ (ppm)')
ax[0].grid(True)
ax[1].plot(dados.index, dados['N2O_ppm'], color='blue', marker='.', linestyle='-', markersize=2)
ax[1].set_ylabel('N₂O (ppm)')
ax[1].grid(True)
plt.xticks(rotation=45)
st.pyplot(fig)

# ============================================================
# CÁLCULOS BÁSICOS: MASSA DE GÁS E PERDA DE C/N
# ============================================================
st.header("⚖️ Massa de gás e perda de C/N (baseado na concentração)")

# Usar média de P e T para os cálculos
P_media = dados['P_Pa'].mean()
T_media = dados['T_K'].mean()
st.write(f"Pressão média: {P_media:.0f} Pa | Temperatura média: {T_media:.2f} K")

# Fator de conversão ppm -> mol/m³
mol_por_m3 = P_media / (R * T_media)   # mol/m³

# Massa de cada gás na câmara em cada instante (kg)
dados['massa_CH4_kg'] = dados['CH4_ppm'] * 1e-6 * mol_por_m3 * M_CH4 * VOLUME_CAMARA / 1000   # /1000 para kg
dados['massa_N2O_kg'] = dados['N2O_ppm'] * 1e-6 * mol_por_m3 * M_N2O * VOLUME_CAMARA / 1000

# Calcular perdas como diferença entre primeiro e último ponto (simplificado)
massa_inicial_CH4 = dados['massa_CH4_kg'].iloc[0]
massa_final_CH4 = dados['massa_CH4_kg'].iloc[-1]
massa_inicial_N2O = dados['massa_N2O_kg'].iloc[0]
massa_final_N2O = dados['massa_N2O_kg'].iloc[-1]

st.write(f"Massa inicial CH₄: {massa_inicial_CH4:.6f} kg")
st.write(f"Massa final CH₄: {massa_final_CH4:.6f} kg")
st.write(f"Massa inicial N₂O: {massa_inicial_N2O:.6f} kg")
st.write(f"Massa final N₂O: {massa_final_N2O:.6f} kg")

# Perda de C e N (apenas a partir da diferença de massa; não é o método mais preciso)
C_perdido_bruto = (massa_inicial_CH4 - massa_final_CH4) * (12/16) if massa_inicial_CH4 > massa_final_CH4 else 0
N_perdido_bruto = (massa_inicial_N2O - massa_final_N2O) * (28/44) if massa_inicial_N2O > massa_final_N2O else 0
st.write(f"**Perda bruta de C como CH₄:** {C_perdido_bruto:.6f} kg")
st.write(f"**Perda bruta de N como N₂O:** {N_perdido_bruto:.6f} kg")

# ============================================================
# CÁLCULO DE FLUXO - MÉTODO CIENTÍFICO (dC/dt)
# ============================================================
st.header("🌀 Fluxo pelo método científico (dC/dt) - Câmara estática")

# Calcular diferenças de tempo e concentração
dados['delta_t_h'] = dados.index.to_series().diff().dt.total_seconds() / 3600
dados['dCH4_dt'] = dados['CH4_ppm'].diff() / dados['delta_t_h']
dados['dN2O_dt'] = dados['N2O_ppm'].diff() / dados['delta_t_h']

# Fluxo em mg/m²/h
dados['flux_CH4_scientific'] = (
    dados['dCH4_dt'] * 1e-6 *
    (dados['P_Pa'] * VOLUME_CAMARA) / (R * dados['T_K']) *
    M_CH4 / area_camara * 1000
)

dados['flux_N2O_scientific'] = (
    dados['dN2O_dt'] * 1e-6 *
    (dados['P_Pa'] * VOLUME_CAMARA) / (R * dados['T_K']) *
    M_N2O / area_camara * 1000
)

st.line_chart(dados[['flux_CH4_scientific', 'flux_N2O_scientific']])
st.write(f"**Fluxo médio CH₄ (mg m⁻² h⁻¹):** {dados['flux_CH4_scientific'].mean():.4f}")
st.write(f"**Fluxo médio N₂O (mg m⁻² h⁻¹):** {dados['flux_N2O_scientific'].mean():.4f}")

# ============================================================
# MÉTODO DE CÂMARA DE FLUXO CONTÍNUO (YANG ET AL. 2017)
# ============================================================
st.header("🌪️ Método de câmara de fluxo contínuo (Yang et al.)")

col1, col2 = st.columns(2)
with col1:
    Q_sw = st.number_input("Vazão de ar de arraste (L/min)", value=5.0, step=0.5)
    usar_Q_ad = st.checkbox("Usar vazão adicional (Q_ad)")
    if usar_Q_ad:
        Q_ad = st.number_input("Q_ad (L/min)", value=0.0, step=0.1)
    else:
        Q_ad = 0.0
with col2:
    area_camara_yang = st.number_input("Área da câmara (m²) - Yang", value=area_camara, step=0.01)
    st.info("Concentrações devem estar em ppm. O cálculo assume que as medições representam o estado estacionário.")

Q_total_m3h = (Q_sw + Q_ad) * 60 / 1000  # m³/h

# Agrupar por dia e calcular fluxo diário
dados['data'] = dados.index.date
fluxos_dia = []

for dia, grupo in dados.groupby('data'):
    # Média das concentrações no dia
    C_ch4_ppm = grupo['CH4_ppm'].mean()
    C_n2o_ppm = grupo['N2O_ppm'].mean()
    
    # Converter ppm para mg/m³ usando P e T médios do dia
    P_media_dia = grupo['P_Pa'].mean()
    T_media_dia = grupo['T_K'].mean()
    P_RT = P_media_dia / (R * T_media_dia)
    C_ch4_mg_m3 = C_ch4_ppm * 1e-6 * P_RT * M_CH4 * 1e3  # ppm -> mg/m³
    C_n2o_mg_m3 = C_n2o_ppm * 1e-6 * P_RT * M_N2O * 1e3
    
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
st.write("Fluxos calculados por dia (método Yang):")
st.dataframe(df_fluxos.style.format({
    'fluxo_CH4_mg': '{:.2f}',
    'fluxo_N2O_mg': '{:.2f}',
    'C_ch4_ppm': '{:.2f}',
    'C_n2o_ppm': '{:.3f}'
}))

st.line_chart(df_fluxos.set_index('data')[['fluxo_CH4_mg', 'fluxo_N2O_mg']])

# ============================================================
# INTEGRAÇÃO TEMPORAL E COMPARAÇÃO COM YANG ET AL. 2017
# ============================================================
st.header("⏱️ Emissões acumuladas e comparação com o artigo")

# Calcular intervalos entre medições (em horas)
df_fluxos = df_fluxos.copy()
df_fluxos['data_prox'] = df_fluxos['data'].shift(-1)
df_fluxos['intervalo_h'] = (df_fluxos['data_prox'] - df_fluxos['data']).dt.total_seconds() / 3600
# Último intervalo: assumir que dura até o fim do experimento (último dia + 5 dias, ajustável)
ultimo_intervalo_dias = st.number_input("Duração após última medição (dias)", value=5)
df_fluxos.loc[df_fluxos.index[-1], 'intervalo_h'] = ultimo_intervalo_dias * 24

# Calcular massa emitida em cada período (kg)
df_fluxos['massa_CH4_kg'] = df_fluxos['fluxo_CH4_mg'] * 1e-6 * area_reator * df_fluxos['intervalo_h']
df_fluxos['massa_N2O_kg'] = df_fluxos['fluxo_N2O_mg'] * 1e-6 * area_reator * df_fluxos['intervalo_h']

# Totais
total_CH4_kg = df_fluxos['massa_CH4_kg'].sum()
total_N2O_kg = df_fluxos['massa_N2O_kg'].sum()

st.write(f"**Emissão total de CH₄:** {total_CH4_kg:.4f} kg")
st.write(f"**Emissão total de N₂O:** {total_N2O_kg:.4f} kg")

# Perdas de C e N
C_perdido = total_CH4_kg * (12/16)
N_perdido = total_N2O_kg * (28/44)
C_inicial_kg = massa_seca_total * (teor_c_inicial / 100)
N_inicial_kg = massa_seca_total * (teor_n_inicial / 100)

perc_C_perdido = (C_perdido / C_inicial_kg) * 100 if C_inicial_kg > 0 else 0
perc_N_perdido = (N_perdido / N_inicial_kg) * 100 if N_inicial_kg > 0 else 0

st.write(f"**Carbono perdido como CH₄:** {C_perdido:.4f} kg ({perc_C_perdido:.3f}% do C inicial)")
st.write(f"**Nitrogênio perdido como N₂O:** {N_perdido:.4f} kg ({perc_N_perdido:.3f}% do N inicial)")

# GEE total
CO2eq_CH4 = total_CH4_kg * GWP_CH4
CO2eq_N2O = total_N2O_kg * GWP_N2O
CO2eq_total = CO2eq_CH4 + CO2eq_N2O
massa_seca_t = massa_seca_total / 1000
CO2eq_por_t = CO2eq_total / massa_seca_t

st.write(f"**Emissão total de GEE:** {CO2eq_total:.2f} kg CO₂-eq")
st.write(f"**Emissão por tonelada de MS:** {CO2eq_por_t:.2f} kg CO₂-eq/t MS")

# Comparação com Yang
st.markdown("### Comparação com Yang et al. (2017) - Vermicompostagem")
st.write(f"Seu resultado - % C perdido (CH₄): **{perc_C_perdido:.3f}%** (Yang: 0,13%)")
st.write(f"Seu resultado - % N perdido (N₂O): **{perc_N_perdido:.3f}%** (Yang: 0,92%)")
st.write(f"Seu resultado - GEE por tonelada: **{CO2eq_por_t:.2f}** (Yang: 8,1 kg CO₂-eq/t MS)")

st.info("""
**Nota:** Os valores calculados dependem fortemente dos parâmetros inseridos (massa seca, teores de C/N, área do reator, vazão, etc.). 
Para reproduzir exatamente os números do artigo, utilize os parâmetros calibrados: 
- Massa seca total = 375 kg 
- Teor de C inicial = 43,6% 
- Teor de N inicial = 1,42% 
- Área do reator = 1,5 m² 
- Vazão Q_sw = 5 L/min 
- Área da câmara = 0,13 m² 
- Dados gerados com o script fornecido.
""")

# ============================================================
# DOWNLOAD DOS RESULTADOS (opcional)
# ============================================================
st.header("📥 Download dos resultados")
resultados = pd.DataFrame({
    'data': df_fluxos['data'],
    'fluxo_CH4_mg_m2_h': df_fluxos['fluxo_CH4_mg'],
    'fluxo_N2O_mg_m2_h': df_fluxos['fluxo_N2O_mg'],
    'C_ch4_ppm': df_fluxos['C_ch4_ppm'],
    'C_n2o_ppm': df_fluxos['C_n2o_ppm'],
    'intervalo_h': df_fluxos['intervalo_h']
})
csv = resultados.to_csv(index=False).encode('utf-8')
st.download_button("Baixar fluxos calculados (CSV)", csv, "fluxos_diarios.csv", "text/csv")

st.success("Análise concluída!")
