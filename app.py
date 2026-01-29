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
    page_title="FAO Agrifood Carbon Market",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# LOAD DO EXCEL LOCAL (GITHUB)
# =========================
@st.cache_data(ttl=86400)
def load_data():
    file_path = "Dataset.xlsx"
    
    # Verifica se o arquivo existe antes de tentar carregar
    if not os.path.exists(file_path):
        return None, None
    
    try:
        # engine='openpyxl' é essencial para ambientes Linux/Cloud
        excel = pd.ExcelFile(file_path, engine='openpyxl')
        data = {sheet: excel.parse(sheet) for sheet in excel.sheet_names}
        return data, excel.sheet_names
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None, None

# =========================
# FUNÇÕES DE APOIO
# =========================
def dataset_overview(dataframes):
    if not dataframes: return 0, 0, 0, 0
    rows = sum(df.shape[0] for df in dataframes.values())
    cols = sum(df.shape[1] for df in dataframes.values())
    numeric = sum(len(df.select_dtypes(include=np.number).columns) for df in dataframes.values())
    
    fills = []
    for df in dataframes.values():
        if df.empty: continue
        fill = 100 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
        fills.append(fill)
    
    avg_fill = np.mean(fills) if fills else 0
    return rows, cols, numeric, avg_fill

def smart_insights(df):
    insights = []
    numeric_cols = df.select_dtypes(include=np.number)
    
    if not numeric_cols.empty:
        # Evita erro se as colunas forem todas zeros/nulos
        variances = numeric_cols.var()
        if not variances.empty:
            col = variances.idxmax()
            insights.append(f"🔍 Maior variabilidade em **{col}**")
            insights.append(f"📈 Valor máximo em {col}: **{numeric_cols[col].max():,.0f}**")
    
    missing = df.isnull().mean().mul(100)
    if (missing > 30).any():
        insights.append("⚠️ Algumas colunas têm mais de 30% de valores ausentes")
    
    if not insights:
        insights.append("✅ Nenhuma anomalia imediata detectada.")
    return insights

# =========================
# APP PRINCIPAL
# =========================
def main():
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")

    # ---------- LOAD ----------
    dataframes, sheets = load_data()

    if dataframes is None:
        st.error("❌ Arquivo 'Dataset.xlsx' não encontrado no repositório!")
        st.info("Certifique-se de que o arquivo está na raiz do seu GitHub com o nome exato.")
        st.stop()

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.header("📂 Navegação")
        selected_sheet = st.selectbox("Selecione a aba:", sheets)
        st.markdown("---")
        st.header("🚀 Ferramentas")
        show_summary = st.toggle("📊 Visão Geral do Dataset", True)
        show_insights = st.toggle("🧠 Insights Automáticos", True)

    # ---------- VISÃO GERAL ----------
    if show_summary:
        st.subheader("📊 Visão Geral do Dataset")
        rows, cols, numeric, fill = dataset_overview(dataframes)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total de Registros", f"{rows:,}")
        c2.metric("Total de Colunas", cols)
        c3.metric("Colunas Numéricas", numeric)
        c4.metric("Preenchimento Médio", f"{fill:.1f}%")

        overview_list = []
        for name, df in dataframes.items():
            overview_list.append({
                "Aba": name,
                "Linhas": df.shape[0],
                "Colunas": df.shape[1],
                "% Nulos": round(df.isnull().mean().mean() * 100, 1)
            })
        st.table(pd.DataFrame(overview_list))

    # ---------- ABA SELECIONADA ----------
    df = dataframes[selected_sheet]
    st.divider()
    st.header(f"📄 Aba: {selected_sheet}")

    # Insights
    if show_insights:
        with st.expander("🧠 Insights Rápidos", expanded=True):
            for insight in smart_insights(df):
                st.write(insight)

    # TABS
    tab1, tab2, tab3 = st.tabs(["📋 Dados", "📈 Exploração", "💾 Exportar"])

    with tab1:
        st.dataframe(df, use_container_width=True)

    with tab2:
        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        if num_cols:
            col_viz = st.selectbox("Escolha uma coluna numérica para ver a distribuição:", num_cols)
            fig = px.histogram(df, x=col_viz, title=f"Distribuição de {col_viz}", color_discrete_sequence=['#2ecc71'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Esta aba não possui dados numéricos para visualização.")

    with tab3:
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Baixar como CSV", csv, f"{selected_sheet}.csv", "text/csv")

    st.markdown("---")
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if __name__ == "__main__":
    main()
