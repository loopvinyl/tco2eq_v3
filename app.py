import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import warnings
import os

warnings.filterwarnings("ignore")

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="FAO Carbon Market Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CARREGAMENTO DE DADOS
# =========================
@st.cache_data(ttl=86400)
def load_data():
    file_path = "Dataset.xlsx"
    
    if not os.path.exists(file_path):
        return None, None
    
    try:
        # engine='openpyxl' é obrigatório para arquivos .xlsx no Streamlit Cloud
        excel = pd.ExcelFile(file_path, engine='openpyxl')
        data = {sheet: excel.parse(sheet) for sheet in excel.sheet_names}
        return data, excel.sheet_names
    except Exception as e:
        st.error(f"Erro crítico ao ler o Excel: {e}")
        return None, None

# =========================
# LÓGICA DE INSIGHTS (CORRIGIDA)
# =========================
def get_smart_insights(df):
    insights = []
    
    # Seleciona apenas colunas numéricas que tenham ao menos um valor válido
    numeric_cols = df.select_dtypes(include=[np.number]).dropna(axis=1, how='all')
    
    if not numeric_cols.empty:
        try:
            # Calcula variância ignorando nulos
            vars = numeric_cols.var().dropna()
            if not vars.empty:
                top_col = vars.idxmax()
                max_val = numeric_cols[top_col].max()
                insights.append(f"🔍 **Maior variabilidade:** Coluna `{top_col}`")
                insights.append(f"📈 **Valor máximo em `{top_col}`:** {max_val:,.2f}")
        except:
            pass
    
    # Análise de nulos
    nulos_pct = df.isnull().mean() * 100
    cols_criticas = nulos_pct[nulos_pct > 50].count()
    if cols_criticas > 0:
        insights.append(f"⚠️ **Atenção:** {cols_criticas} colunas têm mais de 50% de dados ausentes.")
    
    if not insights:
        insights.append("ℹ️ Esta aba contém predominantemente metadados ou textos descritivos.")
        
    return insights

# =========================
# INTERFACE PRINCIPAL
# =========================
def main():
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")
    
    dataframes, sheets = load_data()

    if dataframes is None:
        st.error("🚨 Erro: Arquivo 'Dataset.xlsx' não encontrado no diretório principal.")
        st.markdown("Verifique se o arquivo está no seu repositório GitHub junto com o `main.py`.")
        st.stop()

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("📂 Navegação")
        selected_sheet = st.selectbox("Escolha a aba do Excel:", sheets)
        
        st.divider()
        st.header("⚙️ Filtros de Visualização")
        hide_empty = st.checkbox("Ocultar colunas vazias", value=True)
        show_summary = st.toggle("Visão Geral do Projeto", True)

    # --- VISÃO GERAL ---
    if show_summary:
        with st.expander("📊 Estatísticas do Dataset Completo", expanded=False):
            total_rows = sum(len(d) for d in dataframes.values())
            total_sheets = len(sheets)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Linhas", f"{total_rows:,}")
            c2.metric("Total de Abas", total_sheets)
            c3.metric("Status do Arquivo", "Online ✅")

    # --- PROCESSAMENTO DA ABA SELECIONADA ---
    df = dataframes[selected_sheet].copy()
    
    if hide_empty:
        df = df.dropna(axis=1, how='all')

    st.header(f"📄 Aba Atual: {selected_sheet}")

    # Cards de Métricas Rápidas
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Linhas", df.shape[0])
    m2.metric("Colunas Ativas", df.shape[1])
    m3.metric("Colunas Numéricas", len(df.select_dtypes(include=np.number).columns))
    m4.metric("Preenchimento", f"{(1 - df.isnull().mean().mean())*100:.1f}%")

    # --- TABS DE CONTEÚDO ---
    tab_data, tab_viz, tab_export = st.tabs(["📋 Visualizar Dados", "📈 Exploração Visual", "💾 Exportar"])

    with tab_data:
        st.subheader("Insights da Aba")
        insights = get_smart_insights(df)
        for text in insights:
            st.markdown(f"- {text}")
        
        st.divider()
        st.dataframe(df, use_container_width=True, height=400)

    with tab_viz:
        st.subheader("Análise Gráfica")
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        
        if len(num_cols) >= 1:
            col_x = st.selectbox("Selecione a métrica:", num_cols)
            fig = px.histogram(df, x=col_x, title=f"Distribuição de {col_x}", 
                               color_discrete_sequence=['#2ecc71'], marginal="box")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Esta aba não possui dados numéricos suficientes para gerar gráficos.")

    with tab_export:
        st.subheader("Download dos Dados")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Baixar aba atual como CSV",
            data=csv,
            file_name=f"fao_data_{selected_sheet.lower()}.csv",
            mime="text/csv"
        )

    st.divider()
    st.caption(f"FAO Dashboard | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
