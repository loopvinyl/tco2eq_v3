import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px

# ==================== CONFIGURAÇÕES INICIAIS ====================
st.set_page_config(page_title="VermiSense IoT", layout="wide")
st.title("🌱 VermiSense – Monitoramento IoT de Emissões em Vermicompostagem")
st.markdown("**Solução IoT para coleta automática de dados de CH₄ e N₂O em vermicomposteiras, com cálculo de emissões e impacto ambiental.**")

# ==================== CONEXÃO COM BANCO DE DADOS ====================
conn = sqlite3.connect('vermisense.db', check_same_thread=False)
c = conn.cursor()

# Cria tabelas se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                localizacao TEXT,
                area_pilha REAL,
                area_camara REAL,
                vazao_ar REAL,
                massa_inicial REAL,
                umidade REAL,
                toc REAL,
                tn REAL,
                gwp_ch4 INTEGER,
                gwp_n2o INTEGER
            )''')

c.execute('''CREATE TABLE IF NOT medicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dispositivo_id INTEGER,
                timestamp DATETIME,
                ch4 REAL,
                n2o REAL,
                FOREIGN KEY(dispositivo_id) REFERENCES dispositivos(id)
            )''')
conn.commit()

# ==================== SIDEBAR: GERENCIAMENTO DE DISPOSITIVOS ====================
with st.sidebar:
    st.header("📡 Gerenciar Dispositivos IoT")
    with st.expander("➕ Adicionar novo dispositivo"):
        with st.form("form_dispositivo"):
            nome = st.text_input("Nome do dispositivo", value="Vermicomposteira 1")
            local = st.text_input("Localização", value="Setor A")
            area_pilha = st.number_input("Área superficial da pilha (m²)", value=1.5)
            area_camara = st.number_input("Área da câmara de fluxo (m²)", value=0.13)
            vazao = st.number_input("Vazão de ar (L/min)", value=5.0)
            massa = st.number_input("Massa inicial de resíduos (kg)", value=1500.0)
            umidade = st.number_input("Umidade inicial (%)", value=50.8)
            toc = st.number_input("Carbono orgânico total (%)", value=43.6)
            tn = st.number_input("Nitrogênio total (g/kg)", value=14.2)
            gwp_ch4 = st.number_input("GWP CH₄", value=25)
            gwp_n2o = st.number_input("GWP N₂O", value=298)
            submitted = st.form_submit_button("Salvar dispositivo")
            if submitted:
                c.execute('''INSERT INTO dispositivos 
                            (nome, localizacao, area_pilha, area_camara, vazao_ar, massa_inicial, 
                             umidade, toc, tn, gwp_ch4, gwp_n2o)
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                          (nome, local, area_pilha, area_camara, vazao, massa, umidade, toc, tn, gwp_ch4, gwp_n2o))
                conn.commit()
                st.success("Dispositivo cadastrado!")

    # Lista dispositivos existentes
    dispositivos_df = pd.read_sql("SELECT id, nome, localizacao FROM dispositivos", conn)
    if not dispositivos_df.empty:
        st.subheader("📋 Dispositivos ativos")
        st.dataframe(dispositivos_df, use_container_width=True)
    else:
        st.info("Nenhum dispositivo cadastrado. Adicione um para começar.")

# ==================== SEÇÃO PRINCIPAL ====================
if dispositivos_df.empty:
    st.warning("Cadastre pelo menos um dispositivo no menu lateral para começar.")
    st.stop()

# Seleciona dispositivo para visualização
dispositivo_id = st.selectbox("Selecione o dispositivo para monitorar", 
                              options=dispositivos_df['id'].tolist(),
                              format_func=lambda x: dispositivos_df[dispositivos_df['id']==x]['nome'].values[0])

# Busca parâmetros do dispositivo selecionado
params = pd.read_sql(f"SELECT * FROM dispositivos WHERE id = {dispositivo_id}", conn).iloc[0]

# ==================== SIMULAÇÃO DE RECEBIMENTO AUTOMÁTICO DE DADOS ====================
st.subheader("📲 Recebimento de dados IoT")
st.markdown("**Simulação:** Cada clique no botão abaixo gera uma nova leitura dos sensores, como se os dados fossem enviados automaticamente via rede.")

if st.button("📡 Receber nova medição automática"):
    # Gera valores típicos (podem ser ajustados conforme necessidade)
    novo_ch4 = np.random.normal(50, 20)  # mg/m³
    novo_n2o = np.random.normal(3, 1)    # mg/m³
    timestamp = datetime.now()
    c.execute("INSERT INTO medicoes (dispositivo_id, timestamp, ch4, n2o) VALUES (?, ?, ?, ?)",
              (dispositivo_id, timestamp, novo_ch4, novo_n2o))
    conn.commit()
    st.success(f"Nova medição registrada: CH₄ = {novo_ch4:.2f} mg/m³, N₂O = {novo_n2o:.2f} mg/m³")

