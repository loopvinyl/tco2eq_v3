import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import warnings

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
def load_excel():
    excel = pd.ExcelFile("Dataset.xlsx")
    data = {sheet: excel.parse(sheet) for sheet in excel.sheet_names}
    return data, excel.sheet_names


# =========================
# FUNÇÕES DE APOIO
# =========================
def dataset_overview(dataframes):
    rows = sum(df.shape[0] for df in dataframes.values())
    cols = sum(df.shape[1] for df in dataframes.values())
    numeric = sum(len(df.select_dtypes(include=np.number).columns) for df in dataframes.values())
    fill = np.mean([
        100 - (df.isnull().sum().sum() / (df.shape[0] * df.shape[1]) * 100)
        if df.shape[0] * df.shape[1] > 0 else 100
        for df in dataframes.values()
    ])
    return rows, cols, numeric, fill


def smart_insights(df):
    insights = []
    numeric_cols = df.select_dtypes(include=np.number)
    if not numeric_cols.empty:
        col = numeric_cols.var().idxmax()
        insights.append(f"🔍 Maior variabilidade em **{col}**")
        insights.append(f"📈 Valor máximo observado: **{numeric_cols[col].max():,.0f}**")
    missing = df.isnull().mean().mul(100)
    if (missing > 30).any():
        insights.append("⚠️ Algumas colunas têm mais de 30% de valores ausentes")
    return insights


# =========================
# APP
# =========================
def main():
    st.title("🌱 FAO Agrifood Carbon Market Dashboard")

    st.markdown("""
    **Dashboard interativo avançado** para exploração do  
    *Agrifood Voluntary Carbon Market Dataset (FAO)*

    📌 Dados carregados **exclusivamente do Excel hospedado no GitHub**  
    📌 Sem APIs externas | 100% reprodutível | Streamlit Cloud Ready
    """)

    # ---------- LOAD ----------
    dataframes, sheets = load_excel()

    # ---------- SIDEBAR ----------
    with st.sidebar:
        st.header("📂 Navegação")

        selected_sheet = st.selectbox(
            "Selecione a aba:",
            sheets
        )

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

        overview = pd.DataFrame([
            {
                "Aba": name,
                "Linhas": df.shape[0],
                "Colunas": df.shape[1],
                "Numéricas": len(df.select_dtypes(include=np.number).columns),
                "% Nulos": round(df.isnull().mean().mean() * 100, 1)
            }
            for name, df in dataframes.items()
        ])

        st.dataframe(overview, use_container_width=True)

        st.markdown("---")

    # ---------- ABA SELECIONADA ----------
    df = dataframes[selected_sheet]

    st.header(f"📄 {selected_sheet}")

    # Métricas rápidas
    total_cells = df.shape[0] * df.shape[1]
    fill_rate = 100 if total_cells == 0 else (
        100 - (df.isnull().sum().sum() / total_cells * 100)
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Registros", df.shape[0])
    c2.metric("Colunas", df.shape[1])
    c3.metric("Numéricas", len(df.select_dtypes(include=np.number).columns))
    c4.metric("Preenchimento", f"{fill_rate:.1f}%")

    # ---------- INSIGHTS ----------
    if show_insights:
        st.subheader("🧠 Insights Automáticos")
        for insight in smart_insights(df):
            st.write(f"- {insight}")

    # ---------- TABS ----------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Dados",
        "🔍 Qualidade",
        "📈 Exploração",
        "💾 Exportar"
    ])

    # ---------- TAB 1 ----------
    with tab1:
        st.dataframe(df, use_container_width=True, height=450)

    # ---------- TAB 2 ----------
    with tab2:
        st.subheader("Qualidade dos Dados")

        missing = pd.DataFrame({
            "Coluna": df.columns,
            "% Ausentes": (df.isnull().mean() * 100).round(2)
        }).sort_values("% Ausentes", ascending=False)

        st.dataframe(missing[missing["% Ausentes"] > 0], use_container_width=True)

    # ---------- TAB 3 ----------
    with tab3:
        st.subheader("Exploração Visual")

        num_cols = df.select_dtypes(include=np.number).columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()

        chart = st.selectbox(
            "Tipo de gráfico:",
            ["Histograma", "Barras", "Dispersão"]
        )

        if chart == "Histograma" and num_cols:
            col = st.selectbox("Coluna:", num_cols)
            fig = px.histogram(df, x=col, nbins=30)
            st.plotly_chart(fig, use_container_width=True)

        elif chart == "Barras" and cat_cols:
            col = st.selectbox("Coluna:", cat_cols)
            top = df[col].value_counts().head(15)
            fig = px.bar(x=top.index, y=top.values)
            st.plotly_chart(fig, use_container_width=True)

        elif chart == "Dispersão" and len(num_cols) >= 2:
            x = st.selectbox("Eixo X:", num_cols)
            y = st.selectbox("Eixo Y:", num_cols)
            fig = px.scatter(df, x=x, y=y, trendline="ols", opacity=0.6)
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Não há colunas compatíveis para este gráfico.")

    # ---------- TAB 4 ----------
    with tab4:
        st.subheader("Exportação")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Baixar aba atual (CSV)",
            csv,
            f"{selected_sheet.replace(' ', '_')}.csv",
            "text/csv"
        )

        report = f"""
Relatório – {selected_sheet}
Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Registros: {df.shape[0]}
Colunas: {df.shape[1]}
Preenchimento: {fill_rate:.1f}%
"""
        st.download_button(
            "📄 Baixar relatório (TXT)",
            report,
            f"relatorio_{selected_sheet}.txt",
            "text/plain"
        )

    # ---------- FOOTER ----------
    st.markdown("---")
    st.caption(
        f"FAO Agrifood Carbon Market Dashboard • "
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
    )


if __name__ == "__main__":
    main()