# ==================== VISUALIZAÇÃO DOS DADOS ====================
st.subheader("📈 Histórico de medições")
medicoes = pd.read_sql(f"SELECT timestamp, ch4, n2o FROM medicoes WHERE dispositivo_id = {dispositivo_id} ORDER BY timestamp", conn)
if not medicoes.empty:
    # Filtro de data
    min_date = medicoes['timestamp'].min().date()
    max_date = medicoes['timestamp'].max().date()
    data_inicio = st.date_input("Data inicial", min_date)
    data_fim = st.date_input("Data final", max_date)
    medicoes_filtradas = medicoes[(medicoes['timestamp'].dt.date >= data_inicio) & 
                                  (medicoes['timestamp'].dt.date <= data_fim)]
    
    # Gráfico interativo com Plotly
    fig = px.line(medicoes_filtradas, x='timestamp', y=['ch4', 'n2o'], 
                  labels={'value':'Concentração (mg/m³)', 'timestamp':'Data'},
                  title='Concentrações de CH₄ e N₂O ao longo do tempo')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabela com dados recentes
    st.dataframe(medicoes_filtradas.sort_values('timestamp', ascending=False).head(10))
else:
    st.info("Nenhuma medição encontrada para este dispositivo.")

# ==================== CÁLCULO DAS EMISSÕES ====================
st.subheader("🌍 Cálculo de Emissões de GEE")
if len(medicoes) < 2:
    st.warning("São necessárias pelo menos duas medições para calcular fluxos e emissões.")
else:
    # Parâmetros do dispositivo
    area_camara = params['area_camara']
    vazao = params['vazao_ar'] / 1000  # m³/min
    area_pilha = params['area_pilha']
    massa_inicial = params['massa_inicial']
    umidade = params['umidade']
    toc = params['toc']
    tn = params['tn']
    gwp_ch4 = params['gwp_ch4']
    gwp_n2o = params['gwp_n2o']
    
    # Preparar dados com fluxo diário
    df = medicoes.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df['dias'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds() / (3600 * 24)
    
    # Cálculo do fluxo horário (mg/m²·h)
    Q = vazao  # m³/min
    df['flux_ch4_h'] = (df['ch4'] * Q * 60) / area_camara
    df['flux_n2o_h'] = (df['n2o'] * Q * 60) / area_camara
    
    # Fluxo diário (mg/m²·dia)
    df['flux_ch4_d'] = df['flux_ch4_h'] * 24
    df['flux_n2o_d'] = df['flux_n2o_h'] * 24
    
    # Integração (mg/m²) usando regra do trapézio
    cum_ch4_mg_m2 = np.trapz(df['flux_ch4_d'], df['dias'])
    cum_n2o_mg_m2 = np.trapz(df['flux_n2o_d'], df['dias'])
    
    # Extrapolação para a pilha inteira
    fator_extrapolacao = area_pilha / area_camara
    cum_ch4_kg = cum_ch4_mg_m2 * area_camara / 1e6 * fator_extrapolacao
    cum_n2o_kg = cum_n2o_mg_m2 * area_camara / 1e6 * fator_extrapolacao
    
    # Balanço de massa
    materia_seca = massa_inicial * (1 - umidade/100)  # kg
    carbono_inicial = materia_seca * (toc / 100)      # kg C
    nitrogenio_inicial = (tn / 1000) * materia_seca   # kg N
    
    ch4_c_kg = cum_ch4_kg * (12/16)      # kg C
    n2o_n_kg = cum_n2o_kg * (28/44)      # kg N
    
    perc_c = (ch4_c_kg / carbono_inicial * 100) if carbono_inicial > 0 else 0
    perc_n = (n2o_n_kg / nitrogenio_inicial * 100) if nitrogenio_inicial > 0 else 0
    
    # CO2 equivalente
    co2eq_ch4 = cum_ch4_kg * gwp_ch4
    co2eq_n2o = cum_n2o_kg * gwp_n2o
    total_co2eq = co2eq_ch4 + co2eq_n2o
    co2eq_por_ton = (total_co2eq / materia_seca * 1000) if materia_seca > 0 else 0
    
    # Exibição dos resultados em colunas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("CH₄ acumulado (kg)", f"{cum_ch4_kg:.4f}")
        st.metric("N₂O acumulado (kg)", f"{cum_n2o_kg:.4f}")
    with col2:
        st.metric("Perda de C como CH₄ (%)", f"{perc_c:.3f}%")
        st.metric("Perda de N como N₂O (%)", f"{perc_n:.3f}%")
    with col3:
        st.metric("Total CO₂eq (kg)", f"{total_co2eq:.2f}")
        st.metric("CO₂eq por tonelada MS", f"{co2eq_por_ton:.2f} kg/t")
    
    # Comparação com referência do artigo (opcional)
    st.caption("🔍 Referência (Yang et al. 2017): CH₄-C: 0.13% | N₂O-N: 0.92% | GHG: 8.1 kg CO₂eq/t MS")

# ==================== EXPORTAÇÃO DE DADOS ====================
st.subheader("📤 Exportar Dados")
if not medicoes.empty:
    csv = medicoes.to_csv(index=False)
    st.download_button("Baixar medições como CSV", data=csv, file_name=f"medicoes_{dispositivo_id}.csv")
